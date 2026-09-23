
APPENDIX A
SOURCE CODE

The experiments were run in Python in cloud notebooks (Section 3.8.8). The code is given in the order in which it was run.

A.1 Environment setup

```python
import os
os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

!pip install -q catboost tabpfn tabfm shap statsmodels openpyxl
```

A.2 Data loading

```python
import os
import time
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations, product

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    confusion_matrix, classification_report, accuracy_score,
    precision_score, recall_score, f1_score, roc_auc_score
)

warnings.filterwarnings("ignore")
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

df = pd.read_csv("/kaggle/input/datasets/nirajanshahi/hairfall/data.csv")
print("Shape:", df.shape)
print("Duplicates:", df.duplicated().sum())
print("Missing values:\n", df.isnull().sum()[df.isnull().sum() > 0])
print("\nhair_fall distribution:\n", df["hair_fall"].value_counts().sort_index())
```

Output: Shape (21606, 23); Duplicates 0; no missing values; hair_fall counts 0 = 9,723, 1 = 7,562, 2 = 4,321.

A.3 Preprocessing

```python
df_model = df.drop(columns=["id", "full_name"]).copy()

gender_map = {"Female": 0, "F": 0, "Male": 1, "M": 1, "Other": 2, "O": 2}
df_model["gender"] = df_model["gender"].map(gender_map)

class_names = ["Low", "Moderate", "High"]
X = df_model.drop(columns=["hair_fall"])
y = df_model["hair_fall"]

print("Gender value counts:\n", df_model["gender"].value_counts())
print("\nX shape:", X.shape, "| y shape:", y.shape)
print("\nClass distribution:\n", y.value_counts().sort_index())
```

Output: X shape (21606, 20); gender counts 1 = 12,109, 0 = 9,485, 2 = 12.

A.4 Class distribution plot

```python
class_counts = y.value_counts().sort_index()
plt.figure(figsize=(7, 5))
ax = sns.barplot(x=class_names, y=class_counts.values,
                 palette=["#4F94D4", "#E8A33D", "#D45A47"], edgecolor="black")
for i, v in enumerate(class_counts.values):
    ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontweight="bold")
plt.xlabel("Hair Fall Risk Tier")
plt.ylabel("Number of Records")
plt.title("Class Distribution: Low vs Moderate vs High")
plt.tight_layout()
plt.savefig("class_distribution.png", dpi=150)
plt.show()
```

A.5 Train/test split

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=RANDOM_STATE
)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

print("Train shape:", X_train.shape, "| Test shape:", X_test.shape)
print("\nTrain class balance:\n", y_train.value_counts(normalize=True).sort_index())
print("\nTest class balance:\n", y_test.value_counts(normalize=True).sort_index())
```

Output: train (17,284, 20), test (4,322, 20); class proportions 0.450 / 0.350 / 0.200 in both.

A.6 CatBoost tuning and training

[CHECK BEFORE SUBMISSION: the grid-search loop below was written from the procedure described in Section 3.8.4. Replace it with the original notebook cell if it differs. Delete this note afterwards.]

```python
from catboost import CatBoostClassifier

param_grid = {"depth": [4, 6, 8], "learning_rate": [0.01, 0.03, 0.1]}
grid_rows = []

for depth, lr in product(param_grid["depth"], param_grid["learning_rate"]):
    fold_scores = []
    for tr_idx, va_idx in skf.split(X_train, y_train):
        fold_model = CatBoostClassifier(
            iterations=1000, depth=depth, learning_rate=lr,
            early_stopping_rounds=50, loss_function="MultiClass",
            eval_metric="TotalF1", random_seed=RANDOM_STATE,
            verbose=0, l2_leaf_reg=3.0
        )
        fold_model.fit(
            X_train.iloc[tr_idx], y_train.iloc[tr_idx],
            eval_set=(X_train.iloc[va_idx], y_train.iloc[va_idx]),
            use_best_model=True
        )
        fold_pred = fold_model.predict(X_train.iloc[va_idx]).flatten()
        fold_scores.append(f1_score(y_train.iloc[va_idx], fold_pred, average="macro"))
    grid_rows.append({"depth": depth, "learning_rate": lr,
                      "cv_macro_f1": np.mean(fold_scores)})

