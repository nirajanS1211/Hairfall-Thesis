"""Generate one paste-into-Kaggle file per step: backend/kaggle/Step_XX_<name>_kaggle.py.

Each file = Kaggle prelude + the local step code UNCHANGED + zip/auto-download epilogue. The prelude embeds
workspace/lab.py verbatim (evaluate, shap_report, context ...) and only swaps the environment bits (Postgres -> data.csv,
Mac paths -> /kaggle/working, MPS -> CUDA, T4 memory workarounds). Edit a step or lab.py, then re-run:
    python3 backend/kaggle/build_kaggle_steps.py
"""
import re
from pathlib import Path

HERE = Path(__file__).parent
STEPS = HERE.parent / "steps"
LAB = (HERE.parent / "workspace" / "lab.py").read_text()
assert "'''" not in LAB

PRELUDE = r'''
import base64, glob, io, os, shutil, subprocess, sys, time, types
from pathlib import Path

STEP = "@STEP@"
NEEDS = @NEEDS@   # extra pip packages for this step
GPU = @GPU@       # foundation-model steps need the GPU (T4)


def _pip(*a):
    subprocess.run([sys.executable, "-m", "pip", *a], check=True)


if NEEDS:
    _pip("install", "-q", *NEEDS)
if any(n.startswith("tabfm") for n in NEEDS):
    # Kaggle's old JAX/Flax crashes tabfm's import (it expects ImportError, gets AttributeError); without flax tabfm
    # falls back to its PyTorch backend, exactly like the Mac.
    _pip("uninstall", "-y", "-q", "flax")
    for k in [k for k in sys.modules if k == "tabfm" or k.startswith(("tabfm.", "flax"))]:
        del sys.modules[k]
    sys.modules["flax"] = None

import numpy as np
import pandas as pd
import torch
from IPython.display import display  # steps call display(): a notebook builtin, imported so plain scripts work too

if GPU:
    assert torch.cuda.is_available(), "No GPU - Notebook settings > Accelerator > GPU"

try:
    from kaggle_secrets import UserSecretsClient
    os.environ["HF_TOKEN"] = UserSecretsClient().get_secret("HF_TOKEN")
except Exception:
    pass

# ---- everything the step writes goes to /kaggle/working/thesis_project/<STEP>/ (same layout as the Mac) ----
PROJECT = Path("/kaggle/working/thesis_project")
OUT = PROJECT / STEP
OUT.mkdir(parents=True, exist_ok=True)
# results of earlier steps (added as a Kaggle dataset) are copied in, so step_file()/PROJECT.glob() just work
for d in glob.glob("/kaggle/input/**/Step_*", recursive=True):
    if os.path.isdir(d) and not (PROJECT / os.path.basename(d)).exists() and os.path.basename(d) != STEP:
        shutil.copytree(d, PROJECT / os.path.basename(d))

# ---- lab.py, verbatim, as an importable module `lab` ----
LAB_SRC = @LAB@
sys.modules.setdefault("psycopg", types.ModuleType("psycopg"))  # lab.py imports it; Kaggle reads data.csv instead
lab = types.ModuleType("lab")
lab.__file__ = "/kaggle/working/lab.py"
exec(compile(LAB_SRC, "lab.py", "exec"), lab.__dict__)
sys.modules["lab"] = lab
lab.PROJECT, lab.OUT = PROJECT, OUT
lab.test_rows = lambda: None                  # whole test set, like the local test_rows.txt = all
lab.device = lambda: "cuda" if torch.cuda.is_available() else "cpu"


def _load_df(table):
    hits = glob.glob("/kaggle/input/**/data.csv", recursive=True)
    assert hits, "data.csv not found under /kaggle/input - add a dataset containing data.csv"
    return pd.read_csv(hits[0])


lab.load_df = _load_df

# ---- T4 (15 GB) memory workarounds: identical results, less memory ----
def _chunk_predict(cls, chunk):  # predict in slices; halve the slice on CUDA out-of-memory
    orig = cls.predict_proba

    def predict_proba(self, X, *a, **k):
        parts, i, b = [], 0, chunk
        while i < len(X):
            try:
                parts.append(orig(self, X.iloc[i:i + b] if hasattr(X, "iloc") else X[i:i + b], *a, **k))
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                if b == 1:
                    raise
                b = max(1, b // 2)
                print(f"  GPU out of memory -> batch size {b}", flush=True)
                continue
            i += b
        return np.vstack(parts)

    cls.predict_proba = predict_proba


if any(n.startswith("tabpfn") for n in NEEDS):
    from tabpfn import TabPFNClassifier
    _chunk_predict(TabPFNClassifier, 500)

if any(n.startswith("tabfm") for n in NEEDS):
    from tabfm import TabFMClassifier
    from tabfm import tabfm_v1_0_0_pytorch as tabfm_v1
    _chunk_predict(TabFMClassifier, 100)
    # no flash attention on the T4 -> SDPA builds the full n x n score matrix. Splitting the queries into chunks gives
    # the exact same result (softmax is per query row) with far less memory.
    _sdpa = torch.nn.functional.scaled_dot_product_attention

    def _chunked_sdpa(q, k, v, attn_mask=None, **kw):
        n, Q = q.shape[-2], 1024
        if n <= Q:
            return _sdpa(q, k, v, attn_mask=attn_mask, **kw)
        out = []
        for s in range(0, n, Q):
            m = attn_mask[..., s:s + Q, :] if attn_mask is not None and attn_mask.shape[-2] == n else attn_mask
            out.append(_sdpa(q[..., s:s + Q, :], k, v, attn_mask=m, **kw))
        return torch.cat(out, dim=-2)

    torch.nn.functional.scaled_dot_product_attention = _chunked_sdpa
    _tabfm_load = tabfm_v1.load

    def _load(*a, **k):
        k.setdefault("device", "cuda")  # load() defaults to CPU!
        net = _tabfm_load(*a, **k)
        for mod in net.modules():
            if hasattr(mod, "col_chunk_size"):
                mod.col_chunk_size = 4  # default 16 feature-columns at once -> too much memory on a T4
        return net

    tabfm_v1.load = _load


class _Tee(io.TextIOBase):  # everything printed is also saved to output.txt
    def __init__(self, *s): self.s = s
    def write(self, t):
        for x in self.s: x.write(t)
        return len(t)
    def flush(self):
        for x in self.s: x.flush()


_LOG, _NB_STDOUT = io.StringIO(), sys.stdout
sys.stdout = _Tee(_NB_STDOUT, _LOG)
if GPU:
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# ======================= step code (unchanged from backend/steps/@STEP@.py) =======================
'''

