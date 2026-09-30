# Chapter 2: Background Study and Literature Review

## 2.1 Background Study

Human hair grows in a repeating cycle of three phases: a growth phase (anagen), a short regression phase (catagen), and a resting phase (telogen) after which the hair is shed. Losing some hair every day is therefore normal. Hair loss becomes a medical problem when this cycle is disturbed, so that too many follicles enter the resting phase early or the follicles shrink and stop producing thick hair. Clinically, the most common forms are androgenetic alopecia (pattern hair loss driven by hormones and inheritance), telogen effluvium (a temporary but heavy shedding that follows a physical or emotional trigger), and alopecia areata (patchy loss caused by an autoimmune reaction).

**Hormones and heredity.** Androgenetic alopecia depends on inherited sensitivity of the follicles to androgen hormones, which is why family history is an important risk indicator. Agaoglu et al. (2021) studied how common early-onset androgenetic alopecia is and how it relates to lifestyle and dietary habits.

**Nutrition and iron status.** Hair follicles are among the most active tissues in the body, so they are sensitive to shortages of iron, zinc, and some vitamins. Guo and Katta (2017) reviewed the evidence on nutrient deficiency, supplement use, and hair loss. Lin et al. (2023) focused on iron-deficiency-related alopecia in women, and Treister-Goltzman et al. (2022) combined the available studies in a systematic review and meta-analysis of iron deficiency and non-scarring alopecia in women. Blood indicators such as haemoglobin and iron are therefore treated as important risk markers.

**Thyroid function.** Thyroid hormones help regulate the hair cycle, and both an underactive and an overactive thyroid are linked with hair disorders (Hussein et al., 2023). In Nepal, Marahatta et al. (2018) reported on the association between alopecia areata and thyroid dysfunction in patients from eastern Nepal.

**Psychological stress.** Stress is thought to push follicles out of the growth phase too early, which leads to increased shedding some weeks later (Bai et al., 2026).

**Infection and physical illness.** A sudden illness, fever, or major physical strain can trigger telogen effluvium. Cline et al. (2021) documented a surge in telogen effluvium in communities heavily affected by coronavirus disease 2019 (COVID-19), showing how a large health event can raise the number of people who present with hair loss.

**How people are affected in real life.** Hair loss is rarely only a cosmetic matter. It is linked with lower self-confidence, anxiety, and a poorer quality of life, and in many cases the person does not know which of the factors above is responsible. Survey evidence shows that young people are affected too. In a survey of 610 participants in Bangladesh, most respondents were aged 18 to 24, and stress, allergies, dandruff, and family history were the main causes they reported (Khatun et al., 2022). Worldwide, the burden of alopecia areata has been analysed over three decades using the Global Burden of Disease data, including differences in lifetime risk between women and men (Sun et al., 2025).

**Current trend.** Reports suggest that hair loss is being seen more often and at a younger age. Early-onset androgenetic alopecia has been linked to lifestyle and dietary habits (Agaoglu et al., 2021), and shedding after infection rose sharply during the COVID-19 period (Cline et al., 2021).

**From biology to machine learning.** Because the causes above overlap and interact, no single test can predict hair loss risk. Diagnosis today relies mostly on clinical examination and the patient's own history, which is slow, subjective, and hard to reach in rural areas. This has led researchers to apply machine learning to hair loss. Earlier work mainly used scalp or hair images (Shakeel et al., 2021; Sayyad et al., 2022), and more recent work uses survey and clinical tables with classical algorithms such as Random Forest and XGBoost (Khatun et al., 2022; Kumar et al., 2025; Sai et al., 2023). The newest direction is tabular foundation models such as TabPFN (Hollmann et al., 2025) and TabFM (Kong et al., 2026), which have not yet been tested on hair loss.

## 2.2 Literature Review

**Hair loss prediction from survey and lifestyle data.** Khatun et al. (2022) surveyed 610 people in Bangladesh and trained a Support Vector Machine (SVM), k-Nearest Neighbours (KNN), Logistic Regression, Random Forest, and XGBoost to diagnose hair fall disorder. XGBoost gave the best accuracy of 92.62%. The study shows that questionnaire data can carry a useful signal, but it tested only classical models and did not explain individual predictions.

