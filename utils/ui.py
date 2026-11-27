import base64
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent


def _repair_text(value: str) -> str:
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


def tr(vi: str, en: str) -> str:
    from utils.i18n import get_current_lang
    cur_lang = get_current_lang()
    return _repair_text(vi) if cur_lang == "vi" else _repair_text(en)


def html(s: str) -> None:
    st.markdown("\n".join(l.strip() for l in s.splitlines() if l.strip()), unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_image_data_uri(candidates: tuple[str, ...]) -> str | None:
    for rel in candidates:
        p = ROOT / rel
        if p.exists() and p.is_file():
            ext = p.suffix.lower().lstrip(".")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext
            b64 = base64.b64encode(p.read_bytes()).decode("ascii")
            return f"data:image/{mime};base64,{b64}"
    return None


def get_doctor_data_uri() -> str | None:
    return load_image_data_uri((
        "assets/doctor_photo.png",
        "assets/doctor_photo.jpg",
        "assets/doctor.png",
        "assets/doctor.jpg",
    ))


def get_eiu_logo_data_uri() -> str | None:
    return load_image_data_uri((
        "assets/eiu_logo.png",
        "assets/eiu_logo.jpg",
    ))


def _svg_mask_css(selector: str, svg_raw: str) -> str:
    encoded = base64.b64encode(svg_raw.encode("utf-8")).decode("ascii")
    url = f"data:image/svg+xml;base64,{encoded}"
    return f"""
    {selector} [data-testid="stPageLink-NavLink"]::before {{
        content: "" !important;
        display: inline-block !important;
        width: 19px !important;
        height: 19px !important;
        min-width: 19px !important;
        flex: 0 0 19px !important;
        margin-right: 10px !important;
        background-color: currentColor !important;
        -webkit-mask-image: url('{url}') !important;
        mask-image: url('{url}') !important;
        -webkit-mask-repeat: no-repeat !important;
        mask-repeat: no-repeat !important;
        -webkit-mask-position: center !important;
        mask-position: center !important;
        -webkit-mask-size: contain !important;
        mask-size: contain !important;
    }}
    """


NAV_HOME_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
NAV_ASSESS_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
NAV_RESULT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="7" rx="1"/><rect x="12" y="6" width="3" height="11" rx="1"/><rect x="17" y="13" width="3" height="4" rx="1"/></svg>'
NAV_ABOUT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
NAV_TEACHER_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>'


def get_eiu_logo_bilingual_svg(lang_code: str = "vi") -> str:
    """Dùng trực tiếp ảnh assets/eiu_logo.png, tự động cắt khoảng trống và chuyển ngữ VI / EN."""
    logo_uri = get_eiu_logo_data_uri()
    if not logo_uri:
        return '<div style="color:#FFFFFF;font-weight:800;font-size:1.2rem;">EIU</div>'

    if lang_code == "vi":
        return f'''<div style="width:100%;max-width:255px;height:86px;overflow:hidden;position:relative;margin:0 auto;">
  <img src="{logo_uri}" alt="EIU Logo VI"
       style="width:740px !important;max-width:none !important;height:auto !important;position:absolute;top:-2px;left:50%;transform:translateX(-50%);display:block;"/>
</div>'''
    else:
        return f'''<div style="width:100%;max-width:255px;height:88px;overflow:hidden;position:relative;margin:0 auto;">
  <div style="width:100%;height:43px;overflow:hidden;position:relative;">
    <img src="{logo_uri}" alt="EIU Top"
         style="width:740px !important;max-width:none !important;height:auto !important;position:absolute;top:-2px;left:50%;transform:translateX(-50%);display:block;"/>
  </div>
  <div style="width:100%;height:45px;overflow:hidden;position:relative;">
    <img src="{logo_uri}" alt="EIU Bottom EN"
         style="width:740px !important;max-width:none !important;height:auto !important;position:absolute;top:-92px;left:50%;transform:translateX(-50%);display:block;"/>
  </div>
</div>'''


EIU_LOGO_TRANSPARENT_SVG = get_eiu_logo_bilingual_svg("vi")
EIU_LOGO_SVG = EIU_LOGO_TRANSPARENT_SVG

HEART_PULSE_SVG = '''<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H9.5l1.5-3 2 6 1.5-3h5.27"/></svg>'''

SHIELD_PLUS_SVG = '''<svg viewBox="0 0 64 64" width="54" height="54" fill="none"><path d="M32 6L10 15v17c0 14.5 9.4 24.4 22 28 12.6-3.6 22-13.5 22-28V15L32 6z" fill="#3B82F6"/><path d="M32 11L15 18v14c0 11.4 7.2 19.3 17 22.4 9.8-3.1 17-11 17-22.4V18L32 11z" fill="#60A5FA" opacity="0.35"/><rect x="29" y="22" width="6" height="20" rx="2" fill="#FFFFFF"/><rect x="22" y="29" width="20" height="6" rx="2" fill="#FFFFFF"/></svg>'''

GLUCOMETER_SVG = '''<svg viewBox="0 0 320 280" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:270px">
<defs>
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#3B82F6"/>
        <stop offset="100%" stop-color="#1D4ED8"/>
    </linearGradient>
</defs>
<rect x="90" y="34" width="140" height="200" rx="30" fill="url(#blueGrad)"/>
<rect x="106" y="52" width="108" height="74" rx="14" fill="#FFFFFF"/>
<text x="160" y="102" text-anchor="middle" font-size="40" font-weight="800" fill="#142D4E" font-family="Plus Jakarta Sans,sans-serif">96</text>
<text x="160" y="118" text-anchor="middle" font-size="10" font-weight="700" fill="#64748B" font-family="Plus Jakarta Sans,sans-serif">mg / dL</text>
<circle cx="124" cy="66" r="4" fill="#16A34A"/>
<circle cx="160" cy="174" r="16" fill="#EFF6FF"/>
<circle cx="160" cy="174" r="8" fill="#1D4ED8"/>
<circle cx="128" cy="174" r="7" fill="#93C5FD"/>
<circle cx="192" cy="174" r="7" fill="#93C5FD"/>
<rect x="142" y="229" width="36" height="30" rx="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/>
<line x1="160" y1="239" x2="160" y2="254" stroke="#DC2626" stroke-width="3" stroke-linecap="round"/>
</svg>'''

DOCTOR_SVG = '''<svg viewBox="0 0 240 280" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:230px">
<circle cx="120" cy="140" r="110" fill="#EFF6FF"/>
<path d="M60 280v-75c0-28 26-42 60-42s60 14 60 42v75z" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="2"/>
<path d="M100 163l20 38 20-38z" fill="#DBEAFE"/>
<path d="M110 163l10 26 10-26" fill="#1D4ED8"/>
<rect x="110" y="138" width="20" height="24" rx="8" fill="#F8D7C4"/>
<circle cx="120" cy="115" r="32" fill="#FCE9DE"/>
<path d="M88 108c-4-40 20-56 32-56 22 0 40 18 30 64-10-6-16-10-34-10s-22 2-28 2z" fill="#2C2420"/>
<circle cx="110" cy="115" r="2.8" fill="#1E293B"/>
<circle cx="130" cy="115" r="2.8" fill="#1E293B"/>
<path d="M114 126q6 6 12 0" stroke="#DC2626" stroke-width="2" fill="none" stroke-linecap="round"/>
<path d="M96 166c-10 26-2 44 24 44s30-20 20-44" stroke="#1E40AF" stroke-width="4" fill="none" stroke-linecap="round"/>
<circle cx="120" cy="210" r="7" fill="#1D4ED8"/>
<circle cx="120" cy="210" r="3" fill="#FFFFFF"/>
</svg>'''

FLOW_ARROWS_SVG = '''<svg viewBox="0 0 36 20" width="32" height="20" fill="none" stroke="#2563EB" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" style="display:block;margin:0 auto">
  <path d="M5 4l5 6-5 6" class="flow-ch-1"/>
  <path d="M14 4l5 6-5 6" class="flow-ch-2"/>
  <path d="M23 4l5 6-5 6" class="flow-ch-3"/>
</svg>'''


def style() -> None:
    nav_masks = (
        _svg_mask_css('[class*="st-key-nav_home_"]', NAV_HOME_SVG)
        + _svg_mask_css('[class*="st-key-nav_assess_"]', NAV_ASSESS_SVG)
        + _svg_mask_css('[class*="st-key-nav_results_"]', NAV_RESULT_SVG)
        + _svg_mask_css('[class*="st-key-nav_about_"]', NAV_ABOUT_SVG)
        + _svg_mask_css('[class*="st-key-nav_teacher_"]', NAV_TEACHER_SVG)
    )

    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {{
    --primary-blue: #1D4ED8;
    --primary-bright: #2563EB;
    --deep-navy: #142D4E;
    --sidebar-top: #183E7D;
    --sidebar-bottom: #0F2958;
    --bg-slate: #EEF4FB;
    --text-primary: #172B4D;
    --text-secondary: #5B6B82;
    --border-subtle: #DCE5F2;
    --border-card: #E2EAF4;
}}

.stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
}}

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background-color: var(--bg-slate) !important;
    color: var(--text-primary);
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
}}

