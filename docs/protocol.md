# Analysis Protocol — Patient Subtyping in a Type 2 Diabetes Cohort (Synthea)

## Status: Phase 0 complete — ready for Phase 1 (data generation)

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
be updated accordingly (documented deviation if needed).

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

---

## 3. Feature Engineering: Charlson Comorbidity Index (CCI)

Chosen over a simple comorbidity count, for consistency with a recognized standard in
epidemiological/RWE literature.

**Implementation note**: the CCI is traditionally defined using ICD-9/ICD-10 codes, while
Synthea uses SNOMED-CT codes in `conditions.csv`. In Phase 2, a SNOMED → Charlson category
mapping will need to be built, limited to the conditions actually present and relevant in the
generated dataset (a contained effort, not the full CCI schema).

---

## 4. Initial Clinical Hypotheses

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

## 5. Literature Reference for Validation

Ahlqvist et al., 2018, *Lancet Diabetes & Endocrinology* — identification of 5 adult-onset
diabetes subgroups (SAID, SIDD, SIRD, MOD, MARD) based on age, BMI, HbA1c, autoantibodies, and
insulin resistance/secretion indices. To be used as a conceptual reference for cluster
interpretation, with appropriate caution: the data used here are synthetic and do not include
all variables from the original study (e.g., autoantibodies, HOMA-B/HOMA-IR).

---

## 6. Next Steps (Phase 1)

1. Environment setup (Java + Synthea)
2. Generation of the synthetic population (~20,000 patients)
3. Initial exploration of the generated CSVs and verification of variable availability (see
   Section 2)
4. Cohort filtering according to inclusion criteria (Section 1)