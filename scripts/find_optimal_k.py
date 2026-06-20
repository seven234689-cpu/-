#!/usr/bin/env python
"""Find optimal K for the GPA clustering in db.py using Elbow + Silhouette."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import db


def main():
    if len(db.df_gpa) < 4:
        print(f'❌ ข้อมูลน้อยเกินไป (มี {len(db.df_gpa)} คน) ต้องมีอย่างน้อย 4 คนเพื่อทดสอบ K=2..3')
        sys.exit(1)

    X = db.sc_fit.transform(db.df_gpa[['gpa']].values)
    max_k = min(10, len(X) - 1)

    print(f'จำนวนนักศึกษา: {len(X)}')
    print('=' * 50)
    print(f'{"K":>3} | {"Inertia":>10} | {"Silhouette":>10}')
    print('-' * 50)

    results = []
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        sil = silhouette_score(X, labels)
        results.append((k, km.inertia_, sil))
        print(f'{k:>3} | {km.inertia_:>10.4f} | {sil:>10.4f}')

    best_k = max(results, key=lambda r: r[2])
    print('=' * 50)
    print(f'✅ K ที่ดีที่สุด (Silhouette สูงสุด) = {best_k[0]} (silhouette={best_k[2]:.4f})')
    print('   ดู Inertia เทียบหา "จุดหักศอก" (elbow) ด้วยตาเพื่อยืนยันอีกที')


if __name__ == '__main__':
    main()
