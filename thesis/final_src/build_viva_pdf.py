"""Builds final/Viva_Question_Bank.pdf from viva_content.py.  Run: python build_viva_pdf.py"""
import os
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from viva_content import KEY_NUMBERS, SECTIONS, TIPS  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(BASE), "final", "Viva_Question_Bank.pdf")
LOGO = os.path.join(BASE, "assets", "lincoln_logo.jpeg")

F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Body", F + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("Body-B", F + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("Body-I", F + "Arial Italic.ttf"))
pdfmetrics.registerFont(TTFont("Head", F + "Georgia Bold.ttf"))
from reportlab.lib.fonts import addMapping  # noqa: E402
addMapping("Body", 0, 0, "Body"); addMapping("Body", 1, 0, "Body-B"); addMapping("Body", 0, 1, "Body-I")
addMapping("Body", 1, 1, "Body-B")

DARK = colors.HexColor("#1B1F2A")
RED = colors.HexColor("#C8102E")
MUTED = colors.HexColor("#5B6170")
SOFT = colors.HexColor("#F2F3F5")
PINK = colors.HexColor("#FBE9EC")
GOLD = colors.HexColor("#B7791F")

st = {
    "title": ParagraphStyle("title", fontName="Head", fontSize=30, leading=36, textColor=colors.white),
    "sub": ParagraphStyle("sub", fontName="Body", fontSize=13, leading=18, textColor=colors.HexColor("#D5D8DF")),
    "h1": ParagraphStyle("h1", fontName="Head", fontSize=20, leading=25, textColor=DARK, spaceAfter=4),
    "intro": ParagraphStyle("intro", fontName="Body-I", fontSize=10, leading=14, textColor=MUTED, spaceAfter=10),
    "q": ParagraphStyle("q", fontName="Body-B", fontSize=11, leading=15, textColor=DARK),
    "a": ParagraphStyle("a", fontName="Body", fontSize=10, leading=14.5, textColor=colors.HexColor("#2A2F3A")),
    "body": ParagraphStyle("body", fontName="Body", fontSize=10.5, leading=15, textColor=DARK),
    "small": ParagraphStyle("small", fontName="Body", fontSize=9, leading=12, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=9.5, leading=13, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="Body-B", fontSize=9.5, leading=13, textColor=DARK),
    "num": ParagraphStyle("num", fontName="Body-B", fontSize=10, leading=14, textColor=colors.white, alignment=TA_CENTER),
    "toc": ParagraphStyle("toc", fontName="Body", fontSize=11, leading=17, textColor=DARK),
}

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


def on_cover(c, doc):
    c.saveState()
    c.setFillColor(DARK)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.roundRect(MARGIN, PAGE_H - MARGIN - 2.3 * cm, 6.0 * cm, 2.3 * cm, 6, stroke=0, fill=1)
    c.drawImage(LOGO, MARGIN + 0.2 * cm, PAGE_H - MARGIN - 2.1 * cm, width=5.6 * cm, height=1.9 * cm,
                preserveAspectRatio=True, mask="auto")
    c.restoreState()


def on_page(c, doc):
    c.saveState()
    c.setFont("Body", 8.5)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 1.1 * cm, "Viva Question Bank  ·  Hair Fall Risk Stratification  ·  Krishna Gautam")
    c.drawRightString(PAGE_W - MARGIN, 1.1 * cm, str(doc.page))
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN,
                      bottomMargin=1.9 * cm, title="Viva Question Bank", author="Krishna Gautam")
frame = Frame(MARGIN, 1.9 * cm, PAGE_W - 2 * MARGIN, PAGE_H - MARGIN - 1.9 * cm, id="f", leftPadding=0,
              rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate("cover", [frame], onPage=on_cover), PageTemplate("body", [frame], onPage=on_page)])

W = PAGE_W - 2 * MARGIN
story = []