.block-container {{
    max-width: 1120px;
    padding-top: 1.4rem !important;
    padding-bottom: 3rem !important;
}}

h1, h2, h3 {{
    color: var(--deep-navy) !important;
    letter-spacing: -0.02em;
}}

/* ============ SIDEBAR ============ */
section[data-testid="stSidebar"] {{
    min-width: 300px !important;
    width: 300px !important;
}}
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
[data-testid="stSidebarContent"] {{
    background: linear-gradient(180deg, var(--sidebar-top) 0%, var(--sidebar-bottom) 100%) !important;
    border-right: none !important;
}}
[data-testid="stSidebarHeader"] {{
    padding: 0.55rem 0.8rem 0.1rem 0.8rem !important;
    height: auto !important;
    min-height: 0 !important;
}}
[data-testid="stSidebarUserContent"] {{
    padding-top: 0.25rem !important;
}}
section[data-testid="stSidebar"] * {{
    color: #F1F5F9;
}}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {{
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}}

.sb-logo-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.45rem 0.1rem 0.35rem 0.1rem;
    margin-top: 0.1rem;
    margin-bottom: 0.35rem;
    width: 100%;
}}
.sb-logo-wrap svg,
.sb-logo-img {{
    width: 100% !important;
    max-width: 268px !important;
    height: auto !important;
    display: block !important;
    object-fit: contain;
}}