grid_results = (pd.DataFrame(grid_rows)
                .sort_values("cv_macro_f1", ascending=False)
                .reset_index(drop=True))
print(grid_results.to_string(index=False))

best_depth = int(grid_results.loc[0, "depth"])
best_lr = float(grid_results.loc[0, "learning_rate"])
print(f"\nBest: depth={best_depth}, learning_rate={best_lr}, "
      f"CV macro-F1={grid_results.loc[0, 'cv_macro_f1']:.4f}")

cb_model = CatBoostClassifier(
    iterations=1000, depth=best_depth, learning_rate=best_lr,
    early_stopping_rounds=50, loss_function="MultiClass",
    eval_metric="TotalF1", random_seed=RANDOM_STATE,
    verbose=0, l2_leaf_reg=3.0
)

t0 = time.time()
cb_model.fit(X_train, y_train, eval_set=(X_test, y_test), use_best_model=True)
cb_train_time = time.time() - t0

t0 = time.time()
y_pred_cb = cb_model.predict(X_test).flatten()
cb_predict_time = time.time() - t0
y_proba_cb = cb_model.predict_proba(X_test)
print(f"Training time: {cb_train_time:.2f}s | "
      f"Inference: {(cb_predict_time / len(X_test)) * 1000:.4f} ms/sample")
```

Result: best setting depth = 4, learning rate = 0.1, cross-validation macro-F1 = 0.7665. The final fit uses the test partition as the early-stopping evaluation set (see Section 5.2).

A.7 TabPFN inference

```python
import torch
from kaggle_secrets import UserSecretsClient

os.environ["TABPFN_TOKEN"] = UserSecretsClient().get_secret("TABPFN_TOKEN")

# Allow the pretrained checkpoint to load with recent PyTorch versions
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

from tabpfn import TabPFNClassifier

tabpfn_model = TabPFNClassifier(device="cuda", random_state=RANDOM_STATE)

t0 = time.time()
tabpfn_model.fit(X_train, y_train)
tabpfn_fit_time = time.time() - t0

t0 = time.time()
y_pred_tabpfn = tabpfn_model.predict(X_test)
tabpfn_predict_time = time.time() - t0
y_proba_tabpfn = tabpfn_model.predict_proba(X_test)
print(f"Fit time: {tabpfn_fit_time:.2f}s | "
      f"Inference: {(tabpfn_predict_time / len(X_test)) * 1000:.4f} ms/sample")
```

A.8 TabFM inference (500-row context)

```python
import sys
sys.modules["flax.nnx"] = None          # force the PyTorch implementation

from tabfm import TabFMClassifier
from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1_0_0

tabfm_base = tabfm_v1_0_0.load(model_type="classification")

np.random.seed(RANDOM_STATE)
context_idx = np.random.choice(X_train.index, size=500, replace=False)
X_train_context = X_train.loc[context_idx]
y_train_context = y_train.loc[context_idx]

tabfm_model = TabFMClassifier(model=tabfm_base, n_estimators=1)

t0 = time.time()
tabfm_model.fit(X_train_context, y_train_context)
tabfm_fit_time = time.time() - t0

t0 = time.time()
y_pred_tabfm = tabfm_model.predict(X_test)
tabfm_predict_time = time.time() - t0
y_proba_tabfm = tabfm_model.predict_proba(X_test)
print(f"Fit time: {tabfm_fit_time:.2f}s")
print(f"Predict time: {tabfm_predict_time / 60:.1f} min | "
      f"Per-sample: {(tabfm_predict_time / len(X_test)) * 1000:.2f} ms")
