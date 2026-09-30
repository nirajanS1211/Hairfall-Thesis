"""Draws the Gantt chart for Section 4.2. Run: python make_gantt.py
Change MONTHS or the task list below to adjust the schedule."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]

MONTHS = 6
TODAY = 2.0  # end of month 2 = proposal submission

# (task, start, end, done)   start/end are in months from the beginning (0 to MONTHS)
done_tasks = [
    ("Problem formulation and domain study", 0.0, 1.0),
    ("Literature review and research gap", 0.5, 2.0),
    ("Dataset comparison and preparation", 1.0, 2.0),
    ("Preprocessing, range check and split", 1.5, 2.0),
    ("Lab environment and pipeline code", 1.0, 2.0),
]
plan_tasks = [
    ("CatBoost grid search and training", 2.0, 3.0),
    ("TabPFN and TabFM runs (Kaggle GPU)", 2.5, 4.0),
    ("Training-size experiment (500, 2,000, all)", 3.0, 4.5),
    ("SHAP explainability for the three models", 3.5, 5.0),
    ("Metrics, McNemar test, confidence intervals", 4.5, 5.5),
    ("Results analysis and discussion", 5.0, 6.0),
    ("Thesis writing, review and defence", 4.0, 6.0),
]
rows = [("done",) + t for t in done_tasks] + [("plan",) + t for t in plan_tasks]
n = len(rows)
gap = 0.8  # extra space between the two groups

fig, ax = plt.subplots(figsize=(9.2, 5.6))
ylab, y = [], 0
ypos = []
for i, r in enumerate(rows):
    if i == len(done_tasks):
        y += gap
    ypos.append(y)
    y += 1
total_h = y

for (kind, name, s, e), yy in zip(rows, ypos):
    yc = total_h - yy - 0.5
    if kind == "done":
        ax.add_patch(Rectangle((s, yc - 0.3), e - s, 0.6, fc="black", ec="black"))
    else:
        ax.add_patch(Rectangle((s, yc - 0.3), e - s, 0.6, fc="white", ec="black", hatch="////", lw=1.2))
    ylab.append((yc, f"{rows.index((kind, name, s, e)) + 1}. {name}"))

ax.set_yticks([a for a, _ in ylab]); ax.set_yticklabels([b for _, b in ylab], fontsize=10)
ax.set_xlim(0, MONTHS); ax.set_ylim(0, total_h + 0.3)
ax.set_xticks([i + 0.5 for i in range(MONTHS)]); ax.set_xticklabels([f"Month {i+1}" for i in range(MONTHS)], fontsize=10)
ax.xaxis.tick_top()
for i in range(MONTHS + 1):
    ax.axvline(i, color="#999999", lw=0.8)
for a, _ in ylab:
    ax.axhline(a - 0.5, color="#dddddd", lw=0.6)
ax.axvline(TODAY, color="black", lw=1.6, ls="--")
ax.text(TODAY + 0.05, 0.05, "Proposal\nsubmission", fontsize=9, va="bottom", style="italic")

# group headings at left inside the plot
ax.text(-0.02, total_h - 0.02, "", fontsize=1)
for spine in ("right", "bottom"):
    ax.spines[spine].set_visible(False)
ax.tick_params(length=0)

# legend below
lx = 0.3
ax.add_patch(Rectangle((lx, -1.1), 0.5, 0.4, fc="black", ec="black", clip_on=False))
ax.text(lx + 0.6, -0.9, "Completed up to the proposal", fontsize=9.5, va="center")
ax.add_patch(Rectangle((lx + 2.9, -1.1), 0.5, 0.4, fc="white", ec="black", hatch="////", clip_on=False))
ax.text(lx + 3.5, -0.9, "Planned after proposal approval", fontsize=9.5, va="center")
fig.savefig("fig_4_1_gantt.png", dpi=220, bbox_inches="tight", facecolor="white")
print("ok")
