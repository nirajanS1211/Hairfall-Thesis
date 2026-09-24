# Step 8c - CatBoost SHAP · Full
# CatBoost SHAP (TreeExplainer, exact) | model from Step 5c
import time

import shap
from catboost import CatBoostClassifier
from lab import SEED, load_split, shap_report, step_file

SIZE = "Full"
N_EXPLAIN = 1000  # test rows to explain
X_train, X_test, y_train, y_test = load_split()
model = CatBoostClassifier()
model.load_model(str(step_file("Step_05c_CatBoost_Full", "catboost.cbm")))
X_exp = X_test.sample(min(N_EXPLAIN, len(X_test)), random_state=SEED)

t = time.time()
shap_values = shap.TreeExplainer(model).shap_values(X_exp)
shap_report("CatBoost", SIZE, shap_values, X_exp, time.time() - t, extra={"explainer": "TreeExplainer"})
