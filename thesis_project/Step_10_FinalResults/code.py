# Step 10 - Final results
# Final comparison: all models x all training sizes, scaling curves and timings
import json

import matplotlib.pyplot as plt
import pandas as pd
from lab import OUT, PROJECT

metrics = [json.loads(p.read_text()) for p in sorted(PROJECT.glob("Step_0[567]*/metrics.json"))]
if not metrics:
    raise RuntimeError("No trained models found - run steps 5-7 first.")
res = pd.DataFrame(metrics)
order = {"500": 0, "2000": 1, "Full": 2}
res = res.sort_values(["size", "model"], key=lambda s: s.map(order) if s.name == "size" else s).reset_index(drop=True)
cols = ["model", "size", "context_rows", "test_rows", "accuracy", "macro_f1", "weighted_f1", "roc_auc_ovr",
        "fit_seconds", "predict_seconds"]
display(res[cols])
res[cols].to_csv(OUT / "final_results.csv", index=False)

shap_rows = [json.loads(p.read_text()) for p in sorted(PROJECT.glob("Step_08*/shap_summary.json"))]
if shap_rows:
    shap_df = pd.DataFrame(shap_rows)
    shap_df["top_5"] = shap_df["top_5"].str.join(", ")
    display(shap_df)
    shap_df.to_csv(OUT / "shap_top_features.csv", index=False)

colors = {"CatBoost": "#f59e0b", "TabPFN": "#2563eb", "TabFM": "#16a34a"}
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for metric, ax in zip(["accuracy", "macro_f1", "roc_auc_ovr"], axes):
    for model, d in res.groupby("model"):
        ax.plot(d["context_rows"], d[metric], marker="o", label=model, color=colors.get(model))
    ax.set_xscale("log"); ax.set_xlabel("training / context rows (log)"); ax.set_title(metric)
    ax.grid(alpha=.3)
axes[0].legend()
fig.suptitle("Performance vs training size"); fig.tight_layout()
fig.savefig(OUT / "scaling_curves.png", dpi=150); plt.show()

res["total_seconds"] = res["fit_seconds"] + res["predict_seconds"]
pivot = res.pivot(index="size", columns="model", values="total_seconds").reindex(list(order))
ax = pivot.plot.bar(figsize=(7, 4), color=[colors.get(c) for c in pivot.columns], logy=True, rot=0)
ax.set_ylabel("seconds (log)"); ax.set_title("Train + predict time on this Mac")
plt.tight_layout(); plt.savefig(OUT / "timings.png", dpi=150); plt.show()
