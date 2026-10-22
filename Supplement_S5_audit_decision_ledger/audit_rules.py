"""Bounded contract decisions from saved, value-free audit measurements (stdlib only).

This is a result interpreter, not a generator, matcher for arbitrary tables, or
certificate verifier. Select propositions before choosing their evidence family.
Missing evidence never triggers another family or certifies business truth.
"""
import math
import re
from functools import lru_cache


class EvidenceError(ValueError):
    pass


def need(d, key, kind=None):
    if not isinstance(d, dict) or key not in d:
        raise EvidenceError('missing field: ' + key)
    v = d[key]
    if kind is not None and type(v) is not kind:
        raise EvidenceError('wrong type: ' + key)
    return v


def count(d, key, positive=False):
    v = need(d, key, int)
    if v < (1 if positive else 0):
        raise EvidenceError('invalid count: ' + key)
    return v


def require(condition, reason):
    if not condition:
        raise EvidenceError(reason)


def scores(v):
    require(type(v) is list and len(v) == 6, 'expected six native scores')
    require(all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1 for x in v), 'invalid score')
    return v


def result(status, reason, measurements=None):
    return {'status': status, 'reason': reason, 'measurements': measurements or {}}


def proposition(ok, reason, measurements=None):
    return result('SUPPORTED' if ok else 'CONTRADICTED', reason, measurements)


def optimal_cost_and_count(matrix, columns):
    """Recompute tiny saved numeric assignment instances; no original cells read."""
    n = len(matrix)
    require(0 < n <= 20, 'saved-matrix evaluator supports 1..20 rows only')
    require(all(type(row) is list and len(row) == n for row in matrix), 'cost matrix is not square')
    require(all(type(x) is int and 0 <= x <= columns for row in matrix for x in row), 'invalid Hamming cost')

    @lru_cache(None)
    def solve(mask):
        i = bin(mask).count('1')
        if i == n:
            return (0, 1)
        best, ways = None, 0
        for j in range(n):
            if not mask & (1 << j):
                tail, num = solve(mask | (1 << j))
                cost = matrix[i][j] + tail
                if best is None or cost < best:
                    best, ways = cost, num
                elif cost == best:
                    ways += num
        return best, ways
    return solve(0)


def dimensions(f):
    rows, cells, cols = count(f, 'rows', True), count(f, 'cells', True), count(f, 'columns', True)
    require(rows * cols == cells, 'inconsistent dimensions')
    return rows, cells, cols


def native(f):
    _, cells, _ = dimensions(f)
    n = need(f, 'native', dict)
    require(need(n, 'identity_crosswalk_valid', bool), 'native correspondence not established')
    require(need(n, 'independent_events_present', bool), 'independent native event witness unavailable')
    for k in ['events', 'changes', 'unexplained', 'unrealized', 'value_mismatches', 'noop_events']:
        count(n, k)
    require(n['noop_events'] <= n['events'] and n['changes'] <= cells, 'invalid native event/change denominator')
    require(n['unexplained'] <= n['changes'] and n['unrealized'] <= n['events'] - n['noop_events'], 'invalid native discrepancy counts')
    require(n['value_mismatches'] <= n['events'], 'invalid event-value mismatch count')
    require(n['changes'] - n['unexplained'] == n['events'] - n['noop_events'] - n['unrealized'], 'native summary accounting inconsistent; not a producer defect verdict')
    return n


def generator_native(f):
    dimensions(f)
    n = native(f)
    ok = all(n[k] == 0 for k in ['unexplained', 'unrealized', 'value_mismatches'])
    ok = ok and n['events'] - n['noop_events'] == n['changes']
    return proposition(ok, 'Native identity-aligned changes versus independently saved native events; this saved run only.', n)


def generator_position(f):
    _, cells, _ = dimensions(f)
    n = native(f)
    p = need(f, 'position', dict)
    vals = {k: count(p, k) for k in ['tp', 'fp', 'fn', 'tn', 'target_correct', 'apparent_changes']}
    require(sum(vals[k] for k in ['tp', 'fp', 'fn', 'tn']) == cells, 'position confusion counts do not cover cells')
    require(vals['tp'] + vals['fp'] == vals['apparent_changes'], 'position difference count mismatch')
    require(vals['tp'] + vals['fn'] == n['changes'], 'position reference count mismatch')
    require(vals['target_correct'] <= cells, 'invalid position target count')
    vals['zero_event_false_alarm'] = n['events'] == 0 and vals['fp'] > 0
    ok = vals['fp'] == vals['fn'] == 0 and vals['target_correct'] == cells
    return proposition(ok, 'Position pairing judged against native correspondence; apparent differences are not new injections.', vals)


