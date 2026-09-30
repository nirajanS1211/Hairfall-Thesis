# Run the steps on Google Colab

Same steps as `backend/kaggle/`, adapted for Colab (paths, secrets, data location, download). Generated from the Kaggle files by
`backend/kaggle_to_colab.py` — re-run it after editing a Kaggle file.

## Once per Colab notebook
1. **Runtime → Change runtime type → T4 GPU** (steps 5–8 need it for TabPFN/TabFM; steps 1–4 and 9–10 work on CPU).
2. **Secrets** (key icon in the left sidebar): add `HF_TOKEN` and `TABPFN_TOKEN`, and switch **Notebook access** on for both.
3. **Upload `data.csv`** to the Files panel (left sidebar → folder icon → upload). It must end up as `/content/data.csv`.

## Run a step
1. Paste the whole `Step_xx_..._colab.py` into one cell and run it.
2. When it finishes, the browser downloads `Step_xx_....zip` automatically.
3. Import it on the Mac: `cd backend && .venv/bin/python import_kaggle_run.py ~/Downloads/Step_xx_....zip`

## Steps that need earlier results
Later steps read the outputs of earlier ones (e.g. steps 5–8 need Step 4's `train.csv` / `test.csv`).
- Same session: nothing to do — everything stays in `/content/thesis_project/`.
- New session: upload the zips of the earlier steps (`Step_04_TrainTestSplit.zip`, …) to the Files panel. They are unpacked automatically.
  Step 9 needs the model steps 5–7, and Step 10 needs 5–8 (and 9 for the McNemar table).

## Tips
- Run one step per cell and don't paste an old copy above it — leftover cells can conflict.
- If `pip` upgrades torch, use **Runtime → Restart session** once and run the step again.
- Colab wipes `/content` when the session ends — download each step's zip before closing.