```

A.9 Evaluation

```python
def evaluate_model(name, y_true, y_pred, y_proba, cmap, filename):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    metrics = {
        "Model": name,
        "Accuracy": accuracy_score(y_true, y_pred),
        "Macro_Precision": precision_score(y_true, y_pred, average="macro"),
        "Macro_Recall": recall_score(y_true, y_pred, average="macro"),
        "Macro_F1": f1_score(y_true, y_pred, average="macro"),
        "ROC_AUC": roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro"),
    }
    print(f"\n{name}")
    print(classification_report(y_true, y_pred, target_names=class_names))
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap=cmap,
                xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title(f"{name} — Confusion Matrix")
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.show()
    return metrics

results_table = pd.DataFrame([
    evaluate_model("CatBoost", y_test, y_pred_cb, y_proba_cb, "Blues", "catboost_confusion_matrix.png"),
    evaluate_model("TabPFN", y_test, y_pred_tabpfn, y_proba_tabpfn, "Greens", "tabpfn_confusion_matrix.png"),
    evaluate_model("TabFM", y_test, y_pred_tabfm, y_proba_tabfm, "Oranges", "tabfm_confusion_matrix.png"),
])
results_table.insert(1, "Training_Context", [len(X_train), len(X_train), len(X_train_context)])
print(results_table.to_string(index=False))
results_table.to_csv("final_three_way_results.csv", index=False)
```

A.10 McNemar's test

```python
from statsmodels.stats.contingency_tables import mcnemar

y_true_values = y_test.values
correct = {
    "CatBoost": np.asarray(y_pred_cb) == y_true_values,
    "TabPFN": np.asarray(y_pred_tabpfn) == y_true_values,
    "TabFM": np.asarray(y_pred_tabfm) == y_true_values,
}

mcnemar_rows = []
for name_a, name_b in combinations(correct.keys(), 2):
    a, b = correct[name_a], correct[name_b]
    table = [
        [int(np.sum(a & b)),  int(np.sum(a & ~b))],
        [int(np.sum(~a & b)), int(np.sum(~a & ~b))],
    ]
    outcome = mcnemar(table, exact=False, correction=True)
    mcnemar_rows.append({
        "Comparison": f"{name_a} vs {name_b}",
        "McNemar_Statistic": outcome.statistic,
        "p_value": outcome.pvalue,
        "Significant": outcome.pvalue < 0.05,
    })

statistical_results = pd.DataFrame(mcnemar_rows)
print(statistical_results.to_string(index=False))
statistical_results.to_csv("final_statistical_analysis.csv", index=False)
```

A.11 Training context experiment

[CHECK BEFORE SUBMISSION: the original notebook had separate cells for the 100-, 500- and 2,000-row runs. The version below combines them into one procedure. Replace it with the original cells if they differ, and confirm that the 100-row run also drew its rows with seed 42. Delete this note afterwards.]

```python
from catboost import CatBoostClassifier
from tabpfn import TabPFNClassifier
from tabfm import TabFMClassifier

np.random.seed(RANDOM_STATE)
subset_idx = np.random.choice(X_test.index, size=500, replace=False)
X_test_500 = X_test.loc[subset_idx]
y_test_500 = y_test.loc[subset_idx]

eval_sets = {
    100: (X_test, y_test),
    500: (X_test, y_test),
    2000: (X_test_500, y_test_500),
}

def sample_context(size):
    np.random.seed(RANDOM_STATE)
    idx = np.random.choice(X_train.index, size=size, replace=False)
    return X_train.loc[idx], y_train.loc[idx]

def run_context(size):
    X_ctx, y_ctx = sample_context(size)
    X_eval, y_eval = eval_sets[size]
    rows = []

    cb = CatBoostClassifier(
        iterations=1000, depth=best_depth, learning_rate=best_lr,
        early_stopping_rounds=50, loss_function="MultiClass",
        eval_metric="TotalF1", random_seed=RANDOM_STATE,
        verbose=0, l2_leaf_reg=3.0
    )
    cb.fit(X_ctx, y_ctx, eval_set=(X_eval, y_eval), use_best_model=True)
    rows.append(("CatBoost", cb.predict(X_eval).flatten()))

    pfn = TabPFNClassifier(device="cuda", random_state=RANDOM_STATE)
    pfn.fit(X_ctx, y_ctx)
    rows.append(("TabPFN", pfn.predict(X_eval)))

    fm = TabFMClassifier(model=tabfm_base, n_estimators=1)
    fm.fit(X_ctx, y_ctx)
    rows.append(("TabFM", fm.predict(X_eval)))

    return [
        {"Context_Size": size, "Model": name, "Test_Set_Size": len(y_eval),
         "Accuracy": accuracy_score(y_eval, p),
         "Macro_F1": f1_score(y_eval, p, average="macro")}
        for name, p in rows
    ]

