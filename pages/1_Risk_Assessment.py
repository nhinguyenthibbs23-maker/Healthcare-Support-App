import streamlit as st

from utils.i18n import age_labels, health_labels
from utils.prediction import predict
from utils.ui import style, tr

style()

S = st.session_state
F = S.setdefault("form", {})
step = int(S.setdefault("assess_step", 1))
if step < 1 or step > 8:
    step = 1
    S["assess_step"] = 1

TOTAL_STEPS = 8

YES_NO_MAP = {"yes": tr("Có", "Yes"), "no": tr("Không", "No")}
UNKNOWN_MAP = {
    "yes": tr("Có", "Yes"),
    "no": tr("Không", "No"),
    "unknown": tr("Không rõ / Chưa từng đo", "Unknown / Never checked"),
}

age_list = age_labels()
age_values = [str(i + 1) for i in range(len(age_list))]
age_map = {str(i + 1): lbl for i, lbl in enumerate(age_list)}

health_list = health_labels()
health_values = [str(i + 1) for i in range(len(health_list))]
health_map = {str(i + 1): lbl for i, lbl in enumerate(health_list)}


def get_idx(options, val, default_idx=0):
    return options.index(val) if val in options else default_idx


# Stepper Header
step_pct = int((step / float(TOTAL_STEPS)) * 100)
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
    <div>
        <h2 style="margin:0;font-size:1.75rem;font-weight:800;color:#142D4E;">
            {tr("Khảo sát Nguy cơ Tiểu đường", "Diabetes Risk Assessment")}
        </h2>
        <div style="font-size:0.92rem;color:#5B6B82;margin-top:2px;">
            {tr("Trả lời lần lượt từng câu hỏi ngắn để mô hình đánh giá hồ sơ của bạn.", "Answer each brief question one step at a time to generate your assessment.")}
        </div>
    </div>
    <div>
        <span style="font-size:0.86rem;font-weight:700;color:#1D4ED8;background:#EFF6FF;border:1px solid #BFDBFE;padding:6px 14px;border-radius:999px;">
            {tr(f"Câu {step} / {TOTAL_STEPS}", f"Question {step} of {TOTAL_STEPS}")}
        </span>
    </div>
</div>
<div style="width:100%;height:7px;background:#E2E8F0;border-radius:999px;overflow:hidden;margin-bottom:1.6rem;">
    <div style="width:{step_pct}%;height:100%;background:#2563EB;border-radius:999px;transition:width 0.25s ease;"></div>
</div>
""", unsafe_allow_html=True)

bmi_error = False

with st.container(border=True):
    # =======================================================
    # QUESTION 1: AGE GROUP
    # =======================================================
    if step == 1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-6 8-6s8 2 8 6"/></svg>
            <span>{tr("1. Bạn thuộc nhóm tuổi nào? *", "1. Which age group are you in? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Chọn khoảng tuổi hiện tại của bạn theo phân nhóm điều tra.", "Select your current age range."))

        sel_age = st.selectbox(
            tr("Nhóm tuổi", "Age Group"),
            options=age_values,
            index=get_idx(age_values, str(F.get("age", "5"))),
            format_func=lambda v: age_map[v],
            key="w_age",
            label_visibility="collapsed",
        )
        F["age"] = sel_age

    # =======================================================
    # QUESTION 2: HEIGHT & WEIGHT TOGETHER -> BMI
    # =======================================================
    elif step == 2:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><path d="M12 3v18M5 7h14"/><path d="M5 7l-2 6a2.5 2.5 0 0 0 4 0L5 7zM19 7l-2 6a2.5 2.5 0 0 0 4 0L19 7z"/></svg>
            <span>{tr("2. Chiều cao và Cân nặng của bạn *", "2. Your Height & Weight *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Ứng dụng sẽ tự động tính chỉ số khối cơ thể (BMI) từ hai số đo này.", "Body Mass Index (BMI) is calculated automatically from both measurements."))

        c_h, c_w = st.columns(2, gap="medium")
        with c_h:
            h_val = st.number_input(
                tr("Chiều cao (cm)", "Height (cm)"),
                min_value=100.0,
                max_value=230.0,
                value=float(F.get("height", 165.0)),
                step=0.5,
                key="w_height",
            )
            F["height"] = h_val

        with c_w:
            w_val = st.number_input(
                tr("Cân nặng (kg)", "Weight (kg)"),
                min_value=25.0,
                max_value=250.0,
                value=float(F.get("weight", 62.0)),
                step=0.5,
                key="w_weight",
            )
            F["weight"] = w_val

        bmi_calc = float(w_val) / ((float(h_val) / 100.0) ** 2)
        F["bmi"] = bmi_calc

        if bmi_calc < 18.5:
            bmi_cat_lbl = tr("Thiếu cân", "Underweight")
            bmi_color = "#3B82F6"
        elif bmi_calc < 25.0:
            bmi_cat_lbl = tr("Bình thường", "Normal")
            bmi_color = "#16A34A"
        elif bmi_calc < 30.0:
            bmi_cat_lbl = tr("Thừa cân", "Overweight")
            bmi_color = "#D97706"
        else:
            bmi_cat_lbl = tr("Béo phì", "Obese")
            bmi_color = "#DC2626"

        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:wrap;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:14px 20px;margin:14px 0 6px 0;">
            <div style="display:inline-flex;align-items:center;gap:6px;font-size:0.95rem;color:#475569;line-height:1.2;">
                <span>{tr("Chỉ số BMI tính được:", "Calculated BMI:")}</span>
                <strong style="font-size:1.15rem;color:#142D4E;line-height:1.2;">{bmi_calc:.1f} kg/m²</strong>
            </div>
            <span style="display:inline-flex;align-items:center;background:{bmi_color};color:#fff;font-size:0.82rem;font-weight:700;padding:5px 14px;border-radius:999px;line-height:1.2;">
                {bmi_cat_lbl}
            </span>
        </div>
        """, unsafe_allow_html=True)

        if not (12.0 <= bmi_calc <= 98.0):
            bmi_error = True
            st.warning(tr(
                "Chỉ số BMI nằm ngoài phạm vi hợp lệ của mô hình (12.0 – 98.0). Vui lòng kiểm tra lại chiều cao và cân nặng.",
                "Calculated BMI is outside the supported model range (12.0 – 98.0). Please check your height and weight."
            ))

    # =======================================================
    # QUESTION 3: HIGH BLOOD PRESSURE
    # =======================================================
    elif step == 3:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><path d="M22 12h-4l-3 7-4-14-3 7H2"/></svg>
            <span>{tr("3. Bạn đã từng được bác sĩ thông báo bị Tăng huyết áp chưa? *", "3. Have you ever been told by a doctor that you have High Blood Pressure? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Không tính tăng huyết áp chỉ khi mang thai hoặc ở mức ranh giới nhẹ.", "Exclude pregnancy-related or borderline readings."))

        bp_choice = st.radio(
            tr("Huyết áp cao", "High Blood Pressure"),
            options=["no", "yes", "unknown"],
            index=get_idx(["no", "yes", "unknown"], F.get("bp", "no")),
            format_func=lambda v: UNKNOWN_MAP[v],
            horizontal=True,
            key="w_bp",
            label_visibility="collapsed",
        )
        F["bp"] = bp_choice

    # =======================================================
    # QUESTION 4: HIGH CHOLESTEROL
    # =======================================================
    elif step == 4:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
            <span>{tr("4. Bạn đã từng được thông báo có chỉ số Mỡ máu (Cholesterol) cao chưa? *", "4. Have you ever been told that your Blood Cholesterol is high? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Chọn 'Không rõ' nếu bạn chưa từng xét nghiệm mỡ máu.", "Select 'Unknown' if you have never been tested."))

        chol_choice = st.radio(
            tr("Mỡ máu cao", "High Cholesterol"),
            options=["no", "yes", "unknown"],
            index=get_idx(["no", "yes", "unknown"], F.get("chol", "no")),
            format_func=lambda v: UNKNOWN_MAP[v],
            horizontal=True,
            key="w_chol",
            label_visibility="collapsed",
        )
        F["chol"] = chol_choice

    # =======================================================
    # QUESTION 5: GENERAL HEALTH
    # =======================================================
    elif step == 5:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>
            <span>{tr("5. Bạn tự đánh giá sức khỏe tổng quát của mình ở mức nào? *", "5. How would you rate your General Health overall? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Đánh giá cảm nhận chung về thể trạng hiện tại của bạn.", "Your perceived current overall health."))

        health_choice = st.radio(
            tr("Sức khỏe tổng quát", "General Health"),
            options=health_values,
            index=get_idx(health_values, str(F.get("health", "2")), 1),
            format_func=lambda v: health_map[v],
            horizontal=True,
            key="w_health",
            label_visibility="collapsed",
        )
        F["health"] = health_choice

    # =======================================================
    # QUESTION 6: SMOKER
    # =======================================================
    elif step == 6:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><path d="M18 12H2v4h16"/><path d="M22 12v4"/><path d="M18 8c0-2-2-2-2-4"/></svg>
            <span>{tr("6. Bạn đã từng hút ít nhất 100 điếu thuốc lá trong đời chưa? *", "6. Have you smoked at least 100 cigarettes in your entire life? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Tính cộng dồn khoảng 5 bao thuốc trong suốt cuộc đời, không cần đang hút hiện tại.", "Approximately 5 packs across your lifetime."))

        smoker_choice = st.radio(
            tr("Hút thuốc", "Smoker"),
            options=["no", "yes"],
            index=get_idx(["no", "yes"], F.get("smoker", "no")),
            format_func=lambda v: YES_NO_MAP[v],
            horizontal=True,
            key="w_smoker",
            label_visibility="collapsed",
        )
        F["smoker"] = smoker_choice

    # =======================================================
    # QUESTION 7: PHYSICAL ACTIVITY
    # =======================================================
    elif step == 7:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span>{tr("7. Trong 30 ngày qua, bạn có vận động thể chất ngoài công việc chính không? *", "7. Have you done physical activity or exercise in the past 30 days (other than your regular job)? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Ví dụ: đi bộ tập thể dục, chạy bộ, đạp xe, bơi lội hoặc thể thao.", "Such as walking, running, cycling, swimming, or sports."))

        activity_choice = st.radio(
            tr("Vận động thể chất", "Physical Activity"),
            options=["yes", "no"],
            index=get_idx(["yes", "no"], F.get("activity", "yes")),
            format_func=lambda v: YES_NO_MAP[v],
            horizontal=True,
            key="w_activity",
            label_visibility="collapsed",
        )
        F["activity"] = activity_choice

    # =======================================================
    # QUESTION 8: DIFFICULTY WALKING
    # =======================================================
    elif step == 8:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.75rem;color:#1D4ED8;font-size:1.08rem;font-weight:700;">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2"><circle cx="12" cy="4" r="2"/><path d="M15 22v-5l-3-3 1-5 3 2h3"/><path d="M9 14l-2 8"/><path d="M9 9l3-1"/></svg>
            <span>{tr("8. Bạn có gặp khó khăn nghiêm trọng khi đi bộ hoặc leo cầu thang không? *", "8. Do you have serious difficulty walking or climbing stairs? *")}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(tr("Khó khăn đáng kể về vận động chi dưới theo tình trạng hiện tại.", "Mobility limitations affecting walking or stair climbing."))

        walk_choice = st.radio(
            tr("Khó khăn đi bộ", "Difficulty Walking"),
            options=["no", "yes"],
            index=get_idx(["no", "yes"], F.get("walk", "no")),
            format_func=lambda v: YES_NO_MAP[v],
            horizontal=True,
            key="w_walk",
            label_visibility="collapsed",
        )
        F["walk"] = walk_choice


