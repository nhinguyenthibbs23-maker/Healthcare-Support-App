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

    return f"""You are Dr. Nguyen Hoai Duc (Bác sĩ Nguyễn Hoài Đức), an empathetic, evidence-based digital health guide integrated into the GlucoGuide diabetes screening platform.

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
            else "Invalid API key (Google AI Studio keys usually start with 'AIzaSy