.sb-brand-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.45rem 0.1rem 0.85rem 0.1rem;
    margin: 0.35rem 0 0.75rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}}
.sb-brand-name {{
    font-size: 1.32rem;
    font-weight: 800;
    color: #FFFFFF !important;
    letter-spacing: -0.02em;
}}
.sb-section-lbl {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #93C5FD !important;
    margin: 0.95rem 0 0.4rem 0;
}}

/* Sidebar Nav Links */
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    border-radius: 11px !important;
    padding: 0.62rem 0.85rem !important;
    margin: 3px 0 !important;
    color: #DBEAFE !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    background: transparent !important;
    transition: all 0.15s ease;
    text-decoration: none !important;
}}
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p,
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] span {{
    color: inherit !important;
    font-weight: inherit !important;
}}
section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
    background: rgba(255, 255, 255, 0.11) !important;
    color: #FFFFFF !important;
}}
[class*="st-key-nav_"][class*="_active"] [data-testid="stPageLink-NavLink"] {{
    background: #2554A3 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.16);
}}
{nav_masks}

/* Hide duplicate radio widget label */
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[class*="st-key-sb_lang_seg"] [data-testid="stWidgetLabel"],
[class*="st-key-sb_mode_seg"] [data-testid="stWidgetLabel"],
[class*="st-key-sb_"] [data-testid="stWidgetLabel"] {{
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    visibility: hidden !important;
    overflow: hidden !important;
}}

