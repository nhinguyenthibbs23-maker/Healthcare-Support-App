# GlucoGuide - huong dan nhanh cho nhom

## Chay ung dung

Ye u cau Python 3.13.9 va scikit-learn 1.7.1 (xem requirements.txt). Trong Anaconda Prompt, di chuyen vao thu muc goc project, sau do chay:

```bat
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Model da duoc luu san. Khong can chay train.py khi chi muon mo app. De huan luyen lai toan bo pipeline va cap nhat cac bao cao, dung `python train.py`.

## Hai che do

- User: tra loi 8 cau hoi, xem diem phan loai va giai thich de hieu. Khong hien thi tuy chinh threshold/cost.
- Instructor: xem bao cao mo hinh, tuning, PCA, feature selection, calibration, uncertainty, fairness va threshold/cost sensitivity. Chinh threshold trong trang nay chi phuc vu bai hoc; khong thay doi model/threshold trang User. Day la dieu huong giao dien, khong phai phan quyen bao mat.

## B?i to?n va gi?i h?n

Muc tieu la phan loai hoi cuu nhan diabetes/prediabetes tu khai trong BRFSS 2015. Nhan gom ca nguoi da va chua duoc chan doan; day khong phai xet nghiem, chan doan, tam soat benh chua phat hien, hay du bao benh tuong lai. Khong dien giai diem thanh phan tram nguy co va khong dua ra khuyen nghi xet nghiem dua tren diem.

Bo du lieu co 253,680 dong va 21 bien dau vao goc. Khong co respondent ID; cac dong co cung profile duoc giu trong cung partition de giam ro ri giua split. Khong dung survey weights. Ket qua khong duoc xem la dai dien quoc gia hay co kha nang ap dung lam sang.

## Ket qua hien tai (18 Nov 2026)

- Mo hinh: Histogram Gradient Boosting; 8 dau vao: Age, BMI, HighBP, HighChol, GenHlth, Smoker, PhysActivity, DiffWalk.
- Tim kiem: 9 ho classifier, 3-fold StratifiedGroupKFold, toi da 16 cau hinh ngau nhien moi ho (khong gian huu han co the it hon).
- Threshold validation: 0.169330 voi gia dinh minh hoa FP=1, FN=5; day khong phai chi phi y te. Chi Instructor duoc dieu chinh threshold/cost.
- Test holdout (n=50,886; 7,064 nhan duong): ROC-AUC 0.8195; Average Precision 0.4175; Brier 0.0981; precision 0.3276; recall 0.7092; F1 0.4482. Confusion matrix: TN 33,539; FP 10,283; FN 2,054; TP 5,010.
- Bootstrap validation HGB so voi RF co AP delta 0.0022, 95% CI [-0.0048, 0.0101], nen chua the ket luan HGB hon ro rang.

Xem `reports/course_model_experiments.md`, `AUDIT_RESPONSE.md`, `models/model_meta.json` va cac CSV trong `reports/` de co day du phuong phap va bang ket qua.

## Nhom va viec con lai

Nhom co 4 thanh vien. Deploy len Streamlit, public GitHub, quay video demo va lay y kien nguoi dung ngoai nhom do nhom thuc hien.
