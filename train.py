
"""Offline rebuild. Test data never select features, model, or threshold."""
import argparse
import hashlib
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.base import clone

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_score,
    recall_score, f1_score, confusion_matrix, brier_score_loss,
    roc_curve, precision_recall_curve
)
from sklearn.inspection import permutation_importance

from utils.data_loader import ROOT, TARGET, SPECS, SHORT, SOURCES, load_data
from utils.threshold import threshold_table, choose_threshold
from tune_models import make_split, run_tuning, run_pca, preprocessor


def evaluate(y, p, t):
    pred = p >= t
    return dict(
        roc_auc=float(roc_auc_score(y, p)),
        average_precision=float(average_precision_score(y, p)),
        brier=float(brier_score_loss(y, p)),
        precision=float(precision_score(y, pred, zero_division=0)),
        recall=float(recall_score(y, pred, zero_division=0)),
        f1=float(f1_score(y, pred, zero_division=0)),
        confusion_matrix=confusion_matrix(y, pred, labels=[0, 1]).tolist(),
        n=len(y),
        positive_count=int(sum(y))
    )


def questionnaire_size_report(X, y, refit_ids, validation_ids, estimator_template, params, reports):
    """Compare 5, 8, and 21 inputs on one validation sample with fixed HGB settings."""
    from sklearn.pipeline import Pipeline

    previous_short = ['Age', 'BMI', 'HighBP', 'HighChol', 'GenHlth']
    sets = [
        ('5 inputs (previous form)', previous_short),
        ('8 inputs (current form)', list(SHORT)),
        ('21 inputs (all predictors)', list(SPECS)),
    ]
    rows = []
    predictions = {}
    estimator_params = {
        key.removeprefix('model__'): value for key, value in params.items()
    }
    for label, cols in sets:
        pipe = Pipeline([
            ('preprocess', preprocessor(cols)),
            ('model', clone(estimator_template).set_params(**estimator_params)),
        ])
        pipe.fit(X.iloc[refit_ids][cols], y.iloc[refit_ids])
        probability = pipe.predict_proba(X.iloc[validation_ids][cols])[:, 1]
        predictions[str(len(cols))] = probability
        rows.append(dict(
            questionnaire=label,
            feature_count=len(cols),
            train_rows=len(refit_ids),
            validation_rows=len(validation_ids),
            roc_auc=float(roc_auc_score(y.iloc[validation_ids], probability)),
            average_precision=float(average_precision_score(y.iloc[validation_ids], probability)),
            brier=float(brier_score_loss(y.iloc[validation_ids], probability)),
            parameters='Selected 8-input model settings held fixed',
        ))
    frame = pd.DataFrame(rows)
    frame.to_csv(reports / 'questionnaire_size_comparison.csv', index=False)
    np.savez_compressed(
        reports / 'questionnaire_size_predictions.npz',
        y=y.iloc[validation_ids].to_numpy(),
        **{f'p_{k}': v for k, v in predictions.items()},
    )
    return frame


def wilson_interval(successes, total, z=1.959963984540054):
    if total <= 0:
        return (None, None)
    p = successes / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return (float(max(0.0, center - half)), float(min(1.0, center + half)))


def bootstrap_score_difference(y, p_a, p_b, reps=1000, seed=2026):
    """Paired stratified bootstrap; descriptive because models were selected on validation."""
    y = np.asarray(y, dtype=int)
    p_a, p_b = np.asarray(p_a), np.asarray(p_b)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    rng = np.random.default_rng(seed)
    ap_delta, auc_delta = [], []
    for _ in range(reps):
        ix = np.concatenate((
            rng.choice(pos, len(pos), replace=True),
            rng.choice(neg, len(neg), replace=True),
        ))
        ap_delta.append(
            average_precision_score(y[ix], p_a[ix]) -
            average_precision_score(y[ix], p_b[ix])
        )
        auc_delta.append(
            roc_auc_score(y[ix], p_a[ix]) - roc_auc_score(y[ix], p_b[ix])
        )
    return {
        'average_precision_delta_low': float(np.quantile(ap_delta, .025)),
        'average_precision_delta_high': float(np.quantile(ap_delta, .975)),
        'roc_auc_delta_low': float(np.quantile(auc_delta, .025)),
        'roc_auc_delta_high': float(np.quantile(auc_delta, .975)),
        'bootstrap_replicates': reps,
        'interpretation': 'Paired validation bootstrap; exploratory and selection-conditioned, not confirmatory.',
    }


