"""Two-language helper for GlucoGuide (Vietnamese default, English optional)."""

import streamlit as st

LANGS = {
    "Tiếng Việt": "vi",
    "English": "en",
}

REV_LANGS = {
    "vi": "Tiếng Việt",
    "en": "English",
}

AGES_EN = [
    "18–24 years", "25–29 years", "30–34 years", "35–39 years", "40–44 years",
    "45–49 years", "50–54 years", "55–59 years", "60–64 years", "65–69 years",
    "70–74 years", "75–79 years", "80 years or older",
]

AGES_VI = [
    "18–24 tuổi", "25–29 tuổi", "30–34 tuổi", "35–39 tuổi", "40–44 tuổi",
    "45–49 tuổi", "50–54 tuổi", "55–59 tuổi", "60–64 tuổi", "65–69 tuổi",
    "70–74 tuổi", "75–79 tuổi", "Từ 80 tuổi trở lên",
]


def repair_text(value):
    text = value
    for _ in range(3):
        try:
            candidate = text.encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if candidate == text:
            break
        text = candidate
    return text


def lang() -> str:
    if "sb_lang_radio" in st.session_state and st.session_state["sb_lang_radio"] in ("vi", "en"):
        st.session_state["lang"] = st.session_state["sb_lang_radio"]
    elif "lang_label" in st.session_state and st.session_state["lang_label"] in LANGS:
        st.session_state["lang"] = LANGS[st.session_state["lang_label"]]
    return st.session_state.get("lang", "vi")


get_current_lang = lang


def pick_language():
    if "lang" not in st.session_state:
        st.session_state["lang"] = "vi"

    cur_lang = lang()
    lbl = "NGÔN NGỮ" if cur_lang == "vi" else "LANGUAGE"
    st.sidebar.markdown(f'<div class="sb-section-lbl">{lbl}</div>', unsafe_allow_html=True)
    with st.sidebar.container(key="sb_lang_seg"):
        chosen = st.radio(
            "sb_lang_select_hidden",
            options=["vi", "en"],
            format_func=lambda v: "Tiếng Việt" if v == "vi" else "English",
            index=0 if cur_lang == "vi" else 1,
            horizontal=True,
            key="sb_lang_radio",
            label_visibility="collapsed",
        )
        if chosen != cur_lang:
            st.session_state["lang"] = chosen
            st.session_state["lang_label"] = REV_LANGS[chosen]
            st.rerun()


def t(key, **kw):
    s = TEXT[key][lang()]
    return s.format(**kw) if kw else s


def age_labels():
    return AGES_VI if lang() == "vi" else AGES_EN


def health_labels():
    return [t("h1"), t("h2"), t("h3"), t("h4"), t("h5")]


def factor_name(f):
    return t("f_" + f)


TEXT = {
    "disclaimer": {
        "vi": "Công cụ phục vụ mục đích giáo dục, không dùng trong chẩn đoán lâm sàng.",
        "en": "Educational tool, not for clinical diagnosis.",
    },
    "yes": {"vi": "Có", "en": "Yes"},
    "no": {"vi": "Không", "en": "No"},
    "unknown": {"vi": "Không rõ", "en": "Unknown"},
    "h1": {"vi": "Rất tốt (Xuất sắc)", "en": "Excellent"},
    "h2": {"vi": "Tốt", "en": "Very good"},
    "h3": {"vi": "Bình thường", "en": "Good"},
    "h4": {"vi": "Hơi yếu", "en": "Fair"},
    "h5": {"vi": "Kém", "en": "Poor"},
    "f_Age": {"vi": "Độ tuổi", "en": "Age group"},
    "f_BMI": {"vi": "Chỉ số BMI (chiều cao / cân nặng)", "en": "BMI (weight for height)"},
    "f_HighBP": {"vi": "Huyết áp cao", "en": "High blood pressure"},
    "f_HighChol": {"vi": "Mỡ máu (Cholesterol) cao", "en": "High cholesterol"},
    "f_GenHlth": {"vi": "Tự đánh giá sức khỏe", "en": "Self-rated health"},
    "f_Smoker": {"vi": "Tiền sử hút thuốc", "en": "Smoking history"},
    "f_PhysActivity": {"vi": "Vận động thể chất", "en": "Leisure-time activity"},
    "f_DiffWalk": {"vi": "Khó khăn khi đi bộ", "en": "Walking difficulty"},
}
