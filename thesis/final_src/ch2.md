CHAPTER 2
LITERATURE REVIEW

This chapter surveys published work relevant to the study. It first reviews machine learning studies on hair loss (Section 2.1). It then reviews the three families of methods used in this study: tree ensembles and gradient boosting (Section 2.2), the debate on trees versus deep learning for tabular data (Section 2.3), and transformer-based tabular foundation models (Sections 2.4 and 2.5). Section 2.6 reviews explainability with SHAP, and Section 2.7 reviews the measures and tests used to compare classifiers. Section 2.8 brings the literature together, criticises it and identifies the gap that this study addresses.

2.1 Machine learning for hair loss prediction

Machine learning has been applied to hair loss with structured survey data, clinical data and scalp images. Studies using structured data are the most relevant here because the present study also uses tabular clinical and lifestyle features.

Widowati et al. [@widowati] developed an explainable decision-support system for multi-class hair loss severity classification. Their main methodological point was that feature transformations should be fitted only inside cross-validation folds, since fitting them on all the data inflates the estimated generalisation performance. This is a useful warning for any comparison of models, because leakage from preprocessing can favour one model over another without being noticed. Sayyad and Midhunchakkaravarthy [@sayyad] built a diagnostic model for Alopecia Areata and improved prediction for that condition, but their model did not cover the wider multi-factorial risk drivers of hair loss.

Several studies compared classifiers. Sai et al. [@sai] compared individual classification algorithms with an ensemble method for hair fall prediction and reported that the ensemble outperformed every individual algorithm on accuracy, precision and recall. Patel et al. [@patel] proposed a Random Forest framework using hereditary factors, hormonal markers, medical history and nutritional status, and found that Random Forest outperformed XGBoost, CatBoost and LightGBM on their dataset. Anderson and Roberts [@anderson] analysed survey-based lifestyle and clinical indicators, including dandruff severity, chronic illness history, thyroid function and micronutrient status, and used ROC-AUC and macro-F1 to account for class imbalance. Chen et al. [@chen] combined genetic, hormonal and scalp-condition data with lifestyle variables and compared standard classifiers with neural networks. The neural networks captured more complex feature interactions, but at the cost of interpretability of individual predictions.

Image-based approaches have also been reported. Shakeel et al. [@shakeel] extracted texture, shape and colour features from scalp images and classified healthy hair and Alopecia Areata with Support Vector Machine (SVM) and k-Nearest Neighbour (KNN) classifiers, obtaining 91.4% accuracy for SVM against 88.9% for KNN. Image-based work answers a different question from the present one, since it detects a visible condition, whereas risk stratification from laboratory and lifestyle data aims to estimate risk before hair loss is visible.

Table 2.1 summarises these studies.

Table 2.1: Summary of related studies on hair loss prediction

| Ref. | Focus | Approach | Main finding | Limitation relevant to this study |
|---|---|---|---|---|
| [@widowati] | Multi-class hair loss severity | Explainable decision-support system | Transformations must be kept inside cross-validation folds | Does not compare foundation models |
| [@sayyad] | Alopecia Areata | Machine learning diagnostic model | Improved prediction for one condition | Single condition, not multi-factorial risk |
| [@sai] | Hair fall prediction | Individual classifiers vs. an ensemble | Ensemble outperformed all individual classifiers | Classical models only |
| [@patel] | Hair fall prediction | Random Forest with hereditary, hormonal, medical and nutritional factors | Random Forest outperformed XGBoost, CatBoost and LightGBM | Conflicts with [@sai]; result specific to their dataset |
| [@chen] | Hair loss from genetic and scalp data | Classifiers vs. neural networks | Neural networks captured richer interactions | Lower interpretability |
| [@shakeel] | Healthy hair vs. Alopecia Areata | Image features with SVM and KNN | SVM 91.4%, KNN 88.9% accuracy | Image-based and binary; not tabular risk tiers |
| [@anderson] | Hair loss severity from survey data | Survey-based clinical and lifestyle features | Used ROC-AUC and macro-F1 for class imbalance | Not compared with foundation models |

