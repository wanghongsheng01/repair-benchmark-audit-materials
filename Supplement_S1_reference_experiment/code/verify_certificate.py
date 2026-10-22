"""Independent protocol current checker; no repairer import, call, or supplied E.

This module separately parses D/R, establishes the selected-fragment protocol
preconditions, and derives E before checking snapshots and occurrence arithmetic.
It checks internal consistency with asserted authority, not provenance or truth.
Only the Python standard library is used; this is the sole delivered checker.
"""
from __future__ import annotations
import hashlib
import json
import math


class Rejected(Exception):
    pass


def _require(condition, reason):
    if not condition:
        raise Rejected(reason)


def _identifier(value):
    return isinstance(value, str) and len(value) > 0 and ":" not in value and not any(map(str.isspace, value))


def _json_value(value):
    if isinstance(value, dict):
        return all(type(k) is str and _json_value(v) for k, v in value.items())
    if isinstance(value, list):
        return all(_json_value(v) for v in value)
    return type(value) in (str, bool, int, type(None)) or (type(value) is float and math.isfinite(value))


def _edge_list(value):
    if not isinstance(value, list):
        return False
    for item in value:
        if not isinstance(item, dict) or set(item) != {"role", "target", "qualifiers"}:
            return False
        if not _identifier(item["role"]) or not isinstance(item["target"], str) or not item["target"]:
            return False
        if not isinstance(item["qualifiers"], dict) or not _json_value(item["qualifiers"]):
            return False
    return True


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)


def _sha(value):
    return hashlib.sha256(_encoded(value).encode("utf-8")).hexdigest()


def _sorted(value):
    return sorted(value, key=_encoded)


def _bag(values):
    bag = {}
    for item in values:
        key = _encoded(item)
        bag[key] = bag.get(key, 0) + 1
    return bag


