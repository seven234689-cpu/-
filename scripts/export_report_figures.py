#!/usr/bin/env python
"""Export dashboard analysis charts as high-res PNG for use in the thesis/report."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pages.dashboard as dash_page

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'report_figures')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d')

    figures = {
        f'heatmap_subject_semester_{stamp}.png': dash_page.fig_heat,
        f'correlation_matrix_{stamp}.png': dash_page.fig_corr,
        f'grade_distribution_{stamp}.png': dash_page.fig_grade,
        f'cluster_donut_{stamp}.png': dash_page.fig_donut,
    }

    for filename, fig in figures.items():
        path = os.path.join(OUT_DIR, filename)
        fig.write_image(path, scale=3)
        print(f'✅ {filename}')

    print('=' * 48)
    print(f'บันทึกแล้วที่: {os.path.abspath(OUT_DIR)}')


if __name__ == '__main__':
    main()
