import streamlit as st
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