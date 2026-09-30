# Chapter 3: Methodology

## 3.1 Research Framework

The study follows one pipeline from data to explanation, shown in Figure 3.1. The final dataset is cleaned and split once. The same training and test rows are then given to three models, CatBoost, TabPFN, and TabFM. Their predictions are compared with the same metrics and statistical tests, and SHAP is applied to all three so that each predicted risk tier can be traced to its features.

![Figure 3.1: Overall research framework](figures/fig_3_1_framework.png)

**Figure 3.1:** Overall research framework

The framework serves the two objectives in Chapter 1. Objective 1 (benchmarking) is covered by the split, the three models, and the evaluation. Objective 2 (transparent insight) is covered by the SHAP stage.

## 3.2 Dataset Description

### 3.2.1 Source datasets and how they are related

Three datasets were involved. The main dataset used for modelling contains all 21,606 records and all columns needed for the study. To check that this dataset is realistic and that the findings do not depend on one source only, it was compared with two public datasets. Table 3.1 lists the three datasets, and Figure 3.2 shows how they are related.

**Table 3.1:** The three datasets

| Dataset | Source | Rows | Columns | Content | Row identifier |
|---|---|---|---|---|---|
| Dataset 1 | Kaggle "Hair Loss Dataset" (Dhankour, 2023) | 100,000 | 11 | 10 numeric biomarker and index columns and hair_fall (0 to 5) | None |
| Dataset 2 | Mendeley "Dataset for evaluating hair fall causes" (Arnob et al., 2024) | 716 | 14 | Questionnaire: age, gender, 8 Yes/No health and lifestyle answers, hair fall problem, food habit | Timestamp |
| Final dataset (data.csv) | Prepared for this study | 21,606 | 23 | 20 features and the 3-tier target hair_fall | id (1 to 21,606) |

![Figure 3.2: Relationship between the source datasets and the final dataset](figures/fig_3_2_dataset_link.png)

**Figure 3.2:** Relationship between the source datasets and the final dataset

The datasets are related by the meaning of their columns and not by a record key. Dataset 1 has no identifier at all, and Dataset 2 has only a timestamp, and the people in the three datasets are not the same individuals. A record-by-record join is therefore not possible. Instead, each column of the final dataset was matched to the column or question that measures the same thing, as shown in Table 3.2. The primary key of the final dataset is its own id column, which runs from 1 to 21,606 and was removed before modelling.

**Table 3.2:** Where each column of the final dataset comes from

| Final column | Dataset 1 column | Dataset 2 question | Unit or coding |
|---|---|---|---|
| age | none | What is your age? | years |
| gender | none | What is your gender? | Female, Male, Other |
| total_protein | total_protein | none | g/dL |
| calcium | calcium | none | mg/dL |
| iron | iron | none | µg/dL |
| vitamin_d | vitamin | none | ng/mL |
| alt_liver | liver_data | none | U/L |
| manganese | manganese | none | µg/L |
| body_water_content | body_water_content | none | % |
| stress_level | stress_level | none | 0 to 40 |
| total_keratine | total_keratine | none | 0 to 100 score |
| hair_texture | hair_texture | none | 0 to 100 score |
| family_hair_fall_history | none | Family member with hair fall or baldness? | 0 = No, 1 = Yes |
| chronic_illness | none | Chronic illness in the past? | 0 = No, 1 = Yes |
| late_night_sleep | none | Stay up late at night? | 0 = No, 1 = Yes |
| sleep_disturbance | none | Any sleep disturbance? | 0 = No, 1 = Yes |
| water_reason | none | Water in your area a reason for hair fall? | 0 = No, 1 = Yes |
| chemical_use | none | Use chemicals, gel or colour in hair? | 0 = No, 1 = Yes |
| anemia | none | Do you have anemia? | 0 = No, 1 = Yes |
| stress | none | Do you have too much stress? | 0 = No, 1 = Yes |
| hair_fall (target) | hair_fall (0 to 5) | Do you have a hair fall problem? | 0 Low, 1 Moderate, 2 High |

### 3.2.2 What the comparison showed

The comparison was done with a script (Datasets/comparison/dataset_comparison.py), and all numbers below come from it.

