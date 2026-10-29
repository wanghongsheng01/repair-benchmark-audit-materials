# Protocol S8: comparison-contract audit of a redistributed outlier-detection benchmark

Frozen on 29 October 2026, before any ARFF or NPZ data file was parsed. At freezing time only the
following had been inspected: the DAMI web page (dataset names, variant directory names, the published
instance/outlier/attribute table), the names of the files inside the two DAMI tarballs (`tar t`), the
ADBench `Classical` directory listing, and the dataset table in the ADBench README (sample, feature and
anomaly counts). No data values, labels or native evaluation results had been read.

## Question
The audit procedure of the paper is applied to a second domain, unsupervised outlier detection. The
producer is the DAMI repository that accompanies Campos et al. (2016, DMKD 30(4):891-927); it ships every
dataset in several pre-processing variants (with/without duplicates, normalized/not normalized,
downsampled versions v01-v10, categorical handling) together with native ELKI evaluation results per
variant. The consumer is the ADBench `Classical` redistribution (Han et al., NeurIPS 2022 Datasets and
Benchmarks), which ships one `.npz` file per dataset name with arrays `X` and `y`.

The question is consumer compatibility and record correspondence: when an evaluation reads a dataset by
name from the redistribution, which producer variant does it actually read, under which value
interpretation, and how much does that choice move a detector score? This is a contract check. It does
not evaluate or rank outlier detectors, and no published ranking is re-evaluated.

## Pinned inputs
- DAMI: `https://www.dbs.ifi.lmu.de/research/outlier-evaluation/input/literature.tar.gz` and
  `.../input/semantic.tar.gz` (server Last-Modified 13 Nov 2015); SHA-256 recorded at analysis time.
  Native results: `<name>_<variant>.evaluation.csv.gz` files linked from each dataset page, downloaded only
  for the variants named in endpoint E3.
- ADBench: commit `3dac8221081e190f157d78e93bfa8867f90d0965`, files
  `adbench/datasets/Classical/<id>_<name>.npz`; SHA-256 recorded.

## Scope (fixed now)
All dataset names present in both inventories, matched case-insensitively (PenDigits = pendigits):
ALOI, Glass, Ionosphere, Lymphography, PenDigits, Shuttle, Waveform, WBC, WDBC, WPBC, Annthyroid,
Cardiotocography, Hepatitis, InternetAds, PageBlocks, Pima, SpamBase, Stamps, Wilt (19 names).
Every DAMI ARFF file of each name is a candidate variant. No name is excluded after looking at data.
KDDCup99, Arrhythmia, HeartDisease and Parkinson are absent from ADBench `Classical` and are out of scope.

## Value interpretation
- DAMI: numeric attributes in file order, excluding the attribute named `id` and the label attribute
  `outlier`; label `yes` = outlier (documented on the DAMI page). If a file deviates (non-numeric
  attribute, other label values), it is recorded and the variant is reported as unparsed, not repaired.
- ADBench: `X` as float64, `y` with 1 = anomaly (README). `allow_pickle=False`.
- V0: exact equality of float64 values.
- V1: equality after rounding every value to 6 decimal places.
- V2: per-column min-max normalization of the DAMI variant (constant columns map to 0), then rounding to 6
  decimals, compared with ADBench rounded to 6 decimals. V2 is applied only to non-normalized variants.

## Correspondence
Row-multiset equality of feature vectors (duplicates counted), followed by multiset equality of
(feature vector, label). Column order is taken as given. If V0-V2 all fail for every variant of a name,
the provenance with respect to DAMI is *undetermined*; as a diagnostic only, the report lists the DAMI
variant(s) with equal row count and equal dimensionality and the fraction of ADBench rows found in each
under V1. No match is claimed from a diagnostic.

## Endpoints
- E1 inventory: n, d, outlier count of every candidate variant and of every ADBench file; agreement of the
  DAMI files with the counts in the DAMI web table (native witness) and of the ADBench files with the
  counts in its README.
- E2 correspondence: for each name, the set of DAMI variants matching under V0, V1 or V2, and label
  agreement under that match. Outcomes: *matched* (variant list, interpretation), *features matched but
  labels differ*, or *undetermined*.
- E3 native control: an independent NumPy implementation of the ELKI detectors KNN (distance to the k-th
  nearest neighbor) and KNNW (sum of the distances to the k nearest neighbors), Euclidean distance, with
  ROC AUC computed with tied scores counted one half. For each name, the native DAMI ROC AUC of KNN and
  KNNW at k in {1, 5, 10, 20, 50} is compared with the implementation on (a) the DAMI variant listed by the
  DAMI web table counts and (b) every DAMI variant matched in E2. Both neighbor conventions (query point
  excluded; query point counted as its own first neighbor) are computed, and the one that reproduces the
  native results is reported together with the maximum absolute difference. Datasets with more than 20,000
  rows are evaluated at the same k values in chunks; none is subsampled.
- E4 score sensitivity: for each name, ROC AUC of KNN and KNNW at the primary k = 10 (other k secondary)
  on the ADBench file and on every DAMI variant of that name; the difference between the ADBench file and
  the DAMI web-table variant, and the range over all variants. Ordering of KNN versus KNNW per name under
  each file. No significance test is applied, because the variants of one name are not independent samples.

## Attribution rules
- Exact match to the DAMI web-table variant: no discrepancy attributable to correspondence.
- Match to another DAMI variant: a difference from the web-table variant is attributed to variant
  correspondence (duplicates, normalization or downsampling), not to the detector or the producer.
