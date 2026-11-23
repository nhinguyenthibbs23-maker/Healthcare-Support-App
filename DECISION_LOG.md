# GlucoGuide — Project Decision Log

**Project:** GlucoGuide  
**Project Type:** Classroom Data Mining Demonstration  
**Dataset:** BRFSS 2015  
**Last Updated:** 18 November 2026  
**Team Size:** 4

This decision log records the main methodological, technical, and application-design decisions made during the development of GlucoGuide. It reflects the current project artifacts and supersedes earlier decisions where explicitly stated.

## Decision 1: Define the Prediction Target as Retrospective Classification

**Decision:**  
The target is the self-reported diabetes/prediabetes label in the BRFSS 2015 dataset.

**Rationale:**  
The dataset contains respondents with and without a previous diagnosis. The target represents a retrospective classification task based on survey responses rather than a clinical diagnosis.

**Implementation:**
- Removed the previous-diagnosis and adult eligibility gate from the user form.
- Retained the self-reported diabetes/prediabetes label as the classification target.
- Updated the application description to reflect the actual task.

**Implication:**  
GlucoGuide does not claim to identify undiagnosed disease, screen or triage patients, predict future diabetes onset, or determine who needs medical testing.

## Decision 2: Use Eight Model Input Features

**Decision:**  
The final user-facing model uses eight input features.

**Selected Features:**
1. Age
2. BMI
3. HighBP
4. HighChol
5. GenHlth
6. Smoker
7. PhysActivity
8. DiffWalk

**Rationale:**  
The application input form and the trained model must use a consistent set of variables.

**Implementation:**  
The model input was modified from five features to eight features, with the corresponding application inputs aligned to the selected model features.

**Implication:**  
The user form provides the eight variables required by the current model pipeline.

## Decision 3: Select Histogram Gradient Boosting as the Final Model

**Decision:**  
Histogram Gradient Boosting (HGB) was selected as the final model.

**Model Parameters:**
- `max_iter = 100`
- `learning_rate = 0.03`
- `max_leaf_nodes = 15`
- `l2_regularization = 0.0`

**Rationale:**  
The project compared multiple classifier families through a structured hyperparameter search.

**Implementation:**
- Nine classifier families were included.
- Search used 3-fold StratifiedGroupKFold.
- Up to 16 randomized parameter configurations were evaluated per family.
- Actual search counts are documented in `reports/hyperparameter_search.csv`.

**Implication:**  
The selected model is the current project model, but the available comparison does not establish statistically significant superiority over all alternatives.

## Decision 4: Use an Illustrative Classification Threshold

**Decision:**  
The current classification threshold is **0.169330**.

**Rationale:**  
The threshold was selected on the validation set under an illustrative false-positive cost of 1 and false-negative cost of 5.

**Implementation:**
- Threshold and cost simulation are available only in Instructor mode.
- The user-facing result uses the saved threshold.
- Instructor threshold adjustments do not modify the user-facing saved threshold.
- Alternative cost ratios of 1:1, 1:2, 1:5, and 1:10 are reported in `reports/threshold_cost_sensitivity.csv`.

**Implication:**  
The threshold is a teaching assumption, not a clinically optimal decision boundary. The model score is not presented as an individual disease probability.

## Decision 5: Separate User Mode and Instructor Mode

**Decision:**  
The application provides separate User and Instructor modes.

**Rationale:**  
The application distinguishes the simplified user-facing classification experience from the model-analysis and teaching functions.

**Implementation:**
- User mode presents the model score and its interpretation.
- Instructor mode contains threshold and cost simulation.
- Instructor mode includes model analysis, PCA, feature-selection experiments, calibration, uncertainty analysis, and subgroup reporting.

**Implication:**  
Instructor mode is a navigation mode only. It is not authenticated access control.

## Decision 6: Add Model Analysis and Feature Experiments

**Decision:**  
Additional model-analysis functions were included in Instructor mode.

**Implementation:**
- PCA demonstration using fixed-settings Logistic Regression.
- Feature-selection experiments.
- Questionnaire-size experiments.
- Paired uncertainty summaries.
- Model comparison and bootstrap analysis.

**Rationale:**  
These functions support classroom exploration of model behavior and methodological trade-offs.

**Implication:**  
The PCA demonstration is not a tuned comparison across all classifier families. The exploratory analyses do not establish clinical validity.

## Decision 7: Report Uncertainty and Calibration

**Decision:**  
The project includes uncertainty and calibration analyses.

**Implementation:**
- Held-out test calibration by decile.
- Profile-cluster bootstrap intervals for ROC-AUC, Average Precision, and Brier score.
- Operating-point uncertainty intervals.
- Deduplicated sensitivity analysis.

**Rationale:**  
Point estimates alone do not fully describe model performance or the effect of repeated predictor profiles.

**Implication:**  
These analyses describe uncertainty under the project's sampling and evaluation design. They do not substitute for external or clinical validation.

## Decision 8: Include Fairness-Related Subgroup Reporting

**Decision:**  
Instructor summaries report subgroup performance by income group.

**Implementation:**
- Recall and false-positive-rate summaries.
- Wilson confidence intervals.
- Discussion of possible diagnosis-access and self-report ascertainment effects.

**Rationale:**  
Observed classification performance may differ across population groups, and self-reported outcomes may reflect differences in access to diagnosis.

**Implication:**  
The reported intervals are observation-level rather than cluster-adjusted. They do not prove that the model is fair. Survey weights are not used.

