# Project audit response

This is an external audit response, not an independent clinical validation. The project is a classroom data-mining demonstration.

## Changes made

1. **Target and user population:** Removed the previous-diagnosis/adult eligibility gate from the user form. The target contains self-reported diabetes/prediabetes from respondents with and without a prior diagnosis. The app now describes retrospective survey-label classification; it does not claim to find undiagnosed disease, screen, triage, or predict future onset.
2. **User-facing interpretation:** Replaced disease-risk categories and the fixed 0.35 boundary with a numeric classifier score and comparison to the illustrative classification threshold. Copy says the score is not an individual disease probability, cannot determine testing, and a low score does not rule out disease.
3. **Instructor-only threshold controls:** Threshold and cost simulation stays in Instructor mode, as requested. It is for teaching, does not alter the user-facing saved threshold, and uses hypothetical relative FP/FN penalties. Reports compare ratios 1:1, 1:2, 1:5, and 1:10; no ratio is claimed to be clinically optimal.
4. **Tuning and model comparison:** Search now covers nine classifier families with 3-fold StratifiedGroupKFold and up to 16 randomized parameter configurations per family. Finite search spaces may have fewer configurations; the report records actual counts. Selected-model bootstrap intervals are exploratory and do not support a claim of statistically established superiority.
5. **PCA and feature experiments:** Added Instructor-mode PCA, forward/other feature-selection, questionnaire size, and paired uncertainty summaries. PCA is a fixed-settings Logistic Regression demonstration, not a tuned comparison across all model families.
6. **Test uncertainty and calibration:** Added held-out test calibration-by-decile, profile-cluster bootstrap intervals for ROC-AUC/AP/Brier, operating-point intervals, and deduplicated sensitivity analysis. These describe uncertainty under this sampling design; they are not clinical validation.
7. **Fairness reporting:** Instructor summaries show income-group recall and false-positive-rate Wilson intervals and discuss possible diagnosis-access/self-report ascertainment effects. The intervals are observation-level, not cluster-adjusted, and do not prove fairness. Survey weights are not used.
8. **Documentation and tests:** Updated current metrics, model parameters, threshold, and limits in README, decision log, team guide, experiment report, and UI expectations. Runtime text handling repairs legacy mojibake in translation strings.

## Current evidence

Selected model: Histogram Gradient Boosting. Eight inputs: Age, BMI, HighBP, HighChol, GenHlth, Smoker, PhysActivity, DiffWalk. Threshold: 0.169330 using illustrative FP=1/FN=5. On the held-out test set (n=50,886; 7,064 positive self-reports), ROC-AUC=0.8195, Average Precision=0.4175, Brier=0.0981, precision=0.3276, recall=0.7092, F1=0.4482. Confusion matrix: TN=33,539, FP=10,283, FN=2,054, TP=5,010.

Validation bootstrap comparison of HGB with Random Forest: AP difference=0.0022, 95% interval [-0.0048, 0.0101], which includes zero. This is exploratory and selection-conditioned.

## Verification and runtime

Python source compilation passed. The UI test suite was attempted in the current workspace but could not load the saved estimator: this workspace has scikit-learn 1.9.1, while the project pins 1.7.1 and the model was serialized with 1.7.1. Run tests in the pinned Anaconda environment. Deployment is not included.

## Remaining limits

The dataset is a 2015 US self-reported survey, lacks respondent IDs, contains duplicate profiles, and is not analyzed with survey weights. A deduplicated sensitivity report is provided, and identical full predictor profiles are kept within the same partition. Validation was reused for exploratory comparisons. None of these controls substitutes for a clinical outcome dataset, external validation, survey-design-aware estimates, or stakeholder review. Instructor mode is a navigation mode, not authenticated access control.
