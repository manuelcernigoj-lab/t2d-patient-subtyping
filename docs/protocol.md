# Analysis Protocol — Patient Subtyping in a Type 2 Diabetes Cohort (Synthea)

## Status: Phases 0–4 complete + exploratory extension (notebook 05) — ready for reporting

---

## 1. Cohort Definition

**Source population**: ~20,000 synthetic patients generated with Synthea (targeting a final
cohort of 1,500-2,000 diabetic patients, assuming a real-world prevalence of ~8-10%).

**Inclusion criteria**:

- Type 2 diabetes diagnosis present in `conditions.csv` (SNOMED-CT `44054006`)
- At least one HbA1c measurement recorded in `observations.csv` (LOINC `4548-4`)

**Criteria intentionally left open (to be assessed exploratively)**:

- **Age**: no minimum age filter is applied at this stage. After the ETL step, the age
  distribution of the diabetic cohort will be reviewed. If a relevant subgroup of early-onset
  patients emerges (e.g., <30 years), a decision will be made, with documented justification,
  to either:
  - include them in the main analysis,
  - treat them as a separate subgroup with dedicated commentary,
  - or exclude them with explicit reasoning.

  This decision will be made **based on the actual data**, during Phase 2/3, and documented as
  a deviation from the initial protocol.

  **Outcome (Phase 2)**: the age distribution was reviewed (range 19-110, median 63, mean 64.6).
  Only 7 out of 1,763 patients (0.4%) are below age 30, too small a subgroup to analyze
  separately, and the distribution shows no secondary peak suggesting a distinct early-onset
  phenotype. **Decision**: all 1,763 patients are included in the main analysis without any
  age-based filtering or stratification.

**Deceased patients**: included in the analysis, using the last available value for each
variable (standard approach for cross-sectional analyses on EHR data).

---

## 2. Candidate Variables

| Domain | Variables | Source (Synthea file) | Clinical rationale |
|---|---|---|---|
| Demographics | Age, sex, BMI | `patients.csv`, `observations.csv` (LOINC 39156-5) | Key dimensions in diabetes subtype frameworks (e.g., Ahlqvist et al.) |
| Comorbidity | Charlson Comorbidity Index (CCI) | `conditions.csv` | Overall disease burden, standard in epidemiology |
| Medication | Drug classes: metformin, sulfonylureas, insulin, SGLT2 inhibitors, GLP-1 agonists | `medications.csv` | Treatment pattern as a proxy for severity/phenotype |
| Laboratory | HbA1c, glucose, LDL/HDL/triglycerides, creatinine/eGFR | `observations.csv` | Glycemic control and metabolic/renal complications |
| Healthcare utilization | Number of encounters/year | `encounters.csv` | Proxy for overall care burden |

**Note**: this list is a clinically-reasoned "wishlist". In Phase 1, after initial exploration of
the generated CSVs, the actual availability of each variable will be verified and the list will
be updated accordingly (documented deviation if needed). *Medication classes were revised in
Phase 2 based on actual availability, see Section 4.*

### Deviation log

- **LDL cholesterol**: the originally planned LOINC code `2089-1` ("LDL calculated") returned
  zero observations for the cohort. Investigation by `DESCRIPTION` search identified
  `18262-6` ("Cholesterol in LDL, direct assay") as the code actually used by Synthea. The
  candidate variable list has been updated accordingly: `2089-1` → `18262-6`.
- **Total cholesterol**: LOINC `2093-3` ("Cholesterol [Mass/volume] in Serum or Plasma") was
  found during the same investigation and added as an additional candidate variable, since it
  is clinically informative and was not part of the original wishlist.

Final laboratory variable set: HbA1c (`4548-4`), Glucose (`2339-0`), BMI (`39156-5`), LDL
(`18262-6`), HDL (`2085-9`), Total Cholesterol (`2093-3`), Triglycerides (`2571-8`), Creatinine
(`2160-0`).

### Missing data handling: Creatinine

