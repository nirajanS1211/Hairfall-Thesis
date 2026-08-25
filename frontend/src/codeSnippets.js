export const CODE_SNIPPETS = {
  data_cleaning: `df = pd.read_csv("data.csv")

df_model = df.drop(columns=["id", "full_name"]).copy()
gender_map = {"Female": 0, "F": 0, "Male": 1, "M": 1, "Other": 2, "O": 2}
df_model["gender"] = df_model["gender"].map(gender_map)

X = df_model.drop(columns=["hair_fall"])
y = df_model["hair_fall"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=RANDOM_STATE
)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)`,

  catboost_training: `cb_model = CatBoostClassifier(
    iterations=1000, depth=4, learning_rate=0.1,
    early_stopping_rounds=50,
    loss_function="MultiClass", eval_metric="TotalF1",
    random_seed=RANDOM_STATE, verbose=0, l2_leaf_reg=3.0
)
cb_model.fit(
    X_train, y_train,
    eval_set=(X_test, y_test), use_best_model=True
)

y_pred_cb = cb_model.predict(X_test).flatten()
y_proba_cb = cb_model.predict_proba(X_test)`,

  catboost_confusion_matrix: `cm_cb = confusion_matrix(y_test, y_pred_cb)
sns.heatmap(cm_cb, annot=True, fmt="d", cmap="Blues",
            xticklabels=class_names, yticklabels=class_names)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("CatBoost — Confusion Matrix")`,

  catboost_training_curve: `evals_result = cb_model.get_evals_result()
plt.plot(evals_result["learn"]["MultiClass"], label="Train Loss")
plt.plot(evals_result["validation"]["MultiClass"], label="Validation Loss")
plt.xlabel("Boosting Iteration")
plt.ylabel("MultiClass Loss")
plt.title("CatBoost — Training vs Validation Loss")`,

  tabpfn_training: `from tabpfn import TabPFNClassifier

tabpfn_model = TabPFNClassifier(device="cuda", random_state=RANDOM_STATE)
tabpfn_model.fit(X_train, y_train)

y_pred_tabpfn = tabpfn_model.predict(X_test)
y_proba_tabpfn = tabpfn_model.predict_proba(X_test)

cm_tabpfn = confusion_matrix(y_test, y_pred_tabpfn)
sns.heatmap(cm_tabpfn, annot=True, fmt="d", cmap="Greens",
            xticklabels=class_names, yticklabels=class_names)`,

  tabfm_training: `from tabfm import TabFMClassifier
from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1_0_0

model = tabfm_v1_0_0.load()
tabfm_model = TabFMClassifier(model=model, n_estimators=1)
tabfm_model.fit(X_train_context, y_train_context)  # 500-row context

y_pred_tabfm = tabfm_model.predict(X_test)
y_proba_tabfm = tabfm_model.predict_proba(X_test)

cm_tabfm = confusion_matrix(y_test, y_pred_tabfm)
sns.heatmap(cm_tabfm, annot=True, fmt="d", cmap="Purples",
            xticklabels=class_names, yticklabels=class_names)`,

  model_comparison: `final_results = pd.DataFrame({
    "Model": ["CatBoost", "TabPFN", "TabFM"],
    "Training_Context": [17284, 17284, 500],
    "Accuracy": [cb_accuracy, tabpfn_accuracy, tabfm_accuracy],
    "Macro_Precision": [cb_precision, tabpfn_precision, tabfm_precision],
    "Macro_Recall": [cb_recall, tabpfn_recall, tabfm_recall],
    "Macro_F1": [cb_f1, tabpfn_f1, tabfm_f1],
    "ROC_AUC": [cb_roc_auc, tabpfn_roc_auc, tabfm_roc_auc],
})
final_results.to_csv("final_three_way_results.csv", index=False)`,

  catboost_shap: `explainer_cb = shap.TreeExplainer(cb_model)
shap_values_cb = explainer_cb.shap_values(X_test)

shap.summary_plot(shap_values_cb, X_test, class_names=class_names, plot_type="bar")

high_class_idx = 2
shap_vals_high = shap_values_cb[:, :, high_class_idx]
shap.summary_plot(shap_vals_high, X_test)

explanation = shap.Explanation(
    values=shap_vals_high[sample_idx],
    base_values=explainer_cb.expected_value[high_class_idx],
    data=X_test.iloc[sample_idx],
    feature_names=X_test.columns.tolist()
)
shap.plots.waterfall(explanation)`,

  tabpfn_shap: `def tabpfn_predict_proba_small(X):
    return tabpfn_shap_model.predict_proba(pd.DataFrame(X, columns=X_test.columns))

background_small = shap.sample(X_train_small, 15, random_state=RANDOM_STATE)
explainer_tabpfn_kernel = shap.KernelExplainer(tabpfn_predict_proba_small, background_small)
shap_values_tabpfn = explainer_tabpfn_kernel.shap_values(X_test_sample_kernel, nsamples=100)

shap.summary_plot(shap_values_tabpfn[:, :, 2], X_test_sample_kernel, plot_type="bar")`,

  tabfm_shap: `def tabfm_predict_proba_padded(X):
    X_df = pd.DataFrame(X, columns=X_test.columns)
    if len(X_df) == 1:
        X_padded = pd.concat([X_df, X_df], ignore_index=True)
        return tabfm_model.predict_proba(X_padded)[:1]
    return tabfm_model.predict_proba(X_df)

background_tabfm = shap.sample(X_train_context, 15, random_state=RANDOM_STATE)
explainer_tabfm_kernel = shap.KernelExplainer(tabfm_predict_proba_padded, background_tabfm)
shap_values_tabfm = explainer_tabfm_kernel.shap_values(X_test_sample_tabfm, nsamples=100)

shap.summary_plot(shap_values_tabfm[:, :, 2], X_test_sample_tabfm, plot_type="bar")`,

  mcnemar: `from statsmodels.stats.contingency_tables import mcnemar

def run_mcnemar(correct_a, correct_b, name_a, name_b):
    table = [
        [np.sum(correct_a & correct_b), np.sum(correct_a & ~correct_b)],
        [np.sum(~correct_a & correct_b), np.sum(~correct_a & ~correct_b)],
    ]
    result = mcnemar(table, exact=False, correction=True)
    print(f"{name_a} vs {name_b}: statistic={result.statistic:.4f}, p={result.pvalue:.4f}")
    return result

cb_correct = (y_pred_cb == y_test.values)
tabpfn_correct = (y_pred_tabpfn == y_test.values)
tabfm_correct = (y_pred_tabfm == y_test.values)

r1 = run_mcnemar(cb_correct, tabpfn_correct, "CatBoost", "TabPFN")
r2 = run_mcnemar(cb_correct, tabfm_correct, "CatBoost", "TabFM")
r3 = run_mcnemar(tabpfn_correct, tabfm_correct, "TabPFN", "TabFM")`,

  matched_2000_context: `context_idx = np.random.choice(X_train.index, size=2000, replace=False)
X_train_2000 = X_train.loc[context_idx]
y_train_2000 = y_train.loc[context_idx]

test_idx = np.random.choice(X_test.index, size=500, replace=False)
X_test_500 = X_test.loc[test_idx]
y_test_500 = y_test.loc[test_idx]

cb_model.fit(X_train_2000, y_train_2000, eval_set=(X_test_500, y_test_500), use_best_model=True)
tabpfn_model.fit(X_train_2000, y_train_2000)
tabfm_model.fit(X_train_2000, y_train_2000)

matched_2000_results = pd.DataFrame({
    "Model": ["CatBoost", "TabPFN", "TabFM"],
    "Context_Size": [2000, 2000, 2000],
    "Test_Set_Size": [500, 500, 500],
    "Accuracy": [cb_accuracy, tabpfn_accuracy, tabfm_accuracy],
    "Macro_F1": [cb_f1, tabpfn_f1, tabfm_f1],
    "ROC_AUC": [cb_roc_auc, tabpfn_roc_auc, tabfm_roc_auc],
})
matched_2000_results.to_csv("matched_2000ctx_results.csv", index=False)`,

  context_scaling: `for size in [100, 500]:
    idx = np.random.choice(X_train.index, size=size, replace=False)
    X_ctx, y_ctx = X_train.loc[idx], y_train.loc[idx]

    cb_ctx = CatBoostClassifier(depth=4, learning_rate=0.1, verbose=0)
    cb_ctx.fit(X_ctx, y_ctx, eval_set=(X_test, y_test), use_best_model=True)

    tabpfn_ctx = TabPFNClassifier(device="cuda", random_state=RANDOM_STATE)
    tabpfn_ctx.fit(X_ctx, y_ctx)
    # TabFM at matching context size computed the same way

context_scaling_comparison.to_csv("context_scaling_comparison.csv", index=False)`,
};
