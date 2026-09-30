"""Compare Dataset1 (Kaggle), Dataset2 (Mendeley survey) and the final data.csv.

Run from the Datasets folder:  python comparison/dataset_comparison.py
Writes the CSV tables used in thesis section 3.2 into comparison/.
Nothing in the source files is changed.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
d1 = pd.read_csv(ROOT / "Dataset1.csv")
d2 = pd.read_csv(ROOT / "Dataset2.csv")
fin = pd.read_csv(ROOT / "Final_data.csv")

# ---------- 1. Overview ----------
overview = pd.DataFrame([
    ["Dataset 1", "Kaggle hair loss table", len(d1), d1.shape[1], "10 numeric biomarker / index columns + hair_fall (0-5)", "none"],
    ["Dataset 2", "Mendeley hair fall survey", len(d2), d2.shape[1], "13 questionnaire answers (Yes/No, age, gender, food habit)", "Timestamp (respondent name removed before use)"],
    ["Final data.csv", "Dataset used in this thesis", len(fin), fin.shape[1], "20 features + hair_fall (0-2)", "id (1 to 21,606)"],
], columns=["dataset", "what_it_is", "rows", "columns", "content", "row_identifier"])
overview.to_csv(HERE / "01_overview.csv", index=False)

# ---------- 2. Column linkage (feature concept level; there is no shared key) ----------
link = pd.DataFrame([
    ["age", "-", "What is your age ?", "Dataset 2", "years"],
    ["gender", "-", "What is your gender ?", "Dataset 2", "Female / Male / Other"],
    ["total_protein", "total_protein", "-", "Dataset 1", "g/dL"],
    ["calcium", "calcium", "-", "Dataset 1", "mg/dL"],
    ["iron", "iron", "-", "Dataset 1", "ug/dL"],
    ["vitamin_d", "vitamin", "-", "Dataset 1", "ng/mL"],
    ["alt_liver", "liver_data", "-", "Dataset 1", "U/L"],
    ["manganese", "manganese", "-", "Dataset 1", "ug/L"],
    ["body_water_content", "body_water_content", "-", "Dataset 1", "%"],
    ["stress_level", "stress_level", "-", "Dataset 1", "0-40 scale"],
    ["total_keratine", "total_keratine", "-", "Dataset 1", "0-100 score"],
    ["hair_texture", "hair_texture", "-", "Dataset 1", "0-100 score"],
    ["family_hair_fall_history", "-", "Is there anyone in your family having a hair fall problem or a baldness issue?", "Dataset 2", "0/1"],
    ["chronic_illness", "-", "Did you face any type of chronic illness in the past?", "Dataset 2", "0/1"],
    ["late_night_sleep", "-", "Do you stay up late at night?", "Dataset 2", "0/1"],
    ["sleep_disturbance", "-", "Do you have any type of sleep disturbance?", "Dataset 2", "0/1"],
    ["water_reason", "-", "Do you think that in your area water is a reason behind hair fall problems?", "Dataset 2", "0/1"],
    ["chemical_use", "-", "Do you use chemicals, hair gel, or color in your hair?", "Dataset 2", "0/1"],
    ["anemia", "-", "Do you have anemia?", "Dataset 2", "0/1"],
    ["stress", "-", "Do you have too much stress", "Dataset 2", "0/1"],
    ["hair_fall (target)", "hair_fall (0-5)", "Do you have hair fall problem ?", "Both (re-scaled to 3 tiers)", "0 Low, 1 Moderate, 2 High"],
], columns=["final_column", "dataset1_column", "dataset2_question", "concept_comes_from", "unit_or_coding"])
link.to_csv(HERE / "02_column_linkage.csv", index=False)

# ---------- 3. Dataset 1: value ranges and relationship with its own target ----------
rows = []
map1 = {"total_protein": "total_protein", "calcium": "calcium", "iron": "iron", "vitamin_d": "vitamin",
        "alt_liver": "liver_data", "manganese": "manganese", "body_water_content": "body_water_content",
        "stress_level": "stress_level", "total_keratine": "total_keratine", "hair_texture": "hair_texture"}
for f_col, c1 in map1.items():
    x1 = d1[c1]
    ks = stats.kstest((x1 - x1.min()) / (x1.max() - x1.min()), "uniform")
    r1 = stats.spearmanr(x1, d1["hair_fall"])[0]
    rf = stats.spearmanr(fin[f_col], fin["hair_fall"])[0]
    rows.append([f_col, x1.min(), x1.max(), round(x1.mean(), 2), fin[f_col].min(), fin[f_col].max(), round(fin[f_col].mean(), 2),
                 round(ks.statistic, 4), round(r1, 4), round(rf, 4)])
d1cmp = pd.DataFrame(rows, columns=["feature", "d1_min", "d1_max", "d1_mean", "final_min", "final_max", "final_mean",
                                    "d1_KS_vs_uniform", "d1_spearman_with_hair_fall", "final_spearman_with_hair_fall"])
d1cmp.to_csv(HERE / "03_dataset1_vs_final_biomarkers.csv", index=False)

# ---------- 4. Dataset 2 cleaning and comparison with the final data ----------
yn = {"Yes": 1, "No": 0, "Yea": 1, "\\No": 0}
q = {c: c for c in d2.columns}
d2c = pd.DataFrame({
    "age": d2["What is your age ?"],
    "male": (d2["What is your gender ?"] == "Male").astype(int),
    "hair_fall_problem": d2["Do you have hair fall problem ?"].map(yn),
    "family_hair_fall_history": d2["Is there anyone in your family having a hair fall problem or a baldness issue?"].map(yn),
    "chronic_illness": d2["Did you face any type of chronic illness in the past?"].map(yn),
    "late_night_sleep": d2["Do you stay up late at night?"].map(yn),
    "sleep_disturbance": d2["Do you have any type of sleep disturbance?"].map(yn),
    "water_reason": d2["Do you think that in your area water is a reason behind hair fall problems?"].map(yn),
    "chemical_use": d2["Do you use chemicals, hair gel, or color in your hair?"].map(yn),
    "anemia": d2["Do you have anemia?"].map(yn),
    "stress": d2["Do you have too much stress"].map(yn),
})
qc = {"rows_raw": len(d2d := d2), "age_outliers_over_60": int((d2c.age > 60).sum()),
      "typo_labels_fixed": int(d2["Do you use chemicals, hair gel, or color in your hair?"].eq("Yea").sum() +
                               d2["Do you have too much stress"].eq("\\No").sum())}
d2c = d2c[d2c.age <= 60].reset_index(drop=True)
qc["rows_after_cleaning"] = len(d2c)
qc["age_mean_d2"] = round(d2c.age.mean(), 1); qc["age_min_d2"] = int(d2c.age.min()); qc["age_max_d2"] = int(d2c.age.max())
qc["age_mean_final"] = round(fin.age.mean(), 1); qc["age_min_final"] = int(fin.age.min()); qc["age_max_final"] = int(fin.age.max())
pd.Series(qc).to_csv(HERE / "04_dataset2_quality.csv", header=["value"])

bin_feats = ["family_hair_fall_history", "chronic_illness", "late_night_sleep", "sleep_disturbance", "water_reason",
             "chemical_use", "anemia", "stress"]
fin_any = (fin["hair_fall"] > 0).astype(int)
rows = []
for c in bin_feats:
    p2, pf = d2c[c].mean(), fin[c].mean()
    # difference in feature prevalence between people with and without hair fall
    d2_diff = d2c.loc[d2c.hair_fall_problem == 1, c].mean() - d2c.loc[d2c.hair_fall_problem == 0, c].mean()
    fin_diff = fin.loc[fin_any == 1, c].mean() - fin.loc[fin_any == 0, c].mean()
    rows.append([c, round(100 * p2, 1), round(100 * pf, 1), round(100 * (pf - p2), 1),
                 round(100 * d2_diff, 1), round(100 * fin_diff, 1), int(np.sign(d2_diff) == np.sign(fin_diff))])
d2cmp = pd.DataFrame(rows, columns=["feature", "d2_prevalence_%", "final_prevalence_%", "final_minus_d2_pts",
                                    "d2_gap_hairfall_yes_minus_no_pts", "final_gap_hairfall_yes_minus_no_pts", "same_direction"])
extra = pd.DataFrame([["male_share", round(100 * d2c.male.mean(), 1), round(100 * (fin.gender == "Male").mean(), 1),
                       None, None, None, None],
                      ["hair_fall_any", round(100 * d2c.hair_fall_problem.mean(), 1), round(100 * fin_any.mean(), 1),
                       None, None, None, None]], columns=d2cmp.columns)
d2cmp = pd.concat([d2cmp, extra], ignore_index=True)
d2cmp.to_csv(HERE / "05_dataset2_vs_final_binary.csv", index=False)

print(overview.to_string(index=False)); print(); print(pd.Series(qc)); print(); print(d1cmp.to_string(index=False)); print(); print(d2cmp.to_string(index=False))
