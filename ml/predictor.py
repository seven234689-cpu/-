"""Step 4–5: Load .pkl and predict the remaining semesters from whatever
semesters are already known (1..7), instead of always forecasting from
semester 1 alone."""

import numpy as np
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold

from ml.data_prep import (
    clip_gpa, encode_major, prepare_gpa_table, split_xy_stage, stage_feature_cols,
)
from ml.train import (
    DEFAULT_MODEL_PATH, _make_random_forest, _make_xgboost,
    load_artifact, save_artifact, train_all_stages,
)

_MODEL_FACTORIES = {'RandomForest': _make_random_forest, 'XGBoost': _make_xgboost}
MAX_KNOWN = 7


class GPAPredictor:
    def __init__(self, artifact_path=None):
        self.artifact_path = artifact_path or DEFAULT_MODEL_PATH
        self.artifact = None
        self.stages = {}

    @property
    def is_ready(self):
        return bool(self.stages)

    @property
    def metrics(self):
        """RMSE/params of the stage-1 (semester-1-only) models — used for the
        summary table on the predict page."""
        return self.stages.get(1, {}).get('metrics', {})

    def load(self):
        self.artifact = load_artifact(self.artifact_path)
        if not self.artifact:
            return False
        self.stages = self.artifact.get('stages', {})
        return bool(self.stages)

    def train_from_df(self, df, df_student=None, sem_order=None, save=True):
        table = prepare_gpa_table(df, df_student, sem_order)
        self.stages = train_all_stages(table, max_known=MAX_KNOWN)
        self.artifact = {'stages': self.stages, 'n_students': len(table)}
        if save:
            save_artifact(self.stages, self.artifact_path, meta={'n_students': len(table)})
        return table

    def build_features(self, known_gpas, gender=0, fr_1=0.0, ns_1=0.0, major=None, major_id=None):
        """known_gpas: list of GPA values for semesters 1..k (contiguous, k = len(list))."""
        k = len(known_gpas)
        if not (1 <= k <= MAX_KNOWN):
            raise ValueError(f'known_gpas must have 1..{MAX_KNOWN} values, got {k}')

        arr = np.array(known_gpas, dtype=float)
        row = {f'gpa_{i+1}': v for i, v in enumerate(arr)}
        row.update({
            'gender': float(gender),
            'major_id': float(major_id) if major_id is not None else encode_major(major),
            'fr_1': float(fr_1),
            'ns_1': float(ns_1),
            'gpa_known_std': float(np.std(arr)) if k > 1 else 0.0,
            'gpa_known_min': float(np.min(arr)),
            'weak_known': float(np.sum(arr <= 2.0)),
            'fr_known': float(fr_1),  # approximation: only semester-1 fail rate is collected from the UI today
        })
        cols = stage_feature_cols(k)
        return np.array([[row[c] for c in cols]], dtype=float), k

    def predict_from_known(self, known_gpas, gender=0, fr_1=0.0, ns_1=0.0, major=None, major_id=None):
        """
        Predict GPA for whichever semesters come after the known ones.
        known_gpas: list of GPA for semesters 1..k (k = len(known_gpas)).
        Returns {model_name: {1: known[0], ..., k: known[k-1], k+1: pred, ..., 8: pred}}.
        """
        if not self.is_ready:
            raise RuntimeError('Model not loaded. Call load() or train_from_df() first.')

        X, k = self.build_features(known_gpas, gender, fr_1, ns_1, major, major_id)
        stage = self.stages.get(k)
        if not stage:
            raise ValueError(f'No trained model for known={k} semesters')

        out = {}
        for name, model in stage['models'].items():
            preds = np.atleast_1d(clip_gpa(model.predict(X)[0]))
            known = {i + 1: round(float(v), 3) for i, v in enumerate(known_gpas)}
            for idx, _col in enumerate(stage['target_cols'], start=k + 1):
                known[idx] = round(float(preds[idx - k - 1]), 3)
            out[name] = known
        return out

    def predict_all(self, gpa_1, gender=0, fr_1=0.0, ns_1=0.0, major=None, major_id=None, **_ignored):
        """Backwards-compatible shortcut: predict from semester 1 only."""
        return self.predict_from_known([gpa_1], gender, fr_1, ns_1, major, major_id)

    def evaluate_real_scenario(self, df, df_student=None, sem_order=None, n_splits=5):
        """
        Honest held-out evaluation of the semester-1-only stage (k=1): K-Fold CV
        where each row is scored only by a model that never saw that row during
        training (unlike a plain fit-then-score-on-the-same-data pass, which
        looks better than the model really is).
        """
        table = prepare_gpa_table(df, df_student, sem_order)
        if len(table) < n_splits * 2 or not self.is_ready:
            return {}

        X, y, _feature_cols, _target_cols = split_xy_stage(table, k=1)

        stage1_metrics = self.stages.get(1, {}).get('metrics', {})
        candidates = [name for name in stage1_metrics if name in _MODEL_FACTORIES]
        if not candidates:
            return {}

        sem_names = ['1/II', '2/I', '2/II', '3/I', '3/II', '4/I', '4/II']
        per_model_actual = {name: {i: [] for i in range(2, 9)} for name in candidates}
        per_model_pred = {name: {i: [] for i in range(2, 9)} for name in candidates}

        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        for train_idx, test_idx in kf.split(X):
            for name in candidates:
                params = stage1_metrics.get(name, {}).get('params', {})
                model = _MODEL_FACTORIES[name](**params)
                if model is None:
                    continue
                model.fit(X[train_idx], y[train_idx])
                preds = clip_gpa(model.predict(X[test_idx]))
                actual = y[test_idx]
                for col_idx, sem_idx in enumerate(range(2, 9)):
                    per_model_actual[name][sem_idx].extend(actual[:, col_idx].tolist())
                    per_model_pred[name][sem_idx].extend(preds[:, col_idx].tolist())

        def overall_rmse(name):
            errs = [
                abs(a - p)
                for sem in per_model_actual[name]
                for a, p in zip(per_model_actual[name][sem], per_model_pred[name][sem])
            ]
            return float(np.sqrt(np.mean([e ** 2 for e in errs])))

        best_name = min(candidates, key=overall_rmse)
        actual_by_sem = per_model_actual[best_name]
        pred_by_sem = per_model_pred[best_name]
        all_actual = [v for sem in actual_by_sem.values() for v in sem]
        all_pred = [v for sem in pred_by_sem.values() for v in sem]

        out = {}
        for sem_idx, name in zip(range(2, 9), sem_names):
            actual_vals = np.array(actual_by_sem[sem_idx])
            pred_vals = np.array(pred_by_sem[sem_idx])
            errs = np.abs(pred_vals - actual_vals)
            out[name] = {
                'rmse': round(float(np.sqrt(np.mean(errs ** 2))), 4),
                'mae': round(float(np.mean(errs)), 4),
                'r2': round(float(r2_score(actual_vals, pred_vals)), 4),
            }
        all_actual_arr = np.array(all_actual)
        all_pred_arr = np.array(all_pred)
        all_errors = np.abs(all_pred_arr - all_actual_arr)
        out['ລວມ'] = {
            'rmse': round(float(np.sqrt(np.mean(all_errors ** 2))), 4),
            'mae': round(float(np.mean(all_errors)), 4),
            'r2': round(float(r2_score(all_actual_arr, all_pred_arr)), 4),
        }
        out['n_students'] = len(table)
        out['best_model'] = best_name
        return out


def get_or_train_predictor(df, df_student=None, sem_order=None, artifact_path=None):
    """Load .pkl if present; otherwise train from senior data and save."""
    predictor = GPAPredictor(artifact_path)
    if predictor.load():
        return predictor

    if len(df) > 10:
        predictor.train_from_df(df, df_student, sem_order, save=True)
    return predictor
