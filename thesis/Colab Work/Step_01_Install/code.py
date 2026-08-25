import os
os.environ["NUMBA_DISABLE_JIT"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

!pip install -q catboost tabpfn tabfm shap statsmodels openpyxl

print("Environment configured, dependencies installed.")