A critical reading of these studies shows four points. First, the conclusions about the best model conflict: an ensemble was best in [@sai], whereas Random Forest beat several boosting methods in [@patel]. Because the datasets, targets and metrics differ, the two findings cannot be reconciled, and neither can be assumed to hold for a new dataset. Second, the studies target different outcomes (a single condition, image classes, or severity), so their reported accuracies are not comparable with each other or with the present study. Third, methodological care varies. Only [@widowati] stresses the control of leakage inside cross-validation, and only [@anderson] explicitly uses metrics that account for class imbalance. Fourth, interpretability is treated unevenly: [@chen] found that more flexible models were harder to interpret, and among these studies only [@widowati] was designed as an explainable system.

For the present study, these observations lead to three design decisions. The comparison of models is made on the same data, split and metrics, so that any difference can be attributed to the models. The metrics include macro-averaged measures, because the classes are unequal in size. The explanation method is applied to every model, so that interpretability is compared and not assumed.

2.2 Tree ensembles and gradient boosting

A single decision tree is easy to interpret but unstable, because small changes in the training data can change its structure. Ensemble learning combines several simple models to obtain a more accurate and stable prediction. In bagging-based ensembles such as Random Forest [@breiman01], many trees are grown on random samples of the data and random subsets of features, and their votes are combined. Random Forest is robust and needs little tuning, which is one reason it appears often in applied studies such as [@patel].

Boosting builds the ensemble in a different way: models are trained one after another, and each new model corrects the errors of the ensemble built so far. Friedman [@friedman01] showed that this can be treated as gradient descent in function space. At step m, a new tree h_m is fitted to the negative gradient of the loss (the pseudo-residuals) and added to the current model with a learning rate ν:

EQ[gbresid]: r_{im} = -\left[\frac{\partial L\big(y_i, F(x_i)\big)}{\partial F(x_i)}\right]_{F = F_{m-1}}

EQ[gbupdate]: F_m(x) = F_{m-1}(x) + \nu\, h_m(x)

Because each tree targets the remaining error, boosted trees can represent non-linear feature interactions that a single tree cannot, and they have long been the standard method for structured tabular data. XGBoost [@chen16] made this approach scalable by adding a regularised objective, sparsity-aware split finding and efficient system design, and LightGBM [@ke17] increased training speed with histogram-based splits and sampling techniques.

Encoding categorical variables is a recurring difficulty in boosting, since simple encodings can produce sparse features and leak information from the target. Prokhorenkova et al. [@prokhorenkova] proposed CatBoost to address this. It computes target statistics for categorical values using an artificial ordering of the training data, so that the statistic for a record never uses that record's own label, and it applies the same idea to the boosting procedure itself (ordered boosting) to reduce prediction shift. CatBoost also builds symmetric (oblivious) trees, in which the same split condition is used across a whole level, which acts as a regulariser and makes prediction fast. The authors reported better results than other boosting implementations on the benchmarks they used. These properties make CatBoost a strong, well-established baseline for tabular clinical data, which is why it is used as the tuned reference model in this study. The finding of Patel et al. [@patel] that Random Forest outperformed CatBoost shows, however, that the ranking of tuned tree-based methods depends on the dataset.

2.3 Tree-based models and deep learning on tabular data

Deep learning has been very successful on images and text, but its advantage on tabular data has been questioned. Shwartz-Ziv and Armon [@shwartz22] compared XGBoost with several recent deep models on datasets that were not used in the deep models' original papers. XGBoost generally performed better on those datasets and needed much less tuning, and an ensemble of the deep models with XGBoost performed better than either alone. Grinsztajn et al. [@grinsztajn22] carried out a large benchmark and concluded that tree-based models remained state of the art on medium-sized tabular datasets, even when their speed advantage was ignored, and they discussed properties of tabular data (such as uninformative features and irregular target functions) that suit trees better than standard neural networks.

