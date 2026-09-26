# Step 1 - Environment check
# Environment check (all packages are pre-installed in backend/.venv)
import os
import platform
import sys
from importlib.metadata import version

import torch

print("Python ", sys.version.split()[0])
print("System ", platform.platform())
print("RAM    ", round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1), "GB")
print("Device ", "mps (Apple GPU)" if torch.backends.mps.is_available() else "cpu")
print()
for pkg in ["pandas", "numpy", "scikit-learn", "statsmodels", "catboost", "tabpfn", "tabfm", "shap", "torch", "matplotlib"]:
    print(f"{pkg:14s} {version(pkg)}")
