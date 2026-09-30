"""Builds Presentation/Hairfall_Presentation.pptx and .pdf (plain black and white, short, with speaker notes)."""
import subprocess
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
OUT = ROOT / "Presentation"
FONT = "Arial"
BLACK = RGBColor(0, 0, 0)
GREY = RGBColor(0x59, 0x59, 0x59)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 14
COUNT = [1]


def text(slide, x, y, w, h, paras, size=20, bold=False, align=PP_ALIGN.LEFT, color=BLACK, anchor=MSO_ANCHOR.TOP, bullet=False, space=8):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    if isinstance(paras, str): paras = [paras]
    for i, t in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space)
        r = p.add_run(); r.text = ("•  " + t) if bullet else t
        r.font.size = Pt(size); r.font.bold = bold; r.font.name = FONT; r.font.color.rgb = color
    return tb


def line(slide, x, y, w):
    ln = slide.shapes.add_connector(1, Inches(x), Inches(y), Inches(x + w), Inches(y))
    ln.line.color.rgb = BLACK; ln.line.width = Pt(1.25)


def new_slide(title, n, notes):
    COUNT[0] += 1
    n = COUNT[0]
    s = prs.slides.add_slide(BLANK)
    text(s, 0.6, 0.35, 12.1, 0.9, title, size=32, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    line(s, 0.65, 1.25, 12.0)
    text(s, 0.6, 7.0, 9, 0.35, "Comparing CatBoost, TabPFN, and TabFM for Explainable Hair Fall Risk Prediction", size=11, color=GREY)
    text(s, 11.7, 7.0, 1.0, 0.35, f"{n} / {TOTAL}", size=11, color=GREY, align=PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = notes
    return s


def cell_border(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = etree.SubElement(tcPr, qn(tag), w="12700", cap="flat", cmpd="sng", algn="ctr")
        sf = etree.SubElement(ln, qn("a:solidFill")); etree.SubElement(sf, qn("a:srgbClr"), val="000000")
        etree.SubElement(ln, qn("a:prstDash"), val="solid")


def table(slide, x, y, w, rows, col_w, size=14, header=True, row_h=0.45):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    tbl = shp.table
    tblPr = tbl._tbl.tblPr
    for a in ("firstRow", "bandRow"): tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is not None: sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # "No Style, Table Grid"
    for j, cw in enumerate(col_w): tbl.columns[j].width = Inches(cw)
    for i, r in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(r):
            c = tbl.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = RGBColor(0xEE, 0xEE, 0xEE) if (header and i == 0) else RGBColor(255, 255, 255)
            c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.04)
            tf = c.text_frame; tf.word_wrap = True; tf.text = ""
            p = tf.paragraphs[0]; run = p.add_run(); run.text = val
            run.font.size = Pt(size); run.font.name = FONT; run.font.color.rgb = BLACK; run.font.bold = (header and i == 0) or (j == 0 and not header)
            cell_border(c)
    return tbl


def picture(slide, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(FIG / name), Inches(x), Inches(y), **kw)


# 1 Title -------------------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
text(s, 0.8, 0.6, 11.7, 0.5, "Tribhuvan University, Institute of Science and Technology", size=18, align=PP_ALIGN.CENTER, color=GREY)
s.shapes.add_picture(str(FIG / "tu_logo_bw.png"), Inches(6.17), Inches(1.3), height=Inches(1.6))
text(s, 0.8, 3.2, 11.7, 1.7, "Comparing CatBoost, TabPFN, and TabFM for Explainable Hair Fall Risk Prediction", size=36, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
line(s, 3.2, 5.05, 7.0)
text(s, 0.8, 5.25, 11.7, 1.6, ["Dissertation Proposal", "Submitted by: Nirajan Shahi (Roll no. 49/079)", "Supervised by: Asst. Prof. Jagadish Bhatta", "Central Department of Computer Science and Information Technology, Kirtipur, Kathmandu"], size=16, align=PP_ALIGN.CENTER, space=4)
s.notes_slide.notes_text_frame.text = "Introduce the topic: we compare three models for predicting hair fall risk and explain each prediction."

# Contents ------------------------------------------------------------------------------------------
s = new_slide("Contents", 2, "Outline of the talk: the project in one slide, the problem, what is known, the gap, the data and methods, and what we expect.")
table(s, 2.2, 1.7, 8.9, [
    ["Topic", "Slides"],
    ["1.  Project at a glance", "3"],
    ["2.  Problem and objectives", "4 - 5"],
    ["3.  Background and literature", "6 - 8"],
    ["4.  Research gap", "9"],
    ["5.  Data and methods", "10 - 12"],
    ["6.  Expected outcomes", "13"],
], [7.0, 1.9], size=20, row_h=0.65)

# 3 At a glance ------------------------------------------------------------------------------------
s = new_slide("Project at a glance", 3, "One-slide summary. The problem, the aim, what is missing in earlier work, the data and method, and what we expect.")
table(s, 0.65, 1.7, 12.0, [
    ["Problem", "Hair fall risk is hard to judge, and prediction models are hard to explain."],
    ["Objectives", "Benchmark CatBoost, TabPFN, and TabFM, and explain every model with SHAP."],
    ["Research gap", "Foundation models were never tested on hair fall data, and CatBoost was never tuned."],
    ["Data and method", "21,606 records, 3 risk tiers; same split for all models; accuracy, macro-F1, ROC-AUC."],
    ["Expected outcome", "A fair comparison and explanations that agree with known causes."],
], [2.6, 9.4], size=18, header=False, row_h=0.85)

# 4 Problem ----------------------------------------------------------------------------------------
s = new_slide("Problem statement", 4, "Hair loss has many causes that act together, so no single test predicts it. Earlier studies used classical models, and new foundation models are untested and hard to explain.")
text(s, 0.8, 1.9, 11.7, 4.5, [
    "Hair loss risk is hard to judge: hormones, nutrition, stress, and habits act together.",
    "Earlier studies used classical algorithms, with accuracies from about 50% to 100%.",
    "Newer foundation models (TabPFN, TabFM) are untested on hair fall data and hard to explain.",
], size=26, bullet=True, space=26)

# 5 Objectives -------------------------------------------------------------------------------------
s = new_slide("Objectives", 5, "Two objectives: compare the three models, and explain them.")
text(s, 0.8, 2.1, 11.7, 4.0, [
    "1.  Implement and benchmark CatBoost, TabPFN, and TabFM for multi-tier hair fall risk.",
    "2.  Explain every model with SHAP so each predicted risk tier can be traced to specific indicators.",
], size=28, space=30)

# 6 Background -------------------------------------------------------------------------------------
s = new_slide("Background: what causes hair loss", 6, "Hair grows in cycles. Anything that pushes follicles into the resting phase early causes shedding. These factors overlap, so a model that combines many indicators is useful.")
table(s, 0.65, 1.8, 12.0, [
    ["Factor", "What it does"],
    ["Hormones and heredity", "Inherited sensitivity to androgens; family history matters"],
    ["Nutrition and iron", "Shortage of iron, zinc, and vitamins weakens follicles"],
    ["Thyroid function", "Thyroid hormones regulate the hair cycle"],
    ["Psychological stress", "Pushes follicles into the resting phase early"],
], [3.8, 8.2], size=20, row_h=0.8)

# 7 Literature -------------------------------------------------------------------------------------
s = new_slide("Literature: what others did", 7, "These are the closest studies. They use classical models on survey data, the results differ a lot, and none compared explanations.")
table(s, 0.65, 1.8, 12.0, [
    ["Study", "Models", "Main result"],
    ["Khatun et al. (2022)", "SVM, KNN, LR, RF, XGBoost", "XGBoost 92.62%"],
    ["Kumar et al. (2025)", "RF, XGBoost, CatBoost, LightGBM", "RF 100%, CatBoost 49.5%"],
    ["Siami & Azis (2025)", "LR, DT, RF, GB, XGBoost", "About 50% at best"],
], [3.8, 5.0, 3.2], size=20, row_h=0.8)
text(s, 0.65, 5.5, 12, 0.6, "LR = Logistic Regression, DT = Decision Tree, RF = Random Forest, GB = Gradient Boosting", size=12, color=GREY)

# 8 Model families ---------------------------------------------------------------------------------
s = new_slide("Literature: the three models", 8, "CatBoost is a strong boosted-tree model. TabPFN and TabFM are new foundation models: pretrained once, then they predict in one pass without training.")
text(s, 0.8, 1.9, 11.7, 4.5, [
    "CatBoost (Prokhorenkova et al., 2018): boosted trees for categorical data.",
    "TabPFN (Hollmann et al., 2025): pretrained transformer, best on small tables.",
    "TabFM (Kong et al., 2026): 400-million-parameter foundation model.",
], size=26, bullet=True, space=26)

# 9 Research gap -----------------------------------------------------------------------------------
s = new_slide("Research gap", 9, "This is what we found missing. It is why the project compares these three models and explains them.")
text(s, 0.8, 1.9, 11.7, 4.5, [
    "Only classical algorithms were used, and CatBoost was never tuned.",
    "TabPFN and TabFM were never tested on hair loss data.",
    "No study explains boosted trees and foundation models side by side.",
], size=28, bullet=True, space=28)

# 10 Data ------------------------------------------------------------------------------------------
s = new_slide("Data", 10, "Two public datasets feed a super dataset of 200,000 records. Comparing it with them gives the final dataset of 21,606 records used for modelling.")
text(s, 0.6, 1.8, 5.0, 4.5, [
    "Two public datasets: Kaggle and Mendeley.",
    "Super dataset: 200,000 records.",
    "Final dataset: 21,606 records, 20 features, 3 risk tiers.",
], size=22, bullet=True, space=20)
picture(s, "fig_3_2_dataset_link.png", 5.7, 2.4, w=7.3)

# 11 Framework -------------------------------------------------------------------------------------
s = new_slide("Research framework", 11, "One pipeline: clean and split once, give the same rows to the three models, evaluate them the same way, and explain each with SHAP.")
picture(s, "fig_3_1_framework.png", 1.9, 1.6, w=9.5)
text(s, 0.9, 6.3, 11.5, 0.6, "Same split and seed for all models.", size=18, align=PP_ALIGN.CENTER)

# 12 Models ----------------------------------------------------------------------------------------
s = new_slide("Models", 12, "CatBoost needs training and tuning. TabPFN and TabFM only read the training rows as context and predict, so they need no tuning.")
table(s, 0.65, 1.8, 12.0, [
    ["Model", "Tuning"],
    ["CatBoost", "Trained and tuned (grid search, 5-fold cross-validation)"],
    ["TabPFN", "None"],
    ["TabFM", "None"],
], [3.8, 8.2], size=22, row_h=0.9)

# 13 Expected outcomes ------------------------------------------------------------------------------
s = new_slide("Expected outcomes", 13, "These are expectations to test, not results. The study can also show the opposite.")
text(s, 0.8, 1.9, 11.7, 4.5, [
    "A fair comparison of the three models on the same data.",
    "TabPFN and TabFM competitive without tuning (to be tested).",
    "Explanations that agree with known causes: iron, stress, family history.",
], size=26, bullet=True, space=26)

# Thank you -----------------------------------------------------------------------------------------
s = prs.slides.add_slide(BLANK)
COUNT[0] += 1
text(s, 0.8, 2.3, 11.7, 1.4, "Thank you", size=54, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
line(s, 4.2, 3.9, 5.0)
text(s, 0.8, 4.1, 11.7, 1.2, ["Questions are welcome", "Nirajan Shahi  |  Supervisor: Asst. Prof. Jagadish Bhatta"], size=20, align=PP_ALIGN.CENTER, space=8)
text(s, 11.7, 7.0, 1.0, 0.35, f"{COUNT[0]} / {TOTAL}", size=11, color=GREY, align=PP_ALIGN.RIGHT)
s.notes_slide.notes_text_frame.text = "Thank the panel and invite questions."

prs.save(OUT / "Hairfall_Presentation.pptx")
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT), str(OUT / "Hairfall_Presentation.pptx")], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("ok", COUNT[0])
