# Chapter 2: Background Study and Literature Review

## 2.1 Background Study

Human hair grows in a repeating cycle of three phases: a growth phase (anagen), a short regression phase (catagen), and a resting phase (telogen) after which the hair is shed. Losing some hair every day is therefore normal. Hair loss becomes a medical problem when this cycle is disturbed, so that too many follicles enter the resting phase early or the follicles shrink and stop producing thick hair. Clinically, the most common forms are androgenetic alopecia (pattern hair loss driven by hormones and inheritance), telogen effluvium (a temporary but heavy shedding that follows a physical or emotional trigger), and alopecia areata (patchy loss caused by an autoimmune reaction).

The biological factors that disturb the hair cycle are well documented, and they usually act together rather than alone. The main ones are described below.

**Hormones and heredity.** Androgenetic alopecia depends on inherited sensitivity of the follicles to androgen hormones, which is why family history is one of the strongest risk indicators. Agaoglu et al. (2021) studied how common early-onset androgenetic alopecia is and how it relates to lifestyle and dietary habits.

**Nutrition and iron status.** Hair follicles are among the most active tissues in the body, so they are sensitive to shortages of iron, zinc, and some vitamins. Guo and Katta (2017) reviewed the evidence on nutrient deficiency, supplement use, and hair loss. Lin et al. (2023) focused on iron-deficiency-related alopecia in women, and Treister-Goltzman et al. (2022) combined the available studies in a systematic review and meta-analysis of iron deficiency and non-scarring alopecia in women. These studies are why blood indicators such as haemoglobin and iron are treated as important risk markers.

**Thyroid function.** Thyroid hormones help regulate the hair cycle, and both an underactive and an overactive thyroid are linked with hair disorders (Hussein et al., 2023). In Nepal, Marahatta et al. (2018) reported on the association between alopecia areata and thyroid dysfunction in patients from eastern Nepal.

**Psychological stress.** Stress is thought to push follicles out of the growth phase too early, which leads to increased shedding some weeks later (Bai et al., 2026). Stress can also make an existing condition worse, so it is both a cause and a consequence of hair loss.

**Infection and physical illness.** A sudden illness, fever, or major physical strain can trigger telogen effluvium. Cline et al. (2021) documented a surge in telogen effluvium in communities heavily affected by COVID-19, showing how a large health event can raise the number of people who present with hair loss.

**How people are affected in real life.** Hair loss is rarely only a cosmetic matter. It is linked with lower self-confidence, anxiety, and a poorer quality of life, and in many cases the person does not know which of the factors above is responsible. Survey evidence shows that young people are affected too. In a survey of 610 participants in Bangladesh, most respondents were aged 18 to 24, and stress, allergies, dandruff, and family history were the main causes they reported (Khatun et al., 2022). Worldwide, the burden of alopecia areata has been analysed over three decades using the Global Burden of Disease data, including differences in lifetime risk between women and men (Sun et al., 2025).

**Current trend.** Reports suggest that hair loss is being seen more often and at a younger age. Early-onset androgenetic alopecia has been linked to lifestyle and dietary habits (Agaoglu et al., 2021), and post-infection shedding rose sharply during the COVID-19 period (Cline et al., 2021). Research and public interest have followed the same direction: bibliometric work has mapped global research trends and emerging topics in hair loss treatment (Wang et al., 2026), and Google search patterns have been used to track worldwide interest in hair loss treatments (Todorova & Kluger, 2026).

**From biology to machine learning.** Because the causes above overlap and interact, no single test can predict hair loss risk. Diagnosis today relies mostly on clinical examination and the patient's own history, which is slow, subjective, and hard to reach in rural areas. This has led researchers to apply machine learning to hair loss. Earlier work mainly used scalp or hair images (Shakeel et al., 2021; Sayyad et al., 2022), and more recent work uses survey and clinical tables with classical algorithms such as Random Forest and XGBoost (Khatun et al., 2022; Kumar et al., 2025; Sai et al., 2023). The newest direction is tabular foundation models such as TabPFN (Hollmann et al., 2025) and TabFM (Kong et al., 2026), which have not yet been tested on hair loss. Section 2.2 reviews this work in detail.

