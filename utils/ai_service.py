import os
from pathlib import Path
import streamlit as st
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parent.parent

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def get_api_key() -> Optional[str]:
    """Retrieve Gemini API key from session_state, secrets.toml, .env, or env vars."""
    # 1. UI session state input if user typed or saved it
    if "gemini_api_key" in st.session_state and str(st.session_state["gemini_api_key"]).strip():
        return str(st.session_state["gemini_api_key"]).strip()

    # 2. Environment variable
    env_val = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_val:
        return env_val

    # 3. Read .streamlit/secrets.toml directly from workspace
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import tomllib
            data = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
            val = str(data.get("GEMINI_API_KEY", "")).strip()
            if val and val != "your_gemini_api_key_here":
                return val
        except Exception:
            pass

    # 4. Read .streamlit/secrets.toml.example directly (in case user edited the example)
    example_path = ROOT / ".streamlit" / "secrets.toml.example"
    if example_path.exists():
        try:
            import tomllib
            data = tomllib.loads(example_path.read_text(encoding="utf-8"))
            val = str(data.get("GEMINI_API_KEY", "")).strip()
            if val and val != "your_gemini_api_key_here":
                return val
        except Exception:
            pass

    # 5. Read .env file directly if present
    env_path = ROOT / ".env"
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("GEMINI_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if k and k != "your_gemini_api_key_here":
                        return k
        except Exception:
            pass

    # 6. Streamlit secrets (with safe catch for sandbox / permission restrictions)
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass

    return None


def save_api_key(key: str):
    """Save API key to session state and persist to .streamlit/secrets.toml."""
    clean_k = (key or "").strip()
    st.session_state["gemini_api_key"] = clean_k
    st.session_state["gemini_last_error"] = None
    try:
        sec_dir = ROOT / ".streamlit"
        sec_dir.mkdir(parents=True, exist_ok=True)
        sec_file = sec_dir / "secrets.toml"
        sec_file.write_text(f'# GlucoGuide Secrets Configuration\nGEMINI_API_KEY = "{clean_k}"\n', encoding="utf-8")
    except Exception:
        pass


def _detect_lang(text: str, default_lang: Optional[str] = None) -> str:
    q = (text or "").lower()
    vi_markers = [
        "giải thích", "kết quả", "yếu tố", "ảnh hưởng", "tại sao", "làm gì",
        "bước tiếp", "của tôi", "nguy cơ", "tiểu đường", "đường huyết", "chẩn đoán",
        "ăn gì", "kiêng", "thực đơn", "thể dục", "huyết áp", "mỡ máu", "khám",
        "ă", "â", "đ", "ê", "ô", "ơ", "ư", "á", "à", "ả", "ã", "ạ",
    ]
    en_markers = ["explain", "result", "factor", "influence", "why", "next", "what should", "my ", "diet", "food", "eat"]
    if any(m in q for m in vi_markers):
        return "vi"
    if any(m in q for m in en_markers):
        return "en"
    if default_lang in ("vi", "en"):
        return default_lang
    try:
        from utils.i18n import lang
        return lang()
    except Exception:
        return "vi"


def build_system_instruction(context: Dict[str, Any], current_lang: Optional[str] = None) -> str:
    """Build grounded system prompt with user screening context."""
    prob = context.get("probability", 0.0)
    prob_pct = f"{prob * 100:.1f}%"
    threshold = context.get("threshold", 0.1693)
    risk_cat = (
        "Elevated Risk (Above Screening Threshold)"
        if prob >= threshold
        else "Low / Average Risk (Below Screening Threshold)"
    )

    factors_summary = context.get("factors_summary", "Not calculated yet.")
    user_answers = context.get("answers", {})
    lang_directive = (
        "Respond strictly in Vietnamese." if current_lang == "vi"
        else "Respond strictly in English." if current_lang == "en"
        else "Respond in the same language as the user's message (Vietnamese or English)."
    )

    return f"""You are the GlucoGuide AI Assistant, an empathetic, evidence-based digital health guide integrated into the GlucoGuide diabetes screening platform.

### CLINICAL & SCREENING CONTEXT FOR THIS USER:
- **Predicted Probability of Survey Label:** {prob_pct} ({prob:.4f})
- **Classification Threshold:** {threshold:.4f}
- **Assigned Category:** {risk_cat}
- **Top Contributing Factors (Exact Shapley Attributions):**
{factors_summary}
- **User Provided Physical & Lifestyle Responses:**
{user_answers}

### CRITICAL MEDICAL & ETHICAL DIRECTIVES:
1. **Brevity & Focus (STRICT):** Answer directly, concisely, and straight to the point. Keep responses under 100–130 words (2 to 4 bullet points or 1–2 short paragraphs). Avoid lengthy greetings, repetitive pleasantries, or reciting the entire medical background unless specifically asked.
2. **Screening vs. Diagnosis:** This tool uses an academic machine learning model (Histogram Gradient Boosting) trained on self-reported CDC BRFSS 2015 data. It is an educational screening demonstration, NOT a diagnostic medical device. Never diagnose diabetes or any other medical condition.
3. **Grounding in ML Reality:** Only discuss the user's actual factors listed above. Do not hallucinate or invent clinical metrics that were not collected.
4. **Actionable & Direct:** Give clear, practical, bulleted takeaways that are easy to understand and apply.
5. **No Prescription or Treatment:** Never prescribe medication or treatment regimens.
6. **Language:** {lang_directive}
"""


def _get_supported_models(api_key: str) -> list[tuple[str, str]]:
    """Query Google API for the exact list of supported models for this key."""
    import requests
    if "cached_gemini_models" in st.session_state and st.session_state["cached_gemini_models"]:
        return st.session_state["cached_gemini_models"]

    found = []
    # Query Google's ListModels endpoint to get available models
    for api_ver in ("v1beta", "v1"):
        try:
            r = requests.get(f"https://generativelanguage.googleapis.com/{api_ver}/models?key={api_key}", timeout=6)
            if r.status_code == 200:
                data = r.json()
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        m_name = m.get("name", "").replace("models/", "")
                        if m_name and (api_ver, m_name) not in found:
                            found.append((api_ver, m_name))
        except Exception:
            pass

    if found:
        def _sort_key(item):
            ver, name = item
            score = 100
            if "2.5-flash" in name: score = 10
            elif "2.0-flash" in name: score = 20
            elif "1.5-flash" in name: score = 30
            elif "flash" in name: score = 40
            elif "pro" in name: score = 50
            return (score, ver)
        found.sort(key=_sort_key)
        st.session_state["cached_gemini_models"] = found
        return found

    # Fallback default pairs across v1 and v1beta
    return [
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-2.0-flash"),
        ("v1", "gemini-1.5-pro"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1", "gemini-pro"),
    ]


def _call_gemini_rest(
    api_key: str,
    system_instruction: str,
    history: List[Dict[str, str]],
    user_message: str,
) -> tuple[Optional[str], Optional[str]]:
    """Call Google Gemini REST API directly using requests."""
    try:
        import requests
    except ImportError:
        return None, "Thư viện requests không khả dụng."

    contents = []
    for msg in history[-8:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg["content"]}],
        })
    contents.append({
        "role": "user",
        "parts": [{"text": user_message}],
    })

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}],
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 350,
        },
    }

    candidates_to_try = _get_supported_models(api_key)
    last_err = ""

    for api_ver, model_name in candidates_to_try:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"], None
            else:
                try:
                    err_json = resp.json()
                    last_err = err_json.get("error", {}).get("message", f"HTTP {resp.status_code}")
                except Exception:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:120]}"
        except Exception as e:
            last_err = str(e)

    return None, last_err


