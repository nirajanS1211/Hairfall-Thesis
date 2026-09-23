"""Makes the final thesis: final/Hairfall_Thesis.docx and final/Hairfall_Thesis.pdf.

1. builds the .docx (build_thesis.py)
2. converts it to PDF with LibreOffice
3. finds the page of every heading, table and figure in the PDF and writes pages.json
4. rebuilds with those page numbers in the table of contents and lists, and repeats until they are stable
Run:  python make_final.py
"""
import json
import os
import re
import subprocess
import sys

import fitz

BASE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.join(os.path.dirname(BASE), "final")
DOCX = os.path.join(FINAL, "Hairfall_Thesis.docx")
PDF = os.path.join(FINAL, "Hairfall_Thesis.pdf")
PAGES = os.path.join(BASE, "pages.json")


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


def norm(s):
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def build_and_convert():
    subprocess.run([sys.executable, os.path.join(BASE, "build_thesis.py")], check=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", DOCX, "--outdir", FINAL], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def entries():
    """Reads the entries written by build_thesis.py (entries.json)."""
    e = json.load(open(os.path.join(BASE, "entries.json"), encoding="utf-8"))
    return [tuple(x) for x in e["toc"]], e["tables"], e["figures"], e["appendices"]


def compute_pages():
    toc, tabs, figs, apps = entries()
    doc = fitz.open(PDF)
    texts = [norm(p.get_text()) for p in doc]
    n = len(texts)

    def find(needle, start, strict_after=None):
        lo = start if strict_after is None else strict_after + 1
        for i in range(lo, n):
            if needle in texts[i]:
                return i
        raise SystemExit(f"not found in PDF: {needle!r} from page {lo + 1}")

    front_break = {"Declaration", "Recommendation", "Certificate", "Acknowledgements", "Abbreviations/Acronyms",
                   "Units and Conversions", "ABSTRACT", "Table of Contents", "List of Tables", "List of Figures",
                   "List of Appendices"}
    found = {}
    cur = 1
    main_start = None
    for lvl, text in toc:
        if text in front_break:
            needle = "List of Abbreviations/Acronyms" if text == "Abbreviations/Acronyms" else text
            cur = find(needle, cur, strict_after=cur if found else None)
        elif text.startswith("CHAPTER"):
            num, title = text.split("  ", 1)
            cur = find(f"{num} {title}", cur, strict_after=cur)
            if main_start is None:
                main_start = cur
        elif text == "REFERENCES":
            cur = find("REFERENCES", cur, strict_after=cur)
        elif text.startswith("Appendix"):
            letter, title = text.split(": ", 1)
            cur = find(f"{letter.upper()} {title.upper()}", cur, strict_after=cur)
        else:
            cur = find(norm(text), cur)
        found[f"toc|{text}"] = cur

    def label(i):
        return str(i - main_start + 1) if i >= main_start else roman(i)

    pages = {k: label(v) for k, v in found.items()}
    cur = main_start
    for cap in tabs:
        head = cap.split(":")[0] + ":"
        cur = find(head, cur)
        pages[f"tab|{cap}"] = label(cur)
    cur = main_start
    for cap in figs:
        head = cap.split(":")[0] + ":"
        cur = find(head, cur)
        pages[f"fig|{cap}"] = label(cur)
    for t in apps:
        pages[f"app|{t}"] = pages[f"toc|{t}"]
    return pages, n, main_start


def main():
    if os.path.exists(PAGES):
        os.remove(PAGES)
    previous = None
    for attempt in range(1, 5):
        build_and_convert()
        pages, n, main_start = compute_pages()
        print(f"pass {attempt}: {n} PDF pages, Chapter 1 on PDF page {main_start + 1}")
        if pages == previous:
            break
        json.dump(pages, open(PAGES, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        previous = pages
    else:
        raise SystemExit("page numbers did not settle")
    print("final files:", DOCX, PDF)


if __name__ == "__main__":
    main()
