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
        <div style="display:flex;align-items:center;justify-content:space-between;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:12px 18px;margin-top:12px;">
            <div style="font-size:0.92rem;color:#475569;">
                {tr("Chỉ số BMI tính được:", "Calculated BMI:")}
                <strong style="font-size:1.15rem;color:#142D4E;margin-left:4px;">{bmi_calc:.1f} kg/m²</strong>
            </div>
            <span style="background:{bmi_color};color:#fff;font-size:0.8rem;font-weight:700;padding:4px 12px;border-radius:999px;">
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
                    st.error(f"{tr('Lỗi tính toán:', 'Calculation error:')} {e}")