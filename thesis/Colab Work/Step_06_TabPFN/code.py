tabpfn_model = TabPFNClassifier(device="cuda", random_state=RANDOM_STATE)
tabpfn_model.fit(X_train, y_train)
y_pred_tabpfn = tabpfn_model.predict(X_test)
y_proba_tabpfn = tabpfn_model.predict_proba(X_test)