def _format_gemini_error(raw_err: str, lang: str = "vi") -> str:
    """Provide clean human-readable diagnostic messages."""
    s = str(raw_err)
    if "NameResolutionError" in s or "ConnectionError" in s or "getaddrinfo failed" in s:
        return (
            "Không thể kết nối mạng tới máy chủ Google (vui lòng kiểm tra kết nối Internet)"
            if lang == "vi"
            else "Cannot connect to Google API server (please check internet connection)"
        )
    if "API_KEY_INVALID" in s or "API key not valid" in s or "400" in s:
        return (
            "API Key không hợp lệ (Key của Google AI Studio thường có định dạng 'AIzaSy...')"
            if lang == "vi"
            else "Invalid API key (Google AI Studio keys usually start with 'AIzaSy...')"
        )
    if "RESOURCE_EXHAUSTED" in s or "429" in s or "quota" in s.lower():
        return (
            "Đã đạt giới hạn hạn ngạch gọi API miễn phí (Quota limit). Vui lòng thử lại sau"
            if lang == "vi"
            else "Rate limit or quota exceeded. Please try again shortly"
        )
    if "not found for API version" in s:
        return (
            "Phiên bản model không khả dụng cho tài khoản API này. Hệ thống tự động chuyển sang Cơ sở dữ liệu Y tế Nội bộ"
            if lang == "vi"
            else "Requested model is unavailable for this API account. Switched to internal knowledge base"
        )
    return s[:120]


