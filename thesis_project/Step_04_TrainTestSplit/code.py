# Step 4 - Train/test split
# 80/20 stratified train/test split + the matched training sizes used in steps 5-8
import pandas as pd
from lab import OUT, SEED, SIZES, context, step_file
from sklearn.model_selection import train_test_split

clean = pd.read_csv(step_file("Step_03_CleanEncode", "hairfall_clean.csv"))
train, test = train_test_split(clean, test_size=0.20, stratify=clean["hair_fall"], random_state=SEED)
print(f"Train: {len(train):,} rows | Test: {len(test):,} rows")

X_train, y_train = train.drop(columns="hair_fall"), train["hair_fall"]
rows = []
for label, n in SIZES.items():
    _, y_ctx = context(X_train, y_train, n)
    dist = y_ctx.value_counts(normalize=True).sort_index().round(3).to_dict()
    rows.append({"size": label, "rows": len(y_ctx), "Low": dist[0], "Moderate": dist[1], "High": dist[2]})
sizes = pd.DataFrame(rows)
print("\nTraining sizes (same stratified rows for every model):")
display(sizes)
print("Test class share:", test["hair_fall"].value_counts(normalize=True).sort_index().round(3).to_dict())

train.to_csv(OUT / "train.csv", index=False)
test.to_csv(OUT / "test.csv", index=False)
sizes.to_csv(OUT / "training_sizes.csv", index=False)