# ---------------- cover ----------------
total_q = sum(len(s[2]) for s in SECTIONS)
star_q = sum(1 for s in SECTIONS for q in s[2] if q[2])
story += [Spacer(1, 4.2 * cm),
          Paragraph("VIVA PREPARATION", ParagraphStyle("k", fontName="Body-B", fontSize=12, textColor=colors.HexColor("#F2A0AB"))),
          Spacer(1, 0.4 * cm),
          Paragraph("Question Bank for the Thesis Defence", st["title"]),
          Spacer(1, 0.6 * cm),
          Paragraph("Comparative Benchmarking of CatBoost, TabPFN and TabFM for Explainable Multi-Tier Hair Fall "
                    "Risk Stratification", ParagraphStyle("t2", parent=st["sub"], fontSize=15, leading=21,
                                                         textColor=colors.white)),
          Spacer(1, 1.2 * cm)]
stats = Table([[Paragraph(f"<font size=26><b>{total_q}</b></font>", st["num"]),
                Paragraph(f"<font size=26><b>{star_q}</b></font>", st["num"]),
                Paragraph(f"<font size=26><b>{len(SECTIONS)}</b></font>", st["num"])],
               [Paragraph("questions with answers", st["num"]), Paragraph("marked 'very likely'", st["num"]),
                Paragraph("topics, incl. Nepal context", st["num"])]], colWidths=[W / 3] * 3, rowHeights=[1.3 * cm, 0.8 * cm])
stats.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#2A2F3D")),
                           ("LINEAFTER", (0, 0), (1, 1), 1, DARK)]))
story += [stats, Spacer(1, 1.6 * cm),
          Paragraph("Krishna Gautam  ·  Supervisor: Rabin Shrestha", st["sub"]),
          Paragraph("Master of Computer Science (MCS)  ·  Lincoln International College of Management &amp; IT", st["sub"]),
          NextPageTemplate("body"), PageBreak()]

# ---------------- how to use + tips ----------------
story.append(Paragraph("How to use this booklet", st["h1"]))
story.append(Paragraph(
    "Questions are grouped in the order examiners usually ask them: summary first, then problem, data, method, "
    "results and limitations. Each answer is short enough to say aloud in 20-40 seconds. Questions marked "
    "<font color='#C8102E'><b>VERY LIKELY</b></font> are asked in almost every viva; read those first. "
    "The dataset and limitations sections are where examiners push hardest. Text in [square brackets] must be "
    "filled with your own facts.", st["body"]))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("How to answer well", ParagraphStyle("h2", parent=st["h1"], fontSize=15, leading=19)))
rows = []
for i, (h, d) in enumerate(TIPS, 1):
    rows.append([Paragraph(str(i), st["num"]), Paragraph(f"<b>{escape(h)}</b><br/>{escape(d)}", st["cell"])])
t = Table(rows, colWidths=[0.9 * cm, W - 0.9 * cm])
t.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), RED), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                       ("ROWBACKGROUNDS", (1, 0), (1, -1), [SOFT, colors.white]),
                       ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                       ("LEFTPADDING", (1, 0), (1, -1), 10), ("LINEBELOW", (0, 0), (0, -2), 1.5, colors.white)]))
story += [t, Spacer(1, 0.6 * cm)]
story.append(Paragraph("Contents", ParagraphStyle("h2", parent=st["h1"], fontSize=15, leading=19)))
n = 1
toc_rows = []
for title, _, qs in SECTIONS:
    toc_rows.append([Paragraph(escape(title), st["toc"]), Paragraph(f"Q{n}–Q{n + len(qs) - 1}", st["toc"])])
    n += len(qs)
tt = Table(toc_rows, colWidths=[W - 3 * cm, 3 * cm])
tt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DADDE3")),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 1),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
story += [tt, PageBreak()]

