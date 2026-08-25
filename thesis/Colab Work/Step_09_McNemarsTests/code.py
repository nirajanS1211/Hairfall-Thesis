r1 = run_mcnemar(cb_correct, tabpfn_correct, "CatBoost", "TabPFN")
r2 = run_mcnemar(cb_correct, tabfm_correct, "CatBoost", "TabFM")
r3 = run_mcnemar(tabpfn_correct, tabfm_correct, "TabPFN", "TabFM")