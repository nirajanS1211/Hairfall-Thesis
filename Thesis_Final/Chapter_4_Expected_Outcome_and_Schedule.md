# Chapter 4: Expected Outcome and Working Schedule

## 4.1 Expected Outcomes

This study is expected to give a fair comparison of CatBoost, TabPFN, and TabFM on hair fall data, because all three use the same dataset, split, random seed, and metrics, unlike earlier studies that compared different classical models on different datasets (Khatun et al., 2022; Kumar et al., 2025; Siami & Azis, 2025). CatBoost is tuned with a grid search and cross-validation on the training data, so it should act as a strong baseline, unlike the untuned CatBoost result in earlier work (Kumar et al., 2025). TabPFN and TabFM are expected to be competitive with the tuned CatBoost without any tuning, especially with small training sets, as their benchmark results suggest (Hollmann et al., 2025; Kong et al., 2026). The study can also show the opposite, and a difference between models is accepted only if McNemar's test shows that it is larger than chance. It will also record the practical limits of TabFM on a real health dataset, such as how much training data it can take, how long it runs, and what problems appear, since an independent reproduction reported software defects and memory failures on larger tables (Pandey, 2026).

SHAP is expected to show which measurements and habits drive each model's predicted risk tier and whether the three models agree. The factors the models rely on are expected to match the known biological causes of hair loss, such as iron level, stress, and family history. Agreement would support the use of the models as decision support, and disagreement would be reported as a finding. Overall, the study expects to show whether explainable, data-efficient tabular modelling can be a practical alternative to heavily tuned gradient boosting for structured health risk prediction, and to leave a documented and reproducible pipeline that others can rerun on their own data.

## 4.2 Working Schedule

The work is planned over six months, with the schedule shown as a Gantt chart in Figure 4.1. The tasks on the left are split into what has already been done up to this proposal (black bars) and what will be done after the proposal is approved (hatched bars). The completed tasks are the problem formulation, the literature review, the comparison and preparation of the datasets, the preprocessing and split, and the setup of the local environment and pipeline code. The planned tasks follow the order of the methodology in Chapter 3: model training, the training-size experiment, SHAP, evaluation, discussion, and thesis writing.

![Figure 4.1: Working schedule (Gantt chart)](figures/fig_4_1_gantt.png)

**Figure 4.1:** Working schedule (Gantt chart)
