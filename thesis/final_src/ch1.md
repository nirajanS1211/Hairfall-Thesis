CHAPTER 1
INTRODUCTION

This chapter introduces the study. It presents the background of hair fall risk prediction (Section 1.1), the statement of the problem (Section 1.2), the research questions (Section 1.3), the research objectives (Section 1.4) and the significance of the study (Section 1.5). The thesis has five chapters. Chapter 2 reviews the literature, Chapter 3 describes the methodology, Chapter 4 presents and discusses the results, and Chapter 5 gives the conclusion and recommendations. The references and appendices follow Chapter 5.

Scope of the study. The study is limited to three-tier (Low, Moderate, High) hair fall risk classification from structured tabular clinical and lifestyle data. The dataset has 21,606 records, assembled from two public datasets and adjusted with domain-informed relationships. Three models are compared: CatBoost, TabPFN and TabFM. They are evaluated on one held-out test partition with accuracy, macro-averaged precision, recall and F1-score, ROC-AUC (area under the receiver operating characteristic curve) and McNemar's test, and their predictions are explained with SHAP (Shapley Additive Explanations).

Limitations of the study. The dataset was constructed and not drawn from a clinical registry, so the results show model capability on this data and are not a validated diagnostic tool. TabFM was evaluated with a 500-row training context because of its runtime, and the SHAP analysis of the two foundation models used a reduced training context and a small sample of test records. Scalp images, free-text records and other hair or scalp conditions are outside the scope of the study.

1.1 Background

Hair loss, known clinically as alopecia, affects people of all ages and backgrounds. Some daily shedding is a normal part of the hair growth cycle. A marked or sudden increase in shedding, however, often signals a deeper disturbance such as hormonal imbalance, nutrient deficiency, physical strain or prolonged psychological stress. Visible hair loss also carries an emotional cost, and it is commonly linked to lower self-confidence, anxiety and a reduced sense of well-being.

Hair grows in cycles. Each follicle passes through a growth phase, a short transition phase and a resting phase, after which the hair is shed and a new hair begins to grow. In a healthy scalp only a small share of hairs is shed each day. Hair fall becomes a concern when more follicles than usual enter the resting phase and are shed together. This can be triggered by physical or psychological stress, inadequate nutrition, illness and hormonal change, so very different conditions can produce the same visible result. This is one reason why no single test identifies the risk, and why an estimate based on several measurements together is more informative than a judgement based on one.

Predicting who is at risk is difficult because no single biomarker reliably indicates hair loss. Risk arises from the combined and non-linear interaction of many factors, including iron and protein levels, vitamin D status, liver function, stress, sleep habits, exposure to chemical hair treatments, chronic illness and family history. Because these factors act together, it is impractical for a clinician or an individual to judge overall risk by observation alone. In practice, assessment still depends largely on self-reported history and delayed clinical examination, which are subjective, inconsistent between observers and hard to reach in under-resourced settings.

Much of the data that could support a more objective assessment is tabular. Laboratory results, demographic details, clinical history and lifestyle indicators are naturally stored as rows and columns, and Electronic Health Records (EHRs) hold such data in large volumes. Machine learning can find patterns in this kind of data that are hard to notice manually, and several studies have applied it to hair loss. Widowati et al. [@widowati] built an explainable decision-support system for multi-class hair loss severity classification and showed that feature transformations must be restricted to within cross-validation folds to avoid inflated performance estimates. Sayyad and Midhunchakkaravarthy [@sayyad] developed a diagnostic model for Alopecia Areata, but it addressed a single condition rather than the wider set of risk factors behind hair loss. Sai et al. [@sai] compared individual classifiers with an ensemble method for hair fall prediction and found that the ensemble performed better on accuracy, precision and recall. Patel et al. [@patel] proposed a Random Forest framework using hereditary, hormonal, nutritional and medical-history factors. Chen et al. [@chen] combined genetic, hormonal, scalp and lifestyle data and observed that neural networks captured more complex feature interactions but were harder to interpret. Image-based work has also been done: Shakeel et al. [@shakeel] extracted texture, shape and colour features from scalp images and classified healthy hair and Alopecia Areata with Support Vector Machine (SVM) and k-Nearest Neighbour (KNN) classifiers.

On structured data, gradient-boosted decision trees have long been the standard approach. CatBoost [@prokhorenkova] is one such method, designed to handle categorical features and to reduce target leakage through ordered target encoding. A newer family of models, tabular foundation models, takes a different route. These are transformers pretrained on large collections of synthetic datasets, and they predict directly from the training data supplied as context in a single forward pass, without dataset-specific training. TabPFN [@hollmann23] introduced this idea, and TabFM [@kong], released by Google Research, extends it with attention applied alternately across rows and columns. Reports on the TabArena benchmark suggest that TabFM can outperform heavily tuned gradient-boosted models in a purely zero-shot setting [@kong], and an independent reproduction has confirmed its competitive accuracy while also documenting defects in the official implementation [@pauli].

Predictive accuracy alone is not enough in a health setting, because a practitioner needs to know why a model reached its output. Both boosted ensembles and transformer models are opaque by default. SHAP (Shapley Additive Explanations) [@lundberg17] addresses this by attributing a prediction to individual input features using Shapley values from cooperative game theory, and it can be applied to very different model types. This makes it suitable for comparing explanations across architectures.

The literature reviewed above shows that hair loss prediction has mostly relied on classical classifiers, that interpretability is a recognised concern for the more complex models, and that tabular foundation models have not been evaluated against gradient boosting on hair fall data. To our knowledge, no study has compared more than one foundation model on this task. These gaps motivate the present study, which benchmarks CatBoost, TabPFN and TabFM for multi-tier hair fall risk classification (Low, Moderate and High) on structured clinical and lifestyle data and applies SHAP to all three models.