/* Segmented Radio in Sidebar - Spacious & Never cramped */
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] div[role="radiogroup"],
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] div[role="radiogroup"],
[class*="st-key-sb_"] div[data-testid="stRadio"] div[role="radiogroup"],
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] > div,
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] > div,
[class*="st-key-sb_"] div[data-testid="stRadio"] > div {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 6px !important;
    background: rgba(255, 255, 255, 0.12) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 13px !important;
    padding: 4px !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label,
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label,
[class*="st-key-sb_"] div[data-testid="stRadio"] div[role="radiogroup"] label {{
    flex: 1 1 50% !important;
    width: 50% !important;
    min-width: 0 !important;
    margin: 0 !important;
    padding: 9px 10px !important;
    border-radius: 10px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    background: transparent !important;
    border: none !important;
    box-sizing: border-box !important;
}}
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child,
[class*="st-key-sb_"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {{
    display: none !important;
}}
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label p,
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label p,
[class*="st-key-sb_"] div[data-testid="stRadio"] div[role="radiogroup"] label p {{
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    color: #DBEAFE !important;
    margin: 0 !important;
    white-space: nowrap !important;
    letter-spacing: -0.01em !important;
    text-overflow: clip !important;
    overflow: visible !important;
    text-align: center !important;
}}
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked),
[class*="st-key-sb_"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {{
    background: #FFFFFF !important;
    box-shadow: 0 1px 4px rgba(15, 41, 88, 0.25) !important;
}}
[class*="st-key-sb_lang_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
[class*="st-key-sb_mode_seg"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
[class*="st-key-sb_"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p {{
    color: #142D4E !important;
    font-weight: 700 !important;
}}

/* Sidebar Disclaimer */
.sb-note {{
    display: flex;
    gap: 8px;
    align-items: flex-start;
    background: rgba(255, 255, 255, 0.09);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 0.76rem;
    line-height: 1.45;
    margin-top: 1.25rem;
}}
.sb-note span {{
    color: #E2E8F0 !important;
}}

/* ============ BUTTONS & INPUTS ============ */
div.stButton > button[kind="primary"] {{
    background-color: var(--primary-bright) !important;
    color: #FFFFFF !important;
    border: 0 !important;
    border-radius: 999px !important;
    min-height: 44px !important;
    font-weight: 600 !important;
    padding: 0 1.6rem !important;
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25) !important;
}}
div.stButton > button[kind="primary"]:hover {{
    background-color: var(--primary-blue) !important;
}}
div.stButton > button[kind="secondary"] {{
    background-color: #FFFFFF !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 999px !important;
    min-height: 42px !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}}
div.stButton > button[kind="secondary"]:hover {{
    border-color: var(--primary-bright) !important;
    color: var(--primary-bright) !important;
    background-color: #EFF6FF !important;
}}

/* ============ HERO & HOW IT WORKS ============ */
.st-key-home_hero {{
    background: #FFFFFF !important;
    border: 1px solid var(--border-card) !important;
    border-radius: 20px !important;
    padding: 2.2rem 2.6rem 2.2rem 2.6rem !important;
    box-shadow: 0 4px 20px rgba(20, 45, 78, 0.03) !important;
    overflow: hidden !important;
}}
.brand-title {{
    font-size: 2.85rem;
    font-weight: 800;
    color: var(--deep-navy);
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0 0 0.65rem 0;
}}
.brand-subtitle {{
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.35;
    color: var(--deep-navy);
    margin: 0 0 0.75rem 0;
}}
.brand-lead {{
    color: var(--text-secondary);
    font-size: 0.96rem;
    line-height: 1.6;
    max-width: 32rem;
    margin-bottom: 1.5rem;
}}
.hero-doctor-container {{
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
}}
.doctor-speech-bubble {{
    background: #F0F7FF;
    border: 1.5px solid #BFDBFE;
    border-radius: 16px;
    padding: 9px 13px;
    margin-bottom: 12px;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
    position: relative;
    width: 100%;
    max-width: 325px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: bubbleFloat 3.2s ease-in-out infinite;
}}
.doctor-speech-bubble:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.16);
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
    gap: 6px;
    margin-bottom: 3px;
}}
.bubble-title {{
    font-size: 0.74rem;
    font-weight: 700;
    color: #1E40AF;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    flex: 1;
}}
.bubble-sound-btn {{
    font-size: 0.72rem;
    font-weight: 600;
    color: #2563EB;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 2px 7px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    cursor: pointer;
    transition: all 0.15s ease;
}}
.bubble-sound-btn:hover {{
    background: #DBEAFE;
}}
.bubble-text {{
    font-size: 0.82rem;
    font-weight: 500;
    line-height: 1.42;
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
    max-width: 325px;
    height: auto;
    max-height: 420px;
    object-fit: cover;
    object-position: center top;
    border-radius: 24px;
    display: block;
    box-shadow: 0 10px 28px rgba(15, 40, 84, 0.12);
    border: none;
}}

/* Animated Arrow on Button */
@keyframes arrowBounceX {{
    0%, 100% {{ transform: translateX(0); }}
    50% {{ transform: translateX(6px); }}
}}
.st-key-home_hero button[kind="primary"] {{
    transition: all 0.22s ease !important;
}}
.st-key-home_hero button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(37, 84, 163, 0.35) !important;
}}
.st-key-home_hero button[kind="primary"] p::after {{
    content: " →";
    display: inline-block;
    animation: arrowBounceX 1.3s ease-in-out infinite;
    margin-left: 6px;
    font-weight: 800;
}}

