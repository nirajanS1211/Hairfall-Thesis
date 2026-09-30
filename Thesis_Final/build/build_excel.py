"""Builds Hairfall_Proposal_Summary.xlsx: a short, plain (black, white, grey) summary of the whole proposal."""
import re
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
wb = Workbook()
thin = Side(style="thin", color="000000")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="D9D9D9")
F = "Arial"


def sheet(name, rows, widths, title=None, header=True):
    ws = wb.create_sheet(name)
    r0 = 1
    if title:
        ws.cell(1, 1, title).font = Font(name=F, size=14, bold=True)
        r0 = 3
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = ws.cell(r0 + i, j + 1, v)
            c.font = Font(name=F, size=11, bold=(header and i == 0))
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = BORDER
            if header and i == 0: c.fill = HEAD
    for j, w in enumerate(widths): ws.column_dimensions[get_column_letter(j + 1)].width = w
    ws.sheet_view.showGridLines = False
    return ws


wb.remove(wb.active)

sheet("1 Overview", [
    ["Item", "Detail"],
    ["Title", "Comparing CatBoost, TabPFN, and TabFM for Explainable Hair Fall Risk Prediction"],
    ["Submitted by", "Nirajan Shahi (Roll no. 49/079)"],
    ["Supervisor", "Asst. Prof. Jagadish Bhatta"],
    ["Submitted to", "Central Department of Computer Science and Information Technology, Tribhuvan University, Kirtipur, Kathmandu"],
    ["Degree", "M.Sc. Computer Science and Information Technology (M.Sc. CSIT)"],
    ["Time plan", "4 months: proposal work (Months 1 and 2) and final work (Months 3 and 4)"],
    ["One line", "Benchmark three models (CatBoost, TabPFN, TabFM) for predicting hair fall risk and explain every model with SHAP."],
], [22, 95], title="Project summary")

sheet("2 Problem and objectives", [
    ["Part", "Summary"],
    ["Problem 1", "Hair loss risk is hard to judge: hormones, nutrition, stress, illness, and habits act together and no single test predicts it."],
    ["Problem 2", "Assessment often relies on self-reporting or late clinical checks."],
    ["Problem 3", "Earlier prediction studies used classical algorithms with very different accuracies (about 50% to 100%)."],
    ["Problem 4", "Tabular foundation models (TabPFN, TabFM) have not been tested on hair fall data, and predictions of the models are hard to explain."],
    ["Objective 1", "Implement and benchmark CatBoost, TabPFN, and TabFM for predicting multi-tier hair fall risk from structured clinical and lifestyle data."],
    ["Objective 2", "Provide transparent, feature-level insights for every model through SHAP, so each predicted risk tier can be traced to specific indicators."],
], [16, 110], title="Problem and objectives")

sheet("3 Background", [
    ["Factor", "What it does", "Source"],
    ["Hormones and heredity", "Inherited sensitivity to androgens; family history is an important indicator", "Agaoglu et al. (2021)"],
    ["Nutrition and iron", "Shortage of iron, zinc, and vitamins weakens follicles", "Guo & Katta (2017); Lin et al. (2023); Treister-Goltzman et al. (2022)"],
    ["Thyroid function", "Thyroid hormones regulate the hair cycle", "Hussein et al. (2023); Marahatta et al. (2018)"],
    ["Psychological stress", "Pushes follicles into the resting phase early", "Bai et al. (2026)"],
    ["Illness and infection", "Can trigger heavy shedding (telogen effluvium)", "Cline et al. (2021)"],
    ["Who is affected", "Young people too; survey of 610 people in Bangladesh, mostly aged 18 to 24", "Khatun et al. (2022); Sun et al. (2025)"],
], [26, 70, 58], title="Background: causes of hair loss")