scaling_rows = []
for size in [100, 500, 2000]:
    t0 = time.time()
    scaling_rows.extend(run_context(size))
    print(f"Context {size} done in {(time.time() - t0) / 60:.1f} min")

scaling_results = pd.DataFrame(scaling_rows)
print(scaling_results.to_string(index=False))
scaling_results.to_csv("context_scaling_results.csv", index=False)

plot_df = scaling_results.pivot(index="Context_Size", columns="Model",
                                values="Accuracy").sort_index()
x_labels = [str(i) for i in plot_df.index]
plt.figure(figsize=(8, 5))
for model_name in ["CatBoost", "TabPFN", "TabFM"]:
    plt.plot(x_labels, plot_df[model_name] * 100, marker="o", label=model_name)
plt.xlabel("Training Context Size (rows)")
plt.ylabel("Accuracy (%)")
plt.title("Accuracy vs Training Context Size")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("context_scaling_accuracy.png", dpi=150)
plt.show()
```

A.12 SHAP explanations

[CHECK BEFORE SUBMISSION: the random seeds in the SHAP sampling and the 800-row TabPFN context were reconstructed. The Step 8b output line says "30 test samples, 800-row reduced context", but the original sampling cell had no fixed seed. Replace this block with the original notebook cells if they differ. Delete this note afterwards.]

```python
import shap

high_class_idx = 2

# --- CatBoost: exact TreeExplainer on the full test partition ---
explainer_cb = shap.TreeExplainer(cb_model)
shap_values_cb = explainer_cb.shap_values(X_test)

shap.summary_plot(shap_values_cb, X_test, class_names=class_names,
                  plot_type="bar", show=False)
plt.title("CatBoost — Global Feature Importance (SHAP)")
plt.tight_layout()
plt.savefig("catboost_shap_global_importance.png", dpi=150, bbox_inches="tight")
plt.show()

if isinstance(shap_values_cb, list):
    shap_vals_high_cb = shap_values_cb[high_class_idx]
else:
    shap_vals_high_cb = shap_values_cb[:, :, high_class_idx]

if isinstance(explainer_cb.expected_value, (list, np.ndarray)):
    base_value_cb = explainer_cb.expected_value[high_class_idx]
else:
    base_value_cb = explainer_cb.expected_value

def save_beeswarm_and_waterfall(prefix, title, values_high, data, base_value):
    shap.summary_plot(values_high, data, show=False)
    plt.title(f"{title} — SHAP Beeswarm (High Risk)")
    plt.tight_layout()
    plt.savefig(f"{prefix}_shap_beeswarm_high.png", dpi=150, bbox_inches="tight")
    plt.show()

    explanation = shap.Explanation(
        values=values_high[0], base_values=base_value,
        data=data.iloc[0], feature_names=data.columns.tolist()
    )
    shap.plots.waterfall(explanation, show=False)
    plt.title(f"{title} — Patient Waterfall")
    plt.tight_layout()
    plt.savefig(f"{prefix}_shap_waterfall_patient.png", dpi=150, bbox_inches="tight")
    plt.show()

save_beeswarm_and_waterfall("catboost", "CatBoost", shap_vals_high_cb, X_test, base_value_cb)

# --- TabPFN: KernelExplainer with a reduced context ---
np.random.seed(RANDOM_STATE)
small_idx = np.random.choice(X_train.index, size=800, replace=False)
X_train_small = X_train.loc[small_idx]
y_train_small = y_train.loc[small_idx]