EPILOGUE = r'''
# ======================= end of step code =======================
sys.stdout = _NB_STDOUT
(OUT / "output.txt").write_text(_LOG.getvalue())
shutil.make_archive(f"/kaggle/working/{STEP}", "zip", root_dir=PROJECT, base_dir=STEP)
ZIP = f"/kaggle/working/{STEP}.zip"
print(f"Done -> {ZIP}   (import on the Mac: cd backend && .venv/bin/python import_kaggle_run.py ~/Downloads/{STEP}.zip)")

# Kaggle wipes the session's files when it closes, so push the zip to your computer's Downloads folder automatically
# (embedded in the page) + a manual link as a fallback.
from IPython.display import HTML, FileLink, display
b64 = base64.b64encode(open(ZIP, "rb").read()).decode()
display(HTML(f'<a id="dl" download="{STEP}.zip" href="data:application/zip;base64,{b64}">Download {STEP}.zip</a>'
             '<script>document.getElementById("dl").click()</script>'))
display(FileLink(ZIP))
'''


def needs_for(body: str):
    def uses(pkg):
        return re.search(rf"^\s*(import|from)\s+{pkg}\b", body, re.M)
    pip = {"catboost": "catboost", "shap": "shap", "tabpfn": "tabpfn", "tabfm": "tabfm[pytorch]==1.0.1"}
    return [v for k, v in pip.items() if uses(k)]


def inputs_note(step: str, body: str):
    if step.startswith(("Step_02", "Step_03")): return ["data.csv (thesis_project/data/data.csv)"]
    if step.startswith("Step_01"): return []
    if step.startswith("Step_09"): return ["Step_05a-c, Step_06a-c, Step_07a-c folders (predictions.csv)"]
    if step.startswith("Step_10"): return ["Step_05a-c, Step_06a-c, Step_07a-c (metrics.json), optionally Step_08* (shap_summary.json)"]
    return sorted(set(re.findall(r'step_file\("(Step_\w+)"', body))) or ["Step_04_TrainTestSplit (train.csv, test.csv)"]


for f in sorted(STEPS.glob("Step_*.py")):
    step, body = f.stem, f.read_text()
    if step.startswith("Step_01"):  # environment check: Kaggle has no MPS, and tabpfn/tabfm are only installed by their own steps
        body = body.replace('"mps (Apple GPU)" if torch.backends.mps.is_available() else "cpu"',
                            'torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"')
        body = body.replace('    print(f"{pkg:14s} {version(pkg)}")',
                            '    try:\n        print(f"{pkg:14s} {version(pkg)}")\n    except Exception:\n        print(f"{pkg:14s} (not installed on this Kaggle image)")')
    needs = needs_for(body)
    gpu = any(n.startswith(("tabpfn", "tabfm")) for n in needs)
    head = [f"# {step} - Kaggle version (generated by build_kaggle_steps.py; step code below is the local step unchanged)",
            "# Paste into ONE Kaggle notebook cell and Run.",
            f"# Settings: Accelerator = {'GPU (T4)' if gpu else 'None (CPU is fine)'}, Internet = {'On' if needs else 'Off is fine'}."
            + (" HF_TOKEN under Add-ons > Secrets." if gpu else ""),
            f"# Needs as a Kaggle dataset (Add Input): {'; '.join(inputs_note(step, body)) or 'nothing'}.",
            f"# Result: /kaggle/working/{step}.zip (downloads automatically) -> import on the Mac with import_kaggle_run.py."]
    prelude = (PRELUDE.replace("@LAB@", "r'''" + LAB + "'''").replace("@STEP@", step)
               .replace("@NEEDS@", repr(needs)).replace("@GPU@", repr(gpu)))
    out = HERE / f"{step}_kaggle.py"
    out.write_text("\n".join(head) + "\n" + prelude + body.rstrip() + "\n" + EPILOGUE)
    print(f"{out.name:48s} needs={needs} gpu={gpu}")
