"""Real K-Means clustering result (GPA -> risk group) as a 1D scatter/trend
chart for the report, using the project's actual db.df_gpa data."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib.pyplot as plt
import numpy as np

import db

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'report_figures')
os.makedirs(OUT_DIR, exist_ok=True)

df = db.df_gpa
CC = {'ສູງ': '#2E7D32', 'ກາງ': '#1565C0', 'ສ່ຽງ': '#C62828'}

plt.rcParams['font.family'] = 'Phetsarath OT'

fig, ax = plt.subplots(figsize=(9, 4.5))

rng = np.random.default_rng(42)
for label, color in CC.items():
    sub = df[df['cluster'] == label]
    jitter = rng.uniform(-0.4, 0.4, size=len(sub))
    ax.scatter(sub['gpa'], jitter, s=14, alpha=0.6, color=color, label=f'{label} (n={len(sub)})')

centers = db.df_gpa.groupby('cluster')['gpa'].mean()
for label, gpa in centers.items():
    ax.axvline(gpa, color=CC[label], linestyle='--', linewidth=1, alpha=0.7)

ax.set_yticks([])
ax.set_xlabel('GPA ສະເລ່ຍ')
ax.set_xlim(0, 4)
ax.set_title('ການແຈກຢາຍ GPA ຂອງນັກສຶກສາຕາມກຸ່ມທີ່ໄດ້ຈາກ K-Means (n=%d)' % len(df))
ax.legend(loc='upper left', fontsize=9)
ax.grid(True, axis='x', linestyle='--', alpha=0.3)

plt.tight_layout()
path = os.path.join(OUT_DIR, 'kmeans_trend.png')
plt.savefig(path, dpi=150)
plt.close(fig)
print(f'Saved {path}')
for label, gpa in centers.items():
    print(f'  {label}: mean GPA = {gpa:.3f}, n = {(df["cluster"]==label).sum()}')
