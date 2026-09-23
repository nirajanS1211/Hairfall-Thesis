CHAPTER 4
RESULTS AND DISCUSSION

This chapter presents the findings of the study in the order of the specific objectives in Section 1.4. Section 4.1 compares the predictive performance of the three models (Objective 1). Section 4.2 reports the effect of training context size (Objective 2). Section 4.3 presents the SHAP explanations (Objective 3). Section 4.4 reports computational cost and implementation limitations (Objective 4). Section 4.5 discusses the plausibility of the findings and compares them with similar studies. Unless stated otherwise, all results were obtained on the held-out test partition of 4,322 records (1,945 Low, 1,513 Moderate and 864 High), and CatBoost and TabPFN used all 17,284 training records while TabFM used a 500-row context.

4.1 Predictive performance of the three models

4.1.1 Overall performance

Table 4.1 gives the overall results. All three models scored far above the accuracy of 33.3% expected from random guessing on three classes, and above the 45.0% obtained by always predicting the largest class (Low). This shows that the features carry real information about hair fall risk. TabPFN had the highest accuracy (78.57%), followed by CatBoost (78.51%) and TabFM (77.88%). TabPFN was highest on macro-recall, macro-F1 and ROC-AUC, and CatBoost was highest on macro-precision. The largest gap between any two models was 0.0072 on macro-F1 and 0.0052 on ROC-AUC. TabPFN achieved this without any tuning, whereas CatBoost needed a grid search, and TabFM came within 0.69 percentage points of TabPFN using under 3% of the training records.

Table 4.1: Performance of the three models on the test partition

| Model | Training context | Accuracy | Macro-precision | Macro-recall | Macro-F1 | ROC-AUC |
|---|---|---|---|---|---|---|
| CatBoost | 17,284 | 78.51% | 0.7915 | 0.7662 | 0.7763 | 0.9189 |
| TabPFN | 17,284 | 78.57% | 0.7875 | 0.7722 | 0.7787 | 0.9232 |
| TabFM | 500 | 77.88% | 0.7904 | 0.7608 | 0.7715 | 0.9180 |

4.1.2 Per-class performance and confusion matrices

Table 4.2 shows the F1-score for each risk tier. All three models classified the Low and High tiers better than the Moderate tier, and the pattern was the same for every model.

Table 4.2: F1-score by risk tier

| Model | Low | Moderate | High |
|---|---|---|---|
| CatBoost | 0.86 | 0.71 | 0.77 |
| TabPFN | 0.86 | 0.71 | 0.78 |
| TabFM | 0.85 | 0.71 | 0.76 |

[Insert Figure 4.1: CatBoost confusion matrix (Colab Work/Step_05_CatBoost/catboost_confusion_matrix.png)]
Figure 4.1: CatBoost confusion matrix

[Insert Figure 4.2: TabPFN confusion matrix (Colab Work/Step_06_TabPFN/tabpfn_confusion_matrix.png)]
Figure 4.2: TabPFN confusion matrix

[Insert Figure 4.3: TabFM confusion matrix (Colab Work/Step_07_TabFM/tabfm_confusion_matrix.png)]
Figure 4.3: TabFM confusion matrix

The confusion matrices (Figures 4.1 to 4.3) show that almost all errors fell between neighbouring tiers. Only 3 records for CatBoost, 1 for TabPFN and 3 for TabFM were confused between Low and High, out of 929, 926 and 956 misclassified records respectively. The High tier had the lowest recall in every model (0.70, 0.73 and 0.69), and 256, 230 and 269 of its 864 records were predicted as Moderate. The ordered nature of the target is a likely reason for the weaker Moderate results: the Moderate tier lies between the other two and shares a boundary with each of them, whereas Low and High each border only one tier. This study did not test that explanation with an ordinal model, so it is offered as an interpretation.

4.1.3 Statistical significance

McNemar's test with continuity correction was applied to each pair of models on the same 4,322 records (Table 4.3).

Table 4.3: Pairwise McNemar's test

| Comparison | Statistic | p-value | Significant at α = 0.05 |
|---|---|---|---|
| CatBoost vs TabPFN | 0.0147 | 0.9037 | No |
| CatBoost vs TabFM | 1.6528 | 0.1986 | No |
| TabPFN vs TabFM | 2.5798 | 0.1082 | No |

