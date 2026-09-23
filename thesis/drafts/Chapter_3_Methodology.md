CHAPTER 3
METHODOLOGY

This chapter describes how the study was conducted to meet the research objectives stated in Section 1.4. It covers the research design and approach, the study area and population, sample selection and size, the data collection, and the data analysis approach and tools. Table 3.1 links each method to the objective it serves.

Table 3.1: Link between the research objectives and the methods used

| Specific objective (Section 1.4) | Method used | Section |
|---|---|---|
| 1. Compare predictive performance and test significance | Common train/test split, CatBoost tuning, TabPFN and TabFM inference, macro-averaged metrics, ROC-AUC, McNemar's test | 3.5, 3.8.2, 3.8.3, 3.8.6 |
| 2. Evaluate the effect of training context size | Retraining all three models on 100, 500 and 2,000 training rows | 3.8.4 |
| 3. Explain predictions with SHAP | TreeExplainer for CatBoost, KernelExplainer for TabPFN and TabFM | 3.8.5 |
| 4. Assess computational cost and implementation limitations | Recording runtimes and documenting implementation problems | 3.8.7 |

3.1 Research design

The study used a quantitative, experimental design based on secondary data. It was a model-comparison (benchmarking) study: the same dataset, the same train/test partition and the same evaluation measures were applied to three models, so that differences in results could be attributed to the models and not to the data. No primary data were collected from people, so there was no field study area and no direct contact with respondents.

The study followed the pipeline in Figure 3.1. The data were preprocessed and split once. CatBoost was tuned and trained on the training partition, while TabPFN and TabFM received the training rows as context without any training. All three models were evaluated on the same held-out test partition, compared with a statistical test, examined with reduced training contexts, and explained with SHAP.

Figure 3.1: Block diagram of the research methodology

```
Dataset (21,606 records, 20 features, 3 risk tiers)
        |
Preprocessing (drop id/full_name, encode gender, check missing values)
        |
Stratified 80/20 split ----> Training (17,284)      Test (4,322)
        |                          |                     |
        |        +-----------------+----------------+    |
        |        |                 |                |    |
        |    CatBoost           TabPFN           TabFM    |
        |  (grid search,     (zero-shot,      (zero-shot, |
        |   5-fold CV)      full context)   500-row ctx)  |
        |        |                 |                |    |
        |        +-----------------+----------------+    |
        |                          |                     |
        +--> Reduced-context runs (100 / 500 / 2,000)    |
                                   |                     |
                     Evaluation on test partition <------+
        (accuracy, macro-P/R/F1, ROC-AUC, McNemar, runtime)
                                   |
                       SHAP explanations of all models
```

The design was chosen because the research questions ask for a like-for-like comparison of models on one task. A single fixed split and a fixed random seed (42) made the results reproducible.

3.2 Research approach

A quantitative, deductive approach was used. The proposition examined was that zero-shot tabular foundation models can match a tuned gradient-boosted model on multi-tier hair fall risk classification. It was examined with numerical performance measures and a statistical test, and the predictions were then explained with SHAP. A quantitative approach was suitable because the research questions ask about measurable differences in performance, data efficiency and feature contribution.

3.3 Study area

The study was not a field study, so there was no geographical study area. The data were taken from two public datasets [13], [14], and all experiments were run in cloud notebook environments (Section 3.8.8).

3.4 Study population

The population was the set of patient records describing demographic, biochemical, clinical and lifestyle attributes related to hair fall. The dataset had 21,606 records with 23 columns: an identifier (id), a name (full_name), 20 predictor variables and the target variable hair_fall. There were no duplicate rows and no missing values. The target had three ordinal tiers: 0 (Low, 9,723 records, 45.0%), 1 (Moderate, 7,562 records, 35.0%) and 2 (High, 4,321 records, 20.0%).

3.5 Sample selection

The whole dataset was used, so no separate sampling of records was done. It was divided into a training and a test partition by a stratified 80/20 split with a fixed random seed of 42, so that class proportions were preserved in both parts. The test partition was held out and was not used for tuning CatBoost's hyperparameters. The same partition was used for all three models.

For the training-context experiment (Section 3.8.4), smaller training samples of 100, 500 and 2,000 rows were drawn at random (seed 42) from the training partition. TabFM's main evaluation used a 500-row context drawn in the same way.

3.6 Sample size

The full dataset had 21,606 records. The split gave 17,284 training records and 4,322 test records (1,945 Low, 1,513 Moderate and 864 High). CatBoost and TabPFN used all 17,284 training records, and TabFM used a 500-row context (about 2.9% of the training partition). The reduced-context runs used 100, 500 and 2,000 training rows. The 100-row and 500-row runs were evaluated on all 4,322 test records, and the 2,000-row run on a fixed random subset of 500 test records.

3.7 Methods of data collection

No primary data were collected from people. The study used secondary data and computational modelling and measurement.