sheet("4 Literature", [
    ["Study", "Data", "Models", "Main result", "Limitation"],
    ["Khatun et al. (2022)", "Survey, 610 people, Bangladesh", "SVM, KNN, LR, RF, XGBoost", "XGBoost 92.62%", "Classical models only, no explanation"],
    ["Sai et al. (2023)", "Hair fall data", "SVM, KNN, DT, RF, LR, ensemble", "Ensemble best", "No categorical-aware boosting, no explanation"],
    ["Kumar et al. (2025)", "2,000 records, 10 features", "RF, XGBoost, CatBoost, LightGBM and others", "RF 100%, CatBoost 49.5%", "Very high score, CatBoost untuned"],
    ["Siami & Azis (2025)", "Balanced multi-factor data", "LR, DT, RF, GB, XGBoost, voting", "About 50% at best", "Weak signal, modest accuracy"],
    ["Leema et al. (2025)", "Survey, 750 people", "LSTM, RF, TFT, ARIMAX", "TFT 97.5%", "Private data, self-reported only"],
    ["Shakeel et al. (2021)", "Hair images", "SVM, KNN", "91.4% and 88.9%", "Images needed, one condition"],
    ["Sayyad et al. (2022)", "268 images", "VGG with SVM", "98.31%", "Small image set, one condition"],
    ["Pandikumar et al. (2024)", "Scalp images and lifestyle sequences", "CNN, LSTM", "Framework proposed", "Needs images"],
    ["Prokhorenkova et al. (2018)", "Benchmarks", "CatBoost", "Beats other boosting libraries", "Not health-specific"],
    ["Hollmann et al. (2025)", "Benchmarks", "TabPFN", "Strong on small tables", "No hair loss data"],
    ["Kong et al. (2026)", "TabArena, 51 datasets", "TabFM", "First among default foundation models", "No health data"],
    ["Pandey (2026)", "13 TabArena datasets", "TabFM vs XGBoost, RF, TabPFN", "Confirmed competitive", "Four defects, memory limit"],
    ["Lundberg & Lee (2017)", "General method", "SHAP", "Explains any model", "Not a hair loss study"],
], [26, 30, 38, 30, 38], title="Literature review (LR = Logistic Regression, DT = Decision Tree, RF = Random Forest, GB = Gradient Boosting)")

sheet("5 Research gap", [
    ["No.", "What was found"],
    [1, "Hair loss prediction studies used only classical algorithms, and their accuracies differ widely (about 50% to 100%) on different datasets."],
    [2, "CatBoost was compared only once, and it was not tuned."],
    [3, "TabPFN and TabFM have not been tested on hair loss data."],
    [4, "TabFM has only one independent check, which reported software defects and memory limits."],
    [5, "No study explains a boosted-tree model and foundation models side by side."],
], [8, 120], title="Research gap")

sheet("6 Datasets", [
    ["Dataset", "Source", "Rows", "Columns", "Content", "Row identifier"],
    ["Dataset 1", "Kaggle Hair Loss Dataset (Dhankour, 2023)", "100,000", "13", "age, gender, 10 numeric measurement columns, hair_fall (0 to 5)", "Age and gender"],
    ["Dataset 2", "Mendeley hair fall causes (Arnob et al., 2024)", "716", "14", "Questionnaire: age, gender, 8 Yes/No answers, hair fall problem, food habit", "Age and gender"],
    ["Super dataset", "Consolidated health dataset", "200,000", "All columns of both and many additional fields", "Every column of Dataset 1 and Dataset 2 and additional derived fields", "Age and gender"],
    ["Final dataset", "Derived from Dataset 1, Dataset 2, and the super dataset", "21,606", "23", "20 features and the 3-tier target hair_fall (Low 45%, Moderate 35%, High 20%)", "id (1 to 21,606)"],
], [16, 42, 12, 26, 60, 18], title="Datasets")

# columns sheet from Table 3.2 in the chapter
txt = (ROOT / "Chapter_3_Methodology.md").read_text()
blk = txt[txt.index("**Table 3.2:**"):]
rows = []
for l in blk.splitlines():
    if l.startswith("|") and not l.startswith("|---"):
        rows.append([c.strip() for c in l.strip().strip("|").split("|")])
    elif rows and not l.startswith("|"): break
sheet("7 Columns", rows, [26, 38, 26, 22, 22, 14], title="Columns of the final dataset and where they come from")