## 2.2 Literature Review

This section reviews the published research that is closest to the present study. For each study it states what data was used, which models were tested, what was found, and what was left open. The studies are grouped by topic, and Table 2.1 at the end of the section summarises them. Longer notes on each paper are kept in the Literature_Summary folder.

**Hair loss prediction from survey and lifestyle data.** Khatun et al. (2022) surveyed 610 people in Bangladesh and trained SVM, KNN, Logistic Regression, Random Forest, and XGBoost to diagnose hair fall disorder. XGBoost gave the best accuracy of 92.62%. The study shows that questionnaire data can carry a useful signal, but it tested only classical models and did not explain individual predictions.

Sai et al. (2023) compared SVM, KNN, decision tree, random forest, and logistic regression with an ensemble method for hair fall prediction. The ensemble was better than every single algorithm in accuracy, precision, and recall. The study did not include boosting models designed for categorical data or any explanation method.

Kumar et al. (2025) built a Random Forest hair loss predictor on a dataset of 2,000 records with 10 features (genetics, hormones, medical history, nutrition, stress) and added a web interface built with Django. Random Forest reached 100% accuracy, while XGBoost (67.5%), CatBoost (49.5%), and LightGBM (47.5%) scored much lower. A score of 100% on a real health problem is unusual and may point to an easy or synthetic-looking dataset, so it is better read as a result on that one dataset than as proof that Random Forest is best. The very low CatBoost score also suggests that the boosting models were not tuned, which is an open question this study tests properly.

Siami and Azis (2025) compared Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost, and a voting ensemble on a balanced dataset of genetic, hormonal, lifestyle, and environmental indicators. Accuracy and F1-score stayed at about 50% at best, although age, stress, and nutritional deficiency were identified as important factors. The authors concluded that richer clinical inputs were needed.

Leema et al. (2025) collected questionnaire data from 750 university students and community members and proposed HairSentinel, which forecasts hair fall trends and flags unusual episodes using a Temporal Fusion Transformer. It reached 97.5% accuracy and was compared with LSTM, Random Forest, and ARIMAX. Their dataset is not public, which makes the result impossible to reproduce, and it rests on self-reported data rather than blood test values.

**Hair loss detection from images and deep learning.** Shakeel et al. (2021) proposed a framework that classifies healthy hair and alopecia areata from hair images using colour, texture, and shape features with SVM and KNN, with accuracies of 91.4% and 88.9%. Sayyad et al. (2022) used a VGG network with an SVM classifier and reported 98.31% accuracy on 200 healthy-hair images (Figaro1k) and 68 alopecia areata images (DermNet). Pandikumar et al. (2024) proposed a deep learning framework that combines CNNs on scalp images with LSTM networks on lifestyle sequences. These studies need images or specialised equipment, address alopecia areata or scalp condition rather than risk from routine health indicators, and use small image sets.

**Gradient boosting and CatBoost.** Prokhorenkova et al. (2018) introduced CatBoost, which handles categorical features with ordered target statistics and ordered boosting to avoid target leakage. This design makes CatBoost a strong choice for survey-style data with many categorical answers. In hair loss research, however, CatBoost appears only as a side comparison and was not tuned (Kumar et al., 2025).

**Tabular foundation models.** Hollmann et al. (2025) presented TabPFN, a transformer pretrained on millions of synthetic datasets that predicts on a new table in a single forward pass without task-specific training. It performed best on small datasets of up to about 10,000 rows. Kong et al. (2026) introduced TabFM, a 400-million-parameter model trained on synthetic tables, which ranked first among default tabular foundation models on the 51 datasets of the TabArena benchmark and outperformed tuned AutoML pipelines. An independent reproduction on three machines and 13 TabArena datasets confirmed competitive accuracy against XGBoost, Random Forest, and TabPFN, but reported four upstream software defects and memory failures above about 10,000 rows on a 24 GB GPU (Pandey, 2026). None of these studies used medical or hair loss data.