None of the three differences was significant, so no difference in accuracy was detected between a grid-searched gradient-boosted model, a zero-shot model with the full training data, and a zero-shot model with a 500-row context. A non-significant result does not prove that the models are equivalent. It only shows that the data give no evidence of a difference. The comparison with TabFM was also made at unequal context sizes, which is why Section 4.2 examines the models at matched sizes.

4.2 Effect of training context size

The three models were retrained with 100, 500 and 2,000 training rows (Section 3.8.4). Table 4.4 and Figure 4.4 give the results. The 100-row and 500-row runs used the full test partition, and the 2,000-row run used a fixed subset of 500 test records for all models. The 2,000-row column can therefore be compared across models but not with the other rows in absolute terms.

Table 4.4: Accuracy and macro-F1 with reduced training context

| Training rows | Test records | CatBoost acc. | TabPFN acc. | TabFM acc. | CatBoost F1 | TabPFN F1 | TabFM F1 |
|---|---|---|---|---|---|---|---|
| 100 | 4,322 | 60.53% | 71.54% | 74.41% | 0.5745 | 0.7062 | 0.7363 |
| 500 | 4,322 | 69.64% | 77.65% | 77.88% | 0.6768 | 0.7691 | 0.7715 |
| 2,000 | 500 | 74.40% | 76.20% | 77.40% | 0.7260 | 0.7508 | 0.7631 |
| Full (17,284) | 4,322 | 78.51% | 78.57% | not run | 0.7763 | 0.7787 | not run |

[Insert Figure 4.4: Accuracy against training context size for the three models (line chart of Table 4.4; the file matched_2000ctx_chart.png in Colab Work/Step_11 can be used or redrawn)]
Figure 4.4: Accuracy under reduced training context

At every reduced size, both foundation models scored higher than CatBoost. At 100 rows, which is under 0.6% of the training partition, CatBoost reached 60.53%, which was 11.01 points below TabPFN and 13.88 points below TabFM. The gaps were 8.01 and 8.24 points at 500 rows and 1.80 and 3.00 points at 2,000 rows, so they narrowed as the context grew, and at full context CatBoost matched TabPFN (78.51% and 78.57%).

The foundation models kept most of their full-data performance with small contexts. At 500 rows TabPFN was 0.92 points below its own full-context accuracy, whereas CatBoost was 8.87 points below its own. TabFM at 500 rows was 0.63 points below CatBoost's full-context accuracy while using 2.9% of the training records. From 100 to 500 rows CatBoost gained 9.11 points, TabPFN 6.11 and TabFM 3.47, so the tuned gradient-boosted model depended most on the amount of training data.

TabFM scored higher than TabPFN at all three reduced sizes, but the margin shrank from 2.87 points at 100 rows to 0.23 points at 500 rows. The 1.20-point margin at 2,000 rows was measured on only 500 records, where the 95% interval for an accuracy near 76% is about ±3.7 points, so the order of the two foundation models cannot be treated as reliable. McNemar's test was not run at the reduced sizes, so no significance claim is made for these comparisons. The full-context TabFM run did not finish (Section 4.4), which is why that cell is empty.

4.3 Explainability of the predictions (SHAP)

4.3.1 Global feature importance

Figures 4.5 to 4.7 rank the features by mean absolute SHAP value. The CatBoost plot covers the full test partition and adds the contributions of the three classes. The TabPFN and TabFM plots cover only the sampled records (30 and 20) and show the High risk class. The bar lengths are on different scales, so the models are compared by rank and not by magnitude.

[Insert Figure 4.5: CatBoost global importance (Colab Work/Step_08a_CatBoost_SHAP/catboost_shap_global_importance.png)]
Figure 4.5: CatBoost global feature importance (SHAP)

[Insert Figure 4.6: TabPFN global importance (Colab Work/Step_08b_TabPFN_SHAP/tabpfn_shap_global_importance.png)]
Figure 4.6: TabPFN global feature importance (SHAP)

[Insert Figure 4.7: TabFM global importance (Colab Work/Step_08c_TabFM_SHAP/tabfm_shap_global_importance.png)]
Figure 4.7: TabFM global feature importance (SHAP)

Table 4.5: Ten most important features in each model

| Rank | CatBoost | TabPFN | TabFM |
|---|---|---|---|
| 1 | iron | stress_level | stress_level |
| 2 | stress_level | iron | alt_liver |
| 3 | total_protein | alt_liver | total_protein |
| 4 | vitamin_d | total_protein | vitamin_d |
| 5 | alt_liver | vitamin_d | calcium |
| 6 | calcium | calcium | iron |
| 7 | manganese | manganese | manganese |
| 8 | body_water_content | chemical_use | body_water_content |
| 9 | family_hair_fall_history | family_hair_fall_history | chemical_use |
| 10 | stress | body_water_content | late_night_sleep |

