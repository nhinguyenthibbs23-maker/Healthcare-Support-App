# Current Data Mining Experiments (18 Nov 2026)

## Scope and target

The task is retrospective binary classification of the BRFSS 2015 self-reported diabetes/prediabetes label. It is not a screen for undiagnosed disease, a clinical diagnosis, or a prediction of future onset. The project excludes claims about clinical risk and testing recommendations.

## Training protocol

- Dataset rows: 253,680. Group identical full predictor profiles in the split to reduce profile leakage; no respondent identifier is available.
- Split: stratified, grouped train/validation/test. Test partition remains outside model and threshold selection.
- Preprocessing is fitted within each sklearn pipeline. Up to 10,000 stratified training rows are used for 3-fold StratifiedGroupKFold randomized search; tuned candidates are refit on 40,000 rows and compared on 10,000 validation rows.
- Nine classifier families are searched. Each family requests up to 16 settings; smaller finite spaces use fewer settings. Actual draws: Gradient Boosting: 16, Logistic Regression: 10, Support Vector Machine (linear): 10, Histogram Gradient Boosting: 16, Random Forest: 16, K-Nearest Neighbors: 16, Extra Trees: 16, Naive Bayes: 4, Decision Tree: 16.
- The 8-input questionnaire uses Age, BMI, HighBP, HighChol, GenHlth, Smoker, PhysActivity, DiffWalk. This is a practical compromise; no questionnaire subset is clinically validated.

## Selected pipeline and threshold

- Selected pipeline: Histogram Gradient Boosting (short | tuned | Histogram Gradient Boosting).
- Validation-selected threshold: 0.169330. Illustrative relative costs are FP=1 and FN=5, controlled in Instructor mode only. These are not clinical or monetary estimates; threshold sensitivity for alternative ratios is reported separately.
- Validation average precision: 0.4329. Paired bootstrap vs. the strongest selected-family validation comparator: AP delta 0.0022 (95% interval -0.0048 to 0.0101). This exploratory, selection-conditioned interval includes zero; do not claim statistically established superiority.

## One-time held-out test evaluation

| Metric | Result |
|---|---:|
| Rows | 50886 |
| Positive labels | 7064 |
| ROC-AUC | 0.8195 |
| Average Precision | 0.4175 |
| Brier score | 0.0981 |
| Precision at selected threshold | 0.3276 |
| Recall at selected threshold | 0.7092 |
| F1 | 0.4482 |

Confusion matrix [[TN, FP], [FN, TP]]: [[33539, 10283], [2054, 5010]]. Profile-cluster bootstrap intervals for ranking/calibration metrics, Wilson intervals for the operating point, test calibration by decile, and a deduplicated sensitivity analysis are in the adjacent CSV files. These quantify sampling uncertainty under the chosen design; they do not establish clinical transportability.

## PCA, feature selection, and questionnaire burden

PCA remains a fixed-settings Logistic Regression comparison, not a fully tuned PCA pipeline across every classifier. It is included to demonstrate dimensionality reduction and the variance/performance trade-off. Results:

| Components | representation | principal_components | validation_rows | variance_explained | validation_roc_auc | validation_average_precision | validation_brier |
|---|---|---|---|---|---|---|---|
| PCA + Logistic Regression (1 PCs) | 1 | 50726 | 0.13657936449794944 | 0.7841475134485036 | 0.3532992756418252 | 0.10502325760155969 |
| PCA + Logistic Regression (2 PCs) | 2 | 50726 | 0.21060533095048906 | 0.7879549183602381 | 0.36024754268869585 | 0.10386160795231461 |
| PCA + Logistic Regression (3 PCs) | 3 | 50726 | 0.276073797561703 | 0.7931726844300597 | 0.3709052220005988 | 0.10332523466601518 |
| PCA + Logistic Regression (5 PCs) | 5 | 50726 | 0.3806282920437575 | 0.7946735093558099 | 0.36829088812571537 | 0.103035869647934 |
| PCA + Logistic Regression (8 PCs) | 8 | 50726 | 0.5118732305977585 | 0.7989644152263622 | 0.38000789318412775 | 0.10201825294636845 |
| PCA + Logistic Regression (12 PCs) | 12 | 50726 | 0.6674844664687788 | 0.7993499531661064 | 0.3784666837933194 | 0.10207025984318847 |
| PCA + Logistic Regression (16 PCs) | 16 | 50726 | 0.8155307192083247 | 0.7994591585862584 | 0.3793189267500192 | 0.10203903908354663 |
| PCA + Logistic Regression (20 PCs) | 20 | 50726 | 0.9537901913126268 | 0.7996736773280324 | 0.3800182182537192 | 0.1019815671444201 |
| PCA + Logistic Regression (22 PCs) | 22 | 50726 | 0.9999999999999999 | 0.8157059985835288 | 0.40202064667113624 | 0.09953274847944985 |
| No PCA (standardized encoded inputs) | 29 | 50726 | 1.0 | 0.8156909158922203 | 0.40200887234301363 | 0.09953392261019622 |
| No PCA (app Logistic Regression preprocessing) | 29 | 50726 | 1.0 | 0.8157366431929196 | 0.4020535291165258 | 0.0995324516611133 |

Feature-selection outputs include forward selection, permutation importance, ablation/size comparison and paired bootstrap. Comparisons on validation data are exploratory and share the same validation set; the 5/8/21-input comparison holds selected settings fixed and is not independently retuned. PCA and selection report paths: `pca_comparison.csv`, `forward_selection.csv`, `feature_selection.csv`, `permutation_importance.csv`, `questionnaire_size_comparison.csv`, `questionnaire_size_bootstrap.csv`.

## Fairness and limits

Instructor reports show income-subgroup recall and false-positive rates with observation-level Wilson intervals. Differences are descriptive, may reflect unequal access to diagnosis and self-report ascertainment, and are not proof of fairness or unfairness. BRFSS survey weights are not used. Identical response profiles are not guaranteed to represent the same respondents; grouping reduces but cannot eliminate all dependence or dataset bias. External validation on an appropriate clinical screening cohort is needed before any health-care use.

## Reproduction

Use Python 3.13.9 and scikit-learn 1.7.1 as pinned in `requirements.txt`. Run `python train.py` to rerun tuning and the complete pipeline; the saved artifacts correspond to the current model metadata.