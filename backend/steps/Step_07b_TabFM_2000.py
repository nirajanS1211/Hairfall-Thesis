# Step 7b - TabFM · 2000
# TabFM (Google foundation model, rows are given as context) | context = 2000
import time

from lab import SIZES, context, evaluate, load_split, predict_proba_batched
from tabfm import TabFMClassifier
from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1

SIZE = "2000"
BATCH = 100        # test rows per prediction batch - lower this if the Mac runs out of memory
X_train, X_test, y_train, y_test = load_split()
X_ctx, y_ctx = context(X_train, y_train, SIZES[SIZE])
print(f"Context rows: {len(X_ctx):,} | Test rows: {len(X_test):,}")

t = time.time()
model = TabFMClassifier(model=tabfm_v1.load(), n_estimators=1)
model.fit(X_ctx, y_ctx)
fit_s = time.time() - t

t = time.time()
proba = predict_proba_batched(model, X_test, BATCH, tag=f"tabfm_{SIZE}_{len(X_test)}")
pred_s = time.time() - t
evaluate("TabFM", SIZE, len(X_ctx), y_test, proba, fit_s, pred_s)