tabpfn_small = TabPFNClassifier(device="cuda", random_state=RANDOM_STATE)
tabpfn_small.fit(X_train_small, y_train_small)

def tabpfn_predict_proba_small(X):
    return tabpfn_small.predict_proba(pd.DataFrame(X, columns=X_test.columns))

background_small = shap.sample(X_train_small, 15, random_state=RANDOM_STATE)
explainer_tabpfn_kernel = shap.KernelExplainer(tabpfn_predict_proba_small, background_small)

np.random.seed(RANDOM_STATE)
sample_idx_kernel = np.random.choice(X_test.index, size=30, replace=False)
X_test_sample_kernel = X_test.loc[sample_idx_kernel].reset_index(drop=True)

t0 = time.time()
shap_values_tabpfn = np.array(
    explainer_tabpfn_kernel.shap_values(X_test_sample_kernel, nsamples=100))
print(f"TabPFN SHAP time: {time.time() - t0:.1f}s | shape: {shap_values_tabpfn.shape}")

shap.summary_plot(shap_values_tabpfn[:, :, high_class_idx], X_test_sample_kernel,
                  plot_type="bar", show=False)
plt.title("TabPFN — Global Feature Importance (SHAP)")
plt.tight_layout()
plt.savefig("tabpfn_shap_global_importance.png", dpi=150, bbox_inches="tight")
plt.show()

save_beeswarm_and_waterfall(
    "tabpfn", "TabPFN", shap_values_tabpfn[:, :, high_class_idx],
    X_test_sample_kernel, explainer_tabpfn_kernel.expected_value[high_class_idx])

# --- TabFM: KernelExplainer with the 500-row context ---
def tabfm_predict_proba_padded(X):
    X_df = pd.DataFrame(X, columns=X_test.columns)
    if len(X_df) == 1:                      # single-row workaround
        X_padded = pd.concat([X_df, X_df], ignore_index=True)
        return tabfm_model.predict_proba(X_padded)[:1]
    return tabfm_model.predict_proba(X_df)

background_tabfm = shap.sample(X_train_context, 15, random_state=RANDOM_STATE)
explainer_tabfm_kernel = shap.KernelExplainer(tabfm_predict_proba_padded, background_tabfm)

np.random.seed(RANDOM_STATE)
sample_idx_tabfm = np.random.choice(X_test.index, size=20, replace=False)
X_test_sample_tabfm = X_test.loc[sample_idx_tabfm].reset_index(drop=True)

t0 = time.time()
shap_values_tabfm = np.array(
    explainer_tabfm_kernel.shap_values(X_test_sample_tabfm, nsamples=100))
print(f"TabFM SHAP time: {(time.time() - t0) / 60:.1f} min | shape: {shap_values_tabfm.shape}")

shap.summary_plot(shap_values_tabfm[:, :, high_class_idx], X_test_sample_tabfm,
                  plot_type="bar", show=False)
plt.title("TabFM — Global Feature Importance (SHAP)")
plt.tight_layout()
plt.savefig("tabfm_shap_global_importance.png", dpi=150, bbox_inches="tight")
plt.show()

save_beeswarm_and_waterfall(
    "tabfm", "TabFM", shap_values_tabfm[:, :, high_class_idx],
    X_test_sample_tabfm, explainer_tabfm_kernel.expected_value[high_class_idx])
```

A.13 Numba diagnostic test

```python
import numba

@numba.njit
def test_func(x):
    return x + 1

try:
    result = test_func(5)
    print("Numba JIT test: SUCCESS, result =", result)
except Exception as e:
    print("Numba JIT test: FAILED")
    print(e)
```


A.14 Descriptive analysis of the dataset

This code was run after the main experiments, on the same data file, to produce Table 3.3, Table 4.8 and Table 4.9 (Section 3.8.2).

```python
import pandas as pd
from scipy.stats import spearmanr

df = pd.read_csv("data.csv")
df["gender"] = df["gender"].map({"Female": 0, "F": 0, "Male": 1, "M": 1, "Other": 2, "O": 2})
X = df.drop(columns=["id", "full_name", "hair_fall"])
y = df["hair_fall"]