Sai et al. (2023) compared SVM, KNN, decision tree, random forest, and logistic regression with an ensemble method for hair fall prediction. The ensemble was better than every single algorithm in accuracy, precision, and recall. The study did not include boosting models designed for categorical data or any explanation method.

Kumar et al. (2025) built a Random Forest hair loss predictor on a dataset of 2,000 records with 10 features (genetics, hormones, medical history, nutrition, stress) and added a web interface built with Django. Random Forest reached 100% accuracy, while XGBoost (67.5%), CatBoost (49.5%), and LightGBM (47.5%) scored much lower. A score of 100% is unusual and should be read as a result on that one dataset, and the low CatBoost score suggests that the boosting models were not tuned.

Siami and Azis (2025) compared Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost, and a voting ensemble on a balanced dataset of genetic, hormonal, lifestyle, and environmental indicators. Accuracy and F1-score stayed at about 50% at best, although age, stress, and nutritional deficiency were identified as important factors. The authors concluded that richer clinical inputs were needed.

Leema et al. (2025) collected questionnaire data from 750 university students and community members and proposed HairSentinel, which forecasts hair fall trends and flags unusual episodes using a Temporal Fusion Transformer (TFT). It reached 97.5% accuracy and was compared with a Long Short-Term Memory network (LSTM), Random Forest, and an Autoregressive Integrated Moving Average with Exogenous Variables model (ARIMAX). Their dataset is not public, which makes the result impossible to reproduce, and it rests on self-reported data rather than blood test values.

**Hair loss detection from images and deep learning.** Shakeel et al. (2021) proposed a framework that classifies healthy hair and alopecia areata from hair images using colour, texture, and shape features with SVM and KNN, with accuracies of 91.4% and 88.9%. Sayyad et al. (2022) used a VGG network with an SVM classifier and reported 98.31% accuracy on 200 healthy-hair images (Figaro1k) and 68 alopecia areata images (DermNet). Pandikumar et al. (2024) proposed a deep learning framework that combines convolutional neural networks (CNNs) on scalp images with LSTM networks on lifestyle sequences. These studies need images or specialised equipment, address alopecia areata or scalp condition rather than risk from routine health indicators, and use small image sets.

**Gradient boosting and CatBoost.** Prokhorenkova et al. (2018) introduced CatBoost, which handles categorical features with ordered target statistics and ordered boosting to avoid target leakage. This design makes CatBoost a strong choice for survey-style data with many categorical answers. In hair loss research, however, CatBoost appears only as a side comparison and was not tuned (Kumar et al., 2025).

**Tabular foundation models.** Hollmann et al. (2025) presented TabPFN, a transformer pretrained on millions of synthetic datasets that predicts on a new table in a single forward pass without task-specific training. It performed best on small datasets of up to about 10,000 rows. Kong et al. (2026) introduced TabFM, a 400-million-parameter model trained on synthetic tables, which ranked first among default tabular foundation models on the 51 datasets of the TabArena benchmark and outperformed tuned automated machine learning (AutoML) pipelines. An independent reproduction on three machines and 13 TabArena datasets confirmed competitive accuracy against XGBoost, Random Forest, and TabPFN, but reported four upstream software defects and memory failures above about 10,000 rows on a 24 GB graphics processing unit (GPU) (Pandey, 2026). None of these studies used medical or hair loss data.

**Explainability.** Lundberg and Lee (2017) proposed SHAP, which assigns each feature a contribution to a prediction using Shapley values from game theory. Because SHAP works with any model, it can be used to compare explanations from architecturally different models on the same data. Among the hair loss studies above, the emphasis is on accuracy, and none compares explanations across a boosted-tree model and foundation models.

### 2.2.1 Research Gap

- Hair loss prediction studies used only classical algorithms, and their accuracies differ widely (about 50% to 100%) on different datasets.
- CatBoost was compared only once, and it was not tuned.
- TabPFN and TabFM have not been tested on hair loss data.
- TabFM has only one independent check, which reported software defects and memory limits.
- No study explains a boosted-tree model and foundation models side by side.
