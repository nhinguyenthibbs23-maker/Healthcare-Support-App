# GlucoGuide — Healthcare Decision-Support App

**Data Mining Course Project | Eastern International University (EIU)**  
**Team members:**  

[Nguyen Bao Ngoc](https://github.com/ngocnguyen-vn)

[Nguyen Thi Yen Nhi](https://github.com/nhinguyenthibbs23-maker)

[Do Nguyen Minh Thu](https://github.com/minhthu1302)

[Le Hoang Lam](https://github.com/LamHoang30)

**App link:** https://healthcare-support-app-qsw9qo27b8ozxvlvedjsae.streamlit.app/ 

**Video link:** https://youtu.be/M-jpsLZf8z0?si=0umhSKK0m2uxzGKJ
    
**Built with:** Python · scikit-learn · Streamlit · Plotly

> **Educational project — not for clinical use.** GlucoGuide is a classroom decision-support demonstration. It classifies patterns associated with a self-reported diabetes/prediabetes label in the CDC BRFSS 2015 survey. It is not a diagnostic test, does not identify undiagnosed diabetes, does not predict future disease onset, and must not be used to make clinical or treatment decisions.

## 1. Problem and intended user

### User-decision statement

An adult exploring their health information uses GlucoGuide at home to review how their self-reported health profile compares with patterns in the BRFSS 2015 survey and to decide whether to discuss blood-glucose testing or preventive health questions with a qualified healthcare professional.

The app presents a model estimate and an educational interpretation. It does **not** determine whether someone has diabetes or whether a test is medically required. A clinician and appropriate laboratory tests are needed for diagnosis.

### What the project demonstrates

The project focuses on the complete decision-support workflow—not simply maximizing a classification score:

- define the user, decision moment, and intended action;
- use only inputs available at that moment;
- build and evaluate a reproducible machine-learning pipeline;
- explain model output and error trade-offs;
- communicate uncertainty, limitations, and responsible use through an accessible interface.

## 2. Dataset

GlucoGuide uses the **Diabetes Health Indicators / CDC BRFSS 2015** dataset.

- **Source:** [Kaggle dataset](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset)
- **Original survey:** [CDC BRFSS 2015](https://www.cdc.gov/brfss/annual_data/annual_2015.html)
- **Codebook:** [2015 BRFSS Codebook](https://www.cdc.gov/brfss/annual_data/2015/pdf/CODEBOOK15_LLCP.pdf)
- **Dataset size:** 253,680 survey records; 21 original columns
- **Target:** `Diabetes_binary`
  - `0`: respondent did not report diabetes or prediabetes
  - `1`: respondent reported diabetes or prediabetes

The outcome is self-reported and includes respondents with a previous diagnosis. Therefore, it is not a ground-truth label for undiagnosed disease or a clinical diagnosis.

### Model inputs

The deployed model uses eight questionnaire features:

| Feature | Meaning in the app |
|---|---|
| `Age` | BRFSS age category |
| `BMI` | Body Mass Index calculated from entered height and weight |
| `HighBP` | Self-reported high blood pressure |
| `HighChol` | Self-reported high cholesterol |
| `GenHlth` | Self-rated general health |
| `Smoker` | Smoking-history indicator as defined by the source data |
| `PhysActivity` | Physical-activity indicator |
| `DiffWalk` | Difficulty walking or climbing stairs |

The application converts the questionnaire answers into the model's expected encoded values. The original BRFSS feature definitions and category encodings should be consulted when interpreting these variables.

## 3. Model and evaluation

### Final model

- **Estimator:** Histogram Gradient Boosting Classifier
- **Feature set:** 8 inputs
- **Saved artifact:** `models/pipeline.joblib`
- **Metadata:** `models/model_meta.json`
- **Default classification threshold:** `0.169330`
- **Threshold selection assumption:** validation-set cost ratio of FP = 1 and FN = 5, in illustrative relative units—not actual monetary or medical costs.

The training workflow compared course-relevant classification models and feature sets. Model selection used grouped cross-validation and validation data. The selected pipeline was refitted on the training partition, the operating threshold was selected on the validation partition, and final performance was measured on a held-out test set.

### Held-out test performance

The following metrics are reported by the saved model metadata for the test set (`n = 50,886`; positive labels = 7,064):

| Metric | Result |
|---|---:|
| ROC-AUC | 0.8195 |
| Average Precision (PR-AUC) | 0.4175 |
| Brier score | 0.0981 |
| Precision at selected threshold | 0.3276 |
| Recall at selected threshold | 0.7092 |
| F1-score | 0.4482 |

**Confusion matrix at the selected threshold**

| | Predicted negative | Predicted positive |
|---|---:|---:|
| Actual negative | TN = 33,539 | FP = 10,283 |
| Actual positive | FN = 2,054 | TP = 5,010 |

These results describe retrospective classification of survey labels. They do not establish clinical accuracy, effectiveness, or suitability for individual patient care. The positive class is relatively uncommon, so precision, recall, PR-AUC, calibration, and the consequences of false predictions are important alongside ROC-AUC.

### Data splitting and leakage checks

The source dataset does not provide a respondent identifier suitable for a true person-level split. The project therefore groups records by their complete original 21-feature profile and keeps each profile within one partition, using a stratified approximately 60/20/20 train-validation-test split. This reduces exact-profile overlap across partitions, but it cannot guarantee that all records from the same individual are separated.

The audit also identified duplicate rows and conflicting target labels for some identical predictor profiles. These limitations are documented in the model metadata and project decision log. The app should be interpreted as a model-development demonstration, not an externally validated system.

## 4. Application features

GlucoGuide provides two interface modes.

### User mode

- **Home:** project introduction and entry point
- **Risk Assessment:** step-by-step questionnaire; BMI is calculated from height and weight
- **My Results:** model score, threshold-based result category, feature-level explanation, and educational next-step information
- **AI Assistant:** optional Gemini-powered conversational explanation; a built-in offline response path is available when the API key is not configured
- **About GlucoGuide:** data, purpose, and health-use disclaimer

### Instructor mode

The instructor-facing overview provides model and project inspection, including:

- model card and intended-use documentation;
- ROC and precision-recall performance views;
- confusion matrix and classification metrics;
- feature importance and model-comparison results;
- Shapley-based explanation of an individual estimate;
- false-positive / false-negative cost and threshold exploration;
- methodology, subgroup fairness summaries, and limitations.

The threshold and cost simulator is an educational analysis tool. Changes made there do not alter the default threshold used in the public user results.

## 5. Repository structure

```text
Healthcare-Support-App/
├── app.py                         # Streamlit entry point
├── pages/
│   ├── 1_Risk_Assessment.py       # Questionnaire
│   ├── 2_My_Results.py            # Result and explanation
│   ├── 3_About_GlucoGuide.py      # User-facing project information
│   └── 4_Teacher_Overview.py      # Instructor/model overview
├── components/
│   └── ai_assistant.py             # AI assistant interface
├── utils/                           # Prediction, explanations, UI, threshold,
│                                    # localization, data and clinic utilities
├── models/
│   ├── pipeline.joblib              # Trained scikit-learn pipeline
│   ├── model_meta.json              # Features, threshold, assumptions, metrics
│   └── *.csv / *.npz                # Evaluation and analysis artifacts
├── data/
│   └── diabetes_binary_health_indicators_BRFSS2015.csv
├── reports/                          # Training, validation and audit reports
├── train.py                          # Rebuilds the model
├── tune_models.py                    # Model-search workflow
├── tests/                             # Application tests
├── requirements.txt
├── DECISION_LOG.md
└── AI_USE_APPENDIX.md
```

## 6. Run locally

### Requirements

Use a compatible Python environment. The project metadata records Python 3.13.9 and pins the main scientific-library versions in `requirements.txt`.

```bash
# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the app
streamlit run app.py
```

### Optional Gemini API configuration

The AI Assistant can use the Gemini API when a key is configured. Copy the example secrets file:

```bash
# Windows PowerShell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml

# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then add your key to `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "YOUR_API_KEY"
```

Do not commit `.streamlit/secrets.toml` or expose API keys in source code, screenshots, or public logs. The app includes an offline fallback when the key is unavailable.

### Run tests

```bash
python -m unittest discover -s tests -v
```

## 7. Deploy to Streamlit Community Cloud

1. Push the project repository to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create a new app and select the repository, branch, and `app.py` as the entry point.
4. Add `GEMINI_API_KEY` under the app's **Settings → Secrets** if the online AI assistant is required.
5. Deploy and test the public app from a fresh browser session.

The deployed app should load the saved pipeline; it should not retrain the model during normal user interaction.

## 8. Limitations and responsible use

- The model is trained on a **US 2015 telephone survey**, not a representative clinical dataset of Vietnamese users.
- The target is **self-reported diabetes/prediabetes**, not laboratory-confirmed diagnosis.
- The dataset contains duplicated profiles and some identical predictor profiles with conflicting labels.
- No respondent identifier is available to guarantee a person-level train/test split.
- Model scores and threshold categories are statistical outputs, not individual clinical probabilities.
- False positives and false negatives have different consequences; the selected cost ratio is illustrative and subjective.
- Subgroup analyses are exploratory and do not prove fairness or clinical safety.
- The AI Assistant may generate inaccurate or overly general information. Its responses are not medical advice.
- The project has not undergone clinical validation or prospective evaluation.

**If you are concerned about diabetes, consult a qualified healthcare professional and discuss appropriate blood-glucose testing. Do not use GlucoGuide to diagnose, rule out, or treat a medical condition.**

## 9. Project documentation

- [`DECISION_LOG.md`](DECISION_LOG.md) — key modeling and implementation decisions
- [`AI_USE_APPENDIX.md`](AI_USE_APPENDIX.md) — draft disclosure of AI-assisted work; the team must review and finalize it
- [`models/model_meta.json`](models/model_meta.json) — model configuration, threshold, input ranges, and evaluation metrics
- [`reports/`](reports/) — supporting experiments, data audit, and evaluation analyses

---

*GlucoGuide is an educational healthcare decision-support project. It is not intended for clinical use.*