def matching_evidence(f):
    rows, cells, cols = dimensions(f)
    m = need(f, 'matching', dict)
    require(need(m, 'all_optima_enumerated', bool), 'incomplete all-optima evidence')
    matrix = need(m, 'cost_matrix', list)
    require(len(matrix) == rows, 'matching row count mismatch')
    cost, ways = optimal_cost_and_count(matrix, cols)
    require(cost == count(m, 'saved_cost') and ways == count(m, 'saved_optima', True), 'saved optimum/count disagrees with matrix')
    support = need(m, 'cell_support', list)
    require(len(support) == cells, 'cell support does not cover every cell')
    require(sorted(count(x, 'cell_index', True) for x in support) == list(range(1, cells + 1)), 'duplicate/missing support cell')
    ambiguous = 0
    for x in support:
        options = need(x, 'label_options', list)
        require(options and all(type(v) is bool for v in options) and len(set(options)) == len(options), 'invalid label support')
        targets = count(x, 'target_option_count', True)
        ambiguous += int(len(options) != 1 or targets != 1)
    return {'cost': cost, 'optima': ways, 'cells': cells, 'ambiguous_cells': ambiguous}


def generator_determinacy(f):
    m = matching_evidence(f)
    if m['ambiguous_cells']:
        return result('UNKNOWN', 'Globally optimal assignments support different labels or targets; do not select a convenient optimum.', m)
    return result('SUPPORTED', 'All saved optimal assignments induce one semantic answer; identity uniqueness is not asserted.', m)


def generator_match_agreement(f):
    n, m = native(f), matching_evidence(f)
    require(m['ambiguous_cells'] == 0, 'semantic answer ambiguous across optima')
    b = need(f, 'reveal_bounds', dict)
    for key in ['label_correct', 'target_correct', 'tp', 'fp', 'fn', 'tn', 'repair_correct']:
        pair = need(b, key, dict)
        lo, hi = count(pair, 'min'), count(pair, 'max')
        require(lo <= hi <= m['cells'], 'invalid score bound: ' + key)
        require(lo == hi, 'semantically unique labels/targets require collapsed score bounds')
    v = {k: x['min'] for k, x in b.items()}
    require(v['tp'] + v['fp'] + v['fn'] + v['tn'] == m['cells'], 'reveal confusion counts do not cover cells')
    require(v['tp'] + v['tn'] == v['label_correct'], 'reveal label accuracy and confusion counts disagree')
    require(v['tp'] + v['fn'] == n['changes'], 'reveal change denominator disagrees with native witness')
    require(v['repair_correct'] <= v['tp'] and v['repair_correct'] <= v['target_correct'], 'invalid repair-value hit count')
    ok = b['label_correct']['min'] == b['target_correct']['min'] == m['cells']
    ok = ok and b['tp']['min'] == b['repair_correct']['min'] == n['changes'] and b['fp']['max'] == b['fn']['max'] == 0
    return proposition(ok, 'All-optima semantic agreement with revealed native witness; no claim of sidecar necessity.', dict(m, bounds=b))


def generator_documentation(f):
    n = native(f)
    if n['events'] == 0:
        return result('NOT_APPLICABLE', 'No emitted event on which to score a value-orientation probe; retained zero-event case.')
    d = need(f, 'documentation', dict)
    require(count(d, 'probe_cells', True) == n['events'], 'probe scope does not match events')
    require(count(d, 'implementation_mismatches') == 0, 'native exporter/scorer orientation not established')
    a, b = need(d, 'snapshot_probe', dict), need(d, 'documented_probe', dict)
    for v in [a, b]:
        for level in ['cell', 'value']:
            for metric in ['precision', 'recall']:
                z = need(need(v, level, dict), metric)
                require(type(z) in (int, float) and math.isfinite(z) and 0 <= z <= 1, 'invalid probe score')
    same = a['cell'] == b['cell'] and a['value'] == b['value'] and count(d, 'wiki_mismatches') == 0
    return proposition(same, 'Version-specific documented-field versus snapshot-value probe; native consistency is a separate endpoint.', d)


def consumer_label_evidence(f):
    _, cells, _ = dimensions(f)
    d = need(f, 'labels', dict)
    raw, norm = count(d, 'raw'), count(d, 'native')
    removed, added, common = count(d, 'removed'), count(d, 'added'), count(d, 'common')
    require(raw == removed + common and norm == added + common, 'label accounting inconsistent')
    require(raw <= cells and norm <= cells, 'labels exceed supplied cells')
    for k in ['raw_coordinates_sha256', 'native_coordinates_sha256']:
        require(re.fullmatch('[0-9a-f]{64}', need(d, k, str)) is not None, 'invalid label digest')
    hashes_equal = d['raw_coordinates_sha256'] == d['native_coordinates_sha256']
    require(hashes_equal == (removed == added == 0), 'label hashes and delta counts disagree; invalid evidence')
    return d, hashes_equal