# Navigation Bar
st.write("")
col_prev, col_next = st.columns([1, 1.2], gap="medium")

with col_prev:
    if step > 1:
        if st.button(tr("← Câu trước", "← Previous"), use_container_width=True):
            S["assess_step"] = step - 1
            st.rerun()

with col_next:
    if step < TOTAL_STEPS:
        if st.button(
            tr("Câu tiếp theo →", "Next Question →"),
            type="primary",
            use_container_width=True,
            disabled=bmi_error,
        ):
            S["assess_step"] = step + 1
            st.rerun()
    else:
        if st.button(
            tr("Hoàn tất & Xem Kết quả →", "Complete & Assess Risk →"),
            type="primary",
            use_container_width=True,
        ):
            bmi_final = float(F.get("weight", 62.0)) / ((float(F.get("height", 165.0)) / 100.0) ** 2)
            bp_in = F.get("bp", "no")
            chol_in = F.get("chol", "no")

            answers = {
                "Age": int(F.get("age", 5)),
                "BMI": float(bmi_final),
                "HighBP": int(bp_in == "yes") if bp_in != "unknown" else float("nan"),
                "HighChol": int(chol_in == "yes") if chol_in != "unknown" else float("nan"),
                "GenHlth": int(F.get("health", 2)),
                "Smoker": int(F.get("smoker", "no") == "yes"),
                "PhysActivity": int(F.get("activity", "yes") == "yes"),
                "DiffWalk": int(F.get("walk", "no") == "yes"),
            }

            with st.spinner(tr("Mô hình đang tính toán xác suất phân loại...", "Generating screening assessment...")):
                try:
                    prob = predict(answers)
                    S["answers"] = answers
                    S["probability"] = prob
                    S["assess_step"] = 1
                    st.switch_page("pages/2_My_Results.py")
                except Exception as e:
                    st.error(f"{tr('Lỗi tính toán:', 'Calculation error:')} {e}") code page 1. code page 2 import math
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

render_floating_ai_assistant(ai_context). Code page 3 import streamlit as st
from utils.ui import style, tr, html, GLUCOMETER_SVG

style()


