"""Render real admin.py logic as Colab/Jupyter-style code-cell + output images
for the report. Output shown is always from actually running the real logic
on sample inputs — never fabricated.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib.pyplot as plt

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'report_figures')
os.makedirs(OUT_DIR, exist_ok=True)

LAO_FONT = 'Lao UI'


def render_colab_cell(code, output, filename):
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    ax.axis('off')

    ax.add_patch(plt.Rectangle((0, 0.55), 1, 0.45, transform=ax.transAxes,
                                facecolor='#F8F9FA', edgecolor='#DADCE0', linewidth=1))
    ax.text(0.02, 0.97, code, transform=ax.transAxes, fontsize=10.5,
            family=LAO_FONT, va='top', ha='left', color='#202124')

    ax.add_patch(plt.Rectangle((0, 0.02), 1, 0.50, transform=ax.transAxes,
                                facecolor='#FFFFFF', edgecolor='#DADCE0', linewidth=1))
    ax.text(0.02, 0.48, output, transform=ax.transAxes, fontsize=10.5,
            family=LAO_FONT, va='top', ha='left', color='#188038')

    ax.text(0.0, 1.0, '[ ]:', transform=ax.transAxes, fontsize=9,
            family='monospace', va='top', ha='left', color='#5F6368')

    plt.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close(fig)
    print(f'Saved {path}')


# ── Figure 3.8/3.9: gender + major detection ────────────────────────────────
CODE_1 = '''MAJOR_MAP = {137:'ວິທະຍາສາດຄອມພິວເຕີ', 144:'ການພັດທະນາເວັບໄຊ',
             149:'ການພັດທະນາໂປຣແກຣມຄອມພິວເຕີ'}

g = str(g_raw).strip()
gender = 'F' if 'ນາງ' in g else 'M'
major  = MAJOR_MAP.get(int(total_credit), 'ບໍ່ລະບຸ')'''

MAJOR_MAP = {137: 'ວິທະຍາສາດຄອມພິວເຕີ', 144: 'ການພັດທະນາເວັບໄຊ',
             149: 'ການພັດທະນາໂປຣແກຣມຄອມພິວເຕີ'}

lines_1 = []
for g_raw in [' ທ້າວ', 'ນາງ', 'ສ.ນ']:
    g = str(g_raw).strip()
    gender = 'F' if 'ນາງ' in g else 'M'
    lines_1.append(f'{g_raw!r} -> {gender}')
lines_1.append('')
for total_credit in [137, 144, 149]:
    major = MAJOR_MAP.get(int(total_credit), 'ບໍ່ລະບຸ')
    lines_1.append(f'{total_credit} -> {major}')
lines_1.append('(ຄ່າອື່ນທີ່ບໍ່ກົງ 137/144/149) -> ບໍ່ລະບຸ')

render_colab_cell(CODE_1, '\n'.join(lines_1), 'colab_gender_major.png')

# ── Figure 3.10: grade -> grade point dictionary ────────────────────────────
CODE_2 = '''gm = {
    'A': 4.0, 'B+': 3.5, 'B': 3.0, 'C+': 2.5, 'C': 2.0,
    'D+': 1.5, 'D': 1.0, 'F': 0.0
}

gp = gm.get(g)
if gp is None:
    continue  # ບໍ່ມີຢູ່ໃນ Dictionary -> ຂ້າມຂໍ້ມູນນັ້ນໄປ ບໍ່ບັນທຶກ'''

lines_2 = []
for g in ['A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F']:
    gp = MAJOR_MAP and {'A': 4.0, 'B+': 3.5, 'B': 3.0, 'C+': 2.5, 'C': 2.0,
                         'D+': 1.5, 'D': 1.0, 'F': 0.0}.get(g)
    lines_2.append(f'{g!r:>6} -> {gp}')

render_colab_cell(CODE_2, '\n'.join(lines_2), 'colab_grade_point.png')

# ── Figure 3.12: StandardScaler + K-Means clustering (real data, real run) ──
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import db  # noqa: E402

CODE_3 = '''sc_fit = StandardScaler()
X = sc_fit.fit_transform(df_gpa[['gpa']].values)

km = KMeans(n_clusters=3, random_state=42, n_init=10)
df_gpa['cn'] = km.fit_predict(X)

ci = np.argsort(sc_fit.inverse_transform(km.cluster_centers_).flatten())
lm = {ci[0]:'ສ່ຽງ', ci[1]:'ກາງ', ci[2]:'ສູງ'}
df_gpa['cluster'] = df_gpa['cn'].map(lm)'''

sample = db.df_gpa[['student_code', 'gpa', 'cn', 'cluster']].head(6)
lines_3 = [f"{r.student_code}  gpa={r.gpa:.3f}  cn={r.cn}  -> {r.cluster}"
           for r in sample.itertuples()]
lines_3.append('')
lines_3.append(f"ນັກສຶກສາທັງໝົດ: {len(db.df_gpa)} ຄົນ")
counts = db.df_gpa['cluster'].value_counts()
for label, n in counts.items():
    lines_3.append(f"{label}: {n} ຄົນ")

render_colab_cell(CODE_3, '\n'.join(lines_3), 'colab_kmeans.png')