continuous = ["age", "total_protein", "calcium", "iron", "vitamin_d", "alt_liver",
              "manganese", "body_water_content", "stress_level", "total_keratine", "hair_texture"]
flags = [c for c in X.columns if c not in continuous and c != "gender"]

# Mean, standard deviation, minimum and maximum of each continuous predictor (Table 3.3)
print(df[continuous].describe().loc[["mean", "std", "min", "max"]].round(2).T)

# Mean of each continuous predictor in each risk tier (Table 4.8)
print(df.groupby("hair_fall")[continuous].mean().round(2).T)

# Spearman rank correlation of each predictor with the ordinal risk tier (Table 4.8)
rho = {c: spearmanr(df[c], y, nan_policy="omit")[0] for c in continuous + flags}
for name, value in sorted(rho.items(), key=lambda kv: -abs(kv[1])):
    print(f"{name:28s}{value:+.3f}")

# Proportion of records with each binary flag in each risk tier (Table 4.9)
print(df.groupby("hair_fall")[flags].mean().round(3).T)
```

A.15 Wilson score intervals for accuracy

This code was run after the main experiments to produce Table 4.6.

```python
from statsmodels.stats.proportion import proportion_confint

n_test = 4322
accuracies = {"CatBoost": 0.785053, "TabPFN": 0.785747, "TabFM": 0.778806}
for name, acc in accuracies.items():
    low, high = proportion_confint(round(acc * n_test), n_test, alpha=0.05, method="wilson")
    print(f"{name}: {acc*100:.2f}%  95% Wilson interval {low*100:.2f}% to {high*100:.2f}%")
```

A.16 Ordinal-aware measures

This code was run after the main experiments, on the confusion matrices of Fig. 4.1 to Fig. 4.3, to produce Table 4.4.

```python
import numpy as np

confusion = {
    "CatBoost": [[1672, 271, 2], [288, 1114, 111], [1, 256, 607]],
    "TabPFN":   [[1654, 290, 1], [268, 1108, 137], [0, 230, 634]],
    "TabFM":    [[1615, 328, 2], [250, 1157, 106], [1, 269, 594]],
}
weights = np.array([[(i - j) ** 2 / 4 for j in range(3)] for i in range(3)])

for name, cm in confusion.items():
    cm = np.array(cm, dtype=float)
    n = cm.sum()
    p_o = np.trace(cm) / n
    p_e = (cm.sum(0) * cm.sum(1)).sum() / n ** 2
    kappa = (p_o - p_e) / (1 - p_e)
    expected = np.outer(cm.sum(1), cm.sum(0)) / n
    qwk = 1 - (weights * cm).sum() / (weights * expected).sum()
    within_one = 1 - (cm[0, 2] + cm[2, 0]) / n
    mae = sum(abs(i - j) * cm[i, j] for i in range(3) for j in range(3)) / n
    print(f"{name}: kappa={kappa:.4f}  QWK={qwk:.4f}  within one tier={within_one*100:.2f}%  MAE={mae:.4f}")
