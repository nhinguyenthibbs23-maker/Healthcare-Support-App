import json
import re
import streamlit as st
import streamlit.components.v1 as components
from utils.ai_service import generate_ai_response
from utils.i18n import lang as current_lang
from utils.ui import tr, get_doctor_data_uri

VOICE_MARKER = "\u200b"


def _clean_for_speech(text: str) -> str:
    t = re.sub(r'#+\s*', '', text)
    t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)
    t = re.sub(r'\*([^*]+)\*', r'\1', t)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = re.sub(r'`([^`]+)`', r'\1', t)
    t = re.sub(r'[-*•]\s*', '', t)
    t = re.sub(r'\n+', '. ', t)
    return t.strip()


def _render_tts_button(text: str, lang_code: str, unique_id: str, auto_play: bool = False):
    clean_text = _clean_for_speech(text)
    if not clean_text:
        return
    text_json = json.dumps(clean_text)
    btn_label = "Nghe bác sĩ đọc" if lang_code == "vi" else "Listen to Doctor"
    stop_label = "Dừng đọc" if lang_code == "vi" else "Stop Reading"
    again_label = "Nghe lại" if lang_code == "vi" else "Listen Again"
    speech_lang = "vi-VN" if lang_code == "vi" else "en-US"

    auto_block = ""
    if auto_play:
        auto_block = f"""
        window.addEventListener('load', function() {{
            setTimeout(function() {{ speak_{unique_id}(); }}, 450);
        }});
        """

    html_code = f"""
    <div style="margin: 4px 0 2px 0;">
        <button id="tts_{unique_id}" onclick="speak_{unique_id}()" style="
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            color: #1E40AF;
            border-radius: 14px;
            padding: 4px 11px;
            font-size: 11.5px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            transition: all 0.15s ease;
        ">
            <span id="icon_{unique_id}">🔊</span>
            <span id="lbl_{unique_id}">{btn_label}</span>
        </button>
    </div>
    <script>
    let playing_{unique_id} = false;
    function speak_{unique_id}() {{
        if (!('speechSynthesis' in window)) {{
            return;
        }}
        const btn = document.getElementById('tts_{unique_id}');
        const icon = document.getElementById('icon_{unique_id}');
        const lbl = document.getElementById('lbl_{unique_id}');

        if (window.speechSynthesis.speaking || playing_{unique_id}) {{
            window.speechSynthesis.cancel();
            playing_{unique_id} = false;
            if (btn) {{
                btn.style.background = '#EFF6FF';
                btn.style.borderColor = '#BFDBFE';
                btn.style.color = '#1E40AF';
            }}
            if (icon) icon.innerText = '🔊';
            if (lbl) lbl.innerText = '{btn_label}';
            return;
        }}

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance({text_json});
        utterance.lang = '{speech_lang}';
        utterance.pitch = 0.92;
        utterance.rate = 0.96;

        const voices = window.speechSynthesis.getVoices();
        let maleVoice = null;
        if ('{lang_code}' === 'vi') {{
            const viVoices = voices.filter(v => v.lang.toLowerCase().startsWith('vi'));
            const isFemaleVi = (n) => (
                n.includes('hoaimy') || n.includes('hoai my') || n.includes('female') ||
                n.includes('linh') || n.includes('lan') || n.includes('mai') ||
                n.includes('hoa') || n.includes('nu') ||
                n.includes('standard-a') || n.includes('standard-c') ||
                n.includes('wavenet-a') || n.includes('wavenet-c') || n.includes('neural2-a')
            );
            maleVoice = viVoices.find(v => {{
                const n = v.name.toLowerCase().replace(/vietnam(ese)?/g, '');
                return !isFemaleVi(n) && (
                    n.includes('namminh') || n.includes('nam minh') || n.includes('male') ||
                    n.includes('minh') || n.includes('hung') || n.includes('dung') ||
                    n.includes('tuan') || n.includes('hoang') || n.includes('duc') ||
                    /\ban\b/.test(n) ||
                    n.includes('standard-b') || n.includes('standard-d') ||
                    n.includes('wavenet-b') || n.includes('wavenet-d') || n.includes('neural2-d')
                );
            }}) || viVoices.find(v => !isFemaleVi(v.name.toLowerCase().replace(/vietnam(ese)?/g, '')))
              || viVoices[0] || null;
        }} else {{
            const enVoices = voices.filter(v => v.lang.toLowerCase().startsWith('en'));
            const isFemaleEn = (n) => (
                n.includes('female') || n.includes('zira') || n.includes('jenny') ||
                n.includes('samantha') || n.includes('aria') || n.includes('sara') ||
                n.includes('hazel') || n.includes('susan') || n.includes('victoria') ||
                n.includes('karen') || n.includes('moira') || n.includes('tessa')
            );
            maleVoice = enVoices.find(v => {{
                const n = v.name.toLowerCase();
                return !isFemaleEn(n) && (
                    n.includes('male') || n.includes('guy') || n.includes('david') ||
                    n.includes('mark') || n.includes('christopher') || n.includes('eric') ||
                    n.includes('andrew') || n.includes('brian') || n.includes('roger') ||
                    n.includes('steffan') || n.includes('george') || n.includes('ryan') ||
                    n.includes('daniel') || n.includes('alex') || n.includes('aaron') ||
                    n.includes('arthur') || n.includes('oliver') || n.includes('tom') ||
                    n.includes('standard-b') || n.includes('standard-d') ||
                    n.includes('standard-i') || n.includes('standard-j') ||
                    n.includes('wavenet-b') || n.includes('wavenet-d')
                );
            }}) || enVoices.find(v => !isFemaleEn(v.name.toLowerCase()))
              || enVoices[0] || null;
        }}
        if (maleVoice) utterance.voice = maleVoice;

        utterance.onstart = () => {{
            playing_{unique_id} = true;
            if (btn) {{
                btn.style.background = '#FEF2F2';
                btn.style.borderColor = '#FECACA';
                btn.style.color = '#DC2626';
            }}
            if (icon) icon.innerText = '⏹️';
            if (lbl) lbl.innerText = '{stop_label}';
        }};
        utterance.onend = () => {{
            playing_{unique_id} = false;
            if (btn) {{
                btn.style.background = '#EFF6FF';
                btn.style.borderColor = '#BFDBFE';
                btn.style.color = '#1E40AF';
            }}
            if (icon) icon.innerText = '🔊';
            if (lbl) lbl.innerText = '{again_label}';
        }};
        utterance.onerror = () => {{
            playing_{unique_id} = false;
            if (btn) {{
                btn.style.background = '#EFF6FF';
                btn.style.borderColor = '#BFDBFE';
                btn.style.color = '#1E40AF';
            }}
            if (icon) icon.innerText = '🔊';
            if (lbl) lbl.innerText = '{btn_label}';
        }};

        window.speechSynthesis.speak(utterance);
    }}
    {auto_block}
    </script>
    """
    components.html(html_code, height=36)


