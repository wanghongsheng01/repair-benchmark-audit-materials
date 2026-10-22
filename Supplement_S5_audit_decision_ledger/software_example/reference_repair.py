"""Typed occurrence repair, protocol current; Python standard library only.

Completeness is an explicit caller assertion, never a claim of business truth.
The authority schema deliberately covers the selected reference fragment only.
Duplicate registry identities are rejected as schema violations (they are not
evidence of two distinct semantic candidates). Refusal preserves the input.
"""
from __future__ import annotations
import collections
import copy
import hashlib
import json


SCHEMA = "REFERENCE_OCCURRENCE_CERTIFICATE_V3"
RULE = "UNIQUE_COMPLETE_DECLARATION_BINDING_MULTISET_DELTA"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def ordered(edges):
    return sorted(edges, key=canonical)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _name(value):
    return isinstance(value, str) and bool(value) and not any(x.isspace() or x == ":" for x in value)


def _json(value):
    if value is None or type(value) in (bool, int, str):
        return True
    if type(value) is float:
        return value == value and abs(value) != float("inf")
    if isinstance(value, list):
        return all(_json(x) for x in value)
    return isinstance(value, dict) and all(isinstance(k, str) and _json(v) for k, v in value.items())


def _edges(value):
    return isinstance(value, list) and all(
        isinstance(e, dict) and set(e) == {"role", "target", "qualifiers"}
        and _name(e["role"]) and isinstance(e["target"], str) and bool(e["target"])
        and isinstance(e["qualifiers"], dict) and _json(e["qualifiers"])
        for e in value)


def resolve_contract(contract, registry, metric_id):
    """Return the selected adjacency or a closed, structured refusal reason."""
    if not isinstance(contract, dict) or contract.get("complete") is not True:
        return None, "INCOMPLETE_AUTHORITY"
    if not _json(contract) or not _json(registry):
        return None, "MALFORMED_AUTHORITY"
    try:
        metric = contract["metric"]
        if not isinstance(metric, dict) or not _name(metric.get("name")) or not _name(metric_id):
            return None, "MALFORMED_AUTHORITY"
        if metric["name"] != metric_id:
            return None, "METRIC_IDENTITY_MISMATCH"
        if not isinstance(registry, dict) or not isinstance(registry["metrics"], list) or not isinstance(registry["measures"], dict):
            return None, "MALFORMED_AUTHORITY"
        metrics, measures = registry["metrics"], registry["measures"]
        if any(not _name(n) for n in metrics):
            return None, "MALFORMED_AUTHORITY"
        if len(metrics) != len(set(metrics)):
            return None, "DUPLICATE_REGISTRY_IDENTITY"
        for name, candidates in measures.items():
            if not _name(name) or not isinstance(candidates, list):
                return None, "MALFORMED_AUTHORITY"
            if any(not isinstance(t, str) or not t.startswith("measure:") or
                   not t[8:].endswith("." + name) or not _name(t[8:-(len(name) + 1)])
                   for t in candidates):
                return None, "INVALID_TYPED_TARGET"
            if len(candidates) != len(set(candidates)):
                return None, "DUPLICATE_REGISTRY_IDENTITY"
        if not isinstance(metric["type"], str):
            return None, "MALFORMED_AUTHORITY"
        kind = metric["type"].lower()
        if kind not in ("simple", "cumulative", "ratio", "derived", "conversion"):
            return None, "UNSUPPORTED"
        params = metric["type_params"]
        if not isinstance(params, dict):
            return None, "MALFORMED_AUTHORITY"
        if kind in ("simple", "cumulative"):
            refs = [("measure_of", params["measure"], False)]
        elif kind == "ratio":
            refs = [(key + "_of", params[key], True) for key in ("numerator", "denominator")]
        elif kind == "derived":
            if not isinstance(params["metrics"], list):
                return None, "MALFORMED_AUTHORITY"
            refs = [("depends_on", ref, True) for ref in params["metrics"]]
        else:
            conversion = params["conversion_type_params"]
            if not isinstance(conversion, dict):
                return None, "MALFORMED_AUTHORITY"
            refs = [(key + "_of", conversion[key], False) for key in ("base_measure", "conversion_measure")]
        edges = []
        for role, ref, is_metric in refs:
            if not isinstance(ref, (str, dict)):
                return None, "MALFORMED_AUTHORITY"
            name = ref if isinstance(ref, str) else ref["name"]
            if not _name(name):
                return None, "MALFORMED_AUTHORITY"
            candidates = (["metric:" + name] if name in metrics else []) if is_metric else measures.get(name, [])
            if len(candidates) != 1:
                return None, "NONUNIQUE_BINDING"
            qualifiers = {} if isinstance(ref, str) else {key: value for key, value in ref.items() if key != "name"}
            edges.append({"role": role, "target": candidates[0], "qualifiers": qualifiers})
        return ordered(edges), "RESOLVED"
    except (KeyError, TypeError, AttributeError):
        return None, "MALFORMED_AUTHORITY"


def _resolve_task(task):
    if not isinstance(task, dict) or not _edges(task.get("current_edges")):
        return None, "MALFORMED_TASK"
    return resolve_contract(task.get("contract"), task.get("registry"), task.get("metric_id"))


def _refuse(task, reason):
    return {"edges": copy.deepcopy(task.get("current_edges") if isinstance(task, dict) else None),
            "answered": False, "reason": reason, "certificate": None}


def patch(task):
    expected, status = _resolve_task(task)
    if expected is None:
        return _refuse(task, status)
    current = collections.Counter(canonical(edge) for edge in task["current_edges"])
    target = collections.Counter(canonical(edge) for edge in expected)
    expand = lambda counter: ordered([json.loads(key) for key, count in counter.items() for _ in range(count)])
    removed, added, preserved = expand(current - target), expand(target - current), expand(current & target)
    certificate = {"schema": SCHEMA, "metric": task["metric_id"],
                   "authority_digest": digest({"contract": task["contract"], "registry": task["registry"]}),
                   "observed_adjacency_digest": digest(ordered(task["current_edges"])), "rule": RULE,
                   "removed": removed, "added": added, "preserved": preserved}
    return {"edges": ordered(preserved + added), "answered": True, "reason": status, "certificate": certificate}


def rebuild(task):
    expected, status = _resolve_task(task)
    return ({"edges": expected, "answered": True, "reason": status} if expected is not None
            else _refuse(task, status))
