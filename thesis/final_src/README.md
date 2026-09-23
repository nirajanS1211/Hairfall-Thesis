# How the single thesis file is made

`../Hairfall_Thesis.docx` is generated from the text files in this folder by `build_thesis.py`.

- `ch1.md` … `ch5.md`, `appendices.md`: the text. Citations are written as `[@key]` and are numbered
  automatically in order of first appearance (IEEE). Equations are `EQ[label]: latex` and are numbered
  automatically. `refs.json` holds the reference list. `assets/` holds the two figures drawn for the thesis.
- To rebuild after editing a text file:  `python build_thesis.py`
- All formatting is in Word STYLES (Home > Styles > Manage Styles), so font family, size and spacing can be
  changed in one place: Normal (body), Heading 1–4, Front Heading, Appendix Heading, Table Caption,
  Figure Caption, Table Text, Equation, Code, Reference, Cover 14/16/Title, etc.
- After opening the .docx in Word press Ctrl+A then F9 (update fields) to fill in the page numbers of the
  table of contents and of the lists of tables, figures and appendices.
- Yellow-highlighted text in [square brackets] is a placeholder to be replaced by you.
- Spine print (Appendix 2, 14 pt Times New Roman): title, author, year.
