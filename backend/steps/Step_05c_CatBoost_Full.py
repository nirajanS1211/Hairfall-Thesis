# Step 5c - CatBoost · Full
# CatBoost | training size = Full
import itertools
import time

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lab import OUT, SEED, SIZES, context, evaluate, load_split
from sklearn.metrics import f1_score
from sklearn.model_selection import StratifiedKFold

SIZE = "Full"
X_train, X_test, y_train, y_test = load_split()
X_ctx, y_ctx = context(X_train, y_train, SIZES[SIZE])
print(f"Training rows: {len(X_ctx):,} | Test rows: {len(X_test):,}")

# 1) Grid search: depth x learning rate, 5-fold stratified CV on the training rows (test set untouched)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
grid, t0 = [], time.time()
for depth, lr in itertools.product([4, 6, 8], [0.01, 0.03, 0.1]):
    f1s, iters = [], []
    for tr, va in skf.split(X_ctx, y_ctx):
        m = CatBoostClassifier(iterations=1000, depth=depth, learning_rate=lr, l2_leaf_reg=3,
                               loss_function="MultiClass", early_stopping_rounds=50, random_seed=SEED, verbose=0)
        m.fit(X_ctx.iloc[tr], y_ctx.iloc[tr], eval_set=(X_ctx.iloc[va], y_ctx.iloc[va]))
        f1s.append(f1_score(y_ctx.iloc[va], m.predict(X_ctx.iloc[va]).ravel(), average="macro"))
        iters.append(m.get_best_iteration() + 1)
    grid.append({"depth": depth, "learning_rate": lr, "cv_macro_f1": round(np.mean(f1s), 4),
                 "cv_std": round(np.std(f1s), 4), "iterations": int(np.mean(iters))})
    print(f"depth={depth} lr={lr:<5} CV macro-F1 = {np.mean(f1s):.4f} +/- {np.std(f1s):.4f}", flush=True)
grid = pd.DataFrame(grid).sort_values("cv_macro_f1", ascending=False).reset_index(drop=True)
grid.to_csv(OUT / "grid_search.csv", index=False)
best = grid.iloc[0]
print(f"\nBest: depth={int(best.depth)} lr={best.learning_rate} iterations={int(best.iterations)} "
      f"(CV macro-F1 {best.cv_macro_f1:.4f}) | grid search took {time.time() - t0:,.0f}s")

# 2) Final model on all training rows with the best parameters
t = time.time()
model = CatBoostClassifier(iterations=int(best.iterations), depth=int(best.depth), learning_rate=float(best.learning_rate),
                           l2_leaf_reg=3, loss_function="MultiClass", random_seed=SEED, verbose=0)
model.fit(X_ctx, y_ctx)
fit_s = time.time() - t

# 3) Test
t = time.time()
proba = model.predict_proba(X_test)
pred_s = time.time() - t
model.save_model(str(OUT / "catboost.cbm"))
evaluate("CatBoost", SIZE, len(X_ctx), y_test, proba, fit_s, pred_s,
         extra={"depth": int(best.depth), "learning_rate": float(best.learning_rate),
                "iterations": int(best.iterations), "cv_macro_f1": float(best.cv_macro_f1)})