The same seven continuous biomarkers (iron, stress_level, total_protein, vitamin_d, alt_liver, calcium and manganese) were the seven most important features in all three models, and manganese was seventh in each. The models differed mainly in the order within this group. For example, iron was first for CatBoost, second for TabPFN and sixth for TabFM. Because the foundation-model values came from only 20 to 30 records, differences in this order should not be interpreted. Only the shared set of leading features is reported as a finding. The composite scores total_keratine and hair_texture contributed almost nothing in all three models, and gender also contributed very little.

4.3.2 Direction of the effects

The beeswarm plots (Figures 4.8 to 4.10) show how feature values moved the predicted probability of the High risk class.

[Insert Figure 4.8: CatBoost beeswarm, High risk (Colab Work/Step_08a_CatBoost_SHAP/catboost_shap_beeswarm_high.png)]
Figure 4.8: CatBoost SHAP beeswarm plot (High risk)

[Insert Figure 4.9: TabPFN beeswarm, High risk (Colab Work/Step_08b_TabPFN_SHAP/tabpfn_shap_beeswarm_high.png)]
Figure 4.9: TabPFN SHAP beeswarm plot (High risk)

[Insert Figure 4.10: TabFM beeswarm, High risk (Colab Work/Step_08c_TabFM_SHAP/tabfm_shap_beeswarm_high.png)]
Figure 4.10: TabFM SHAP beeswarm plot (High risk)

In all three models, high values of stress_level and alt_liver pushed the prediction toward High risk, and high values of iron, total_protein, vitamin_d, calcium and manganese pushed it away. For CatBoost, higher body_water_content also lowered the High risk contribution, and higher age and every binary risk flag (stress, family_hair_fall_history, chemical_use, anemia, chronic_illness, late_night_sleep, sleep_disturbance and water_reason) raised it. The TabPFN and TabFM plots showed the same direction for the leading biomarkers.

4.3.3 Patient-level explanations

Waterfall plots show how the features moved one patient's predicted High risk score from the baseline value to the final value (Figures 4.11 to 4.13). The three plots show different patients, because the CatBoost plot uses the first test record and the two foundation-model plots each use the first record of a different random sample, so they should not be compared with each other.

[Insert Figure 4.11: CatBoost waterfall (Colab Work/Step_08a_CatBoost_SHAP/catboost_shap_waterfall_patient.png)]
Figure 4.11: CatBoost patient-level explanation

[Insert Figure 4.12: TabPFN waterfall (Colab Work/Step_08b_TabPFN_SHAP/tabpfn_shap_waterfall_patient.png)]
Figure 4.12: TabPFN patient-level explanation

[Insert Figure 4.13: TabFM waterfall (Colab Work/Step_08c_TabFM_SHAP/tabfm_shap_waterfall_patient.png)]
Figure 4.13: TabFM patient-level explanation

4.4 Computational cost and implementation limitations

4.4.1 TabFM runtime

TabFM (version 1.0.0, PyTorch backend) was much slower at prediction than CatBoost and TabPFN, and its running time rose steeply with the size of the training context (Table 4.6). With a 500-row context, predicting the 4,322 test records took approximately 8 minutes. With a 2,000-row context, predicting only 500 test records took approximately 15 minutes. That is about 1.8 seconds per record compared with about 0.11 seconds per record at 500 rows, so a context four times larger made each prediction roughly sixteen times slower. An attempt to use the full 17,284-row context, run in batches of 50 records with results saved after each batch, did not finish within the session limits of the cloud platform. TabFM was therefore evaluated with a 500-row context, the largest tested size that allowed a complete evaluation of the full test partition. A single ensemble member (n_estimators = 1) was used throughout, because the default ensemble setting multiplied the cost of every prediction.

Table 4.6: Approximate TabFM prediction time by context size

| Training context | Test records | Approximate time | Approximate time per record |
|---|---|---|---|
| 500 rows | 4,322 | 8 minutes | 0.11 s |
| 2,000 rows | 500 | 15 minutes | 1.8 s |
| 17,284 rows | 4,322 | Did not finish | – |

4.4.2 Software problems and workarounds

Three problems arose while running the models.

