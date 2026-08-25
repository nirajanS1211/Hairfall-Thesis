cb_model = CatBoostClassifier(iterations=1000, depth=4, learning_rate=0.1, early_stopping_rounds=50, loss_function="MultiClass", eval_metric="TotalF1", random_seed=RANDOM_STATE, verbose=0, l2_leaf_reg=3.0)
cb_model.fit(X_train, y_train, eval_set=(X_test, y_test), use_best_model=True)
y_pred_cb = cb_model.predict(X_test).flatten()
y_proba_cb = cb_model.predict_proba(X_test)