- Match only under V1 or V2: attributed to value interpretation.
- Undetermined: no producer or consumer defect is claimed; same-named files are simply not the same
  dataset with respect to DAMI.
- A difference between the implementation and native ELKI results on a matched variant is attributed to the
  implementation (adapter) unless one neighbor convention reproduces the native results.

## Exclusions and amendments
Any amendment after data are parsed is appended below with a timestamp and reason; failed runs are kept.

### Amendment A1 (29 October 2026, after E1/E2 and a first E3 check on Glass)
Observation: on Glass, native KNNW at k is reproduced exactly by the query-excluded convention, but native
KNN at k is reproduced by neither frozen convention; it is reproduced exactly by the distance to the
(k+1)-th nearest neighbor with the query point excluded. The native results were produced by ELKI 0.7.0
`ComputeKNNOutlierScores` with `-startk 1 -stepk 1 -maxk 100` (DAMI package `scripts/runAlgorithms.sh`);
the jar was not executed. Amendment: the implementation stores the query-excluded KNN series for
k = 1..51 and KNNW for k = 1..50, and E3 reports, for every variant with a native file, the maximum
absolute difference under (i) the two frozen conventions and (ii) the observed shift (KNN native k vs
excluded k+1). E3 is extended from the frozen variant set to every variant with a native file; the
frozen subset is reported separately. The shift is an exploratory observation from one dataset that is
then tested on all others. E4 is unchanged and uses the query-excluded convention at k = 10, with the
shifted KNN series reported as a secondary analysis.

### Amendment A2 (same time)
Several DAMI variants of one name carry the web-table counts (for example the ten downsampled versions
v01-v10). E3(a) and E4 therefore use all variants with the table counts; none is chosen by its data.

### Amendment A3 (29 October 2026, after E4 was computed)
Observation: the ADBench loader at the pinned commit (`adbench/datasets/data_generator.py`, read as text,
not executed) splits each dataset 70/30 with stratification, subsamples datasets with more than 10,000
rows to 10,000, and by default min-max scales features with a scaler fitted on the training split. The
native ADBench consumer therefore does not read the stored feature scale directly. Additional analysis
E5, outside the frozen endpoints: KNN and KNNW (query excluded, k = 10) after per-column min-max scaling
of the whole file, for the ADBench file and every DAMI variant. E5 isolates the part of the E4 differences
that a min-max consumer removes (normalization) from the part it keeps (duplicates, downsampling version,
source). It does not reproduce ADBench's split, subsampling or semi-supervised settings, and it is not a
replication of any published ADBench score.

### Amendment A4 (29 October 2026, after E4)
Additional analysis E6, outside the frozen endpoints: consequences for method rankings, computed only from
the native DAMI evaluation files (no re-implementation). For every name with native results for the
ADBench-matched variant and for at least one other variant of the same name, the twelve native methods
(KNN, KNNW, LOF, SimplifiedLOF, LoOP, LDOF, ODIN, FastABOD, KDEOS, LDF, INFLO, COF; those absent on a
file are dropped for both files of a comparison) are ranked by ROC AUC at k = 10. Reported per pair of
variants: Kendall's tau-b between the two rankings, whether the top-ranked method is the same, and the
number of method pairs whose order reverses. A NumPy LOF re-implementation was tried first and did not
reproduce the native LOF values (maximum absolute difference 0.04-0.08 on two variants); it is kept in
`code/lof.py` and is not used for any reported number.

### Amendment A5 (29 October 2026, after two independent internal reviews of the draft)
Reviewers noted that most E6 comparisons pair one random outlier downsample with another, that the
top-1 endpoint has no tolerance, and that one measure and one k were used. Additional analysis E6b,
outside the frozen endpoints, replaces E6 in the paper: (i) every comparison of the ADBench-matched
variant with another DAMI variant of the same name is classed as *replicate* (same preparation and
outlier percentage, different downsampled version), *preparation* (same sample, different duplicate
handling, normalization or categorical coding) or *other*; (ii) a replicate noise floor is computed from
all pairs of downsampled versions within one preparation; (iii) a change of the best detector is
*material* only if, in at least one of the two files, the other file's best detector scores more than
0.01 below that file's best; (iv) three native measures: ROC AUC at k = 10, Average Precision at k = 10,
and ROC AUC averaged over all k; (v) counts are reported per comparison and averaged per name. Ties of
the best score are broken by detector name and cannot be material. Diagnostic E3b tests whether the
non-exact native values of E3 coincide with tied detector scores. Planted-cause validation E7: known
perturbations (row permutation, label inversion, min-max rescaling, duplicated row, substituted
variant, KNN parameter off by one) are applied to the matched files, and the procedure's attribution is
compared with the planted cause. Native per-object scores (`results.csv.gz`) of one variant (Glass) were
downloaded to locate the KNN offset at score level.

### Amendment A6 (29 October 2026, after a second internal review)
Corrections and clarifications, no new endpoint: (i) the k-averaged measure of E6b averages ROC AUC over
k = 1..50, not over all k, because small datasets lack larger k; detectors without all 50 values (FastABOD,
LDOF, KDEOS start at k = 2 or 3) are dropped, leaving nine detectors for that measure; (ii) the planted
"KNN parameter off by one" case of A5 is not run separately, because E3 already tests every variant
against the native values under both readings of k; (iii) one-sided binomial tests of the preparation
rate against the replicate floor are reported (`code/headline_revision.py`); (iv) the sources that
ADBench cites per dataset are extracted by `code/e9_adbench_sources.py` from the saved arXiv HTML, and
the Glass per-object check of A5 is scripted in `code/e3c_glass_per_object.py`.