def _same(left, right):
    """Structural equality is type-sensitive (False must not equal zero)."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def _derive(task):
    """Checker-owned parser, intentionally independent of repair implementation."""
    _require(isinstance(task, dict) and _edge_list(task.get("current_edges")), "MALFORMED_TASK")
    declaration, registry = task.get("contract"), task.get("registry")
    _require(isinstance(declaration, dict) and declaration.get("complete") is True, "INCOMPLETE_AUTHORITY")
    _require(_json_value(declaration) and _json_value(registry), "MALFORMED_AUTHORITY")
    try:
        metric = declaration["metric"]
        _require(isinstance(metric, dict) and _identifier(metric.get("name")) and _identifier(task.get("metric_id")), "MALFORMED_AUTHORITY")
        _require(metric["name"] == task["metric_id"], "METRIC_IDENTITY_MISMATCH")
        _require(isinstance(registry, dict) and isinstance(registry["metrics"], list) and isinstance(registry["measures"], dict), "MALFORMED_AUTHORITY")
        names = registry["metrics"]
        _require(all(_identifier(x) for x in names), "MALFORMED_AUTHORITY")
        _require(len(names) == len(set(names)), "DUPLICATE_REGISTRY_IDENTITY")
        for reference_name, identities in registry["measures"].items():
            _require(_identifier(reference_name) and isinstance(identities, list), "MALFORMED_AUTHORITY")
            for identity in identities:
                _require(isinstance(identity, str) and identity.startswith("measure:"), "INVALID_TYPED_TARGET")
                tail = "." + reference_name
                body = identity[len("measure:"):]
                _require(body.endswith(tail) and _identifier(body[:-len(tail)]), "INVALID_TYPED_TARGET")
            _require(len(identities) == len(set(identities)), "DUPLICATE_REGISTRY_IDENTITY")
        _require(isinstance(metric["type"], str), "MALFORMED_AUTHORITY")
        kind = metric["type"].lower()
        layout = {"simple": (("measure_of", "measure", False),),
                  "cumulative": (("measure_of", "measure", False),),
                  "ratio": (("numerator_of", "numerator", True), ("denominator_of", "denominator", True)),
                  "conversion": (("base_measure_of", "base_measure", False), ("conversion_measure_of", "conversion_measure", False))}
        _require(kind in layout or kind == "derived", "UNSUPPORTED")
        parameters = metric["type_params"]
        _require(isinstance(parameters, dict), "MALFORMED_AUTHORITY")
        if kind == "derived":
            _require(isinstance(parameters["metrics"], list), "MALFORMED_AUTHORITY")
            requests = [("depends_on", item, True) for item in parameters["metrics"]]
        else:
            if kind == "conversion":
                parameters = parameters["conversion_type_params"]
                _require(isinstance(parameters, dict), "MALFORMED_AUTHORITY")
            requests = [(role, parameters[field], metric_target) for role, field, metric_target in layout[kind]]
        derived = []
        for role, reference, metric_target in requests:
            _require(isinstance(reference, (dict, str)), "MALFORMED_AUTHORITY")
            target_name = reference["name"] if isinstance(reference, dict) else reference
            _require(_identifier(target_name), "MALFORMED_AUTHORITY")
            if metric_target:
                candidates = ["metric:" + entry for entry in names if entry == target_name]
            else:
                candidates = registry["measures"].get(target_name, [])
            _require(len(candidates) == 1, "NONUNIQUE_BINDING")
            qualifiers = dict(reference) if isinstance(reference, dict) else {}
            qualifiers.pop("name", None)
            derived.append(dict(role=role, target=candidates[0], qualifiers=qualifiers))
        return _sorted(derived)
    except (KeyError, TypeError, AttributeError):
        raise Rejected("MALFORMED_AUTHORITY") from None


def check(task, prediction):
    """Return explicit verdict and protocol status for success or refusal."""
    expected, status = None, "RESOLVED"
    try:
        expected = _derive(task)
    except Rejected as error:
        status = str(error)
    try:
        _require(isinstance(prediction, dict), "MALFORMED_PREDICTION")
        if expected is None:
            original = task.get("current_edges") if isinstance(task, dict) else None
            _require(prediction.get("answered") is False and prediction.get("reason") == status,
                     "REFUSAL_STATUS_MISMATCH")
            _require("certificate" in prediction and prediction["certificate"] is None,
                     "REFUSAL_MUST_NOT_CERTIFY")
            _require("edges" in prediction and _same(prediction["edges"], original), "REFUSAL_CHANGED_INPUT")
        else:
            _require(prediction.get("answered") is True and prediction.get("reason") == "RESOLVED", "SUCCESS_STATUS_MISMATCH")
            certificate = prediction.get("certificate")
            keys = {"schema", "metric", "authority_digest", "observed_adjacency_digest", "rule", "removed", "added", "preserved"}
            _require(isinstance(certificate, dict) and set(certificate) == keys, "MALFORMED_CERTIFICATE")
            _require(certificate["schema"] == "REFERENCE_OCCURRENCE_CERTIFICATE_V3", "SCHEMA_MISMATCH")
            _require(certificate["rule"] == "UNIQUE_COMPLETE_DECLARATION_BINDING_MULTISET_DELTA", "RULE_MISMATCH")
            _require(certificate["metric"] == task["metric_id"], "CERTIFICATE_IDENTITY_MISMATCH")
            _require(certificate["authority_digest"] == _sha({"contract": task["contract"], "registry": task["registry"]}), "AUTHORITY_SNAPSHOT_MISMATCH")
            _require(certificate["observed_adjacency_digest"] == _sha(_sorted(task["current_edges"])), "OBSERVATION_SNAPSHOT_MISMATCH")
            _require(_edge_list(prediction.get("edges")) and all(_edge_list(certificate[k]) for k in ("removed", "added", "preserved")), "MALFORMED_OCCURRENCE_LIST")
            current, target = _bag(task["current_edges"]), _bag(expected)
            required = {"removed": {}, "added": {}, "preserved": {}}
            for edge in current.keys() | target.keys():
                before, after = current.get(edge, 0), target.get(edge, 0)
                for label, count in (("removed", max(before - after, 0)), ("added", max(after - before, 0)), ("preserved", min(before, after))):
                    if count:
                        required[label][edge] = count
            _require(all(_bag(certificate[key]) == value for key, value in required.items()), "OCCURRENCE_DELTA_MISMATCH")
            _require(_bag(prediction["edges"]) == target, "OUTPUT_PROJECTION_MISMATCH")
        return {"valid": True, "protocol_status": status, "failure": None}
    except (Rejected, KeyError, TypeError, ValueError) as error:
        return {"valid": False, "protocol_status": status, "failure": str(error)}


def verify(task, prediction):
    """Boolean entry point for the same sole protocol checker."""
    return check(task, prediction)["valid"]