.st-key-how_card {{
    background: #FFFFFF !important;
    border: 1px solid var(--border-card) !important;
    border-radius: 20px !important;
    padding: 1.5rem 2rem !important;
    box-shadow: 0 4px 18px rgba(20, 45, 78, 0.03) !important;
}}
.how-layout {{
    display: grid;
    grid-template-columns: 96px 1fr;
    gap: 1.5rem;
    align-items: center;
}}
.how-shield-box {{
    width: 90px;
    height: 90px;
    border-radius: 18px;
    background: #EFF6FF;
    border: 1px solid #DBEAFE;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.how-title {{
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--deep-navy);
    margin-bottom: 0.85rem;
}}
.how-steps {{
    display: grid;
    grid-template-columns: 1fr auto 1fr auto 1fr;
    gap: 12px;
    align-items: center;
}}
.how-step-box {{
    background: #F8FAFC;
    border: 1px solid #E8EFF8;
    border-radius: 14px;
    padding: 14px 14px;
    text-align: center;
}}
.flow-num-badge {{
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: var(--primary-bright);
    color: #FFFFFF;
    font-size: 0.78rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 6px;
}}
.how-step-txt {{
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--deep-navy);
    line-height: 1.35;
}}
.how-arrow {{
    color: #93C5FD;
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -1px;
    display: flex;
    align-items: center;
    justify-content: center;
}}

@keyframes flowChevron {{
    0%, 100% {{ opacity: 0.35; transform: translateX(-2px); }}
    50% {{ opacity: 1; transform: translateX(3px); }}
}}
.flow-ch-1 {{ animation: flowChevron 1.4s ease-in-out infinite; }}
.flow-ch-2 {{ animation: flowChevron 1.4s ease-in-out 0.22s infinite; }}
.flow-ch-3 {{ animation: flowChevron 1.4s ease-in-out 0.44s infinite; }}

