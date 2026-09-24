# Step 3 - Validate against clinical reference ranges, encode -> Postgres + CSV
import numpy as np
import pandas as pd
from lab_db import load_df, save_df

df = load_df("hairfall_raw")
n0 = len(df)

# 1) Sanity checks (the raw file was already cleaned: labels standardised, no missing/duplicates)
assert set(df["gender"].unique()) <= {"Female", "Male", "Other"}, "unexpected gender label"
print("Gender:", df["gender"].value_counts().to_dict())
print("Missing values:", int(df.isna().sum().sum()), "| Duplicate rows:", int(df.drop(columns=["id"]).duplicated().sum()))
dups = 0

# 2) Clinical reference check. (normal_low, normal_high, impossible_low, impossible_high)
#    Values outside NORMAL are kept: abnormal biomarkers are exactly what predicts hair fall.
#    Only physiologically IMPOSSIBLE values (data errors) are dropped.
REF = {
    "total_protein":      (6.0, 8.3, 2.0, 12.0),     # g/dL   serum total protein
    "calcium":            (8.5, 10.5, 5.0, 14.0),    # mg/dL  serum calcium
    "iron":               (60, 170, 5, 500),         # ug/dL  serum iron
    "vitamin_d":          (25, 80, 1, 150),          # ng/mL  25-OH vitamin D (lab range 25-80)
    "alt_liver":          (7, 56, 1, 500),           # U/L    ALT
    "manganese":          (4, 15, 0.5, 60),          # ug/L   whole-blood manganese
    "body_water_content": (45, 65, 20, 85),          # %      total body water
}
rows = []
for c, (lo, hi, ilo, ihi) in REF.items():
    below, above = int((df[c] < lo).sum()), int((df[c] > hi).sum())
    impossible = int(((df[c] < ilo) | (df[c] > ihi)).sum())
    at_floor = int((df[c] == df[c].min()).sum())
    rows.append(dict(feature=c, below_normal=below, above_normal=above, impossible=impossible,
                     pct_abnormal=round(100 * (below + above) / len(df), 1), rows_at_minimum=at_floor))
    df = df[(df[c] >= ilo) & (df[c] <= ihi)]
report = pd.DataFrame(rows)
display(report)
print(f"Rows removed as physiologically impossible: {n0 - dups - len(df)}")

# 3) Encode + drop identifiers (id, full_name are personal / non-predictive)
df["gender"] = df["gender"].map({"Female": 0, "Male": 1, "Other": 2})
clean = df.drop(columns=["id", "full_name"]).reset_index(drop=True)
assert clean.isna().sum().sum() == 0
print("Clean shape:", clean.shape)

# 4) Save
save_df(clean, "hairfall_clean")
save_df(report, "hairfall_range_report")
clean.to_csv("outputs/hairfall_clean.csv", index=False)
report.to_csv("outputs/range_report.csv", index=False)