def generate_ai_response(
    user_message: str,
    history: List[Dict[str, str]],
    context: Dict[str, Any],
    current_lang: Optional[str] = None,
) -> str:
    """Generate response using Gemini API or fallback seamlessly with transparent status."""
    active_lang = _detect_lang(user_message, current_lang)
    api_key = get_api_key()

    if not api_key:
        return get_offline_explanation(user_message, context, active_lang)

    system_instruction = build_system_instruction(context, active_lang)

    # 1. Try google.genai SDK if available
    if GENAI_AVAILABLE:
        try:
            client = genai.Client(api_key=api_key)
            contents = []
            for msg in history[-6:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])],
                    )
                )
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_message)],
                )
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,
                    max_output_tokens=350,
                ),
            )
            if response.text:
                st.session_state["gemini_last_error"] = None
                return response.text
        except Exception as e:
            st.session_state["gemini_last_error"] = str(e)

    # 2. Try REST API with requests (always available)
    rest_reply, rest_err = _call_gemini_rest(api_key, system_instruction, history, user_message)
    if rest_reply:
        st.session_state["gemini_last_error"] = None
        return rest_reply

    if rest_err:
        st.session_state["gemini_last_error"] = rest_err

    # Fallback to rich offline explanation with diagnostic note
    offline_reply = get_offline_explanation(user_message, context, active_lang)
    diag_raw = st.session_state.get("gemini_last_error")
    if diag_raw:
        friendly_err = _format_gemini_error(diag_raw, active_lang)
        if active_lang == "vi":
            note = f"> ⚠️ **Thông báo kết nối Gemini:** {friendly_err}\n> *Đang trả lời bằng Cơ sở Dữ liệu Y tế Chuyên gia GlucoGuide:*\n\n"
        else:
            note = f"> ⚠️ **Gemini Connection Notice:** {friendly_err}\n> *Answering via GlucoGuide Clinical Knowledge Base:*\n\n"
        return note + offline_reply

    return offline_reply