def write_evaluation_supplements(X, y, groups, val, test, pval, ptest,
                                 threshold, reports, out, selected_algorithm):
    """Create uncertainty, calibration, operating-point, and paired-comparison reports."""
    # Fixed test operating-point intervals (Wilson) and score reliability by decile.
    test_rows = []
    cm = confusion_matrix(y.iloc[test], ptest >= threshold, labels=[0, 1])
    tn, fp = cm[0]
    fn, tp = cm[1]
    for name, k, n in [
        ('precision', tp, tp + fp), ('recall', tp, tp + fn),
        ('false_positive_rate', fp, fp + tn),
    ]:
        lo, hi = wilson_interval(int(k), int(n))
        test_rows.append(dict(metric=name, estimate=k / n if n else None,
                              ci_95_low=lo, ci_95_high=hi, numerator=int(k), denominator=int(n),
                              method='Wilson interval; observation-level'))
    pd.DataFrame(test_rows).to_csv(reports / 'test_operating_point_intervals.csv', index=False)

    calibration = pd.DataFrame({'score': ptest, 'label': y.iloc[test].to_numpy()})
    calibration['score_decile'] = pd.qcut(calibration.score, 10, labels=False, duplicates='drop') + 1
    cal = calibration.groupby('score_decile', observed=True).agg(
        n=('label', 'size'), mean_score=('score', 'mean'), observed_label_rate=('label', 'mean')
    ).reset_index()
    cal.to_csv(reports / 'test_calibration_by_decile.csv', index=False)

    # Paired bootstrap uses identical rows for the selected and comparison model.
    saved = np.load(reports / 'tuned_validation_predictions.npz')
    names = saved['model_names'].astype(str)
    probabilities = saved['probabilities']
    selected_i = int(np.flatnonzero(names == selected_algorithm)[0])
    competitors = [i for i in range(len(names)) if i != selected_i]
    comparator_i = max(competitors, key=lambda i: average_precision_score(saved['y'], probabilities[i]))
    diff = bootstrap_score_difference(saved['y'], probabilities[selected_i], probabilities[comparator_i])
    pd.DataFrame([dict(
        selected_model=selected_algorithm, comparator=names[comparator_i],
        average_precision_delta=float(average_precision_score(saved['y'], probabilities[selected_i]) - average_precision_score(saved['y'], probabilities[comparator_i])),
        roc_auc_delta=float(roc_auc_score(saved['y'], probabilities[selected_i]) - roc_auc_score(saved['y'], probabilities[comparator_i])),
        **diff,
    )]).to_csv(reports / 'model_selection_bootstrap.csv', index=False)

    # Paired 5/8/21 input AP deltas on identical validation respondents.
    q = np.load(reports / 'questionnaire_size_predictions.npz')
    qrows = []
    for a, b in [('8', '5'), ('21', '8')]:
        delta = bootstrap_score_difference(q['y'], q[f'p_{a}'], q[f'p_{b}'], reps=1000, seed=2026 + int(a))
        qrows.append(dict(comparison=f'{a} minus {b} inputs',
                          average_precision_delta=float(average_precision_score(q['y'], q[f'p_{a}']) - average_precision_score(q['y'], q[f'p_{b}'])),
                          roc_auc_delta=float(roc_auc_score(q['y'], q[f'p_{a}']) - roc_auc_score(q['y'], q[f'p_{b}'])),
                          **delta))
    pd.DataFrame(qrows).to_csv(reports / 'questionnaire_size_bootstrap.csv', index=False)

    # Threshold stability under alternative assumed false-positive/negative ratios.
    from utils.threshold import threshold_table, choose_threshold
    table = threshold_table(y.iloc[val], pval)
    cost_rows = []
    for fp_cost, fn_cost in [(1, 1), (1, 2), (1, 5), (1, 10)]:
        chosen, _ = choose_threshold(table, fp_cost, fn_cost)
        vv = evaluate(y.iloc[val], pval, float(chosen.threshold))
        cost_rows.append(dict(fp_cost=fp_cost, fn_cost=fn_cost,
                              validation_threshold=float(chosen.threshold),
                              precision=vv['precision'], recall=vv['recall'],
                              false_positives=vv['confusion_matrix'][0][1],
                              false_negatives=vv['confusion_matrix'][1][0]))
    pd.DataFrame(cost_rows).to_csv(reports / 'threshold_cost_sensitivity.csv', index=False)

    # Cluster bootstrap by identical full predictor profile to reflect the split unit.
    group_values, inv = np.unique(groups[test], return_inverse=True)
    n_groups = len(group_values)
    rng = np.random.default_rng(8831)
    boot = {k: [] for k in ('roc_auc', 'average_precision', 'brier')}
    yt = y.iloc[test].to_numpy()
    for _ in range(300):
        draw = rng.integers(0, n_groups, n_groups)
        weights_by_group = np.bincount(draw, minlength=n_groups)
        weights = weights_by_group[inv]
        if not np.any(weights[yt == 1]) or not np.any(weights[yt == 0]):
            continue
        boot['roc_auc'].append(roc_auc_score(yt, ptest, sample_weight=weights))
        boot['average_precision'].append(average_precision_score(yt, ptest, sample_weight=weights))
        boot['brier'].append(brier_score_loss(yt, ptest, sample_weight=weights))
    base = evaluate(y.iloc[test], ptest, threshold)
    rows = []
    for metric in boot:
        rows.append(dict(metric=metric, estimate=base[metric],
                         ci_95_low=float(np.quantile(boot[metric], .025)),
                         ci_95_high=float(np.quantile(boot[metric], .975)),
                         bootstrap_replicates=len(boot[metric]),
                         resampling_unit='Full 21-predictor profile cluster'))
    pd.DataFrame(rows).to_csv(reports / 'test_cluster_bootstrap_intervals.csv', index=False)

    # Wilson intervals for subgroup recall and FPR; small groups remain unstable.
    fairness = pd.read_csv(out / 'fairness.csv')
    lower_recall, upper_recall, lower_fpr, upper_fpr = [], [], [], []
    for row in fairness.itertuples(index=False):
        lo, hi = wilson_interval(int(row.TP), int(row.TP + row.FN))
        flo, fhi = wilson_interval(int(row.FP), int(row.FP + row.TN))
        lower_recall.append(lo); upper_recall.append(hi)
        lower_fpr.append(flo); upper_fpr.append(fhi)
    fairness['recall_ci_95_low'] = lower_recall
    fairness['recall_ci_95_high'] = upper_recall
    fairness['FPR_ci_95_low'] = lower_fpr
    fairness['FPR_ci_95_high'] = upper_fpr
    fairness['interval_method'] = 'Wilson; observation-level, not cluster-adjusted'
    fairness.to_csv(out / 'fairness.csv', index=False)


