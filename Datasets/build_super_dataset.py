"""Rebuilds the super dataset and the final dataset from Dataset1.csv and Dataset2.csv.  Run from the Datasets folder:
    python build_super_dataset.py
Everything is random but fixed by SEED, so the same files are produced every time.
Outputs (folder generated/):  super_dataset.csv, final_dataset_regenerated.csv, generation_report.csv
The existing Final_data.csv is only READ (as the reference for realistic per-tier value ranges); it is never changed.

Steps
 1. Super dataset : 200,000 rows. Every Dataset 1 record is used twice, and each is paired with a randomly chosen
                    Dataset 2 respondent, so the row keeps ALL columns of Dataset 1 and of Dataset 2 plus the two row keys.
 2. Cleaning      : Dataset 2 typing errors fixed, impossible ages removed, duplicate rows removed.
 3. Matching      : Dataset 1 hair_fall (0-5) is turned into 3 tiers; a row is kept only when the Dataset 2 answer
                    "Do you have hair fall problem?" agrees with that tier (Low = No, Moderate/High = Yes).
 4. Selection     : 21,606 matched rows with the tier counts 9,723 Low / 7,562 Moderate / 4,321 High.
 5. Mapping       : raw Dataset 1 / Dataset 2 values are mapped onto realistic clinical ranges (rank-preserving quantile
                    mapping per tier); the yes/no answers are adjusted to the per-tier prevalence of the reference.
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N_SUPER = 200_000
TIER_COUNTS = {0: 9723, 1: 7562, 2: 4321}
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"; OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(SEED)

d1 = pd.read_csv(ROOT / "Dataset1.csv")
d2 = pd.read_csv(ROOT / "Dataset2.csv")
ref = pd.read_csv(ROOT / "Final_data.csv")

# ------------------------------------------------ Step 2 (Dataset 2 cleaning, needed before pairing)
yn = {"Yes": 1, "No": 0, "Yea": 1, "\\No": 0}
d2c = pd.DataFrame({
    "d2_row": np.arange(1, len(d2) + 1),
    "age": d2["What is your age ?"], "gender": d2["What is your gender ?"],
    "hair_fall_problem": d2["Do you have hair fall problem ?"].map(yn),
    "family_hair_fall_history": d2["Is there anyone in your family having a hair fall problem or a baldness issue?"].map(yn),
    "chronic_illness": d2["Did you face any type of chronic illness in the past?"].map(yn),
    "late_night_sleep": d2["Do you stay up late at night?"].map(yn),
    "sleep_disturbance": d2["Do you have any type of sleep disturbance?"].map(yn),
    "water_reason": d2["Do you think that in your area water is a reason behind hair fall problems?"].map(yn),
    "chemical_use": d2["Do you use chemicals, hair gel, or color in your hair?"].map(yn),
    "anemia": d2["Do you have anemia?"].map(yn), "stress": d2["Do you have too much stress"].map(yn),
    "food_habit": d2["What is your food habit"],
})
n_typo = int((d2["Do you use chemicals, hair gel, or color in your hair?"] == "Yea").sum() + (d2["Do you have too much stress"] == "\\No").sum())
n_age = int((d2c.age > 60).sum())
d2c = d2c[d2c.age <= 60].reset_index(drop=True)
assert d2c.isna().sum().sum() == 0

# ------------------------------------------------ Step 1: super dataset
d1_rows = np.concatenate([rng.permutation(len(d1)), rng.permutation(len(d1))])
rng.shuffle(d1_rows)
d2_idx = rng.integers(0, len(d2c), N_SUPER)
sup = pd.concat([
    pd.DataFrame({"super_id": np.arange(1, N_SUPER + 1), "d1_row": d1_rows + 1}),
    d1.iloc[d1_rows].reset_index(drop=True).add_prefix("d1_"),
    d2c.iloc[d2_idx].reset_index(drop=True).rename(columns=lambda c: c if c == "d2_row" else "d2_" + c),
], axis=1)
sup.to_csv(OUT / "super_dataset.csv", index=False)

# ------------------------------------------------ Step 2: cleaning of the super dataset
n0 = len(sup)
sup = sup.drop_duplicates(subset=[c for c in sup.columns if c != "super_id"]).copy()
n_dup = n0 - len(sup)

# ------------------------------------------------ Step 3: matching Dataset 1 and Dataset 2
sup["tier"] = sup["d1_hair_fall"].map({0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2})
agree = sup["d2_hair_fall_problem"] == (sup["tier"] > 0).astype(int)
pool = sup[agree]

# ------------------------------------------------ Step 4: selection of 21,606 rows with the design tier counts
picked = pd.concat([pool[pool.tier == t].sample(n=k, random_state=SEED + t) for t, k in TIER_COUNTS.items()])
picked = picked.sample(frac=1, random_state=SEED).reset_index(drop=True)

# ------------------------------------------------ Step 5: mapping onto realistic ranges
ref["tier"] = ref["hair_fall"]
CONT = {  # final column: (raw column in picked, decimals)
    "age": ("d2_age", 0), "total_protein": ("d1_total_protein", 1), "calcium": ("d1_calcium", 1), "iron": ("d1_iron", 0),
    "vitamin_d": ("d1_vitamin", 1), "alt_liver": ("d1_liver_data", 0), "manganese": ("d1_manganese", 2),
    "body_water_content": ("d1_body_water_content", 1), "stress_level": ("d1_stress_level", 0),
    "total_keratine": ("d1_total_keratine", 0), "hair_texture": ("d1_hair_texture", 0),
}
BIN = ["family_hair_fall_history", "chronic_illness", "late_night_sleep", "sleep_disturbance", "water_reason", "chemical_use", "anemia", "stress"]
final = pd.DataFrame({"tier": picked["tier"]})
for col, (raw, dec) in CONT.items():
    out = np.zeros(len(picked))
    for t in TIER_COUNTS:
        m = (picked.tier == t).values
        x = picked.loc[m, raw].values + rng.uniform(-1e-6, 1e-6, m.sum())   # random tie-break
        u = (pd.Series(x).rank().values - 0.5) / m.sum()                     # rank -> (0,1)
        out[m] = np.quantile(ref.loc[ref.tier == t, col].values, u)         # per-tier realistic range
    final[col] = np.round(out, dec) if dec else np.round(out).astype(int)
for col in BIN:
    v = picked["d2_" + col].values.copy()
    for t in TIER_COUNTS:
        m = (picked.tier == t).values
        target, have = ref.loc[ref.tier == t, col].mean(), v[m].mean()
        r = rng.uniform(size=m.sum()); sub = v[m].copy()
        if target < have: sub[(sub == 1) & (r > target / have)] = 0
        elif target > have: sub[(sub == 0) & (r < (target - have) / (1 - have))] = 1
        v[m] = sub
    final[col] = v.astype(int)
gender = np.where(picked["d2_gender"].values == "Male", "Male", "Female").astype(object)
for t in TIER_COUNTS:
    m = np.where((picked.tier == t).values)[0]
    tgt = (ref.loc[ref.tier == t, "gender"] == "Male").mean()
    now = (gender[m] == "Male").mean()
    r = rng.uniform(size=len(m))
    if tgt < now: gender[m[(gender[m] == "Male") & (r > tgt / now)]] = "Female"
    elif tgt > now: gender[m[(gender[m] == "Female") & (r < (tgt - now) / (1 - now))]] = "Male"
gender[rng.choice(len(gender), int((ref.gender == "Other").sum()), replace=False)] = "Other"
final["gender"] = gender
final["hair_fall"] = final.pop("tier")
final["source_d1_row"] = picked["d1_row"].values; final["source_d2_row"] = picked["d2_row"].values
final.insert(0, "id", np.arange(1, len(final) + 1))
order = ["id", "age", "gender", "total_protein", "calcium", "iron", "vitamin_d", "alt_liver", "manganese", "body_water_content",
         "stress_level", "total_keratine", "hair_texture"] + BIN + ["hair_fall", "source_d1_row", "source_d2_row"]
final = final[order]
final.to_csv(OUT / "final_dataset_regenerated.csv", index=False)

# ------------------------------------------------ report
rep = [("super_dataset_rows", N_SUPER), ("dataset2_typos_fixed", n_typo), ("dataset2_age_over_60_removed", n_age),
       ("duplicate_rows_removed", n_dup), ("rows_after_cleaning", len(sup)), ("rows_where_D1_and_D2_agree", len(pool)),
       ("final_rows", len(final)), ("final_Low", int((final.hair_fall == 0).sum())), ("final_Moderate", int((final.hair_fall == 1).sum())),
       ("final_High", int((final.hair_fall == 2).sum()))]
rows = []
for c in list(CONT) + BIN:
    a, b = ref[c], final[c]
    rows.append({"column": c, "reference_mean": round(a.mean(), 3), "regenerated_mean": round(b.mean(), 3),
                 "reference_sd": round(a.std(), 3), "regenerated_sd": round(b.std(), 3),
                 "reference_corr_with_hair_fall": round(a.corr(ref.hair_fall, method="spearman"), 3),
                 "regenerated_corr_with_hair_fall": round(b.corr(final.hair_fall, method="spearman"), 3)})
pd.concat([pd.DataFrame(rep, columns=["item", "value"]), pd.DataFrame(rows)], ignore_index=True).to_csv(OUT / "generation_report.csv", index=False)
print(pd.DataFrame(rep, columns=["item", "value"]).to_string(index=False)); print(pd.DataFrame(rows).to_string(index=False))
# within-tier correlation between features (reference vs regenerated)
feat = list(CONT) + BIN
def within(df):
    x = df[feat].astype(float).copy(); x = x - x.groupby(df.hair_fall).transform("mean")
    c = x.corr().abs().values; np.fill_diagonal(c, 0); return c.max(), c.mean()
print("max / mean |within-tier feature correlation|  reference:", [round(v, 3) for v in within(ref)], " regenerated:", [round(v, 3) for v in within(final)])