def get_offline_explanation(
    user_message: str,
    context: Dict[str, Any],
    current_lang: Optional[str] = None,
) -> str:
    """Bilingual local clinical explanation database when Gemini API is unavailable."""
    active_lang = _detect_lang(user_message, current_lang)
    prob = context.get("probability", 0.0)
    prob_pct = f"{prob * 100:.1f}%"
    threshold = context.get("threshold", 0.1693)
    thresh_pct = f"{threshold * 100:.1f}%"
    is_elevated = prob >= threshold
    factors = context.get("top_factors", [])
    answers = context.get("answers", {})
    bmi = float(answers.get("BMI", 0.0))

    q = (user_message or "").lower()

    if active_lang == "en":
        # 1. Result explanation
        if any(k in q for k in ["explain", "result", "meaning", "category", "why did i receive", "score"]):
            status_en = "Elevated Risk (Above Threshold)" if is_elevated else "Low / Average Risk (Below Threshold)"
            return (
                f"### Your Screening Result Breakdown\n\n"
                f"- **Predicted Model Score:** **{prob_pct}**\n"
                f"- **Classification Threshold:** {thresh_pct}\n"
                f"- **Category:** **{status_en}**\n\n"
                f"**What this means:**\n"
                f"The value {prob_pct} reflects how closely your survey profile aligns with CDC BRFSS respondents who self-reported diabetes or prediabetes. "
                f"This is a **statistical screening score**, not a medical diagnosis.\n\n"
                f"**Screening vs. Diagnosis:**\n"
                f"- *Screening:* Highlights statistical risk patterns worth discussing.\n"
                f"- *Diagnosis:* Requires clinical blood tests (such as Fasting Plasma Glucose or HbA1c) ordered by a physician."
            )

        # 2. Factors
        if any(k in q for k in ["factor", "influence", "shapley", "affect", "why", "contribute"]):
            factors_text = ""
            for f in factors:
                c = float(f.get("Contribution", 0))
                direction = "raises score" if c > 0 else "lowers score"
                factors_text += f"- **{f.get('Factor', f.get('Feature'))}:** {c:+.3f} ({direction}).\n"
            return (
                f"### Key Factors Influencing Your Score\n\n"
                f"The model uses **Exact Shapley** attribution to measure each input's contribution:\n\n"
                f"{factors_text}\n"
                f"**Important note:** These reflect statistical associations in the 2015 survey population (for example, BMI {bmi:.1f}), not direct medical causation."
            )

        # 3. Nutrition & Diet
        if any(k in q for k in ["diet", "food", "eat", "nutrition", "sugar", "carbs"]):
            return (
                "### Nutrition & Diet Guidelines\n\n"
                "1. **Prioritize high-fiber foods:** Vegetables, legumes, whole grains, and leafy greens.\n"
                "2. **Reduce refined sugars:** Avoid sweetened beverages, pastries, and processed snacks.\n"
                "3. **Portion control:** Use the plate method (50% vegetables, 25% lean protein, 25% complex carbohydrates).\n"
                "4. **Hydration:** Drink plenty of water rather than soft drinks or packaged fruit juices."
            )

        # 4. Exercise & Physical Activity
        if any(k in q for k in ["exercise", "physical activity", "workout", "sport", "walking"]):
            return (
                "### Physical Activity Recommendations\n\n"
                "1. **Target:** At least **2.5 hours per week** (about 30 mins/day) of moderate-intensity aerobic activity (e.g. brisk walking, cycling, swimming).\n"
                "2. **Resistance training:** 2–3 sessions per week to preserve muscle mass and improve insulin sensitivity.\n"
                "3. **Break up sitting:** Stand and walk for 2–3 minutes every 30–60 minutes of desk work."
            )

        # 5. Next steps
        if any(k in q for k in ["next", "what should i do", "advice", "recommend", "doctor", "test"]):
            if is_elevated:
                return (
                    "### Suggested Next Steps\n\n"
                    "1. **Consult a physician:** Schedule a routine visit with a healthcare professional.\n"
                    "2. **Discuss standard lab tests:** Ask about **HbA1c** or **Fasting Plasma Glucose** testing.\n"
                    "3. **Monitor key metrics:** Keep track of blood pressure, cholesterol, and weight.\n"
                    "4. **Healthy habits:** Favor whole foods, vegetables, and regular moderate physical activity."
                )
            return (
                "### Suggested Next Steps\n\n"
                "1. **Maintain healthy routines:** Keep up balanced meals and regular physical activity.\n"
                "2. **Routine check-ups:** Even with a lower screening score, periodic annual check-ups remain important.\n"
                "3. **Watch for symptoms:** Consult a doctor if you experience unusual thirst, frequent urination, or unexplained fatigue."
            )

        return (
            f"Hello! Your screening score is **{prob_pct}** "
            f"({'above' if is_elevated else 'below'} the {thresh_pct} threshold).\n\n"
            f"You can ask me about:\n"
            f"- *Explain my result and what it means*\n"
            f"- *Which factors influenced my score most?*\n"
            f"- *Nutrition, diet, and sugar intake*\n"
            f"- *Exercise recommendations*\n"
            f"- *What tests should I discuss with my doctor?*"
        )

    # Vietnamese responses
    # 1. Result explanation
    if any(k in q for k in ["explain", "giải thích", "kết quả", "result", "meaning", "nghĩa", "phân loại", "tại sao tôi nhận", "điểm số"]):
        status_vi = "Nguy cơ tăng cao (Trên ngưỡng sàng lọc)" if is_elevated else "Nguy cơ thấp / trung bình (Dưới ngưỡng sàng lọc)"
        return (
            f"### Phân tích Kết quả Sàng lọc của bạn\n\n"
            f"- **Xác suất mô hình dự đoán:** **{prob_pct}**\n"
            f"- **Ngưỡng sàng lọc của mô hình:** {thresh_pct}\n"
            f"- **Phân loại hiện tại:** **{status_vi}**\n\n"
            f"**Ý nghĩa lâm sàng:**\n"
            f"Con số {prob_pct} thể hiện mức độ tương đồng giữa thông tin sức khỏe của bạn với nhóm người tham gia khảo sát CDC BRFSS có tự báo cáo chẩn đoán tiểu đường. "
            f"Đây là chỉ số **sàng lọc thống kê**, không phải kết luận chẩn đoán y khoa.\n\n"
            f"**Sàng lọc và Chẩn đoán:**\n"
            f"- *Sàng lọc:* Giúp nhận diện sớm các đặc điểm nguy cơ đáng lưu tâm.\n"
            f"- *Chẩn đoán:* Đòi hỏi bác sĩ thực hiện xét nghiệm hóa sinh như đường huyết lúc đói (FPG) hoặc HbA1c."
        )

    # 2. Factors
    if any(k in q for k in ["factor", "yếu tố", "ảnh hưởng", "influence", "why", "tại sao", "đóng góp", "nguyên nhân"]):
        factors_text = ""
        for f in factors:
            c = float(f.get("Contribution", 0))
            direction = "làm tăng xác suất nguy cơ" if c > 0 else "làm giảm xác suất nguy cơ"
            factors_text += f"- **{f.get('Factor', f.get('Feature'))}:** {c:+.3f} ({direction}).\n"
        return (
            f"### Các yếu tố tác động nhiều nhất đến kết quả của bạn\n\n"
            f"Mô hình sử dụng thuật toán **Exact Shapley** để lượng hóa đóng góp của từng câu trả lời:\n\n"
            f"{factors_text}\n"
            f"**Lưu ý:** Đây là mối liên hệ thống kê trong dữ liệu khảo sát (chẳng hạn độ tuổi hay chỉ số BMI {bmi:.1f}), không phải quan hệ nhân quả trực tiếp."
        )

    # 3. Nutrition & Diet
    if any(k in q for k in ["ăn gì", "kiêng", "thực đơn", "chế độ ăn", "dinh dưỡng", "đường", "trái cây", "cơm", "tinh bột", "uống"]):
        return (
            "### Hướng dẫn Dinh dưỡng & Ăn uống Dự phòng\n\n"
            "1. **Tăng cường chất xơ hòa tan:** Ăn nhiều rau xanh (rau cải, bông cải, rau muống), đậu hạt và ngũ cốc nguyên cám. Chất xơ giúp làm chậm hấp thu đường vào máu.\n"
            "2. **Hạn chế đường hấp thu nhanh:** Giảm tối đa nước ngọt có gas, trà sữa, bánh kẹo, siro và nước ép trái cây đóng hộp.\n"
            "3. **Kiểm soát khẩu phần tinh bột:** Ưu tiên gạo lứt, khoai lang, yến mạch thay cho tinh bột tinh chế; chia đều lượng tinh bột trong các bữa ăn.\n"
            "4. **Chất béo lành mạnh:** Dùng dầu thực vật (dầu ô liu, dầu đậu nành), mỡ cá (cá hồi, cá thu) thay cho mỡ động vật và đồ chiên rán nhiều lần."
        )

    # 4. Exercise & Physical Activity
    if any(k in q for k in ["vận động", "thể dục", "tập thể dục", "thể thao", "chạy bộ", "đi bộ", "gym"]):
        return (
            "### Khuyến nghị Vận động Thể chất\n\n"
            "1. **Thời lượng:** Duy trì ít nhất **2.5 giờ mỗi tuần** vận động cường độ vừa (như đi bộ nhanh, bơi lội, đạp xe, yoga) — chia đều 30 phút/ngày, 5 ngày/tuần.\n"
            "2. **Tập kháng lực:** Bổ sung bài tập cơ bắp 2 lần/tuần để tăng cường khối cơ, giúp cơ thể sử dụng insulin hiệu quả hơn.\n"
            "3. **Giảm thời gian ngồi yên:** Cứ sau mỗi 45–60 phút ngồi làm việc, hãy đứng dậy đi lại thư giãn 2–3 phút."
        )

    # 5. Blood Pressure & Cholesterol
    if any(k in q for k in ["huyết áp", "mỡ máu", "cholesterol", "tim mạch", "cao huyết áp"]):
        return (
            "### Mối liên hệ giữa Huyết áp, Mỡ máu và Đái tháo đường\n\n"
            "1. **Hội chứng chuyển hóa:** Huyết áp cao, rối loạn mỡ máu và kháng insulin thường đi kèm với nhau, làm tăng gấp bội nguy cơ biến cố tim mạch.\n"
            "2. **Mục tiêu huyết áp:** Thường được khuyến cáo duy trì dưới **130/80 mmHg** (theo hướng dẫn của bác sĩ).\n"
            "3. **Kiểm soát:** Giảm lượng muối ăn (< 5g muối/ngày), hạn chế rượu bia, tăng cường rau củ và tái khám tim mạch định kỳ."
        )

    # 6. Diagnosis & Next steps
    if any(k in q for k in ["next", "làm gì", "bước tiếp theo", "what should i do", "advice", "lời khuyên", "khám", "xét nghiệm", "bác sĩ"]):
        if is_elevated:
            return (
                "### Khuyến nghị các bước tiếp theo\n\n"
                "1. **Thăm khám y tế:** Sắp xếp lịch khám với bác sĩ đa khoa hoặc chuyên khoa nội tiết.\n"
                "2. **Xét nghiệm máu kiểm tra:** Trao đổi với bác sĩ về xét nghiệm **HbA1c** hoặc **Đường huyết lúc đói (FPG)**.\n"
                "3. **Theo dõi chỉ số:** Kiểm soát huyết áp, mỡ máu và cân nặng định kỳ.\n"
                "4. **Duy trì lối sống lành mạnh:** Tăng cường rau xanh, hạn chế đường tinh luyện và vận động đều đặn."
            )
        return (
            "### Khuyến nghị duy trì sức khỏe\n\n"
            "1. **Tiếp tục thói quen tốt:** Duy trì chế độ ăn cân bằng và vận động thể chất thường xuyên.\n"
            "2. **Khám sức khỏe định kỳ:** Điểm sàng lọc thấp không loại trừ hoàn toàn nguy cơ, bạn vẫn nên kiểm tra tổng quát hàng năm.\n"
            "3. **Theo dõi dấu hiệu cơ thể:** Nếu thấy khát nhiều, tiểu nhiều hoặc mệt mỏi bất thường, hãy đi khám sớm."
        )

    # 7. Symptoms
    if any(k in q for k in ["triệu chứng", "dấu hiệu", "biểu hiện", "khát", "tiểu nhiều", "sút cân", "mệt mỏi"]):
        return (
            "### Các Dấu hiệu Cảnh báo Sớm Cần Lưu ý\n\n"
            "- Thường xuyên cảm thấy rất khát dù uống nhiều nước.\n"
            "- Đi tiểu nhiều lần, đặc biệt là vào ban đêm.\n"
            "- Sút cân nhanh không rõ nguyên nhân dù ăn uống bình thường.\n"
            "- Cảm giác mệt mỏi mạn tính, kiệt sức không hồi phục sau khi ngủ.\n"
            "- Vết thương, vết trầy xước lâu lành hoặc dễ bị nhiễm trùng da.\n\n"
            "👉 *Nếu bạn đang gặp phải các triệu chứng trên, hãy tới cơ sở y tế để được bác sĩ chỉ định xét nghiệm đường huyết sớm nhất.*"
        )

    # Default fallback prompt with suggestions
    return (
        f"Xin chào! Điểm sàng lọc hiện tại của bạn là **{prob_pct}** "
        f"({'trên' if is_elevated else 'dưới'} ngưỡng {thresh_pct}).\n\n"
        f"Tôi là Trợ lý Y tế ảo GlucoGuide. Bạn có thể hỏi tôi bất kỳ câu hỏi nào về:\n"
        f"- *Giải thích chi tiết kết quả {prob_pct} và phân loại của bạn*\n"
        f"- *Các yếu tố nào đang tác động nhiều nhất đến nguy cơ?*\n"
        f"- *Chế độ ăn uống, dinh dưỡng và lượng đường nên dùng*\n"
        f"- *Kế hoạch vận động thể chất phù hợp*\n"
        f"- *Mối liên hệ giữa huyết áp, mỡ máu và tiểu đường*\n"
        f"- *Các xét nghiệm y tế cần làm khi đi khám bác sĩ*"
    )
