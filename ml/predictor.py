"""Step 4–5: Load .pkl and predict semesters 2–8 from semester-1 input."""

import os

import numpy as np

from ml.data_prep import FEATURE_COLS, TARGET_COLS, clip_gpa, encode_major, prepare_gpa_table, split_xy
from ml.train import DEFAULT_MODEL_PATH, load_artifact, save_artifact, train_models


class GPAPredictor:
    def __init__(self, artifact_path=None):
        self.artifact_path = artifact_path or DEFAULT_MODEL_PATH
        self.artifact = None
        self.models = {}
        self.metrics = {}

    @property
    def is_ready(self):
        return bool(self.models)

    def load(self):
        self.artifact = load_artifact(self.artifact_path)
        if not self.artifact:
            return False
        self.models = self.artifact.get('models', {})
        self.metrics = self.artifact.get('metrics', {})
        return bool(self.models)

    def train_from_df(self, df, df_student=None, sem_order=None, save=True):
        table = prepare_gpa_table(df, df_student, sem_order)
        X, y = split_xy(table)
        trained = train_models(X, y)
        self.models = {name: info['model'] for name, info in trained.items()}
        self.metrics = {
            name: {'rmse': info['rmse'], 'params': info.get('params', {})}
            for name, info in trained.items()
        }
        self.artifact = {
            'feature_cols': FEATURE_COLS,
            'target_cols': TARGET_COLS,
            'models': self.models,
            'metrics': self.metrics,
            'n_students': len(table),
        }
        if save:
            save_artifact(
                trained,
                self.artifact_path,
                meta={'n_students': len(table), 'n_samples': len(X)},
            )
        return table

    def build_features(self, gpa_1, gender=0, fr_1=0.0, ns_1=0.0, major=None, major_id=None,
                        gpa_1_std=0.0, gpa_1_min=None, weak_1=0.0):
        row = {
            'gpa_1': float(gpa_1),
            'gender': float(gender),
            'fr_1': float(fr_1),
            'ns_1': float(ns_1),
            'major_id': float(major_id) if major_id is not None else encode_major(major),
            'gpa_1_std': float(gpa_1_std),
            'gpa_1_min': float(gpa_1_min) if gpa_1_min is not None else float(gpa_1),
            'weak_1': float(weak_1),
        }
        return np.array([[row[c] for c in FEATURE_COLS]], dtype=float)

    def predict_all(self, gpa_1, gender=0, fr_1=0.0, ns_1=0.0, major=None, major_id=None,
                     gpa_1_std=0.0, gpa_1_min=None, weak_1=0.0):
        """
        Predict GPA for semesters 2–8 in one shot.
        Returns {model_name: {1: gpa_1, 2: pred, ..., 8: pred}}.
        """
        if not self.is_ready:
            raise RuntimeError('Model not loaded. Call load() or train_from_df() first.')

        X = self.build_features(gpa_1, gender, fr_1, ns_1, major, major_id,
                                 gpa_1_std, gpa_1_min, weak_1)
        out = {}
        for name, model in self.models.items():
            preds = clip_gpa(model.predict(X)[0])
            known = {1: round(float(gpa_1), 3)}
            for idx, col in enumerate(TARGET_COLS, start=2):
                known[idx] = round(float(preds[idx - 2]), 3)
            out[name] = known
        return out

    def evaluate_real_scenario(self, df, df_student=None, sem_order=None):
        """Evaluate: only semester-1 input → predict semesters 2–8 vs actual."""
        table = prepare_gpa_table(df, df_student, sem_order)
        if len(table) < 5 or not self.is_ready:
            return {}

        sem_names = ['1/II', '2/I', '2/II', '3/I', '3/II', '4/I', '4/II']
        results = {i: [] for i in range(2, 9)}
        all_errors = []

        for _, row in table.iterrows():
            preds_by_model = self.predict_all(
                row['gpa_1'],
                gender=row.get('gender', 0),
                fr_1=row.get('fr_1', 0.0),
                ns_1=row.get('ns_1', 0.0),
                major_id=row.get('major_id', -1.0),
                gpa_1_std=row.get('gpa_1_std', 0.0),
                gpa_1_min=row.get('gpa_1_min', row['gpa_1']),
                weak_1=row.get('weak_1', 0.0),
            )
            best_name = min(self.metrics, key=lambda m: self.metrics[m]['rmse'])
            preds = preds_by_model[best_name]
            for sem_idx in range(2, 9):
                actual = float(row[f'gpa_{sem_idx}'])
                err = abs(preds[sem_idx] - actual)
                results[sem_idx].append(err)
                all_errors.append(err)

        out = {}
        for sem_idx, name in zip(range(2, 9), sem_names):
            errs = results[sem_idx]
            out[name] = {
                'rmse': round(float(np.sqrt(np.mean([e ** 2 for e in errs]))), 4),
                'mae': round(float(np.mean(errs)), 4),
            }
        out['ລວມ'] = {
            'rmse': round(float(np.sqrt(np.mean([e ** 2 for e in all_errors]))), 4),
            'mae': round(float(np.mean(all_errors)), 4),
        }
        out['n_students'] = len(table)
        return out


def get_or_train_predictor(df, df_student=None, sem_order=None, artifact_path=None):
    """Load .pkl if present; otherwise train from senior data and save."""
    predictor = GPAPredictor(artifact_path)
    if predictor.load():
        return predictor

    if len(df) > 10:
        predictor.train_from_df(df, df_student, sem_order, save=True)
    return predictor
