# -*- coding: utf-8 -*-
TITLE = "Anthropometric data leakage inflates machine learning performance in child stunting prediction"
SHORT_TITLE = "Anthropometric data leakage inflates machine learning performance … (Ahmad Dedi Jubaedi)"
AUTHORS = [("Ahmad Dedi Jubaedi", "1"), ("Pulung Nurtantio Andono", "2"), ("Nova Rijati", "2"), ("Ahmad Zainul Fanani", "2")]
AFFIL = [("1", "Faculty of Computer Science, Universitas Serang Raya, Banten, Indonesia"),
         ("2", "Faculty of Computer Science, Universitas Dian Nuswantoro, Semarang, Indonesia")]
KEYWORDS = ["Data leakage", "Indonesian Health Survey", "Machine learning", "Model evaluation", "Reproducibility", "Stunting", "Target leakage"]
ABSTRACT = ("Many machine learning studies report near-perfect accuracy for predicting child stunting, yet stunting is defined "
 "from height, age, and sex, and these same anthropometric variables are frequently used as predictors. This study "
 "quantifies how much such target leakage inflates reported performance. Using 84,205 children aged 0–59 months from the "
 "2023 Indonesian Health Survey, we trained logistic regression, random forest, and gradient boosting models on four "
 "feature sets: upstream determinants only, determinants plus current weight, determinants plus all current anthropometry, "
 "and height, age, and sex alone. Models were evaluated on a household-grouped hold-out set with bootstrap confidence "
 "intervals and grouped cross-validation. With determinants only, the area under the ROC curve (AUC) ranged from 0.654 to "
 "0.670. Adding anthropometry raised gradient boosting AUC to 0.998 and accuracy to 97.8%, an absolute AUC gain of 0.328 "
 "(95% CI 0.320–0.337); height, age, and sex alone reproduced this performance. Permutation importance attributed almost "
 "all predictive signal to height and age. Near-perfect stunting classifiers therefore reconstruct the label rather than "
 "predict risk. Determinant-only models provide a realistic baseline for future studies.")

