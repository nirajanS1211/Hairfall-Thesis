# Hairfall Lab

## Setup on a new Mac (once)

```bash
# 1. Tools
brew install python@3.12 minio
brew install --cask orbstack
open -a OrbStack

# 2. Get the project
git clone <repo-url> Hairfall-Thesis
cd Hairfall-Thesis

# 3. Python environment
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate

# 4. Keys
cp .env.example .env
nano .env            # TABPFN_TOKEN=...   HF_TOKEN=... (optional)
cd ..

# 5. Dataset (not in git) - copy it to exactly this path
mkdir -p thesis_project/data
cp /path/to/data.csv thesis_project/data/data.csv

# 6. Model weights (TabFM, 6.5 GB, one time)
backend/.venv/bin/hf download google/tabfm-1.0.0-pytorch
```

TabPFN license (one time): https://ux.priorlabs.ai → Licenses → accept **TabPFN-3.5**.

## Run

```bash
./start.sh             # starts Postgres, MinIO and the app, opens http://127.0.0.1:8000
./start.sh --restart   # also restarts the app server (refused while a step is running)
./stop.sh              # stops everything cleanly - asks first if a step is still running
./backup.sh            # database + files -> backups/<date-time>/ (safe while running)
```

`start.sh` never restarts a running app, so a long training step is never killed by accident.

## The app

| Tab            | What it is for                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------ |
| **Risk check** | One person enters their lab results and answers → plain-language hair-fall risk, the main reasons (SHAP) and tips. *Developer* shows every model's probabilities and the calculation. Every check is saved (Postgres `predictions` + MinIO `predictions/<id>/record.json`). |
| **Notebook**   | The thesis pipeline, step by step: edit code, run, see output, figures and files, reopen any earlier run. |
| **Results**    | All models × training sizes: metrics, scaling charts, McNemar tests, confusion matrices, SHAP, CatBoost tuning, data quality. |
| **Dataset**    | The raw patient table with search, sorting and column statistics.                                |

Links can be shared: `/#predict/12` opens check 12, `?view=dev#predict/12` opens its developer view, `/#notebook/Step_06a_TabPFN_500` opens a step.

## Import runs made on Kaggle

The files in `backend/kaggle/` are the same steps packaged for a Kaggle GPU notebook. Each run downloads `Step_xx.zip`; import it with:

```bash
cd backend && .venv/bin/python import_kaggle_run.py ~/Downloads/Step_06a_TabPFN_500.zip
```

## Useful

```bash
tail -f backend/data/api.log                                   # server log
.venv/bin/hf download google/tabfm-1.0.0-pytorch               # resume a stuck download (run inside backend/)
```

| What             | Where                                           |
| ---------------- | ----------------------------------------------- |
| App              | http://127.0.0.1:8000                           |
| MinIO console    | http://127.0.0.1:9001 (minioadmin / minioadmin) |
| Step code        | `backend/steps/`                                |
| Results per step | `thesis_project/<Step>/`                        |
| Database + files | `backend/data/`                                 |
| Backups          | `backups/` (restore steps at the top of `backup.sh`) |

## Move results to another laptop

```bash
# old laptop
./stop.sh
tar czf hairfall-results.tgz thesis_project backend/data

# new laptop (inside the project folder, before ./start.sh)
tar xzf hairfall-results.tgz
```
