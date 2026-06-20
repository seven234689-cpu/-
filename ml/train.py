"""Step 3: Multi-Output model training (Random Forest + XGBoost) and .pkl persistence."""

import os
from datetime import datetime, timezone

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.multioutput import MultiOutputRegressor

from ml.data_prep import FEATURE_COLS, TARGET_COLS, clip_gpa

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'models', 'gpa_predictor.pkl'
)


RF_PARAM_GRID = {
    'estimator__n_estimators': [100, 200],
    'estimator__max_depth': [6, 12, None],
    'estimator__min_samples_leaf': [1, 3, 5],
}

XGB_PARAM_GRID = {
    'estimator__n_estimators': [100, 200],
    'estimator__max_depth': [3, 6],
    'estimator__learning_rate': [0.05, 0.08, 0.15],
}


def _make_random_forest(**params):
    base = dict(random_state=42, n_jobs=1)
    base.update(params)
    return MultiOutputRegressor(RandomForestRegressor(**base), n_jobs=1)


def _make_xgboost(**params):
    try:
        from xgboost import XGBRegressor
    except ImportError:
        return None

    base = dict(
        random_state=42, n_jobs=1, objective='reg:squarederror',
        subsample=0.9, colsample_bytree=0.9,
    )
    base.update(params)
    return MultiOutputRegressor(XGBRegressor(**base), n_jobs=1)


def _tune(factory, param_grid, X, y, n_splits=3):
    """Grid-search hyperparameters, return the best raw params dict."""
    model = factory()
    if model is None:
        return None
    search = GridSearchCV(
        model, param_grid, cv=KFold(n_splits=n_splits, shuffle=True, random_state=42),
        scoring='neg_root_mean_squared_error', n_jobs=1,
    )
    search.fit(X, y)
    return {k.replace('estimator__', ''): v for k, v in search.best_params_.items()}


def _cross_val_rmse(model_factory, X, y, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    rmses = []
    for train_idx, test_idx in kf.split(X):
        model = model_factory()
        model.fit(X[train_idx], y[train_idx])
        pred = clip_gpa(model.predict(X[test_idx]))
        rmse = float(np.sqrt(mean_squared_error(y[test_idx], pred)))
        rmses.append(rmse)
    return round(float(np.mean(rmses)), 4)


def train_models(X, y):
    """Train all configured models and return {name: {model, rmse}}."""
    if len(X) < 10:
        raise ValueError(f'Need at least 10 students with full 8 semesters, got {len(X)}')

    trained = {}

    rf_params = _tune(_make_random_forest, RF_PARAM_GRID, X, y) or {}
    rf_factory = lambda: _make_random_forest(**rf_params)
    rf_rmse = _cross_val_rmse(rf_factory, X, y)
    rf_model = rf_factory()
    rf_model.fit(X, y)
    trained['RandomForest'] = {'model': rf_model, 'rmse': rf_rmse, 'params': rf_params}

    if _make_xgboost() is not None:
        xgb_params = _tune(_make_xgboost, XGB_PARAM_GRID, X, y) or {}
        xgb_factory = lambda: _make_xgboost(**xgb_params)
        xgb_rmse = _cross_val_rmse(xgb_factory, X, y)
        xgb_model = xgb_factory()
        xgb_model.fit(X, y)
        trained['XGBoost'] = {'model': xgb_model, 'rmse': xgb_rmse, 'params': xgb_params}

    return trained


def save_artifact(trained, path=None, meta=None):
    path = path or DEFAULT_MODEL_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    payload = {
        'version': 1,
        'trained_at': datetime.now(timezone.utc).isoformat(),
        'feature_cols': FEATURE_COLS,
        'target_cols': TARGET_COLS,
        'models': {name: info['model'] for name, info in trained.items()},
        'metrics': {
            name: {'rmse': info['rmse'], 'params': info.get('params', {})}
            for name, info in trained.items()
        },
        'meta': meta or {},
    }
    joblib.dump(payload, path)
    return path


def load_artifact(path=None):
    path = path or DEFAULT_MODEL_PATH
    if not os.path.exists(path):
        return None
    return joblib.load(path)
