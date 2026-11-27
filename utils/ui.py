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


def get_eiu_logo_data_uri(lang_code: str = "vi") -> str | None:
    if lang_code == "vi":
        return load_image_data_uri((
            "assets/eiu_logo_vi.png",
            "assets/eiu_logo_vi.jpg",
            "assets/eiu_logo.png",
            "assets/eiu_logo.jpg",
        ))
    return load_image_data_uri((
        "assets/eiu_logo_en.png",
        "assets/eiu_logo_en.jpg",
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
    """Hiển thị trực tiếp 2 ảnh logo tách riêng theo ngôn ngữ VI / EN trong thư mục assets."""
    logo_uri = get_eiu_logo_data_uri(lang_code)
    if not logo_uri:
        return '<div style="color:#FFFFFF;font-weight:800;font-size:1.2rem;">EIU</div>'

    alt_text = "Đại học Quốc tế Miền Đông" if lang_code == "vi" else "Eastern International University"
    return (
        f'<img src="{logo_uri}" alt="{alt_text}" class="sb-logo-img" '
        f'style="width:100%;max-width:268px;height:105px;display:block;margin:0 auto;object-fit:contain;" />'
    )


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
<circle cx="130" cy="115" r="2.8" fill="#1E293B
