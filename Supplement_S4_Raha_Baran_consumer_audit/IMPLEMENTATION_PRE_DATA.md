# Implementation clarification before data acquisition

This specifies the frozen E3 endpoint and an E2/E3 route check before observing any paired CSV.

For each valid pair, let E0 be raw CSV inequality and E1 be unchanged native Dataset.get_actual_errors_dictionary() coordinates. Four dictionaries will be scored with the unchanged native get_data_cleaning_evaluation method: native coordinates/native clean values; native coordinates/raw clean values; raw coordinates/raw clean values; raw coordinates/native clean values. All dictionaries are full deterministic probes, not trained repair outputs.

For each of the first two fixed-coordinate dictionaries, additionally call unchanged create_repaired_dataset, then unchanged get_correction_dictionary, then unchanged get_data_cleaning_evaluation. Preserve the materialized dictionary count, coordinate hash, target-value hash and score. Expected equivalence of direct and materialized routes is a hypothesis, not an assumption: the constructor normalizes data, the materializer normalizes input correction values, and the dictionary scorer compares values directly. Any difference is described as interface-route sensitivity under those actual APIs. No source patch or additional normalization is added.

For E2 call official write_csv_dataset on the native dirty and clean DataFrames, then construct a second official Dataset from those exported files. Record dirty/clean cell-value changes, error-coordinate changes, and common-error target changes. Independent standard-library code computes exactly one and two applications of the source-described normalizer to untouched input values and compares every cell with native loaded and reloaded tables. No extra loop until convergence or changed stop rule is used.

For E4 construct official dirty/dirty and clean/clean self-pair Dataset objects and score empty dictionaries. Native normalized oracle should return six ones iff E1 is nonempty, otherwise six zeroes according to upstream convention. No new value corruption, arbitrary row permutation or synthetic production-defect claim is introduced. Native row alignment is positional; no authoritative key is supplied by the inspected generic evaluator.

Independent audit implementations use stdlib csv/html/re and independently expressed arithmetic; they do not import native Dataset or the native harness. This first cross-check is not presented as an external human review. Parent will assign separate independent review.
