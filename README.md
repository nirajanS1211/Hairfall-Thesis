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
./start.sh      # starts everything and opens http://127.0.0.1:8000
./stop.sh       # stops everything (saved results are kept)
```

## Useful

```bash
tail -f backend/data/api.log                                   # server log
.venv/bin/hf download google/tabfm-1.0.0-pytorch               # resume a stuck download (run inside backend/)
```

| What | Where |
|---|---|
| UI | http://127.0.0.1:8000 |
| MinIO console | http://127.0.0.1:9001 (minioadmin / minioadmin) |
| Step code | `backend/steps/` |
| Results per step | `thesis_project/<Step>/` |
| Database + files | `backend/data/` |

## Move results to another laptop

```bash
# old laptop
./stop.sh
tar czf hairfall-results.tgz thesis_project backend/data

# new laptop (inside the project folder, before ./start.sh)
tar xzf hairfall-results.tgz
```
