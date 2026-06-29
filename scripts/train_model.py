#!/usr/bin/env python
"""Train Multi-Output GPA models from senior data and save to models/gpa_predictor.pkl."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import db
from ml.predictor import GPAPredictor


def main():
    if len(db.df) < 10:
        print('❌ Not enough data in MySQL. Import CSV first: python scripts/import_csv.py')
        sys.exit(1)

    predictor = GPAPredictor()
    table = predictor.train_from_df(db.df, db.df_student, db.sem_order, save=True)

    print('=' * 48)
    print('✅ Training complete')
    print(f'   Students (full 8 semesters): {len(table)}')
    print(f'   Model file: {os.path.abspath(predictor.artifact_path)}')
    print('-' * 48)
    for name, metric in predictor.metrics.items():
        print(f'   {name:14} RMSE (5-Fold CV): {metric["rmse"]}')
        print(f'   {"":14} Best params: {metric["params"]}')
    print('-' * 48)
    print('   RMSE ແຍກຕາມພາກຮຽນ (1/I -> ພາກນັ້ນ):')
    per_sem = predictor.evaluate_real_scenario(db.df, db.df_student, db.sem_order)
    for sem_name, m in per_sem.items():
        if not isinstance(m, dict):
            continue
        print(f'   {sem_name:8} RMSE={m["rmse"]:.4f}  MAE={m["mae"]:.4f}')
    print('=' * 48)


if __name__ == '__main__':
    main()
