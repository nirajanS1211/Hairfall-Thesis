"""Draws the block diagrams for Chapter 3 (black and white, print friendly). Run: python make_figures.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "Times", "DejaVu Serif"]
FS = 10.5
S = 0.78  # figure size factor: smaller figure -> relatively larger text when scaled to page width
LIGHT, MID = "#f2f2f2", "#d9d9d9"


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w * S, h * S))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fill="white", fs=FS, bold=False, style="round,pad=0.02,rounding_size=0.08", ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fill, ec="black", lw=1.1, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, text=None, ls="-", rad=0.0, dx=0, dy=0.12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, lw=1.1, color="black",
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, text, ha="center", va="bottom", fontsize=FS - 1.5, style="italic")


def group(ax, x, y, w, h, title):
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec="black", lw=1.0, ls="--"))
    ax.text(x + 0.12, y + h - 0.1, title, ha="left", va="top", fontsize=FS - 1, fontweight="bold")


def save(fig, name):
    fig.savefig(name, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------- Figure 3.1: overall framework ----------------
fig, ax = canvas(12.4, 5.2)
box(ax, 0.2, 2.1, 1.8, 1.0, "Final dataset\n21,606 records", MID, bold=True)
box(ax, 2.4, 2.1, 2.2, 1.0, "Preprocessing\nremove identifiers,\nencode gender", LIGHT)
box(ax, 5.0, 2.1, 1.7, 1.0, "Stratified split\n80 % train\n20 % test", LIGHT)
box(ax, 7.3, 3.75, 2.1, 0.85, "CatBoost\n(tuned and trained)", "white")
box(ax, 7.3, 2.175, 2.1, 0.85, "TabPFN\n(in-context)", "white")
box(ax, 7.3, 0.6, 2.1, 0.85, "TabFM\n(in-context)", "white")
box(ax, 10.0, 2.1, 1.8, 1.0, "Predicted\nrisk tier\nLow / Mod. / High", MID, fs=FS - 1)
arrow(ax, 2.0, 2.6, 2.4, 2.6); arrow(ax, 4.6, 2.6, 5.0, 2.6)
for yy in (4.175, 2.6, 1.025):
    arrow(ax, 6.7, 2.6, 7.3, yy)
    arrow(ax, 9.4, yy, 10.0, 2.6)
box(ax, 9.6, 0.2, 2.4, 0.9, "Evaluation\nmetrics, time,\nMcNemar test", LIGHT, fs=FS - 1.5)
box(ax, 9.6, 4.1, 2.4, 0.9, "Explainability\nSHAP: global +\nper-patient", LIGHT, fs=FS - 1.5)
arrow(ax, 10.9, 3.1, 10.9, 4.1); arrow(ax, 10.9, 2.1, 10.9, 1.1)
save(fig, "fig_3_1_framework.png")

# ---------------- Figure 3.2: dataset linkage ----------------
fig, ax = canvas(11.6, 4.8)
box(ax, 0.2, 3.1, 2.7, 1.4, "Dataset 1 (Kaggle)\n100,000 rows\n13 columns", MID, fs=FS - 1)
box(ax, 0.2, 0.3, 2.7, 1.4, "Dataset 2 (Mendeley)\n716 survey answers\n14 columns", MID, fs=FS - 1)
box(ax, 4.3, 1.6, 2.7, 1.6, "Super dataset\n200,000 rows\nmany fields; age and\ngender identified", LIGHT, bold=True, fs=FS - 1)
box(ax, 8.6, 1.6, 2.6, 1.6, "Final dataset\n21,606 records", MID, bold=True, fs=FS - 1)
arrow(ax, 2.9, 3.4, 4.3, 2.8); arrow(ax, 2.9, 1.5, 4.3, 2.0)
arrow(ax, 7.0, 2.4, 8.6, 2.4)
arrow(ax, 2.9, 4.1, 9.9, 4.1, ls="--", rad=0.0); arrow(ax, 9.9, 4.1, 9.9, 3.2, ls="--")
arrow(ax, 2.9, 0.6, 9.9, 0.6, ls="--", rad=0.0); arrow(ax, 9.9, 0.6, 9.9, 1.6, ls="--")
save(fig, "fig_3_2_dataset_link.png")

# ---------------- Figure 3.3: CatBoost ----------------
fig, ax = canvas(12, 5.6)
ax.set_ylim(-0.9, 5.6)
box(ax, 0.2, 2.1, 1.7, 1.4, "Input row\n(20 features)", MID)
group(ax, 2.5, 0.5, 5.3, 4.4, "Symmetric decision trees, added one by one")
for i, (x, t) in enumerate([(2.8, "Tree 1"), (4.4, "Tree 2"), (6.0, "... Tree T")]):
    # small symmetric tree: same split on each level
    ax.add_patch(Rectangle((x, 2.55), 1.4, 0.4, fc=LIGHT, ec="black", lw=1)); ax.text(x + 0.7, 2.75, "split A", ha="center", va="center", fontsize=8)
    ax.add_patch(Rectangle((x, 2.05), 0.7, 0.4, fc="white", ec="black", lw=1)); ax.text(x + 0.35, 2.25, "split B", ha="center", va="center", fontsize=8)
    ax.add_patch(Rectangle((x + 0.7, 2.05), 0.7, 0.4, fc="white", ec="black", lw=1)); ax.text(x + 1.05, 2.25, "split B", ha="center", va="center", fontsize=8)
    for k in range(4):
        ax.add_patch(Rectangle((x + k * 0.35, 1.55), 0.35, 0.4, fc=MID, ec="black", lw=1)); ax.text(x + k * 0.35 + 0.175, 1.75, f"L{k+1}", ha="center", va="center", fontsize=7)
    ax.text(x + 0.7, 3.15, t, ha="center", fontsize=FS - 1, fontweight="bold")
ax.text(5.15, 3.85, "Each tree learns the mistakes of the trees before it", ha="center", fontsize=FS - 1.5, style="italic")
ax.text(5.15, 0.9, "Illustration with depth 2: one split per level\nfor the whole tree, so 4 leaves (depth $d$ gives $2^d$ leaves)", ha="center", fontsize=FS - 2.5)
arrow(ax, 1.9, 2.8, 2.5, 2.8)
box(ax, 8.4, 2.1, 1.4, 1.4, "Add tree\noutputs\n(one score\nper class)", LIGHT)
box(ax, 10.3, 2.1, 1.5, 1.4, "Softmax\nLow / Mod. /\nHigh\nprobability", MID)
arrow(ax, 7.8, 2.8, 8.4, 2.8); arrow(ax, 9.8, 2.8, 10.3, 2.8)
box(ax, 2.0, -0.75, 6.3, 0.85, "Categorical answers: ordered target statistics\n(each row is encoded from earlier rows only)", "white", fs=FS - 2)
save(fig, "fig_3_3_catboost.png")

# ---------------- Figure 3.4: TabPFN ----------------
fig, ax = canvas(12, 5.8)
box(ax, 0.2, 3.5, 2.2, 1.1, "Training rows\n(features + known\nrisk tier)", MID)
box(ax, 0.2, 1.3, 2.2, 1.1, "Patient to predict\n(features only,\ntier unknown)", LIGHT)
arrow(ax, 2.4, 4.05, 3.0, 3.4); arrow(ax, 2.4, 1.85, 3.0, 2.5)
box(ax, 3.0, 2.3, 1.7, 1.3, "Embed every\nvalue of the table\nas a vector", "white")
group(ax, 5.1, 0.9, 4.0, 4.1, "Transformer layers (fixed weights)")
box(ax, 5.4, 3.4, 3.0, 0.9, "Attention across the\nfeatures of one row", LIGHT)
box(ax, 5.4, 1.5, 3.0, 0.9, "Attention across rows:\npatient looks at training rows", LIGHT)
arrow(ax, 6.9, 3.4, 6.9, 2.4, rad=0.0); arrow(ax, 8.4, 1.95, 8.4, 3.85, rad=-0.6, ls="--")
ax.text(8.85, 2.9, "repeat", fontsize=FS - 2, style="italic", rotation=90, va="center")
arrow(ax, 4.7, 2.95, 5.4, 3.8); arrow(ax, 4.7, 2.95, 5.4, 2.0)
box(ax, 9.9, 2.3, 1.9, 1.3, "Class\nprobabilities\nLow / Mod. /\nHigh", MID)
arrow(ax, 9.1, 2.95, 9.9, 2.95)
ax.text(6.0, 0.35, "One forward pass, no training on hair fall data. The weights were learned once on millions of synthetic tables.", ha="center", fontsize=FS - 1.5, style="italic")
save(fig, "fig_3_4_tabpfn.png")

# ---------------- Figure 3.5: TabFM ----------------
fig, ax = canvas(12, 5.8)
box(ax, 0.2, 3.5, 2.2, 1.1, "Context table\n(training rows with\nknown risk tier)", MID)
box(ax, 0.2, 1.3, 2.2, 1.1, "Query rows\n(patients to predict,\ntier unknown)", LIGHT)
arrow(ax, 2.4, 4.05, 3.0, 3.4); arrow(ax, 2.4, 1.85, 3.0, 2.5)
box(ax, 3.0, 2.3, 1.7, 1.3, "Embed every\ncell of the table", "white")
group(ax, 5.1, 0.9, 4.0, 4.1, "Table encoder (fixed weights)")
box(ax, 5.4, 3.4, 3.0, 0.9, "Column-wise attention:\nsame feature across rows", LIGHT)
box(ax, 5.4, 1.5, 3.0, 0.9, "Row-wise attention:\nfeatures within one row", LIGHT)
arrow(ax, 6.9, 3.4, 6.9, 2.4); arrow(ax, 8.4, 1.95, 8.4, 3.85, rad=-0.6, ls="--")
ax.text(8.85, 2.9, "alternate", fontsize=FS - 2, style="italic", rotation=90, va="center")
arrow(ax, 4.7, 2.95, 5.4, 3.8); arrow(ax, 4.7, 2.95, 5.4, 2.0)
box(ax, 9.9, 3.5, 1.9, 1.1, "In-context\ntransformer\n(context + query)", "white")
box(ax, 9.9, 1.3, 1.9, 1.1, "Class\nprobabilities\nLow / Mod. / High", MID)
arrow(ax, 9.1, 3.4, 9.9, 3.9); arrow(ax, 10.85, 3.5, 10.85, 2.4)
ax.text(6.0, 0.35, "About 400 million parameters, pretrained once on synthetic tables. No training or tuning on hair fall data.", ha="center", fontsize=FS - 1.5, style="italic")
save(fig, "fig_3_5_tabfm.png")

# ---------------- Figure 3.6: SHAP workflow ----------------
fig, ax = canvas(11, 4.8)
box(ax, 0.2, 1.9, 2.1, 1.2, "Trained model:\nCatBoost,\nTabPFN, TabFM", MID)
box(ax, 2.6, 3.3, 2.3, 1.0, "CatBoost:\nTreeExplainer (exact)", LIGHT)
box(ax, 2.6, 0.7, 2.3, 1.0, "TabPFN, TabFM:\nKernelExplainer\n(repeated predictions)", LIGHT)
arrow(ax, 2.3, 2.7, 2.6, 3.7); arrow(ax, 2.3, 2.3, 2.6, 1.3)
box(ax, 5.4, 1.9, 2.0, 1.2, "SHAP value of\neach feature for\neach patient", "white")
arrow(ax, 4.9, 3.8, 5.4, 2.8); arrow(ax, 4.9, 1.2, 5.4, 2.2)
box(ax, 8.0, 3.3, 2.8, 1.0, "Global ranking\n(which features\nmatter most)", MID)
box(ax, 8.0, 0.7, 2.8, 1.0, "Per-patient\nexplanation\n(why this tier)", MID)
arrow(ax, 7.4, 2.8, 8.0, 3.7); arrow(ax, 7.4, 2.2, 8.0, 1.3)
save(fig, "fig_3_6_shap.png")

# ---------------- Figure 3.7: experimental environment ----------------
fig, ax = canvas(11.4, 4.2)
group(ax, 0.2, 0.5, 4.9, 3.0, "Local machine: Mac (Apple silicon)")
box(ax, 0.5, 1.9, 4.3, 1.0, "CatBoost tuning and training", LIGHT)
box(ax, 0.5, 0.75, 4.3, 0.95, "Statistical tests, result tables\nand figures", LIGHT, fs=FS - 1)
group(ax, 6.2, 0.5, 4.9, 3.0, "Kaggle notebook (GPU accelerator)")
box(ax, 6.5, 1.9, 4.3, 1.0, "TabPFN and TabFM predictions", LIGHT)
box(ax, 6.5, 0.75, 4.3, 0.95, "Same split and random seed 42", LIGHT, fs=FS - 1)
arrow(ax, 5.1, 2.3, 6.2, 2.3, "train and\ntest files", dy=0.15); arrow(ax, 6.2, 1.2, 5.1, 1.2, "predictions,\nmetrics", dy=-0.62)
save(fig, "fig_3_7_environment.png")
print("done")
