CHAPTER 2
LITERATURE REVIEW

This chapter surveys published work relevant to the study. It covers machine learning for hair loss prediction, gradient-boosted decision trees, tabular foundation models and explainability with SHAP. It ends by identifying the gap that this study addresses.

2.1 Machine learning for hair loss prediction

Machine learning has been applied to hair loss with structured survey data, clinical data and scalp images. Studies using structured data are the most relevant here because the present study also uses tabular clinical and lifestyle features.

Widowati et al. [1] developed an explainable decision-support system for multi-class hair loss severity classification. Their main methodological point was that feature transformations should be fitted only inside cross-validation folds, since fitting them on all the data inflates the estimated generalisation performance. Sayyad and Midhunchakkaravarthy [2] built a diagnostic model for Alopecia Areata and improved prediction for that condition, but their model did not cover the wider multi-factorial risk drivers of hair loss.

Several studies compared classifiers. Sai et al. [3] compared individual classification algorithms with an ensemble method for hair fall prediction and reported that the ensemble outperformed every individual algorithm on accuracy, precision and recall. Patel et al. [4] proposed a Random Forest framework using hereditary factors, hormonal markers, medical history and nutritional status, and found that Random Forest outperformed XGBoost, CatBoost and LightGBM on their dataset. Anderson and Roberts [12] analysed survey-based lifestyle and clinical indicators, including dandruff severity, chronic illness history, thyroid function and micronutrient status, and used ROC-AUC and macro-F1 to account for class imbalance. Chen et al. [5] combined genetic, hormonal and scalp-condition data with lifestyle variables and compared standard classifiers with neural networks. The neural networks captured more complex feature interactions, but at the cost of interpretability of individual predictions.

Image-based approaches have also been reported. Shakeel et al. [6] extracted texture, shape and colour features from scalp images and classified healthy hair and Alopecia Areata with SVM and KNN, obtaining 91.4% accuracy for SVM against 88.9% for KNN.

Table 2.1 summarises these studies.

Table 2.1: Summary of related studies on hair loss prediction

| Ref. | Focus | Approach | Main finding | Limitation relevant to this study |
|---|---|---|---|---|
| [1] | Multi-class hair loss severity | Explainable decision-support system | Transformations must be kept inside cross-validation folds | Does not compare foundation models |
| [2] | Alopecia Areata | Machine learning diagnostic model | Improved prediction for one condition | Single condition, not multi-factorial risk |
| [3] | Hair fall prediction | Individual classifiers vs. an ensemble | Ensemble outperformed all individual classifiers | Classical models only |
| [4] | Hair fall prediction | Random Forest with hereditary, hormonal, medical and nutritional factors | Random Forest outperformed XGBoost, CatBoost and LightGBM | Conflicts with [3]; result specific to their dataset |
| [5] | Hair loss from genetic and scalp data | Classifiers vs. neural networks | Neural networks captured richer interactions | Lower interpretability |
| [6] | Healthy hair vs. Alopecia Areata | Image features with SVM and KNN | SVM 91.4%, KNN 88.9% accuracy | Image-based and binary; not tabular risk tiers |
| [12] | Hair loss severity from survey data | Survey-based clinical and lifestyle features | Used ROC-AUC and macro-F1 for class imbalance | Not compared with foundation models |

2.2 Gradient-boosted decision trees and CatBoost

Ensemble learning combines several simple models to obtain a more accurate and stable prediction. In boosting, models are trained one after another and each new model corrects the errors of the ensemble built so far. Gradient boosting treats this correction as a numerical optimisation problem, fitting each new tree to the remaining errors of the current ensemble. Because of this, boosted trees can represent non-linear feature interactions that a single tree cannot, and they have long been the standard method for structured tabular data.

Encoding categorical variables is a recurring difficulty in boosting, since simple encodings can produce sparse features and leak information from the target. Prokhorenkova et al. [7] proposed CatBoost to address this. It uses ordered target statistics and ordered boosting to prevent target leakage, and reported better results than other boosting implementations on the benchmarks they used. These properties make CatBoost a strong, well-established baseline for tabular clinical data, which is why it is used as the tuned reference model in this study. The finding of Patel et al. [4] that Random Forest outperformed CatBoost shows, however, that the ranking of tuned tree-based methods depends on the dataset.

2.3 Tabular foundation models

A newer approach borrows the idea of foundation models from language modelling. A model is pretrained once, offline, on a large collection of synthetic datasets, so that it learns tabular prediction as a general skill. At prediction time it receives the labelled training rows as context together with the query rows, and it outputs predictions in a single forward pass without gradient-based training. This is called in-context learning, and it is implemented with the self-attention mechanism of transformers.

TabPFN [8] introduced this idea for tabular classification. It was presented as a transformer that solves small tabular classification problems in about a second, without hyperparameter tuning.

TabFM [9], released by Google Research, is a more recent model. It alternates row-wise and column-wise attention over the input table before an in-context transformer produces the predictions, whereas TabPFN applies attention mainly across samples. On the TabArena benchmark suite it was reported to outperform heavily tuned gradient-boosted baselines in a purely zero-shot setting [9]. An independent evaluation by a third party [10], run on three machines and thirteen datasets, confirmed its competitive zero-shot accuracy against XGBoost, Random Forest and TabPFN, but it also documented four defects in the official implementation. The evidence reviewed here on TabFM comes from general benchmarks, not from health or dermatology data.

2.4 Explainability with SHAP

Boosted ensembles and attention-based models both give no direct explanation for an individual prediction. In clinical use this is a serious limitation, because a practitioner needs a reason for a risk estimate before acting on it. Lundberg and Lee [11] proposed SHAP, which is based on Shapley values from cooperative game theory. Each feature is treated as a player and the model output as the payoff, and the prediction is split into additive contributions of the individual features. SHAP can be applied to any model, so the explanations of different architectures can be compared on the same basis. Accuracy alone is not sufficient in clinical use, and feature attributions allow practitioners to compare model outputs with known biological mechanisms.

2.5 Research gap

The reviewed work shows the following:

1. Studies on hair loss prediction have used classical classifiers, ensembles, Random Forest, neural networks and image features [1]–[6], [12]. Their conclusions about the best model conflict ([3] versus [4]), and their targets differ, so the results are not comparable.
2. Interpretability remains a concern. The neural models in [5] were harder to interpret, and among the reviewed hair loss studies only [1] was designed as an explainable system.
3. CatBoost [7] is an established boosting baseline for tabular data, but it has not been compared with tabular foundation models on hair fall data.
4. TabPFN [8] and TabFM [9] have been evaluated only on general benchmarks. No reviewed study evaluates them on health survey data, compares the two models with each other and with a tuned gradient-boosted model, or applies a common explanation method to all of them. TabFM's reliability is also only partly established [10].

This study addresses these gaps by benchmarking CatBoost, TabPFN and TabFM on multi-tier hair fall risk classification with the same data, split and metrics, and by applying SHAP to all three models.