sheet("8 Methods", [
    ["Step", "What will be done"],
    ["Preprocessing", "Remove id and name; check missing values and duplicates; range check (keep out-of-range values, remove impossible ones); code gender 0/1/2; target 0 Low, 1 Moderate, 2 High"],
    ["Split", "Stratified 80% train (17,284) and 20% test (4,322), seed 42; training sizes 500, 2,000, and all 17,284"],
    ["CatBoost", "Symmetric boosted trees; tuned with grid search (depth, learning rate) and 5-fold cross-validation on training rows only"],
    ["TabPFN", "Pretrained transformer; training rows used as context; one forward pass; no tuning"],
    ["TabFM", "Pretrained foundation model (about 400 million parameters); training rows as context; no tuning"],
    ["Explainability", "SHAP: TreeExplainer for CatBoost, KernelExplainer for TabPFN and TabFM; global ranking and per-patient explanations"],
    ["Evaluation", "Accuracy, macro-precision, macro-recall, macro-F1, ROC-AUC (one-versus-rest), confusion matrix; McNemar's test and Wilson 95% intervals"],
    ["Tools", "Python: Pandas, NumPy, Scikit-learn, CatBoost, TabPFN, TabFM, PyTorch, SHAP, Statsmodels, Matplotlib"],
    ["Environment", "Mac (Apple silicon) for CatBoost, statistics, and figures; Kaggle GPU notebooks for TabPFN and TabFM; same split and seed for all models"],
], [20, 130], title="Methodology")

sheet("9 Expected outcomes", [
    ["No.", "Expected outcome"],
    [1, "A fair comparison of CatBoost, TabPFN, and TabFM on the same hair fall data (same dataset, split, seed, metrics)."],
    [2, "A properly tuned CatBoost as a strong baseline."],
    [3, "TabPFN and TabFM competitive with tuned CatBoost without tuning, especially with small training sets (to be tested; the opposite can also be found)."],
    [4, "The practical limits of TabFM recorded on a real health dataset."],
    [5, "SHAP explanations compared across the models and checked against known causes (iron, stress, family history)."],
], [8, 120], title="Expected outcomes")

# schedule as a grid (half-month columns)
ws = wb.create_sheet("10 Schedule")
ws.cell(1, 1, "Working schedule (4 months)").font = Font(name=F, size=14, bold=True)
tasks = [
    ("Problem formulation", 0, 2, "p"), ("Literature review", 1, 4, "p"), ("Dataset study", 2, 4, "p"), ("Proposal documentation", 2, 4, "p"),
    ("Data preprocessing and split", 4, 5, "f"), ("CatBoost tuning and training", 4, 6, "f"), ("TabPFN and TabFM (Kaggle)", 5, 7, "f"),
    ("Training-size experiment", 6, 7, "f"), ("SHAP explanations", 6, 8, "f"), ("Metrics and McNemar test", 7, 8, "f"),
    ("Results and discussion", 7, 8, "f"), ("Thesis writing and defence", 6, 8, "f"),
]
ws.cell(3, 1, "Task").font = Font(name=F, bold=True); ws.cell(3, 1).fill = HEAD; ws.cell(3, 1).border = BORDER
for m in range(4):
    ws.merge_cells(start_row=3, start_column=2 + 2 * m, end_row=3, end_column=3 + 2 * m)
    c = ws.cell(3, 2 + 2 * m, f"Month {m + 1}"); c.font = Font(name=F, bold=True); c.fill = HEAD; c.alignment = Alignment(horizontal="center")
    for k in range(2): ws.cell(3, 2 + 2 * m + k).border = BORDER
BLACK = PatternFill("solid", fgColor="000000"); GREY = PatternFill("solid", fgColor="A6A6A6")
for i, (name, s, e, kind) in enumerate(tasks):
    r = 4 + i
    c = ws.cell(r, 1, f"{i + 1}. {name}"); c.font = Font(name=F, size=11); c.border = BORDER
    for k in range(8):
        cell = ws.cell(r, 2 + k); cell.border = BORDER
        if s <= k < e: cell.fill = BLACK if kind == "p" else GREY
ws.cell(4 + len(tasks) + 1, 1, "Black = proposal work (Months 1 and 2)     Grey = final work (Months 3 and 4)").font = Font(name=F, size=11)
ws.column_dimensions["A"].width = 34
for k in range(8): ws.column_dimensions[get_column_letter(2 + k)].width = 9
ws.sheet_view.showGridLines = False

refs = [l.strip() for l in (ROOT / "References.md").read_text().splitlines() if l.strip() and not l.startswith("#") and not l.startswith("*(APA")]
refs = [re.sub(r"\*", "", r) for r in refs]
sheet("11 References", [["APA 7th edition (alphabetical)"]] + [[r] for r in refs], [160], title="References")

wb.save(ROOT / "Hairfall_Proposal_Summary.xlsx")
print("ok", wb.sheetnames)
