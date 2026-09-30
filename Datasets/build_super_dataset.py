"""Rebuilds the super dataset and the final dataset from Dataset1.csv and Dataset2.csv.  Run from the Datasets folder:
    python build_super_dataset.py
Everything is random but fixed by SEED, so the same files are produced every time.
Outputs (folder generated/):  super_dataset.csv, final_dataset_regenerated.csv, generation_report.csv
The existing Final_data.csv is only READ (as the reference for realistic per-tier value ranges); it is never changed.

Steps
 0. Link fields   : Dataset 1 has no age or gender, so `age` and `gender` columns are added to it (Dataset1.csv is rewritten, the
                    original is kept in backup/Dataset1_original.csv). Each Dataset 1 record gets the age and gender of a
                    randomly chosen Dataset 2 respondent. Age and gender are the fields that link the two datasets.
 1. Super dataset : 200,000 rows. Every Dataset 1 record is used twice, and each is paired with a randomly chosen
                    Dataset 2 respondent OF THE SAME AGE AND GENDER (link_age, link_gender). The values are then RANDOMISED a little (small noise on numbers, a few yes/no
                    answers flipped), so the rows are new records and not exact copies. Each row keeps the row numbers
                    d1_row and d2_row (the row in Dataset1.csv / Dataset2.csv it came from) and, in the columns
                    d1src_* and d2src_*, the ORIGINAL source values, so the two can be compared directly.
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

d1 = pd.read_csv(ROOT / "backup" / "Dataset1_original.csv")   # original Kaggle file (Dataset1.csv is rewritten below with age and gender added)
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

# ------------------------------------------------ Step 1: super dataset (randomised copies with source keys)
NOISE_SD = 0.04      # standard deviation of the noise on Dataset 1 numbers, as a share of each column's range
HAIRFALL_SHIFT = 0.10  # chance that the Dataset 1 hair_fall value moves by one step
AGE_SD = 1.5         # noise on age in years
FLIP_YN = 0.05       # chance that a yes/no answer is flipped
FLIP_GENDER = 0.03   # chance that the gender is flipped
FLIP_FOOD = 0.05     # chance that the food habit is replaced by a random category
# link fields: Dataset 1 has no age or gender, so both are added, taken together from a random Dataset 2 respondent
d1 = d1.copy()
pick = rng.integers(0, len(d2c), len(d1))
d1.insert(0, "age", d2c.age.values[pick])
d1.insert(1, "gender", d2c.gender.values[pick])
d1.to_csv(ROOT / "Dataset1.csv", index=False)
d1_rows = np.concatenate([rng.permutation(len(d1)), rng.permutation(len(d1))])
rng.shuffle(d1_rows)
s1 = d1.iloc[d1_rows].reset_index(drop=True)
# pair every Dataset 1 record with a random Dataset 2 respondent of the same age and gender
d2_idx = np.empty(N_SUPER, dtype=int)
key1 = s1["age"].astype(str) + "|" + s1["gender"]
key2 = d2c["age"].astype(str) + "|" + d2c["gender"]
for k in key1.unique():
    m = np.where(key1.values == k)[0]
    d2_idx[m] = rng.choice(np.where(key2.values == k)[0], len(m))
s2 = d2c.iloc[d2_idx].reset_index(drop=True)
D1_NUM = [c for c in d1.columns if c not in ("hair_fall", "age", "gender")]
r1 = pd.DataFrame(index=range(N_SUPER))
r1["age"] = np.clip(np.round(s1["age"] + rng.normal(0, AGE_SD, N_SUPER)), 15, 60).astype(int)
g1 = s1["gender"].values.copy(); f1 = rng.uniform(size=N_SUPER) < FLIP_GENDER
g1[f1] = np.where(g1[f1] == "Male", "Female", "Male"); r1["gender"] = g1
for c in D1_NUM:
    lo, hi = d1[c].min(), d1[c].max()
    r1[c] = np.clip(np.round(s1[c] + rng.normal(0, NOISE_SD * (hi - lo), N_SUPER)), lo, hi).astype(int)
shift = rng.choice([-1, 0, 1], N_SUPER, p=[HAIRFALL_SHIFT / 2, 1 - HAIRFALL_SHIFT, HAIRFALL_SHIFT / 2])
r1["hair_fall"] = np.clip(s1["hair_fall"] + shift, 0, 5)
BINC = ["hair_fall_problem", "family_hair_fall_history", "chronic_illness", "late_night_sleep", "sleep_disturbance", "water_reason", "chemical_use", "anemia", "stress"]
r2 = pd.DataFrame(index=range(N_SUPER))
r2["age"] = np.clip(np.round(s2["age"] + rng.normal(0, AGE_SD, N_SUPER)), 15, 60).astype(int)
g = s2["gender"].values.copy(); f = rng.uniform(size=N_SUPER) < FLIP_GENDER
g[f] = np.where(g[f] == "Male", "Female", "Male"); r2["gender"] = g
for c in BINC:
    r2[c] = np.where(rng.uniform(size=N_SUPER) < FLIP_YN, 1 - s2[c].values, s2[c].values)
fh = s2["food_habit"].values.copy(); f = rng.uniform(size=N_SUPER) < FLIP_FOOD
fh[f] = rng.choice(np.array(sorted(set(d2c.food_habit))), f.sum()); r2["food_habit"] = fh
sup = pd.concat([
    pd.DataFrame({"super_id": np.arange(1, N_SUPER + 1), "d1_row": d1_rows + 1, "d2_row": s2["d2_row"].values, "link_age": s1["age"].values, "link_gender": s1["gender"].values}),
    r1.add_prefix("d1_"), r2.add_prefix("d2_"),
    s1.add_prefix("d1src_"), s2.drop(columns="d2_row").add_prefix("d2src_"),
], axis=1)
sup.to_csv(OUT / "super_dataset.csv", index=False)
# how much the randomised values differ from the source values (Dataset 1 / Dataset 2)
cmp_rows = []
for c in ["age"] + D1_NUM + ["hair_fall"]:
    a, b = sup["d1_" + c], sup["d1src_" + c]
    cmp_rows.append({"column": "d1_" + c, "compared_with": f"Dataset1.csv row d1_row, column {c}", "share_changed_%": round(100 * (a != b).mean(), 1),
                     "mean_abs_difference": round((a - b).abs().mean(), 2), "correlation_with_source": round(a.corr(b), 3)})
cmp_rows.append({"column": "d2_age", "compared_with": "Dataset2.csv row d2_row, age", "share_changed_%": round(100 * (sup.d2_age != sup.d2src_age).mean(), 1),
                 "mean_abs_difference": round((sup.d2_age - sup.d2src_age).abs().mean(), 2), "correlation_with_source": round(sup.d2_age.corr(sup.d2src_age), 3)})
cmp_rows.append({"column": "d1_gender", "compared_with": "Dataset1.csv row d1_row, gender", "share_changed_%": round(100 * (sup.d1_gender != sup.d1src_gender).mean(), 1), "mean_abs_difference": None, "correlation_with_source": None})
for c in ["gender"] + BINC + ["food_habit"]:
    cmp_rows.append({"column": "d2_" + c, "compared_with": f"Dataset2.csv row d2_row, {c}", "share_changed_%": round(100 * (sup["d2_" + c] != sup["d2src_" + c]).mean(), 1),
                     "mean_abs_difference": None, "correlation_with_source": None})
pd.DataFrame(cmp_rows).to_csv(OUT / "super_vs_sources_comparison.csv", index=False)

# ------------------------------------------------ Step 2: cleaning of the super dataset
n0 = len(sup)
sup = sup.drop_duplicates(subset=[c for c in sup.columns if c.startswith(("d1_", "d2_")) and "src" not in c]).copy()
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