1.2 Statement of the problem

Hair fall risk is hard to assess objectively. It depends on the combined effect of nutritional, hormonal, metabolic, lifestyle and hereditary factors, and no single indicator is reliable on its own (Section 1.1). Current practice relies on self-reported history and delayed clinical examination, which vary between observers and are difficult to access in under-resourced settings. Machine learning can model these interacting factors, but the existing work has three shortcomings that make it inadequate for this purpose.

First, the evidence on which model suits hair fall data is inconsistent. Sai et al. [@sai] found that an ensemble method outperformed individual classifiers, whereas Patel et al. [@patel] found that Random Forest outperformed XGBoost, CatBoost and LightGBM. Studies also differ in target (a single condition such as Alopecia Areata [@sayyad], image-based classification [@shakeel], or survey-based severity [@widowati]), so their results cannot be compared directly. No clear, well-founded choice of model exists for structured hair fall data.

Second, tabular foundation models have not been tested on this problem. TabPFN [@hollmann23] and TabFM [@kong] predict from supplied context without dataset-specific training, and TabFM has been reported to outperform heavily tuned gradient-boosted trees on the TabArena benchmark [@kong]. That evidence comes from general benchmarks, not from health survey data. It is therefore unknown whether these models can match a tuned gradient-boosted model such as CatBoost [@prokhorenkova] on hair fall risk, or whether the result holds across more than one foundation model. The reliability of a newly released model such as TabFM also needs checking, since an independent reproduction found defects in its official implementation [@pauli].

Third, the models that capture complex feature interactions are difficult to interpret. Chen et al. [@chen] observed that neural models gained accuracy at the cost of per-prediction interpretability, and the same opacity applies to boosted ensembles and transformers. Without feature-level explanations, a predicted risk level cannot be checked against known clinical reasoning, and this limits its usefulness for decision support.

These gaps make the research necessary. A comparison of CatBoost, TabPFN and TabFM on the same data, split and metrics, with SHAP explanations for all three, is needed to establish whether tuning-free foundation models can replace tuned gradient boosting for multi-tier (Low, Moderate, High) hair fall risk classification, and whether their predictions can be traced to interpretable clinical and lifestyle indicators.

1.3 Research questions

Based on the problem stated in Section 1.2, this study seeks to answer the following research questions:

1. Can the zero-shot tabular foundation models TabPFN and TabFM match the predictive performance of a tuned CatBoost model in classifying multi-tier (Low, Moderate, High) hair fall risk from structured clinical and lifestyle data, and are the differences between the three models statistically significant?

2. How does the amount of training data supplied (the training context size) affect the performance of CatBoost, TabPFN and TabFM, and which model uses limited data most efficiently?

3. Which clinical and lifestyle features contribute most to the predicted risk tier in each model, and are these contributions consistent across the three models and clinically plausible?

4. What are the practical computational costs and implementation limitations (runtime, memory and software reliability) of using each model, particularly the recently released TabFM?

1.4 Research objectives

General objective

To benchmark CatBoost, TabPFN and TabFM for explainable multi-tier (Low, Moderate, High) hair fall risk stratification from structured clinical and lifestyle data.

Specific objectives

1. To compare the predictive performance of a tuned CatBoost model with that of the zero-shot TabPFN and TabFM models using accuracy, macro-precision, macro-recall, macro-F1 and ROC-AUC, and to test whether the differences between them are statistically significant.

2. To evaluate how the training context size affects the performance of the three models, and to identify which model uses limited training data most efficiently.

3. To explain the predictions of the three models with SHAP and to compare the features that contribute most to the predicted risk tier across the models.

4. To assess the computational cost and implementation limitations of the three models, with particular attention to the recently released TabFM.

1.5 Significance/Rationale of the study

This study is justified by the gaps identified in Section 1.2. It compares a tuned gradient-boosted model with two tabular foundation models on the same hair fall data and explains all three with SHAP. The main beneficiaries and the ways they benefit are as follows.

Clinicians and dermatology practitioners. A model that estimates Low, Moderate or High hair fall risk from routine laboratory values and lifestyle information can support earlier screening and a more consistent assessment than self-reported history alone. Because SHAP attributes each prediction to specific indicators such as iron, protein, vitamin D and stress level, a practitioner can check the result against clinical knowledge instead of accepting it as a black box. The study is intended as decision support, not as a replacement for clinical diagnosis.

Individuals at risk of hair loss. Risk tiers linked to identifiable, modifiable factors (for example nutritional status, stress and sleep habits) can help people recognise early warning signs and seek advice sooner. This is particularly useful where access to specialist dermatological care is limited.

Machine learning researchers and practitioners working with tabular data. The study gives a controlled comparison of two independently developed foundation models, TabPFN and TabFM, against a tuned CatBoost baseline. The context-size analysis shows how much training data each model needs, which matters where labelled clinical data is scarce. The record of TabFM's runtime behaviour and implementation problems helps others decide whether to adopt this recently released model.

Future researchers. The study uses one dataset, split, set of metrics and explanation method for all three models, and it reports the limits of the data and of the computing resources available. This provides a reproducible reference for later work, such as evaluation on real clinical data or ordinal classification methods.

Beyond these groups, the study has value for the research community as a documented example of how a new class of models can be evaluated fairly on a health problem. It shows the steps that a fair comparison needs: a tuned baseline, the same data and split for every model, a statistical test, a variation of the training size and an explanation method applied to every model. It also records the practical problems that arose with a recently released model, which are usually left out of benchmark reports.

Overall, the study helps establish whether tuning-free foundation models can replace tuned gradient boosting for structured health risk prediction while keeping predictions explainable.