# ---------------- key numbers ----------------
story.append(Paragraph("Key numbers to remember", st["h1"]))
story.append(Paragraph("Examiners often ask for exact values. Learn this page by heart.", st["intro"]))
kn = [[Paragraph(escape(k), st["cellb"]), Paragraph(escape(v), st["cell"])] for k, v in KEY_NUMBERS]
kt = Table(kn, colWidths=[4.2 * cm, W - 4.2 * cm])
kt.setStyle(TableStyle([("ROWBACKGROUNDS", (0, 0), (-1, -1), [SOFT, colors.white]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
story += [kt, Spacer(1, 0.5 * cm)]
elev = ("<b>Your 30-second elevator answer:</b> I benchmarked a tuned CatBoost against two zero-shot tabular "
        "foundation models, TabPFN and TabFM, for three-tier hair fall risk. All reached about 78% accuracy with no "
        "significant difference; with little data the foundation models were far better; SHAP showed the same seven "
        "biomarkers drive every model; TabFM was slow at large context. The data are constructed, so it is a "
        "benchmark, not a clinical tool.")
et = Table([[Paragraph(elev, st["body"])]], colWidths=[W])
et.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PINK), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
story += [et, PageBreak()]

# ---------------- questions ----------------
qn = 1
for si, (title, intro, qs) in enumerate(SECTIONS, 1):
    head = Table([[Paragraph(f"<font color='#C8102E'>{si:02d}</font>&nbsp;&nbsp;{escape(title)}", st["h1"])]],
                 colWidths=[W])
    head.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    block = [head]
    if intro:
        block.append(Paragraph(escape(intro), st["intro"]))
    else:
        block.append(Spacer(1, 0.2 * cm))
    first = True
    for q, a, star in qs:
        tag = "&nbsp;&nbsp;<font name='Body-B' size='7.5' color='#C8102E'>VERY LIKELY</font>" if star else ""
        qrow = Table([[Paragraph(f"Q{qn}", st["num"]), Paragraph(escape(q) + tag, st["q"])]],
                     colWidths=[1.45 * cm, W - 1.45 * cm])
        qrow.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), RED if star else DARK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                  ("LEFTPADDING", (1, 0), (1, 0), 9), ("TOPPADDING", (0, 0), (-1, -1), 4),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        arow = Table([[Paragraph(escape(a).replace("[", "<font color='#B7791F'><b>[").replace("]", "]</b></font>"), st["a"])]],
                     colWidths=[W - 1.45 * cm])
        arow.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SOFT), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        wrap = Table([["", arow]], colWidths=[1.45 * cm, W - 1.45 * cm])
        wrap.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                  ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        item = [qrow, wrap, Spacer(1, 0.32 * cm)]
        if first:
            block += item
            story.append(KeepTogether(block))
            first = False
        else:
            story.append(KeepTogether(item))
        qn += 1
    story.append(Spacer(1, 0.4 * cm))

# ---------------- closing checklist ----------------
story.append(PageBreak())
story.append(Paragraph("Night-before checklist", st["h1"]))
check = ["Say the 2-minute summary aloud three times (Q1).", "Learn the Key Numbers page.",
         "Re-read the dataset and limitations answers; practise saying them calmly.",
         "Open the demo app once and test one prediction; keep screenshots in case the internet or API fails.",
         "Keep the thesis PDF open to point to tables and sections.",
         "Fill every [square bracket] in this booklet with your own facts (plagiarism %, meetings).",
         "Bring a printed copy of the thesis, the slides, and the supervisor progress form."]
ct = Table([[Paragraph("☐", ParagraphStyle("cb", fontName="Body", fontSize=13, textColor=RED)), Paragraph(escape(c), st["body"])] for c in check],
           colWidths=[0.8 * cm, W - 0.8 * cm])
ct.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DADDE3"))]))
story += [ct, Spacer(1, 0.6 * cm),
          Paragraph("Sources used to choose the question types: general viva-question guides (iLovePhD, VivaCoach, upGrad) "
                    "and machine-learning viva lists, adapted to this thesis and to the Nepali context.", st["small"])]

doc.build(story)
print("saved", OUT, total_q, "questions")
