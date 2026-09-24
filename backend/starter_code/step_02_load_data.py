# Step 2 - Load the raw dataset and save it to Postgres (names are already base64-encoded)
import pandas as pd
from lab_db import DATA_DIR, save_df

df = pd.read_csv(DATA_DIR / "data.csv")
print("Shape:", df.shape)
print("Missing values:", int(df.isna().sum().sum()))
print("\nDtypes:\n", df.dtypes.to_string())
print("\nTarget distribution (0 Low, 1 Moderate, 2 High):\n", df["hair_fall"].value_counts().sort_index().to_string())
display(df.head())
save_df(df, "hairfall_raw")
