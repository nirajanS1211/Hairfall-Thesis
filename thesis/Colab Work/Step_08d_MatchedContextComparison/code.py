# Matched 500-row context: CatBoost, TabPFN, TabFM
cb_500.fit(X_train_500, y_train_500, eval_set=(X_test, y_test), use_best_model=True)
tabpfn_500.fit(X_train_500, y_train_500)
# TabFM at 500 rows already computed in Step 7