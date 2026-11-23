import json
import streamlit as st
import streamlit.components.v1 as components

from utils.i18n import pick_language, lang
from utils.ui import (
    style,
    html,
    tr,
    get_doctor_data_uri,
    get_eiu_logo_data_uri,
    get_eiu_logo_bilingual_svg,
    EIU_LOGO_TRANSPARENT_SVG,
    DOCTOR_SVG,
    HEART_PULSE_SVG,
    SHIELD_PLUS_SVG,
)

if "lang" not in st.session_state:
    st.session_state["lang"] = "vi"
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "user"

st.set_page_config(
    page_title="GlucoGuide",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

style()


def home_view():
    """Home Page matching Image 1 design with doctor photo & 3-step How It Works."""
    doctor_uri = get_doctor_data_uri()
    cur_l = st.session_state.get("lang", "vi")
    speech_script = tr(
        "Xin chào! Hãy cùng tôi dành 2 phút đánh giá nguy cơ để chủ động bảo vệ sức khỏe trước bệnh tiểu đường nhé!",
        "Hello! Spend 2 minutes with me to assess your risk and proactively protect your health against diabetes!"
    )
    bubble_title = tr("Bác sĩ Nguyễn Hoài Đức", "Dr. Nguyen Hoai Duc")
    listen_lbl = tr("Nghe nói", "Listen")
    stop_lbl = tr("Dừng", "Stop")
    script_json = json.dumps(speech_script)

    doctor_img_tag = (
        f'<img src="{doctor_uri}" alt="{bubble_title}" class="hero-doctor-img"/>'
        if doctor_uri
        else f'<div style="padding-bottom:1.2rem;">{DOCTOR_SVG}</div>'
    )

    stethoscope_svg = (
        '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#1E40AF" '
        'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;">'
        '<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/>'
        '<path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/>'
        '<circle cx="20" cy="10" r="2"/>'
        '</svg>'
    )
    speaker_svg = (
        '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
        '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
        '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>'
        '</svg>'
    )
    stop_svg = (
        '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" '
        'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="6" y="6" width="12" height="12" rx="2"/>'
        '</svg>'
    )

    doctor_iframe_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<style>
- {{ box-sizing: border-box; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; }}
  html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    overflow: hidden;
  }}
  .hero-doctor-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    padding: 6px 4px 4px 4px;
  }}
  .doctor-speech-bubble {{
    background: #F0F7FF;
    border: 1.5px solid #BFDBFE;
    border-radius: 16px;
    padding: 10px 14px;
    margin-bottom: 12px;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
    position: relative;
    width: 100%;
    max-width: 330px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    animation: bubbleFloat 3.2s ease-in-out infinite;
  }}
  .doctor-speech-bubble:hover {{
    transform: translateY(-2px);
    border-color: #93C5FD;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.16);
  }}
  .doctor-speech-bubble.is-speaking {{
    border-color: #2563EB;
    background: #EFF6FF;
  }}
  .doctor-speech-bubble::after {{
    content: '';
    position: absolute;
    bottom: -7px;
    left: 50%;
    transform: translateX(-50%);
    border-width: 7px 7px 0;
    border-style: solid;
    border-color: #BFDBFE transparent transparent transparent;
  }}
  @keyframes bubbleFloat {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-4px); }}
  }}
  .bubble-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 4px;
  }}
  .bubble-title {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.74rem;
    font-weight: 700;
    color: #1E40AF;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .bubble-sound-btn {{
    font-size: 0.72rem;
    font-weight: 600;
    color: #1D4ED8;
    background: #FFFFFF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 3px 9px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .bubble-sound-btn:hover {{
    background: #DBEAFE;
  }}
  .bubble-text {{
    font-size: 0.82rem;
    font-weight: 500;
    line-height: 1.44;
    color: #1E3A8A;
    margin: 0;
    font-style: italic;
  }}
  .hero-doctor-wrap {{
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
  }}
  .hero-doctor-img {{
    width: 100%;
    max-width: 315px;
    height: auto;
    max-height: 365px;
    object-fit: cover;
    object-position: center top;
    border-radius: 22px;
    display: block;
    box-shadow: 0 10px 28px rgba(15, 40, 84, 0.12);
  }}
</style>
</head>
<body>
<div class="hero-doctor-container">
  <div class="doctor-speech-bubble" id="heroDoctorBubble" onclick="toggleDoctorBubble()" title="{tr("Bấm để nghe bác sĩ nói", "Click to hear doctor speak")}">
    <div class="bubble-header">
      <span class="bubble-title">{stethoscope_svg}<span>{bubble_title}</span></span>
      <span class="bubble-sound-btn" id="bubbleSoundBtn">{speaker_svg}<span>{listen_lbl}</span></span>
    </div>
    <p class="bubble-text">“{speech_script}”</p>
  </div>
  <div class="hero-doctor-wrap">
    {doctor_img_tag}
  </div>
</div>

