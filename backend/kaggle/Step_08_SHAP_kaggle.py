# Step 8a-8i - SHAP for CatBoost / TabPFN / TabFM at 500 / 2000 / Full  (Kaggle GPU version)
# Same logic as backend/steps/Step_08*.py + workspace/lab.py shap_report, but standalone and on a CUDA GPU.
# Paste into ONE Kaggle notebook cell. Settings: Accelerator = GPU (T4), Internet = On. HF_TOKEN under Add-ons > Secrets.
# Add a dataset containing train.csv and test.csv (from thesis_project/Step_04_TrainTestSplit/).
# TabPFN and TabFM want different installs -> run them in SEPARATE notebooks: set MODELS = ["CatBoost"], ["TabPFN"] or ["TabFM"].
# Result: /kaggle/working/Step_08_SHAP_<models>.zip with one folder per step (auto-downloaded at the end).
#   Import on the Mac:  cd backend && .venv/bin/python import_kaggle_run.py ~/Downloads/Step_08_SHAP_TabFM.zip
MODELS = ["TabFM"]          # any of "CatBoost", "TabPFN", "TabFM"
SIZES_TO_RUN = ["500", "2000", "Full"]
# Time on a T4 (TabFM Full predicts ~0.8 s/row): CatBoost seconds | TabPFN ~1h total | TabFM ~2.5h for Full, <30 min for 500/2000.

import base64, glob, io, json, os, shutil, subprocess, sys, time

def pip(*a):
    subprocess.run([sys.executable, "-m", "pip", *a], check=True)

pip("install", "-q", "shap")
if "CatBoost" in MODELS:
    pip("install", "-q", "catboost")
if "TabPFN" in MODELS:
    pip("install", "-q", "tabpfn")
if "TabFM" in MODELS:
    pip("install", "-q", "tabfm[pytorch]==1.0.1")
    pip("uninstall", "-y", "-q", "flax")  # old Kaggle JAX/Flax crashes tabfm's import; without flax it uses PyTorch
    for k in [k for k in sys.modules if k == "tabfm" or k.startswith(("tabfm.", "flax"))]:
        del sys.modules[k]
    sys.modules["flax"] = None

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import torch
from sklearn.model_selection import train_test_split

try:
    from kaggle_secrets import UserSecretsClient
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    pass

SEED = 42
CLASS_NAMES = ["Low", "Moderate", "High"]
SIZES = {"500": 500, "2000": 2000, "Full": None}
STEP_IDS = {("CatBoost", "500"): "Step_08a_CatBoost_SHAP_500", ("CatBoost", "2000"): "Step_08b_CatBoost_SHAP_2000",
            ("CatBoost", "Full"): "Step_08c_CatBoost_SHAP_Full", ("TabPFN", "500"): "Step_08d_TabPFN_SHAP_500",
            ("TabPFN", "2000"): "Step_08e_TabPFN_SHAP_2000", ("TabPFN", "Full"): "Step_08f_TabPFN_SHAP_Full",
            ("TabFM", "500"): "Step_08g_TabFM_SHAP_500", ("TabFM", "2000"): "Step_08h_TabFM_SHAP_2000",
            ("TabFM", "Full"): "Step_08i_TabFM_SHAP_Full"}
# Best CatBoost params from Steps 5a/5b/5c grid search
CATBOOST = {"500": dict(depth=4, learning_rate=0.03, iterations=742),
            "2000": dict(depth=4, learning_rate=0.03, iterations=1000),
            "Full": dict(depth=4, learning_rate=0.1, iterations=849)}
# KernelExplainer settings (identical to the local steps)
KERNEL = {"TabPFN": dict(n_explain=30, nsamples=100, background=10),
          "TabFM": dict(n_explain=20, nsamples=100, background=5)}
N_EXPLAIN_CATBOOST = 1000
WORK = "/kaggle/working"
assert torch.cuda.is_available(), "No GPU - Notebook settings > Accelerator > GPU"
DEVICE = "cuda"


