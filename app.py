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
  * {{ box-sizing: border-box; font-family: 'Plus Jakarta Sans', -apple-system, sans-serif; }}
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