Creatinine showed 52.4% missingness across the cohort (924 of 1,763 patients), substantially
higher than any other laboratory variable (all others: 0% missing). This is interpreted as
**missing not at random**: creatinine is not part of routine diabetes monitoring and is more
likely to be ordered when renal impairment is already suspected (e.g., in older patients or
those with other comorbidities). Imputing with the sample median of the measured subgroup would
therefore be biased, that subgroup is enriched for patients with a clinical reason to be
tested.

**Decision**: missingness is encoded explicitly via a binary indicator (`creatinine_measured`),
preserving the "was this patient tested?" signal as a separate feature. The missing values
themselves are imputed with a fixed clinical reference value (0.9 mg/dL, approximate midpoint of
the normal adult range), rather than a sample-derived statistic.

**Quantitative validation**: the median creatinine value among the 840 patients for whom it
*was* measured is 2.1 mg/dL, well above the normal range upper limit (~1.3 mg/dL) and more than
double the reference value used for imputation. This confirms the selection-bias hypothesis:
patients who get tested are not representative of the cohort as a whole, supporting the choice
of a reference value over the sample median.

---

## 3. Feature Engineering: Charlson Comorbidity Index (CCI)

Chosen over a simple comorbidity count, for consistency with a recognized standard in
epidemiological/RWE literature.

**Implementation note**: the CCI is traditionally defined using ICD-9/ICD-10 codes, while
Synthea uses SNOMED-CT codes in `conditions.csv`. A SNOMED → Charlson category mapping was built,
grounded in the conditions actually present in the cohort (identified via frequency analysis and
targeted keyword search), rather than the full theoretical CCI schema.

### Mapping and category weights

| Charlson category | Weight | SNOMED-CT codes mapped |
|---|---|---|
| Diabetes (uncomplicated) | 1 | 44054006 |
| Diabetes with end-organ damage | 2 | 127013003, 90781000119102, 368581000119106 |
| Myocardial infarction | 1 | 399211009, 401314000, 401303003, 22298006 |
| Congestive heart failure | 1 | 88805009, 84114007 |
| Cerebrovascular disease | 1 | 230690007 |
| Renal disease (moderate/severe) | 2 | 433144002, 431857002, 46177005 |
| Connective tissue disease | 1 | 69896004, 200936003 |
| Mild liver disease | 1 | 128302006 |
| Malignancy (non-metastatic) | 2 | 254837009, 424132000, 109838007, 363406005, 93761005, 93143009, 254632001, 67811000119102 |
| Metastatic malignancy | 6 | 94503003, 94260004 |

**Mutual exclusivity**: within the diabetes group and the malignancy group, only the higher
weight is counted when both levels are present for a patient (e.g., a patient with diabetes and
diabetic nephropathy scores 2, not 1+2=3).

**Exclusions (documented deviations from a literal SNOMED keyword match)**:

- *"Ischemic heart disease"* (414545008) was considered as a possible proxy for myocardial
  infarction, but excluded once explicit, more specific infarction codes were found in the data
  (see table above). Using the broader "ischemic heart disease" label would have overstated this
  category.
- *"Carcinoma in situ of prostate"* (92691004) was excluded from the malignancy category. The
  standard CCI counts invasive malignancy; in-situ (pre-invasive) neoplasms are conventionally
  not included.
- Chronic kidney disease stages 1-2 were identified in the data but excluded, consistent with the
  standard CCI definition, which counts only moderate/severe renal disease (stage 3 and above).

### Resulting distribution

CCI ranges from 1 to 10 across the cohort (mean 2.31, median 2, SD 1.45). All patients score at
least 1 point by definition (uncomplicated diabetes is always present in this cohort).

---

## 4. Feature Engineering: Medication and Healthcare Utilization

### Medication features

Initial frequency analysis and targeted keyword search of `medications.csv` identified two
well-represented antidiabetic drug classes (metformin: 890 patients; insulin, combining 3 codes:
658 patients) and two rare ones (GLP-1 agonists: 17 patients; SGLT2 inhibitors: 4 patients). No
sulfonylureas, DPP-4 inhibitors, or thiazolidinediones were found in the generated dataset.

