import math
import streamlit as st

from utils.data_loader import meta
from utils.prediction import load_pipeline
from utils.explanation import explain
from utils.i18n import factor_name, age_labels, health_labels
from utils.ui import style, html, tr, ring
from components.ai_assistant import render_floating_ai_assistant
from utils.clinic_finder import render_clinic_finder

style()

S = st.session_state

if "probability" not in S or "answers" not in S:
    st.markdown(f"""
    <div style="text-align:center;padding:3rem 1.5rem;background:#FFFFFF;border:1px solid #DCE5F2;border-radius:18px;max-width:540px;margin:2rem auto;">
        <h3 style="margin:0 0 0.5rem;color:#142D4E;font-size:1.35rem;font-weight:800;">
            {tr("Chưa có kết quả sàng lọc", "No Screening Results Found")}
        </h3>
        <p style="color:#5B6B82;font-size:0.92rem;line-height:1.55;">
            {tr(
                "Bạn chưa hoàn thành bảng khảo sát 8 yếu tố. Hãy thực hiện khảo sát để nhận kết quả phân loại và tư vấn từ Trợ lý AI.",
                "You haven't completed the 8-factor risk questionnaire yet. Please complete the assessment to view your result and consult the AI Assistant."
            )}
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.columns([1, 1.1, 1])[1].button(tr("Bắt đầu Khảo sát Ngay →", "Start Risk Assessment →"), type="primary", use_container_width=True):
        st.session_state["assess_step"] = 1
        st.switch_page("pages/1_Risk_Assessment.py")
    st.stop()

m = meta()
p = float(S["probability"])
answers = S["answers"]
threshold = float(m["threshold"])
is_elevated = p >= threshold

# Phân tầng 3 mức nguy cơ
if p >= 0.25:
    tier = "high"
    tier_color = "#DC2626"
    banner_bg, banner_bd = "#FEF2F2", "#FECACA"
    advice_bg = "#FFF5F5"
    tier_badge = tr("Mức Cao", "High Risk")
    tier_title = tr("Nguy cơ Cao (Trên ngưỡng sàng lọc)", "High Risk (Above Screening Threshold)")
    tier_summary = tr(
        f"Điểm dự báo của bạn ({p*100:.1f}%) vượt khá rõ ngưỡng sàng lọc ({threshold*100:.1f}%). Hồ sơ sức khỏe có nhiều điểm tương đồng với nhóm tự báo cáo tiểu đường hoặc tiền tiểu đường.",
        f"Your score ({p*100:.1f}%) is noticeably above the screening threshold ({threshold*100:.1f}%). Your profile aligns with survey patterns reported among diabetes or prediabetes cases."
    )
    tier_steps = [
        tr("Sớm đến cơ sở y tế để bác sĩ chỉ định xét nghiệm chẩn đoán chuẩn (FPG, HbA1c hoặc nghiệm pháp dung nạp glucose).", "Schedule a medical consultation soon to discuss diagnostic blood tests (FPG, HbA1c, or OGTT)."),
        tr("Theo dõi sát các dấu hiệu cảnh báo như khát nước nhiều, đi tiểu thường xuyên, mệt mỏi kéo dài.", "Monitor warning signs such as increased thirst, frequent urination, or persistent fatigue."),
        tr("Xây dựng kế hoạch dinh dưỡng và vận động an toàn cùng bác sĩ hoặc chuyên gia dinh dưỡng.", "Work with a clinician or dietitian on a safe nutrition and exercise plan."),
    ]
elif p >= 0.12:
    tier = "moderate"
    tier_color = "#D97706"
    banner_bg, banner_bd = "#FFFBEB", "#FDE68A"
    advice_bg = "#FFFDF5"
    tier_badge = tr("Mức Trung bình", "Moderate Risk")
    tier_title = tr("Nguy cơ Trung bình / Cận ngưỡng (Cần theo dõi sớm)", "Moderate / Borderline Risk (Early Attention)")
    tier_summary = tr(
        f"Điểm dự báo của bạn ({p*100:.1f}%) nằm ở vùng trung bình / cận ngưỡng sàng lọc ({threshold*100:.1f}%). Một số yếu tố sức khỏe đang làm tăng nhẹ mức độ nguy cơ.",
        f"Your score ({p*100:.1f}%) sits in the borderline zone near the screening threshold ({threshold*100:.1f}%). Certain health factors slightly elevate your statistical risk."
    )
    tier_steps = [
        tr("Chủ động đặt lịch kiểm tra đường huyết lúc đói (FPG) hoặc HbA1c trong lần khám định kỳ sắp tới.", "Ask your doctor for a routine Fasting Plasma Glucose (FPG) or HbA1c test at your next check-up."),
        tr("Điều chỉnh khẩu phần tinh bột tinh chế, chia nhỏ bữa ăn và kiểm soát BMI hợp lý.", "Moderate refined carbohydrates, prioritize balanced meals, and maintain a healthy BMI."),
        tr("Theo dõi huyết áp và mỡ máu định kỳ 6 tháng/lần để phát hiện sớm biến động.", "Check blood pressure and cholesterol every 6 months."),
    ]
else:
    tier = "low"
    tier_color = "#16A34A"
    banner_bg, banner_bd = "#F0FDF4", "#BBF7D0"
    advice_bg = "#F7FEF9"
    tier_badge = tr("Mức Thấp", "Low Risk")
    tier_title = tr("Nguy cơ Thấp (Dưới ngưỡng sàng lọc)", "Low Risk (Below Screening Threshold)")
    tier_summary = tr(
        f"Điểm dự báo của bạn ({p*100:.1f}%) nằm ở vùng nguy cơ thấp và dưới ngưỡng sàng lọc ({threshold*100:.1f}%). Hồ sơ hiện tại cho thấy các chỉ số nền tảng đang ở trạng thái thuận lợi.",
        f"Your score ({p*100:.1f}%) falls in the low-risk zone below the screening threshold ({threshold*100:.1f}%). Your baseline profile currently looks favorable."
    )
    tier_steps = [
        tr("Duy trì thói quen ăn uống cân bằng: tăng cường rau xanh, chất xơ hòa tan và hạn chế đồ uống nhiều đường.", "Maintain balanced nutrition rich in fiber and vegetables while limiting sugary beverages."),
        tr("Tiếp tục vận động thể lực đều đặn ít nhất 2.5 giờ mỗi tuần (khoảng 30 phút/ngày: đi bộ nhanh, đạp xe, bơi lội).", "Keep up at least 2.5 hours of moderate physical activity per week (about 30 mins/day: brisk walking, cycling, swimming)."),
        tr("Khám sức khỏe tổng quát định kỳ mỗi 12 tháng để theo dõi các chỉ số chuyển hóa (HbA1c / FPG) định kỳ.", "Schedule routine annual preventive health check-ups to track metabolic metrics."),
    ]

# Gợi ý cá nhân hóa theo từng yếu tố đầu vào
bmi_val = float(answers.get("BMI", 22.0))
bp_raw = answers.get("HighBP")
chol_raw = answers.get("HighChol")
bp_nan = isinstance(bp_raw, float) and math.isnan(bp_raw)
chol_nan = isinstance(chol_raw, float) and math.isnan(chol_raw)

factor_tips = []
if bmi_val >= 25.0:
    factor_tips.append(tr("Chỉ số BMI đang ở mức thừa cân/béo phì: giảm 5–7% cân nặng giúp cải thiện rõ rệt độ nhạy insulin.", "BMI in overweight/obese range: a 5–7% weight reduction can meaningfully improve insulin sensitivity."))
if not bp_nan and bp_raw == 1:
    factor_tips.append(tr("Có tiền sử tăng huyết áp: tiếp tục đo huyết áp tại nhà, ăn nhạt (<5g muối/ngày) và tái khám đúng hẹn.", "History of high blood pressure: monitor BP regularly, reduce sodium intake, and keep scheduled check-ups."))
elif bp_nan:
    factor_tips.append(tr("Chưa rõ chỉ số huyết áp: bạn nên đo kiểm tra huyết áp tại nhà thuốc hoặc cơ sở y tế.", "Blood pressure status unknown: consider checking your blood pressure at a clinic or pharmacy."))
if not chol_nan and chol_raw == 1:
    factor_tips.append(tr("Có tiền sử mỡ máu cao: hạn chế chất béo bão hòa, đồ chiên rán và kiểm tra lipid máu định kỳ.", "History of high cholesterol: limit saturated fats and monitor lipid panels regularly."))
elif chol_nan:
    factor_tips.append(tr("Chưa rõ chỉ số mỡ máu: nên bổ sung xét nghiệm lipid máu trong lần kiểm tra sức khỏe tới.", "Cholesterol status unknown: include a lipid panel in your next routine check-up."))
if answers.get("PhysActivity") == 0:
    factor_tips.append(tr("Ít vận động trong 30 ngày qua: hãy bắt đầu với 15–20 phút đi bộ mỗi ngày sau bữa ăn.", "Limited recent activity: start with 15–20 minutes of daily post-meal walking."))
if answers.get("Smoker") == 1:
    factor_tips.append(tr("Có tiền sử hút thuốc lá: hạn chế hoặc ngừng hút thuốc giúp giảm rõ nguy cơ biến chứng mạch máu.", "Smoking history: reducing or quitting tobacco lowers vascular and metabolic risk."))
if not factor_tips:
    factor_tips.append(tr("Các thói quen sinh hoạt cơ bản của bạn đang khá tích cực — hãy tiếp tục duy trì đều đặn.", "Your baseline lifestyle indicators look solid — keep maintaining these positive routines."))

# Exact Shapley
cache_key = tuple((k, ("nan" if (isinstance(v, float) and math.isnan(v)) else v)) for k, v in sorted(answers.items()))
if S.get("_why_key") != cache_key:
    why_df, why_desc = explain(load_pipeline(), answers, m)
    S["_why"] = why_df
    S["_why_desc"] = why_desc
    S["_why_key"] = cache_key

why = S["_why"].copy()
factors_list, factors_summary_text = [], ""
for _, row in why.iterrows():
    f_name = factor_name(row["Feature"])
    f_contrib = float(row["Contribution"])
    f_dir = tr("Tăng điểm số", "Raises score") if f_contrib > 0 else tr("Giảm điểm số", "Lowers score")
    factors_list.append({"Feature": row["Feature"], "Factor": f_name, "Contribution": f_contrib, "Direction": f_dir})
    factors_summary_text += f"- {f_name} ({row['Feature']}): {f_contrib:+.4f} -> {f_dir}\n"

ai_context = {
    "probability": p,
    "threshold": threshold,
    "is_elevated": is_elevated,
    "answers": answers,
    "top_factors": factors_list,
    "factors_summary": factors_summary_text,
}


def get_user_answer_display(f_key: str, ans: dict) -> str:
    v = ans.get(f_key)
    if f_key == "Age":
        idx = int(v) - 1
        al = age_labels()
        return al[idx] if 0 <= idx < len(al) else str(v)
    elif f_key == "BMI":
        return f"{float(v):.1f} kg/m²"
    elif f_key == "GenHlth":
        idx = int(v) - 1
        hl = health_labels()
        return hl[idx] if 0 <= idx < len(hl) else str(v)
    elif f_key in ("HighBP", "HighChol"):
        if isinstance(v, float) and math.isnan(v):
            return tr("Không rõ", "Unknown")
        return tr("Có", "Yes") if v == 1 else tr("Không", "No")
    elif f_key in ("Smoker", "PhysActivity", "DiffWalk"):
        return tr("Có", "Yes") if v == 1 else tr("Không", "No")
    return str(v)


st.markdown(f"""
<div style="margin-bottom:1.2rem;">
    <h2 style="margin:0;font-size:1.85rem;font-weight:800;color:#142D4E;">{tr("Kết quả Sàng lọc của tôi", "My Screening Results")}</h2>
    <div style="font-size:0.92rem;color:#5B6B82;margin-top:3px;">
        {tr("Tổng hợp điểm phân loại từ mô hình học máy. Nhấn vào biểu tượng bác sĩ ở góc dưới bên phải để hỏi Trợ lý AI.",
            "Classification score summary from the machine learning model. Tap the doctor icon at the bottom-right to ask AI Assistant.")}
    </div>
</div>
""", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;background:{banner_bg};border:1px solid {banner_bd};border-radius:12px;padding:13px 16px;margin-bottom:1.2rem;">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="{tier_color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex:0 0 24px;">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="m9 12 2 2 4-4"/>
        </svg>
        <div>
            <div style="font-size:1.12rem;font-weight:800;color:{tier_color};">{tier_title}</div>
            <div style="font-size:0.78rem;color:#475569;margin-top:2px;">
                {tr("Dựa trên mô hình Histogram Gradient Boosting (CDC BRFSS 2015)", "Based on Histogram Gradient Boosting (CDC BRFSS 2015)")}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    r_col, m_col = st.columns([0.9, 1.5], vertical_alignment="center", gap="large")
    with r_col:
        html(ring(p, f"{p * 100:.1f}%", tier_color, tr("Xác suất Dự báo", "Model Score")))
    with m_col:
        bp_tag = tr("Huyết áp: Không rõ", "BP: Unknown") if bp_nan else (tr("Huyết áp: Tăng huyết áp", "BP: High") if bp_raw == 1 else tr("Huyết áp: Bình thường", "BP: Normal"))
        chol_tag = tr("Mỡ máu: Không rõ", "Cholesterol: Unknown") if chol_nan else (tr("Mỡ máu: Cao", "Cholesterol: High") if chol_raw == 1 else tr("Mỡ máu: Bình thường", "Cholesterol: Normal"))
        st.markdown(f"""
        <div style="font-size:0.78rem;font-weight:700;color:#64748B;text-transform:uppercase;">{tr("Ý nghĩa kết quả này", "What This Means")}</div>
        <div style="font-size:0.94rem;color:#1E293B;line-height:1.6;margin:5px 0 12px;">{tier_summary}</div>
        <div style="font-size:0.84rem;font-weight:600;color:#1D4ED8;">BMI: {bmi_val:.1f} kg/m² &nbsp;·&nbsp; {bp_tag} &nbsp;·&nbsp; {chol_tag}</div>
        """, unsafe_allow_html=True)

    st.divider()

    steps_li = "".join(f"<li>{s}</li>" for s in tier_steps)
    tips_li = "".join(f"<li>{s}</li>" for s in factor_tips)
    st.markdown(f"""
    <div style="background:{advice_bg};border:1px solid {banner_bd};border-radius:14px;padding:16px 18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div style="display:flex;align-items:center;gap:6px;">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#142D4E" stroke-width="2" style="flex:0 0 18px;">
                    <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                </svg>
                <strong style="color:#142D4E;font-size:0.95rem;">{tr("Lời khuyên Phù hợp theo Mức Nguy cơ của Bạn", "Tailored Guidance for Your Risk Level")}</strong>
            </div>
            <span style="color:{tier_color};font-size:0.78rem;font-weight:800;text-transform:uppercase;">{tier_badge}</span>
        </div>
        <div style="font-size:0.86rem;font-weight:700;color:#142D4E;margin-top:6px;">
            {tr(f"Khuyến nghị duy trì sức khỏe cho nhóm {tier_badge}:", f"Recommendations for {tier_badge} group:")}
        </div>
        <ul style="margin:4px 0 10px;padding-left:20px;color:#334155;font-size:0.88rem;line-height:1.6;">{steps_li}</ul>
        <div style="border-top:1px solid rgba(0,0,0,0.08);padding-top:10px;">
            <strong style="color:#142D4E;font-size:0.84rem;">{tr("Gợi ý cá nhân hóa theo các câu trả lời của bạn:", "Personalized tips based on your answers:")}</strong>
            <ul style="margin:5px 0 0;padding-left:20px;color:#334155;font-size:0.86rem;line-height:1.6;">{tips_li}</ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

# Option to view factor contributions (Exact Shapley) matching Image 4
if st.toggle(tr("Xem chi tiết đóng góp của các yếu tố (Exact Shapley)", "Show detailed factor contributions (Exact Shapley)"), value=False, key="toggle_shapley_details"):
    with st.container(border=True):
        st.markdown(f"""
        <div style="font-size:1.1rem;font-weight:800;color:#142D4E;margin-bottom:0.25rem;">
            {tr("Đóng góp của các yếu tố (Exact Shapley)", "Factor Contributions (Exact Shapley)")}
        </div>
        <div style="font-size:0.88rem;color:#5B6B82;margin-bottom:1.1rem;">
            {tr("Lượng hóa mức độ đẩy xác suất mô hình tăng lên hoặc giảm xuống so với mức nền khảo sát:",
                "Quantifying how much each factor pushes the model probability up or down relative to baseline:")}
        </div>
        """, unsafe_allow_html=True)

        why["Abs"] = why["Contribution"].abs()
        max_share = max(float(why["Abs"].max()), 0.01)
        rows = []
        for _, row in why.iterrows():
            f_key = row["Feature"]
            c_val = float(row["Contribution"])
            w = max(4.0, (abs(c_val) / max_share) * 100.0)
            user_val_str = get_user_answer_display(f_key, answers)
            full_factor_label = f"{factor_name(f_key)} ({user_val_str})"

            if c_val < 0:
                bar_bg = "#10B981"
                sign_str = tr(f"Giảm điểm ({c_val*100:.1f}%)", f"Lowers ({c_val*100:.1f}%)")
                sign_color = "#16A34A"
            else:
                bar_bg = "#F59E0B"
                sign_str = tr(f"Tăng điểm (+{c_val*100:.1f}%)", f"Raises (+{c_val*100:.1f}%)")
                sign_color = "#D97706"

            rows.append(
                f'<div class="bar-row">'
                f'<div class="bar-name">{full_factor_label}</div>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{w:.1f}%;background:{bar_bg}"></div></div>'
                f'<div class="bar-val" style="color:{sign_color};">{sign_str}</div>'
                f'</div>'
            )
        html("".join(rows))

st.write("")
render_clinic_finder()

st.write("")
col_retake_l, col_retake_m, col_retake_r = st.columns([1, 1.8, 1])
with col_retake_m:
    if st.button(tr("← Làm lại Khảo sát", "← Retake Assessment"), use_container_width=True):
        st.session_state["assess_step"] = 1
        st.switch_page("pages/1_Risk_Assessment.py")

render_floating_ai_assistant(ai_context)