def build(features, algorithm):
    """All preprocessing lives in the pipeline. Original BMI values are retained."""
    other_numeric = [
        c for c in features if c in ['MentHlth', 'PhysHlth']
    ]
    category = [
        c for c in features if c not in other_numeric + ['BMI']
    ]
    parts = []

    if 'BMI' in features:
        parts.append((
            'bmi',
            Pipeline([
                ('impute', SimpleImputer(strategy='median')),
                ('scale', StandardScaler())
            ]),
            ['BMI']
        ))

    if other_numeric:
        parts.append((
            'numeric',
            Pipeline([
                ('impute', SimpleImputer(strategy='median')),
                ('scale', StandardScaler())
            ]),
            other_numeric
        ))

    if category:
        parts.append((
            'category',
            Pipeline([
                ('impute', SimpleImputer(strategy='most_frequent')),
                ('encode', OneHotEncoder(
                    handle_unknown='ignore',
                    sparse_output=False
                ))
            ]),
            category
        ))

    est = (
        LogisticRegression(max_iter=1000, C=1.)
        if algorithm == 'Logistic Regression'
        else HistGradientBoostingClassifier(
            max_depth=3,
            max_iter=300,
            learning_rate=0.05,
            random_state=0
        )
        if algorithm == 'Gradient Boosting'
        else RandomForestClassifier(
            n_estimators=140,
            max_depth=14,
            min_samples_leaf=30,
            max_features='sqrt',
            n_jobs=-1,
            random_state=42
        )
    )

    return Pipeline([
        ('preprocess', ColumnTransformer(parts)),
        ('model', est)
    ])