**Dataset 1.** Every column of Dataset 1 is spread evenly between its minimum and maximum (for example, iron runs from 0 to 499 and stress_level from 0 to 99), and the target hair_fall is spread evenly over the six values 0 to 5. Its columns also show no relationship with its own target: the Spearman correlation between every biomarker and hair_fall lies between −0.006 and +0.004. Dataset 1 therefore supplies the list of biomarkers and their types, but its values cannot be used directly to predict risk. In the final dataset the values lie in real clinical ranges (for example iron 10 to 217 µg/dL and total protein 4.8 to 9.5 g/dL) and most biomarkers are related to the target (for example iron ρ = −0.31, stress_level ρ = +0.33, total_protein ρ = −0.30).

**Dataset 2.** Dataset 2 is a real survey of young people (mean age 23.9 years) and was cleaned first: one age of 218 was removed and two typing errors ("Yea" and "\No") were corrected, leaving 715 usable rows. Two checks were made against the final dataset, shown in Table 3.3. First, the risk factors are much more common in the survey (for example stress 72.0% and family history 72.7%) than in the final dataset (40.3% and 34.5%), because the survey respondents are self-selected and many were interested in hair fall. Second, and more important, the direction of each risk factor is the same in both datasets. In the survey, people with a hair fall problem more often reported every one of the eight factors than those without, and the same is true in the final dataset for all eight.

**Table 3.3:** Risk factors in Dataset 2 and in the final dataset (percentage points)

| Risk factor | Dataset 2: how common (%) | Final: how common (%) | Dataset 2: gap, hair fall vs none | Final: gap, hair fall vs none | Same direction |
|---|---|---|---|---|---|
| Family history | 72.7 | 34.5 | +41.0 | +10.1 | Yes |
| Chronic illness | 45.7 | 29.9 | +41.1 | +8.7 | Yes |
| Late-night sleep | 65.3 | 40.2 | +44.7 | +6.7 | Yes |
| Sleep disturbance | 55.4 | 35.2 | +41.4 | +6.5 | Yes |
| Water as a reason | 60.0 | 29.8 | +51.4 | +5.0 | Yes |
| Chemical use | 63.9 | 39.9 | +40.7 | +10.8 | Yes |
| Anemia | 28.7 | 24.6 | +22.2 | +8.7 | Yes |
| Stress | 72.0 | 40.3 | +48.3 | +11.2 | Yes |

*Gap = share of people with the factor among those with hair fall minus the share among those without. For the final dataset, "hair fall" means Moderate or High risk.*

The survey shows stronger gaps than the final dataset because survey respondents answered about a problem they already knew they had, while the final dataset describes graded risk. Because of these differences the final dataset is treated as a **semi-synthetic benchmark**: the associations learned by the models reflect relationships built into the data from the dermatology literature and the survey, and they are not new clinical evidence. [CONFIRM: add one sentence on how the 21,606 records were first generated.] This limitation is stated again when the results are discussed.

### 3.2.3 The final dataset

The final dataset has 21,606 records with 20 features and one target, in four groups.

1. **Demographics and heredity:** age (20 to 55 years), gender, family_hair_fall_history.
2. **Blood and body measurements:** total_protein, calcium, iron, vitamin_d, alt_liver (liver enzyme ALT), manganese, body_water_content, stress_level (0 to 40 scale), and two 0 to 100 hair condition scores, total_keratine and hair_texture.
3. **Clinical conditions (0/1):** chronic_illness, anemia, stress.
4. **Lifestyle and environment (0/1):** late_night_sleep, sleep_disturbance, water_reason, chemical_use.

The target hair_fall has three risk tiers: 0 = Low (9,723 records, 45%), 1 = Moderate (7,562, 35%), and 2 = High (4,321, 20%). Gender is Male for 12,109 records, Female for 9,485, and Other for 12.

## 3.3 Data Preprocessing

The following steps were applied to the final dataset before any model was run.

