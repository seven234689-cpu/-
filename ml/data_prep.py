"""Step 1–2: Data preparation and X/y splitting for 8-semester GPA prediction."""

import numpy as np
import pandas as pd

FEATURE_COLS = ['gpa_1', 'gender', 'fr_1', 'ns_1', 'major_id', 'gpa_1_std', 'gpa_1_min', 'weak_1']
TARGET_COLS = [f'gpa_{i}' for i in range(2, 9)]

MAJOR_ENCODE = {
    'ວິທະຍາສາດຄອມພິວເຕີ': 0,
    'ການພັດທະນາເວັບໄຊ': 1,
    'ການພັດທະນາໂປຣແກຣມຄອມພິວເຕີ': 2,
}


def encode_major(major):
    return float(MAJOR_ENCODE.get(major, -1))


def prepare_gpa_table(df, df_student=None, sem_order=None):
    """
    Build a wide table: one row per student with GPA, F-rate, and subject count
    for semesters 1–8. Keeps rows that have gpa_1 and all targets (gpa_2..gpa_8).
    """
    if sem_order is None:
        sem_order = ["1/I", "1/II", "2/I", "2/II", "3/I", "3/II", "4/I", "4/II"]

    sem_order_map = {s: i + 1 for i, s in enumerate(sem_order)}
    df2 = df.copy()

    if df_student is not None and 'gender' not in df2.columns:
        cols = ['student_code', 'gender']
        if 'major' in df_student.columns:
            cols.append('major')
        df2 = df2.merge(
            df_student[cols],
            on='student_code',
            how='left',
        )

    pr = (
        df2.groupby(['student_code', 'semester'])['grade_point']
        .mean()
        .reset_index(name='gpa')
    )
    pr['sem_idx'] = pr['semester'].map(sem_order_map)

    fr = (
        df2.groupby(['student_code', 'semester'])
        .apply(lambda x: (x['grade'] == 'F').mean(), include_groups=False)
        .reset_index(name='f_rate')
    )
    fr['sem_idx'] = fr['semester'].map(sem_order_map)

    ns = (
        df2.groupby(['student_code', 'semester'])['grade_point']
        .count()
        .reset_index(name='n_subj')
    )
    ns['sem_idx'] = ns['semester'].map(sem_order_map)

    sem1 = df2[df2['semester'].map(sem_order_map) == 1]
    sem1_stats = sem1.groupby('student_code')['grade_point'].agg(
        gpa_1_std='std', gpa_1_min='min',
    )
    sem1_stats['weak_1'] = (
        sem1.groupby('student_code')['grade_point']
        .apply(lambda x: (x <= 2.0).sum())
    )

    gender = df2.groupby('student_code')['gender'].first().map({'M': 0, 'F': 1})
    if 'major' in df2.columns:
        major_id = df2.groupby('student_code')['major'].first().map(encode_major).rename('major_id')
    else:
        major_id = pd.Series(-1.0, index=gender.index, name='major_id')

    pw = pr.pivot(index='student_code', columns='sem_idx', values='gpa').rename(
        columns={i: f'gpa_{i}' for i in range(1, 9)}
    )
    fw = fr.pivot(index='student_code', columns='sem_idx', values='f_rate').rename(
        columns={i: f'fr_{i}' for i in range(1, 9)}
    )
    nw = ns.pivot(index='student_code', columns='sem_idx', values='n_subj').rename(
        columns={i: f'ns_{i}' for i in range(1, 9)}
    )

    table = (pw.join(fw, rsuffix='_f').join(nw, rsuffix='_n')
                .join(gender).join(major_id).join(sem1_stats))
    table['gender'] = table['gender'].fillna(0)
    table['major_id'] = table['major_id'].fillna(-1.0)
    table['gpa_1_std'] = table['gpa_1_std'].fillna(0.0)
    table['gpa_1_min'] = table['gpa_1_min'].fillna(table['gpa_1'])
    table['weak_1'] = table['weak_1'].fillna(0.0)

    required = ['gpa_1'] + TARGET_COLS
    table = table.dropna(subset=[c for c in required if c in table.columns])
    table = table.reset_index()

    for col in FEATURE_COLS + TARGET_COLS:
        if col not in table.columns:
            table[col] = 0.0

    table['fr_1'] = table['fr_1'].fillna(0.0)
    table['ns_1'] = table['ns_1'].fillna(0.0)

    return table


def split_xy(gpa_table):
    """X = semester-1 features, y = GPA for semesters 2–8 (multi-output)."""
    X = gpa_table[FEATURE_COLS].astype(float).values
    y = gpa_table[TARGET_COLS].astype(float).values
    return X, y


def clip_gpa(values):
    """Clamp predictions to valid GPA range [0, 4]."""
    arr = np.asarray(values, dtype=float)
    return np.clip(arr, 0.0, 4.0)
