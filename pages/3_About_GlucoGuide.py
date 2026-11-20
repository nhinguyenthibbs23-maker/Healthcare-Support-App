import streamlit as st
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
            st.switch_page("pages/1_Risk_Assessment.py")