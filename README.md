# GlucoGuide: Nền tảng Sàng lọc Nguy cơ Đái tháo đường & Trợ lý Lâm sàng Thông minh
*(GlucoGuide: Diabetes Risk Screening & Clinical Intelligence Platform)*

**Đồ án Môn học Khai phá Dữ liệu (Data Mining Course Project)**  
**Đơn vị:** Trường Đại học Quốc tế Miền Đông (Eastern International University - EIU)  
**Nhóm tác giả:** 4 thành viên  

> **Tuyên bố y tế quan trọng:** Đây là dự án học thuật phục vụ mục đích giáo dục và nghiên cứu khoa học. Mô hình phân loại nhãn khảo sát tự báo cáo từ tập dữ liệu CDC BRFSS 2015. Công cụ **không có chức năng chẩn đoán y khoa**, không phát hiện bệnh chưa từng biết, không thay thế xét nghiệm máu lâm sàng và không dùng để ra quyết định điều trị y tế.

---

## 1. Tổng quan Dự án & Kiến trúc Hai Chế độ (Dual Modes)

GlucoGuide cung cấp hai trải nghiệm người dùng hoàn toàn khác biệt trên cùng một hệ thống học máy cốt lõi:

### A. Chế độ Người dùng (User Mode)
Giao diện đơn giản, thân thiện, dễ tiếp cận và tập trung vào trải nghiệm cá nhân hóa:
1. **Trang chủ (Home):** Giới thiệu thương hiệu GlucoGuide, giải thích quy trình 3 bước, cam kết quyền riêng tư và nút bắt đầu khảo sát nổi bật.
2. **Khảo sát Nguy cơ (Risk Assessment):** Bảng câu hỏi thu thập 8 đặc trưng của mô hình được thiết kế dạng **trắc nghiệm từng bước (Stepped Questionnaire - 3 bước)** kèm thanh tiến trình trực quan và bộ tính chỉ số BMI tự động.
3. **Kết quả của tôi (My Results):**
   - **Bảng kết quả cá nhân:** Vòng tròn xác suất dự báo, phân loại rủi ro (Dưới/Trên ngưỡng 0.1693), ý nghĩa kết quả, huy hiệu nhận diện yếu tố chính và biểu đồ thanh đóng góp của từng đặc trưng theo thuật toán **Exact Shapley Attribution**.
   - **Trợ lý AI (AI Assistant):** Tích hợp trực tiếp song song (side-by-side). Sử dụng SDK chính thức `google-genai` với mô hình `gemini-2.5-flash` (hỗ trợ chế độ offline thông minh khi chưa có khóa API) để giải thích kết quả, phân tích yếu tố ảnh hưởng và đưa ra lời khuyên y tế dự phòng.
4. **Giới thiệu (About GlucoGuide):** Trang thông tin thân thiện dành riêng cho người dùng phổ thông, giải thích cơ chế sàng lọc và tuyên bố trách nhiệm y tế.

### B. Chế độ Giảng viên (Teacher Mode)
Được tổ chức trên **một trang duy nhất (Project Overview)** với **6 tab ngang** phục vụ công tác đánh giá và thẩm định học thuật:
- **Tab 1 – Full Model Card:** Đầy đủ 13 phần theo chuẩn Mitchell et al. Model Cards, kèm nút tải tệp tài liệu Model Card HTML/In ấn chuyên nghiệp.
- **Tab 2 – Model Performance:** Biểu đồ tương tác Plotly ROC Curve (AUC = 0.8195), Precision-Recall Curve (AP = 0.4175), Ma trận nhầm lẫn (Confusion Matrix 50.886 mẫu test) và Báo cáo phân loại chi tiết.
- **Tab 3 – Explainability:** Phân tích tầm quan trọng toàn cục (Permutation Feature Importance), nghiên cứu đối sánh 7 thuật toán × 4 bộ đặc trưng (5, 8, 12, 21 biến), và giải thích Exact Shapley.
- **Tab 4 – Cost & Threshold Simulator:** Bảng mô phỏng ngưỡng quyết định tương tác, cho phép điều chỉnh trọng số phạt $FP$ và $FN$ để kiểm chứng tác động tới ngưỡng cắt tối ưu và tổng thiệt hại kỳ vọng.
- **Tab 5 – Methodology:** Toàn bộ quy trình nghiên cứu học máy 10 bước từ tiền xử lý, phân tầng tránh rò rỉ (`StratifiedGroupKFold`), kiểm định chéo đến triển khai.
- **Tab 6 – Ethics & Limitations:** Phân tích đạo đức về sai số âm tính giả/dương tính giả, kiểm định phụ nhóm (Fairness by Age, Sex, Income, Education từ `fairness.csv`) và giới hạn dữ liệu khảo sát BRFSS.

