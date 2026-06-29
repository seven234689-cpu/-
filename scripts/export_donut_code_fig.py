"""Render the real fig_donut code (pages/dashboard.py) as a VS-Code-dark-style
code screenshot for the report (Figure 3.17 replacement)."""
import os

import matplotlib.pyplot as plt

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'report_figures')
os.makedirs(OUT_DIR, exist_ok=True)

BG = '#1E1E1E'
KEYWORD = '#C586C0'
FUNC = '#DCDCAA'
STRING = '#CE9178'
NUM = '#B5CEA8'
PLAIN = '#D4D4D4'
COMMENT = '#6A9955'

lines = [
    [(COMMENT, "# Donut cluster")],
    [(PLAIN, "fig_donut = "), (FUNC, "go.Figure"), (PLAIN, "("), (FUNC, "go.Pie"), (PLAIN, "(")],
    [(PLAIN, "    labels="), (PLAIN, "["), (STRING, "'ກຸ່ມ ສູງ'"), (PLAIN, ", "),
     (STRING, "'ກຸ່ມ ກາງ'"), (PLAIN, ", "), (STRING, "'ກຸ່ມ ສ່ຽງ'"), (PLAIN, "],")],
    [(PLAIN, "    values="), (PLAIN, "[db.high, db.mid, db.risk], hole="), (NUM, "0.55"), (PLAIN, ",")],
    [(PLAIN, "    marker="), (FUNC, "dict"), (PLAIN, "(colors=["), (STRING, "'#2E7D32'"), (PLAIN, ", "),
     (STRING, "'#1565C0'"), (PLAIN, ", "), (STRING, "'#C62828'"), (PLAIN, "],")],
    [(PLAIN, "                line="), (FUNC, "dict"), (PLAIN, "(color="), (STRING, "'white'"),
     (PLAIN, ", width="), (NUM, "3"), (PLAIN, ")),")],
    [(PLAIN, "    textposition="), (STRING, "'inside'"), (PLAIN, ",")],
    [(PLAIN, "    hovertemplate="), (STRING, "'<b>%{label}</b><br>%{value} ຄົນ<br>%{percent}<extra></extra>'")],
    [(PLAIN, "))")],
]

fig, ax = plt.subplots(figsize=(9, 3.6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.axis('off')

def has_lao(s):
    return any('຀' <= ch <= '໿' for ch in s)

fig.canvas.draw()
renderer = fig.canvas.get_renderer()

y = 0.95
for line in lines:
    x = 0.02
    for color, text in line:
        font = 'Phetsarath OT' if has_lao(text) else 'Consolas'
        t = ax.text(x, y, text, transform=ax.transAxes, fontsize=11, family=font,
                     va='top', ha='left', color=color)
        bbox = t.get_window_extent(renderer=renderer)
        bbox_axes = bbox.transformed(ax.transAxes.inverted())
        x += (bbox_axes.x1 - bbox_axes.x0)
    y -= 0.105

plt.tight_layout()
path = os.path.join(OUT_DIR, 'code_donut_chart.png')
plt.savefig(path, dpi=150, facecolor=BG)
plt.close(fig)
print(f'Saved {path}')
