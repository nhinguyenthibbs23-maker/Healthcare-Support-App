import sys
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from utils.data_loader import ROOT, meta

# Ensure compatibility across scikit-learn versions when loading pickled HistGradientBoostingClassifier
try:
    import sklearn._loss._loss
    sys.modules['_loss'] = sklearn._loss._loss
except Exception:
    pass


def patch_estimator(estimator):
    """Bridge scikit-learn version differences for unpickled transformers."""
    if hasattr(estimator, 'transformers_'):
        for _, trans, _ in estimator.transformers_:
            patch_estimator(trans)
    if hasattr(estimator, 'named_steps'):
        for _, step in estimator.named_steps.items():
            patch_estimator(step)
    if hasattr(estimator, '_fit_dtype') and not hasattr(estimator, '_fill_dtype'):
        estimator._fill_dtype = estimator._fit_dtype


@st.cache_resource
def load_pipeline():
    pipe = joblib.load(ROOT / 'models/pipeline.joblib')
    patch_estimator(pipe)
    return pipe


def validate_input(values, m):
    if set(values) != set(m['features']):
        raise ValueError('Please complete every question.')
    for c, v in values.items():
        if v is None or (isinstance(v, (float, np.floating)) and np.isnan(v)):
            if c in m['valid_values']:
                continue
            raise ValueError('Missing answer: ' + c)
        if not isinstance(v, (int, float, np.number)) or not np.isfinite(v):
            raise ValueError('Invalid answer: ' + c)
        lo, hi = m['valid_input_ranges'][c]
        if not lo <= v <= hi:
            raise ValueError(f'{c} must be between {lo:g} and {hi:g}.')
        if c in m['valid_values'] and v not in m['valid_values'][c]:
            raise ValueError('Unsupported value: ' + c)


def predict(values):
    m = meta()
    validate_input(values, m)
    pipeline = load_pipeline()
    df = pd.DataFrame([values], columns=m['features'])
    return float(pipeline.predict_proba(df)[0, 1])