The dataset was assembled from two public sources. The physiological biomarker data came from the Kaggle Hair Loss Dataset [13], chosen for its continuous clinical indicators relevant to hair health. The demographic and lifestyle indicators came from the Mendeley Hair Fall Problem Survey Dataset [14], chosen for its binary lifestyle and hereditary risk factors. Respondent names were removed before processing. Because the two sources came from different respondent groups, feature values were adjusted using relationships between risk factors and hair loss reported in the dermatological literature, and this produced the final dataset. It was therefore a constructed dataset and not a clinical registry. The consequences for the interpretation of the results are discussed in Chapter 4.

The 20 predictor variables fell into four groups (Table 3.2).

Table 3.2: Predictor variables

| Group | Variables |
|---|---|
| Demographics and heredity | age (years); gender (Female, Male, Other); family_hair_fall_history (0/1) |
| Serum and physiological biomarkers | total_protein (g/dL); iron (µg/dL); calcium (mg/dL); vitamin_d (ng/mL); manganese (µg/L); alt_liver (U/L); body_water_content (%); stress_level (0–40, modelled on the Perceived Stress Scale) |
| Hair condition scores | total_keratine and hair_texture (composite 0–100 scores, not standard laboratory measurements) |
| Clinical and lifestyle flags (0/1) | chronic_illness, anemia, stress, late_night_sleep, sleep_disturbance, water_reason (exposure to hard or chemically treated water), chemical_use (hair dyes, relaxers and other chemical treatments) |

Model outputs (predictions, class probabilities, SHAP values) and running times were collected by running the experiments in Section 3.8, which is the measurement part of the study.

3.8 Data analysis approach and tools

The data were analysed in the steps below. The analysis was done in Python, and the tools are listed in Section 3.8.8.

3.8.1 Data preprocessing

The following steps were applied before modelling.

1. Identifier removal. The columns id and full_name carry no predictive information and could create false associations, so they were removed.
2. Encoding. The gender attribute was mapped to numbers (0 = Female, 1 = Male, 2 = Other). The target was already coded as 0, 1 and 2, so it needed no change. All other predictors were numeric or binary and were used as they were. TabPFN and TabFM received these raw values without scaling.
3. Missing values. The data were checked and no missing values were found, so no imputation was needed.


3.8.2 Models and justification

Three models were selected to represent three different approaches to tabular prediction, in line with Objective 1.

3.8.2.1 CatBoost

CatBoost [7] is a gradient-boosted decision tree method that builds trees one after another, each correcting the errors of the ensemble so far. At iteration t it minimises a regularised objective:

$$\mathcal{L}^{(t)} = \sum_i L\big(y_i,\; F_{t-1}(x_i) + h_t(x_i)\big) + \Omega(h_t)$$

where L is the multi-class cross-entropy loss, F_{t-1} is the ensemble built so far, h_t is the new tree and Ω penalises tree complexity. CatBoost reduces target leakage through ordered target statistics and builds symmetric (oblivious) trees, which limits overfitting. It was selected as the tuned, well-established baseline whose performance the foundation models had to match.

3.8.2.2 TabPFN

TabPFN [8] is a transformer pretrained offline on synthetic datasets. It does not train on the target data. It receives the labelled training rows D_train and a query x_test together and returns the predictive distribution in a single forward pass:

$$P(y_{test}\mid x_{test}, \mathcal{D}_{train}) = \int P(y_{test}\mid x_{test}, \theta)\, P(\theta\mid \mathcal{D}_{train})\, d\theta$$

This is done with self-attention:

$$\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{QK^{T}}{\sqrt{d_k}}\right)V$$

TabPFN was selected as the established tabular foundation model, which needs no hyperparameter tuning or feature scaling.

3.8.2.3 TabFM

TabFM [9] is a tabular foundation model released by Google Research. It alternates row-wise and column-wise attention over the table before an in-context transformer produces the prediction, and it also needs no training or tuning:

$$P(y_{test}\mid x_{test}, \mathcal{D}_{train}) = \mathrm{TabFM}(x_{test}, \mathcal{D}_{train})$$

TabFM was selected as a second, independently developed foundation model, so that the study could test whether the behaviour of zero-shot models holds for more than one architecture.


3.8.3 Experimental setup

CatBoost. A grid search was run over tree depth {4, 6, 8} and learning rate {0.01, 0.03, 0.1}. Each combination was scored by stratified 5-fold cross-validation on the training partition, using macro-F1. All models used the MultiClass loss, l2_leaf_reg = 3.0, at most 1,000 iterations, early stopping after 50 rounds and a random seed of 42. The best combination was depth = 4 and learning rate = 0.1 (cross-validation macro-F1 = 0.7665). The final model was trained on the full training partition with this setting. In this final fit, early stopping was monitored on the test partition, so the test data influenced the number of trees selected. This is noted as a limitation in Chapter 5.