**Decision**: standalone binary features were built only for metformin and insulin. GLP-1
agonists and SGLT2 inhibitors were grouped into a single `on_other_antidiabetic` feature, since
individually they are too rare (0.2%-1% of the cohort) to carry discriminative power for
clustering, a feature that is almost entirely zero contributes no useful variance. This
preserves the "on a more recent/specialist therapy" signal without introducing near-constant
columns. This is a deviation from the original wishlist (Section 2), which listed sulfonylureas
and SGLT2 inhibitors as separate candidate variables.

Resulting features: `on_metformin`, `on_insulin`, `on_other_antidiabetic`. 516 patients (29% of
the cohort) are on none of the three, plausibly patients managed by diet/lifestyle alone, or
with borderline glycemic control not yet requiring pharmacological treatment.

### Healthcare utilization

Built as `encounters_per_year`: total encounters divided by each patient's observation window
(time between first and last recorded encounter), to make patients with different
follow-up lengths comparable.

**Distribution note**: the resulting variable is right-skewed (median 1.31, mean 2.42, max
20.64), a small subgroup of patients has much higher utilization than the majority, plausibly
overlapping with the high-CCI/complication subgroup. Flagged for Phase 3: this skew may warrant
a log transformation before scaling, since K-means relies on Euclidean distance and extreme
values could otherwise dominate the clustering result.

---

## 5. Initial Clinical Hypotheses

Defined *before* the exploratory analysis, as a reference for cluster interpretation in Phase 4
— not as an outcome to be forced.

