# Step 8f - TabPFN SHAP · Full
# TabPFN SHAP (KernelExplainer, model-agnostic) | context = Full
import time

import numpy as np
import shap
from lab import SEED, SIZES, context, load_split, shap_report
import pandas as pd
from lab import device
from tabpfn import TabPFNClassifier

SIZE = "Full"
N_EXPLAIN = 30   # test rows to explain  (cost ~ N_EXPLAIN x NSAMPLES x BACKGROUND predictions)
NSAMPLES = 100
BACKGROUND = 10    # k-means summary of the context used as SHAP background
X_train, X_test, y_train, y_test = load_split()
X_ctx, y_ctx = context(X_train, y_train, SIZES[SIZE])
model = TabPFNClassifier(device=device(), random_state=SEED, ignore_pretraining_limits=True)
model.fit(X_ctx, y_ctx)


def predict_proba(a):
    X = pd.DataFrame(a, columns=X_ctx.columns)
    if len(X) == 1:  # some foundation models fail on a single row: pad and keep the first
        return model.predict_proba(pd.concat([X, X]))[:1]
    return model.predict_proba(X)


X_exp = X_test.sample(N_EXPLAIN, random_state=SEED)
background = shap.kmeans(X_ctx, BACKGROUND)
print(f"Explaining {N_EXPLAIN} rows, {NSAMPLES} samples each, {BACKGROUND} background points...", flush=True)
t = time.time()
shap_values = shap.KernelExplainer(predict_proba, background).shap_values(X_exp, nsamples=NSAMPLES)
shap_report("TabPFN", SIZE, shap_values, X_exp, time.time() - t,
            extra={"explainer": "KernelExplainer", "nsamples": NSAMPLES, "background": BACKGROUND})
