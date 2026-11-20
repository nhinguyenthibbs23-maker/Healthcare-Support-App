"""Course model comparison and PCA experiment for GlucoGuide.

Hyperparameter search runs on a stratified sample of the training partition
with grouped cross-validation to keep identical profiles together. PCA is
evaluated on the full validation partition. The held-out test partition is
intentionally not used by this experiment.
"""
import argparse
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedGroupKFold,
    StratifiedKFold,
    ParameterGrid,
    train_test_split,
)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

from utils.data_loader import ROOT, SHORT, TARGET, SPECS, load_data
from utils.threshold import threshold_table, choose_threshold


def preprocessor(features):
    categorical = [c for c in features if c != 'BMI']
    parts = [('bmi', Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ]), ['BMI'])]
    if categorical:
        parts.append(('category', Pipeline([
            ('impute', SimpleImputer(strategy='most_frequent')),
            ('encode', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
        ]), categorical))
    return ColumnTransformer(parts, sparse_threshold=0)


def logistic_pipeline(features):
    return Pipeline([
        ('preprocess', preprocessor(features)),
        ('model', LogisticRegression(max_iter=1000, C=1.0, random_state=42)),
    ])


def candidates(seed):
    return {
        'Decision Tree': (DecisionTreeClassifier(random_state=seed), {
            'model__max_depth': [4, 8, 14, None],
            'model__min_samples_leaf': [20, 50, 100],
            'model__criterion': ['gini', 'entropy'],
        }),
        'Logistic Regression': (LogisticRegression(max_iter=1500, random_state=seed), {
            'model__C': [0.05, 0.2, 1.0, 5.0, 20.0],
            'model__class_weight': [None, 'balanced'],
        }),
        'Naive Bayes': (GaussianNB(), {
            'model__var_smoothing': [1e-11, 1e-9, 1e-7, 1e-5],
        }),
        'K-Nearest Neighbors': (KNeighborsClassifier(n_jobs=-1), {
            'model__n_neighbors': [21, 41, 71, 101],
            'model__weights': ['uniform', 'distance'],
            'model__p': [1, 2],
        }),
        'Support Vector Machine (linear)': (LinearSVC(
            dual='auto', max_iter=5000, random_state=seed
        ), {
            'model__C': [0.03, 0.1, 0.3, 1.0, 3.0],
            'model__class_weight': [None, 'balanced'],
        }),
        'Random Forest': (RandomForestClassifier(
            n_jobs=-1, random_state=seed
        ), {
            'model__n_estimators': [120, 240],
            'model__max_depth': [10, 18, None],
            'model__min_samples_leaf': [20, 50, 100],
            'model__max_features': ['sqrt', 0.8],
        }),
        'Extra Trees': (ExtraTreesClassifier(
            n_jobs=-1, random_state=seed
        ), {
            'model__n_estimators': [120, 240],
            'model__max_depth': [10, 18, None],
            'model__min_samples_leaf': [20, 50, 100],
            'model__max_features': ['sqrt', 0.8],
        }),
        'Gradient Boosting': (GradientBoostingClassifier(random_state=seed), {
            'model__n_estimators': [100, 180, 260],
            'model__learning_rate': [0.03, 0.06, 0.1],
            'model__max_depth': [2, 3],
            'model__min_samples_leaf': [20, 50],
        }),
        'Histogram Gradient Boosting': (HistGradientBoostingClassifier(
            random_state=seed
        ), {
            'model__max_iter': [100, 200, 300],
            'model__learning_rate': [0.03, 0.06, 0.1],
            'model__max_leaf_nodes': [15, 31],
            'model__l2_regularization': [0.0, 1.0],
        }),
    }


def validation_scores(probability, X, y):
    score = probability
    return {
        'validation_roc_auc': float(roc_auc_score(y, score)),
        'validation_average_precision': float(average_precision_score(y, score)),
        'validation_brier': float(brier_score_loss(y, score)),
    }


def make_split(df):
    X = df[list(SPECS)]
    y = df[TARGET].astype(int)
    groups = pd.util.hash_pandas_object(X, index=False).values
    # Assign unique full profiles first, then map their folds back to all rows.
    # This preserves the no-identical-profile-across-splits rule and is faster
    # than running StratifiedGroupKFold over 253k repeated rows.
    _, inverse = np.unique(groups, return_inverse=True)
    group_size = np.bincount(inverse)
    group_positive = np.bincount(inverse, weights=y.to_numpy())
    group_label = (group_positive >= group_size / 2).astype(int)
    profile_folds = list(StratifiedKFold(
        n_splits=5, shuffle=True, random_state=42
    ).split(np.zeros(len(group_size)), group_label))
    fold_ids = np.empty(len(group_size), dtype=np.int8)
    for fold_id, (_, held_out_profiles) in enumerate(profile_folds):
        fold_ids[held_out_profiles] = fold_id
    row_fold = fold_ids[inverse]
    test = np.flatnonzero(row_fold == 0)
    validation = np.flatnonzero(row_fold == 1)
    train = np.flatnonzero(row_fold >= 2)
    return X, y, groups, train, validation, test


def run_tuning(X, y, groups, train_ids, val_ids, sample_size, refit_size, iterations, folds, seed, reuse_search=False):
    all_rows = []
    search_rows = []
    validation_probabilities = {}
    fitted_models = {}
    available = min(sample_size, len(train_ids))
    sample_ids, _ = train_test_split(
        train_ids, train_size=available, stratify=y.iloc[train_ids],
        random_state=seed,
    )
    Xs = X.iloc[sample_ids][SHORT]
    ys = y.iloc[sample_ids]
    gs = groups[sample_ids]
    validation_size = min(10000, len(val_ids))
    _, validation_ids = train_test_split(
        val_ids, test_size=validation_size,
        stratify=y.iloc[val_ids], random_state=seed,
    )
    refit_count = min(refit_size, len(train_ids))
    refit_pool = train_ids[~np.isin(train_ids, sample_ids)]
    refit_ids, _ = train_test_split(
        refit_pool, train_size=min(refit_count, len(refit_pool)),
        stratify=y.iloc[refit_pool], random_state=seed + 1,
    )
    cv = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    cached_search = None
    if reuse_search:
        cache_path = out / 'hyperparameter_search.csv'
        if not cache_path.exists():
            raise FileNotFoundError('Cannot reuse search: hyperparameter_search.csv is missing.')
        cached_search = pd.read_csv(cache_path).set_index('model')
        expected_models = set(candidates(seed))
        if set(cached_search.index) != expected_models:
            raise ValueError('Cached search model families do not match the current workflow.')
        if not (cached_search['search_sample_rows'] == len(sample_ids)).all() or not (cached_search['cv_folds'] == folds).all():
            raise ValueError('Cached search sample size or fold count does not match this run.')

    for name, (estimator, params) in candidates(seed).items():
        print(f'Tuning {name} ({len(sample_ids):,} sample rows)...', flush=True)
        pipe = Pipeline([('preprocess', preprocessor(SHORT)), ('model', estimator)])
        if cached_search is not None:
            saved = cached_search.loc[name]
            best_params = json.loads(saved['best_parameters'])
            best_score = float(saved['best_cv_average_precision'])
            best_std = float(saved['best_cv_std'])
            actual_draws = min(iterations, len(ParameterGrid(params)))
            elapsed = float(saved.get('search_seconds', 0.0))
        else:
            search = RandomizedSearchCV(
                pipe, params, n_iter=iterations, scoring='average_precision',
                cv=cv, n_jobs=1, refit=False, random_state=seed,
                return_train_score=False, error_score='raise', verbose=0,
            )
            started = time.time()
            search.fit(Xs, ys, groups=gs)
            best_index = int(search.best_index_)
            best_params = search.best_params_
            best_score = float(search.best_score_)
            best_std = float(search.cv_results_['std_test_score'][best_index])
            actual_draws = int(search.n_iter_)
            elapsed = round(time.time() - started, 2)
        search_rows.append({
            'model': name,
            'search_sample_rows': len(sample_ids),
            'cv_folds': folds,
            'sampled_candidates': actual_draws,
            'best_cv_average_precision': best_score,
            'best_cv_std': best_std,
            'best_parameters': json.dumps(best_params, sort_keys=True),
            'search_seconds': elapsed,
        })

        # Refit on a stratified training sample, then score an independent
        # validation sample. Calibrate LinearSVC on training data only so its
        # decision score can use the same 0-1 threshold control as other models.
        fitted = clone(pipe).set_params(**best_params)
        fitted.fit(X.iloc[refit_ids][SHORT], y.iloc[refit_ids])
        probability_model = fitted
        if name == 'Support Vector Machine (linear)':
            probability_model = CalibratedClassifierCV(
                estimator=fitted, method='sigmoid', cv=3
            ).fit(X.iloc[refit_ids][SHORT], y.iloc[refit_ids])
        fitted_models[name] = probability_model
        probability = probability_model.predict_proba(
            X.iloc[validation_ids][SHORT]
        )[:, 1]
        validation_probabilities[name] = probability
        metrics = validation_scores(
            probability, X.iloc[validation_ids][SHORT], y.iloc[validation_ids]
        )
        cost_best, _ = choose_threshold(
            threshold_table(y.iloc[validation_ids], probability), 1.0, 5.0
        )
        chosen_threshold = float(min(cost_best.threshold, 1.0))
        prediction = probability >= chosen_threshold
        y_validation = y.iloc[validation_ids].to_numpy()
        tp = int(np.sum((y_validation == 1) & prediction))
        fp = int(np.sum((y_validation == 0) & prediction))
        fn = int(np.sum((y_validation == 1) & ~prediction))
        tn = int(np.sum((y_validation == 0) & ~prediction))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
        all_rows.append({
            'model': name,
            'features': ', '.join(SHORT),
            'refit_rows': len(refit_ids),
            'validation_rows': len(validation_ids),
            'best_cv_average_precision': best_score,
            'best_parameters': json.dumps(best_params, sort_keys=True),
            **metrics,
            'cost_fp_assumption': 1.0,
            'cost_fn_assumption': 5.0,
            'cost_selected_threshold': chosen_threshold,
            'precision_at_cost_threshold': precision,
            'recall_at_cost_threshold': recall,
            'f1_at_cost_threshold': f1,
            'true_positive': tp,
            'false_positive': fp,
            'false_negative': fn,
            'true_negative': tn,
        })

    search_frame = pd.DataFrame(search_rows).sort_values(
        'best_cv_average_precision', ascending=False
    )
    validation_frame = pd.DataFrame(all_rows).sort_values(
        'validation_average_precision', ascending=False
    )
    search_frame.to_csv(out / 'hyperparameter_search.csv', index=False)
    validation_frame.to_csv(out / 'tuned_model_validation.csv', index=False)
    probability_matrix = np.vstack([
        validation_probabilities[name] for name in validation_frame['model']
    ])
    np.savez_compressed(
        out / 'tuned_validation_predictions.npz',
        y=y.iloc[validation_ids].to_numpy(),
        model_names=np.asarray(validation_frame['model'].tolist(), dtype='U'),
        probabilities=probability_matrix,
    )
    return search_frame, validation_frame, sample_ids, fitted_models, validation_ids, refit_ids


def run_pca(X, y, train_ids, val_ids):
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    prep = preprocessor(SHORT)
    X_train = prep.fit_transform(X.iloc[train_ids][SHORT])
    X_val = prep.transform(X.iloc[val_ids][SHORT])
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    max_components = min(X_train.shape[1], X_train.shape[0])
    pca_full = PCA(n_components=max_components, svd_solver='full')
    pca_full.fit(X_train)
    variance = pca_full.explained_variance_ratio_
    numerical_rank = int(np.sum(pca_full.explained_variance_ > 1e-12))
    dimensions = sorted(set([1, 2, 3, 5, 8, 12, 16, 20, numerical_rank]))
    dimensions = [k for k in dimensions if k <= numerical_rank]

    # Apples-to-apples baseline: same standardized encoded matrix, without PCA.
    direct_model = LogisticRegression(C=1.0, max_iter=1500, random_state=42)
    direct_model.fit(X_train, y.iloc[train_ids])
    direct_p = direct_model.predict_proba(X_val)[:, 1]
    rows = [{
        'representation': 'No PCA (standardized encoded inputs)',
        'principal_components': X_train.shape[1],
        'validation_rows': len(val_ids),
        'variance_explained': 1.0,
        'validation_roc_auc': float(roc_auc_score(y.iloc[val_ids], direct_p)),
        'validation_average_precision': float(average_precision_score(y.iloc[val_ids], direct_p)),
        'validation_brier': float(brier_score_loss(y.iloc[val_ids], direct_p)),
    }]

    # Also report the existing app preprocessing as context for the project.
    baseline = logistic_pipeline(SHORT)
    baseline.fit(X.iloc[train_ids][SHORT], y.iloc[train_ids])
    base_p = baseline.predict_proba(X.iloc[val_ids][SHORT])[:, 1]
    rows.append({
        'representation': 'No PCA (app Logistic Regression preprocessing)',
        'principal_components': max_components,
        'validation_rows': len(val_ids),
        'variance_explained': 1.0,
        'validation_roc_auc': float(roc_auc_score(y.iloc[val_ids], base_p)),
        'validation_average_precision': float(average_precision_score(y.iloc[val_ids], base_p)),
        'validation_brier': float(brier_score_loss(y.iloc[val_ids], base_p)),
    })
    for k in dimensions:
        pca = PCA(n_components=k, svd_solver='full')
        train_pc = pca.fit_transform(X_train)
        val_pc = pca.transform(X_val)
        model = LogisticRegression(C=1.0, max_iter=1500, random_state=42)
        model.fit(train_pc, y.iloc[train_ids])
        p = model.predict_proba(val_pc)[:, 1]
        rows.append({
            'representation': f'PCA + Logistic Regression ({k} PCs)',
            'principal_components': k,
            'validation_rows': len(val_ids),
            'variance_explained': float(np.sum(pca.explained_variance_ratio_)),
            'validation_roc_auc': float(roc_auc_score(y.iloc[val_ids], p)),
            'validation_average_precision': float(average_precision_score(y.iloc[val_ids], p)),
            'validation_brier': float(brier_score_loss(y.iloc[val_ids], p)),
        })
    result = pd.DataFrame(rows).sort_values('principal_components')
    result.to_csv(out / 'pca_comparison.csv', index=False)
    return result, X_train.shape[1], numerical_rank


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data' / 'diabetes_binary_health_indicators_BRFSS2015.csv')
    parser.add_argument('--sample-size', type=int, default=10000,
                        help='Stratified training rows used for hyperparameter search.')
    parser.add_argument('--iterations', type=int, default=8,
                        help='Random parameter settings evaluated per algorithm.')
    parser.add_argument('--refit-size', type=int, default=40000,
                        help='Stratified training rows used to fit each tuned comparison model.')
    parser.add_argument('--cv-folds', type=int, default=3)
    parser.add_argument('--pca-only', action='store_true',
                        help='Regenerate the PCA comparison without rerunning model searches.')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    df = load_data(args.data)
    X, y, groups, train_ids, val_ids, test_ids = make_split(df)
    assert not (set(groups[train_ids]) & set(groups[val_ids]))
    assert not (set(groups[train_ids]) & set(groups[test_ids]))
    assert not (set(groups[val_ids]) & set(groups[test_ids]))

    print(f'Scikit-learn {sklearn.__version__}; train/validation/test = '
          f'{len(train_ids):,}/{len(val_ids):,}/{len(test_ids):,}', flush=True)
    if args.pca_only:
        pca, dimensions, rank = run_pca(X, y, train_ids, val_ids)
        print(f'Encoded input dimensions: {dimensions}; effective PCA rank: {rank}', flush=True)
        print(pca.to_string(index=False), flush=True)
        return
    search, tuned, sample_ids, _, _, _ = run_tuning(
        X, y, groups, train_ids, val_ids,
        args.sample_size, args.refit_size, args.iterations, args.cv_folds, args.seed,
    )
    pca, encoded_features, pca_rank = run_pca(X, y, train_ids, val_ids)

    summary = {
        'method': 'RandomizedSearchCV on a 10,000-row stratified training sample with 3-fold StratifiedGroupKFold; selected settings refit on a non-overlapping 40,000-row stratified sample from the remaining training partition; validation compared on a 10,000-row stratified sample; each candidate threshold selected on validation with FP=1 and FN=5; test partition untouched.',
        'outer_split_method': 'Five-fold stratification over unique full 21-feature profiles using each profile majority target, then assigning every original row to the profile fold; this keeps identical profiles in one partition.',
        'feature_set': SHORT,
        'input_rows': len(df),
        'train_rows': len(train_ids),
        'validation_rows': len(val_ids),
        'test_rows_reserved': len(test_ids),
        'search_sample_rows': len(sample_ids),
        'refit_rows_per_model': min(args.refit_size, len(train_ids)),
        'validation_sample_rows_per_model': min(10000, len(val_ids)),
        'search_iterations_per_model': args.iterations,
        'cv_folds': args.cv_folds,
        'seed': args.seed,
        'encoded_dimensions_before_pca': encoded_features,
        'effective_pca_rank': pca_rank,
        'python_version': platform.python_version(),
        'sklearn_version': sklearn.__version__,
        'numpy_version': np.__version__,
        'pandas_version': pd.__version__,
        'scipy_version': scipy.__version__,
        'selected_by_cv_average_precision': search.iloc[0]['model'],
        'best_validation_average_precision': tuned.iloc[0]['validation_average_precision'],
        'note': 'Exploratory course comparison. Threshold metrics are per-candidate validation results under illustrative FP=1 and FN=5 penalties; the About page provides cost and manual-threshold controls. This experiment does not replace the deployed model or its operating threshold; test data remain untouched.',
    }
    (ROOT / 'reports' / 'tuning_run.json').write_text(json.dumps(summary, indent=2))
    print('\nTuned models (validation, sorted by Average Precision):', flush=True)
    print(tuned.to_string(index=False), flush=True)
    print('\nPCA comparison:', flush=True)
    print(pca.to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