def _default_greeting() -> str:
    return tr(
        "Xin chào! Tôi là Bác sĩ Nguyễn Hoài Đức – Trợ lý AI GlucoGuide. Tôi có thể giúp bạn hiểu rõ kết quả sàng lọc, các yếu tố tác động và gợi ý bước tiếp theo.",
        "Hi! I'm Dr. Nguyen Hoai Duc – GlucoGuide AI Assistant. I can help explain your screening result, key contributing factors, and suggested next steps.",
    )


def _sync_chat_state():
    cur_l = current_lang()
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [{"role": "assistant", "content": _default_greeting()}]
        st.session_state["chat_lang"] = cur_l
    elif st.session_state.get("chat_lang") != cur_l:
        st.session_state["chat_lang"] = cur_l
        if len(st.session_state["chat_messages"]) == 1:
            st.session_state["chat_messages"][0]["content"] = _default_greeting()


def render_floating_ai_assistant(context: dict):
    _sync_chat_state()
    doc_uri = get_doctor_data_uri()
    cur_l = current_lang()

    if doc_uri:
        btn_bg_css = f'background-image: url("{doc_uri}") !important; background-size: cover !important; background-position: center top !important; background-repeat: no-repeat !important; background-color: #EFF6FF !important;'
        avatar_html = f'<img src="{doc_uri}" alt="Doctor AI" style="width:42px;height:42px;border-radius:50%;object-fit:cover;object-position:top;border:2.5px solid #2563EB;box-shadow:0 2px 8px rgba(37,99,235,0.25);"/>'
    else:
        btn_bg_css = "background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;"
        avatar_html = '<div style="width:42px;height:42px;border-radius:50%;background:#EFF6FF;border:2.5px solid #2563EB;"></div>'

    ai_badge_label = tr("Hỏi AI", "Ask AI")

    st.markdown(f"""
    <style>
    .st-key-ai_fab_wrap {{
        position: fixed !important;
        bottom: 26px !important;
        right: 28px !important;
        z-index: 9999 !important;
        width: auto !important;
        height: auto !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    .st-key-ai_fab_wrap [data-testid="stPopover"] {{
        width: auto !important;
        height: auto !important;
        display: inline-block !important;
    }}
    .st-key-ai_fab_wrap [data-testid="stPopoverButton"],
    .st-key-ai_fab_wrap [data-testid="stPopover"] button,
    .st-key-ai_fab_wrap button {{
        width: 72px !important;
        height: 72px !important;
        min-width: 72px !important;
        min-height: 72px !important;
        max-width: 72px !important;
        max-height: 72px !important;
        padding: 0 !important;
        border-radius: 50% !important;
        {btn_bg_css}
        border: 3.5px solid #2563EB !important;
        box-shadow: 0 10px 28px rgba(29, 78, 216, 0.45) !important;
        position: relative !important;
        overflow: visible !important;
        transition: transform 0.18s ease, box-shadow 0.18s ease !important;
        cursor: pointer !important;
    }}
    .st-key-ai_fab_wrap [data-testid="stPopoverButton"]:hover,
    .st-key-ai_fab_wrap [data-testid="stPopover"] button:hover,
    .st-key-ai_fab_wrap button:hover {{
        transform: scale(1.08) !important;
        box-shadow: 0 14px 34px rgba(29, 78, 216, 0.55) !important;
    }}
    .st-key-ai_fab_wrap [data-testid="stPopoverButton"] > *,
    .st-key-ai_fab_wrap [data-testid="stPopover"] button > *,
    .st-key-ai_fab_wrap button > *,
    .st-key-ai_fab_wrap [data-testid="stPopoverButton"] svg,
    .st-key-ai_fab_wrap [data-testid="stPopover"] button svg,
    .st-key-ai_fab_wrap button svg {{
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        font-size: 0 !important;
    }}
    .st-key-ai_fab_wrap [data-testid="stPopoverButton"]::before,
    .st-key-ai_fab_wrap [data-testid="stPopover"] button::before,
    .st-key-ai_fab_wrap button::before {{
        content: "" !important;
        display: block !important;
        position: absolute !important;
        top: -2px !important;
        right: -2px !important;
        width: 24px !important;
        height: 24px !important;
        border-radius: 50% !important;
        background-color: #2563EB !important;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E%3C/svg%3E") !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: 13px 13px !important;
        border: 2.5px solid #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.28) !important;
        z-index: 10 !important;
    }}
    .st-key-ai_fab_wrap [data-testid="stPopoverButton"]::after,
    .st-key-ai_fab_wrap [data-testid="stPopover"] button::after,
    .st-key-ai_fab_wrap button::after {{
        content: "{ai_badge_label}" !important;
        display: block !important;
        position: absolute !important;
        bottom: -9px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        background: #1D4ED8 !important;
        color: #FFFFFF !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        padding: 3px 11px !important;
        border-radius: 999px !important;
        border: 2px solid #FFFFFF !important;
        white-space: nowrap !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.28) !important;
        z-index: 10 !important;
        line-height: 1.1 !important;
    }}
    div[data-baseweb="popover"] [data-testid="stPopoverBody"] {{
        width: 450px !important;
        max-width: 94vw !important;
        border-radius: 18px !important;
        padding: 16px 18px !important;
    }}
    /* Make chat input placeholder spacious and crisp inside popover */
    div[data-baseweb="popover"] [data-testid="stChatInput"] {{
        width: 100% !important;
        margin-top: 6px !important;
    }}
    div[data-baseweb="popover"] [data-testid="stChatInput"] > div {{
        min-height: 46px !important;
        border-radius: 14px !important;
        padding: 4px 8px !important;
    }}
    div[data-baseweb="popover"] [data-testid="stChatInputTextArea"],
    div[data-baseweb="popover"] [data-testid="stChatInput"] textarea {{
        font-size: 0.88rem !important;
        line-height: 1.45 !important;
        padding: 10px 12px !important;
        min-height: 42px !important;
        width: 100% !important;
    }}
    div[data-baseweb="popover"] [data-testid="stChatInputTextArea"]::placeholder,
    div[data-baseweb="popover"] [data-testid="stChatInput"] textarea::placeholder {{
        font-size: 0.86rem !important;
        color: #64748B !important;
        opacity: 1 !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="ai_fab_wrap"):
        with st.popover(" ", help=tr("Mở Trợ lý AI GlucoGuide", "Open GlucoGuide AI Assistant")):
            h_l, h_r = st.columns([3.4, 1], vertical_alignment="center")
            with h_l:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;">
                    {avatar_html}
                    <div>
                        <div style="font-size:0.98rem;font-weight:800;color:#142D4E;line-height:1.2;">{tr("Bác sĩ Nguyễn Hoài Đức", "Dr. Nguyen Hoai Duc")}</div>
                        <div style="font-size:0.74rem;color:#64748B;">{tr("Trợ lý AI GlucoGuide · Hỗ trợ sàng lọc", "GlucoGuide AI · Screening Companion")}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with h_r:
                if st.button(tr("Làm mới", "Reset"), key="reset_chat", use_container_width=True):
                    st.session_state["chat_messages"] = [{"role": "assistant", "content": _default_greeting()}]

            st.divider()

            chat_box = st.container(height=275)

            st.caption(tr("Gợi ý câu hỏi:", "Quick questions:"))
            q_cols = st.columns(2)
            chips = [
                tr("Giải thích kết quả của tôi", "Explain my result"),
                tr("Tại sao tôi nhận phân loại này?", "Why this risk category?"),
                tr("Yếu tố nào ảnh hưởng nhất?", "Top influencing factors?"),
                tr("Tôi nên làm gì tiếp theo?", "What should I do next?"),
            ]
            selected_prompt = None
            for i, chip_text in enumerate(chips):
                if q_cols[i % 2].button(chip_text, key=f"fab_chip_{i}", use_container_width=True):
                    selected_prompt = chip_text

            user_query = st.chat_input(
                placeholder=tr("Nhập câu hỏi sức khỏe của bạn tại đây...", "Type your health question here..."),
                key="fab_chat_input",
            )

            # ── Voice Recognition Button (auto-TTS ONLY triggers when spoken via Mic) ──
            mic_label = tr("🎤 Nói chuyện với AI", "🎤 Speak to AI")
            listening_lbl = tr("⏹ Đang nghe...", "⏹ Listening...")
            no_support = tr("Trình duyệt không hỗ trợ nhận dạng giọng nói.", "Your browser does not support speech recognition.")
            speech_lang = "vi-VN" if cur_l == "vi" else "en-US"
            components.html(f"""
            <div style="margin:4px 0 0 0;display:flex;justify-content:center;">
              <button id="voiceBtn" onclick="toggleVoice()" style="
                background:#EFF6FF;border:1.5px solid #BFDBFE;color:#1E40AF;
                border-radius:20px;padding:7px 20px;font-size:12.5px;font-weight:700;
                cursor:pointer;display:inline-flex;align-items:center;gap:7px;
                font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
                transition:all 0.2s ease;width:auto;">
                {mic_label}
              </button>
            </div>
            <div id="voiceStatus" style="text-align:center;font-size:11px;color:#64748B;min-height:16px;margin-top:3px;"></div>
            <script>
            let _recog = null;
            let _listening = false;
            function toggleVoice() {{
              if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {{
                document.getElementById('voiceStatus').innerText = {repr(no_support)};
                return;
              }}
              if (_listening && _recog) {{
                _recog.stop();
                return;
              }}
              const SRClass = window.SpeechRecognition || window.webkitSpeechRecognition;
              _recog = new SRClass();
              _recog.lang = '{speech_lang}';
              _recog.interimResults = false;
              _recog.maxAlternatives = 1;
              _listening = true;
              const btn = document.getElementById('voiceBtn');
              const status = document.getElementById('voiceStatus');
              btn.innerText = {repr(listening_lbl)};
              btn.style.background = '#FEF2F2';
              btn.style.borderColor = '#FCA5A5';
              btn.style.color = '#DC2626';
              status.innerText = '🔴 ' + ('{speech_lang}' === 'vi-VN' ? 'Hãy nói...' : 'Listening...');

              _recog.onresult = function(e) {{
                const transcript = e.results[0][0].transcript;
                const markedTranscript = transcript + '\u200b';
                const chatInput = window.parent.document.querySelector('[data-testid="stChatInputTextArea"], textarea[aria-label], .stChatInput textarea');
                if (chatInput) {{
                  const nativeInput = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
                  nativeInput.set.call(chatInput, markedTranscript);
                  chatInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                  setTimeout(() => {{
                    chatInput.dispatchEvent(new KeyboardEvent('keydown', {{ key:'Enter', code:'Enter', keyCode:13, bubbles:true }}));
                  }}, 250);
                }}
                status.innerText = '✅ "' + transcript + '"';
              }};
              _recog.onerror = function(e) {{
                status.innerText = '⚠️ ' + e.error;
              }};
              _recog.onend = function() {{
                _listening = false;
                btn.innerText = {repr(mic_label)};
                btn.style.background = '#EFF6FF';
                btn.style.borderColor = '#BFDBFE';
                btn.style.color = '#1E40AF';
                setTimeout(() => {{ status.innerText = ''; }}, 3000);
              }};
              _recog.start();
            }}
            </script>
            """, height=72)

            is_voice_triggered = bool(user_query and VOICE_MARKER in user_query)
            raw_prompt = selected_prompt or user_query
            prompt_to_process = raw_prompt.replace(VOICE_MARKER, "").strip() if raw_prompt else None

            if prompt_to_process:
                st.session_state["chat_messages"].append({"role": "user", "content": prompt_to_process})
                reply = generate_ai_response(
                    prompt_to_process,
                    st.session_state["chat_messages"][:-1],
                    context,
                    current_lang=cur_l,
                )
                st.session_state["chat_messages"].append({"role": "assistant", "content": reply})
                if is_voice_triggered:
                    st.session_state["auto_speak_idx"] = len(st.session_state["chat_messages"]) - 1

            with chat_box:
                assistant_avatar = doc_uri if doc_uri else None
                auto_idx = st.session_state.pop("auto_speak_idx", -1)
                for idx, msg in enumerate(st.session_state["chat_messages"]):
                    with st.chat_message(msg["role"], avatar=(assistant_avatar if msg["role"] == "assistant" else None)):
                        st.markdown(msg["content"])
                        if msg["role"] == "assistant":
                            _render_tts_button(msg["content"], cur_l, f"tts_{idx}", auto_play=(idx == auto_idx))

            st.caption(tr(
                "Thông tin chỉ phục vụ mục đích giáo dục, không thay thế chẩn đoán của bác sĩ.",
                "Educational information only; does not replace professional medical advice.",
            ))
