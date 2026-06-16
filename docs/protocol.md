# Analysis Protocol — Patient Subtyping in a Type 2 Diabetes Cohort (Synthea)

## Status: Phase 2 complete (ETL and feature engineering) — ready for Phase 3 (clustering)

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
  patients emerges (e.g., <30 years), a decision will be made — with documented justification —
  to either:
  - include them in the main analysis,
  - treat them as a separate subgroup with dedicated commentary,
  - or exclude them with explicit reasoning.

  This decision will be made **based on the actual data**, during Phase 2/3, and documented as
  a deviation from the initial protocol.

  **Outcome (Phase 2)**: the age distribution was reviewed (range 19-110, median 63, mean 64.6).
  Only 7 out of 1,763 patients (0.4%) are below age 30 — too small a subgroup to analyze
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
Phase 2 based on actual availability — see Section 4.*

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
therefore be biased — that subgroup is enriched for patients with a clinical reason to be
tested.

**Decision**: missingness is encoded explicitly via a binary indicator (`creatinine_measured`),
preserving the "was this patient tested?" signal as a separate feature. The missing values
themselves are imputed with a fixed clinical reference value (0.9 mg/dL, approximate midpoint of
the normal adult range), rather than a sample-derived statistic.

**Quantitative validation**: the median creatinine value among the 840 patients for whom it
*was* measured is 2.1 mg/dL — well above the normal range upper limit (~1.3 mg/dL) and more than
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
clustering — a feature that is almost entirely zero contributes no useful variance. This
preserves the "on a more recent/specialist therapy" signal without introducing near-constant
columns. This is a deviation from the original wishlist (Section 2), which listed sulfonylureas
and SGLT2 inhibitors as separate candidate variables.

Resulting features: `on_metformin`, `on_insulin`, `on_other_antidiabetic`. 516 patients (29% of
the cohort) are on none of the three — plausibly patients managed by diet/lifestyle alone, or
with borderline glycemic control not yet requiring pharmacological treatment.

### Healthcare utilization

Built as `encounters_per_year`: total encounters divided by each patient's observation window
(time between first and last recorded encounter), to make patients with different
follow-up lengths comparable.

**Distribution note**: the resulting variable is right-skewed (median 1.31, mean 2.42, max
20.64) — a small subgroup of patients has much higher utilization than the majority, plausibly
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
  plus other agents) — a clinically high-priority group due to complication risk.

**Note**: H3 and H4 may overlap in practice. Clustering will help clarify whether these represent
distinct groups or a single phenotype with dual characteristics.

---

## 6. Literature Reference for Validation

Ahlqvist et al., 2018, *Lancet Diabetes & Endocrinology* — identification of 5 adult-onset
diabetes subgroups (SAID, SIDD, SIRD, MOD, MARD) based on age, BMI, HbA1c, autoantibodies, and
insulin resistance/secretion indices. To be used as a conceptual reference for cluster
interpretation, with appropriate caution: the data used here are synthetic and do not include
all variables from the original study (e.g., autoantibodies, HOMA-B/HOMA-IR).

---

## 7. Next Steps (Phase 3)

1. Exploratory data analysis on the full `patient_features` table (distributions, correlations)
2. Address the right-skewed `encounters_per_year` variable (Section 4) before scaling
3. Feature scaling and encoding of categorical variables
4. Determine the number of clusters (elbow method, silhouette score) — no fixed K a priori
5. Run and compare at least two clustering algorithms (e.g., K-means, agglomerative)
6. Dimensionality reduction for visualization (PCA and/or UMAP)