@media (prefers-reduced-motion: reduce) {{
    .flow-ch-1, .flow-ch-2, .flow-ch-3 {{ animation: none; opacity: 0.9; }}
}}

.callout-blue {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 14px;
    padding: 12px 18px;
    color: #1E3A8A;
    font-size: 0.88rem;
    line-height: 1.5;
}}

.ring-card {{
    background: #FFFFFF;
    border-radius: 50%;
    width: 170px;
    height: 170px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border-subtle);
}}
.bar-row {{ display: flex; align-items: center; gap: 14px; margin: 0.75rem 0; }}
.bar-name {{ flex: 0 0 350px; font-size: 0.88rem; color: #1E293B; font-weight: 600; }}
.bar-track {{ flex: 1; height: 12px; background: #EEF2F6; border-radius: 6px; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 6px; min-width: 4px; }}
.bar-val {{ flex: 0 0 140px; text-align: right; font-weight: 700; font-size: 0.84rem; }}

@media (max-width: 860px) {{
    .how-layout {{ grid-template-columns: 1fr; }}
    .how-shield-box {{ display: none; }}
    .how-steps {{ grid-template-columns: 1fr; }}
    .how-arrow-cell {{ display: none; }}
}}
</style>""", unsafe_allow_html=True)


def ring(frac: float, text: str, color: str, sub: str) -> str:
    r = 64
    c = 6.28318 * r
    d = c * max(0.04, min(1.0, frac))
    return (
        f'<div class="ring-card">'
        f'<svg viewBox="0 0 170 170" width="160" height="160">'
        f'<circle cx="85" cy="85" r="{r}" fill="none" stroke="#E2E8F0" stroke-width="12"/>'
        f'<circle cx="85" cy="85" r="{r}" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" '
        f'stroke-dasharray="{d:.1f} {c:.1f}" transform="rotate(-90 85 85)"/>'
        f'<text x="85" y="87" text-anchor="middle" font-size="28" font-weight="800" fill="#142D4E" font-family="Plus Jakarta Sans,sans-serif">{text}</text>'
        f'<text x="85" y="108" text-anchor="middle" font-size="11" font-weight="600" fill="#64748B" font-family="Plus Jakarta Sans,sans-serif">{sub}</text>'
        f'</svg></div>'
    )


def _sweep(y_true, prob, fp_cost, fn_cost):
    rows = []
    for k in range(101):
        th = k / 100.0
        pred = (prob >= th).astype(int)
        tp = int(np.sum((y_true == 1) & (pred == 1)))
        fp = int(np.sum((y_true == 0) & (pred == 1)))
        fn = int(np.sum((y_true == 1) & (pred == 0)))
        tn = int(np.sum((y_true == 0) & (pred == 0)))
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        rows.append({
            "threshold": th,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": p, "recall": r,
            "f1": 2 * p * r / (p + r) if (p + r) else 0.0,
            "fpr": fp / (fp + tn) if (fp + tn) else 0.0,
            "penalty": fp_cost * fp + fn_cost * fn,
        })
    df = pd.DataFrame(rows)
    return df, df.loc[df["penalty"].idxmin()]


def simulator(m, _t, *, key_prefix="sim"):
    from utils.data_loader import load_validation_predictions
    y_true, prob = load_validation_predictions()
    _cost_node = m.get("costs") or m.get("cost_assumptions") or {}
    _default_fp = float(_cost_node.get("fp", _cost_node.get("FP", 1.0)))
    _default_fn = float(_cost_node.get("fn", _cost_node.get("FN", 5.0)))
    ca, cb = st.columns(2)
    fp_c = ca.number_input(
        tr("Trọng số phạt Dương tính giả (FP)", "Penalty for false alarm (FP)"),
        min_value=0.0, max_value=1000.0, value=_default_fp, step=1.0, key=f"{key_prefix}_fp",
    )
    fn_c = cb.number_input(
        tr("Trọng số phạt Âm tính giả (FN)", "Penalty for missed positive label (FN)"),
        min_value=0.0, max_value=1000.0, value=_default_fn, step=1.0, key=f"{key_prefix}_fn",
    )
    df, best = _sweep(y_true, prob, fp_c, fn_c)

    m1, m2, m3 = st.columns(3)
    m1.metric(tr("Ngưỡng tối ưu", "Cost-selected threshold"), f"{best['threshold']*100:.1f}%")
    m2.metric(tr("Thiệt hại TB / người", "Val penalty / person"), f"{best['penalty']/len(y_true):.3f}")
    m3.metric(tr("Tổng thiệt hại (Val)", "Total val penalty"), f"{best['penalty']:,.0f}")

    th = st.slider(
        tr("Thử nghiệm ngưỡng phân loại", "Try a threshold yourself"),
        0.0, 1.0, float(round(m["threshold"], 2)), 0.01, key=f"{key_prefix}_th",
    )
    row = df.iloc[(df["threshold"] - th).abs().argmin()]
    st.dataframe(
        pd.DataFrame([{
            "Threshold": f"{row['threshold']:.2f}",
            "TP": int(row["tp"]), "FP": int(row["fp"]), "FN": int(row["fn"]), "TN": int(row["tn"]),
            "Precision": f"{row['precision']:.4f}", "Recall": f"{row['recall']:.4f}",
            "F1": f"{row['f1']:.4f}", "FPR": f"{row['fpr']:.4f}", "Penalty": f"{row['penalty']:,.0f}",
        }]),
        hide_index=True, use_container_width=True,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["threshold"], y=df["recall"], name="Recall", line=dict(color="#16A34A", width=3)))
    fig.add_trace(go.Scatter(x=df["threshold"], y=df["precision"], name="Precision", line=dict(color="#1D4ED8", width=3)))
    fig.add_trace(go.Scatter(x=df["threshold"], y=df["fpr"], name="FPR", line=dict(color="#D97706", width=2.2)))
    fig.add_vline(x=float(row["threshold"]), line_dash="dash", line_color="#142D4E")
    fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=30), template="plotly_white", xaxis_title="Threshold", yaxis_title="Rate")
    st.plotly_chart(fig, use_container_width=True)


def tuned_model_threshold_explorer(m=None, _t="tuned_sim", *, key_prefix=None):
    from utils.data_loader import load_tuned_validation_predictions, load_tuned_model_validation, meta
    if m is None or isinstance(m, str):
        if isinstance(m, str):
            _t = m
        m = meta()
    if key_prefix is None:
        key_prefix = _t if isinstance(_t, str) else "tuned_sim"
    y_true, probs_by_model = load_tuned_validation_predictions()
    summary = load_tuned_model_validation()
    names = [n for n in summary["model"].tolist() if n in probs_by_model]
    if not names:
        return
    _cost_node = m.get("costs") or m.get("cost_assumptions") or {}
    _default_fp = float(_cost_node.get("fp", _cost_node.get("FP", 1.0)))
    _default_fn = float(_cost_node.get("fn", _cost_node.get("FN", 5.0)))
    chosen = st.selectbox(tr("Mô hình đánh giá", "Model to examine"), names, key=f"{key_prefix}_m")
    th = st.slider(tr("Ngưỡng mô hình", "Model threshold"), 0.0, 1.0, float(round(m["threshold"], 2)), 0.01, key=f"{key_prefix}_th")
    df, _ = _sweep(y_true, probs_by_model[chosen], _default_fp, _default_fn)
    row = df.iloc[(df["threshold"] - th).abs().argmin()]
    c1, c2, c3 = st.columns(3)
    c1.metric("Precision", f"{row['precision']*100:.1f}%")
    c2.metric("Recall", f"{row['recall']*100:.1f}%")
    c3.metric("F1-Score", f"{row['f1']:.3f}")
