"""Nested Cross-Validation — honest evaluation with zero hyperparameter leakage.

Unlike evaluate_real_scenario() (which reuses hyperparameters tuned once on the
full 559-student dataset), this script re-runs GridSearchCV INSIDE each outer
fold using only that fold's training data, so the reported RMSE/MAE/R2 cannot
be inflated by hyperparameter choices that "saw" the test rows in advance.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import r2_score

import db
from ml.data_prep import prepare_gpa_table, split_xy_stage, clip_gpa
from ml.train import (
    RF_PARAM_GRID, XGB_PARAM_GRID, _make_random_forest, _make_xgboost,
)

FACTORIES = {'RandomForest': _make_random_forest, 'XGBoost': _make_xgboost}
GRIDS = {'RandomForest': RF_PARAM_GRID, 'XGBoost': XGB_PARAM_GRID}
SEM_NAMES = ['1/II', '2/I', '2/II', '3/I', '3/II', '4/I', '4/II']


def nested_cv(X, y, n_splits=5, inner_splits=3):
    outer = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    per_model_actual = {n: [] for n in FACTORIES}
    per_model_pred = {n: [] for n in FACTORIES}

    for fold_i, (tr, te) in enumerate(outer.split(X), start=1):
        for name, factory in FACTORIES.items():
            search = GridSearchCV(
                factory(), GRIDS[name],
                cv=KFold(n_splits=inner_splits, shuffle=True, random_state=42),
                scoring='neg_root_mean_squared_error', n_jobs=1,
            )
            search.fit(X[tr], y[tr])
            best = factory(**search.best_params_)
            best.fit(X[tr], y[tr])
            pred = clip_gpa(best.predict(X[te]))
            per_model_actual[name].append(y[te])
            per_model_pred[name].append(pred)
        print(f'  fold {fold_i}/{n_splits} done', flush=True)

    results = {}
    for name in FACTORIES:
        actual = np.concatenate(per_model_actual[name], axis=0)
        pred = np.concatenate(per_model_pred[name], axis=0)
        rmse = float(np.sqrt(np.mean((pred - actual) ** 2)))
        results[name] = {'actual': actual, 'pred': pred, 'rmse_overall': rmse}
    return results


def main():
    table = prepare_gpa_table(db.df, db.df_student, db.sem_order)
    X, y, _f, _t = split_xy_stage(table, k=1)
    print(f'n_students = {len(table)}')
    print('Running nested CV (GridSearchCV inside each outer fold)...')

    results = nested_cv(X, y)

    best_name = min(results, key=lambda n: results[n]['rmse_overall'])
    print(f'\nOverall RMSE by model: ' +
          ', '.join(f'{n}={results[n]["rmse_overall"]:.4f}' for n in results))
    print(f'Best model (honest, nested CV): {best_name}\n')

    actual = results[best_name]['actual']
    pred = results[best_name]['pred']

    print(f'{"ພາກ":<8}{"RMSE":<10}{"MAE":<10}{"R2":<10}')
    all_a, all_p = [], []
    for col_idx, sem in enumerate(SEM_NAMES):
        a = actual[:, col_idx]
        p = pred[:, col_idx]
        all_a.append(a); all_p.append(p)
        rmse = float(np.sqrt(np.mean((p - a) ** 2)))
        mae = float(np.mean(np.abs(p - a)))
        r2 = float(r2_score(a, p))
        print(f'{sem:<8}{rmse:<10.4f}{mae:<10.4f}{r2:<10.4f}')

    all_a = np.concatenate(all_a)
    all_p = np.concatenate(all_p)
    rmse = float(np.sqrt(np.mean((all_p - all_a) ** 2)))
    mae = float(np.mean(np.abs(all_p - all_a)))
    r2 = float(r2_score(all_a, all_p))
    print(f'{"ລวม":<8}{rmse:<10.4f}{mae:<10.4f}{r2:<10.4f}')


if __name__ == '__main__':
    main()
