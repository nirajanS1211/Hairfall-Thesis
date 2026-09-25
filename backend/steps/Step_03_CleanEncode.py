# Step 3 - Validate & encode
# Validate against clinical reference ranges and encode
import matplotlib.pyplot as plt
import pandas as pd
from lab import OUT, load_df

df = load_df("hairfall_dataset")
n0 = len(df)

# 1) Sanity checks
assert set(df["gender"].unique()) <= {"Female", "Male", "Other"}, "unexpected gender label"
print("Gender:", df["gender"].value_counts().to_dict())
print("Missing values:", int(df.isna().sum().sum()),
      "| Duplicate rows:", int(df.drop(columns=["id"]).duplicated().sum()))

# 2) Clinical reference check: (normal_low, normal_high, impossible_low, impossible_high)
#    Abnormal values are KEPT (they are what predicts hair fall); only impossible values are dropped.
REF = {
    "total_protein":      (6.0, 8.3, 2.0, 12.0),  # g/dL   serum total protein
    "calcium":            (8.5, 10.5, 5.0, 14.0), # mg/dL  serum calcium
    "iron":               (60, 170, 5, 500),      # ug/dL  serum iron
    "vitamin_d":          (25, 80, 1, 150),       # ng/mL  25-OH vitamin D
    "alt_liver":          (7, 56, 1, 500),        # U/L    ALT
    "manganese":          (4, 15, 0.5, 60),       # ug/L   whole-blood manganese
    "body_water_content": (45, 65, 20, 85),       # %      total body water
}
rows = []
for c, (lo, hi, ilo, ihi) in REF.items():
    below, above = int((df[c] < lo).sum()), int((df[c] > hi).sum())
    rows.append(dict(feature=c, normal_range=f"{lo}-{hi}", below_normal=below, above_normal=above,
                     impossible=int(((df[c] < ilo) | (df[c] > ihi)).sum()),
                     pct_abnormal=round(100 * (below + above) / len(df), 1)))
    df = df[(df[c] >= ilo) & (df[c] <= ihi)]
report = pd.DataFrame(rows)
display(report)
print(f"Rows removed as physiologically impossible: {n0 - len(df)}")

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.barh(report["feature"], report["pct_abnormal"], color="#2563eb")
ax.set_xlabel("% of patients outside the normal range"); ax.set_title("Biomarkers outside reference ranges")
fig.tight_layout(); fig.savefig(OUT / "range_check.png", dpi=150); plt.show()

# 3) Encode gender, drop identifiers (id, full_name are personal / non-predictive)
df["gender"] = df["gender"].map({"Female": 0, "Male": 1, "Other": 2})
clean = df.drop(columns=["id", "full_name"]).reset_index(drop=True)
assert clean.isna().sum().sum() == 0
print("Clean shape:", clean.shape, "| features:", clean.shape[1] - 1)

clean.to_csv(OUT / "hairfall_clean.csv", index=False)
report.to_csv(OUT / "range_report.csv", index=False)
