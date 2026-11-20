import math
import re
import unicodedata
from pathlib import Path
import urllib.parse
import pandas as pd
import requests
import streamlit as st
from utils.ui import tr

ROOT = Path(__file__).resolve().parent.parent
PROVINCES_CSV_PATH = ROOT / "data" / "provinces_34.csv"
HEADERS = {"User-Agent": "GlucoGuide-HealthScreening/1.0 (contact: support@glucoguide.edu.vn)"}


def _clean_html(raw: str) -> str:
    """Strip leading indentation and blank lines so CommonMark never renders HTML as a code block."""
    return "\n".join(line.strip() for line in raw.splitlines() if line.strip())


def _is_en() -> bool:
    return st.session_state.get("lang", "vi") == "en"


def _to_ascii_en(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return s
    s = s.replace("Đ", "D").replace("đ", "d")
    s = re.sub(r"\bPhường\s+(\d+)\b", r"Ward \1", s)
    s = re.sub(r"\bPhường\s+([^,]+)", r"\1 Ward", s)
    s = re.sub(r"\bQuận\s+(\d+)\b", r"District \1", s)
    s = re.sub(r"\bQuận\s+([^,]+)", r"\1 District", s)
    s = re.sub(r"\bHuyện\s+([^,]+)", r"\1 District", s)
    s = re.sub(r"\bĐường\s+([^,]+)", r"\1 St.", s)
    s = s.replace("TP.HCM", "HCMC").replace("TP. Hồ Chí Minh", "Ho Chi Minh City").replace("Hà Nội", "Hanoi")
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# Crisp inline SVG icons (no emojis)
SVG_PIN = (
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#1D4ED8" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 18px;">'
    '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
    '<circle cx="12" cy="10" r="3"/>'
    '</svg>'
)

SVG_PIN_SM = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#5B6B82" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;margin-top:2px;">'
    '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
    '<circle cx="12" cy="10" r="3"/>'
    '</svg>'
)

SVG_HOSPITAL = (
    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#1D4ED8" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 15px;">'
    '<path d="M12 6v4"/><path d="M14 14h-4"/><path d="M14 18h-4"/><path d="M14 8h-4"/>'
    '<path d="M18 12h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h2"/>'
    '<path d="M18 22V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v18"/>'
    '</svg>'
)

SVG_CLINIC = (
    '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="#16A34A" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 15px;">'
    '<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/>'
    '<path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/>'
    '<circle cx="20" cy="10" r="2"/>'
    '</svg>'
)

SVG_STAR = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#B45309" '
    'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;">'
    '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>'
    '</svg>'
)

SVG_LAB = (
    '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#0F766E" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 13px;margin-top:2px;">'
    '<path d="M9 3h6"/><path d="M10 9h4"/><path d="M10 3v6L5 20a1 1 0 0 0 .9 1.5h12.2a1 1 0 0 0 .9-1.5L14 9V3"/>'
    '</svg>'
)

SVG_PHONE = (
    '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#5B6B82" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 13px;">'
    '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
    '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
    '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>'
    '</svg>'
)

SVG_NAV_ARROW = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#FFFFFF" '
    'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 14px;">'
    '<polygon points="3 11 22 2 13 21 11 13 3 11"/>'
    '</svg>'
)

SVG_MAP_HEADER = (
    '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#142D4E" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 16px;">'
    '<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>'
    '<line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>'
    '</svg>'
)


