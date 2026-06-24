# Patient Subtyping in Type 2 Diabetes — RWE Data Science Portfolio Project

**Author**: Manuel  
**Status**: Phases 0–4 complete + exploratory extension (notebook 05)  
**Language**: English (code, documentation, reports) | Italian (working conversations)

---

## Project Overview

This project demonstrates end-to-end Real World Evidence (RWE) data science capabilities: from raw synthetic clinical data to actionable patient stratification, with honest reporting of methodological choices and limitations.

**Central question**: Can routine baseline clinical variables predict distinct Type 2 diabetes patient subtypes at or near diagnosis?

**Answer**: Yes. Three clinically coherent subtypes emerge from unsupervised clustering; a treatment-naive predictive model achieves 92% recall on the highest-risk subtype using only baseline labs and demographics.

---

## Why this project

The pharmaceutical and healthcare industries increasingly rely on RWE data science for:
- Patient segmentation to improve trial design and targeting
- Early risk stratification for personalized care pathways
- Precision medicine — understanding which patients respond to which treatments

This project mirrors that workflow: ETL on large clinical datasets → unsupervised profiling → supervised early prediction. The synthetic data avoids privacy barriers while preserving analytical rigor.

---

## Repository Structure

```
t2d-patient-subtyping/
├── README.md                          (this file)
├── .gitignore                         (data/, .venv/, __pycache__)
├── docs/
│   ├── protocol.md                    (living methodology document, Phases 0–4 + extension)
│   ├── project_brief.md               (Phase 0 scope)
│   └── report_figures/                (output images for non-technical report)
├── data/
│   ├── csv/                           (Synthea raw output, git-ignored)
│   └── processed/                     (derived parquet/CSV, git-ignored)
│       ├── patient_features.parquet
│       ├── patient_features_clustered.parquet
│       └── patient_features_dashboard.csv
├── notebooks/
│   ├── 01_data_exploration.ipynb      (Phase 1–2: ETL, feature engineering)
│   ├── 02_clustering.ipynb            (Phase 3: K=3 clustering, profiling)
│   ├── 03_cluster0_metformin_gradient.ipynb  (Phase 3 supplement: gradient analysis)
│   ├── 04_predictive_modeling.ipynb   (Phase 4: supervised classification)
│   └── 05_treatment_adherence.ipynb   (Exploratory: treatment intensity score)
├── src/
│   └── plot_style.py                  (shared color palette, rcParams, registered colormaps)
├── requirements.txt                   (Python dependencies)
└── .venv/                             (virtual environment, git-ignored)
```

---

## Quick Start

### 1. Environment Setup

```bash
# Clone or navigate to the repo directory
cd t2d-patient-subtyping

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Data

Download Synthea (one-time):
```bash
wget https://github.com/synthetichealth/synthea/releases/download/master/synthea-with-dependencies.jar
```

Generate 20,000 synthetic patients:
```bash
java -jar synthea-with-dependencies.jar -p 20000 \
  --exporter.csv.export=true \
  --exporter.fhir.export=false \
  --exporter.baseDirectory=./data \
  Massachusetts
