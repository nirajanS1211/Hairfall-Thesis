ACKNOWLEDGEMENTS (Syllabus 1.1.1)

I would like to express my sincere gratitude to my supervisor, Asst. Prof. Jagadish Bhatta, of the Central Department of Computer Science and Information Technology, Tribhuvan University, for his guidance, suggestions and encouragement throughout this research.

I am thankful to the Head of the Central Department of Computer Science and Information Technology, [name], and to all the teachers and staff of the department for their support during my studies. I also thank the creators of the public datasets used in this study for making their data available, and the providers of the open-source software used in the experiments.

I am grateful to my classmates and friends for their discussions and help, and to my family for their patience, support and encouragement.

[Add or remove names to suit. The syllabus suggests acknowledging the supervisor first, then funding agencies (if any), teachers, classmates and staff, survey respondents (not applicable here, since no survey was conducted), and family.]

Nirajan Shahi
[Month Year]

---

ABBREVIATIONS/ACRONYMS (Syllabus 1.1.2, alphabetical)

| Abbreviation | Full form |
|---|---|
| ALT | Alanine Aminotransferase |
| CSIT | Computer Science and Information Technology |
| CUDA | Compute Unified Device Architecture |
| CV | Cross-Validation |
| EHR | Electronic Health Record |
| GPU | Graphics Processing Unit |
| JIT | Just-In-Time (compilation) |
| KNN | k-Nearest Neighbour |
| M.Sc. | Master of Science |
| NeurIPS | Conference on Neural Information Processing Systems |
| ROC-AUC | Receiver Operating Characteristic – Area Under the Curve |
| SHAP | Shapley Additive Explanations |
| SVM | Support Vector Machine |
| TabFM | Tabular Foundation Model |
| TabPFN | Tabular Prior-Fitted Network |
| TU | Tribhuvan University |

---

UNITS AND CONVERSIONS (Syllabus 1.1.3, alphabetical)

| Unit | Meaning | Used for |
|---|---|---|
| % | Percent | Body water content; accuracy |
| g/dL | Grams per decilitre | Serum total protein |
| GB | Gigabyte | Computer memory |
| min | Minute | Running time |
| mg/dL | Milligrams per decilitre | Serum calcium |
| ng/mL | Nanograms per millilitre | Serum vitamin D |
| s | Second | Running time |
| U/L | Units per litre | Serum alanine aminotransferase |
| µg/dL | Micrograms per decilitre | Serum iron |
| µg/L | Micrograms per litre | Whole-blood manganese |

---

ABSTRACT (Syllabus 1.1.4)
(Heading in capital letters, bold and centred, with no punctuation. Four blank spaces before the first paragraph. 346 words.)

**ABSTRACT**

Hair loss is influenced by many factors acting together, and no single measurement predicts it reliably. Earlier prediction studies used classical classifiers, reached conflicting conclusions about the best model, and did not test newer tabular foundation models. This study benchmarked a tuned gradient-boosted model, CatBoost, against two zero-shot tabular foundation models, TabPFN and TabFM, for classifying hair fall risk into three tiers (Low, Moderate and High) from structured clinical and lifestyle data, and explained the predictions of all three models with SHAP.

The dataset had 21,606 records with 20 predictors, assembled from two public datasets and adjusted using domain-informed relationships. A stratified 80/20 split gave 17,284 training records and 4,322 test records. CatBoost was tuned by grid search with five-fold cross-validation. TabPFN received the full training set as context without tuning, and TabFM received a 500-row context because its running time rose steeply with context size. The models were compared using accuracy, macro-averaged precision, recall and F1-score, ROC-AUC and McNemar's test, and were also retrained with 100, 500 and 2,000 training rows.

Accuracy was 78.51% for CatBoost, 78.57% for TabPFN and 77.88% for TabFM, and no pair of models differed significantly. With small training contexts both foundation models scored clearly higher than CatBoost: at 100 rows the accuracy was 60.53% for CatBoost, 71.54% for TabPFN and 74.41% for TabFM. All three models classified the Moderate tier least well. SHAP showed that iron, stress level, total protein, vitamin D, liver enzyme ALT, calcium and manganese were the most influential features in every model, with the same direction of effect. These relationships were built into the dataset, so they are not new clinical findings. TabFM was slow, and its full-context run could not be completed.

On this dataset, zero-shot foundation models matched a tuned gradient-boosted model in accuracy, depended much less on the amount of training data, and could be explained with SHAP. The results come from a constructed dataset and one data split, so they do not validate a clinical tool. Testing on real clinical data, a full-context evaluation of TabFM and repeated data splits are recommended.