**Explainability.** Lundberg and Lee (2017) proposed SHAP, which assigns each feature a contribution to a prediction using Shapley values from game theory. Because SHAP works with any model, it can be used to compare explanations from architecturally different models on the same data. Among the hair loss studies above, the emphasis is on accuracy, and none compares explanations across a boosted-tree model and foundation models.

**Table 2.1: Summary of reviewed studies**

| Study | Data | Models | Main result | Limitation |
|---|---|---|---|---|
| Khatun et al. (2022) | Survey, 610 people, Bangladesh | SVM, KNN, LR, RF, XGBoost | XGBoost 92.62% | Classical models only, no explanation |
| Sai et al. (2023) | Hair fall data | SVM, KNN, DT, RF, LR, ensemble | Ensemble best | No categorical-aware boosting, no explanation |
| Kumar et al. (2025) | 2,000 records, 10 features | RF, XGBoost, CatBoost, LightGBM and others | RF 100%, CatBoost 49.5% | Suspiciously high score, CatBoost untuned |
| Siami and Azis (2025) | Balanced multi-factor data | LR, DT, RF, GB, XGBoost, voting | About 50% at best | Weak signal, modest accuracy |
| Leema et al. (2025) | Survey, 750 people | LSTM, RF, TFT, ARIMAX | TFT 97.5% | Private data, self-reported only |
| Shakeel et al. (2021) | Hair images | SVM, KNN | 91.4% and 88.9% | Images needed, one condition |
| Sayyad et al. (2022) | 268 images | VGG with SVM | 98.31% | Small image set, one condition |
| Pandikumar et al. (2024) | Scalp images and lifestyle sequences | CNN, LSTM | Framework proposed | Needs images |
| Prokhorenkova et al. (2018) | Benchmarks | CatBoost | Beats other boosting libraries | Not health-specific |
| Hollmann et al. (2025) | Benchmarks | TabPFN | Strong on small tables | No hair loss data |
| Kong et al. (2026) | TabArena, 51 datasets | TabFM | First among default foundation models | No health data |
| Pandey (2026) | 13 TabArena datasets | TabFM vs XGBoost, RF, TabPFN | Confirmed competitive | Four defects, memory limit |

### 2.2.1 Research Gap

Reading the studies together shows five gaps, and each one explains a choice made in this project.

1. **Only classical algorithms were compared on hair loss tables.** The survey-based studies used Logistic Regression, SVM, KNN, Random Forest, and XGBoost (Khatun et al., 2022; Sai et al., 2023; Siami & Azis, 2025). The reported accuracies range from about 50% to 100% on different datasets, so there is no reliable picture of which type of model suits hair loss data. This project therefore compares different families of models on one dataset with one fixed test set.

2. **CatBoost was never properly tuned for hair loss.** CatBoost was designed for categorical features, which dominate survey data, yet it appears only once as a side comparison with a low score (Kumar et al., 2025). This project tunes CatBoost carefully so that it acts as a strong baseline.

3. **Tabular foundation models have not been tested on hair loss or on health survey data.** TabPFN and TabFM were evaluated on general benchmarks (Hollmann et al., 2025; Kong et al., 2026), and the only independent check of TabFM used TabArena datasets (Pandey, 2026). Whether such models can match a tuned boosted-tree model on a health table is not known. This is the reason TabPFN and TabFM are included and trained on the same data.

4. **TabFM is very new and its practical limits are unclear.** The independent reproduction found software defects and memory failures on larger tables (Pandey, 2026). Running TabFM on a real dataset and reporting its cost and limitations is a contribution in itself.

5. **Explanations are not compared across models.** The hair loss studies report accuracy and rarely explain individual predictions, and none explains a boosted-tree model and foundation models side by side. This project applies SHAP (Lundberg & Lee, 2017) to all three models so the clinical plausibility of their explanations can be compared.

Taken together, the gaps lead to the aim of this study: to benchmark CatBoost, TabPFN, and TabFM on the same hair fall risk dataset, and to explain every model with SHAP.

## References