Tuning is a real cost. A gradient-boosted model has several hyperparameters, and finding good values means training the model many times, usually with cross-validation, and it needs some experience to choose sensible ranges. A method that gives comparable results without this step would save time, and it would also remove one source of unfairness in comparisons, namely that a baseline may be tuned more or less carefully than the new method. In the present study CatBoost was tuned by grid search so that the baseline was not handicapped.

These studies matter for the present work in two ways. They justify the use of a tuned gradient-boosted model as the strong baseline that any new method must be compared with. They also explain why tabular foundation models attracted attention: if a pretrained model can match tuned trees without a tuning stage, it would remove a step that currently takes time and expertise.

2.4 Transformers, attention and in-context learning

The transformer architecture [@vaswani17] is built on the attention mechanism. Each element of the input is compared with every other element, and the comparison determines how much each element contributes to the representation of the others. In scaled dot-product attention, the queries Q, keys K and values V are combined as:

EQ[attention]: \mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\left(\frac{Q K^{T}}{\sqrt{d_k}}\right) V

where d_k is the dimension of the keys. Attention lets the model relate any element of the input to any other regardless of their distance, and it can be computed for all elements in parallel, which is one reason why transformers can be trained on very large collections of data. Large language models showed that a transformer trained once on a very large collection of data can perform new tasks from examples placed in its input, without any change to its weights. This is called in-context learning, and a model that supports it across many tasks is called a foundation model.

Applied to tabular data, the idea is to pretrain a transformer on a very large number of artificial tabular datasets, so that it learns the general skill of predicting a target from labelled examples. At prediction time, the labelled training rows are given to the model as context together with the query rows, and the prediction is obtained in a single forward pass with no gradient-based training. The training set therefore does not change the model's weights, and it acts instead as input. A consequence is that the cost of a prediction grows with the size of the context, which matters in practice (Section 4.4).

2.5 Tabular foundation models

TabPFN [@hollmann23] introduced this idea for tabular classification. It was presented as a transformer that solves small tabular classification problems in about a second, without hyperparameter tuning. A later version, published in Nature [@hollmann25], extended the approach to larger and more varied tables. The authors reported that it outperformed tuned tree-based ensembles on datasets of up to 10,000 samples and 500 features, in much less time. This is the evidence behind the expectation that zero-shot models can compete with tuned boosting on small and medium-sized tables. The dataset used in the present study has 21,606 records, so its full training partition (17,284 rows) is larger than the range for which that result was reported, which makes the comparison in this study informative about behaviour beyond that range.

TabFM [@kong], released by Google Research, is a more recent model. It alternates row-wise and column-wise attention over the input table before an in-context transformer produces the predictions, whereas TabPFN applies attention mainly across samples. On the TabArena benchmark suite it was reported to outperform heavily tuned gradient-boosted baselines in a purely zero-shot setting [@kong]. An independent evaluation by a third party [@pauli], run on three machines and thirteen datasets, confirmed its competitive zero-shot accuracy against XGBoost, Random Forest and TabPFN, but it also documented four defects in the official implementation. The evidence reviewed here on TabFM comes from general benchmarks, not from health or dermatology data, and it comes from a company blog and a public repository, not from peer-reviewed publication. It should therefore be treated as provisional, which is one reason why testing TabFM independently on a new problem is useful.

The two foundation models differ in design, and the difference matters for how they are used. In TabPFN, attention is applied mainly across the samples of the table, so each query row is related to the labelled rows in the context. In TabFM, attention is applied alternately across rows and across columns before the in-context transformer reads the compressed representation of each row. Both approaches make the training data part of the input at prediction time. This has three consequences for a practical comparison. First, the amount of context that can be used is limited by memory and time, and a large training set may have to be reduced to a smaller context. Second, the cost of each prediction depends on the context size and not only on the model, which is unlike a boosted-tree model whose prediction cost is small once it is trained. Third, the training data must be available whenever predictions are made, which is a consideration for deployment. These points are examined for hair fall data in Chapter 4.

2.6 Explainability with SHAP

