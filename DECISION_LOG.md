

## Audit update - current artifacts (18 November 2026)

This addendum supersedes prior snapshots above. The app is a classroom demonstration of retrospective classification against the self-reported BRFSS 2015 diabetes/prediabetes label. It does not screen for undiagnosed disease, diagnose, predict future onset, or decide who needs testing. The user form has eight model inputs and no prior-diagnosis eligibility gate.

- Selected pipeline: Histogram Gradient Boosting; parameters: `max_iter=100`, `learning_rate=0.03`, `max_leaf_nodes=15`, `l2_regularization=0.0`.
- Search: nine classifier families, 3-fold StratifiedGroupKFold, up to 16 randomized settings per family (actual counts in `reports/hyperparameter_search.csv`).
- Threshold: 0.169330, selected on validation under illustrative FP=1/FN=5 assumptions. Threshold/cost adjustment stays in Instructor mode; it never changes user results. Alternative ratios appear in `reports/threshold_cost_sensitivity.csv`.
- Held-out test (n=50,886; 7,064 positive labels): ROC-AUC 0.8195, AP 0.4175, Brier 0.0981, precision 0.3276, recall 0.7092, F1 0.4482; TN=33,539, FP=10,283, FN=2,054, TP=5,010. Deduplicated sensitivity: AUC 0.8031, AP 0.4195, Brier 0.1076, n=45,878.
- Validation bootstrap comparing selected HGB with RF gives AP delta 0.0022 (95% CI -0.0048 to 0.0101); no demonstrated superiority.
- PCA and feature-selection reports, calibration, uncertainty, threshold sensitivity, and subgroup intervals are available in Instructor mode and under `reports/`. These are educational analyses, not clinical validation.
- Team size: four. Deployment, GitHub publication, video, and external user sessions remain team tasks.