def consumer_labels(f):
    d, hashes_equal = consumer_label_evidence(f)
    removed, added = d['removed'], d['added']
    return proposition(removed == added == 0 and hashes_equal, 'Raw and native-normalized label coordinates under the released positional interface.', d)


def consumer_roundtrip(f):
    consumer_label_evidence(f)
    d = need(f, 'persistence', dict)
    keys = ['dirty_nonidempotent', 'clean_nonidempotent', 'dirty_value_changes', 'clean_value_changes', 'removed_labels', 'added_labels', 'target_changes']
    vals = {k: count(d, k) for k in keys}
    eq = all(need(d, k, bool) for k in ['dirty_digest_equal', 'clean_digest_equal', 'labels_digest_equal', 'targets_digest_equal'])
    require((vals['dirty_value_changes'] == 0) == d['dirty_digest_equal'], 'dirty persistence hash/count inconsistency')
    require((vals['clean_value_changes'] == 0) == d['clean_digest_equal'], 'clean persistence hash/count inconsistency')
    require((vals['removed_labels'] == vals['added_labels'] == 0) == d['labels_digest_equal'], 'label persistence hash/count inconsistency')
    if d['labels_digest_equal']:
        require((vals['target_changes'] == 0) == d['targets_digest_equal'], 'target persistence hash/count inconsistency')
    return proposition(all(v == 0 for v in vals.values()) and eq, 'Observed-value idempotence plus official export/reload on this supplied pair only.', vals)


def consumer_native_probe(f):
    labels, _ = consumer_label_evidence(f)
    require(labels['native'] > 0, 'no nonempty probe denominator; empty-case scores cannot establish exactness')
    d = need(f, 'probes', dict)
    vals = {k: scores(need(d, k, list)) for k in ['normalized_direct_scores', 'normalized_materialized_scores', 'raw_materialized_scores']}
    return proposition(all(x == 1 for v in vals.values() for x in v), 'Normalized direct probe and both official materialized routes recover native labels/targets; these are not repair algorithms.', vals)


def consumer_raw_probe(f):
    labels, _ = consumer_label_evidence(f)
    d = need(f, 'probes', dict)
    n = count(labels, 'native', True)
    raw, norm = scores(need(d, 'raw_direct_scores', list)), scores(need(d, 'normalized_direct_scores', list))
    changed = count(d, 'raw_to_materialized_target_changes')
    require(changed <= n, 'target changes exceed label denominator')
    same_coords = need(d, 'raw_normalized_coordinates_equal', bool)
    require(same_coords, 'probe coordinates differ; cannot isolate a value-only adapter effect')
    require(raw[:3] == norm[:3] == [1, 1, 1], 'cell detection not held exact')
    expected = (n - changed) / n
    require(all(math.isclose(x, expected, abs_tol=1e-12) for x in raw[3:]), 'raw correction scores disagree with target-change count')
    return proposition(raw == norm and changed == 0, 'Fixed-coordinate raw versus normalized direct values; inequality does not establish a native bug or a ranking effect.', {'raw_hits': n - changed, 'native_labels': n, 'target_changes': changed, 'raw_scores': raw, 'normalized_scores': norm})


def consumer_selfpairs(f):
    d = need(f, 'selfpairs', dict)
    vals = {k: count(d, k) for k in ['dirty_labels', 'clean_labels']}
    return proposition(all(v == 0 for v in vals.values()), 'Saved clean/dirty self-pair controls; native empty-case scoring convention is retained separately.', d)


def reference_exact(f):
    d = need(f, 'certificate_index', dict)
    n = count(d, 'records', True)
    require(need(d, 'cohort', str) in ['valid', 'extended'], 'exactness endpoint only selected for resolved cohorts')
    vals = {k: count(d, k) for k in ['resolved', 'answered', 'checker_valid', 'patch_exact', 'rebuild_exact', 'same_edges']}
    availability = need(d, 'field_available', dict)
    require(all(count(availability, k) == n for k in ['patch_exact','rebuild_exact','same_edges']), 'saved exactness field absent; not a false result')
    require(all(v <= n for v in vals.values()), 'cohort counts exceed records')
    return proposition(all(v == n for v in vals.values()), 'Saved per-record checks support exactness relative to supplied complete-authority projection, not business truth.', dict(vals, records=n))