Boosted ensembles and attention-based models both give no direct explanation for an individual prediction. In clinical use this is a serious limitation, because a practitioner needs a reason for a risk estimate before acting on it. Shapley values, introduced in cooperative game theory [@shapley53], distribute the payoff of a game fairly among its players according to their contributions. Lundberg and Lee [@lundberg17] applied this idea to prediction. In their SHAP framework each feature is a player and the model output is the payoff, and the prediction for an instance is split into additive contributions:

EQ[shapadd]: f(x) = \phi_0 + \sum_{j=1}^{M} \phi_j

where φ_0 is the expected model output and φ_j is the contribution of feature j. The Shapley value of feature j averages its marginal contribution over all subsets S of the other features F:

EQ[shapley]: \phi_j = \sum_{S \subseteq F \setminus \{j\}} \frac{|S|!\,(|F|-|S|-1)!}{|F|!}\Big[f_{S \cup \{j\}}(x) - f_S(x)\Big]

Lundberg and Lee [@lundberg17] showed that this is the only additive attribution that satisfies the properties of local accuracy, missingness and consistency. Computing Eq. ({eq:shapley}) exactly requires evaluating the model for a number of feature subsets that grows exponentially with the number of features, so practical algorithms are needed. For tree models, TreeExplainer [@lundberg20] computes exact values in polynomial time by using the tree structure. For models without such structure, Kernel SHAP [@lundberg17] estimates the values by querying the model on perturbed inputs and fitting a weighted linear regression. It works for any model, but the number of model calls grows with the number of explained instances and the number of samples per instance, which is costly when each call is expensive, as with an in-context transformer.

The results of a SHAP analysis are usually shown in three ways. A global bar plot ranks features by their mean absolute contribution. A beeswarm plot shows, for every explained record, the contribution of each feature and colours it by the feature's value, so that the direction of the effect can be read (for example, whether high values of a feature raise or lower the prediction). A waterfall plot shows how the contributions of the features of one record move the prediction from the baseline to its final value. All three are used in Chapter 4.

