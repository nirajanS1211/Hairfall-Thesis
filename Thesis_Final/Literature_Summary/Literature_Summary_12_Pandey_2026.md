# Literature Summary 12: Pandey (devYRPauli) (2026), TabFM reproduction

**Citation:** Pandey, Y. (devYRPauli). (2026). *tabfm-evaluation* [Computer software]. GitHub. https://github.com/devYRPauli/tabfm-evaluation

**Verified:** Yes (repository exists, titled "TabFM: an independent reproduction and hardware study"). The real name behind the account is inferred from the repository's linked blog; check before printing.
**Setup:** Three machines (M1 Pro Mac, M4 Max Mac Studio, dual RTX 4090 workstation), 13 TabArena datasets (748 to 150,000 rows).
**Result:** Competitive against XGBoost, Random Forest, TabPFN. Four upstream defects: multi-GPU crash, dtype=object issue, row-order sensitivity in bfloat16, and out-of-memory above about 10,000 rows on a 24 GB GPU.
**Limitation:** A GitHub repository, not peer reviewed.
**Use in thesis:** Independent evidence and a warning about implementation limits for TabFM.