---

## 2. Thông số Kỹ thuật & Hiệu năng Đã Kiểm định

- **Tập dữ liệu nguồn:** CDC BRFSS 2015 (253.680 bản ghi, 21 biến khảo sát).
- **Thuật toán triển khai:** Histogram Gradient Boosting (`HistGradientBoostingClassifier`).
- **8 Đặc trưng đầu vào:** `Age`, `BMI`, `HighBP`, `HighChol`, `GenHlth`, `Smoker`, `PhysActivity`, `DiffWalk`.
- **Ngưỡng phân loại mặc định:** `0.169330` (được tối ưu trên tập Validation với tỷ lệ phạt tương đối $FP = 1, FN = 5$).
- **Kết quả đánh giá trên tập Kiểm tra độc lập cách ly (Held-out Test, N = 50.886):**

| Chỉ số Đánh giá | Kết quả Nghiệm thu |
| :--- | :---: |
| **Quy mô tập Test** | 50.886 bản ghi (7.064 ca dương tính) |
| **ROC-AUC** | **0.8195** |
| **Average Precision (PR-AUC)** | **0.4175** |
| **Brier Score** | **0.0981** |
| **Độ nhạy (Recall at Threshold 0.1693)** | **70.92%** (`0.7092`) |
| **Độ chuẩn xác (Precision at Threshold)** | **32.76%** (`0.3276`) |
| **F1-Score** | **0.4482** |
| **Ma trận Nhầm lẫn (Confusion Matrix)** | $TN = 33.539, FP = 10.283, FN = 2.054, TP = 5.010$ |

---

## 3. Hướng dẫn Cài đặt & Chạy Ứng dụng Cục bộ (Local Run)

### Bước 1: Chuẩn bị Môi trường Python
Khuyến nghị sử dụng Python 3.11 – 3.13:
```bash
python -m venv venv
# Kích hoạt môi trường ảo:
# Trên Windows:
.\venv\Scripts\activate
# Trên macOS / Linux:
source venv/bin/activate
```

### Bước 2: Cài đặt Thư viện Phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 3: Cấu hình Khóa Gemini API (Tùy chọn)
Để kích hoạt tính năng đối thoại thông minh của Trợ lý AI với mô hình `gemini-2.5-flash`:
1. Sao chép tệp mẫu cấu hình:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Mở tệp `.streamlit/secrets.toml` và điền khóa API của bạn:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
*(Lưu ý: Nếu không cấu hình khóa API, ứng dụng vẫn hoạt động 100% bình thường với bộ giải thích quy luật lâm sàng offline tích hợp sẵn).*

### Bước 4: Khởi chạy Ứng dụng Streamlit
```bash
streamlit run app.py
```

### Bước 5: Chạy Bộ Kiểm thử Tự động (Unit Tests)
```bash
python -m unittest discover -s tests -v
```

---

## 4. Hướng dẫn Triển khai lên Streamlit Community Cloud

1. Đưa toàn bộ mã nguồn lên kho lưu trữ GitHub của nhóm:
   ```bash
   git init
   git add .
   git commit -m "feat: complete GlucoGuide UI/UX redesign and AI assistant integration"
   git branch -M main
   git remote add origin <URL-GITHUB-REPO>
   git push -u origin main
   ```
2. Truy cập [share.streamlit.io](https://share.streamlit.io/) và đăng nhập bằng tài khoản GitHub.
3. Chọn **"New app"**, chọn kho lưu trữ và nhánh `main`, tệp khởi chạy là `app.py`.
4. Trong mục **Advanced settings > Secrets**, dán cấu hình khóa API:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
5. Nhấn **Deploy** để phát hành ứng dụng trực tuyến.
