# Step 6a - TabPFN · 500
# TabPFN (pretrained foundation model, no training - rows are given as context) | context = 500
import time

from lab import SEED, SIZES, context, device, evaluate, load_split, predict_proba_batched
from tabpfn import TabPFNClassifier

SIZE = "500"
BATCH = 500  # test rows per prediction batch - lower this if the Mac runs out of memory
X_train, X_test, y_train, y_test = load_split()
X_ctx, y_ctx = context(X_train, y_train, SIZES[SIZE])
dev = device()
print(f"Context rows: {len(X_ctx):,} | Test rows: {len(X_test):,} | device: {dev}")

t = time.time()
model = TabPFNClassifier(device=dev, random_state=SEED, ignore_pretraining_limits=True)
model.fit(X_ctx, y_ctx)
fit_s = time.time() - t

t = time.time()
proba = predict_proba_batched(model, X_test, BATCH, tag=f"tabpfn_{SIZE}_{len(X_test)}")
pred_s = time.time() - t
evaluate("TabPFN", SIZE, len(X_ctx), y_test, proba, fit_s, pred_s, extra={"device": dev})
