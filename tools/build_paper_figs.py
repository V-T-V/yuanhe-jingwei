# -*- coding: utf-8 -*-
"""元和经纬 · 论文插图生成：python tools/build_paper_figs.py

数据源（口径纪律）：data/stats.json（tools/stats.py 产物）——凡数字出自脚本。
输出：docs/figs/fig1_dao.png · fig2_lost.png · fig3_zhen.png（200dpi 麻纸石青，学 HHH docs/build_paper_figs.py）
build_paper_pdf.py 于插图缺失时自动调用本脚本（管线可重入）。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "figs")
os.makedirs(OUT, exist_ok=True)

STATS = json.load(open(os.path.join(ROOT, "data", "stats.json"), encoding="utf-8"))

# ── 麻纸石青版式（沿站点 CSS 与 PDF 配色） ──
SILK, INK, MUTED = "#efeada", "#2d2820", "#8a7f68"
TEAL, CINNABAR, GRIDC = "#2f5d70", "#8c2c1c", "#ded6bd"
plt.rcParams.update({
    "font.family": "Microsoft YaHei", "axes.unicode_minus": False,
    "figure.facecolor": SILK, "axes.facecolor": SILK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
})
KAI = FontProperties(fname=r"C:\Windows\Fonts\simkai.ttf", size=14)


def frame(ax, axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis=axis, color=GRIDC, lw=.7, alpha=.8)
    ax.set_axisbelow(True)


DAOS = ["关内道", "河南道", "河东道", "河北道", "山南道", "淮南道", "江南道", "剑南道", "岭南道", "陇右道"]

# ══ 图 1　十道州府数与县名录数：淮南整道佚 ══
per = STATS["per_dao"]                                    # stats.json:per_dao
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
frame(ax)
xs = range(len(DAOS))
states = [per[d]["states"] for d in DAOS]
xian = [per[d]["xian"] for d in DAOS]
b1 = ax.bar([x - .19 for x in xs], states, width=.38, color=TEAL, label="州府数", edgecolor=SILK, lw=.5)
b2 = ax.bar([x + .19 for x in xs], xian, width=.38, color=MUTED, label="县名录数", edgecolor=SILK, lw=.5)
for x, v in zip(xs, states):
    ax.text(x - .19, v + 3, str(v), ha="center", fontsize=8, color=INK)
for x, v in zip(xs, xian):
    ax.text(x + .19, v + 3, str(v), ha="center", fontsize=8, color=INK)
ax.annotate("淮南整道佚", xy=(5, 2), xytext=(5.5, 70), fontsize=9, color=CINNABAR,
            arrowprops=dict(arrowstyle="->", color=CINNABAR, lw=1.1))
ax.set_xticks(list(xs))
ax.set_xticklabels(DAOS, fontsize=9)
ax.set_ylabel("条目数", fontsize=9.5)
ax.set_ylim(0, max(xian) * 1.18)
ax.legend(fontsize=9, frameon=False, loc="upper right")
ax.set_title("十道州府数与县名录数（州 227 · 县 1,081）", fontproperties=KAI, pad=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_dao.png"))
plt.close(fig)

# ══ 图 2　卷佚 31 州份的道级分布 ══
lost = sorted([(d, per[d]["lost"]) for d in DAOS if per[d]["lost"] > 0],
              key=lambda kv: -kv[1])                      # stats.json:per_dao[].lost
fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
frame(ax)
names = [k for k, _ in lost]
vals = [v for _, v in lost]
ax.bar(names, vals, color=CINNABAR, width=.52, edgecolor=SILK, lw=.5)
for i, v in enumerate(vals):
    ax.text(i, v + .3, str(v), ha="center", fontsize=9, color=INK)
ax.set_ylabel("卷佚州份数", fontsize=9.5)
ax.set_ylim(0, max(vals) * 1.22)
ax.set_title(f"卷佚 {sum(vals)} 州份的道级分布——剑南残帙与淮南全佚", fontproperties=KAI, pad=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_lost.png"))
plt.close(fig)

# ══ 图 3　镇属规模 TOP12：陇右残帙一镇独大 ══
zm = sorted(STATS["zhen_members"].items(), key=lambda kv: -kv[1])   # stats.json:zhen_members
fig, ax = plt.subplots(figsize=(7.2, 4.8), dpi=200)
frame(ax)
names = [k for k, _ in zm][::-1]
vals = [v for _, v in zm][::-1]
cols = [CINNABAR if n.startswith("陇右") else TEAL for n in names]
ax.barh(names, vals, color=cols, height=.64, edgecolor=SILK, lw=.5)
for i, v in enumerate(vals):
    ax.text(v + .2, i, str(v), va="center", fontsize=8.5, color=INK)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("领州数", fontsize=9.5)
ax.set_xlim(0, max(vals) * 1.12)
ax.set_title("镇属规模 TOP12——陇右诸州（陷蕃残帙）21 州独大", fontproperties=KAI, pad=12)
ax.legend(handles=[Patch(fc=CINNABAR, label="陇右诸州（陷蕃，卷 39/40 残帙）"),
                   Patch(fc=TEAL, label="中原及南方诸镇")],
          loc="lower right", fontsize=8.5, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_zhen.png"))
plt.close(fig)

print("OK →", OUT, sorted(os.listdir(OUT)))
