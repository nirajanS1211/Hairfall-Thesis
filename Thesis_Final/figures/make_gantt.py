"""Draws the Gantt chart for Section 4.2. Run: python make_gantt.py
Months 1 and 2 = proposal work (black), months 3 and 4 = final work (hatched)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]

MONTHS = 4
PRE = 0.0  # no extra column: months 1 and 2 are the proposal work, months 3 and 4 the final work

done_tasks = [
    ("Problem formulation", 0.0, 1.0),
    ("Literature review", 0.4, 1.8),
    ("Dataset study", 0.8, 1.8),
    ("Proposal documentation", 1.0, 2.0),
]
plan_tasks = [
    ("Data preprocessing and split", 2.0, 2.4),
    ("CatBoost tuning and training", 2.2, 2.8),
    ("TabPFN and TabFM (Kaggle)", 2.5, 3.3),
    ("Training-size experiment", 2.8, 3.4),
    ("SHAP explanations", 3.0, 3.6),
    ("Metrics and McNemar test", 3.4, 3.8),
    ("Results and discussion", 3.5, 4.0),
    ("Thesis writing and defence", 3.2, 4.0),
]
rows = [("done",) + t for t in done_tasks] + [("plan",) + t for t in plan_tasks]
n = len(rows)
gap = 0.6
ypos, y = [], 0
for i, r in enumerate(rows):
    if i == len(done_tasks):
        y += gap
    ypos.append(y); y += 1
total_h = y

fig, ax = plt.subplots(figsize=(7.0, 6.0))
ylab = []
for k, ((kind, name, s, e), yy) in enumerate(zip(rows, ypos)):
    yc = total_h - yy - 0.5
    if kind == "done":
        ax.add_patch(Rectangle((s, yc - 0.3), e - s, 0.6, fc="black", ec="black"))
    else:
        ax.add_patch(Rectangle((s, yc - 0.3), e - s, 0.6, fc="white", ec="black", hatch="////", lw=1.2))
    ylab.append((yc, f"{k + 1}. {name}"))
ax.set_yticks([a for a, _ in ylab]); ax.set_yticklabels([b for _, b in ylab], fontsize=12.5)
ax.set_xlim(-PRE, MONTHS); ax.set_ylim(0, total_h + 0.3)
ax.set_xticks([i + 0.5 for i in range(MONTHS)])
ax.set_xticklabels([f"Month {i + 1}" for i in range(MONTHS)], fontsize=12.5)
ax.xaxis.tick_top()
for x in range(MONTHS + 1):
    ax.axvline(x, color="#999999", lw=0.8)
for a, _ in ylab:
    ax.axhline(a - 0.5, color="#dddddd", lw=0.6)
ax.axvline(2, color="black", lw=1.6, ls="--")
for spine in ("right", "bottom"):
    ax.spines[spine].set_visible(False)
ax.tick_params(length=0)
lx = 0.1
ax.add_patch(Rectangle((lx, -1.15), 0.3, 0.4, fc="black", ec="black", clip_on=False))
ax.text(lx + 0.4, -0.95, "Proposal work", fontsize=11.5, va="center")
ax.add_patch(Rectangle((lx + 1.6, -1.15), 0.3, 0.4, fc="white", ec="black", hatch="////", clip_on=False))
ax.text(lx + 2.0, -0.95, "Final work", fontsize=11.5, va="center")
fig.savefig("fig_4_1_gantt.png", dpi=220, bbox_inches="tight", facecolor="white")
print("ok")
