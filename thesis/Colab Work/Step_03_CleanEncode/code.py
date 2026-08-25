df_model = df.drop(columns=["id", "full_name"]).copy()
gender_map = {"Female": 0, "F": 0, "Male": 1, "M": 1, "Other": 2, "O": 2}
df_model["gender"] = df_model["gender"].map(gender_map)
X = df_model.drop(columns=["hair_fall"])
y = df_model["hair_fall"]