1. PermutationExplainer failed. This SHAP method, which had been planned for TabPFN and TabFM, failed with a type-resolution error in numba, the library that shap uses to speed up its masking step. The failure was reproduced on both Google Colaboratory and Kaggle Notebooks. It continued after numba's JIT compilation was disabled with the NUMBA_DISABLE_JIT setting and after numba and llvmlite were reinstalled. KernelExplainer was used instead. It estimates the same Shapley values by querying the model directly, but it is slower, which is why the foundation-model explanations were limited to 30 and 20 test records and a reduced training context.
2. TabFM failed on single-row input. The predict_proba method failed when called with one row, which KernelExplainer does routinely. A single-row query was therefore duplicated into a two-row batch, and only the first output row was kept. This does not change the prediction for the original record. It may be an upstream defect, but this was not checked against the reported defects in [10].
3. TabPFN checkpoint loading failed. Recent PyTorch versions load checkpoints with weights_only set to True by default, which rejected the TabPFN weights. torch.load was wrapped so that weights_only was False before the model was created. TabPFN's licence token was read from the Kaggle secrets store and not written into the notebook.

These problems came from the recency of the software and not from the modelling approaches. TabFM's runtime growth and its single-row failure were not visible from its documentation and were found by testing, which required changing one variable at a time (context size, batch size and backend) to separate design limits from defects.

4.5 Discussion

4.5.1 Plausibility of the findings

The three models reached close accuracy (77.88% to 78.57%) on a task with three imbalanced tiers, and most errors fell between neighbouring tiers, which is what would be expected when risk changes gradually with the input values. The main features found by SHAP (iron, stress level, total protein, vitamin D, liver enzyme ALT, calcium and manganese) and the direction of their effects agree with the relationships used to construct the dataset (Section 3.7). The result should therefore be read as showing that all three models recovered the relationships built into the data. It is not new clinical evidence, because the data were not collected from a clinical registry. For the same reason, the accuracy values show how well the models perform on this dataset and cannot be taken as the accuracy of a diagnostic tool.

The very small contribution of total_keratine and hair_texture is also plausible in this setting. They are composite scores of hair condition and not laboratory measurements, and in all three models the information they carry appears to be covered by the other features.

4.5.2 Comparison with similar studies

A direct comparison of accuracy values with earlier hair loss studies is not possible, because the studies used different data, targets and metrics. The comparison below is therefore about findings and not about numbers.

- Sai et al. [3] found that an ensemble outperformed individual classifiers, and Patel et al. [4] found that Random Forest outperformed XGBoost, CatBoost and LightGBM. Both concern classical models on different datasets. The present study did not include these methods, but it adds that a tuned CatBoost and two zero-shot foundation models were not significantly different in accuracy on this dataset (Table 4.3). This agrees with the view in Section 2.5 that the best model depends on the dataset.
- TabFM has been reported to outperform heavily tuned gradient-boosted models on the TabArena benchmark in a zero-shot setting [9]. In the present study TabFM was not significantly different from CatBoost (with a much smaller context), and with the same small contexts both foundation models scored higher than CatBoost (Table 4.4). This is consistent with a data-efficiency advantage, but at the full training size no advantage over CatBoost was detected, so the findings support the benchmark report only partly. The independent evaluation [10] found TabFM competitive with XGBoost, Random Forest and TabPFN, and the present result for TabFM against TabPFN and CatBoost points in the same direction.
- The stronger results of TabPFN with small contexts agree with its design for small tabular problems [8].
- Chen et al. [5] observed that neural models gained accuracy but lost interpretability. Here SHAP explanations could be produced for CatBoost and for both transformer-based models, although with more limited samples for the latter, so interpretability did not have to be given up.
- Widowati et al. [1] stressed that transformations must be kept inside cross-validation folds. In the present study the only preprocessing was the removal of identifiers and a fixed coding of gender, so no fitted transformation could leak information, and CatBoost's tuning was done by cross-validation within the training partition.

4.5.3 Implications and cautions

The results suggest that, on this dataset, zero-shot foundation models can be used without a tuning stage and still reach a performance comparable to a tuned CatBoost, and that they are more useful when little training data is available. Against this, TabFM was slow and could not be run with the full context, and the explanations for the foundation models rest on small samples. The main limitations (a constructed dataset, one data split, the unequal contexts and test sets, the small SHAP samples, and the use of the test partition for CatBoost's early stopping) are discussed in Chapter 5.
