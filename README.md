# Hair Fall Risk Prediction — Demo App

CatBoost vs TabPFN vs TabFM comparison demo for the thesis: multi-tier hair fall risk
classification (Low / Moderate / High), SHAP explainability across all three models, a
MongoDB-backed prediction history, and an Analysis tab mirroring the Colab research
(dataset stats, correlations, evaluation metrics, context-size scaling).

## Architecture

- `backend/` — FastAPI JSON API, Python 3.11 (required by TabFM). Serves live
  predictions from three models:
  - **CatBoost** — local, retrained on the full 21,606-row dataset, live SHAP
    (TreeExplainer) per prediction.
  - **TabPFN** — Prior Labs' cloud API (`tabpfn-client`), needs `TABPFN_TOKEN`,
    ~5–20s per call, full 17,284-row context.
  - **TabFM** — Google Research's tabular foundation model, runs **fully locally**
    (PyTorch, CPU), no API key needed, but pulls ~5GB of pretrained weights from
    Hugging Face on first startup and is slow on CPU (~20–45s per prediction on a
    laptop with no GPU — it was benchmarked on a Colab T4 GPU originally). Uses a
    500-row context (its own experiments show it matches the other two's
    full-context accuracy with 34x less data).
  - Reads/writes MongoDB for prediction history + dataset analytics.
- `frontend/` — React (Vite) app with two tabs: Predict and Analysis. Talks to the
  backend purely over HTTP/JSON (`VITE_API_URL`).

## Run locally

**Backend** (needs Python 3.11+ — `brew install python@3.11` on macOS)
```bash
cd backend
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # paste TABPFN_TOKEN / MONGODB_URI in once you have them
uvicorn main:app --reload
```
Runs at http://127.0.0.1:8000 — docs at `/docs`. First startup downloads TabFM's
weights (~5GB, one-time, cached in `~/.cache/huggingface`) — expect the first
`uvicorn` start to take several minutes; it's instant on every start after that.

**Frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```
Runs at http://localhost:5173 and calls the backend at `http://localhost:8000` by
default (override via a `frontend/.env.local` with `VITE_API_URL=...`).

All three models degrade gracefully and independently — the app runs fully without
any of them configured:
- No `TABPFN_TOKEN` → TabPFN panel shows a clear "not configured" message.
- TabFM's package/weights fail to load → TabFM panel shows a clear "not configured"
  message, with the reason.
- No `MONGODB_URI` → prediction history and the Analysis tab's dataset stats fall
  back to reading the local dataset CSV directly.
- CatBoost never needs external config and always works.

## One-time setup scripts (`backend/scripts/`)

- `clean_dataset.py` — cleaning logic shared by everything else (reads
  `backend/data/raw_dataset.csv`, maps gender text → 0/1/2; `hair_fall` is already
  the 3-tier 0/1/2 label in the source CSV). Not run directly.
- `retrain_production.py` — retrains CatBoost on the **full** cleaned dataset (all
  21,606 rows) using the same hyperparameters as the evaluated model (depth=4,
  learning_rate=0.1), and exports the full-dataset TabPFN context CSVs. Already run
  once; outputs are in `backend/models/`. Re-run only if the source dataset changes.
- `seed_dataset.py` — one-time: loads the full cleaned dataset into MongoDB's `dataset`
  collection. Requires `MONGODB_URI` to be set. Run once after creating the Atlas
  cluster:
  ```bash
  cd backend && source venv/bin/activate && python scripts/seed_dataset.py
  ```

**Important:** the 80/20-split evaluation metrics in `backend/results.py` (accuracy,
precision, recall, F1, ROC-AUC, and all three pairwise McNemar's tests) are the
thesis's final reported numbers, straight from the Colab notebook's
`final_three_way_results.csv` / `final_statistical_analysis.csv`, and are untouched by
the production retrain — that retrain only affects the model that serves live
predictions, per standard "evaluate on holdout, deploy on everything" practice. TabFM
is evaluated at its own 500-row context per the thesis methodology; it does not get a
"full-context" row because that comparison wasn't run (see the Context-Size Scaling
section in the Analysis tab for the apples-to-apples comparisons that were run).

## Deployment note: TabFM and free-tier hosting