## Decision 9: Include Deduplicated Sensitivity Analysis

**Decision:**  
A deduplicated sensitivity report is included.

**Rationale:**  
The BRFSS dataset lacks respondent IDs and contains duplicate predictor profiles.

**Implementation:**
- Identical full predictor profiles are kept within the same partition.
- A deduplicated sensitivity report is provided.
- The report is available among the project artifacts.

**Implication:**  
These controls reduce certain risks associated with repeated profiles but do not eliminate all limitations related to dataset structure or validation design.

## Decision 10: Treat the AI Assistant as an Informational Feature

**Decision:**  
An AI Assistant feature was added to the application.

**Rationale:**  
The feature provides additional informational support within the educational application.

**Implementation:**  
AI assistance was used during the development and integration of the AI Assistant functionality.

**Implication:**  
The AI Assistant may generate inaccurate or incomplete information. It is not a clinical decision-making tool and does not replace professional medical advice.

## Decision 11: Add Nearby Clinic Search

**Decision:**  
A nearby clinic search feature was added to GlucoGuide to help users locate healthcare facilities in their surrounding area.

**Rationale:**  
The feature provides access to information about nearby healthcare facilities and complements the application's educational health-information functions.

**Implementation:**
- Added a nearby clinic search function to the application.
- Users can search for clinics located near them.
- The clinic-search function is separate from the machine learning prediction pipeline.
- Clinic search does not change the model's prediction, saved threshold, or classification result.

**Implication:**  
Nearby Clinic Search is an informational and navigation-support feature. It does not recommend a specific medical provider, determine clinical urgency, or replace professional healthcare guidance. The availability and accuracy of clinic information depend on the underlying location and search service.

## Decision 12: Maintain an Educational, Non-Clinical Scope

**Decision:**  
GlucoGuide is presented as a classroom data-mining demonstration.

**Rationale:**  
The project uses a historical, self-reported survey dataset rather than a clinical outcome dataset.

**Implementation:**
- Removed disease-risk categories from user-facing interpretation.
- Replaced the fixed 0.35 boundary with a numeric classifier score and comparison to the illustrative threshold.
- Added limitations explaining that the score is not an individual disease probability.
- Clarified that a low score does not rule out disease.

**Implication:**  
The application does not diagnose, screen, triage, predict future onset, or determine testing needs.

## Decision 13: Document Current Model Evidence and Limitations

**Decision:**  
Current model metrics and methodological limitations are documented in the project artifacts.

**Held-Out Test Results:**
- Sample size: 50,886
- Positive self-reported labels: 7,064
- ROC-AUC: 0.8195
- Average Precision: 0.4175
- Brier Score: 0.0981
- Precision: 0.3276
- Recall: 0.7092
- F1 Score: 0.4482

**Confusion Matrix:**
- TN: 33,539
- FP: 10,283
- FN: 2,054
- TP: 5,010

**Deduplicated Sensitivity Results:**
- Sample size: 45,878
- ROC-AUC: 0.8031
- Average Precision: 0.4195
- Brier Score: 0.1076

**Model Comparison:**  
The validation bootstrap comparison between HGB and Random Forest produced an Average Precision difference of 0.0022, with a 95% confidence interval of [-0.0048, 0.0101].

**Implication:**  
The interval includes zero. The comparison does not demonstrate statistically established superiority of HGB over Random Forest.

## Decision 14: Record Environment and Verification Limitations

**Decision:**  
Verification status and environment limitations are explicitly documented.

**Current Verification:**
- Python source compilation passed.
- The UI test suite was attempted in the current workspace.
- The saved estimator could not be loaded because the workspace uses scikit-learn 1.9.1, while the project pins scikit-learn 1.7.1 and the estimator was serialized with version 1.7.1.

**Required Follow-up:**
- Run the tests in the pinned Anaconda environment.
- Confirm that the saved estimator loads correctly.
- Complete deployment and remaining team deliverables.

**Implication:**  
The current workspace test attempt is not equivalent to a successful full application test.

## Decision 15: Acknowledge Remaining Project Limitations

**Decision:**  
The project retains a transparent limitations section.

**Limitations:**
- The dataset is based on self-reported BRFSS 2015 information from the United States.
- Respondent IDs are unavailable.
- Duplicate predictor profiles exist.
- Survey weights are not used.
- Validation data were reused for exploratory comparisons.
- External validation has not been conducted.
- Clinical outcome data are not available.
- Stakeholder review has not been established.
- Deployment, GitHub publication, video, and external user sessions remain team tasks.

**Implication:**  
The current project demonstrates data-mining and model-analysis workflows. It does not establish clinical validity, generalizability to other populations, or readiness for real-world healthcare use.

---

## Current Project Features

The current GlucoGuide application includes:

- Diabetes/prediabetes label classification using the selected HGB model.
- Eight-feature user input form.
- Numeric classifier score and illustrative threshold interpretation.
- Separate User and Instructor modes.
- Instructor-only threshold and cost simulation.
- Model comparison and hyperparameter search reports.
- PCA and feature-selection experiments.
- Calibration and uncertainty analysis.
- Income-group performance summaries.
- AI Assistant for informational support.
- Nearby Clinic Search to help users locate healthcare facilities.

## Current Project Status

The current artifacts reflect the decisions documented above as of **18 November 2026**.

This decision log records the project's methodological and technical choices. It is not an independent clinical validation report.
