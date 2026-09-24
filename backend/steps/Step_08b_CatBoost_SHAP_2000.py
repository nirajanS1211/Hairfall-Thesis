# Step 8b - CatBoost SHAP · 2000
# CatBoost SHAP (TreeExplainer, exact) | model from Step 5b
import time

import shap
from catboost import CatBoostClassifier
from lab import SEED, load_split, shap_report, step_file

SIZE = "2000"
N_EXPLAIN = 1000  # test rows to explain
X_train, X_test, y_train, y_test = load_split()
model = CatBoostClassifier()
model.load_model(str(step_file("Step_05b_CatBoost_2000", "catboost.cbm")))
X_exp = X_test.sample(min(N_EXPLAIN, len(X_test)), random_state=SEED)

t = time.time()
shap_values = shap.TreeExplainer(model).shap_values(X_exp)
shap_report("CatBoost", SIZE, shap_values, X_exp, time.time() - t, extra={"explainer": "TreeExplainer"})