TabFM needs PyTorch + ~5GB of downloaded weights resident in memory. Most free-tier
hosting (e.g. Render's free plan, ~512MB RAM) **will not have enough memory or disk**
to run it. Options for a real deployment:
1. Deploy on a paid tier with enough RAM/disk (2GB+ RAM, a few GB disk).
2. Leave `tabfm` out of the deployed `requirements.txt` — the app already handles a
   missing/failed TabFM import gracefully (503 + a clear message), so CatBoost and
   TabPFN keep working fine without it.
This app was built and demoed locally on a Mac; if deploying the full 3-model stack,
budget accordingly.

## Environment variables

**Backend** (`backend/.env`)
- `TABPFN_TOKEN` — Prior Labs API token. Treat as sensitive (rotate if it's ever
  pasted somewhere shared).
- `MONGODB_URI` — MongoDB Atlas connection string (free M0 cluster is enough).
- `FRONTEND_ORIGINS` — comma-separated allowed CORS origins (defaults to the local
  Vite dev server; set to your deployed frontend URL in production).

**Frontend** (`frontend/.env.local` for dev, or the host's env var settings)
- `VITE_API_URL` — the backend's base URL.

## Deployment

`render.yaml` at the repo root defines both services as a Render Blueprint:
- `hairfall-backend` — Python 3.11 web service, root dir `backend/`.
- `hairfall-frontend` — static site, root dir `frontend/`, built with `npm run build`.

New → Blueprint on Render, point at this repo. Set `TABPFN_TOKEN` and `MONGODB_URI` in
the backend service's environment (marked `sync: false` so they're not committed). See
the TabFM note above before deploying the full 3-model stack on a free plan.

After the first deploy, update the `FRONTEND_ORIGINS` and `VITE_API_URL` placeholder
URLs in `render.yaml` to match the actual `*.onrender.com` URLs Render assigns, then
redeploy — the exact hostnames aren't known until the first deploy creates them.

The frontend can alternatively go on Vercel/Netlify — same idea, set `VITE_API_URL` as
a build-time env var pointing at the backend, and add that frontend's URL to the
backend's `FRONTEND_ORIGINS`.

MongoDB: Atlas free tier (M0), connection string goes in the backend's `MONGODB_URI`.

## Project layout

```
backend/
├── main.py                        FastAPI app: prediction, history, analysis endpoints
├── db.py                          MongoDB connection + collection helpers (graceful degrade)
├── features.py                    Field metadata: labels, units, validation bounds, grouping
├── results.py                     Fixed thesis evaluation metrics (3-way, from Colab)
├── requirements.txt
├── data/
│   └── raw_dataset.csv            source dataset (21,606 rows) used by clean_dataset.py
├── models/
│   ├── catboost_model.cbm                 evaluation model (80/20 split) — kept for reference
│   ├── catboost_model_production.cbm      production model (100% of data) — serves live predictions
│   ├── tabpfn_context_X.csv / _y.csv          original 80/20-split context — kept for debugging
│   ├── tabpfn_context_X_full.csv / _y_full.csv  full-dataset context — used for live TabPFN calls
│   ├── tabfm_500row_context_X.csv / _y.csv    500-row context — used for live TabFM calls
│   ├── feature_columns.json
│   └── class_names.json
├── scripts/
│   ├── clean_dataset.py           raw CSV -> model-ready schema
│   ├── retrain_production.py      one-time: trains catboost_model_production.cbm
│   └── seed_dataset.py            one-time: CSV -> MongoDB `dataset` collection
└── static/shap_reference/         static PNGs for the Analysis tab (SHAP + confusion
                                    matrices for all 3 models, CatBoost's training curve)

frontend/
├── package.json / vite.config.js
└── src/
    ├── App.jsx                    tab switcher + thesis header
    ├── api.js                     fetch wrappers for the backend
    ├── codeSnippets.js            Colab code snippets shown in the Analysis tab
    └── components/
        ├── PredictTab.jsx
        ├── AnalysisTab.jsx
        └── shared.jsx             RiskBadge, ConfidenceBars, Spinner, TimedSpinner, CodeBlock
```

## API

- `GET /api/meta` — feature form config, TabPFN/TabFM availability, SHAP image
  availability
- `POST /api/predict/catboost` — 20 features → prediction, per-class confidence, top-5
  SHAP factors, out-of-training-range warnings
- `POST /api/predict/tabpfn` — same input → prediction + confidence via TabPFN cloud
  (503 if `TABPFN_TOKEN` isn't configured)
- `POST /api/predict/tabfm` — same input → prediction + confidence via local TabFM
  (503 if TabFM failed to load)
- `POST /api/predictions/log` — logs one prediction (input + all three results) to
  MongoDB; called by the frontend once all three model calls have settled
- `GET /api/predictions/history?limit=&skip=` — paginated history, most recent first
  (503 if MongoDB isn't configured)
- `GET /api/analysis/dataset-summary` — row count, class distribution, feature stats,
  correlation matrix (from MongoDB if seeded, else the local CSV)
- `GET /api/analysis/results` — fixed thesis evaluation metrics: per-model metrics,
  three pairwise McNemar's tests, best CatBoost hyperparameters, context-size scaling
  data, matched 2,000-row context comparison
- `GET /health` — reports TabPFN/TabFM/MongoDB configuration status
