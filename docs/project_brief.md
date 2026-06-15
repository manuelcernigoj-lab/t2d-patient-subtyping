# Project Brief — Patient Subtyping with Synthetic EHR Data (Synthea)
### Flagship project for the RWE Data Science portfolio

---

## 1. Project Objective

Build an end-to-end analysis that, starting from synthetic EHR data generated with Synthea,
identifies **patient subtypes** within a population affected by a chronic condition (proposed:
**type 2 diabetes**), based on demographic variables, comorbidities, treatment patterns, and
laboratory indicators.

The goal is not purely technical (applying clustering algorithms), but to **demonstrate clinical
interpretation of the results** — this is where a biotechnology background makes the difference
compared to a purely technical junior profile.

**Final output**: a public notebook/repository plus a short report (or Power BI dashboard)
presenting the identified clusters, characterizing them clinically, and — where possible —
comparing them against existing scientific literature on diabetes subtypes.

---

## 2. Required Resources and Where to Find Them

### 2.1 Data generator: Synthea

- **Repository**: [github.com/synthetichealth/synthea](https://github.com/synthetichealth/synthea)
- **Requirement**: Java JDK 11+ (e.g., Eclipse Temurin, installable via `winget` on Windows or
  from [adoptium.net](https://adoptium.net))
- **Execution** (from a terminal, in the project folder, with `synthea-with-dependencies.jar`):
  ```bash
  java -jar synthea-with-dependencies.jar -p 20000 --exporter.csv.export=true --exporter.fhir.export=false --exporter.baseDirectory=./data Massachusetts
  ```
  - `-p 20000` = total number of patients generated (sized to obtain ~1,500-2,000 diabetic
    patients, given an ~8-10% prevalence)
  - `--exporter.csv.export=true` enables CSV export (used with pandas)
  - `--exporter.fhir.export=false` disables the (default) FHIR/JSON export, which is not needed
    and significantly increases runtime and disk usage
  - The US state (e.g., `Massachusetts`) only affects providers/geography, not clinical content

- **Relevant CSV tables** (full data dictionary in the
  [Synthea wiki](https://github.com/synthetichealth/synthea/wiki/Basic-Setup-and-Running)):
  - `patients.csv` → demographics (age, sex, race, etc.)
  - `conditions.csv` → diagnoses (used to identify the diabetic cohort and comorbidities)
  - `medications.csv` → drug treatments
  - `observations.csv` → lab values (HbA1c, glucose, BMI, blood pressure, lipids...)
  - `encounters.csv` → visit frequency/type

### 2.2 Reference literature (for clinical validation — a key differentiator)

- **Ahlqvist et al., 2018, Lancet Diabetes & Endocrinology** — a study identifying 5 clusters in
  adult-onset diabetes (SAID, SIDD, SIRD, MOD, MARD) based on age, BMI, HbA1c, presence of
  autoantibodies, and insulin resistance/secretion indices. Access to the full paper is not
  required: abstracts/summaries available via PubMed or Google Scholar are sufficient as
  reference criteria to compare against the project's own clusters.
- This comparison should be framed carefully (Synthea data is synthetic, not real), but it is
  exactly the kind of "critical reading of results" that distinguishes a junior-level analysis
  from a mid-level one.

### 2.3 Technical stack (already available)

- Python: `pandas`, `numpy`, `scikit-learn` (KMeans, AgglomerativeClustering, validation
  metrics), `scipy` (statistical tests), `seaborn`/`matplotlib` (with the project color palette),
  optionally `umap-learn` for visualization
- Optional: Power BI for the final cluster presentation dashboard

---

## 3. Timeline (based on 5-6 working hours per day)

Total estimate: **~3 working weeks (15 days)**, split into 5 phases.

### Phase 0 — Setup and protocol specification (Day 1, ~4-5h)

Before writing any code, define a short protocol document covering:

- Target condition: type 2 diabetes (SNOMED-CT code in `conditions.csv`)
- Cohort inclusion criteria (e.g., adult patients with at least N lab observations)
- Candidate variables for clustering (demographics, comorbidities, treatment, labs)
- Clinical hypotheses to test (e.g., "expecting a cluster of younger patients with dominant
  insulin resistance vs. a cluster of older patients with multiple comorbidities")

### Phase 1 — Environment setup and data generation (Days 2-3, ~10-12h)

- Java + Synthea installation, population generation (20,000 patients)
- Initial exploration of the CSV files: structure, size, identification of patients diagnosed
  with type 2 diabetes
- Quality/consistency checks on the synthetic data (plausible values, missing data, duplicates)

### Phase 2 — ETL pipeline and feature engineering (Days 4-7, ~20-24h)

- Join `patients`, `conditions`, `medications`, `observations`, and `encounters` to build a
  **patient-level table** (one row per patient, one column per feature)
- Features to build:
  - Demographics: age, sex, ethnicity
  - Comorbidities: composite indicator (e.g., Charlson Comorbidity Index) for chronic conditions
    associated with diabetes (hypertension, dyslipidemia, obesity, chronic kidney disease...)
  - Treatment: drug classes taken (e.g., metformin, insulin, SGLT2 inhibitors)
  - Laboratory: latest value and/or trend for HbA1c, glucose, BMI, lipids
  - Healthcare utilization: number of encounters/year
- Data cleaning: missing data handling, outliers, categorical encoding, scaling

### Phase 3 — Clustering and EDA (Days 8-11, ~20-24h)

- Preliminary EDA: distributions, correlations, evident patterns
- Determining the number of clusters: elbow method + silhouette score (avoid fixing K a priori
  without justification — a signal of superficial analysis)
- Running and comparing at least 2 algorithms (e.g., K-means vs. agglomerative clustering) to
  demonstrate robustness
- Dimensionality reduction for visualization (PCA and/or UMAP)
- Cluster profiling: descriptive statistics for each group

### Phase 4 — Clinical interpretation and statistical validation (Days 12-13, ~10-12h)

- Statistical tests (ANOVA, chi-square) to confirm that clusters differ significantly on key
  variables
- Clinical characterization of each cluster (e.g., "Cluster 2: patients with marked insulin
  resistance and cardiovascular comorbidities")
- Discursive (non-statistical) comparison with subtypes described in the literature (Ahlqvist et
  al.), highlighting similarities and limitations (synthetic data, limited sample)

### Phase 5 — Reporting, dashboard, and portfolio packaging (Days 14-15, ~10-12h)

- Final cleanup of the notebook (comments, structure, narrative)
- Final visualizations using the defined color palette, following Gestalt principles and
  optimizing the data-ink ratio
- Optional summary Power BI dashboard (cluster profiles, distributions)
- Repository README: context, methodology, limitations, possible extensions

---

## 4. Key Considerations

- **The dataset is synthetic**: state this clearly in the report. This is not a weakness to
  hide, but an opportunity to demonstrate methodological awareness (e.g., "the clusters
  identified here are illustrative of the methodology; on real data they would need to be
  validated against longitudinal data and clinical outcomes").

- **Do not fix K a priori**: always justify the chosen number of clusters using metrics (elbow,
  silhouette) — one of the clearest signals distinguishing a junior analysis from a more mature
  one.

- **Clinical narrative is the real added value**: each cluster should have a "name" and a
  clinically plausible description, not just "Cluster 0, 1, 2". This is where a biotechnology
  background matters more than purely statistical skills.

- **Feature engineering > algorithm**: clustering quality depends much more on the chosen
  variables (e.g., deriving a composite comorbidity indicator) than on the algorithm itself.
  Dedicate real time to Phase 2.

- **Style consistency**: apply the defined color palette from the start and keep code minimal,
  indented, and well-commented — easier to do during development than during final review.

- **Do not over-engineer**: 20,000 generated patients (yielding ~1,500-2,000 diabetic patients)
  and a well-chosen set of features are sufficient. The goal is a complete, well-narrated
  project, not a massive dataset.

- **Connection with project 4.3 (Pharmacovigilance/OpenFDA)**: once this project is complete,
  evaluate whether some feature engineering work (e.g., comorbidity handling, drug class
  grouping) can be reused, maintaining stylistic consistency across portfolio projects.

---

## 5. Final Deliverables

1. GitHub repository with well-documented notebook(s) and a clear folder structure
   (`data/`, `notebooks/`, `src/`, `docs/`)
2. Report/section with clinical interpretation of the clusters (in markdown or as a final
   notebook section)
3. (Optional) Summary Power BI dashboard
4. README including: objective, dataset, methodology, key results, limitations, and possible
   future developments