<script>
  const SCRIPT_TEXT = {script_json};
  const LANG_CODE = '{cur_l}';
  const LISTEN_HTML = `{speaker_svg}<span>{listen_lbl}</span>`;
  const STOP_HTML = `{stop_svg}<span>{stop_lbl}</span>`;
  let isSpeaking = false;
  let hasPlayedInitial = false;

  function setSpeakingUI(active) {{
    isSpeaking = active;
    const btn = document.getElementById('bubbleSoundBtn');
    const bubble = document.getElementById('heroDoctorBubble');
    if (btn) btn.innerHTML = active ? STOP_HTML : LISTEN_HTML;
    if (bubble) {{
      if (active) bubble.classList.add('is-speaking');
      else bubble.classList.remove('is-speaking');
    }}
  }}

  function pickVoice(voices) {{
    if (!voices || !voices.length) return null;
    if (LANG_CODE === 'vi') {{
      const viVoices = voices.filter(v => v.lang.toLowerCase().startsWith('vi'));
      const isFemaleVi = (n) => (
        n.includes('hoaimy') || n.includes('hoai my') || n.includes('female') ||
        n.includes('linh') || n.includes('lan') || n.includes('mai') ||
        n.includes('hoa') || n.includes('nu') ||
        n.includes('standard-a') || n.includes('standard-c') ||
        n.includes('wavenet-a') || n.includes('wavenet-c') || n.includes('neural2-a')
      );
      return viVoices.find(v => {{
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
    }}
    const enVoices = voices.filter(v => v.lang.toLowerCase().startsWith('en'));
    const isFemaleEn = (n) => (
      n.includes('female') || n.includes('zira') || n.includes('jenny') ||
      n.includes('samantha') || n.includes('aria') || n.includes('sara') ||
      n.includes('hazel') || n.includes('susan') || n.includes('victoria') ||
      n.includes('karen') || n.includes('moira') || n.includes('tessa')
    );
    return enVoices.find(v => {{
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

  function startSpeech() {{
    if (!('speechSynthesis' in window)) return;
    try {{
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(SCRIPT_TEXT);
      utterance.lang = LANG_CODE === 'vi' ? 'vi-VN' : 'en-US';
      utterance.pitch = 0.92;
      utterance.rate = 0.96;
      const v = pickVoice(window.speechSynthesis.getVoices());
      if (v) utterance.voice = v;

      utterance.onstart = () => {{
        hasPlayedInitial = true;
        setSpeakingUI(true);
      }};
      utterance.onend = () => setSpeakingUI(false);
      utterance.onerror = () => setSpeakingUI(false);

      window.speechSynthesis.speak(utterance);
    }} catch (e) {{
      setSpeakingUI(false);
    }}
  }}

  function toggleDoctorBubble() {{
    if (!('speechSynthesis' in window)) return;
    if (window.speechSynthesis.speaking || isSpeaking) {{
      window.speechSynthesis.cancel();
      setSpeakingUI(false);
    }} else {{
      hasPlayedInitial = true;
      startSpeech();
    }}
  }}

  function unlockAndPlayOnce() {{
    if (hasPlayedInitial) return;
    hasPlayedInitial = true;
    startSpeech();
    cleanupUnlockListeners();
  }}

  function cleanupUnlockListeners() {{
    document.removeEventListener('pointerdown', unlockAndPlayOnce);
    document.removeEventListener('keydown', unlockAndPlayOnce);
    try {{
      if (window.parent && window.parent.document) {{
        window.parent.document.removeEventListener('pointerdown', unlockAndPlayOnce);
        window.parent.document.removeEventListener('keydown', unlockAndPlayOnce);
      }}
    }} catch (e) {{}}
  }}

  if ('speechSynthesis' in window) {{
    window.speechSynthesis.onvoiceschanged = () => {{
      if (!hasPlayedInitial) startSpeech();
    }};
  }}

  window.addEventListener('load', () => {{
    setTimeout(startSpeech, 250);
    document.addEventListener('pointerdown', unlockAndPlayOnce, {{ once: true }});
    document.addEventListener('keydown', unlockAndPlayOnce, {{ once: true }});
    try {{
      if (window.parent && window.parent.document) {{
        window.parent.document.addEventListener('pointerdown', unlockAndPlayOnce, {{ once: true }});
        window.parent.document.addEventListener('keydown', unlockAndPlayOnce, {{ once: true }});
      }}
    }} catch (e) {{}}
  }});
</script>
</body>
</html>'''

    with st.container(key="home_hero"):
        c_hero_l, c_hero_r = st.columns([1.25, 0.95], vertical_alignment="center", gap="large")

        with c_hero_l:
            html(f"""
            <h1 class="brand-title">GlucoGuide</h1>
            <div class="brand-subtitle">
                {tr("Thấu hiểu Nguy cơ. Chủ động Bảo vệ Sức khỏe.", "Know Your Risk. Take Control of Your Health.")}
            </div>
            <div class="brand-lead">
                {tr(
                    "Công cụ sàng lọc nguy cơ tiểu đường thông minh, giúp bạn hiểu rõ các yếu tố sức khỏe và đưa ra quyết định chăm sóc sức khỏe chủ động.",
                    "A smart diabetes risk screening tool designed to help you understand your health factors and make proactive health decisions."
                )}
            </div>
            """)

            if st.button(tr("Bắt đầu Đánh giá Nguy cơ", "Start Risk Assessment"), type="primary"):
                st.session_state["assess_step"] = 1
                st.switch_page("pages/1_Risk_Assessment.py")

        with c_hero_r:
            components.html(doctor_iframe_html, height=495, scrolling=False)

    st.write("")

    # How It Works 3-Step Banner (matching Image 1)
    with st.container(key="how_card"):
        html(f"""
        <div class="how-layout">
            <div class="how-shield-box">{SHIELD_PLUS_SVG}</div>
            <div>
                <div class="how-title">{tr("Quy trình Hoạt động?", "How It Works?")}</div>
                <div class="how-steps">
                    <div class="how-step-box">
                        <div class="flow-num-badge">1</div>
                        <div class="how-step-txt">{tr("Trả lời vài câu hỏi đơn giản", "Answer a few simple questions")}</div>
                    </div>
                    <div class="how-arrow"><span class="flow-ch-1">›</span><span class="flow-ch-2">›</span><span class="flow-ch-3">›</span></div>
                    <div class="how-step-box">
                        <div class="flow-num-badge">2</div>
                        <div class="how-step-txt">{tr("Nhận kết quả nguy cơ của bạn", "Get your risk result")}</div>
                    </div>
                    <div class="how-arrow"><span class="flow-ch-1">›</span><span class="flow-ch-2">›</span><span class="flow-ch-3">›</span></div>
                    <div class="how-step-box">
                        <div class="flow-num-badge">3</div>
                        <div class="how-step-txt">{tr("Tìm hiểu thêm cùng Trợ lý AI", "Learn more with our AI Assistant")}</div>
                    </div>
                </div>
            </div>
        </div>
        """)


# Determine Mode before building navigation
mode = st.session_state.get("app_mode", "user")

home_title = tr("Trang chủ", "Home")
assess_title = tr("Khảo sát Nguy cơ", "Risk Assessment")
results_title = tr("Kết quả của tôi", "My Results")
about_title = tr("Về GlucoGuide", "About GlucoGuide")
teacher_title = tr("Tổng quan Dự án", "Project Overview")

home_page = st.Page(
    home_view,
    title=home_title,
    default=(mode == "user"),
)
assess_page = st.Page(
    "pages/1_Risk_Assessment.py",
    title=assess_title,
)
results_page = st.Page(
    "pages/2_My_Results.py",
    title=results_title,
)
about_page = st.Page(
    "pages/3_About_GlucoGuide.py",
    title=about_title,
)
teacher_page = st.Page(
    "pages/4_Teacher_Overview.py",
    title=teacher_title,
    default=(mode == "teacher"),
)

if mode == "user":
    nav_items = [
        ("nav_home", home_title, home_page),
        ("nav_assess", assess_title, assess_page),
        ("nav_results", results_title, results_page),
        ("nav_about", about_title, about_page),
    ]
else:
    nav_items = [
        ("nav_teacher", teacher_title, teacher_page),
    ]

pages = [p for _, _, p in nav_items]
nav = st.navigation(pages, position="hidden")

# ============ CUSTOM SIDEBAR (LOGO AT VERY TOP) ============
cur_lang = st.session_state.get("lang", "vi")
logo_markup = get_eiu_logo_bilingual_svg(cur_lang)

with st.sidebar:
    st.markdown(
        f'''
        <div class="sb-logo-wrap">
            {logo_markup}
        </div>
        <div class="sb-brand-row">
            {HEART_PULSE_SVG}
            <div class="sb-brand-name">GlucoGuide</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    for slug, label, page_obj in nav_items:
        state_cls = "active" if page_obj == nav else "idle"
        with st.container(key=f"{slug}_{state_cls}"):
            st.page_link(page_obj, label=label, use_container_width=True)

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
    pick_language()

    mode_lbl = tr("CHẾ ĐỘ", "MODE")
    st.markdown(
        f'<div class="sb-section-lbl">{mode_lbl}</div>',
        unsafe_allow_html=True,
    )
    with st.container(key="sb_mode_seg"):
        cur_mode = st.session_state.get("app_mode", "user")
        selected_mode = st.radio(
            "sb_mode_select_hidden",
            options=["user", "teacher"],
            format_func=lambda val: tr(
                "Người dùng" if val == "user" else "Giảng viên",
                "User" if val == "user" else "Teacher",
            ),
            index=0 if cur_mode == "user" else 1,
            horizontal=True,
            key="sb_mode_radio",
            label_visibility="collapsed",
        )
        if selected_mode != cur_mode:
            st.session_state["app_mode"] = selected_mode
            st.rerun()

    st.markdown(
        f"""
        <div class="sb-note">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#93C5FD" stroke-width="2" style="flex:0 0 16px;margin-top:2px">
                <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
            </svg>
            <span>{tr(
                "Công cụ phục vụ mục đích giáo dục, không dùng trong chẩn đoán lâm sàng.",
                "Educational tool, not for clinical diagnosis."
            )}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

nav.run()