# Body: list of blocks. ('h1', text) numbered heading; ('h2', text) subsection; ('p', text) paragraph;
# ('fig', file, width_cm, caption); ('tbl', key); ('eq', key); ('note', text) yellow author note.
# Citations use {key} or {key1,key2} -> [n] IEEE numbering by first appearance.
BODY = [
('h1', "INTRODUCTION"),
('p', "Stunting, defined as a length- or height-for-age z-score (HAZ) below −2 standard deviations of the World Health "
 "Organization (WHO) Child Growth Standards, remains the most prevalent form of child undernutrition in low- and middle-income "
 "countries and is associated with impaired cognitive development and lower adult productivity {victora}. In Indonesia, stunting "
 "is shaped by factors operating at the child, household, and community levels, including maternal education, birth weight, "
 "sanitation, and region of residence {mulya}. Because these determinants interact in complex, non-linear ways, machine learning "
 "(ML) has been increasingly promoted as a tool to identify children at risk and to rank modifiable risk factors {rahman,mansur,bitew,fenta}."),
('p', "A rapidly growing body of work applies random forests, gradient boosting, support vector machines, and neural networks to "
 "Demographic and Health Surveys and national nutrition surveys {chily,usman,shen,ndag,islam}. Several recent studies report "
 "accuracies above 90% and AUC values close to 1. In Ghana, stunting accuracy ranged from 86% to 98% with child weight, "
 "length/height, and age among the most important predictors {anku}. In Ethiopia, a random forest reached 97.99% accuracy and an "
 "AUC of 0.99995, with child height and weight ranked immediately after age {ayele}; another study identified height as the most "
 "influential feature {wudu}. In Egypt, accuracies above 90% and AUC above 0.96 were reported with height and weight as inputs {hendy,hendyw}."),
('p', "These results share a methodological problem. HAZ is a deterministic function of measured length or height, age, and sex. "
 "When current height is supplied as a predictor together with age and sex, the classifier does not need to learn any risk "
 "mechanism: it only has to re-learn the WHO reference curve. This is a textbook case of target (feature-to-target) leakage, in "
 "which information that encodes the outcome is available during training but would not be available, or would make prediction "
 "unnecessary, at deployment {sasse,bernett}. Leakage has been identified as a leading cause of the reproducibility crisis in "
 "ML-based science across many fields {kapoor,messeri}, has been shown to drastically inflate performance in neuroimaging "
 "{rosen}, and has already contaminated meta-analytic estimates of predictive accuracy {mortel}. Current reporting guidance, "
 "including TRIPOD+AI and REFORMS, explicitly asks authors to justify that predictors are available at the time of prediction "
 "and are not proxies of the outcome {tripod,reforms}."),
('p', "Although the logic of anthropometric leakage is simple, its magnitude has not been quantified on a large, nationally "
 "representative dataset under a controlled design, and there is no leakage-free performance baseline for stunting "
 "prediction in Indonesia. A second, subtler issue is that survey data are clustered: siblings share households, and a random "
 "row-level split lets information about the same household appear in both training and test sets {joeres,apicella}."),
('p', "This study addresses these gaps with three contributions. First, it provides a controlled experiment on 84,205 children from "
 "the 2023 Indonesian Health Survey (Survei Kesehatan Indonesia, SKI 2023) that isolates the effect of anthropometric leakage "
 "by holding the models, data split, and pre-processing constant and varying only the feature set. Second, it reports a "
 "leakage-free baseline built solely from upstream determinants and evaluated on unseen households. Third, it identifies "
 "less obvious outcome-derived variables in the survey that should be excluded, and it translates the findings into practical "
 "recommendations for reviewers and authors."),

('h1', "METHOD"),
('p', "The research design is a controlled comparative experiment summarized in Figure 1. All steps were implemented in "
 "Python (scikit-learn 1.8) as a single script with a fixed random seed (42), and every number reported in this paper is "
 "produced by that script. The four feature scenarios were trained and evaluated under identical splits, models, and "
 "pre-processing so that differences in performance can be attributed to the feature set alone."),
('fig', "fig_method_flow.png", 14.5, "Figure 1. Research design of the leakage experiment"),
('h2', "2.1. Data source and outcome definition"),
('p', "We used the child (0–59 months) module of SKI 2023, a nationally representative household survey conducted by the "
 "Indonesian Ministry of Health, which contains 86,364 child records and 171 variables covering the child, the mother, and the "
 "household. Age in days was computed from the dates of birth and interview. Recumbent length and standing height were "
 "harmonized following the WHO convention (+0.7 cm for children under 731 days measured standing and −0.7 cm for children aged "
 "731 days or more measured recumbent). HAZ was computed from the WHO Child Growth Standards with the LMS method in (1):"),
('eq', "haz"),
('p', "where y is the harmonized length or height and L(t), M(t), and S(t) are the sex- and age-specific Box-Cox power, median, and "
 "coefficient of variation of the WHO reference at age t in days; for length/height-for-age L(t) = 1. Children with missing "
 "height or measurement position, with ages beyond the 1,826 days covered by the WHO reference table, or with biologically implausible "
 "values (|HAZ| > 6), were excluded, leaving 84,205 children. Stunting was coded as 1 when HAZ < −2 and 0 otherwise, giving "
 "19,825 stunted children (unweighted prevalence 23.5%; prevalence weighted by the survey individual weights 22.0%)."),
('h2', "2.2. Feature scenarios"),
('p', "Table 1 defines the four feature sets. Scenario B contains 119 upstream determinants grouped into child characteristics "
 "(age, sex, relationship to household head), maternal factors (education, occupation, age at first pregnancy, smoking and "
 "hygiene behavior, awareness of stunting), perinatal and health-service factors (antenatal care, place and mode of delivery, "
 "gestational age, birth weight and birth length recorded in the maternal and child health book, neonatal services, "
 "immunization, congenital anomalies), infant feeding (current breastfeeding and 24-hour food and liquid recall), water, "
 "sanitation and hygiene, housing materials and floor area, household size, health insurance, access to primary care, "
 "province, and urban–rural residence. Birth weight and birth length are measured at birth, before the outcome, and are "
 "legitimate predictors. Scenario A1 adds current weight, which does not enter the HAZ formula but is strongly correlated "
 "with height (indirect or proxy leakage). Scenario A2 adds all current anthropometry—weight, length/height, mid-upper arm "
 "circumference (MUAC), and waist circumference—and mimics the feature sets used in the studies discussed above. Scenario L0 "
 "uses only height, age, and sex, i.e., exactly the inputs of the HAZ formula, and serves as an upper bound of pure leakage."),
('tbl', "features"),
('p', "Beyond the obvious anthropometric variables, three groups of survey items were excluded from all scenarios because they are "
 "consequences or artifacts of the outcome rather than determinants: i) the reasons for receiving supplementary feeding "
 "(\"severe undernutrition\", \"undernutrition\", \"thin\", \"weight did not increase twice\"), which are recorded because a child "
 "has already been identified as malnourished; ii) the mother's specific beliefs about what stunting means, which may be "
 "influenced by having a stunted child; and iii) measurement-process fields such as the measurement position. Identifiers, "
 "sampling weights, dates, district codes with more than 500 levels, and items with more than 95% missing values were also "
 "excluded. The full exclusion list with reasons is released with the code."),
('h2', "2.3. Data splitting and pre-processing"),
('p', "Children living in the same household share environment, diet, and genetics, and 20.6% of the analyzed children have at "
 "least one other under-five child from the same household in the dataset (75,346 households in total). To prevent household-level leakage, the data were split with stratified group k-fold "
 "partitioning (five folds, household identifier as group) and the first fold was held out as the test set: 67,364 children "
 "(60,286 households) for training and 16,841 children (15,060 households) for testing, with identical stunting prevalence "
 "(23.5%) in both sets and no household in common. Sentinel codes (e.g., 8888 for unknown birth weight) were converted to "
 "missing values. All pre-processing—median imputation with missing-value indicators, standardization, and one-hot encoding "
 "for logistic regression and random forest, and ordinal encoding with native categorical handling for gradient boosting—was "
 "embedded in scikit-learn pipelines and fitted on training data only, so that no statistic of the test set influenced training {sasse}."),
('h2', "2.4. Models"),
('p', "Three algorithms that dominate the stunting-prediction literature were trained on every scenario: L2-regularized logistic "
 "regression (LR); random forest (RF) with 200 trees, square-root feature sampling, minimum leaf size 5, and 50% bootstrap "
 "samples; and histogram-based gradient boosting (HGB) with up to 300 iterations, learning rate 0.08, 31 leaves, and early "
 "stopping on a 10% internal validation split. HGB is the scikit-learn implementation of the same second-order gradient-boosted "
 "tree family as XGBoost and was used because it natively handles missing values and categorical variables. Class imbalance "
 "was handled with balanced class weights rather than synthetic oversampling, because oversampling before splitting is itself a "
 "source of leakage {bernett}. Hyperparameters were fixed a priori and not tuned on the test set."),
('h2', "2.5. Evaluation"),
('p', "Performance on the held-out households was measured with the AUC, the area under the precision–recall curve (PR-AUC), "
 "accuracy, balanced accuracy, precision, recall (sensitivity), specificity, F1 score, Matthews correlation coefficient (MCC), "
 "and Brier score, using a 0.5 probability threshold. A majority-class model that always predicts \"not stunted\" was used as "
 "a naive reference. Ninety-five percent confidence intervals (CIs) for the AUC were obtained from 1,000 bootstrap resamples of "
 "the test set. The effect of leakage was measured with the paired difference ΔAUC = AUC(leaky) − AUC(B) on the same bootstrap "
 "resamples, together with the relative inflation of discrimination above chance in (2):"),
('eq', "infl"),
('p', "To confirm that the results do not depend on one split, HGB was also evaluated with household-grouped five-fold "
 "cross-validation. Finally, permutation importance (decrease in AUC when a variable is randomly shuffled, three repeats, "
 "8,000 test children) was computed for HGB in scenarios A2 and B to show which variables drive each model {rosen,tripod}."),

('h1', "RESULTS AND DISCUSSION"),
('h2', "3.1. Leakage-free baseline performance"),
('p', "Table 2 reports the hold-out performance of all 12 model–scenario combinations. Using only upstream determinants "
 "(scenario B), discrimination was modest and remarkably similar across algorithms: AUC 0.656 (95% CI 0.647–0.665) for LR, "
 "0.654 (0.644–0.663) for RF, and 0.670 (0.661–0.679) for HGB. The best leakage-free model, HGB, detected 61.3% of stunted "
 "children at a specificity of 63.4%, with an F1 score of 0.438 and MCC of 0.212. Household-grouped cross-validation gave "
 "the same picture (AUC 0.671 ± 0.005 across folds; Table 3), indicating that the estimate is stable."),
('p', "These values are far below those reported in much of the literature, but they are what can honestly be expected from "
 "cross-sectional survey determinants of a chronic, multifactorial condition. They are also informative about metric choice. "
 "The RF in scenario B reached 74.4% accuracy, which appears acceptable until it is compared with the 76.5% accuracy of the "
 "majority-class model that never predicts stunting; its recall was only 21.3%. With a prevalence of 23.5%, accuracy rewards "
 "models that ignore the minority class, which is why threshold-independent metrics such as AUC and PR-AUC, together with "
 "recall and MCC, should be the primary reporting metrics {tripod,vancalster}."),
('tbl', "perf"),
('h2', "3.2. Magnitude of anthropometric leakage"),
('p', "Adding anthropometric variables transformed the same models into near-perfect classifiers (Figure 2). With current "
 "weight only (A1), AUC increased by 0.155 for HGB (95% CI 0.146–0.164), 0.147 for LR, and 0.105 for RF, even though "
 "weight is not part of the HAZ formula; weight carries information about height through body size. With all anthropometry "
 "(A2), HGB reached an AUC of 0.9983 (0.9980–0.9986), accuracy of 97.8%, recall of 98.0%, specificity of 97.7%, F1 of 0.954, "
 "and MCC of 0.940—figures that closely resemble the 94%–98% accuracies and AUC near 1 reported in previous studies "
 "{anku,ayele,wudu}. The paired AUC gain of A2 over B was 0.328 (0.320–0.337) for HGB, 0.295 for LR, and 0.209 for RF; in no "
 "bootstrap resample was the gain zero or negative (p < 0.001). Expressed with (2), leakage inflated discrimination above "
 "chance by 193% for HGB (Table 3)."),
('fig', "main_result_roc.png", 16.0, "Figure 2. ROC curves on the household-grouped test set for (a) logistic regression, (b) random forest, and (c) gradient boosting under the four feature scenarios"),
('p', "Scenario L0 demonstrates that this performance requires no determinant at all. With only height, age, and sex, RF achieved "
 "an AUC of 0.9989 and accuracy of 98.4%, and HGB an AUC of 0.9986—statistically indistinguishable from the full leaky model. "
 "The model has simply learned the WHO reference curve. Two model-specific results deserve comment. "
 "LR in L0 (AUC 0.910) is lower than tree ensembles because the relation between height and the stunting boundary is "
 "non-linear in age; LR can only approximate it, which is why its A2 performance (0.951) is also below that of HGB. RF in "
 "A2 (0.862) performs worse than RF in L0, most likely because square-root feature sampling rarely offers height among 123 candidate "
 "variables at each split. Both observations show that the reported performance of a leaky model depends on how "
 "efficiently the algorithm can reconstruct the label, not on its ability to capture risk."),
('fig', "auc_by_model_scenario.png", 13.0, "Figure 3. AUC with 95% bootstrap confidence intervals for each algorithm and feature scenario; the dashed line marks chance level"),
('tbl', "delta"),
('h2', "3.3. What the models learn"),
('p', "Permutation importance (Figure 4) explains why. In the leaky HGB model, shuffling height reduced the AUC by 0.473 and "
 "shuffling age by 0.361, followed at a distance by sex (0.016); every determinant, including maternal education, sanitation, "
 "and feeding practices, had an importance below 0.001. In other words, once height is available the model discards all "
 "information about risk factors, and any \"key determinants\" extracted from such a model are an artifact of ranking noise. "
 "This is consistent with reports in which child height, weight, and age head the feature-importance lists {anku,ayele,wudu}, "
 "and it implies that the determinant rankings published alongside leaky models should not be used to guide policy."),
('fig', "fig_permutation_importance_en.png", 15.5, "Figure 4. Top ten permutation importances of gradient boosting in (a) the leaky scenario A2 and (b) the leakage-free scenario B"),
('p', "In the leakage-free model the importance is spread across plausible determinants: child age (0.041), province (0.031), "
 "birth weight (0.024), birth length (0.012), sex (0.004), type of health insurance, maternal education, household waste "
 "handling, household size, and maternal age at first pregnancy. The prominence of age reflects the well-known "
 "deepening of growth faltering during the first two years; province, insurance, and household variables capture geographic and "
 "socioeconomic gradients; and birth weight and length capture intrauterine growth restriction. These findings agree with "
 "multilevel analyses of Indonesian children {mulya} and with the global evidence on the determinants of stunting {victora}, "
 "which supports the face validity of scenario B."),
('h2', "3.4. Implications for research practice"),
('p', "Table 4 contrasts the performance reported by recent studies that included current anthropometry with the leakage-free "
 "baseline obtained here. The pattern is consistent: when height (and often weight) is among the inputs, reported accuracy "
 "exceeds 86% and AUC approaches 1; when only determinants are used, AUC is around 0.65–0.67. Some studies also applied "
 "synthetic oversampling before splitting {ayele}, which adds a second source of optimism {sasse,bernett}. We do not claim that "
 "these studies are without value—several of them also report determinant analyses—but their headline accuracy figures "
 "measure the ability to recompute HAZ, not to predict stunting."),
('tbl', "lit"),
('p', "Four practical recommendations follow. First, any variable used to compute the outcome (length/height, age in the formula "
 "sense, sex) or strongly determined by it (current weight, MUAC, weight-for-height indicators) must be excluded when the task "
 "is to predict stunting risk; if anthropometry is used for screening, the task should be framed as measurement-based "
 "classification and not as risk prediction. Second, outcome-derived survey items, such as reasons for supplementary feeding, "
 "must be audited and removed. Third, data must be split by household or cluster, and every pre-processing step, including "
 "imputation and oversampling, must be fitted inside the training folds {joeres,apicella}. Fourth, results should be reported "
 "against a naive baseline and with AUC, PR-AUC, recall, and MCC, following TRIPOD+AI and REFORMS {tripod,reforms}. "
 "Reviewers can use a simple red flag: an AUC above 0.95 for stunting from survey data should trigger a check of the feature list."),
('p', "This study has limitations. The data are cross-sectional, so the determinant model identifies associations, not causes. "
 "Some determinants were recorded only for the youngest child or for children under 24 months, and missingness was handled "
 "by imputation with indicators rather than by multiple imputation. Survey weights were used for prevalence estimation but "
 "not for model training. The baseline was obtained with three widely used algorithms under fixed hyperparameters; tuning or "
 "richer feature engineering may raise the determinant-only AUC somewhat, but cannot legitimately approach the values produced "
 "by leakage. Finally, the models were validated internally on unseen households; external validation on another survey round "
 "is needed before any deployment {vancalster}."),

('h1', "CONCLUSION"),
('p', "This study set out to quantify how much the use of anthropometric indicators as predictors inflates the reported "
 "performance of machine learning models for child stunting. On 84,205 children from SKI 2023, determinant-only models "
 "achieved an AUC of 0.654–0.670, whereas adding current anthropometry raised gradient boosting to an AUC of 0.998 and an "
 "accuracy of 97.8%, a gain of 0.328 AUC points; height, age, and sex alone produced the same result. Permutation importance "
 "showed that leaky models rely almost exclusively on height and age. Near-perfect stunting classifiers therefore reconstruct "
 "the WHO label rather than predict risk, and their feature rankings should not guide policy. The leakage-free baseline reported "
 "here offers a realistic reference for future work. Further research should validate the determinant model on external survey "
 "rounds, incorporate longitudinal and community-level data to improve discrimination, and extend the leakage audit to wasting "
 "and underweight, which are defined from weight and height in the same way."),
]

