# Step 9 - McNemar's tests
# McNemar's test: are the models' error patterns significantly different? (per training size)
import itertools

import pandas as pd
from lab import OUT, PROJECT
from statsmodels.stats.contingency_tables import mcnemar

MODELS = {"CatBoost": "Step_05", "TabPFN": "Step_06", "TabFM": "Step_07"}
LETTERS = {"500": "a", "2000": "b", "Full": "c"}

rows = []
for size, letter in LETTERS.items():
    preds = {}
    for name, prefix in MODELS.items():
        f = PROJECT / f"{prefix}{letter}_{name}_{size}" / "predictions.csv"
        if f.exists():
            d = pd.read_csv(f)
            preds[name] = d.set_index("row").assign(correct=lambda x: x.y_true == x.y_pred)["correct"]
        else:
            print(f"[skip] {name} {size}: not trained yet")
    for a, b in itertools.combinations(preds, 2):
        common = preds[a].index.intersection(preds[b].index)  # same test rows only
        ca, cb = preds[a].loc[common], preds[b].loc[common]
        table = [[int((ca & cb).sum()), int((ca & ~cb).sum())], [int((~ca & cb).sum()), int((~ca & ~cb).sum())]]
        res = mcnemar(table, exact=False, correction=True)
        rows.append({"size": size, "comparison": f"{a} vs {b}", "test_rows": len(common),
                     f"only_{a}_correct": table[0][1], "only_other_correct": table[1][0],
                     "chi2": round(float(res.statistic), 4), "p_value": round(float(res.pvalue), 4),
                     "significant_0.05": bool(res.pvalue < 0.05)})

results = pd.DataFrame(rows)
display(results)
results.to_csv(OUT / "mcnemar_results.csv", index=False)