```

APPENDIX B
ADDITIONAL FIGURES

![Fig. B.1: CatBoost training curve](../Colab Work/Step_05_CatBoost/catboost_training_curve.png)

![Fig. B.2: CatBoost confusion matrix with a 2,000-row training context (500 test records)](../Colab Work/Step_11_2000 Rows result/catboost_confusion_matrix_2000ctx.png)

![Fig. B.3: TabPFN confusion matrix with a 2,000-row training context (500 test records)](../Colab Work/Step_11_2000 Rows result/tabpfn_confusion_matrix_2000ctx.png)

![Fig. B.4: TabFM confusion matrix with a 2,000-row training context (500 test records)](../Colab Work/Step_11_2000 Rows result/tabfm_confusion_matrix_2000ctx.png)

![Fig. B.5: Accuracy of the three models with a 2,000-row training context](../Colab Work/Step_11_2000 Rows result/matched_2000ctx_chart.png)


APPENDIX C
RESULT TABLES FROM THE EXPERIMENTS

Table C.1: Full-context results (final_three_way_results.csv)

| Model | Training context | Accuracy | Macro-precision | Macro-recall | Macro-F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| CatBoost | 17,284 | 0.7851 | 0.7915 | 0.7662 | 0.7763 | 0.9189 |
| TabPFN | 17,284 | 0.7857 | 0.7875 | 0.7722 | 0.7787 | 0.9232 |
| TabFM | 500 | 0.7788 | 0.7904 | 0.7608 | 0.7715 | 0.9180 |

Table C.2: McNemar's test (final_statistical_analysis.csv)

| Comparison | Statistic | p-value | Significant |
|---|---|---|---|
| CatBoost vs TabPFN | 0.0147 | 0.9037 | No |
| CatBoost vs TabFM | 1.6528 | 0.1986 | No |
| TabPFN vs TabFM | 2.5798 | 0.1082 | No |

Table C.3: Reduced-context results on the 2,000-row run (matched_2000ctx_results.csv; 500 test records)

| Model | Training rows | Test records | Accuracy | Macro-F1 | ROC-AUC |
|---|---|---|---|---|---|
| CatBoost | 2,000 | 500 | 0.7440 | 0.7260 | 0.8865 |
| TabPFN | 2,000 | 500 | 0.7620 | 0.7508 | 0.9147 |
| TabFM | 2,000 | 500 | 0.7740 | 0.7631 | 0.9139 |

Table C.4: Per-class precision, recall and F1-score on the test partition

| Model | Class | Precision | Recall | F1-score | Support |
|---|---|---|---|---|---|
| CatBoost | Low | 0.85 | 0.86 | 0.86 | 1,945 |
| CatBoost | Moderate | 0.68 | 0.74 | 0.71 | 1,513 |
| CatBoost | High | 0.84 | 0.70 | 0.77 | 864 |
| TabPFN | Low | 0.86 | 0.85 | 0.86 | 1,945 |
| TabPFN | Moderate | 0.68 | 0.73 | 0.71 | 1,513 |
| TabPFN | High | 0.82 | 0.73 | 0.78 | 864 |
| TabFM | Low | 0.87 | 0.83 | 0.85 | 1,945 |
| TabFM | Moderate | 0.66 | 0.76 | 0.71 | 1,513 |
| TabFM | High | 0.85 | 0.69 | 0.76 | 864 |


APPENDIX D
DATASET DESCRIPTION AND SAMPLE RECORDS

The dataset (data.csv) has 21,606 records and 23 columns. The columns id and full_name were removed before modelling, and hair_fall is the target. The 20 predictors are listed in Table 3.2. Table D.1 shows the first three records of the dataset without the name column, with one column per record.

Table D.1: First three records of the dataset (full_name omitted; one column per record)

| Column | Record 1 | Record 2 | Record 3 |
|---|---|---|---|
| id | 1 | 2 | 3 |
| age | 39 | 26 | 34 |
| gender | Female | Male | Male |
| total_protein | 7.5 | 7.1 | 7.6 |
| calcium | 9.8 | 9.5 | 9.4 |
| iron | 56 | 124 | 114 |
| vitamin_d | 26.8 | 29.4 | 23.4 |
| alt_liver | 18 | 29 | 36 |
| manganese | 9.69 | 10.36 | 7.74 |
| body_water_content | 55.8 | 46.5 | 55.4 |
| stress_level | 23 | 31 | 19 |
| total_keratine | 50 | 18 | 42 |
| hair_texture | 48 | 76 | 62 |
| family_hair_fall_history | 0 | 1 | 1 |
| chronic_illness | 0 | 1 | 1 |
| late_night_sleep | 0 | 0 | 0 |
| sleep_disturbance | 0 | 1 | 1 |
| water_reason | 1 | 0 | 0 |
| chemical_use | 0 | 0 | 1 |
| anemia | 0 | 0 | 0 |
| stress | 0 | 1 | 0 |
| hair_fall | 0 | 2 | 1 |