def reference_protocol(f):
    d = need(f, 'certificate_index', dict)
    n = count(d, 'records', True)
    require(count(d, 'unique_case_ids') == n, 'duplicate certificate case identifier')
    agree = count(d, 'expected_checker_agreement')
    require(agree <= n, 'invalid verifier agreement count')
    cohort = need(d, 'cohort', str)
    require(cohort in ['valid','extended','refusal','tamper','idempotence','gold_independence'], 'unsupported certificate cohort')
    vals = {k: count(d, k) for k in ['checker_valid','answered','resolved','certificate_present','expected_valid_true']}
    require(all(v <= n for v in vals.values()), 'protocol count exceeds cohort')
    if agree == n:
        require(vals['expected_valid_true'] == vals['checker_valid'], 'expectation-agreement summary inconsistent')
    ok = agree == n
    if cohort == 'refusal':
        require(count(need(d, 'field_available', dict), 'input_preserved') == n, 'missing preservation evidence')
        ok = ok and vals['checker_valid'] == vals['expected_valid_true'] == n and vals['resolved'] == vals['answered'] == vals['certificate_present'] == 0 and count(d, 'input_preserved') == n
    elif cohort == 'tamper':
        ok = ok and vals['checker_valid'] == vals['expected_valid_true'] == 0
    else:
        ok = ok and all(v == n for v in vals.values())
    return proposition(ok, 'Saved checker outcomes; a valid refusal is not an answered repair. Constructed software cases are not external incidents.', d)


def constructed_authority_check(f):
    x = need(f, 'constructed_authority', dict)
    valid, answered = need(x, 'verifier_valid', bool), need(x, 'answered', bool)
    status = need(x, 'protocol_status', str)
    require(need(x, 'certificate_schema', str) == 'REFERENCE_OCCURRENCE_CERTIFICATE_V3', 'not a current certificate')
    require(need(x, 'complete_assertion', bool), 'complete-authority condition not asserted')
    supplied_match = need(x, 'matches_supplied_projection', bool)
    return proposition(valid and answered and status == 'RESOLVED' and supplied_match, 'Current constructed software example: acceptance relative to supplied authority only.', x)


def constructed_intent_match(f):
    x = need(f, 'constructed_authority', dict)
    same = need(x, 'matches_constructed_original', bool)
    require(need(x, 'intent_basis', str) == 'author_constructed_original', 'no separately declared constructed intent')
    return proposition(same, 'Equality to the manually defined original in this one constructed example; no independent business gold.', x)


RULES = {
    'generator': {'native_event_fidelity': generator_native, 'position_semantic_equivalence': generator_position,
                  'csv_all_optima_determinacy': generator_determinacy, 'csv_all_optima_native_agreement': generator_match_agreement,
                  'documented_value_equivalence': generator_documentation},
    'consumer': {'raw_native_label_equivalence': consumer_labels, 'official_persistence': consumer_roundtrip,
                 'native_probe_exactness': consumer_native_probe, 'raw_direct_value_equivalence': consumer_raw_probe,
                 'selfpair_zero_labels': consumer_selfpairs},
    'reference_certificate': {'given_authority_exactness': reference_exact, 'saved_protocol_checks': reference_protocol,
                              'constructed_supplied_authority_acceptance': constructed_authority_check,
                              'constructed_original_agreement': constructed_intent_match}
}


def evaluate_record(record):
    family = record.get('family')
    decisions = {}
    for claim in record.get('requested_claims', []):
        try:
            require(family in RULES and claim in RULES[family], 'unsupported proposition for selected evidence family; no fallback')
            require(type(record.get('source_refs')) is list and bool(record['source_refs']), 'missing provenance references')
            for src in record['source_refs']:
                require(type(src) is dict, 'malformed source reference')
                require(type(src.get('path')) is str and type(src.get('sha256')) is str and re.fullmatch('[0-9a-f]{64}', src['sha256']) is not None, 'incomplete source identity')
            decisions[claim] = RULES[family][claim](need(record, 'facts', dict))
        except (EvidenceError, KeyError, TypeError, ValueError) as exc:
            decisions[claim] = result('UNKNOWN', str(exc))
    return {'case_id': record.get('case_id'), 'family': family, 'scope': record.get('scope'),
            'source_refs': record.get('source_refs', []), 'evidence_index': record.get('evidence_index', {}),
            'decisions': decisions,
            'unknown': ['independent business truth', 'population defect rate', 'effect on published algorithm rankings',
                        'generalization beyond the supplied snapshots and declared interface'] +
                       (['real-world authority completeness and authenticity', 'agreement with an independently intended business target'] if family == 'reference_certificate' else []),
            'branch_selection': 'proposition first; evidence families do not substitute for one another'}