def feature_selection_report(X, y, train, val, features, reports):
    """Feature-selection evidence on reproducible samples, never on test."""
    from sklearn.model_selection import train_test_split

    train_sample, _ = train_test_split(
        train, train_size=min(40000, len(train)),
        stratify=y.iloc[train], random_state=42,
    )
    validation_sample, _ = train_test_split(
        val, test_size=min(10000, len(val)),
        stratify=y.iloc[val], random_state=42,
    )
    Xtr, ytr = X.iloc[train_sample], y.iloc[train_sample]
    Xva, yva = X.iloc[validation_sample], y.iloc[validation_sample]

    def auc(cols):
        pipe = build(cols, 'Logistic Regression').fit(
            Xtr[cols], ytr
        )
        return float(
            roc_auc_score(
                yva,
                pipe.predict_proba(Xva[cols])[:, 1]
            )
        )

    full, short = auc(features), auc(SHORT)

    rows = [
        dict(
            feature=c,
            in_short=c in SHORT,
            drop_from_full_auc_loss=full - auc(
                [x for x in features if x != c]
            ),
            drop_from_short_auc_loss=(
                short - auc([x for x in SHORT if x != c])
                if c in SHORT else np.nan
            ),
            add_to_short_auc_gain=(
                auc(SHORT + [c]) - short
                if c not in SHORT else np.nan
            )
        )
        for c in features
    ]

    chosen, rest, path = [], list(features), []

    for k in range(1, 9):
        scores = {
            c: auc(chosen + [c])
            for c in rest
        }
        best = max(scores, key=scores.get)
        chosen.append(best)
        rest.remove(best)
        path.append(dict(
            step=k,
            feature=best,
            validation_auc=scores[best]
        ))

    table = pd.DataFrame(rows)
    table['forward_step'] = table.feature.map({
        p['feature']: p['step'] for p in path
    })

    table.sort_values(
        'drop_from_full_auc_loss',
        ascending=False
    ).to_csv(reports / 'feature_selection.csv', index=False)

    pd.DataFrame(path).to_csv(
        reports / 'forward_selection.csv',
        index=False
    )

    return dict(
        full_validation_auc=full,
        short_validation_auc=short,
        train_sample_rows=len(train_sample),
        validation_sample_rows=len(validation_sample),
        forward_top_k=chosen[:len(SHORT)],
        forward_top_k_equals_short=(
            set(chosen[:len(SHORT)]) == set(SHORT)
        )
    )


