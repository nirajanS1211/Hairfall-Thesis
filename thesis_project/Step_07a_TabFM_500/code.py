# Step 7a - TabFM · 500
# TabFM (Google foundation model, rows are given as context) | context = 500
import time

from lab import SIZES, context, evaluate, load_split, predict_proba_batched
from tabfm import TabFMClassifier
from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1

SIZE = "500"
BATCH = 100        # test rows per prediction batch - lower this if the Mac runs out of memory
TEST_ROWS = None   # None = full test set; set e.g. 500 for a quicker (stratified) run
X_train, X_test, y_train, y_test = load_split()
X_ctx, y_ctx = context(X_train, y_train, SIZES[SIZE])
if TEST_ROWS:
    X_test, y_test = context(X_test, y_test, TEST_ROWS)
print(f"Context rows: {len(X_ctx):,} | Test rows: {len(X_test):,}")

t = time.time()
model = TabFMClassifier(model=tabfm_v1.load(), n_estimators=1)
model.fit(X_ctx, y_ctx)
fit_s = time.time() - t

t = time.time()
proba = predict_proba_batched(model, X_test, BATCH)
pred_s = time.time() - t
evaluate("TabFM", SIZE, len(X_ctx), y_test, proba, fit_s, pred_s)