Keywords: hair fall risk, tabular foundation models, CatBoost, TabPFN, TabFM, SHAP, explainable machine learning

---

TABLE OF CONTENTS
(Page numbers to be filled in after the thesis is paginated, or generated with the word processor's automatic table of contents. Dedication is not listed.)

| Title | Page |
|---|---|
| Declaration | ii |
| Recommendation | |
| Certificate | |
| Acknowledgements | |
| Abbreviations/Acronyms | |
| Units and Conversions | |
| Abstract | |
| Table of Contents | |
| List of Tables | |
| List of Figures | |
| List of Appendices | |
| CHAPTER 1: INTRODUCTION | 1 |
| 1.1 Background | |
| 1.2 Statement of the problem | |
| 1.3 Research questions | |
| 1.4 Research objectives | |
| 1.5 Significance/Rationale of the study | |
| CHAPTER 2: LITERATURE REVIEW | |
| 2.1 Machine learning for hair loss prediction | |
| 2.2 Gradient-boosted decision trees and CatBoost | |
| 2.3 Tabular foundation models | |
| 2.4 Explainability with SHAP | |
| 2.5 Research gap | |
| CHAPTER 3: METHODOLOGY | |
| 3.1 Research design | |
| 3.2 Research approach | |
| 3.3 Study area | |
| 3.4 Study population | |
| 3.5 Sample selection | |
| 3.6 Sample size | |
| 3.7 Methods of data collection | |
| 3.8 Data analysis approach and tools | |
| 3.8.1 Data preprocessing | |
| 3.8.2 Models and justification | |
| 3.8.3 Experimental setup | |
| 3.8.4 Training context experiment | |
| 3.8.5 Explainability analysis | |
| 3.8.6 Evaluation metrics and statistical testing | |
| 3.8.7 Computational assessment | |
| 3.8.8 Tools and environment | |
| CHAPTER 4: RESULTS AND DISCUSSION | |
| 4.1 Predictive performance of the three models | |
| 4.2 Effect of training context size | |
| 4.3 Explainability of the predictions (SHAP) | |
| 4.4 Computational cost and implementation limitations | |
| 4.5 Discussion | |
| CHAPTER 5: CONCLUSION AND RECOMMENDATIONS | |
| 5.1 Conclusion | |
| 5.2 Limitations of the study | |
| 5.3 Recommendations | |
| REFERENCES | |
| APPENDICES | |

---

LIST OF TABLES

| Table | Title | Page |
|---|---|---|
| Table 2.1 | Summary of related studies on hair loss prediction | |
| Table 3.1 | Link between the research objectives and the methods used | |
| Table 3.2 | Predictor variables | |
| Table 3.3 | Experimental environment | |
| Table 4.1 | Performance of the three models on the test partition | |
| Table 4.2 | F1-score by risk tier | |
| Table 4.3 | Pairwise McNemar's test | |
| Table 4.4 | Accuracy and macro-F1 with reduced training context | |
| Table 4.5 | Ten most important features in each model | |
| Table 4.6 | Approximate TabFM prediction time by context size | |

---

LIST OF FIGURES

| Figure | Title | Page |
|---|---|---|
| Fig. 3.1 | Block diagram of the research methodology | |
| Fig. 4.1 | CatBoost confusion matrix | |
| Fig. 4.2 | TabPFN confusion matrix | |
| Fig. 4.3 | TabFM confusion matrix | |
| Fig. 4.4 | Accuracy under reduced training context | |
| Fig. 4.5 | CatBoost global feature importance (SHAP) | |
| Fig. 4.6 | TabPFN global feature importance (SHAP) | |
| Fig. 4.7 | TabFM global feature importance (SHAP) | |
| Fig. 4.8 | CatBoost SHAP beeswarm plot (High risk) | |
| Fig. 4.9 | TabPFN SHAP beeswarm plot (High risk) | |
| Fig. 4.10 | TabFM SHAP beeswarm plot (High risk) | |
| Fig. 4.11 | CatBoost patient-level explanation | |
| Fig. 4.12 | TabPFN patient-level explanation | |
| Fig. 4.13 | TabFM patient-level explanation | |

---

LIST OF PLATES/PICTURES

Not applicable. The thesis contains no plates or photographs. (Omit this page.)

---

LIST OF APPENDICES

| Appendix | Title | Page |
|---|---|---|
| Appendix A | Source Code | |
| Appendix B | Additional Figures | |
| Appendix C | Result Tables from the Experiments | |
| Appendix D | Dataset Description and Sample Records | |