def main(path, reuse_search=False):
    out = ROOT / 'models'
    reports = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    reports.mkdir(exist_ok=True)

    df = load_data(path)
    features = list(SPECS)
    X, y, groups, train, val, test = make_split(df)

    assert not (
        set(groups[train]) & set(groups[val])
        or set(groups[train]) & set(groups[test])
        or set(groups[val]) & set(groups[test])
    )

    dup = df.duplicated()
    first = ~dup.values

    bins = pd.cut(
        df.BMI,
        [0, 18.5, 25, 30, 35, 40, 50, 60, np.inf]
    )

    audit = dict(
        rows=len(df),
        columns=list(df.columns),
        dtypes=df.dtypes.astype(str).to_dict(),
        missing=df.isna().sum().to_dict(),
        exact_duplicate_rows=int(dup.sum()),
        conflicting_predictor_profiles=int(
            df.groupby(features)[TARGET].nunique().gt(1).sum()
        ),
        class_counts=y.value_counts().to_dict(),
        ranges={
            c: [float(df[c].min()), float(df[c].max())]
            for c in df
        },
        splits={
            name: {
                'n': len(ids),
                'positive_rate': float(y.iloc[ids].mean())
            }
            for name, ids in [
                ('train', train),
                ('validation', val),
                ('test', test)
            ]
        },
        duplicates=dict(
            extra_copies_by_class={
                str(k): int(v)
                for k, v in df[dup][TARGET].astype(int).value_counts().items()
            },
            positive_rate_all_rows=float(y.mean()),
            positive_rate_after_dedup=float(
                df.drop_duplicates()[TARGET].mean()
            )
        ),
        bmi_positive_rate_by_bin={
            str(k): float(v)
            for k, v in y.groupby(bins, observed=True).mean().items()
        },
        bmi_cap=None,
        bmi_handling='Original BMI values retained; no upper cap'
    )

    (reports / 'data_audit.json').write_text(
        json.dumps(audit, indent=2)
    )

    pd.DataFrame([
        dict(
            feature=c,
            label=v[0],
            encoding=v[1],
            decision=v[2]
        )
        for c, v in SPECS.items()
    ]).to_csv(
        reports / 'feature_dictionary.csv',
        index=False
    )

    print(
        'Feature-selection evidence (validation only)',
        flush=True
    )

    fs = feature_selection_report(
        X, y, train, val, features, reports
    )

    if not fs['forward_top_k_equals_short']:
        print(
            'NOTE: the validation AUC-ranked forward top-%d %s differs from '
            'the curated eight-input questionnaire %s. This is recorded as '
            'a feature-selection tradeoff, not a pipeline error.'
            % (len(SHORT), fs['forward_top_k'], SHORT),
            flush=True
        )

    print('Running course model hyperparameter search', flush=True)
    search_frame, tuned_frame, search_ids, tuned_models, model_val, refit_ids = run_tuning(
        X, y, groups, train, val,
        sample_size=10000,
        refit_size=40000,
        iterations=16,
        folds=3,
        seed=42,
        reuse_search=reuse_search,
    )
    pca_frame, encoded_dimensions, pca_rank = run_pca(
        X, y, train, val
    )

    candidates = []
    fitted = {}

    for alg in [
        'Logistic Regression',
        'Random Forest',
        'Gradient Boosting'
    ]:
        key = 'full | ' + alg
        print('Training ' + key, flush=True)
        pipe = build(features, alg)
        pipe.fit(X.iloc[refit_ids][features], y.iloc[refit_ids])
        p = pipe.predict_proba(X.iloc[model_val][features])[:, 1]
        candidates.append(dict(
            candidate=key,
            feature_set='full',
            algorithm=alg,
            n_features=len(features),
            **evaluate(y.iloc[model_val], p, .5)
        ))
        fitted[key] = (pipe, features, p)

    # Add the tuned course candidates to the same validation comparison.
    for alg, pipe in tuned_models.items():
        key = 'short | tuned | ' + alg
        p = pipe.predict_proba(X.iloc[model_val][SHORT])[:, 1]
        candidates.append(dict(
            candidate=key,
            feature_set='short',
            algorithm=alg,
            n_features=len(SHORT),
            **evaluate(y.iloc[model_val], p, .5)
        ))
        fitted[key] = (pipe, SHORT, p)

    best_full_auc = max(
        c['roc_auc'] for c in candidates
        if c['feature_set'] == 'full'
    )

    eligible = [
        c for c in candidates
        if c['feature_set'] == 'short'
        and c['candidate'].startswith('short | tuned | ')
        and c['roc_auc'] >= best_full_auc - .010
    ]

    if not eligible:
        eligible = [
            c for c in candidates
            if c['feature_set'] == 'short'
            and c['candidate'].startswith('short | tuned | ')
        ]
    if not eligible:
        eligible = [c for c in candidates if c['feature_set'] == 'short']

    # Prefer the short candidate with the best validation Average Precision
    # among models within 0.010 ROC-AUC of the best full-feature candidate.
    selected = max(eligible, key=lambda c: c['average_precision'])

    pipeline, cols, pval = fitted[selected['candidate']]
    selected_params = json.loads(
        tuned_frame.loc[
            tuned_frame['model'] == selected['algorithm'],
            'best_parameters'
        ].iloc[0]
    )
    questionnaire_sizes = questionnaire_size_report(
        X, y, refit_ids, model_val, pipeline.named_steps['model'],
        selected_params, reports,
    )
    if selected['candidate'].startswith('short | tuned | '):
        print('Refitting selected tuned model on the full training partition', flush=True)
        pipeline = clone(pipeline)
        pipeline.fit(X.iloc[train][cols], y.iloc[train])
    pval = pipeline.predict_proba(X.iloc[val][cols])[:, 1]

    # Reference model: age + BMI only. It does not select the final model.
    reference = []

    for key, set_name, alg, ref_cols in [
        (
            'baseline: Age + BMI only | Logistic Regression',
            'baseline',
            'Logistic Regression',
            ['Age', 'BMI']
        )
    ]:
        print('Training ' + key, flush=True)

        ref_pipe = build(ref_cols, alg).fit(
            X.iloc[refit_ids][ref_cols],
            y.iloc[refit_ids]
        )

        reference.append(dict(
            candidate=key,
            feature_set=set_name,
            algorithm=alg,
            n_features=len(ref_cols),
            **evaluate(
                y.iloc[model_val],
                ref_pipe.predict_proba(
                    X.iloc[model_val][ref_cols]
                )[:, 1],
                .5
            )
        ))

    best, _ = choose_threshold(
        threshold_table(y.iloc[val], pval),
        1.,
        5.
    )

    threshold = float(best.threshold)

    ptest = pipeline.predict_proba(
        X.iloc[test][cols]
    )[:, 1]

    test_metrics = evaluate(
        y.iloc[test], ptest, threshold
    )

    # Report-only deduplicated sensitivity analysis.
    test_dedup = evaluate(
        y.iloc[test][first[test]],
        ptest[first[test]],
        threshold
    )

    val_dedup = evaluate(
        y.iloc[val][first[val]],
        pval[first[val]],
        threshold
    )

    joblib.dump(
        pipeline,
        out / 'pipeline.joblib',
        compress=3
    )

    np.savez_compressed(
        out / 'validation_predictions.npz',
        y=y.iloc[val].to_numpy(),
        p=pval
    )
    np.savez_compressed(
        out / 'test_predictions.npz',
        y=y.iloc[test].to_numpy(),
        p=ptest,
        groups=groups[test],
        threshold=np.asarray([threshold]),
    )

    fairness = []

    for feature in ['Age', 'Sex', 'Income', 'Education']:
        for group, block in (
            df.iloc[test]
            .assign(_p=ptest)
            .groupby(feature)
        ):
            yy = block[TARGET].astype(int)
            pp = block._p.to_numpy()

            if yy.nunique() != 2:
                continue

            mm = evaluate(yy, pp, threshold)
            tn, fp = mm['confusion_matrix'][0]
            fn, tp = mm['confusion_matrix'][1]

            fairness.append(dict(
                feature=feature,
                group=int(group),
                n=len(block),
                positive_rate=float(yy.mean()),
                roc_auc=mm['roc_auc'],
                precision=mm['precision'],
                recall=mm['recall'],
                FPR=fp / (tn + fp) if tn + fp else None,
                FDR=fp / (tp + fp) if tp + fp else None,
                TP=tp,
                FP=fp,
                FN=fn,
                TN=tn
            ))

    pd.DataFrame(fairness).to_csv(
        out / 'fairness.csv',
        index=False
    )

    write_evaluation_supplements(
        X, y, groups, val, test, pval, ptest, threshold,
        reports, out, selected['algorithm'],
    )

    fpr, tpr, _ = roc_curve(y.iloc[test], ptest)
    prec, rec, _ = precision_recall_curve(
        y.iloc[test], ptest
    )

    ix = np.unique(
        np.linspace(
            0, len(fpr) - 1,
            min(1000, len(fpr))
        ).astype(int)
    )

    jx = np.unique(
        np.linspace(
            0, len(prec) - 1,
            min(1000, len(prec))
        ).astype(int)
    )

    pd.DataFrame({
        'FPR': fpr[ix],
        'Recall': tpr[ix]
    }).to_csv(out / 'roc.csv', index=False)

    pd.DataFrame({
        'Recall': rec[jx],
        'Precision': prec[jx]
    }).to_csv(out / 'pr.csv', index=False)

    imp = permutation_importance(
        pipeline,
        X.iloc[val][cols],
        y.iloc[val],
        scoring='roc_auc',
        n_repeats=3,
        max_samples=5000,
        random_state=42,
        n_jobs=1
    )

    pd.DataFrame({
        'feature': cols,
        'validation_AUC_drop': imp.importances_mean,
        'sd': imp.importances_std
    }).sort_values(
        'validation_AUC_drop',
        ascending=False
    ).to_csv(
        reports / 'permutation_importance.csv',
        index=False
    )

    pd.DataFrame(
        candidates + reference
    ).drop(
        columns='confusion_matrix'
    ).to_csv(
        reports / 'validation_comparison.csv',
        index=False
    )

    background = (
        X.iloc[train][cols]
        .sample(min(256, len(train)), random_state=42)
        .astype(float)
        .to_dict(orient='records')
    )

    m = dict(
        target=TARGET,
        target_meaning={
            '0': 'No self-reported diabetes/prediabetes',
            '1': 'Self-reported diabetes or prediabetes'
        },
        sources=SOURCES,
        rows=len(df),
        features=cols,
        feature_names=cols,
        valid_input_ranges={
            c: audit['ranges'][c] for c in cols
        },
        valid_values={
            c: sorted(df[c].unique().tolist())
            for c in cols if c != 'BMI'
        },
        algorithm=selected['algorithm'],
        selected_candidate=selected['candidate'],
        threshold=threshold,
        cost_assumptions={
            'FP': 1,
            'FN': 5,
            'units': 'illustrative relative units, not medical costs'
        },
        test_metrics=test_metrics,
        test_metrics_deduplicated=test_dedup,
        validation_metrics=evaluate(
            y.iloc[val], pval, threshold
        ),
        validation_metrics_deduplicated=val_dedup,
        validation_candidates=candidates,
        validation_reference_models=reference,
        model_search=dict(
            method='RandomizedSearchCV with 3-fold StratifiedGroupKFold; Average Precision scored on a stratified 10,000-row training sample; up to 16 parameter draws per model (some search spaces are smaller).',
            models=search_frame['model'].tolist(),
            parameter_draws_requested_max=16,
            parameter_draws_per_model_actual=search_frame.set_index('model')['sampled_candidates'].astype(int).to_dict(),
            search_sample_rows=10000,
            comparison_refit_rows=40000,
            comparison_validation_rows=len(model_val),
            selected_parameters=json.loads(
                tuned_frame.loc[
                    tuned_frame['model'] == selected['algorithm'],
                    'best_parameters'
                ].iloc[0]
            ),
            selected_candidate_validation_average_precision=float(
                selected['average_precision']
            ),
        ),
        pca_experiment=dict(
            report='reports/pca_comparison.csv',
            encoded_dimensions=int(encoded_dimensions),
            effective_rank=int(pca_rank),
            validation_rows=int(pca_frame['validation_rows'].iloc[0]),
            used_for_final_pipeline=False,
        ),
        questionnaire_size_comparison=dict(
            report='reports/questionnaire_size_comparison.csv',
            validation_rows=int(questionnaire_sizes['validation_rows'].iloc[0]),
            selected_estimator=selected['algorithm'],
            settings_held_fixed=True,
        ),
        validation_uncertainty=dict(
            model_selection='reports/model_selection_bootstrap.csv',
            questionnaire_size='reports/questionnaire_size_bootstrap.csv',
            threshold_cost_sensitivity='reports/threshold_cost_sensitivity.csv',
            interpretation='Bootstrap intervals are exploratory; model selection and feature experiments reused validation data.',
        ),
        evaluation_uncertainty=dict(
            test_cluster_bootstrap='reports/test_cluster_bootstrap_intervals.csv',
            operating_point_intervals='reports/test_operating_point_intervals.csv',
            calibration='reports/test_calibration_by_decile.csv',
            fairness_intervals='models/fairness.csv',
        ),
        explanation=dict(
            method=(
                'Exact Shapley values over the questions, on the '
                'probability scale, relative to the average of a '
                '256-row training background. Contributions add '
                'up to (your estimate - background average).'
            ),
            background=background
        ),
        feature_selection=fs,
        bmi_cap=None,
        bmi_handling='Original BMI values retained; no upper cap',
        selection_rule=(
            'Run a 3-fold grouped randomized search with 16 randomized parameter '
            'draws per course model on a stratified 10,000-row training sample. '
            'Among eight-input '
            'candidates whose validation ROC-AUC is within 0.010 of the best '
            'full-feature baseline, select the highest validation Average '
            'Precision. Refit that candidate on the full training partition, '
            'select its operating threshold on the full validation partition '
            'using FP=1 and FN=5, then evaluate once on the untouched test set.'
        ),
        short_auc_gap=(
            best_full_auc - max(
                c['roc_auc'] for c in candidates
                if c['feature_set'] == 'short'
            )
        ),
        audit=audit,
        versions={
            'python': platform.python_version(),
            'sklearn': sklearn.__version__,
            'numpy': np.__version__,
            'pandas': pd.__version__,
            'scipy': scipy.__version__,
        },
        sha256=hashlib.sha256(
            Path(path).read_bytes()
        ).hexdigest(),
        reference={
            c: float(X.iloc[train][c].median())
            for c in cols
        },
        split_method=(
            'Approximately 60/20/20 folds over unique full 21-feature profiles, '
            'stratified by each profile majority target; all original rows for '
            'a profile stay in one partition. Original rows retained; no '
            'respondent IDs available.'
        ),
        imbalance=(
            'No oversampling or class weights: retain original '
            'prevalence and probability scale. Asymmetric validation '
            'cost selects operating threshold. Report PR-AUC, Brier, '
            'recall and precision; accuracy is not selection criterion.'
        ),
        intended_use=(
            'Educational retrospective classification of a self-reported BRFSS 2015 survey label. '
            'Not a screening, triage, diagnosis, individual clinical probability, or future-onset model. '
            'The source population includes respondents with prior diagnoses; the app makes no undiagnosed-population claim.'
        ),
        target_population_alignment=(
            'The outcome combines self-reported diabetes/prediabetes, including previously diagnosed respondents. '
            'The feature set does not identify undiagnosed disease. Consequently, the application is explicitly framed '
            'as a survey-label classification demonstration rather than an undiagnosed screening tool.'
        )
    )

    (out / 'model_meta.json').write_text(
        json.dumps(m, indent=2)
    )

    update_readme(m)

    tuning_path = reports / 'tuning_run.json'
    tuning_summary = json.loads(tuning_path.read_text()) if tuning_path.exists() else {}
    tuning_summary.update({
        'final_training_completed': True,
        'final_selected_candidate': selected['candidate'],
        'final_algorithm': selected['algorithm'],
        'final_threshold': threshold,
        'final_test_metrics': test_metrics,
        'final_test_deduplicated_metrics': test_dedup,
        'cost_assumptions': m['cost_assumptions'],
        'final_model_search': m['model_search'],
        'pca_experiment': m['pca_experiment'],
        'pipeline_rebuilt_by': 'train.py',
    })
    tuning_path.write_text(json.dumps(tuning_summary, indent=2))

    print(
        json.dumps({
            'selected': selected['candidate'],
            'threshold': threshold,
            'test': test_metrics,
            'test_deduplicated': test_dedup,
            'feature_selection': fs
        }, indent=2),
        flush=True
    )


