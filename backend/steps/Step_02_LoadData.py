# Step 2 - Load dataset
# Load the dataset (loaded into the local Postgres automatically at startup)
import matplotlib.pyplot as plt
from lab import CLASS_NAMES, OUT, load_df

df_raw = load_df("hairfall_dataset")
print("Shape:", df_raw.shape)
print("Missing values:", int(df_raw.isna().sum().sum()))
print("\nColumn types:\n" + df_raw.dtypes.to_string())
display(df_raw.head())

counts = df_raw["hair_fall"].value_counts().sort_index()
print("\nTarget distribution:")
for k, v in counts.items():
    print(f"  {k} {CLASS_NAMES[k]:9s} {v:6,d}  ({v / len(df_raw):.1%})")

fig, ax = plt.subplots(figsize=(5, 3.5))
ax.bar(CLASS_NAMES, counts.values, color=["#16a34a", "#f59e0b", "#dc2626"])
ax.set_title("Hair fall risk - class distribution"); ax.set_ylabel("patients")
fig.tight_layout(); fig.savefig(OUT / "class_distribution.png", dpi=150); plt.show()

df_raw.describe().T.round(3).to_csv(OUT / "data_summary.csv")