TABLES = {
"features": ("Table 1. Feature scenarios compared in the experiment",
  [3.0, 5.6, 1.6, 4.3],
  [["Scenario", "Predictors", "Raw variables", "Role"],
   ["B", "Upstream determinants: child, maternal, perinatal, feeding, WASH, housing, access, region", "119", "Leakage-free baseline"],
   ["A1", "B + current weight", "120", "Proxy (indirect) leakage"],
   ["A2", "B + current weight, length/height, MUAC, waist circumference", "123", "Mimics prior studies"],
   ["L0", "Current length/height + age + sex", "3", "Pure target leakage (upper bound)"]]),
"perf": ("Table 2. Hold-out performance on 16,841 children from 15,060 unseen households (threshold 0.5)",
  [1.5, 2.1, 3.0, 1.35, 1.35, 1.35, 1.35, 1.35, 1.35],
  [["Scenario", "Model", "AUC (95% CI)", "PR-AUC", "Accuracy", "Recall", "Specificity", "F1", "MCC"],
   ["Baseline", "Majority class", "0.500", "0.229", "0.771", "0.000", "1.000", "0.000", "0.000"],
   ["B", "LR", "0.661 (0.651–0.671)", "0.352", "0.615", "0.616", "0.614", "0.423", "0.195"],
   ["B", "RF", "0.662 (0.652–0.672)", "0.367", "0.753", "0.216", "0.912", "0.286", "0.168"],
   ["B", "HGB", "0.676 (0.666–0.687)", "0.378", "0.633", "0.612", "0.639", "0.433", "0.214"],
   ["A1", "LR", "0.799 (0.791–0.807)", "0.555", "0.722", "0.746", "0.715", "0.551", "0.397"],
   ["A1", "RF", "0.759 (0.751–0.768)", "0.485", "0.779", "0.379", "0.898", "0.440", "0.313"],
   ["A1", "HGB", "0.822 (0.814–0.830)", "0.608", "0.767", "0.711", "0.783", "0.583", "0.442"],
   ["A2", "LR", "0.950 (0.947–0.953)", "0.804", "0.883", "0.907", "0.876", "0.781", "0.716"],
   ["A2", "RF", "0.858 (0.852–0.864)", "0.644", "0.819", "0.527", "0.905", "0.571", "0.460"],
   ["A2", "HGB", "0.999 (0.998–0.999)", "0.996", "0.979", "0.981", "0.978", "0.955", "0.942"],
   ["L0", "LR", "0.908 (0.904–0.912)", "0.658", "0.829", "0.839", "0.826", "0.692", "0.595"],
   ["L0", "RF", "0.999 (0.999–0.999)", "0.997", "0.987", "0.985", "0.988", "0.972", "0.964"],
   ["L0", "HGB", "0.999 (0.999–0.999)", "0.996", "0.979", "0.983", "0.977", "0.955", "0.942"]]),
"delta": ("Table 3. Paired bootstrap AUC gain over scenario B and household-grouped five-fold cross-validation (HGB)",
  [2.0, 3.2, 3.3, 2.6, 3.6],
  [["Comparison", "ΔAUC LR (95% CI)", "ΔAUC RF (95% CI)", "ΔAUC HGB (95% CI)", "HGB 5-fold CV AUC (mean ± SD)"],
   ["B (reference)", "–", "–", "–", "0.675 ± 0.002"],
   ["A1 vs B", "0.138 (0.129–0.147)", "0.097 (0.090–0.105)", "0.146 (0.136–0.154)", "0.824 ± 0.003"],
   ["A2 vs B", "0.289 (0.279–0.299)", "0.196 (0.189–0.204)", "0.322 (0.312–0.332)", "0.998 ± 0.000"],
   ["L0 vs B", "0.247 (0.237–0.258)", "0.338 (0.328–0.347)", "0.323 (0.312–0.333)", "0.999 ± 0.000"],
   ["Inflation, A2 (2)", "179%", "121%", "183%", "–"]]),
"lit": ("Table 4. Reported performance of recent studies using current anthropometry versus the leakage-free baseline",
  [3.6, 3.0, 5.2, 2.9],
  [["Study", "Data", "Anthropometric inputs (as reported)", "Reported performance"],
   ["Anku and Duah {anku}", "Ghana survey", "Weight, length/height, age among top predictors", "Accuracy 86%–98%"],
   ["Ayele et al. {ayele}", "Ethiopia DHS", "Height and weight ranked after age; SMOTE before split", "Accuracy 97.99%, AUC 0.99995"],
   ["Hendy et al. {hendy}", "Egypt DHS", "Height and weight among inputs", "Accuracy > 90%, AUC > 0.96"],
   ["Wudu et al. {wudu}", "Ethiopia survey", "Height most influential feature (SHAP)", "Accuracy 94%"],
   ["This study, A2 (leaky)", "SKI 2023", "Weight, height, MUAC, waist", "Accuracy 97.8%, AUC 0.998"],
   ["This study, B (leakage-free)", "SKI 2023", "None", "AUC 0.654–0.670"]]),
}