```

### 3. Run Analysis

Open Jupyter and run notebooks in order:
```bash
jupyter notebook
```

- **Notebook 01**: ETL, cohort definition (1,763 T2D patients), feature engineering → exports `patient_features.parquet`
- **Notebook 02**: K-means + hierarchical clustering, K=3 selection, cluster profiling → exports `patient_features_clustered.parquet`
- **Notebook 03**: Exploratory investigation of metformin gradient within Cluster 0
- **Notebook 04**: Predictive model (logistic regression vs. Random Forest vs. HistGradientBoosting), final holdout test evaluation
- **Notebook 05**: Treatment intensity score (continuous medication duration), comparison across clusters

---

## Key Findings

### Phase 3 — Three Patient Subtypes

| Cluster | n (%) | Label | Profile |
|---|---|---|---|
| 0 | 1,303 (73.9%) | Mild, lower treatment intensity | HbA1c 6.09, CCI 1.77, ~50% on metformin |
| 1 | 94 (5.3%) | Dyslipidemic / metabolic | Triglycerides 375.9, HDL 29.9 (lowest), 98% metformin |
| 2 | 366 (20.8%) | Multimorbid, high care complexity | Age 72.7 (oldest), CCI 4.34, 91% insulin |

**Clustering input**: 10 continuous features (age, labs, comorbidity, utilization), scaled with `RobustScaler`. Categorical/medication features excluded from clustering (used for post-hoc profiling and equity checks only).

**Validation**: silhouette score, elbow method, dendrogram structure, Adjusted Rand Index between K-means and agglomerative clustering — all four diagnostics converged on K=3.

### Phase 4 — Predictive Model

**Design**: treatment-naive baseline (9 features available at first visit). CCI and healthcare utilization deliberately excluded to test genuine early stratification.

**Final model**: logistic regression, selected on clinical criterion (maximize Multimorbid recall = 0.92) rather than aggregate macro-F1.

**Holdout test performance** (n=353, never seen during training):
- Dyslipidemic: 100% recall, 95% F1
- Mild: 84% recall, 90% F1
- Multimorbid: **92% recall** (clinical priority), 74% F1

### Phase 5 (Extension) — Treatment Intensity

Among 1,194 pharmacologically managed patients (43% of Mild have no antidiabetic meds):
- **Mild and Dyslipidemic are statistically indistinguishable** in cumulative medication duration (p=0.49, effect size r=0.024)
- **Multimorbid accumulates nearly double** the treatment days (median 6,729 vs. ~3,700, r=0.396)

This confirms the management modality split (pharmacological vs. non-pharmacological) is a real clinical distinction, especially within the Mild subtype.

---

## Methodological Highlights

### Data Quality & Feature Engineering

- **Creatinine missingness** (52.4%): imputed with clinical reference value (0.9 mg/dL) + binary flag `creatinine_measured`, preserving the "was this patient tested?" signal. Median of measured subgroup (2.1 mg/dL) confirmed selection bias.
- **Charlson Comorbidity Index (CCI)**: built from SNOMED codes actually present in the data, not theoretical schema. Mutual exclusivity enforced within disease groups.
- **LDL cholesterol**: originally planned LOINC returned zero data; replaced with direct assay code after targeted investigation.
- **Encounters per year**: log-transformed before scaling to handle right-skew without losing outlier information.

### Cluster Validation

Four independent diagnostics on Phase 3:
1. **Silhouette score**: 0.58 (k=3), compared to k=2 and k=4
2. **Elbow method**: gap in inertia reduction after k=3
3. **Dendrogram**: clear 3-cluster structure
4. **ARI (K-means vs. agglomerative)**: 0.95 agreement between algorithms

### Cross-Validation Strategy (Phase 4)

- **Outer split**: stratified 80/20 train/test, holdout test evaluated once at the end
- **Inner validation**: stratified 5-fold CV on training set for model selection
- **Scaling**: `RobustScaler` wrapped inside `Pipeline` with the model to prevent fold-to-fold leakage
- **Class weight**: `balanced` to counteract 73.9% / 20.8% / 5.3% imbalance

---

## Known Limitations

1. **Synthetic data**: Synthea generates clinically realistic records but with known artifacts in HbA1c and BMI (near-categorical discretization from discrete clinical states). Documented and flagged; does not invalidate methodology but limits direct clinical translation.

2. **Treatment intensity score**: conflates treatment duration with disease history length. Normalization by time-since-diagnosis would be more precise but was not available cleanly in the Synthea output.

3. **Treatment-naive predictive model**: deliberately excludes the most discriminative variables (CCI, healthcare utilization) by design, yielding moderate (not excellent) performance. This is honest reporting, not a limitation to engineer around — the feature restriction is the whole point of the "early stratification" use case.

---

## Skills Demonstrated

- **Data engineering**: chunked ETL on large files (>300 MB), memory-efficient processing, documented data quality decisions
- **Statistical analysis**: unsupervised learning with rigorous model selection, non-parametric testing with effect sizes, equity checks
- **Machine learning**: multiclass classification, class imbalance handling, cross-validation design, model selection on clinical criteria
- **Interpretability**: feature importance tied to clinical hypotheses, honest limitation reporting
- **Reproducibility**: full Git history with conventional commits, synthetic data regenerable, protocol as living document

---

## How to Cite or Extend

This project is a **portfolio demonstration**, not a clinical research paper. Synthetic data is not suitable for peer-reviewed publication without original research framing.

To extend:
1. Swap Synthea data for real EHR data (adjust privacy/compliance steps)
2. Validate cluster labels against published diabetes classification systems (e.g., Ahlqvist et al., *Lancet Diabetes & Endocrinology*, 2018)
3. Test the treatment-naive model on prospective cohorts
4. Build a treatment-aware variant using medication history as a feature

---

## Contact & Questions

For questions about methodology, code, or the analytical approach, refer to:
- `docs/protocol.md` — full methodology
- Individual notebooks — code comments and markdown explanations
- This README — quick reference

---

**Last updated**: June 2026  
**Git status**: All phases committed with conventional commits. Ready for review or extension.