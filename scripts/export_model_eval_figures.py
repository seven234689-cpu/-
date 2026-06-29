"""Generate real Actual-vs-Predicted scatter plots + Feature Importance charts
for Chapter 4 of the report, using the project's actual trained models
(RandomForest, XGBoost) and actual data — no senior's numbers, no fake data.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold

import db
from ml.data_prep import prepare_gpa_table, split_xy_stage, clip_gpa
from ml.predictor import get_or_train_predictor, _MODEL_FACTORIES

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'report_figures')
os.makedirs(OUT_DIR, exist_ok=True)

table = prepare_gpa_table(db.df, db.df_student, db.sem_order)
X, y, feature_cols, target_cols = split_xy_stage(table, k=1)

predictor = get_or_train_predictor(db.df, db.df_student, db.sem_order)
stage1_metrics = predictor.stages[1]['metrics']

kf = KFold(n_splits=5, shuffle=True, random_state=42)


def pooled_predictions(name):
    params = stage1_metrics[name]['params']
    all_a, all_p = [], []
    for tr, te in kf.split(X):
        m = _MODEL_FACTORIES[name](**params)
        m.fit(X[tr], y[tr])
        pred = clip_gpa(m.predict(X[te]))
        all_a.append(y[te])
        all_p.append(pred)
    return np.concatenate(all_a, axis=0), np.concatenate(all_p, axis=0)


def scatter_plot(actual, pred, filename, title):
    a = actual.ravel()
    p = pred.ravel()
    rmse = float(np.sqrt(np.mean((p - a) ** 2)))
    mae = float(np.mean(np.abs(p - a)))
    ss_res = np.sum((a - p) ** 2)
    ss_tot = np.sum((a - np.mean(a)) ** 2)
    r2 = 1 - ss_res / ss_tot

    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    sc = ax.scatter(a, p, c=a, cmap='viridis', alpha=0.65, s=20,
                     edgecolors='white', linewidths=0.3, vmin=0, vmax=4)
    ax.plot([0, 4], [0, 4], color='#E07A5F', linestyle='--', linewidth=1.8,
            label='ເສັ້ນທຳນາຍສົມບູນແບບ\n(Perfect Prediction)')

    stats_text = (f'ລວມທຸກພາກ:\nRMSE = {rmse:.4f}\nMAE = {mae:.4f}\n$R^2$ = {r2:.4f}')
    ax.text(0.06, 0.94, stats_text, transform=ax.transAxes,
            fontsize=10, va='top', ha='left', family='Phetsarath OT',
            bbox=dict(boxstyle='round', facecolor='white', edgecolor='#CCCCCC', alpha=0.92))

    ax.set_xlabel('Actual GPA')
    ax.set_ylabel('Predicted GPA')
    ax.set_xlim(0, 4)
    ax.set_ylim(0, 4)
    ax.grid(True, linestyle='--', alpha=0.3, color='#CCCCCC')
    ax.set_facecolor('#FAFAFA')
    ax.legend(loc='lower right', fontsize=9)
    cbar = plt.colorbar(sc, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_label('Actual GPA', fontsize=9)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close(fig)
    print(f'Saved {path}  (RMSE={rmse:.4f} MAE={mae:.4f} R2={r2:.4f})')


FEATURE_LABELS_LAO = {
    'fr_known': 'ອັດຕາສອບເສຍສະເລ່ຍ (ທຸກພາກທີ່ຮູ້)',
    'fr_1': 'ອັດຕາສອບເສຍ ພາກ 1/I',
    'gpa_1': 'GPA ພາກ 1/I',
    'gpa_known_min': 'GPA ຕ່ຳສຸດທີ່ຮູ້',
    'gpa_known_std': 'ສ່ວນບ່ຽງເບນ GPA ທີ່ຮູ້',
    'major_id': 'ສາຂາ',
    'gender': 'ເພດ',
    'weak_known': 'ຈຳນວນພາກທີ່ອ່ອນ (GPA≤2.0)',
    'ns_1': 'ຈຳນວນວິຊາ ພາກ 1/I',
}


def feature_importance_plot(model, filename, title):
    if not hasattr(model, 'feature_importances_'):
        print(f'no feature_importances_, skipping {filename}')
        return
    importances = model.feature_importances_
    order = np.argsort(importances)[::-1]
    labels = [FEATURE_LABELS_LAO.get(feature_cols[i], feature_cols[i]) for i in order]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(labels[::-1], importances[order][::-1], color='steelblue')
    ax.set_xlabel('Importance')
    ax.set_title(title)
    plt.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close(fig)
    print(f'Saved {path}')
    for i in order:
        print(f'  {feature_cols[i]:20s} {importances[i]:.4f}')


for name, fig_label in [('RandomForest', 'rf'), ('XGBoost', 'xgb')]:
    actual, pred = pooled_predictions(name)
    scatter_plot(actual, pred, f'scatter_{fig_label}.png',
                 f'GPA ຈິງ ແລະ GPA ທີ່ພະຍາກອນ — {name} (ທຸກພາກ, k=1)')

    params = stage1_metrics[name]['params']
    final_model = _MODEL_FACTORIES[name](**params)
    final_model.fit(X, y)
    feature_importance_plot(final_model, f'feat_importance_{fig_label}.png',
                             f'ຄວາມສຳຄັນຂອງ Feature — {name}')

print('Done.')