REFS = {
"victora": "C. G. Victora, P. Christian, L. P. Vidaletti, G. Gatica-Domínguez, P. Menon, and R. E. Black, “Revisiting maternal and child undernutrition in low-income and middle-income countries: variable progress towards an unfinished agenda,” The Lancet, vol. 397, no. 10282, pp. 1388–1399, 2021, doi: 10.1016/S0140-6736(21)00394-9.",
"mulya": "T. Mulyaningsih, I. Mohanty, V. Widyaningsih, T. A. Gebremedhin, R. Miranti, and V. H. Wiyono, “Beyond personal factors: multilevel determinants of childhood stunting in Indonesia,” PLoS ONE, vol. 16, no. 11, p. e0260265, 2021, doi: 10.1371/journal.pone.0260265.",
"rahman": "S. M. J. Rahman et al., “Investigate the risk factors of stunting, wasting, and underweight among under-five Bangladeshi children and its prediction based on machine learning approach,” PLoS ONE, vol. 16, no. 6, p. e0253172, 2021, doi: 10.1371/journal.pone.0253172.",
"mansur": "M. Mansur, A. Afiaz, and M. S. Hossain, “Sociodemographic risk factors of under-five stunting in Bangladesh: assessing the role of interactions using a machine learning method,” PLoS ONE, vol. 16, no. 8, p. e0256729, 2021, doi: 10.1371/journal.pone.0256729.",
"bitew": "F. H. Bitew, C. S. Sparks, and S. H. Nyarko, “Machine learning algorithms for predicting undernutrition among under-five children in Ethiopia,” Public Health Nutrition, vol. 25, no. 2, pp. 269–280, 2022, doi: 10.1017/S1368980021004262.",
"fenta": "H. M. Fenta, T. Zewotir, and E. K. Muluneh, “A machine learning classifier approach for identifying the determinants of under-five child undernutrition in Ethiopian administrative zones,” BMC Medical Informatics and Decision Making, vol. 21, no. 1, p. 291, 2021.",
"chily": "O. N. Chilyabanyama et al., “Performance of machine learning classifiers in classifying stunting among under-five children in Zambia,” Children, vol. 9, no. 7, p. 1082, 2022, doi: 10.3390/children9071082.",
"usman": "M. Usman and K. Kopczewska, “Spatial and machine learning approach to model childhood stunting in Pakistan: role of socio-economic and environmental factors,” International Journal of Environmental Research and Public Health, vol. 19, no. 17, p. 10967, 2022, doi: 10.3390/ijerph191710967.",
"shen": "H. Shen, H. Zhao, and Y. Jiang, “Machine learning algorithms for predicting stunting among under-five children in Papua New Guinea,” Children, vol. 10, no. 10, p. 1638, 2023, doi: 10.3390/children10101638.",
"ndag": "S. Ndagijimana, I. H. Kabano, E. Masabo, and J. M. Ntaganda, “Prediction of stunting among under-5 children in Rwanda using machine learning techniques,” Journal of Preventive Medicine and Public Health, vol. 56, no. 1, pp. 41–49, 2023, doi: 10.3961/jpmph.22.388.",
"islam": "M. M. Islam, N. M. S. J. Kibria, S. Kumar, D. C. Roy, and M. R. Karim, “Prediction of undernutrition and identification of its influencing predictors among under-five children in Bangladesh using explainable machine learning algorithms,” PLoS ONE, vol. 19, no. 12, p. e0315393, 2024, doi: 10.1371/journal.pone.0315393.",
"anku": "E. K. Anku and H. O. Duah, “Predicting and identifying factors associated with undernutrition among children under five years in Ghana using machine learning algorithms,” PLoS ONE, vol. 19, no. 2, p. e0296625, 2024, doi: 10.1371/journal.pone.0296625.",
"ayele": "M. K. Ayele, G. A. Baye, S. H. Yesuf, A. A. Engda, and E. T. Mitiku, “Predicting stunting status among under five children in Ethiopia using ensemble machine learning algorithms,” Scientific Reports, vol. 15, p. 27907, 2025, doi: 10.1038/s41598-025-03206-1.",
"wudu": "T. K. Wudu, A. A. Endalew, and A. A. Dires, “Explainable hybrid machine learning model for predicting stunting and identifying key risk factors among Ethiopian children under five,” Scientific Reports, vol. 16, p. 16204, 2026, doi: 10.1038/s41598-026-46417-w.",
"hendy": "A. Hendy et al., “Supervised machine learning for classification and prediction of stunting among under-five Egyptian children,” BMC Pediatrics, vol. 25, p. 681, 2025, doi: 10.1186/s12887-025-06138-x.",
"hendyw": "A. Hendy et al., “Unlocking insights: using machine learning to identify wasting and risk factors in Egyptian children under 5,” Nutrition, vol. 131, p. 112631, 2025.",
"sasse": "L. Sasse et al., “Overview of leakage scenarios in supervised machine learning,” Journal of Big Data, vol. 12, p. 41, 2025, doi: 10.1186/s40537-025-01193-8.",
"bernett": "J. Bernett et al., “Guiding questions to avoid data leakage in biological machine learning applications,” Nature Methods, vol. 21, no. 8, pp. 1444–1453, 2024, doi: 10.1038/s41592-024-02362-y.",
"kapoor": "S. Kapoor and A. Narayanan, “Leakage and the reproducibility crisis in machine-learning-based science,” Patterns, vol. 4, no. 9, p. 100804, 2023, doi: 10.1016/j.patter.2023.100804.",
"messeri": "L. Messeri and M. J. Crockett, “Artificial intelligence and illusions of understanding in scientific research,” Nature, vol. 627, pp. 49–58, 2024, doi: 10.1038/s41586-024-07146-0.",
"rosen": "M. Rosenblatt, L. Tejavibulya, R. Jiang, S. Noble, and D. Scheinost, “Data leakage inflates prediction performance in connectome-based machine learning models,” Nature Communications, vol. 15, p. 1829, 2024, doi: 10.1038/s41467-024-46150-w.",
"mortel": "L. A. van de Mortel and G. A. van Wingen, “Data leakage in machine learning studies creep into meta-analytic estimates of predictive performance,” Molecular Psychiatry, 2025, doi: 10.1038/s41380-025-03336-y.",
"tripod": "G. S. Collins et al., “TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods,” BMJ, vol. 385, p. e078378, 2024, doi: 10.1136/bmj-2023-078378.",
"reforms": "S. Kapoor et al., “REFORMS: consensus-based recommendations for machine-learning-based science,” Science Advances, vol. 10, no. 18, p. eadk3452, 2024, doi: 10.1126/sciadv.adk3452.",
"joeres": "R. Joeres, D. B. Blumenthal, and O. V. Kalinina, “Data splitting to avoid information leakage with DataSAIL,” Nature Communications, vol. 16, p. 3337, 2025, doi: 10.1038/s41467-025-58606-8.",
"apicella": "A. Apicella, F. Isgrò, and R. Prevete, “Don't push the button! Exploring data leakage risks in machine learning and transfer learning,” Artificial Intelligence Review, 2025, doi: 10.1007/s10462-025-11326-3.",
"vancalster": "B. Van Calster, E. W. Steyerberg, L. Wynants, and M. van Smeden, “There is no such thing as a validated prediction model,” BMC Medicine, vol. 21, p. 70, 2023, doi: 10.1186/s12916-023-02779-w.",
}