st.markdown(f"""
<div style="margin-bottom:1.5rem;">
    <h2 style="margin:0;font-size:1.85rem;font-weight:800;color:#142D4E;letter-spacing:-0.02em;">
        {tr("Giới thiệu về GlucoGuide", "About GlucoGuide")}
    </h2>
    <div style="font-size:0.92rem;color:#5B6B82;margin-top:3px;">
        {tr("Tìm hiểu thêm về công cụ sàng lọc nguy cơ tiểu đường thông minh của chúng tôi",
            "Learn more about our intelligent diabetes risk screening tool")}
    </div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.3, 1.0], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex;gap:12px;align-items:flex-start;">
            <div style="width:38px;height:38px;border-radius:10px;background:#EFF6FF;display:flex;align-items:center;justify-content:center;color:#1D4ED8;flex:0 0 38px;">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                </svg>
            </div>
            <div>
                <div style="font-size:1.05rem;font-weight:700;color:#142D4E;">{tr("GlucoGuide là gì?", "What is GlucoGuide?")}</div>
                <div style="font-size:0.88rem;color:#475569;line-height:1.55;margin-top:4px;">
                    {tr("GlucoGuide là công cụ hỗ trợ sàng lọc sức khỏe thông minh, ứng dụng học máy để nhận diện các quy luật nguy cơ liên quan đến bệnh đái tháo đường từ tập dữ liệu khảo sát sức khỏe hành vi CDC BRFSS 2015.",
                        "GlucoGuide is an intelligent screening tool using machine learning to identify risk patterns associated with diabetes based on the CDC BRFSS 2015 behavioral health survey dataset.")}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex;gap:12px;align-items:flex-start;">
            <div style="width:38px;height:38px;border-radius:10px;background:#EFF6FF;display:flex;align-items:center;justify-content:center;color:#1D4ED8;flex:0 0 38px;">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1D4ED8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                </svg>
            </div>
            <div>
                <div style="font-size:1.05rem;font-weight:700;color:#142D4E;">{tr("Quy trình hoạt động như thế nào?", "How Does It Work?")}</div>
                <div style="font-size:0.88rem;color:#475569;line-height:1.55;margin-top:4px;">
                    {tr("Chỉ với 8 câu hỏi khảo sát ngắn gọn về thông tin thể chất, tiền sử sức khỏe và thói quen sinh hoạt, mô hình sẽ phân tích tức thì và cung cấp kết quả kèm Trợ lý AI đồng hành.",
                        "Answer 8 short questions about your physical metrics, health history, and lifestyle habits. The model analyzes your inputs instantly and presents your result alongside our AI Assistant.")}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex;gap:12px;align-items:flex-start;">
            <div style="width:38px;height:38px;border-radius:10px;background:#FEF2F2;display:flex;align-items:center;justify-content:center;color:#DC2626;flex:0 0 38px;">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
            </div>
            <div>
                <div style="font-size:1.05rem;font-weight:700;color:#142D4E;">{tr("Lưu ý Y khoa Quan trọng", "Important Medical Notes")}</div>
                <ul style="font-size:0.88rem;color:#475569;line-height:1.6;margin:6px 0 0;padding-left:18px;">
                    <li>{tr("Công cụ phục vụ mục đích giáo dục và sàng lọc phòng ngừa.", "This tool is intended for educational screening purposes only.")}</li>
                    <li>{tr("Công cụ KHÔNG thay thế chẩn đoán y khoa chính thức.", "It does NOT diagnose diabetes or provide clinical diagnosis.")}</li>
                    <li>{tr("Luôn tham khảo ý kiến bác sĩ và làm xét nghiệm máu định kỳ.", "Always consult a qualified healthcare professional for medical advice.")}</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_right:
    with st.container(border=True):
        html(f"""
        <div style="text-align:center;padding:1rem 0;">
            {GLUCOMETER_SVG}
            <div style="font-size:1.15rem;font-weight:800;color:#142D4E;margin-top:1rem;">
                {tr("Hệ thống Sàng lọc GlucoGuide", "GlucoGuide Screening System")}
            </div>
            <div style="font-size:0.84rem;color:#5B6B82;max-width:260px;margin:4px auto 1.2rem;">
                {tr("Sàng lọc thông minh hơn. Tương lai khỏe mạnh hơn.", "Smarter Screening. Healthier Tomorrow.")}
            </div>
        </div>
        """)

        if st.button(tr("Bắt đầu Khảo sát Ngay →", "Start Risk Assessment →"), type="primary", use_container_width=True):
            st.session_state["assess_step"] = 1
            st.switch_page("pages/1_Risk_Assessment.py"). code page 4import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import ROOT, meta, SPECS
from utils.i18n import age_labels
from utils.ui import style, tr, html, simulator, tuned_model_threshold_explorer, GLUCOMETER_SVG

style()

m = meta()
metrics = m["test_metrics"]
cm_raw = metrics["confusion_matrix"]
tn, fp = int(cm_raw[0][0]), int(cm_raw[0][1])
fn, tp = int(cm_raw[1][0]), int(cm_raw[1][1])

accuracy = (tn + tp) / max(metrics["n"], 1)
prec_0 = tn / (tn + fn) if (tn + fn) else 0.0
rec_0 = tn / (tn + fp) if (tn + fp) else 0.0
f1_0 = 2 * prec_0 * rec_0 / (prec_0 + rec_0) if (prec_0 + rec_0) else 0.0
prec_1 = float(metrics["precision"])
rec_1 = float(metrics["recall"])
f1_1 = float(metrics["f1"])


def svg(path, size=18, color="#1D4ED8"):
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:block;flex:0 0 {size}px">{path}</svg>'
    )


IC_DB = svg('<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/>', 20)
IC_CPU = svg('<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>', 20)
IC_GEAR = svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.26.6.77 1.02 1.4 1.1H21a2 2 0 0 1 0 4h-.09c-.63.08-1.14.5-1.51 1.1z"/>', 19)
IC_USER = svg('<circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-6 8-6s8 2 8 6"/>', 19)
IC_CHART = svg('<path d="M3 3v18h18"/><rect x="7" y="10" width="3" height="7" rx="1"/><rect x="12" y="6" width="3" height="11" rx="1"/><rect x="17" y="13" width="3" height="4" rx="1"/>', 19)
IC_TARGET = svg('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>', 16)
IC_SCALE = svg('<path d="M12 3v18M5 7h14"/><path d="M5 7l-2.5 6a3 3 0 0 0 5 0L5 7zM19 7l-2.5 6a3 3 0 0 0 5 0L19 7z"/><path d="M8 21h8"/>', 16)
IC_REFRESH = svg('<path d="M21 12a9 9 0 0 0-15.5-6.3L3 8"/><path d="M3 3v5h5"/><path d="M3 12a9 9 0 0 0 15.5 6.3L21 16"/><path d="M21 21v-5h-5"/>', 16)
IC_TREND = svg('<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>', 16)
IC_BULB = svg('<path d="M9 18h6M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>', 19)
IC_INFO = svg('<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>', 17, "#1E40AF")
IC_SHIELD = svg('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>', 18)
IC_ALERT = svg('<circle cx="12" cy="12" r="10"/><path d="M12 8v5M12 16h.01"/>', 18)
IC_STETH = svg('<path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/><path d="M8 15v1a6 6 0 0 0 6 6 6 6 0 0 0 6-6v-4"/><circle cx="20" cy="10" r="2"/>', 18)

st.markdown("""
<style>
.st-key-about_hero{
    background:linear-gradient(125deg,#FFFFFF 0%,#F2F7FF 55%,#DCEBFE 100%);
    border:1px solid #DCE7F7;
    border-radius:22px;
    padding:1.8rem 2rem;
    box-shadow:0 6px 24px rgba(20,45,78,.04);
}
.st-key-about_works, .st-key-about_card{
    background:#FFFFFF;
    border:1px solid #E2EAF4;
    border-radius:20px;
    padding:1.4rem 1.6rem;
    box-shadow:0 4px 18px rgba(29,78,216,.04);
}
.st-key-about_limits{
    background:linear-gradient(120deg,#EFF6FF 0%,#F8FAFC 65%,#E0ECFF 100%);
    border:1px solid #D8E5F8;
    border-radius:20px;
    padding:1.3rem 1.6rem;
}
.pill-ai{
    display:inline-block;
    background:#2563EB;
    color:#FFFFFF;
    font-size:.72rem;
    font-weight:700;
    letter-spacing:.6px;
    padding:4px 12px;
    border-radius:999px;
    margin-bottom:.6rem;
}
.about-h1{font-size:2.35rem;font-weight:800;color:#142D4E;letter-spacing:-0.8px;line-height:1.1;margin:0 0 .5rem}
.about-sub{font-size:1.08rem;font-weight:700;color:#142D4E;margin-bottom:.45rem}
.about-p{font-size:.93rem;color:#5B6B82;line-height:1.55;margin-bottom:1rem;max-width:34rem}

.mini-cards{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.mini-card{
    display:flex;gap:12px;align-items:center;
    background:rgba(255,255,255,.88);
    border:1px solid #D7E4F8;
    border-radius:14px;
    padding:12px 14px;
}
.mini-card .mic{
    width:40px;height:40px;border-radius:11px;background:#DBEAFE;
    display:flex;align-items:center;justify-content:center;flex:0 0 40px
}
.mini-card .mt{font-weight:700;font-size:.9rem;color:#142D4E;line-height:1.2}
.mini-card .md{font-size:.79rem;color:#5B6B82;margin-top:2px;line-height:1.35}

.sec-hdr{display:flex;align-items:center;gap:10px;font-size:1.1rem;font-weight:800;color:#142D4E;margin-bottom:.3rem}
.sec-sub{font-size:.86rem;color:#5B6B82;margin-bottom:1rem}

.flow-wrap{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;gap:10px;align-items:start;margin-top:.7rem}
.flow-step{display:flex;gap:10px;align-items:flex-start}
.flow-num{
    width:24px;height:24px;border-radius:50%;background:#2563EB;color:#fff;
    font-size:.76rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex:0 0 24px;margin-top:2px
}
.flow-ico{margin-bottom:6px}
.flow-tt{font-weight:700;font-size:.88rem;color:#142D4E;margin-bottom:2px}
.flow-dd{font-size:.79rem;color:#5B6B82;line-height:1.4}
.flow-arr{color:#3B82F6;font-size:1.1rem;font-weight:700;padding-top:14px}

.kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:1rem}
.kpi-box{background:#F8FAFC;border:1px solid #E2EAF4;border-radius:14px;padding:14px 12px;text-align:center}
.kpi-top{display:flex;align-items:center;justify-content:center;gap:6px;font-size:.84rem;color:#5B6B82;font-weight:600}
.kpi-val{font-size:1.7rem;font-weight:800;color:#142D4E;margin-top:4px;line-height:1.1}

.crep{width:100%;border-collapse:collapse;font-size:.86rem;margin-top:.35rem}
.crep th{color:#5B6B82;font-weight:700;text-align:center;padding:10px 8px;border-bottom:1px solid #DCE5F2;background:#F8FAFC}
.crep th:first-child{text-align:left}
.crep td{padding:10px 8px;text-align:center;color:#142D4E;border-bottom:1px solid #F1F5F9}
.crep td:first-child{text-align:left;font-weight:700}

.lim-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:16px;align-items:start}
.lim-item{display:flex;gap:10px;align-items:flex-start}
.lim-ic{width:34px;height:34px;border-radius:10px;background:#DBEAFE;display:flex;align-items:center;justify-content:center;flex:0 0 34px}
.lim-tt{font-weight:700;font-size:.88rem;color:#142D4E;line-height:1.25}
.lim-dd{font-size:.8rem;color:#5B6B82;line-height:1.4;margin-top:3px}

@media(max-width:900px){
    .mini-cards,.kpi-grid,.lim-grid{grid-template-columns:1fr 1fr}
    .flow-wrap{grid-template-columns:1fr}
    .flow-arr{display:none}
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# 1. HERO BANNER: Behind GlucoGuide
# ==================================================
with st.container(key="about_hero"):
    h_left, h_right = st.columns([6.2, 4.2], vertical_alignment="center", gap="large")
    with h_left:
        html(f"""
        <div class="pill-ai">{tr("CHẾ ĐỘ GIẢNG VIÊN · BÁO CÁO KỸ THUẬT", "TEACHER MODE · TECHNICAL OVERVIEW")}</div>
        <div class="about-h1">{tr("Kiến trúc & Kiểm định GlucoGuide", "Behind GlucoGuide")}</div>
        <div class="about-sub">{tr("Cách mô hình phân loại nhãn khảo sát được xây dựng và thẩm định.", "How the survey-label classifier was built and evaluated.")}</div>
        <div class="about-p">
            {tr(
                f"GlucoGuide là nguyên mẫu học thuật được huấn luyện trên {m['rows']:,} bản ghi khảo sát BRFSS 2015 tại Hoa Kỳ, phân tích {len(m['features'])} chỉ số sức khỏe để tạo điểm phân loại cho nhãn tự khai báo.",
                f"GlucoGuide is an educational university prototype trained on {m['rows']:,} US 2015 survey records (BRFSS) to analyse {len(m['features'])} health indicators and produce a score for a self-reported survey label."
            )}
        </div>
        <div class="mini-cards">
            <div class="mini-card">
                <div class="mic">{IC_DB}</div>
                <div>
                    <div class="mt">{tr("Dữ liệu Huấn luyện", "Training Data")}</div>
                    <div class="md">{tr(f"Khảo sát CDC BRFSS 2015 ({m['rows']:,} dòng)", f"US 2015 BRFSS survey ({m['rows']:,} records)")}</div>
                </div>
            </div>
            <div class="mini-card">
                <div class="mic">{IC_CPU}</div>
                <div>
                    <div class="mt">{tr("Thuật toán Học máy", "ML Algorithm")}</div>
                    <div class="md">{m['algorithm']} ({len(m['features'])} {tr("đặc trưng", "inputs")})</div>
                </div>
            </div>
        </div>
        """)
    with h_right:
        html(f'<div style="text-align:center">{GLUCOMETER_SVG}</div>')

st.write("")

# ==================================================
# 2. HOW GLUCOGUIDE WORKS (4 STEPS)
# ==================================================
with st.container(key="about_works"):
    html(f"""
    <div class="sec-hdr">{IC_GEAR}<span>{tr("Quy trình Xử lý của Hệ thống", "How GlucoGuide Works")}</span></div>
    <div class="flow-wrap">
        <div class="flow-step">
            <div class="flow-num">1</div>
            <div>
                <div class="flow-ico">{IC_USER}</div>
                <div class="flow-tt">{tr("Thông tin Đầu vào", "User Information")}</div>
                <div class="flow-dd">{tr("Người dùng cung cấp 8 chỉ số sức khỏe qua bảng khảo sát từng bước.", "Users provide 8 selected health indicators through the stepped form.")}</div>
            </div>
        </div>
        <div class="flow-arr">→</div>
        <div class="flow-step">
            <div class="flow-num">2</div>
            <div>
                <div class="flow-ico">{IC_DB}</div>
                <div class="flow-tt">{tr("Tiền xử lý Dữ liệu", "Data Preprocessing")}</div>
                <div class="flow-dd">{tr("Chiều cao & cân nặng tự quy đổi thành BMI; mã hóa trong Pipeline.", "Height & weight convert to BMI; inputs are cleaned and encoded.")}</div>
            </div>
        </div>
        <div class="flow-arr">→</div>
        <div class="flow-step">
            <div class="flow-num">3</div>
            <div>
                <div class="flow-ico">{IC_CPU}</div>
                <div class="flow-tt">{tr("Suy luận Học máy", "Machine Learning Prediction")}</div>
                <div class="flow-dd">{tr("Mô hình phân tích các quy luật tương quan và sinh điểm xác suất.", "The trained model analyses patterns and generates a classifier score.")}</div>
            </div>
        </div>
        <div class="flow-arr">→</div>
        <div class="flow-step">
            <div class="flow-num">4</div>
            <div>
                <div class="flow-ico">{IC_CHART}</div>
                <div class="flow-tt">{tr("Điểm Nhãn Khảo sát", "Survey-label Score")}</div>
                <div class="flow-dd">{tr("Trả về điểm phân loại kèm giải thích Exact Shapley, không phải chẩn đoán.", "Returns a classifier score and Shapley explanation, not a diagnosis.")}</div>
            </div>
        </div>
    </div>
    """)

st.write("")

# ==================================================
# 3. SIX TABS (CLEAN TEXT WITHOUT EMOJIS)
# ==================================================
tabs = st.tabs([
    tr("Hiệu năng & Yếu tố", "Performance & Factors"),
    tr("Ngưỡng & Chi phí", "Threshold & Costs"),
    tr("Công bằng (Fairness)", "Fairness"),
    tr("Dữ liệu & Quyết định", "Data & Decisions"),
    tr("Model Card Đầy đủ", "Full Model Card"),
    tr("PCA & Chọn Đặc trưng", "PCA & Feature Selection"),
])

# ==================================================
# TAB 1 — PERFORMANCE & FACTORS
# ==================================================
with tabs[0]:
    with st.container(key="about_card"):
        html(f"""
        <div class="sec-hdr">{IC_CHART}<span>{tr("Hiệu năng Mô hình trên Tập Test Độc lập", "Model Performance")}</span></div>
        <div class="sec-sub">
            {tr(
                f"Đánh giá một lần duy nhất trên tập kiểm tra cách ly gồm {metrics['n']:,} bản ghi. Ngưỡng mặc định cố định: <b>{m['threshold']:.4f}</b>. Việc điều chỉnh mô phỏng không làm thay đổi kết quả này.",
                f"Evaluation on an untouched held-out test set of {metrics['n']:,} records. Fixed default threshold: <b>{m['threshold']:.4f}</b>. Simulator adjustments do not change these test results."
            )}
        </div>
        <div class="kpi-grid">
            <div class="kpi-box">
                <div class="kpi-top">{IC_TARGET}<span>{tr("Độ chính xác (Accuracy)", "Accuracy")}</span></div>
                <div class="kpi-val">{accuracy:.3f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-top">{IC_SCALE}<span>{tr("Độ chuẩn xác (Precision)", "Precision")}</span></div>
                <div class="kpi-val">{prec_1:.3f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-top">{IC_REFRESH}<span>{tr("Độ nhạy (Recall)", "Recall")}</span></div>
                <div class="kpi-val">{rec_1:.3f}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-top">{IC_TREND}<span>ROC-AUC</span></div>
                <div class="kpi-val">{metrics['roc_auc']:.3f}</div>
            </div>
        </div>
        """)

        c1, c2, c3 = st.columns(3)
        c1.metric("F1-score", f"{f1_1:.3f}")
        c2.metric(tr("Độ chuẩn xác TB (PR-AUC)", "Average precision"), f"{metrics['average_precision']:.3f}")
        c3.metric(tr("Điểm Brier (thấp hơn là tốt hơn)", "Brier score (lower is better)"), f"{metrics['brier']:.3f}")

        st.write("")
        col_l, col_r = st.columns(2, gap="large")

        with col_l:
            st.markdown(f"**{tr('Đường cong ROC', 'ROC Curve')}**")
            roc = pd.read_csv(ROOT / "models/roc.csv")
            fig_roc = px.line(
                roc, x="FPR", y="Recall",
                labels={
                    "FPR": tr("Tỷ lệ dương tính giả (FPR)", "False positive rate"),
                    "Recall": tr("Tỷ lệ dương tính thật (TPR)", "True positive rate"),
                },
            )
            fig_roc.update_traces(line=dict(color="#1D4ED8", width=2.5))
            fig_roc.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(color="#94A3B8", dash="dot", width=1.2))
            fig_roc.update_xaxes(automargin=True, range=[0, 1])
            fig_roc.update_yaxes(automargin=True, range=[0, 1])
            fig_roc.update_layout(template="simple_white", height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_roc, use_container_width=True)

        with col_r:
            st.markdown(f"**{tr('Ma trận Nhầm lẫn (Tập Test)', 'Test Confusion Matrix')}**")
            cm_df = pd.DataFrame(
                [[tn, fp], [fn, tp]],
                index=[tr("Thực tế: 0", "Actual 0"), tr("Thực tế: 1", "Actual 1")],
                columns=[tr("Dự báo: Không gắn cờ", "Not flagged"), tr("Dự báo: Gắn cờ", "Flagged")],
            )
            fig_cm = px.imshow(
                cm_df,
                text_auto=True,
                color_continuous_scale=["#EFF6FF", "#BFDBFE", "#3B82F6", "#1D4ED8"],
                aspect="auto",
                labels={
                    "x": tr("Nhãn dự báo", "Predicted classification"),
                    "y": tr("Nhãn thực tế", "Actual label"),
                    "color": tr("Số bản ghi", "Records"),
                },
            )
            fig_cm.update_xaxes(automargin=True)
            fig_cm.update_yaxes(automargin=True)
            fig_cm.update_layout(template="simple_white", height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_cm, use_container_width=True)

        st.write("")
        col_b1, col_b2 = st.columns(2, gap="large")

        with col_b1:
            st.markdown(f"**{tr('Báo cáo Phân loại (Tập Test)', 'Classification Report (Test Set)')}**")
            html(f"""
            <table class="crep">
                <thead>
                    <tr>
                        <th>{tr("Lớp (Class)", "Class")}</th>
                        <th>Precision</th>
                        <th>Recall</th>
                        <th>F1-Score</th>
                        <th>{tr("Số mẫu", "Support")}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{tr("Không có nhãn tiểu đường (0)", "No diabetes label (0)")}</td>
                        <td>{prec_0:.3f}</td>
                        <td>{rec_0:.3f}</td>
                        <td>{f1_0:.3f}</td>
                        <td>{tn + fp:,}</td>
                    </tr>
                    <tr>
                        <td>{tr("Tiểu đường / tiền tiểu đường (1)", "Diabetes / prediabetes (1)")}</td>
                        <td>{prec_1:.3f}</td>
                        <td>{rec_1:.3f}</td>
                        <td>{f1_1:.3f}</td>
                        <td>{fn + tp:,}</td>
                    </tr>
                </tbody>
            </table>
            """)
            st.write("")
            st.markdown(f"**{tr('Đường cong Precision–Recall', 'Precision–Recall Curve')}**")
            pr = pd.read_csv(ROOT / "models/pr.csv")
            fig_pr = px.line(
                pr, x="Recall", y="Precision",
                labels={"Recall": tr("Độ nhạy (Recall)", "Recall"), "Precision": tr("Độ chuẩn xác (Precision)", "Precision")},
            )
            fig_pr.update_traces(line=dict(color="#2563EB", width=2.5))
            fig_pr.update_xaxes(automargin=True)
            fig_pr.update_yaxes(automargin=True)
            fig_pr.update_layout(template="simple_white", height=250, margin=dict(l=20, r=20, t=15, b=20))
            st.plotly_chart(fig_pr, use_container_width=True)

        with col_b2:
            html(f"""
            <div class="sec-hdr">{IC_BULB}<span>{tr("Mô hình Xem xét Những Yếu tố Nào?", "What Factors Does the Model Consider?")}</span></div>
            <div class="sec-sub">{tr("Tầm quan trọng hoán vị trên tập Validation (mức giảm ROC-AUC khi xáo trộn biến):", "Validation permutation importance (ROC-AUC drop when shuffled):")}</div>
            """)
            imp = pd.read_csv(ROOT / "reports/permutation_importance.csv")
            feat_col = next((c for c in imp.columns if c.lower() in ("feature", "predictor", "name")), imp.columns[0])
            val_col = next((c for c in imp.columns if pd.api.types.is_numeric_dtype(imp[c])), imp.columns[1])

            sub_imp = imp[imp[feat_col].isin(m["features"])].copy()
            name_map = {
                "Age": tr("Độ tuổi", "Age"),
                "BMI": "BMI",
                "HighBP": tr("Huyết áp cao", "High Blood Pressure"),
                "HighChol": tr("Mỡ máu cao", "High Cholesterol"),
                "GenHlth": tr("Sức khỏe tổng quát", "General Health"),
                "Smoker": tr("Tiền sử hút thuốc", "Smoking history"),
                "PhysActivity": tr("Vận động thể chất", "Leisure-time activity"),
                "DiffWalk": tr("Khó khăn đi bộ", "Walking difficulty"),
            }
            sub_imp["Factor"] = sub_imp[feat_col].map(lambda x: name_map.get(x, str(x)))
            sub_imp = sub_imp.sort_values(val_col, ascending=True)

            vals = sub_imp[val_col].tolist()
            factors = sub_imp["Factor"].tolist()
            bar_colors = ["#F97316" if v < 0 else "#2563EB" for v in vals]

            fig_imp = px.bar(
                sub_imp,
                x=val_col,
                y="Factor",
                orientation="h",
                labels={val_col: tr("Mức giảm ROC-AUC", "ROC-AUC drop"), "Factor": ""},
            )
            fig_imp.update_traces(marker_color=bar_colors, text=None, textposition="none", cliponaxis=False)

            # Annotations: all numbers on the RIGHT side
            min_x = min(float(sub_imp[val_col].min()) * 1.35, -0.02)
            max_x = max(float(sub_imp[val_col].max()) * 1.42, 0.07)
            ann_offset = (max_x - min_x) * 0.012  # small gap from bar tip / axis
            for factor, val in zip(factors, vals):
                x_pos = val + ann_offset if val >= 0 else ann_offset * 0.5
                font_color = "#EA580C" if val < 0 else "#1E40AF"
                fig_imp.add_annotation(
                    x=x_pos, y=factor,
                    text=f"{val:.4f}",
                    showarrow=False,
                    xanchor="left",
                    yanchor="middle",
                    font=dict(color=font_color, size=11, family="monospace"),
                )

            fig_imp.update_xaxes(automargin=True, range=[min_x, max_x])
            fig_imp.update_yaxes(automargin=True)
            fig_imp.update_layout(template="simple_white", height=310, margin=dict(l=160, r=70, t=10, b=20))
            st.plotly_chart(fig_imp, use_container_width=True)

            html(f"""
            <div class="callout-blue" style="padding:12px 14px;font-size:.84rem">
                {IC_INFO}
                <span>{tr(
                    "Tầm quan trọng của biến phản ánh ảnh hưởng tổng thể lên ROC-AUC trên tập validation và không hàm ý quan hệ nhân quả cho từng cá nhân.",
                    "Feature importance reflects overall influence on validation ROC-AUC and does not imply causation for an individual case."
                )}</span>
            </div>
            """)

        st.divider()
        st.markdown(f"**{tr('So sánh Số lượng Câu hỏi Khảo sát', 'Questionnaire size comparison')}**")
        size_path = ROOT / "reports/questionnaire_size_comparison.csv"
        if size_path.exists():
            size_df = pd.read_csv(size_path)
            st.dataframe(
                size_df[["questionnaire", "feature_count", "roc_auc", "average_precision", "brier"]].rename(columns={
                    "questionnaire": tr("Bộ câu hỏi", "Question set"),
                    "feature_count": tr("Số biến", "Inputs"),
                    "roc_auc": tr("ROC-AUC (Val)", "Validation ROC-AUC"),
                    "average_precision": tr("PR-AUC (Val)", "Validation Average Precision"),
                    "brier": tr("Điểm Brier (Val)", "Validation Brier score"),
                }),
                hide_index=True,
                use_container_width=True,
            )
            st.caption(tr(
                "Giữ nguyên cấu hình HGB và tập phân chia trên 5, 8 và 21 biến. Bộ 21 biến là mốc tham chiếu; bộ 8 biến giúp rút gọn khảo sát và tránh các câu hỏi nhạy cảm.",
                "Same HGB settings and data split across 5, 8, and 21 inputs. The 21-input model is a benchmark; the 8-input form keeps the questionnaire compact."
            ))

        st.divider()
        st.markdown(f"**{tr('So sánh Các Mô hình đã Tinh chỉnh (Tuned Models)', 'Tuned course-model comparison')}**")
        tuned_path = ROOT / "reports/tuned_model_validation.csv"
        if tuned_path.exists():
            comparison = pd.read_csv(tuned_path)
            columns = [
                "model", "validation_roc_auc", "validation_average_precision",
                "cost_selected_threshold", "precision_at_cost_threshold",
                "recall_at_cost_threshold", "f1_at_cost_threshold",
            ]
            display = comparison[columns].rename(columns={
                "model": tr("Mô hình", "Model"),
                "validation_roc_auc": "ROC-AUC",
                "validation_average_precision": tr("Average Precision", "Average precision"),
                "cost_selected_threshold": tr("Ngưỡng chọn theo chi phí", "Cost-selected threshold"),
                "precision_at_cost_threshold": tr("Precision tại ngưỡng", "Precision at threshold"),
                "recall_at_cost_threshold": tr("Recall tại ngưỡng", "Recall at threshold"),
                "f1_at_cost_threshold": tr("F1 tại ngưỡng", "F1 at threshold"),
            })
            st.dataframe(display, hide_index=True, use_container_width=True)

        st.divider()
        st.markdown(f"**{tr('Kiểm định Độ tin cậy Điểm số trên Tập Test', 'Test-set score reliability')}**")
        calibration_path = ROOT / "reports/test_calibration_by_decile.csv"
        if calibration_path.exists():
            calibration = pd.read_csv(calibration_path)
            fig_cal = px.scatter(
                calibration, x="mean_score", y="observed_label_rate", size="n",
                hover_data=["score_decile", "n"],
                labels={
                    "mean_score": tr("Điểm phân loại trung bình", "Mean classifier score"),
                    "observed_label_rate": tr("Tỷ lệ nhãn dương quan sát", "Observed survey-label rate"),
                },
            )
            fig_cal.update_traces(marker=dict(color="#1D4ED8"))
            fig_cal.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(dash="dot", color="#94A3B8"))
            fig_cal.update_layout(template="simple_white", height=330)
            st.plotly_chart(fig_cal, use_container_width=True)
            ci_path = ROOT / "reports/test_cluster_bootstrap_intervals.csv"
            if ci_path.exists():
                st.dataframe(pd.read_csv(ci_path), hide_index=True, use_container_width=True)

# ==================================================
# TAB 2 — THRESHOLD & COSTS
# ==================================================
with tabs[1]:
    st.subheader(tr("Ngưỡng phân loại và Chi phí quyết định", "Threshold and decision costs"))
    st.write(tr(
        "Ngưỡng phân loại quyết định khi nào một bản ghi bị gắn cờ. Trình mô phỏng dưới đây cho phép giảng viên thử nghiệm trọng số phạt dương tính giả (FP) và âm tính giả (FN) minh họa — không phải chi phí y tế thực tế.",
        "The classification threshold determines when a prediction is flagged. The cost simulator lets instructors examine illustrative FP and FN penalties for survey-label classification (not clinical costs)."
    ))
    simulator(m, "about")
    cost_path = ROOT / "reports/threshold_cost_sensitivity.csv"
    if cost_path.exists():
        st.markdown(f"**{tr('Độ nhạy theo tỷ lệ phạt giả định', 'Sensitivity to assumed error penalties')}**")
        st.dataframe(pd.read_csv(cost_path), hide_index=True, use_container_width=True)
    uncertainty_path = ROOT / "reports/model_selection_bootstrap.csv"
    if uncertainty_path.exists():
        st.markdown(f"**{tr('So sánh Bootstrap theo cặp trên Validation (khám phá)', 'Paired validation comparison (exploratory)')}**")
        st.dataframe(pd.read_csv(uncertainty_path), hide_index=True, use_container_width=True)
    st.divider()
    st.subheader(tr("So sánh ngưỡng tùy chỉnh giữa các mô hình đã tinh chỉnh", "Compare adjustable thresholds across tuned models"))
    tuned_model_threshold_explorer(m, "course_models")

# ==================================================
# TAB 3 — FAIRNESS
# ==================================================
with tabs[2]:
    st.subheader(tr("Kiểm định Hiệu năng theo Nhóm Nhân khẩu học", "Group-level performance audit"))
    st.write(tr(
        "Mục này báo cáo sự khác biệt mô tả trên tập kiểm tra qua các nhóm nhân khẩu học và kinh tế xã hội.",
        "This section reports descriptive test-set differences across selected demographic and socioeconomic groups."
    ))
    st.caption(tr(
        "Các số liệu này không chứng minh tính công bằng tuyệt đối. Chênh lệch có thể phản ánh đặc điểm lấy mẫu, khả năng tiếp cận chẩn đoán y tế và sai số tự khai báo.",
        "These results do not establish fairness. Differences may reflect sampling, prevalence, access to diagnosis, and label ascertainment."
    ))

    fair = pd.read_csv(ROOT / "models/fairness.csv")
    group_map = {
        "Age": tr("Độ tuổi (Age)", "Age"),
        "Sex": tr("Giới tính (Sex)", "Sex"),
        "Income": tr("Thu nhập (Income)", "Income"),
        "Education": tr("Học vấn (Education)", "Education"),
    }
    group = st.selectbox(
        tr("Chiều phân tích", "Audit dimension"),
        ["Age", "Sex", "Income", "Education"],
        format_func=lambda g: group_map[g],
    )
    sub = fair[fair.feature == group].copy()
    ages_disp = age_labels()

    def group_label(v):
        if group == "Age":
            return ages_disp[int(v) - 1]
        if group == "Sex":
            return {
                0: tr("Nữ (mã gốc 0)", "Female (source code)"),
                1: tr("Nam (mã gốc 1)", "Male (source code)"),
            }.get(int(v), str(v))
        return str(int(v))

    sub["Group label"] = sub.group.map(group_label)
    st.caption(SPECS[group][1])
    st.dataframe(sub, hide_index=True, use_container_width=True)

    if group == "Income" and not sub.empty:
        lo_recall = sub.loc[sub.recall.idxmin()]
        hi_recall = sub.loc[sub.recall.idxmax()]
        lo_fpr = sub.loc[sub.FPR.idxmin()]
        hi_fpr = sub.loc[sub.FPR.idxmax()]
        st.warning(tr(
            f"Độ nhạy (Recall) theo nhóm thu nhập dao động từ {lo_recall.recall:.1%} đến {hi_recall.recall:.1%}; FPR từ {lo_fpr.FPR:.1%} đến {hi_fpr.FPR:.1%}. Sự khác biệt này đáng kể và có thể phản ánh bất bình đẳng trong tiếp cận xét nghiệm.",
            f"Income-group recall ranges from {lo_recall.recall:.1%} to {hi_recall.recall:.1%}; FPR ranges from {lo_fpr.FPR:.1%} to {hi_fpr.FPR:.1%}. Healthcare access can affect self-reported diagnosis."
        ))

    fig_fair = px.bar(
        sub,
        x="Group label",
        y=["recall", "FPR"],
        barmode="group",
        range_y=[0, 1],
        title=tr("Độ nhạy (Recall) và Tỷ lệ Dương tính Giả (FPR) theo nhóm", "Recall and false-positive rate by group"),
        labels={"Group label": group_map[group], "value": tr("Tỷ lệ", "Rate"), "variable": tr("Chỉ số", "Metric")},
        color_discrete_map={"recall": "#1D4ED8", "FPR": "#F59E0B"},
    )
    fig_fair.update_xaxes(automargin=True)
    fig_fair.update_yaxes(automargin=True)
    fig_fair.update_layout(template="simple_white", height=400, legend_title_text="")
    st.plotly_chart(fig_fair, use_container_width=True)

    for measure in ["recall", "FPR"]:
        gap = sub[measure].max() - sub[measure].min()
        st.caption(tr(
            f"Khoảng chênh lệch max–min quan sát được của {measure}: {gap:.3f}.",
            f"Observed max–min {measure} gap: {gap:.3f}."
        ))

# ==================================================
# TAB 4 — DATA & DECISIONS
# ==================================================
with tabs[3]:
    st.subheader(tr("Chuẩn bị Dữ liệu và Các Quyết định Thiết kế Mô hình", "Data preparation and model decisions"))
    st.markdown(f"**{tr('Phương pháp chia dữ liệu', 'Data splitting')}**")
    st.write(m["split_method"])
    st.markdown(f"**{tr('Xử lý mất cân bằng lớp', 'Class imbalance')}**")
    st.write(m["imbalance"])
    st.markdown(f"**{tr('Quy tắc chọn mô hình', 'Model selection')}**")
    st.write(m["selection_rule"])
    st.markdown(f"**{tr('Phương pháp giải thích', 'Explanation method')}**")
    st.write(m["explanation"]["method"])
    st.markdown(f"**{tr('Mô hình rút gọn (8 biến) vs Đầy đủ (21 biến)', 'Short vs. full model')}**")
    st.write(tr(
        f"Chênh lệch ROC-AUC trên tập validation giữa mô hình rút gọn tốt nhất và mô hình đầy đủ: {m['short_auc_gap']:.4f}.",
        f"Best short vs full validation ROC-AUC gap: {m['short_auc_gap']:.4f}."
    ))

    st.divider()
    st.markdown(f"**{tr('Kiểm toán trùng lặp và xung đột hồ sơ', 'Duplicate and overlap audit')}**")
    st.write(tr(f"Số dòng trùng lặp hoàn toàn được giữ lại: {m['audit']['exact_duplicate_rows']:,}.", f"Exact duplicate rows retained: {m['audit']['exact_duplicate_rows']:,}."))
    st.write(tr(f"Số hồ sơ đặc trưng trùng nhau nhưng khác nhãn mục tiêu: {m['audit']['conflicting_predictor_profiles']:,}.", f"Conflicting full predictor profiles: {m['audit']['conflicting_predictor_profiles']:,}."))

    st.divider()
    st.markdown(f"**{tr('Từ điển Đặc trưng (Feature dictionary)', 'Feature dictionary')}**")
    st.dataframe(pd.read_csv(ROOT / "reports/feature_dictionary.csv"), hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(f"**{tr('Tầm quan trọng hoán vị trên Validation', 'Validation permutation importance')}**")
    st.dataframe(pd.read_csv(ROOT / "reports/permutation_importance.csv"), hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(f"**{tr('Chi tiết phân chia tập dữ liệu', 'Dataset split details')}**")
    st.json(m["audit"]["splits"])

# ==================================================
# TAB 5 — FULL MODEL CARD
# ==================================================
with tabs[4]:
    c_mc_top, c_mc_dl = st.columns([3, 1], vertical_alignment="center")
    with c_mc_top:
        st.subheader(tr("Model Card: Hồ sơ Kỹ thuật GlucoGuide", "GlucoGuide model card"))
        st.caption(tr(
            "Tài liệu có cấu trúc về mục đích sử dụng, dữ liệu, phát triển, đánh giá, rủi ro và giới hạn triển khai.",
            "Structured documentation of the model's intended use, data, development, evaluation, risks, and deployment limitations."
        ))
    with c_mc_dl:
        html_doc = f"""<html><head><meta charset="utf-8"><title>GlucoGuide Model Card</title>
        <style>body{{font-family:Arial,sans-serif;padding:24px;line-height:1.55;color:#172B4D}}h1,h2{{color:#142D4E}}table{{border-collapse:collapse;width:100%;margin:12px 0}}th,td{{border:1px solid #CBD5E1;padding:8px;text-align:left}}th{{background:#F1F5F9}}</style></head>
        <body><h1>GlucoGuide - Model Card</h1>
        <p><b>Algorithm:</b> {m['algorithm']} | <b>Features:</b> {len(m['features'])} | <b>Test Rows:</b> {metrics['n']:,}</p>
        <h2>Test Metrics</h2>
        <table><tr><th>Metric</th><th>Value</th></tr>
        <tr><td>ROC-AUC</td><td>{metrics['roc_auc']:.6f}</td></tr>
        <tr><td>Average Precision</td><td>{metrics['average_precision']:.6f}</td></tr>
        <tr><td>Brier Score</td><td>{metrics['brier']:.6f}</td></tr>
        <tr><td>Precision (Threshold {m['threshold']:.4f})</td><td>{prec_1:.4%}</td></tr>
        <tr><td>Recall (Threshold {m['threshold']:.4f})</td><td>{rec_1:.4%}</td></tr>
        <tr><td>F1-Score</td><td>{f1_1:.6f}</td></tr></table>
        <p><i>Confusion Matrix: TN={tn:,}, FP={fp:,}, FN={fn:,}, TP={tp:,}</i></p></body></html>"""
        st.download_button(
            label=tr("Tải Model Card (HTML)", "Download Model Card"),
            data=html_doc,
            file_name="GlucoGuide_Model_Card.html",
            mime="text/html",
            use_container_width=True,
        )

    st.markdown(f"### 1. {tr('Thông tin Chi tiết Mô hình', 'Model details')}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div style='font-size:0.8rem;color:#6B7280;margin-bottom:2px'>{tr('Thuật toán','Algorithm')}</div><div style='font-size:1.5rem;font-weight:700;line-height:1.3;word-break:break-word'>{m['algorithm']}</div>", unsafe_allow_html=True)
    c2.metric(tr("Số đặc trưng", "Input features"), len(m["features"]))
    c3.metric(tr("Tổng bản ghi", "Total records"), f"{m['rows']:,}")
    st.write(f"**{tr('Mã ứng viên được chọn:', 'Model selection identifier:')}** `{m['selected_candidate']}`")
    st.write(f"**{tr('Loại mô hình:', 'Model type:')}** {tr('Phân loại nhị phân có giám sát.', 'Supervised binary classification.')}")

    st.divider()
    st.markdown(f"### 2. {tr('Mục đích Sử dụng', 'Intended use')}")
    st.write(tr(
        "Minh họa giáo dục về bài toán phân loại hồi cứu trên dữ liệu khảo sát BRFSS; không phải công cụ chẩn đoán hay chỉ định xét nghiệm lâm sàng.",
        "Educational retrospective classification demonstration. It summarizes patterns associated with a self-reported BRFSS survey label; it is not a diagnostic tool."
    ))
    st.markdown(f"**{tr('Phạm vi ngoài mục đích sử dụng', 'Out-of-scope uses')}**")
    st.markdown(tr(
        "- Chẩn đoán đái tháo đường hoặc tiền đái tháo đường.\n"
        "- Xác định bệnh chưa được chẩn đoán hoặc dự báo phát sinh bệnh trong tương lai.\n"
        "- Thay thế xét nghiệm máu, bác sĩ hoặc tư vấn y khoa chuyên môn.\n"
        "- Ra quyết định điều trị, bảo hiểm, tuyển dụng hoặc triển khai lâm sàng khi chưa được thẩm định độc lập.",
        "- Diagnosing diabetes or prediabetes.\n"
        "- Identifying undiagnosed diabetes or predicting future disease onset.\n"
        "- Replacing laboratory testing, a clinician, or professional medical advice.\n"
        "- Making treatment, medication, insurance, or employment decisions without independent clinical validation."
    ))

    st.divider()
    st.markdown(f"### 3. {tr('Biến Mục tiêu, Nhãn và Đầu ra', 'Target, labels, and outputs')}")
    st.write(f"**{tr('Biến mục tiêu:', 'Target variable:')}** `{m['target']}`")
    st.write(f"**Class 0:** {m['target_meaning']['0']}  \n**Class 1:** {m['target_meaning']['1']}")
    st.write(f"**{tr('Ngưỡng phân loại mặc định:', 'Default classification threshold:')}** `{m['threshold']:.6f}` ({m['threshold']:.2%})")

    st.divider()
    st.markdown(f"### 4. {tr('Dữ liệu Huấn luyện & Đánh giá', 'Training and evaluation data')}")
    split_df = pd.DataFrame([
        {
            tr("Phân tập", "Partition"): name.capitalize(),
            tr("Số bản ghi", "Records"): values["n"],
            tr("Tỷ lệ nhãn dương", "Positive-label rate"): f"{values['positive_rate']:.2%}",
        }
        for name, values in m["audit"]["splits"].items()
    ])
    st.dataframe(split_df, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(f"### 5. {tr('Đặc trưng Đầu vào & Yêu cầu', 'Input features and requirements')}")
    range_rows = []
    for feature in m["features"]:
        bounds = m["valid_input_ranges"].get(feature)
        allowed = m["valid_values"].get(feature)
        range_rows.append({
            tr("Đặc trưng", "Feature"): feature,
            tr("Miền hợp lệ", "Valid range"): f"{bounds[0]:g}–{bounds[1]:g}" if bounds else "N/A",
            tr("Giá trị cho phép", "Allowed values"): ", ".join(f"{x:g}" for x in allowed) if allowed is not None else tr("Liên tục trong miền hợp lệ", "Continuous within valid range"),
        })
    st.dataframe(pd.DataFrame(range_rows), hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(f"### 6. {tr('Đánh giá Hiệu năng & Chi phí Ngưỡng', 'Evaluation, performance & threshold costs')}")
    st.dataframe(pd.DataFrame([
        ("ROC-AUC", f"{metrics['roc_auc']:.6f}"),
        ("Average precision", f"{metrics['average_precision']:.6f}"),
        ("Brier score", f"{metrics['brier']:.6f}"),
        ("Precision", f"{metrics['precision']:.4%}"),
        ("Recall", f"{metrics['recall']:.4%}"),
        ("F1-score", f"{metrics['f1']:.6f}"),
    ], columns=[tr("Chỉ số", "Metric"), tr("Kết quả tập Test", "Test result")]), hide_index=True, use_container_width=True)

    cost = m["cost_assumptions"]
    st.write(f"**{tr('Giả định chi phí chọn ngưỡng:', 'Threshold cost assumptions:')}** FP = {cost['FP']}, FN = {cost['FN']} ({cost['units']})")
    st.write(f"**Python:** `{m['versions']['python']}` · **Scikit-learn:** `{m['versions']['sklearn']}` · **SHA-256:** `{m['sha256']}`")

# ==================================================
# TAB 6 — PCA AND FEATURE SELECTION
# ==================================================
with tabs[5]:
    st.subheader(tr("Thực nghiệm PCA và Chọn Lọc Đặc trưng", "PCA and feature-selection evidence"))
    st.caption(tr(
        "Tất cả thực nghiệm dưới đây mang tính khám phá trên dữ liệu validation, minh họa đánh đổi giữa số chiều và hiệu năng.",
        "All experiments below are exploratory and use validation data."
    ))

    pca_path = ROOT / "reports/pca_comparison.csv"
    if pca_path.exists():
        pca = pd.read_csv(pca_path)
        st.markdown(f"**{tr('Phân tích Thành phần Chính (PCA)', 'Principal component analysis')}**")
        pca_chart = pca[pca.principal_components > 0].copy()
        left, right = st.columns(2)
        with left:
            fig = px.line(
                pca_chart, x="principal_components", y="validation_average_precision", markers=True,
                labels={
                    "principal_components": tr("Số thành phần chính", "Number of components"),
                    "validation_average_precision": tr("Average Precision (Validation)", "Validation average precision"),
                },
            )
            fig.update_traces(line=dict(color="#1D4ED8"))
            fig.update_layout(template="simple_white", height=310)
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.line(
                pca_chart, x="principal_components", y="variance_explained", markers=True,
                labels={
                    "principal_components": tr("Số thành phần chính", "Number of components"),
                    "variance_explained": tr("Phương sai giải thích", "Variance explained"),
                },
            )
            fig.update_traces(line=dict(color="#2563EB"))
            fig.update_yaxes(tickformat=".0%", range=[0, 1])
            fig.update_layout(template="simple_white", height=310)
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pca, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(f"**{tr('Bằng chứng Chọn lọc Đặc trưng & Độ dài Bảng hỏi', 'Feature-selection and questionnaire evidence')}**")
    fs_path = ROOT / "reports/feature_selection.csv"
    forward_path = ROOT / "reports/forward_selection.csv"
    if fs_path.exists():
        fs = pd.read_csv(fs_path).sort_values("drop_from_full_auc_loss", ascending=False)
        st.dataframe(fs, hide_index=True, use_container_width=True)
    if forward_path.exists():
        st.markdown(f"**{tr('Lộ trình Forward Selection', 'Forward-selection path')}**")
        st.dataframe(pd.read_csv(forward_path), hide_index=True, use_container_width=True)
    size_ci = ROOT / "reports/questionnaire_size_bootstrap.csv"
    if size_ci.exists():
        st.markdown(f"**{tr('Khoảng tin cậy Bootstrap theo cặp', 'Paired validation bootstrap intervals')}**")
        st.dataframe(pd.read_csv(size_ci), hide_index=True, use_container_width=True)

st.write("")

# ==================================================
# 4. LIMITATIONS & RESPONSIBLE USE (BOTTOM BANNER)
# ==================================================
with st.container(key="about_limits"):
    html(f"""
    <div class="lim-grid">
        <div class="lim-item">
            <div class="lim-ic">{IC_SHIELD}</div>
            <div>
                <div class="lim-tt">{tr("Giới hạn & Sử dụng có Trách nhiệm", "Limitations & Responsible Use")}</div>
                <div class="lim-dd">{tr("GlucoGuide minh họa phân loại nhãn khảo sát, không phải công cụ chẩn đoán y khoa.", "GlucoGuide is a survey-label classification demonstration, not a clinical diagnostic tool.")}</div>
            </div>
        </div>
        <div class="lim-item">
            <div class="lim-ic">{IC_ALERT}</div>
            <div>
                <div class="lim-tt">{tr("Không phải công cụ chẩn đoán", "Not a diagnostic tool")}</div>
                <div class="lim-dd">{tr("Mô hình không thể xác nhận hay loại trừ bệnh tiểu đường.", "The model cannot confirm or rule out diabetes.")}</div>
            </div>
        </div>
        <div class="lim-item">
            <div class="lim-ic">{IC_DB}</div>
            <div>
                <div class="lim-tt">{tr("Giới hạn dữ liệu", "Data limitations")}</div>
                <div class="lim-dd">{tr("Khảo sát tự báo cáo tại Mỹ 2015; chưa kiểm chứng tại Việt Nam.", "Self-reported US 2015 survey; not validated in Vietnam.")}</div>
            </div>
        </div>
        <div class="lim-item">
            <div class="lim-ic">{IC_STETH}</div>
            <div>
                <div class="lim-tt">{tr("Tham vấn chuyên gia", "Consult professionals")}</div>
                <div class="lim-dd">{tr("Luôn hỏi ý kiến nhân viên y tế có chuyên môn.", "Always seek advice from healthcare professionals.")}</div>
            </div>
        </div>
    </div>
    """)

st.write("")
st.caption(tr(
    "Công cụ phục vụ mục đích giáo dục, không dùng trong chẩn đoán lâm sàng.",
    "Educational tool, not for clinical diagnosis."
))
