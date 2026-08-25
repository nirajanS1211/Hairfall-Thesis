tabfm_model = TabFMClassifier(model=model, n_estimators=1)
tabfm_model.fit(X_train_context, y_train_context)  # 500-row context
y_pred_tabfm = tabfm_model.predict(X_test)
y_proba_tabfm = tabfm_model.predict_proba(X_test)