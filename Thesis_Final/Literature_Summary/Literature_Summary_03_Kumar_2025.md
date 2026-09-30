# Literature Summary 3: Kumar et al. (2025)

**Citation:** Kumar, M. S., Reddy, P. L. K., Reddy, G. D., Kumar, A. S., & Nagendra, P. (2025). Predictive modeling of hair fall using random forest algorithms. *Proceedings of ICITSM-Part II 2025*. https://doi.org/10.4108/eai.28-4-2025.2358120

**Verified:** Yes (PDF read). NOTE: the old proposal cited this as "Patel, Gupta & Mehta (2025)" in "EAI Endorsed Transactions on Pervasive Health and Technology" with a different title. Those authors and that title could not be found; the paper above is the real one.
**Data:** 2,000 records, 10 features (demographics, lifestyle, genetic predisposition).
**Models:** Random Forest (GridSearchCV), Logistic Regression, SVM, KNN, Gradient Boosting, XGBoost, CatBoost, LightGBM; Django web interface.
**Result:** Random Forest 100%, XGBoost 67.5%, CatBoost 49.5%, LightGBM 47.5%.
**Limitation / gap:** 100% accuracy is suspicious; boosting models look untuned; no explainability.
**Use in thesis:** The only study that includes CatBoost on hair loss, which shows the gap (CatBoost never tuned).