def update_readme(m):
    """Keep the compact README results block in sync with the trained model."""
    path = ROOT / 'README.md'
    start, end = '<!-- RESULTS:START -->', '<!-- RESULTS:END -->'

    if not path.exists():
        return

    s = path.read_text(encoding='utf-8')

    if start not in s or end not in s:
        return

    tm = m['test_metrics']
    (tn, fp), (fn, tp) = tm['confusion_matrix']
    rows = [
        ('Selected model', m['algorithm']),
        ('Selected inputs', ', '.join(m['features'])),
        ('Validation threshold', f"{m['threshold']:.4f}"),
        ('Illustrative FP / FN penalties',
         f"{m['cost_assumptions']['FP']} / {m['cost_assumptions']['FN']}"),
        ('Held-out test records', f"{tm['n']:,}"),
        ('ROC-AUC', f"{tm['roc_auc']:.4f}"),
        ('Average Precision', f"{tm['average_precision']:.4f}"),
        ('Precision at threshold', f"{tm['precision']:.4f}"),
        ('Recall at threshold', f"{tm['recall']:.4f}"),
        ('Brier score', f"{tm['brier']:.4f}"),
    ]
    out = ['| Test result | Value |', '|---|---:|'] + [
        f'| {label} | {value} |' for label, value in rows
    ]
    out += [
        '',
        f"Confusion matrix: TN {tn:,}; FP {fp:,}; FN {fn:,}; TP {tp:,}.",
        '',
        f"This model was rebuilt by `train.py` with Python {m['versions']['python']} "
        f"and scikit-learn {m['versions']['sklearn']}. Precision and recall are "
        'measured on the untouched test partition at the validation-selected threshold.'
    ]

    path.write_text(
        s[:s.index(start) + len(start)]
        + '\n'
        + '\n'.join(out)
        + '\n'
        + s[s.index(end):],
        encoding='utf-8'
    )


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument(
        '--data',
        type=Path,
        default=ROOT / 'data/diabetes_binary_health_indicators_BRFSS2015.csv'
    )
    p.add_argument('--reuse-search', action='store_true', help='Reuse a completed matching hyperparameter_search.csv and refit/evaluate downstream artifacts.')
    args = p.parse_args()
    main(args.data, reuse_search=args.reuse_search)
