"""Constructed software tests, not additional benchmark cases or external events."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from audit_rules import evaluate_record, optimal_cost_and_count
from build_inputs import parse, optional_boolean, load_pinned, SOURCE_PATHS
from run_audit import validate_inventory, main

HERE = Path(__file__).resolve().parent
BUNDLE = parse((HERE / 'inputs/saved_evidence.json').read_text())
CASES = {x['case_id']: x for x in BUNDLE['records'] + BUNDLE['certificate_evidence_index'] + BUNDLE.get('current_software_examples', [])}


def case(name):
    return copy.deepcopy(CASES[name])


def status(x, claim):
    return evaluate_record(x)['decisions'][claim]['status']


class ConstructedSoftwareTests(unittest.TestCase):
    def test_current_wrong_authority_is_separate_from_historical_cohorts(self):
        self.assertEqual(len(BUNDLE['current_software_examples']), 1)
        self.assertEqual(sum(x['facts']['certificate_index']['records'] for x in BUNDLE['certificate_evidence_index']), 32946)
        y = evaluate_record(case('current_wrong_qualifier_authority'))
        self.assertEqual(y['decisions']['constructed_supplied_authority_acceptance']['status'], 'SUPPORTED')
        self.assertEqual(y['decisions']['constructed_original_agreement']['status'], 'CONTRADICTED')
        self.assertIn('independent business truth', y['unknown'])

    def test_missing_current_original_does_not_certify_intent(self):
        x = case('current_wrong_qualifier_authority'); del x['facts']['constructed_authority']['matches_constructed_original']
        self.assertEqual(status(x, 'constructed_original_agreement'), 'UNKNOWN')

    def test_complete_empirical_roster(self):
        self.assertEqual(len(BUNDLE['records']), 11)
        self.assertFalse(validate_inventory(BUNDLE))

    def test_dropped_case_and_self_reported_roster_still_rejected(self):
        x = copy.deepcopy(BUNDLE)
        x['records'] = [r for r in x['records'] if r['case_id'] != 'rayyan']
        x['expected_inventory']['consumer'].remove('rayyan')
        self.assertTrue(validate_inventory(x))

    def test_duplicate_case_rejected(self):
        x = copy.deepcopy(BUNDLE); x['records'].append(x['records'][0])
        self.assertTrue(validate_inventory(x))

    def test_missing_event_witness_not_redirected_to_certificate(self):
        x = case('employees-random-egtask'); del x['facts']['native']['independent_events_present']
        out = evaluate_record(x)
        self.assertEqual(out['decisions']['native_event_fidelity']['status'], 'UNKNOWN')
        self.assertEqual(out['decisions']['csv_all_optima_determinacy']['status'], 'SUPPORTED')
        self.assertNotIn('given_authority_exactness', out['decisions'])

    def test_foreign_family_proposition_unknown(self):
        x = case('employees-egtask'); x['requested_claims'] = ['given_authority_exactness']
        self.assertEqual(status(x, 'given_authority_exactness'), 'UNKNOWN')

    def test_native_inconsistent_summary_not_producer_defect(self):
        x = case('employees-random-egtask'); x['facts']['native']['events'] += 1
        self.assertEqual(status(x, 'native_event_fidelity'), 'UNKNOWN')

    def test_two_identical_row_optima_do_not_imply_semantic_ambiguity(self):
        x = case('employees-symmetrictest-egtask')
        y = evaluate_record(x)['decisions']['csv_all_optima_determinacy']
        self.assertEqual((y['status'], y['measurements']['optima']), ('SUPPORTED', 2))

    def test_constructed_semantic_ambiguity_is_unknown(self):
        x = case('synthetic_01-egtask'); x['requested_claims'] = ['csv_all_optima_determinacy']
        x['facts'].update(rows=2, columns=1, cells=2)
        x['facts']['matching'] = {'cost_matrix': [[1,1],[1,1]], 'saved_cost': 2, 'saved_optima': 2,
            'all_optima_enumerated': True, 'cell_support': [
                {'cell_index': i, 'label_options': [True], 'target_option_count': 2} for i in [1,2]]}
        self.assertEqual(status(x, 'csv_all_optima_determinacy'), 'UNKNOWN')

    def test_dp_against_exhaustive_small_constructed_matrices(self):
        for matrix in [[[0,0],[0,0]], [[0,1],[1,0]], [[2,1,0],[1,0,2],[0,2,1]], [[1,1,2],[2,1,1],[1,2,1]]]:
            vals = [sum(matrix[i][j] for i,j in enumerate(p)) for p in itertools.permutations(range(len(matrix)))]
            self.assertEqual(optimal_cost_and_count(matrix, 2), (min(vals), vals.count(min(vals))))

    def test_incomplete_optimum_enumeration_is_unknown(self):
        x = case('employees-egtask'); x['facts']['matching']['all_optima_enumerated'] = False
        self.assertEqual(status(x, 'csv_all_optima_determinacy'), 'UNKNOWN')

    def test_saved_optimum_tamper_is_unknown(self):
        x = case('employees-egtask'); x['facts']['matching']['saved_optima'] = 99
        self.assertEqual(status(x, 'csv_all_optima_determinacy'), 'UNKNOWN')

    def test_missing_or_duplicate_support_is_unknown(self):
        for mode in ['missing','duplicate']:
            x = case('employees-egtask'); s = x['facts']['matching']['cell_support']
            if mode == 'missing': s.pop()
            else: s[-1]['cell_index'] = s[0]['cell_index']
            self.assertEqual(status(x, 'csv_all_optima_determinacy'), 'UNKNOWN')

    def test_impossible_confusion_bounds_are_unknown(self):
        x = case('employees-random-egtask'); x['facts']['reveal_bounds']['tn'] = {'min':0,'max':0}
        self.assertEqual(status(x, 'csv_all_optima_native_agreement'), 'UNKNOWN')

    def test_documented_probe_nan_preserved(self):
        x = case('employees-random-egtask'); y = evaluate_record(x)['decisions']
        self.assertEqual(y['native_event_fidelity']['status'], 'SUPPORTED')
        self.assertEqual(y['documented_value_equivalence']['status'], 'CONTRADICTED')
        self.assertIsNone(y['documented_value_equivalence']['measurements']['documented_probe']['value']['f1'])
        self.assertEqual(y['documented_value_equivalence']['measurements']['documented_probe']['value']['native_f1_text'], 'NaN')

    def test_consumer_mixed_outcomes_remain_separate(self):
        y = evaluate_record(case('rayyan'))['decisions']
        self.assertEqual(y['native_probe_exactness']['status'], 'SUPPORTED')
        self.assertEqual(y['raw_direct_value_equivalence']['status'], 'CONTRADICTED')
        self.assertEqual(y['raw_direct_value_equivalence']['measurements']['raw_hits'], 942)

    def test_consumer_missing_score_unknown(self):
        x = case('rayyan'); del x['facts']['probes']['raw_direct_scores']
        self.assertEqual(status(x, 'raw_direct_value_equivalence'), 'UNKNOWN')

    def test_label_hash_count_conflict_unknown(self):
        x = case('rayyan'); x['facts']['labels']['raw_coordinates_sha256'] = '0' * 64
        self.assertEqual(status(x, 'raw_native_label_equivalence'), 'UNKNOWN')

    def test_empty_label_hashes_unknown(self):
        x = case('rayyan')
        x['facts']['labels']['raw_coordinates_sha256'] = x['facts']['labels']['native_coordinates_sha256'] = ''
        self.assertEqual(status(x, 'raw_native_label_equivalence'), 'UNKNOWN')

    def test_label_denominator_invalid_gates_both_probes(self):
        x = case('rayyan')
        for k in ['raw','native','common']: x['facts']['labels'][k] = x['facts']['cells'] + 1
        for claim in ['raw_native_label_equivalence','native_probe_exactness','raw_direct_value_equivalence']:
            self.assertEqual(status(x, claim), 'UNKNOWN')

    def test_zero_label_probe_not_perfect(self):
        x = case('toy')
        for k in ['raw','native','common']: x['facts']['labels'][k] = 0
        self.assertEqual(status(x, 'native_probe_exactness'), 'UNKNOWN')

    def test_roundtrip_digest_count_conflict_unknown(self):
        x = case('rayyan'); x['facts']['persistence']['dirty_digest_equal'] = False
        self.assertEqual(status(x, 'official_persistence'), 'UNKNOWN')

    def test_false_raw_score_not_reinterpreted_as_effect(self):
        x = case('rayyan'); x['facts']['probes']['raw_direct_scores'][3] = .5
        self.assertEqual(status(x, 'raw_direct_value_equivalence'), 'UNKNOWN')

    def test_valid_refusal_not_answered_repair(self):
        x = case('reference/refusal')
        y = evaluate_record(x)
        self.assertEqual(y['decisions']['saved_protocol_checks']['status'], 'SUPPORTED')
        self.assertEqual(y['decisions']['saved_protocol_checks']['measurements']['answered'], 0)
        self.assertNotIn('given_authority_exactness', y['decisions'])

    def test_missing_certificate_witness_unknown(self):
        for key in ['answered','checker_valid','resolved','certificate_present']:
            x = case('reference/valid'); del x['facts']['certificate_index'][key]
            self.assertEqual(status(x, 'saved_protocol_checks'), 'UNKNOWN')

    def test_unknown_certificate_cohort_unknown(self):
        x = case('reference/valid'); x['facts']['certificate_index']['cohort'] = 'unmeasured'
        self.assertEqual(status(x, 'saved_protocol_checks'), 'UNKNOWN')

    def test_refusal_conflicting_checker_counts_unknown(self):
        x = case('reference/refusal'); x['facts']['certificate_index']['checker_valid'] = 0
        self.assertEqual(status(x, 'saved_protocol_checks'), 'UNKNOWN')

    def test_missing_exactness_field_not_false(self):
        x = case('reference/valid'); x['facts']['certificate_index']['field_available']['patch_exact'] = 0
        self.assertEqual(status(x, 'given_authority_exactness'), 'UNKNOWN')

    def test_optional_boolean_type_strict(self):
        self.assertIsNone(optional_boolean({}, 'x'))
        for value in [None, 0, 1, 'true', [], {}]:
            with self.assertRaises(ValueError): optional_boolean({'x':value}, 'x')

    def test_null_or_missing_source_ref_unknown(self):
        for srcs in [[], [None], [{'path':'x','sha256':'g'*64}]]:
            x = case('employees-egtask'); x['source_refs'] = srcs
            self.assertEqual(status(x, 'native_event_fidelity'), 'UNKNOWN')

    def test_json_duplicate_keys_and_nan_rejected(self):
        for txt in ['{"x":1,"x":2}', '{"x":NaN}']:
            with self.assertRaises(ValueError): parse(txt)

    def test_source_hash_change_rejected(self):
        lock = parse((HERE / 'source_lock.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / SOURCE_PATHS[0]; p.parent.mkdir(parents=True); p.write_text('changed')
            with self.assertRaisesRegex(ValueError, 'source hash/size changed'): load_pinned(Path(tmp), lock)

    def test_input_hash_change_rejected_without_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input.json'; p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'hash mismatch'): main(p, Path(tmp)/'out', '0'*64)
            self.assertFalse((Path(tmp)/'out').exists())

    def test_unknown_matching_still_renders_complete_outputs(self):
        x = copy.deepcopy(BUNDLE); del x['records'][0]['facts']['matching']['cost_matrix']
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'input.json'; p.write_text(json.dumps(x))
            main(p, Path(tmp)/'out', hashlib.sha256(p.read_bytes()).hexdigest())
            y=parse((Path(tmp)/'out/case_ledger.json').read_text())
            self.assertEqual(y['cases'][0]['decisions']['csv_all_optima_determinacy']['status'],'UNKNOWN')
            self.assertIn('UNKNOWN', (Path(tmp)/'out/audit_decision_table.tex').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