SHAP supports both a global view (mean absolute values give an importance ranking across the dataset) and a local view (the contribution of each feature to one patient's prediction). SHAP explains what a model has learned, and it does not show that the relationships are causal. The same method can be applied to different model types, which is why it was chosen here. Two cautions apply in practice. An explanation is only as reliable as the model, so a model that has learned a spurious pattern will give an explanation that reflects the pattern. In addition, Kernel SHAP values are estimates: they depend on the number of samples per instance and on the background data, and when only a few instances are explained the ranking of features with similar importance can change from one run to another. This is why the analysis in Chapter 4 relies on the shared set of leading features and not on the exact order.

2.7 Evaluating and comparing classifiers

Accuracy, the proportion of correct predictions, can be misleading when classes differ in size, because a model that favours the largest class can still score well. Sokolova and Lapalme [@sokolova09] analysed performance measures for classification and described macro-averaging, in which a measure such as precision, recall or the F1-score is computed for each class and then averaged with equal weight, so that small classes count as much as large ones. For multi-class problems, ROC-AUC can be computed by treating each class in turn against all the others and averaging the results.

Reporting differences between two classifiers also requires a statistical test. McNemar's test [@mcnemar47] compares two classifiers evaluated on the same test records. It uses only the records on which the two classifiers disagree: b records that the first classified correctly and the second did not, and c records for the reverse. Under the null hypothesis that both make errors at the same rate, b and c are expected to be equal. Dietterich [@dietterich98] compared several tests for supervised learning algorithms and found that McNemar's test has a low rate of false positive results and is a suitable choice when each algorithm can be trained and run only once, as was the case here. The test has limits. It does not measure variation from the choice of training set or from random seeds, and a non-significant result does not show that the classifiers are equivalent, only that no difference was detected.

Model selection needs care as well. Hyperparameters such as the depth of a tree should be chosen on data that is not used for the final test, and k-fold cross-validation does this by repeatedly training on part of the training data and scoring on the remaining part. Stratified folds keep the class proportions in every fold, which matters when classes are unequal. Selecting hyperparameters on the test data would give an optimistic estimate of performance, which is the kind of leakage that Widowati et al. [@widowati] warned about.

The risk tiers in this study are ordered (Low, Moderate, High), and standard multi-class classifiers treat them as unrelated labels. Ordinal classification methods take the order into account. Frank and Hall [@frank01], for example, proposed a simple approach that turns an ordinal problem with k classes into k−1 binary problems, each asking whether the target is greater than a given tier, so that any binary classifier can be used. Such methods may improve results for the middle tier of an ordered scale. They were not part of this study, whose aim was to compare three methods on the standard multi-class task, and they are noted as further work (Section 5.3).

2.8 Critical summary and research gap

Table 2.2 brings the reviewed methods together.

Table 2.2: Model families relevant to this study

| Model family | Representative studies | Strengths | Known limitations | Role in this study |
|---|---|---|---|---|
| Random Forest and other classical classifiers | [@breiman01], [@sai], [@patel] | Robust, little tuning | Ranking versus boosting varies by dataset | Not evaluated (context only) |
| Gradient-boosted trees | [@friedman01], [@chen16], [@ke17], [@prokhorenkova] | Strong on tabular data; tuned baseline | Needs tuning; needs enough training data | CatBoost, tuned baseline |
| Neural networks | [@chen], [@shwartz22], [@grinsztajn22] | Can capture complex interactions | Often no better than trees on tabular data; harder to interpret | Not evaluated (context only) |
| Tabular foundation models | [@hollmann23], [@hollmann25], [@kong], [@pauli] | No tuning; strong with small data | Cost grows with context; TabFM evidence provisional | TabPFN and TabFM, zero-shot |
| Post-hoc explanation | [@shapley53], [@lundberg17], [@lundberg20] | Model-agnostic feature attribution | Kernel estimation is costly for large-context models | SHAP for all three models |

Three points follow from Table 2.2. Tuned gradient boosting is the method that any new tabular method must be compared with, so a fair benchmark needs a properly tuned CatBoost and not a default configuration. Tabular foundation models are promising mainly because they remove the tuning step and work with little data, so a fair benchmark also needs a varied training size and not only the full dataset. Finally, since both kinds of model are opaque, a fair benchmark for health data should compare what each model relies on, and not only how accurate it is. The design of the present study follows these three points (Chapter 3).

A further point concerns the data. A dataset built by combining sources, as in this study, has feature-target relationships that are set by the rules used to build it. A model trained on such a dataset can be expected to recover those rules, and how well it does so is informative about the model. It says little about how the model would perform on patients from a real clinic, where the relationships are noisier and are not known in advance. For this reason the study is presented as a benchmark of model behaviour and not as a clinical validation.

The reviewed work shows the following.

1. Studies on hair loss prediction have used classical classifiers, ensembles, Random Forest, neural networks and image features [@widowati]–[@shakeel], [@anderson]. Their conclusions about the best model conflict ([@sai] versus [@patel]), and their targets differ, so the results are not comparable.
2. Interpretability remains a concern. The neural models in [@chen] were harder to interpret, and among the reviewed hair loss studies only [@widowati] was designed as an explainable system.
3. Tuned gradient boosting is an established baseline for tabular data [@shwartz22], [@grinsztajn22], and CatBoost [@prokhorenkova] is a leading implementation, but it has not been compared with tabular foundation models on hair fall data.
4. TabPFN [@hollmann23], [@hollmann25] and TabFM [@kong] have been evaluated only on general benchmarks. No reviewed study evaluates them on health survey data, compares the two models with each other and with a tuned gradient-boosted model, or applies a common explanation method to all of them. TabFM's reliability is also only partly established [@pauli].
5. The behaviour of these models when training data is limited, which is common in health settings, has not been examined for hair fall risk, and neither has the cost of explaining large-context models with model-agnostic SHAP.

This study addresses these gaps by benchmarking CatBoost, TabPFN and TabFM on multi-tier hair fall risk classification with the same data, split and metrics, by varying the training context size, and by applying SHAP to all three models.