1. **Removal of identifiers.** The id column and the full_name column (which holds personal names in encoded form) were removed, because they do not describe health and could create false patterns. After removal, 20 features remain.
2. **Quality checks.** The dataset has no missing values and no duplicate records (ignoring id).
3. **Clinical range check.** Each blood and body measurement was compared with its normal reference range and with limits that are physiologically impossible (Table 3.4). No values were impossible, so no record was removed. Values outside the normal range were kept on purpose, because they are the information that indicates risk.
4. **Encoding.** Gender was coded 0 = Female, 1 = Male, 2 = Other. The yes/no columns were already 0/1, and the target was already coded 0, 1, 2.
5. **Stratified split.** The records were split 80% to 20% with the class shares kept equal (random seed 42): 17,284 training records and 4,322 test records, with 45% Low, 35% Moderate, and 20% High in both parts.

**Table 3.4:** Clinical range check of the final dataset

| Measurement | Normal range | Below normal | Above normal | % outside normal | Impossible values |
|---|---|---|---|---|---|
| total_protein (g/dL) | 6.0 to 8.3 | 406 | 605 | 4.7 | 0 |
| calcium (mg/dL) | 8.5 to 10.5 | 1,675 | 392 | 9.6 | 0 |
| iron (µg/dL) | 60 to 170 | 2,217 | 209 | 11.2 | 0 |
| vitamin_d (ng/mL) | 25 to 80 | 8,606 | 0 | 39.8 | 0 |
| alt_liver (U/L) | 7 to 56 | 2,300 | 403 | 12.5 | 0 |
| manganese (µg/L) | 4 to 15 | 1,960 | 208 | 10.0 | 0 |
| body_water_content (%) | 45 to 65 | 2,225 | 2,227 | 20.6 | 0 |

## 3.4 Model Selection

Three models from different families are compared: a tuned gradient boosting model (CatBoost) and two tabular foundation models that predict without training (TabPFN and TabFM). Each is shown as a block diagram with a short explanation of how it works.

### 3.4.1 CatBoost

![Figure 3.3: CatBoost model](figures/fig_3_3_catboost.png)

**Figure 3.3:** CatBoost model (gradient boosted symmetric trees)

CatBoost builds many small decision trees one after another, and each new tree is trained to correct the mistakes of the trees before it. All trees are symmetric, meaning that one split is used for a whole level of the tree, which makes the model fast and hard to overfit. The tree outputs are added to give one score for each risk tier, and a softmax turns the three scores into probabilities. Categorical answers are encoded using only earlier rows, which avoids target leakage (Prokhorenkova et al., 2018). CatBoost is the only model that is trained and tuned on the hair fall data.

### 3.4.2 TabPFN

![Figure 3.4: TabPFN model](figures/fig_3_4_tabpfn.png)

**Figure 3.4:** TabPFN model (in-context learning)

TabPFN is a transformer that was trained beforehand on millions of synthetic tables (Hollmann et al., 2025). To predict, it receives the training rows together with their known risk tiers and the patient to be predicted. Every value is turned into a vector, and attention layers let the model relate the features of a row and relate the patient to the training rows. The class probabilities are produced in a single forward pass. No weights are changed, so nothing is trained on the hair fall data.

### 3.4.3 TabFM

![Figure 3.5: TabFM model](figures/fig_3_5_tabfm.png)

**Figure 3.5:** TabFM model (zero-shot tabular foundation model)

TabFM is a model of about 400 million parameters developed by Google Research and pretrained on synthetic tables (Kong et al., 2026). Like TabPFN, it takes the training rows as context and predicts in one forward pass without tuning. Its table encoder alternates attention along columns and along rows, and an in-context transformer then combines the context rows with the query rows to give the class probabilities. It was published in 2026 and has been tested by others only on general benchmarks (Pandey, 2026), so how it behaves on real health data is one of the open questions of this study.

## 3.5 Explainability with SHAP

![Figure 3.6: SHAP explainability workflow](figures/fig_3_6_shap.png)

**Figure 3.6:** SHAP explainability workflow

SHAP splits a prediction into one contribution per feature, based on Shapley values from game theory (Lundberg & Lee, 2017). The contributions add up to the difference between the model's output and its average output:

f(x) = φ₀ + φ₁ + φ₂ + … + φ₂₀

where φ₀ is the average prediction and φⱼ is the contribution of feature j (for example iron or stress_level) to the predicted risk tier.