class Tee(io.TextIOBase):
    def __init__(self, *s): self.s = s
    def write(self, t):
        for x in self.s: x.write(t)
        return len(t)
    def flush(self):
        for x in self.s: x.flush()


def find(name):
    hits = glob.glob(f"/kaggle/input/**/{name}", recursive=True)
    assert hits, f"{name} not found under /kaggle/input - add the dataset with train.csv and test.csv"
    return hits[0]


tr, te = pd.read_csv(find("train.csv")), pd.read_csv(find("test.csv"))
X_train, y_train = tr.drop(columns="hair_fall"), tr["hair_fall"]
X_test = te.drop(columns="hair_fall")


def context(X, y, size):
    if size is None or size >= len(X):
        return X, y
    Xc, _, yc, _ = train_test_split(X, y, train_size=size, stratify=y, random_state=SEED)
    return Xc, yc


def shap_report(out, model_name, size_label, shap_values, X_explained, seconds, extra=None):
    sv = np.stack(shap_values, axis=-1) if isinstance(shap_values, list) else np.asarray(shap_values)
    if sv.ndim == 2:
        sv = sv[..., None]
    feats = list(X_explained.columns)
    imp = pd.DataFrame({"feature": feats, **{f"mean_abs_{c}": np.abs(sv[:, :, i]).mean(0) for i, c in enumerate(CLASS_NAMES)}})
    imp["mean_abs_all"] = imp[[f"mean_abs_{c}" for c in CLASS_NAMES]].mean(1)
    imp = imp.sort_values("mean_abs_all", ascending=False).reset_index(drop=True)
    imp.to_csv(f"{out}/shap_importance.csv", index=False)
    print(imp.round(4).to_string(index=False))
    fig, ax = plt.subplots(figsize=(7, 6))
    top = imp.head(15)[::-1]
    ax.barh(top["feature"], top["mean_abs_all"], color="#2563eb")
    ax.set_xlabel("mean |SHAP| (averaged over classes)")
    ax.set_title(f"{model_name} ({size_label}) - global feature importance")
    fig.tight_layout(); fig.savefig(f"{out}/shap_global_importance.png", dpi=150); plt.show()
    plt.figure()
    shap.summary_plot(sv[:, :, 2], X_explained, show=False, max_display=15)
    plt.title(f"{model_name} ({size_label}) - SHAP for High risk")
    plt.tight_layout(); plt.savefig(f"{out}/shap_beeswarm_high.png", dpi=150); plt.show()
    summary = {"model": model_name, "size": size_label, "rows_explained": int(len(X_explained)),
               "seconds": round(seconds, 1), "top_5": imp["feature"].head(5).tolist(), **(extra or {})}
    open(f"{out}/shap_summary.json", "w").write(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


# --- TabFM memory workarounds for the 15 GB T4 (exact same result, less memory; see Step_07c_TabFM_Full_kaggle.py) ---
if "TabFM" in MODELS:
    from tabfm import TabFMClassifier
    from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1
    _sdpa = torch.nn.functional.scaled_dot_product_attention
    Q_CHUNK = 1024

    def _chunked_sdpa(q, k, v, attn_mask=None, **kw):
        n = q.shape[-2]
        if n <= Q_CHUNK:
            return _sdpa(q, k, v, attn_mask=attn_mask, **kw)
        out = []
        for s in range(0, n, Q_CHUNK):
            m = attn_mask
            if m is not None and m.shape[-2] == n:
                m = m[..., s:s + Q_CHUNK, :]
            out.append(_sdpa(q[..., s:s + Q_CHUNK, :], k, v, attn_mask=m, **kw))
        return torch.cat(out, dim=-2)

    torch.nn.functional.scaled_dot_product_attention = _chunked_sdpa
if "TabPFN" in MODELS:
    from tabpfn import TabPFNClassifier


def make_model(name, size, X_ctx, y_ctx):
    if name == "TabPFN":
        m = TabPFNClassifier(device=DEVICE, random_state=SEED, ignore_pretraining_limits=True)
    else:
        net = tabfm_v1.load(device="cuda")
        for mod in net.modules():
            if hasattr(mod, "col_chunk_size"):
                mod.col_chunk_size = 4
        m = TabFMClassifier(model=net, n_estimators=1)
    m.fit(X_ctx, y_ctx)
    return m


def run(name, size):
    step = STEP_IDS[(name, size)]
    out = f"{WORK}/Step_08_SHAP_{'_'.join(MODELS)}/{step}"
    os.makedirs(out, exist_ok=True)
    log = io.StringIO()
    nb = sys.stdout
    sys.stdout = Tee(nb, log)
    try:
        print(f"===== {step} | GPU: {torch.cuda.get_device_name(0)} =====")
        X_ctx, y_ctx = context(X_train, y_train, SIZES[size])
        if name == "CatBoost":
            from catboost import CatBoostClassifier
            model = CatBoostClassifier(loss_function="MultiClass", l2_leaf_reg=3, random_seed=SEED, verbose=0, **CATBOOST[size])
            model.fit(X_ctx, y_ctx)  # same final-model recipe as Step 5a-5c
            X_exp = X_test.sample(min(N_EXPLAIN_CATBOOST, len(X_test)), random_state=SEED)
            t = time.time()
            sv = shap.TreeExplainer(model).shap_values(X_exp)
            shap_report(out, name, size, sv, X_exp, time.time() - t, {"explainer": "TreeExplainer"})
        else:
            cfg = KERNEL[name]
            model = make_model(name, size, X_ctx, y_ctx)

            def predict_proba(a, batch=100):
                X = pd.DataFrame(a, columns=X_ctx.columns)
                if len(X) == 1:
                    return model.predict_proba(pd.concat([X, X]))[:1]
                parts, i = [], 0
                while i < len(X):
                    try:
                        parts.append(model.predict_proba(X.iloc[i:i + batch]))
                    except torch.cuda.OutOfMemoryError:
                        torch.cuda.empty_cache()
                        batch = max(1, batch // 2)
                        continue
                    i += batch
                return np.vstack(parts)

            X_exp = X_test.sample(cfg["n_explain"], random_state=SEED)
            background = shap.kmeans(X_ctx, cfg["background"])
            print(f"Explaining {cfg['n_explain']} rows, {cfg['nsamples']} samples each, {cfg['background']} background points...", flush=True)
            t = time.time()
            sv = shap.KernelExplainer(predict_proba, background).shap_values(X_exp, nsamples=cfg["nsamples"])
            shap_report(out, name, size, sv, X_exp, time.time() - t,
                        {"explainer": "KernelExplainer", "nsamples": cfg["nsamples"], "background": cfg["background"]})
            del model
            torch.cuda.empty_cache()
    finally:
        sys.stdout = nb
        open(f"{out}/output.txt", "w").write(log.getvalue())


for name in MODELS:
    for size in SIZES_TO_RUN:
        run(name, size)

ROOT = f"{WORK}/Step_08_SHAP_{'_'.join(MODELS)}"
shutil.make_archive(ROOT, "zip", ROOT)
ZIP = ROOT + ".zip"
print(f"Done -> {ZIP}")

# Kaggle wipes the session when it closes: push the (small) zip to Downloads automatically + a manual link as fallback.
from IPython.display import HTML, FileLink, display
b64 = base64.b64encode(open(ZIP, "rb").read()).decode()
display(HTML(f'<a id="dl" download="{os.path.basename(ZIP)}" href="data:application/zip;base64,{b64}">Download {os.path.basename(ZIP)}</a>'
             '<script>document.getElementById("dl").click()</script>'))
display(FileLink(ZIP))