TabPFN. The default configuration of the TabPFN package was run on a GPU with a random seed of 42. The full training partition (17,284 rows) was supplied as context, and no tuning was done.

TabFM. The PyTorch implementation of TabFM version 1.0.0 was used with a single ensemble member (n_estimators = 1). A context of 500 rows was drawn at random (seed 42) from the training partition, because inference time grew steeply with context size and a full-context evaluation could not be completed within the limits of the cloud platforms (Section 4.5). The asymmetry between TabFM's context and that of the other two models is the reason for the experiment in Section 3.8.4.

The tuning effort was deliberately unequal: CatBoost was tuned by grid search, while TabPFN and TabFM were not tuned. This asymmetry is central to the research question.


3.8.4 Training context experiment

To meet Objective 2, all three models were retrained with reduced training contexts of 100, 500 and 2,000 rows, drawn at random (seed 42) from the training partition. CatBoost was trained on the sampled rows with the configuration above, and TabPFN and TabFM received the sampled rows as context. The 100-row and 500-row runs were evaluated on the full test partition. Because TabFM inference was slow, the 2,000-row run was evaluated on a fixed random subset of 500 test records, for all three models. Results at 2,000 rows are therefore not directly comparable with the other sizes.


3.8.5 Explainability analysis

To meet Objective 3, post-hoc explanations were produced with SHAP [11]. SHAP splits a prediction into additive contributions of the individual features:

$$f(x) = \phi_0 + \sum_j \phi_j$$

where φ_0 is the baseline expected prediction and φ_j is the contribution of feature j.

For CatBoost, TreeExplainer was used, which computes exact Shapley values from the tree structure, on the full test partition. TabPFN and TabFM have no tree structure, so KernelExplainer was used, which estimates the values by querying the model repeatedly. PermutationExplainer, which had been planned, failed because of a numba error in the cloud environments (Section 4.5). Because each query passes through the full in-context mechanism, the analyses of the two foundation models used a reduced training context, a background sample of 15 records, 100 kernel evaluations per explained record, and a random subset of the test partition (30 records for TabPFN and 20 for TabFM). Global importance plots, beeswarm plots and patient-level waterfall plots were produced, and the beeswarm and waterfall plots were drawn for the High risk class. Features were compared across models by rank and not by the size of the values, since the sample sizes differed.


3.8.6 Evaluation metrics and statistical testing

To meet Objective 1, predictions were evaluated on the test partition with macro-averaged measures, which give the three classes equal weight. TP_k, FP_k and FN_k are the true positives, false positives and false negatives of class k, and N is the number of test records.

$$\text{Accuracy} = \frac{\sum_{k=0}^{2} TP_k}{N}$$

$$\text{Macro-Precision} = \frac{1}{3}\sum_{k=0}^{2}\frac{TP_k}{TP_k + FP_k} \qquad \text{Macro-Recall} = \frac{1}{3}\sum_{k=0}^{2}\frac{TP_k}{TP_k + FN_k}$$

$$\text{Macro-F1} = \frac{1}{3}\sum_{k=0}^{2} \frac{2 \cdot \text{Precision}_k \cdot \text{Recall}_k}{\text{Precision}_k + \text{Recall}_k}$$

ROC-AUC was computed with a one-vs-rest strategy and macro-averaged. Per-class F1-scores and confusion matrices were also produced. Macro-averaging was used because the classes were unequal in size (Section 3.4).

Pairwise differences in accuracy between the models were tested with McNemar's test with continuity correction on the same test records, using the counts b and c of records that one model classified correctly and the other did not:

$$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$$

A difference was called significant at α = 0.05. The test was applied to the full-context evaluation only.


3.8.7 Computational assessment

To meet Objective 4, the running time of each model was recorded during training or context fitting and during prediction, and the practical problems met when running the models (runtime growth, software errors and the workarounds used) were documented. These are reported in Section 4.5.


3.8.8 Tools and environment

The experiments were written in Python in cloud notebooks on Kaggle and Google Colaboratory, using an NVIDIA T4 GPU (Table 3.3). Data handling used pandas and NumPy, and scikit-learn was used for the split, cross-validation and metrics. The models came from the catboost, tabpfn and tabfm (PyTorch backend) packages, the explanations from the shap package, the significance test from statsmodels, and the plots from matplotlib and seaborn.

Table 3.3: Experimental environment

| Item | Specification |
|---|---|
| Platform | Google Colaboratory and Kaggle Notebooks (cloud) |
| GPU | NVIDIA T4 (Colab: one T4; Kaggle: two T4, one used) |
| Memory | About 13 GB (Colab) and 30 GB (Kaggle) |
| Operating system | Ubuntu 22.04 |
| Language and framework | Python [version to be confirmed]; PyTorch with CUDA |
| Main libraries | CatBoost, TabPFN, TabFM 1.0.0, SHAP, scikit-learn, statsmodels, pandas, NumPy |