- **CatBoost:** TreeExplainer, which uses the tree structure to compute exact values, applied to a sample of 1,000 test records.
- **TabPFN and TabFM:** KernelExplainer, which estimates the values by repeatedly changing the inputs and predicting again. Because every repeat is a full forward pass of a large model, it is applied to a small sample of test records (a few tens) with a small k-means background set.

The results are a global ranking of the features (which matter most overall) and per-patient explanations (why this person received this tier). The rankings of the three models are compared with each other and with the known biology from Chapter 2.

## 3.6 Tools and Technologies

Table 3.5 lists the tools used for the work, with the versions recorded in the local environment.

**Table 3.5:** Software tools

| Purpose | Tool | Version |
|---|---|---|
| Language | Python | 3.12.14 |
| Data handling | pandas, NumPy | 3.0.6, 2.5.3 |
| Split, metrics, cross-validation | scikit-learn | 1.9.1 |
| Statistical tests | statsmodels (McNemar's test, Wilson intervals) | 0.15.0 |
| Gradient boosting model | CatBoost | 1.2.10 |
| Foundation model 1 | TabPFN | 9.0.0 |
| Foundation model 2 | TabFM (weights from Hugging Face: google/tabfm-1.0.0-pytorch) | 1.0.1 |
| Explainability | SHAP | 0.52.0 |
| Deep learning backend | PyTorch | 2.14.0 |
| Charts | Matplotlib | 3.11.2 |
| Workflow | Local lab application (notebook-style steps) with PostgreSQL and MinIO | — |
| GPU runs | Kaggle notebooks | — |

Package versions used on Kaggle are recorded at the start of each notebook and reported with the results.

## 3.7 Experimental Environment

The work is divided between two environments (Figure 3.7).

![Figure 3.7: Experimental environment](figures/fig_3_7_environment.png)

**Figure 3.7:** Experimental environment

**Local machine.** Data preparation, the split, CatBoost tuning and training, the statistical tests, and the result tables and figures are run on an Apple-silicon Mac (macOS, 17.2 GB memory, Apple GPU) with Python 3.12. The steps are run one by one in a local lab application that stores the data in PostgreSQL and the outputs in MinIO, so every run is saved and can be reopened.

**Kaggle notebooks.** TabFM and TabPFN need a GPU to make their predictions in reasonable time, and TabFM is the largest model (about 6.5 GB of weights). These runs are therefore done in Kaggle notebooks, which offer more GPU capacity than Google Colab. The train and test files created on the local machine are uploaded to the notebook, and the metrics and predictions are downloaded back for comparison. SHAP for the two foundation models is also run there.

To keep the comparison fair, all three models use the same split and the same random seed (42), and the environment of every session (Python, GPU, memory, package versions) is recorded and reported.

## 3.8 Performance Evaluation Metrics

Model performance is measured on the same held-out test set for every model. Because the three risk tiers are not equally common (45%, 35%, 20%), the class-averaged (macro) versions of the metrics are used, so that the smaller High tier counts as much as the Low tier. Here TP, FP, and FN are the true positives, false positives, and false negatives of one class, and K = 3 is the number of classes.

- **Accuracy:** the share of test records whose tier is predicted correctly. Accuracy = (number correct) / (number of test records).
- **Macro-precision:** Precision_k = TP_k / (TP_k + FP_k) for each class, averaged over the three classes. It shows how trustworthy a predicted tier is.
- **Macro-recall:** Recall_k = TP_k / (TP_k + FN_k) for each class, averaged over the three classes. It shows how many patients of a tier are found.
- **Macro-F1:** the harmonic mean of precision and recall for each class, averaged over the classes: F1_k = 2 × Precision_k × Recall_k / (Precision_k + Recall_k).
- **ROC-AUC:** the area under the ROC curve for each tier against the other two (one-versus-rest), averaged over the three tiers. It measures how well the predicted probabilities rank patients, independent of any cut-off.
- **Confusion matrix:** shows which tiers are mixed up. This matters here because the tiers are ordered, and confusing Low with High is a worse mistake than confusing neighbouring tiers.
- **Statistical significance:** McNemar's test is applied to every pair of models on the test set, to decide whether a difference in the number of correct predictions is larger than chance, and the accuracy of each model is given with a 95% Wilson confidence interval.