- **H1 — "Insulin-resistant" cluster**: younger patients, higher BMI, on multiple glucose-lowering
  medications (analogous to Ahlqvist et al.'s SIRD subtype).
- **H2 — "Mild/late-onset" cluster**: older patients, HbA1c close to target, managed with
  metformin or diet alone (analogous to the MARD subtype, typically the largest).
- **H3 — "Multi-morbid" cluster**: high CCI, high encounter frequency, possible renal impairment,
  independent of glycemic control.
- **H4 — "Poor glycemic control" cluster**: elevated HbA1c despite intensive therapy (insulin
  plus other agents), a clinically high-priority group due to complication risk.

**Note**: H3 and H4 may overlap in practice. Clustering will help clarify whether these represent
distinct groups or a single phenotype with dual characteristics.

---

## 6. Literature Reference for Validation

Ahlqvist et al., 2018, *Lancet Diabetes & Endocrinology*, identification of 5 adult-onset
diabetes subgroups (SAID, SIDD, SIRD, MOD, MARD) based on age, BMI, HbA1c, autoantibodies, and
insulin resistance/secretion indices. To be used as a conceptual reference for cluster
interpretation, with appropriate caution: the data used here are synthetic and do not include
all variables from the original study (e.g., autoantibodies, HOMA-B/HOMA-IR).

---

## 7. Phase 3 — Clustering: Methodology and Results

### 7.1 Exploratory Data Analysis

Distribution and correlation analysis on the full `patient_features` table surfaced
several findings ahead of feature engineering: `HbA1c` and `Glucose` show multimodal
distributions, hinting at distinct glycemic-control subgroups even at the univariate
level; `BMI` is bimodal (flagged as a possible Synthea generation artifact rather than
a confirmed clinical pattern); `Triglycerides` is heavily right-skewed; `Creatinine`'s
distribution visibly shows the Phase 2 imputation strategy as a spike near the
reference value, distinct from the measured-value distribution. The correlation
matrix revealed LDL/Total Cholesterol multicollinearity (r=0.90) and a notable
negative correlation between HbA1c and CCI/encounters_per_year/Creatinine (-0.46 to
-0.54), an early signal that H3 and H4 (Section 5) might be distinct rather than
overlapping phenotypes.

### 7.2 Feature Engineering Finalization

- **Total Cholesterol dropped**: r=0.90 with LDL; LDL retained as the more standard
  lipid marker in T2D literature.
- **`encounters_per_year` log1p-transformed** to address right-skew ahead of
  Euclidean-distance-based clustering.
- **Categorical encoding**: `GENDER` binary-mapped; `RACE` and `ETHNICITY` one-hot
  encoded with `drop_first=False`, a deliberate deviation from the regression
  convention of dropping a reference category, since for distance-based clustering,
  dropping a category breaks the equidistance between categories that one-hot
  encoding is meant to provide.

### 7.3 Feature Scaling

`RobustScaler` (median/IQR) applied to the 10 continuous features only; the 13
binary/one-hot columns left unscaled (already on a native 0-1 scale). RobustScaler
chosen over `StandardScaler` for resilience to residual outliers in `Triglycerides`
and `Creatinine`. Final clustering input matrix `X_scaled`, shape (1763, 23).

### 7.4 K Selection — Round 1 (full feature set) and Diagnosis

Elbow method (full 23-feature set) suggested K=4-5; silhouette score favored K=2
(~0.44) almost exclusively, with all K≥3 falling below the 0.25 "weak structure"
threshold (Kaufman & Rousseeuw scale).

**Diagnostic 1 — K=2 profiling**: revealed near-identical values across clusters for
`AGE`, `HbA1c`, `CCI`, `Creatinine`, `encounters_per_year`, but a sharp split on
`on_metformin` (47.7% vs 98.0%) and highly imbalanced cluster sizes (1664 vs 99). This
indicated the K=2 split was driven by medication assignment, not disease severity.

**Diagnostic 2 — dendrogram (ward linkage, full feature set)**: showed 4
default-colored branches (scipy's 0.7×max-height auto-threshold, not a statistically
chosen K), but a weak relative merge-height gap between the two largest branches
(~669 and ~724 patients), suggesting a natural cut closer to K=3.

**Root cause**: with 13 of 23 features being unscaled binary/one-hot columns
(medication flags, `RACE`, `ETHNICITY`), the categorical block was disproportionately
influencing Euclidean distance relative to the 10 RobustScaler-scaled continuous
clinical features.

**Decision (deviation from initial plan)**: medication and demographic categorical
features excluded from the clustering *input* (kept in `patient_features` for
post-hoc profiling and equity checks). Clustering re-run on `X_clinical`, the 10
continuous clinical features only.

### 7.5 K Selection — Round 2 (clinical features only) and Final Choice

Silhouette improved across all K (K=2: 0.44→0.475; K=3: 0.21→0.265; K=4: 0.16→0.19).
**K=3 crossed the 0.25 "reasonable structure" threshold for the first time**; K=4
remained below it. The dendrogram on `X_clinical` showed exactly 3 default-colored
branches (no residual 4th split), with consistent relative gaps (~19-38) across all
three, a markedly cleaner structure than the full-feature dendrogram.

**Robustness check**: KMeans vs. Agglomerative (ward) agreement, measured via
Adjusted Rand Index — K=3: ARI=0.703 (strong agreement); K=4: ARI=0.327 (weak/
divergent, the two algorithms disagree on where to cut). PCA visualization (48.7%
variance explained by PC1+PC2) corroborated this: the small distinct subgroup is
visually identical across K=3 and K=4, while K=4 arbitrarily bisects the large dense
cluster with no visible density gap.

**Decision: K=3 adopted as the final model.** Four independent diagnostics (elbow,
silhouette, dendrogram gap structure, ARI) converge on this choice.

### 7.6 Cluster Profiling Against H1-H4

| Cluster | n (%) | Profile | Hypothesis match |
|---|---|---|---|
| 0 | 1303 (73.9%) | HbA1c 6.09, CCI 1.77 (lowest), encounters 1.34 (lowest), metformin 48% | Partial **H2** (largest subtype, as expected; age criterion not met) |
| 1 | 94 (5.3%) | BMI 31.0, Triglycerides 375.9, HDL 29.9 (lowest), metformin 98% | Partial **H1** (dyslipidemic/insulin-resistant profile; age criterion not met) |
| 2 | 366 (20.8%) | Age 72.7 (oldest), CCI 4.34, encounters 6.35, insulin 91% | Strong **H3** (multi-morbid) |

**H4 ("poor glycemic control despite intensive therapy") not confirmed.** The data
show the inverse pattern: Cluster 2 (most intensively treated, 91% on insulin) has
the lowest HbA1c (3.76); Cluster 0 (least intensively treated, 23% on insulin) has
the highest HbA1c (6.09). **Reinterpretation (documented deviation)**: this more
plausibly reflects *undertreatment* of poorly controlled patients, not treatment-
resistant poor control.

**K=4 evaluated and not adopted**: reproduces Clusters 1 and 2 unchanged; splits
Cluster 0 into two halves differing mainly in metformin use (89% vs 21%) and LDL,
with no difference in age, CCI, or encounters, a treatment/lipid-control gradient
within the same population, not a new severity axis. Flagged as a possible direction
for future work (e.g., a continuous treatment-adherence score) rather than grounds
for a fourth cluster.

### 7.7 Demographic Equity Check (Post-Hoc)

`RACE`, `ETHNICITY`, and `GENDER`, excluded from clustering inputs in Section 7.4,
were checked post-hoc for disproportionate distribution across the K=3 clusters. No
significant association found: RACE (chi2=8.18, p=0.611), ETHNICITY (chi2=2.45,
p=0.294), GENDER (chi2=2.10, p=0.350). Given the cohort size (~1800), this null
result is statistically informative (high test power), though `RACE_hawaiian` and
`RACE_native` (~1% of the cohort each) likely fall below the conventional expected-
cell-count threshold for chi-square reliability, the rarest-category finding should
be read with appropriate caution.

### 7.8 Deviation Log (Phase 3 Summary)

- Total Cholesterol dropped post-hoc (multicollinearity with LDL).
- One-hot encoding used `drop_first=False`, a clustering-specific deviation from the
  regression convention.
- Medication and demographic categorical features excluded from the clustering
  distance metric after diagnostic evidence of disproportionate influence, a
  mid-phase deviation from the original intent of including the full candidate
  feature set (Section 2).
- H4 reinterpreted as an undertreatment pattern rather than treatment-resistant poor
  control, based on cluster-level evidence.

  ## Appendix — Supplementary exploration: metformin gradient and dataset limitations

A supplementary post-hoc exploration (notebook 03) investigated whether the
metformin-associated metabolic gradient observed within Cluster 0 ("Mild, lower
treatment intensity") represented a discrete sub-phenotype. Recursive clustering
(silhouette, K=2-7), Mann-Whitney effect sizes, and visual inspection converged on
classifying it as a real but continuous gradient, not a discrete sub-cluster, the
finalized K=3 solution (Section 7) is unaffected.

**Dataset limitation identified**: HbA1c and BMI show sharp, near-categorical
density spikes inconsistent with continuous biological measurement, most plausibly
a Synthea data-generation artifact (discrete clinical-state modules). This banding
is independent of the metformin gradient and was not investigated further, as the
generation mechanism itself is out of scope. Readers/reviewers of this project
should be aware that subtype boundaries derived from HbA1c in this synthetic
dataset may be influenced by this artifact, and that conclusions drawn from HbA1c
distributional shape (beyond central tendency) warrant caution.

## 8. Phase 4 — Predictive Modeling: Early Subtype Stratification

### 8.1 Objective

Test whether the three Phase 3 subtypes can be predicted from features available at or
near diagnosis, **before** any treatment decision is made, directly testing the
"early subtype identification" framing emphasized in RWE/precision-medicine literature and
job descriptions. Target: `cluster_label` (3 classes, from
`patient_features_clustered.parquet`), imbalanced 73.9% / 20.8% / 5.3% (Mild / Multimorbid
/ Dyslipidemic).

### 8.2 Predictor Set: Treatment-Naive Design

| Included (9 features) | Excluded | Rationale |
|---|---|---|
| AGE, HbA1c, Glucose, BMI, LDL, HDL, Triglycerides, Creatinine, `creatinine_measured` | CCI, `encounters_per_year` | Accumulate over years of follow-up, not available at a single baseline visit; including them would make Cluster 2 trivially separable and defeat the "early" purpose |
| | `on_metformin`, `on_insulin`, `on_other_antidiabetic` | Near-deterministically leak the cluster label (Multimorbid = 91% insulin, Dyslipidemic = 98% metformin); deliberately excluded for a treatment-naive use case |
| | RACE, ETHNICITY, GENDER | Consistent with the equity-driven exclusion already applied to Phase 3 clustering; the Phase 3 equity check found no significant association, so no predictive power is lost |

### 8.3 Train/Test Split and Cross-Validation Strategy

- **Outer split**: 80% train (n=1410) / 20% holdout test (n=353), `stratify=y` to preserve
  class proportions in both sets. The holdout test set was used exactly once, at the end,
  for final model evaluation, never for training or model selection.
- **Inner validation**: `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` on the
  training set, used for model comparison and selection. Stratification was necessary given
  the small minority class (Dyslipidemic, n≈94 total, ≈19 per fold), unstratified folds
  risked unstable per-fold class proportions.
- **Scaling**: `RobustScaler`, wrapped in a `Pipeline` with the logistic regression model so
  it is refit independently within each CV fold (avoiding leakage of fold-test statistics
  into training). Not applied for the two tree-based models (Random Forest,
  HistGradientBoosting), since split-based models are scale-invariant.
- **Primary metric**: macro-F1 (unweighted average of per-class F1), chosen over accuracy
  given the class imbalance, a majority-class-only classifier would reach ~74% accuracy
  while being clinically useless for the two minority subtypes.

### 8.4 Candidate Models and Cross-Validation Results

All three models used `class_weight="balanced"` to counteract class imbalance during
training.

| Model | Macro-F1 (mean ± SD) | Accuracy (mean ± SD) |
|---|---|---|
| Logistic Regression (`max_iter=1000`) | 0.877 ± 0.023 | 0.873 ± 0.020 |
| Random Forest (`n_estimators=300`) | 0.881 ± 0.022 | 0.894 ± 0.019 |
| HistGradientBoosting | 0.898 ± 0.020 | 0.907 ± 0.016 |

**Per-class out-of-fold breakdown** (precision / recall / F1):

| Class | Logistic Regression | Random Forest | HistGradientBoosting |
|---|---|---|---|
| Dyslipidemic / metabolic | 0.94 / 1.00 / 0.97 | 0.90 / 0.96 / 0.93 | 0.96 / 0.99 / 0.97 |
| Mild, lower treatment intensity | 0.98 / 0.85 / 0.91 | 0.97 / 0.89 / 0.93 | 0.94 / 0.93 / 0.94 |
| Multimorbid, high care complexity | 0.64 / 0.92 / 0.75 | 0.69 / 0.90 / 0.78 | 0.77 / 0.80 / 0.78 |

**Feature importance** (fit on full train set, post-CV): logistic regression coefficients
and Random Forest importance converge on the same top features (`Triglycerides`, `Glucose`/
`Creatinine`, `HbA1c`), supporting genuine signal rather than an algorithm-specific
artifact. Logistic regression coefficients are also clinically interpretable: Dyslipidemic
is driven by `Triglycerides` (+2.33) and low `HDL` (-0.97); Multimorbid by `HbA1c` (-1.87)
together with `Creatinine` (+1.08) and `creatinine_measured` (+0.99), the model
independently recovered the Phase 2 missing-not-at-random creatinine signal.

**Caveat**: `HbA1c` ranks among the top 2-3 features in both models, despite the
Synthea-generated banding artifact documented in notebook 03 (Section 7 appendix). `BMI`,
the other flagged variable, shows minimal importance in both models, the exposure is
contained to one feature, but remains a documented limitation of the final model's signal.

### 8.5 Model Selection: Deviation from Macro-F1-Only Selection

**Decision**: HistGradientBoosting had the highest macro-F1 (0.898) but was **not**
selected. Clinical reasoning was applied instead: a Multimorbid patient (Phase 3 profile,
CCI 4.34, 6.35 encounters/year, 91% on insulin) carries materially higher clinical risk if
missed at baseline than a Dyslipidemic patient. **Multimorbid recall was therefore adopted
as the deciding metric**, not aggregate macro-F1.

| Model | Multimorbid recall |
|---|---|
| Logistic Regression | **0.92** |
| Random Forest | 0.90 |
| HistGradientBoosting | 0.80 |

HistGradientBoosting's higher aggregate score came from improved Multimorbid *precision*
(fewer false alarms), not recall, it missed 20% of true Multimorbid patients
(out-of-fold), the opposite direction of the established clinical priority, and was ruled
out on that basis despite the strongest aggregate metric.

**Final model: Logistic Regression**, best Multimorbid recall (0.92), perfect Dyslipidemic
recall (1.00), and the most interpretable of the three candidates (a relevant secondary
benefit for reporting and stakeholder communication). Accepted trade-off: the highest
Mild→Multimorbid confusion of the three models (15%), over-triage of a mild patient, the
lower-risk direction of error compared to under-triage of a complex one.

### 8.6 Final Holdout Test Performance (n=353, evaluated once)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Dyslipidemic / metabolic | 0.90 | 1.00 | 0.95 | 19 |
| Mild, lower treatment intensity | 0.98 | 0.84 | 0.90 | 261 |
| Multimorbid, high care complexity | 0.61 | 0.92 | 0.74 | 73 |
| **Macro avg** | 0.83 | **0.92** | 0.86 | 353 |

Holdout results closely match the cross-validation estimates (macro-F1 0.86 vs. 0.877 ± 0.023;
Multimorbid recall 0.92, identical to the CV estimate), confirming the model-selection
decision generalizes to unseen patients rather than reflecting an artifact of the CV
process itself.

**Answer to the Phase 4 research question**: yes, baseline treatment-naive features
meaningfully stratify patients into the three Phase 3 subtypes, even excluding the most
discriminative variables (CCI, `encounters_per_year`) by design. Performance is strongest
for Dyslipidemic (defined almost entirely by the baseline lipid panel) and good, though
imperfect, for the Mild/Multimorbid boundary, matching the moderate-performance
expectation set at the start of Phase 4 scoping rather than an engineered-away result.

### 8.7 Limitations and Future Work

- Dyslipidemic test support is small (n=19); the precision estimate (0.90) carries wider
  sampling uncertainty than the other two classes despite a strong point estimate.
- Multimorbid precision (0.61) is the weakest spot: roughly 4 in 10 patients flagged as
  Multimorbid are false alarms, an accepted trade-off given the priority on Multimorbid
  recall.
- Part of the model's signal rests on `HbA1c`, a variable with a documented synthetic-data
  banding artifact (notebook 03).
- Future work: a continuous treatment-adherence score (flagged in notebook 03) as an
  additional baseline feature; a probability-threshold adjustment (instead of the default
  0.5 cutoff) to push Multimorbid recall further, trading deeper into Mild/Multimorbid
  confusion if clinically justified.

---

## 9. Exploratory Extension — Treatment Adherence/Intensity Score (Notebook 05)

### 9.1 Motivation

Section 7.6 noted a metformin-associated metabolic gradient within Cluster 0 as a
candidate direction for future work. Notebook 03 (Section 7 appendix) classified this
gradient as continuous rather than a discrete sub-phenotype. This notebook constructs
a quantitative, continuous treatment intensity score to characterize that gradient
across all three Phase 3 subtypes and test whether it aligns with the clinical
profiles established in Phase 3.

This analysis is explicitly **exploratory and descriptive**, it does not modify the
Phase 3 clustering solution (K=3 stands) or the Phase 4 predictive model (treatment-
naive design preserved). The score is a candidate feature for a future treatment-aware
model variant only, not an input to the current pipeline.

### 9.2 Score Definition

**Treatment intensity score**: total antidiabetic drug days, computed as the sum of
per-prescription durations (`STOP − START`) across all recorded antidiabetic
prescriptions for each patient, aggregated by drug class (metformin, insulin,
other_antidiabetic) and then summed into a single `treatment_days_total` score.

Drug codes used (exact codes from Phase 2 notebook 01, for consistency):

| Code | Description | Drug class |
|---|---|---|
| 860975 | Metformin hydrochloride 500 MG ER | metformin |
| 106892 | Insulin isophane/regular 70/30 (Humulin) | insulin |
| 311034 | Insulin regular 100 UNT/ML | insulin |
| 865098 | Insulin Lispro 100 UNT/ML (Humalog) | insulin |
| 897122 | Liraglutide 6 MG/ML Pen Injector | other_antidiabetic |
| 1373463 | Canagliflozin 100 MG Oral Tablet | other_antidiabetic |

**Extraction**: chunked read of `medications.csv` (307 MB) with simultaneous filter on
`PATIENT` (cohort set, O(1) lookup) and `CODE`, same pattern established in Phase 2
for `observations.csv`.

**Open-ended prescriptions**: rows with `STOP = NaN` (ongoing at simulation end)
imputed with the latest `START` date in the extracted dataset as a proxy for the
Synthea simulation end date (2026-06-15). Conservative choice: does not inflate
duration beyond what is observed.

### 9.3 Management Modality: Pharmacological vs. Non-Pharmacological

569 of 1763 patients (32.3%) have `treatment_days_total = 0`, no antidiabetic
medication recorded. These patients are interpreted as managed through non-
pharmacological means (diet, lifestyle modification), a clinically valid first-line
strategy, not a missing-data artifact. Including them in a treatment intensity
analysis would conflate management modality with adherence.

**Decision**: patients with `treatment_days_total = 0` are characterized separately
and excluded from all intensity analyses. The analytical dataset is restricted to
1194 pharmacologically managed patients.

Pharmacological management rate by cluster:

| Cluster | Pharmacological (%) | n |
|---|---|---|
| Multimorbid, high care complexity | 98.6% | 361/366 |
| Dyslipidemic / metabolic | 97.9% | 92/94 |
| Mild, lower treatment intensity | 56.9% | 741/1303 |

The sharp difference in Mild (56.9% vs. ~98% in the other two clusters) is clinically
coherent: Mild patients have the lowest disease burden (CCI 1.77) and glycemic values
closest to target (HbA1c 6.09), making non-pharmacological management a plausible
and appropriate first-line choice for a large fraction of this subgroup.

### 9.4 Statistical Results (pharmacologically managed patients, n=1194)

Kruskal-Wallis: H=170.7, p=8.77e-38. Pairwise Mann-Whitney U (two-sided):

| Comparison | U | p-value | Effect size r | Interpretation |
|---|---|---|---|---|
| Mild vs Multimorbid | 68,643 | 2.21e-39 | 0.396 | Medium — meaningful separation |
| Mild vs Dyslipidemic | 32,579 | 4.89e-01 | 0.024 | Negligible — no practical difference |
| Dyslipidemic vs Multimorbid | 10,450 | 3.99e-08 | 0.258 | Small-medium |

**Key finding**: among pharmacologically managed patients, **Mild and Dyslipidemic are
statistically indistinguishable in treatment intensity** (p=0.49, r=0.024, medians
3708 vs 3751 days). The defining difference between these clusters is metabolic profile
(lipid panel), not treatment duration or persistence. The only clinically meaningful
separation is between Multimorbid and both other clusters (median 6729 days, nearly
double), consistent with higher disease burden and near-universal insulin use.

**Methodological note**: effect sizes are materially smaller than those estimated on
the full cohort including untreated patients (Mild vs Multimorbid r dropped from 0.505
to 0.396 after exclusion). A substantial part of the apparent separation in the full
dataset was driven by the 43% of Mild patients with zero treatment days, a management
modality difference, not a treatment intensity difference.

### 9.5 Limitations

- `treatment_days_total` conflates treatment duration with disease history length:
  patients diagnosed earlier accumulate more days regardless of adherence. Normalizing
  by time since diagnosis would be more precise but was not available as a clean
  variable in the Synthea output.
- One extreme outlier (~46,000 days, ~127 years) is almost certainly a Synthea
  data-generation artifact (open-ended prescription with an early START date). Retained
  in the dataset but noted as a known limitation; robust statistics (median, IQR,
  Mann-Whitney) are unaffected.
- The score was deliberately excluded from the Phase 4 predictive model (treatment-
  naive design). It remains a candidate feature for a future treatment-aware model
  variant if that design constraint is relaxed.