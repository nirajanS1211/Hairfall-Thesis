CHAPTER 5
CONCLUSION AND RECOMMENDATIONS

5.1 Conclusion

This study set out to benchmark CatBoost, TabPFN and TabFM for explainable, multi-tier (Low, Moderate, High) hair fall risk stratification from structured clinical and lifestyle data. It was motivated by three gaps identified in Section 1.2: the evidence on the best model for hair fall data was inconsistent, tabular foundation models had not been tested on this problem, and complex models were hard to interpret. The four research questions of Section 1.3 are answered below, using the results of Chapter 4.

Predictive performance (Research Question 1). The three models reached close results on the 4,322-record test partition. Accuracy was 78.51% for CatBoost, 78.57% for TabPFN and 77.88% for TabFM, and macro-F1 was 0.7763, 0.7787 and 0.7715. McNemar's test found no significant difference between any pair of models at the 0.05 level. On this dataset, therefore, no advantage of the tuned gradient-boosted model over the two zero-shot models was detected, even though only CatBoost was tuned and TabFM used a 500-row context, under 3% of the training records. This does not prove that the models are equivalent.

Effect of training context size (Research Question 2). When the training context was reduced to 100 and 500 rows, both foundation models scored clearly higher than CatBoost. At 100 rows the accuracy was 60.53% for CatBoost, 71.54% for TabPFN and 74.41% for TabFM, and at 500 rows it was 69.64%, 77.65% and 77.88%. The gap narrowed as the context grew, and CatBoost matched TabPFN with the full training partition. At 500 rows, CatBoost was 8.87 points below its full-data accuracy and TabPFN was 0.92 points below its own. The tuned gradient-boosted model therefore depended most on the amount of training data. Because two independently developed foundation models behaved in the same way on this dataset, the behaviour does not seem to be specific to one design, although only one dataset was tested. The ranking of TabFM and TabPFN with each other was not reliable at any size.

Explainability (Research Question 3). SHAP explanations were produced for all three models. The same seven features (iron, stress_level, total_protein, vitamin_d, alt_liver, calcium and manganese) were the most influential in each, and the direction of their effects was the same: higher stress_level and alt_liver values raised the predicted High risk contribution, and higher iron, total_protein, vitamin_d, calcium and manganese values lowered it. This agrees with the relationships used to build the dataset, so it shows that the models recovered those relationships and it is not new clinical evidence.

Computational cost and implementation (Research Question 4). CatBoost and TabPFN ran without difficulty, but TabFM was slow and its running time rose steeply with context size. Its full-context evaluation could not be completed, so a 500-row context was used. The runs also exposed software problems: the planned PermutationExplainer failed because of a numba error and was replaced with KernelExplainer, TabFM failed on single-row input, and TabPFN's checkpoint loading needed a workaround. These problems came from the recency of the software and not from the modelling approaches.

In summary, on this dataset a tuned gradient-boosted model and two zero-shot foundation models gave comparable accuracy, the foundation models were much less dependent on the amount of training data, and all three could be explained with SHAP. This meets the general objective of the study, within the limits described in Section 5.2.

The problem stated in Section 1.2 was that the evidence on the best model for hair fall data was inconsistent, that tabular foundation models had not been tested on it, and that complex models were hard to interpret. The general objective of Section 1.4 was to benchmark the three models for explainable multi-tier hair fall risk stratification, and each of the four specific objectives was met by the analyses in Sections 4.1 to 4.4. The comparison was made on one dataset, so the conclusions describe the behaviour of the models on this dataset and should not be generalised beyond it.

The contribution of the study can be stated in four points. It is a benchmark of two independently developed tabular foundation models against a tuned gradient-boosted model on multi-tier hair fall risk classification, a comparison that the reviewed literature did not contain (Section 2.8). It shows, with matched training contexts, how the models differ when data are limited. It applies one explanation method to three different architectures and checks the explanations against the relationships measured in the data (Section 4.3). It also documents the runtime and software problems met with a recently released model, which may help others who plan to use it.

5.2 Limitations of the study

The conclusions must be read with the following limitations.

1. The dataset was assembled from two public sources and adjusted with domain-informed relationships (Section 3.7). It was not drawn from a clinical registry, so the results show how the models perform on this dataset and are not the validation of a diagnostic tool.
2. TabFM used a 500-row context while CatBoost and TabPFN used 17,284 rows, so no evaluation compares all three at full scale. The 2,000-row run used a 500-record test subset, so it is less precise and not directly comparable with the other sizes. No significance tests were run at reduced contexts.
3. The SHAP analyses of TabPFN and TabFM used a reduced training context and only 30 and 20 test records, so their attributions are less certain than CatBoost's exact values on the full test partition.
4. CatBoost's final fit used the test partition to monitor early stopping, so the test data influenced the number of trees selected (Section 3.8.4). A separate validation split would be cleaner.
5. All results come from one train/test split with one random seed. Confidence intervals were given only for accuracy (Table 4.6) and describe the uncertainty from the finite test sample, not the variation between splits or seeds.
6. The Moderate tier was the hardest to classify in all three models. The study offered an explanation based on the ordered structure of the target but did not test an ordinal model.

5.3 Recommendations

Recommendations for practice. These follow from the findings and apply to structured data of a similar kind.

1. Where labelled data are limited, a zero-shot tabular foundation model such as TabPFN is a reasonable first choice, since it reached the accuracy of the tuned CatBoost without tuning and lost much less accuracy when the training data were reduced.
2. The running time of TabFM should be measured at the intended context size before an evaluation is planned, because its cost grew steeply with the context.
3. Feature-level explanations such as SHAP should accompany any risk prediction, and in this study they were available for all three models. Any use in a health setting should be as decision support and only after validation on real clinical data.

Recommendations for further research. These address the limitations above.

1. Evaluate TabFM with the full training context when its software or the available hardware allows, so that all three models can be compared under identical conditions.
2. Repeat the context-size experiment on the full test partition at every size, with several random seeds and McNemar's test at each size, to find out whether the differences between the foundation models are reliable.
3. Use repeated cross-validation or several random splits with confidence intervals, and a separate validation partition for CatBoost's early stopping.
4. Compute SHAP values for the foundation models on more test records and with larger contexts, so that the feature order can be compared more closely.
5. Compare ordinal-aware models with the multi-class approach, to see whether they improve the classification of the Moderate tier.
6. Validate the framework on real clinical hair loss data when ethically cleared data become available.
7. Study ensembles of the three models, and distillation of the foundation models into lightweight models, since TabPFN and TabFM need their training data at prediction time.

Each recommendation follows from a finding. The first recommendation for practice rests on the results of Section 4.1 and Section 4.2, the second on the runtimes in Section 4.4, and the third on the explanations in Section 4.3. Each recommendation for further research addresses one of the limitations in Section 5.2: the unequal contexts, the small significance tests at reduced sizes, the single split, the small SHAP samples, the Moderate tier, the constructed dataset and the untested ensembles. The recommendations are limited to the scope of this study and to structured data of a similar kind.