TABLES['perf'] = (TABLES['perf'][0], TABLES['perf'][1], [['Scenario', 'Model', 'AUC (95% CI)', 'PR-AUC', 'Accuracy', 'Recall', 'Specificity', 'F1', 'MCC'], ['Baseline', 'Majority class', '0.500', '0.235', '0.765', '0.000', '1.000', '0.000', '0.000'], ['B', 'LR', '0.656 (0.647–0.665)', '0.356', '0.610', '0.615', '0.609', '0.426', '0.191'], ['B', 'RF', '0.654 (0.644–0.663)', '0.358', '0.744', '0.213', '0.908', '0.282', '0.158'], ['B', 'HGB', '0.670 (0.661–0.679)', '0.373', '0.629', '0.613', '0.634', '0.438', '0.212'], ['A1', 'LR', '0.803 (0.795–0.810)', '0.558', '0.721', '0.760', '0.709', '0.562', '0.406'], ['A1', 'RF', '0.759 (0.750–0.767)', '0.483', '0.771', '0.377', '0.893', '0.437', '0.304'], ['A1', 'HGB', '0.825 (0.818–0.833)', '0.620', '0.763', '0.734', '0.772', '0.594', '0.452'], ['A2', 'LR', '0.951 (0.948–0.954)', '0.819', '0.882', '0.908', '0.874', '0.784', '0.718'], ['A2', 'RF', '0.862 (0.856–0.868)', '0.647', '0.818', '0.536', '0.905', '0.582', '0.469'], ['A2', 'HGB', '0.998 (0.998–0.999)', '0.995', '0.978', '0.980', '0.977', '0.954', '0.940'], ['L0', 'LR', '0.910 (0.905–0.914)', '0.679', '0.830', '0.837', '0.828', '0.699', '0.600'], ['L0', 'RF', '0.999 (0.999–0.999)', '0.997', '0.984', '0.982', '0.985', '0.966', '0.956'], ['L0', 'HGB', '0.999 (0.998–0.999)', '0.996', '0.978', '0.983', '0.977', '0.955', '0.941']])
TABLES['delta'] = (TABLES['delta'][0], TABLES['delta'][1], [['Comparison', 'ΔAUC LR (95% CI)', 'ΔAUC RF (95% CI)', 'ΔAUC HGB (95% CI)', 'HGB 5-fold CV AUC (mean ± SD)'], ['B (reference)', '–', '–', '–', '0.671 ± 0.005'], ['A1 vs B', '0.147 (0.139–0.155)', '0.105 (0.098–0.111)', '0.155 (0.146–0.164)', '0.822 ± 0.002'], ['A2 vs B', '0.295 (0.286–0.304)', '0.209 (0.201–0.216)', '0.328 (0.320–0.337)', '0.998 ± 0.000'], ['L0 vs B', '0.254 (0.244–0.263)', '0.345 (0.336–0.354)', '0.328 (0.320–0.337)', '0.999 ± 0.000'], ['Inflation, A2 (2)', '189%', '136%', '193%', '–']])