@st.cache_data(show_spinner=False)
def load_clinics_csv() -> pd.DataFrame:
    """Load the hierarchical Province/City -> District/County diabetes testing facilities CSV."""
    if PROVINCES_CSV_PATH.exists():
        df = pd.read_csv(PROVINCES_CSV_PATH, encoding="utf-8-sig")
        for col in [
            "Tinh_Thanh_Moi",
            "Tinh_Thanh_Moi_EN",
            "Nhan_Hien_Thi",
            "Nhan_Hien_Thi_EN",
            "Tinh_Cu_Sap_Nhap",
            "Quan_Huyen",
            "Quan_Huyen_EN",
            "Ten_Benh_Vien",
            "Ten_Benh_Vien_EN",
            "Dia_Chi",
            "Dia_Chi_EN",
            "Loai_Co_So",
            "Loai_Co_So_EN",
            "Dich_Vu_Xet_Nghiem",
            "Dich_Vu_Xet_Nghiem_EN",
            "Tu_Khoa_Google_Maps",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        return df
    return pd.DataFrame()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data(ttl=3600, show_spinner=False)
def geocode_location(query: str) -> tuple[float, float, str] | None:
    """Resolve province/district/city into real (lat, lon) via Nominatim."""
    q_clean = query.strip()
    if not q_clean:
        return None
    search_q = q_clean if "vietnam" in q_clean.lower() or "việt nam" in q_clean.lower() else f"{q_clean}, Vietnam"
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": search_q, "format": "json", "limit": 1, "accept-language": "vi,en"},
            headers=HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), str(data[0].get("display_name", q_clean))
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800, show_spinner=False)
def retrieve_real_clinics(lat: float, lon: float, radius_m: int = 5000, prefer_en: bool = False) -> list[dict]:
    """Retrieve additional nearby hospitals and clinics around (lat, lon) from OpenStreetMap Overpass API."""
    overpass_query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"hospital|clinic"](around:{radius_m},{lat},{lon});
      way["amenity"~"hospital|clinic"](around:{radius_m},{lat},{lon});
      node["healthcare"~"hospital|clinic|laboratory"](around:{radius_m},{lat},{lon});
    );
    out center 25;
    """
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]
    elements = []
    for url in endpoints:
        try:
            resp = requests.post(
                url,
                data={"data": overpass_query},
                headers=HEADERS,
                timeout=10,
            )
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                if elements:
                    break
        except Exception:
            continue

    results = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        if prefer_en:
            raw_name = tags.get("name:en") or tags.get("int_name") or tags.get("name") or tags.get("official_name")
            name = _to_ascii_en(raw_name) if raw_name else None
        else:
            name = tags.get("name:vi") or tags.get("name") or tags.get("official_name")
        if not name:
            continue
        norm_name = name.strip().lower()
        if norm_name in seen:
            continue
        seen.add(norm_name)

        c_lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
        c_lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")
        if c_lat is None or c_lon is None:
            continue

        amenity = tags.get("amenity") or tags.get("healthcare") or "clinic"
        is_hospital = amenity == "hospital"

        housenumber = tags.get("addr:housenumber", "")
        street = tags.get("addr:street", "")
        ward = tags.get("addr:suburb", "") or tags.get("addr:quarter", "")
        district = tags.get("addr:district", "") or tags.get("addr:city", "") or tags.get("addr:province", "")
        street_line = " ".join(p for p in [housenumber, street] if p)
        full_addr = tags.get("addr:full") or ", ".join(p for p in [street_line, ward, district] if p)
        if prefer_en and full_addr:
            full_addr = _to_ascii_en(full_addr)

        phone = tags.get("phone") or tags.get("contact:phone") or ""
        dist_km = _haversine_km(lat, lon, float(c_lat), float(c_lon))

        results.append(
            {
                "name": name.strip(),
                "is_hospital": is_hospital,
                "address": full_addr,
                "phone": phone.strip(),
                "distance_km": round(dist_km, 2),
                "lat": float(c_lat),
                "lon": float(c_lon),
            }
        )

    results.sort(key=lambda x: x["distance_km"])
    return results[:8]


def _clean_district_for_geocode(district_label: str) -> str:
    """Strip parenthetical old-province hints like '(Bình Dương cũ)' so Nominatim geocodes cleanly."""
    return re.sub(r"\s*\([^)]*\)", "", district_label).strip()


def _render_facility_card(
    name: str,
    address: str,
    badge_cls: str,
    badge_svg: str,
    badge_txt: str,
    right_pill: str,
    maps_query: str,
    service_txt: str = "",
    phone: str = "",
):
    q_maps = urllib.parse.quote(maps_query)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={q_maps}"
    cta_txt = tr("Chỉ đường trên Google Maps", "Directions on Google Maps")
    service_html = (
        f'<div class="gg-cf-svc">{SVG_LAB}<span>{service_txt}</span></div>'
        if service_txt
        else ""
    )
    phone_html = (
        f'<div class="gg-cf-meta">{SVG_PHONE}<span>{phone}</span></div>'
        if phone
        else ""
    )
    card_html = _clean_html(
        f"""
        <div class="gg-cf-card">
            <div class="gg-cf-top-row">
                <span class="{badge_cls}">{badge_svg}<span>{badge_txt}</span></span>
                <span class="gg-cf-dist">{right_pill}</span>
            </div>
            <div class="gg-cf-name">{name}</div>
            <div class="gg-cf-meta">{SVG_PIN_SM}<span>{address}</span></div>
            {service_html}
            {phone_html}
            <a class="gg-cf-btn" href="{maps_url}" target="_blank" rel="noopener noreferrer">
                {SVG_NAV_ARROW}<span>{cta_txt}</span>
            </a>
        </div>
        """
    )
    st.markdown(card_html, unsafe_allow_html=True)


def render_clinic_finder():
    """Render hierarchical Province/City -> District/County selector reading directly from data/provinces_34.csv."""
    is_en = _is_en()
    st.markdown(
        _clean_html(
            """
            <style>
            .gg-cf-head {
                display: flex;
                align-items: flex-start;
                gap: 10px;
                margin-bottom: 10px;
            }
            .gg-cf-title {
                font-size: 1.08rem;
                font-weight: 800;
                color: #142D4E;
                line-height: 1.3;
                margin: 0;
            }
            .gg-cf-sub {
                font-size: 0.85rem;
                color: #5B6B82;
                margin: 3px 0 0 0;
                line-height: 1.45;
            }
            .gg-cf-card {
                background: #F8FAFC;
                border: 1px solid #E2EAF4;
                border-radius: 12px;
                padding: 13px 15px;
                margin-bottom: 10px;
                transition: border-color 0.15s ease, box-shadow 0.15s ease;
            }
            .gg-cf-card:hover {
                border-color: #BFDBFE;
                box-shadow: 0 3px 10px rgba(29, 78, 216, 0.06);
            }
            .gg-cf-top-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 8px;
                margin-bottom: 6px;
                flex-wrap: wrap;
            }
            .gg-cf-badge-hosp {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: #EFF6FF;
                color: #1D4ED8;
                border: 1px solid #BFDBFE;
                border-radius: 999px;
                padding: 2px 9px;
                font-size: 0.74rem;
                font-weight: 700;
            }
            .gg-cf-badge-clin {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: #F0FDF4;
                color: #15803D;
                border: 1px solid #BBF7D0;
                border-radius: 999px;
                padding: 2px 9px;
                font-size: 0.74rem;
                font-weight: 700;
            }
            .gg-cf-badge-ref {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                background: #FFFBEB;
                color: #B45309;
                border: 1px solid #FDE68A;
                border-radius: 999px;
                padding: 2px 9px;
                font-size: 0.74rem;
                font-weight: 700;
            }
            .gg-cf-dist {
                font-size: 0.75rem;
                font-weight: 700;
                color: #475569;
                background: #FFFFFF;
                border: 1px solid #DCE5F2;
                border-radius: 999px;
                padding: 2px 9px;
            }
            .gg-cf-name {
                font-size: 0.95rem;
                font-weight: 700;
                color: #142D4E;
                margin-bottom: 5px;
                line-height: 1.35;
            }
            .gg-cf-meta {
                display: flex;
                align-items: flex-start;
                gap: 6px;
                font-size: 0.82rem;
                color: #5B6B82;
                margin-bottom: 4px;
                line-height: 1.4;
            }
            .gg-cf-svc {
                display: flex;
                align-items: flex-start;
                gap: 6px;
                font-size: 0.81rem;
                color: #0F766E;
                font-weight: 500;
                margin-bottom: 4px;
                line-height: 1.4;
            }
            .gg-cf-btn {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                margin-top: 7px;
                background: #1D4ED8;
                color: #FFFFFF !important;
                text-decoration: none !important;
                font-size: 0.80rem;
                font-weight: 600;
                padding: 6px 13px;
                border-radius: 9px;
                transition: background 0.15s ease;
            }
            .gg-cf-btn:hover {
                background: #1E40AF;
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    df_csv = load_clinics_csv()

    with st.container(border=True):
        c_head, c_gps = st.columns([3.05, 1.4], vertical_alignment="center")
        with c_head:
            st.markdown(
                _clean_html(
                    f"""
                    <div class="gg-cf-head">
                        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:8px;display:flex;align-items:center;justify-content:center;">
                            {SVG_PIN}
                        </div>
                        <div>
                            <div class="gg-cf-title">{tr("Tìm cơ sở xét nghiệm tiểu đường theo Thành phố / Quận / Huyện", "Find Diabetes Testing Facilities by City & District")}</div>
                            <p class="gg-cf-sub">{tr(
                                "Chọn theo từng cấp: 1) Tỉnh / Thành phố → 2) Quận / Huyện / Thành phố để xem ngay danh sách bệnh viện, phòng khám & trung tâm xét nghiệm tiểu đường.",
                                "Filter by administrative level: 1) Province / City → 2) District / County to view diabetes testing hospitals, clinics & labs."
                            )}</p>
                        </div>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        if not df_csv.empty:
            prov_cols = ["ID", "Tinh_Thanh_Moi", "Tinh_Thanh_Moi_EN", "Nhan_Hien_Thi", "Nhan_Hien_Thi_EN"]
            avail_cols = [c for c in prov_cols if c in df_csv.columns]
            prov_df = df_csv[avail_cols].drop_duplicates(subset=["ID"]).sort_values("ID")
            id_to_row = {int(r["ID"]): r for _, r in prov_df.iterrows()}
            prov_ids = list(id_to_row.keys())
        else:
            id_to_row = {
                1: {
                    "Tinh_Thanh_Moi": "TP. Hồ Chí Minh",
                    "Tinh_Thanh_Moi_EN": "Ho Chi Minh City",
                    "Nhan_Hien_Thi": "TP. Hồ Chí Minh",
                    "Nhan_Hien_Thi_EN": "Ho Chi Minh City",
                }
            }
            prov_ids = [1]

        def _fmt_prov(pid: int) -> str:
            r = id_to_row[pid]
            if is_en:
                return r.get("Nhan_Hien_Thi_EN") or _to_ascii_en(r.get("Nhan_Hien_Thi", ""))
            return r.get("Nhan_Hien_Thi", "")

        c_prov, c_dist, c_rad = st.columns([2.15, 1.65, 0.9])
        with c_prov:
            prov_id = st.selectbox(
                tr("1. Tỉnh / Thành phố:", "1. Province / City:"),
                options=prov_ids,
                index=0,
                format_func=_fmt_prov,
                key="gg_clinic_province_34",
            )
            prov_meta = id_to_row[prov_id]
            prov_name_vi = prov_meta["Tinh_Thanh_Moi"]
            prov_name_en = prov_meta.get("Tinh_Thanh_Moi_EN") or _to_ascii_en(prov_name_vi)
            prov_display = prov_name_en if is_en else prov_name_vi

        sub_df = df_csv[df_csv["Tinh_Thanh_Moi"] == prov_name_vi] if not df_csv.empty else pd.DataFrame()
        if not sub_df.empty:
            dist_vi_list = list(dict.fromkeys(sub_df["Quan_Huyen"].tolist()))
            vi_to_en_dist = {}
            for _, r in sub_df.iterrows():
                d_vi = r["Quan_Huyen"]
                if d_vi not in vi_to_en_dist:
                    vi_to_en_dist[d_vi] = r.get("Quan_Huyen_EN") or _to_ascii_en(d_vi)
        else:
            dist_vi_list = ["Quận 1"]
            vi_to_en_dist = {"Quận 1": "District 1"}

        ALL_TOKEN = "__ALL__"
        CUSTOM_TOKEN = "__CUSTOM__"
        district_choices = dist_vi_list + [ALL_TOKEN, CUSTOM_TOKEN]

        def _fmt_dist(token: str) -> str:
            if token == ALL_TOKEN:
                return tr("— Tất cả quận/huyện trong tỉnh/thành —", "— All districts in province/city —")
            if token == CUSTOM_TOKEN:
                return tr("Khác (tự nhập tên quận/huyện/phường)...", "Other (type district/ward)...")
            return vi_to_en_dist.get(token, _to_ascii_en(token)) if is_en else token

        with c_dist:
            selected_dist = st.selectbox(
                tr("2. Quận / Huyện / Thành phố:", "2. District / County / City:"),
                options=district_choices,
                index=0,
                format_func=_fmt_dist,
                key=f"gg_clinic_dist_{prov_id}",
            )

        with c_rad:
            radius_km = st.selectbox(
                tr("Bán kính:", "Radius:"),
                options=[3, 5, 10, 15],
                index=1,
                format_func=lambda x: f"{x} km",
                key="gg_clinic_radius_select",
            )

        sub_clean_vi = ""
        sub_clean_disp = ""
        is_custom_input = False
        if selected_dist == CUSTOM_TOKEN:
            is_custom_input = True
            custom_txt = st.text_input(
                tr("Nhập tên Quận / Huyện / Phường / Đường:", "Enter District / Ward / Street:"),
                value="",
                placeholder=tr("VD: Quận 1, Phường Bến Thành...", "e.g., District 1, Ben Thanh Ward..."),
                key=f"gg_clinic_custom_sub_{prov_id}",
            )
            sub_clean_vi = custom_txt.strip()
            sub_clean_disp = sub_clean_vi
        elif selected_dist != ALL_TOKEN:
            sub_clean_vi = selected_dist
            sub_clean_disp = vi_to_en_dist.get(selected_dist, _to_ascii_en(selected_dist)) if is_en else selected_dist

        # Filter CSV rows by selected Province/City and District/County
        if not sub_df.empty:
            if selected_dist == ALL_TOKEN:
                matched_csv = sub_df.copy()
            elif is_custom_input:
                if sub_clean_vi:
                    kw = sub_clean_vi.lower()
                    mask = (
                        sub_df["Quan_Huyen"].str.lower().str.contains(kw, regex=False)
                        | sub_df["Dia_Chi"].str.lower().str.contains(kw, regex=False)
                        | sub_df["Ten_Benh_Vien"].str.lower().str.contains(kw, regex=False)
                    )
                    if "Quan_Huyen_EN" in sub_df.columns:
                        mask = mask | sub_df["Quan_Huyen_EN"].str.lower().str.contains(kw, regex=False)
                    if "Dia_Chi_EN" in sub_df.columns:
                        mask = mask | sub_df["Dia_Chi_EN"].str.lower().str.contains(kw, regex=False)
                    if "Ten_Benh_Vien_EN" in sub_df.columns:
                        mask = mask | sub_df["Ten_Benh_Vien_EN"].str.lower().str.contains(kw, regex=False)
                    matched_csv = sub_df[mask].copy()
                else:
                    matched_csv = sub_df.copy()
            else:
                matched_csv = sub_df[sub_df["Quan_Huyen"] == sub_clean_vi].copy()
        else:
            matched_csv = pd.DataFrame()

        geocode_sub = _clean_district_for_geocode(sub_clean_vi) if sub_clean_vi else ""
        effective_query_vi = f"{geocode_sub}, {prov_name_vi}" if geocode_sub else prov_name_vi
        effective_query_disp = (
            f"{_clean_district_for_geocode(sub_clean_disp)}, {prov_display}"
            if sub_clean_disp
            else prov_display
        )
        display_area = f"{sub_clean_disp} · {prov_display}" if sub_clean_disp else prov_display

        maps_search_q = urllib.parse.quote(
            f"diabetes testing hospital clinic {effective_query_disp}"
            if is_en
            else f"xét nghiệm tiểu đường bệnh viện phòng khám {effective_query_vi}"
        )
        with c_gps:
            st.link_button(
                tr("Mở Google Maps khu vực ↗", "Open Area in Google Maps ↗"),
                url=f"https://www.google.com/maps/search/{maps_search_q}",
                type="primary",
                use_container_width=True,
            )

        # Coordinates from CSV first (instant, accurate), fallback to Nominatim
        map_points = []
        center_lat, center_lon = None, None
        if not matched_csv.empty and "Lat" in matched_csv.columns and "Lon" in matched_csv.columns:
            valid_coords = matched_csv.dropna(subset=["Lat", "Lon"])
            if not valid_coords.empty:
                center_lat = float(valid_coords.iloc[0]["Lat"])
                center_lon = float(valid_coords.iloc[0]["Lon"])
                for _, r in valid_coords.iterrows():
                    map_points.append({"lat": float(r["Lat"]), "lon": float(r["Lon"])})

        if center_lat is None or center_lon is None:
            geo = geocode_location(effective_query_vi)
            if geo:
                center_lat, center_lon, _ = geo
                map_points.append({"lat": center_lat, "lon": center_lon})

        # Optional live OSM supplement for custom input or when CSV has no rows
        extra_clinics = []
        if (is_custom_input or matched_csv.empty) and center_lat is not None and center_lon is not None:
            extra_clinics = retrieve_real_clinics(
                center_lat, center_lon, radius_m=radius_km * 1000, prefer_en=is_en
            )
            for item in extra_clinics:
                map_points.append({"lat": item["lat"], "lon": item["lon"]})

        total_found = len(matched_csv) + len(extra_clinics)
        st.caption(
            tr(
                f"Khu vực đang lọc: {display_area} — Tìm thấy {total_found} cơ sở xét nghiệm tiểu đường & nội tiết phù hợp.",
                f"Filtered area: {display_area} — Found {total_found} matching diabetes & endocrinology testing facilities.",
            )
        )

        col_list, col_map = st.columns([1.28, 1], gap="medium")
        with col_list:
            if not matched_csv.empty:
                section_lbl = (
                    tr(
                        f"Danh sách cơ sở xét nghiệm tiểu đường tại {sub_clean_disp}",
                        f"Diabetes Testing Facilities in {sub_clean_disp}",
                    )
                    if sub_clean_disp
                    else tr(
                        f"Danh sách cơ sở xét nghiệm tiểu đường tại {prov_display}",
                        f"Diabetes Testing Facilities in {prov_display}",
                    )
                )
                st.markdown(
                    _clean_html(
                        f'<div style="font-size:0.86rem;font-weight:700;color:#142D4E;margin:2px 0 7px 0;">{section_lbl}</div>'
                    ),
                    unsafe_allow_html=True,
                )
                show_df = matched_csv.head(15) if selected_dist == ALL_TOKEN else matched_csv
                for _, row in show_df.iterrows():
                    loai_vi = row.get("Loai_Co_So", "")
                    if "Bệnh viện" in loai_vi:
                        badge_cls = "gg-cf-badge-hosp"
                        badge_svg = SVG_HOSPITAL
                    elif "Xét nghiệm" in loai_vi:
                        badge_cls = "gg-cf-badge-ref"
                        badge_svg = SVG_STAR
                    else:
                        badge_cls = "gg-cf-badge-clin"
                        badge_svg = SVG_CLINIC

                    if is_en:
                        badge_txt = row.get("Loai_Co_So_EN") or "Diabetes Testing Facility"
                        fac_name = row.get("Ten_Benh_Vien_EN") or _to_ascii_en(row["Ten_Benh_Vien"])
                        fac_addr = row.get("Dia_Chi_EN") or _to_ascii_en(row["Dia_Chi"])
                        fac_svc = row.get("Dich_Vu_Xet_Nghiem_EN") or "Endocrinology & Diabetes consultation, blood glucose & HbA1c testing"
                        right_pill = row.get("Quan_Huyen_EN") or _to_ascii_en(row.get("Quan_Huyen", "")) or prov_display
                    else:
                        badge_txt = loai_vi or "Cơ sở xét nghiệm tiểu đường"
                        fac_name = row["Ten_Benh_Vien"]
                        fac_addr = row["Dia_Chi"]
                        fac_svc = row.get("Dich_Vu_Xet_Nghiem", "")
                        right_pill = row.get("Quan_Huyen", "") or prov_display

                    _render_facility_card(
                        name=fac_name,
                        address=fac_addr,
                        badge_cls=badge_cls,
                        badge_svg=badge_svg,
                        badge_txt=badge_txt,
                        right_pill=right_pill,
                        maps_query=f"{fac_name}, {fac_addr}",
                        service_txt=fac_svc,
                    )

            if extra_clinics:
                st.markdown(
                    _clean_html(
                        f'<div style="font-size:0.86rem;font-weight:700;color:#142D4E;margin:10px 0 7px 0;">'
                        f'{tr(f"Cơ sở y tế lân cận quanh {effective_query_disp}", f"Nearby Facilities around {effective_query_disp}")}'
                        f'</div>'
                    ),
                    unsafe_allow_html=True,
                )
                for item in extra_clinics[:5]:
                    badge_cls = "gg-cf-badge-hosp" if item["is_hospital"] else "gg-cf-badge-clin"
                    badge_svg = SVG_HOSPITAL if item["is_hospital"] else SVG_CLINIC
                    badge_txt = (
                        tr("Bệnh viện", "Hospital")
                        if item["is_hospital"]
                        else tr("Phòng khám / Cơ sở y tế", "Clinic / Medical Facility")
                    )
                    dist_txt = tr(f"Cách ~{item['distance_km']} km", f"~{item['distance_km']} km away")
                    addr_txt = item["address"] or tr("Xem vị trí chính xác trên Google Maps", "View exact pin on Google Maps")
                    _render_facility_card(
                        name=item["name"],
                        address=addr_txt,
                        badge_cls=badge_cls,
                        badge_svg=badge_svg,
                        badge_txt=badge_txt,
                        right_pill=dist_txt,
                        maps_query=f"{item['name']}, {effective_query_disp}",
                        phone=item["phone"],
                    )

            if matched_csv.empty and not extra_clinics:
                st.info(
                    tr(
                        f"Không tìm thấy cơ sở khớp trực tiếp với '{sub_clean_disp}'. Bạn có thể chọn quận/huyện trong danh sách hoặc bấm 'Mở Google Maps khu vực ↗'.",
                        f"No direct match for '{sub_clean_disp}'. Select a district from the dropdown or click 'Open Area in Google Maps ↗'.",
                    )
                )

        with col_map:
            st.markdown(
                _clean_html(
                    f'<div style="display:flex;align-items:center;gap:6px;font-size:0.92rem;font-weight:700;color:#142D4E;margin-bottom:8px;">'
                    f'{SVG_MAP_HEADER}'
                    f'<span>{tr("Bản đồ phân bố cơ sở y tế", "Healthcare Facility Distribution Map")}</span>'
                    f'</div>'
                ),
                unsafe_allow_html=True,
            )
            if map_points:
                df_map = pd.DataFrame(map_points).drop_duplicates()
                st.map(df_map[["lat", "lon"]], color="#EF4444", size=65, use_container_width=True)
            else:
                st.info(
                    tr(
                        "Nhấn nút 'Mở Google Maps khu vực ↗' ở góc trên để xem bản đồ trực tiếp.",
                        "Click 'Open Area in Google Maps ↗' above to view the live map.",
                    )
                )
