import base64
import io
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
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


@st.cache_data(show_spinner=False)
def get_eiu_logo_data_uri() -> str | None:
    """Đọc assets/eiu_logo.png, tự động xóa nền (trắng/đen) thành trong suốt RGBA."""
    for rel in ("assets/eiu_logo.png", "assets/eiu_logo.jpg"):
        p = ROOT / rel
        if p.exists() and p.is_file():
            img = Image.open(p).convert("RGBA")
            w, h = img.size
            pixels = img.load()

            corners = [
                pixels[0, 0],
                pixels[w - 1, 0],
                pixels[0, h - 1],
                pixels[w - 1, h - 1],
            ]
            bg_r = sum(c[0] for c in corners) // 4
            bg_g = sum(c[1] for c in corners) // 4
            bg_b = sum(c[2] for c in corners) // 4

            new_data = []
            tolerance = 35
            for r, g, b, a in img.getdata():
                if a == 0 or (
                    abs(r - bg_r) < tolerance
                    and abs(g - bg_g) < tolerance
                    and abs(b - bg_b) < tolerance
                ):
                    new_data.append((0, 0, 0, 0))
                else:
                    new_data.append((r, g, b, a))

            img.putdata(new_data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            return f"data:image/png;base64,{b64}"
    return None


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
    """Dùng ảnh eiu_logo.png đã xóa nền kết hợp tên trường chuyển ngữ động VI / EN."""
    logo_uri = get_eiu_logo_data_uri()
    if lang_code == "vi":
        line1 = "TRƯỜNG ĐẠI HỌC QUỐC TẾ"
        line2 = "MIỀN ĐÔNG"
        sub_size = "11.6"
    else:
        line1 = "EASTERN INTERNATIONAL"
        line2 = "UNIVERSITY"
        sub_size = "11.4"

    if logo_uri:
        return f'''<div style="display:flex;align-items:center;gap:10px;width:100%;">
  <img src="{logo_uri}" alt="EIU Logo" style="width:76px !important;max-width:76px !important;height:auto !important;flex:0 0 76px;object-fit:contain;display:block;"/>
  <div style="display:flex;flex-direction:column;justify-content:center;line-height:1.28;text-align:left;">
    <span style="font-size:0.74rem;font-weight:800;color:#E2E8F0;letter-spacing:0.02em;">{line1}</span>
    <span style="font-size:0.74rem;font-weight:800;color:#CBD5E1;letter-spacing:0.03em;">{line2}</span>
  </div>
</div>'''

    return f'''<svg viewBox="0 0 268 88" style="width:100%;max-width:268px;height:auto;display:block;" fill="none" xmlns="http://www.w3.org/2000/svg">
  <g transform="translate(2, 10) scale(1.36)">
    <rect x="14" y="2" width="16" height="4.5" rx="2.2" fill="#D4B475"/>
    <rect x="6" y="9" width="14" height="4.5" rx="2.2" fill="#93C5FD"/>
    <rect x="23" y="9" width="16" height="4.5" rx="2.2" fill="#D4B475"/>
    <rect x="2" y="16" width="22" height="4.5" rx="2.2" fill="#D4B475"/>
    <rect x="27" y="16" width="16" height="4.5" rx="2.2" fill="#93C5FD"/>
    <rect x="1" y="23" width="15" height="4.5" rx="2.2" fill="#93C5FD"/>
    <rect x="19" y="23" width="25" height="4.5" rx="2.2" fill="#D4B475"/>
    <rect x="3" y="30" width="21" height="4.5" rx="2.2" fill="#D4B475"/>
    <rect x="27" y="30" width="14" height="4.5" rx="2.2" fill="#93C5FD"/>
    <rect x="8" y="37" width="14" height="4.5" rx="2.2" fill="#93C5FD"/>
    <rect x="24" y="37" width="11" height="4.5" rx="2.2" fill="#D4B475"/>
    <rect x="15" y="44" width="15" height="4.5" rx="2.2" fill="#D4B475"/>
  </g>
  <text x="74" y="38" fill="#FFFFFF" font-family="'Plus Jakarta Sans', Arial, sans-serif" font-weight="800" font-size="33" letter-spacing="1.2">EIU</text>
  <text x="74" y="57" fill="#E2E8F0" font-family="'Plus Jakarta Sans', Arial, sans-serif" font-weight="700" font-size="{sub_size}" letter-spacing="0.25">{line1}</text>
  <text x="74" y="73" fill="#CBD5E1" font-family="'Plus Jakarta Sans', Arial, sans-serif" font-weight="700" font-size="{sub_size}" letter-spacing="0.3">{line2}</text>
</svg>'''


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
    justify-content: flex-start;
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
    font-size:
