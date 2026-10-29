"""Planted-cause validation E7 (amendment A5): apply perturbations with a known responsible step to the
matched files and check that the frozen correspondence rules attribute each one correctly."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import NAMES, ROOT, dami_files, minmax, multiset_equal, read_arff, round6


def attribute(Xa, ya, name):
    """Frozen E2 rules applied to a consumer file: returns (outcome, variant, interpretation)."""
    Xa6 = round6(Xa)
    for path in dami_files(name):
        v = os.path.basename(path)[:-5]
        try:
            Xd, yd, _ = read_arff(path)
        except ValueError:
            continue
        if Xd.shape != Xa.shape:
            continue
        tests = [("V0", Xd, Xa), ("V1", round6(Xd), Xa6)]
        if "_norm" not in v:
            tests.append(("V2", round6(minmax(Xd)), round6(minmax(Xa))))
        for interp, A, B in tests:
            if multiset_equal(A, B):
                lab = multiset_equal(A, B, yd, ya)
                return ("matched" if lab else "labels differ"), v, interp
    return "undetermined", None, None


def attribute_all(Xa, ya, name):
    """Variant rule: collect every matching variant and prefer the least-transformed interpretation."""
    Xa6 = round6(Xa)
    found = []
    for path in dami_files(name):
        v = os.path.basename(path)[:-5]
        try:
            Xd, yd, _ = read_arff(path)
        except ValueError:
            continue
        if Xd.shape != Xa.shape:
            continue
        tests = [("V0", Xd, Xa), ("V1", round6(Xd), Xa6)]
        if "_norm" not in v:
            tests.append(("V2", round6(minmax(Xd)), round6(minmax(Xa))))
        for interp, A, B in tests:
            if multiset_equal(A, B):
                found.append((interp, ("matched" if multiset_equal(A, B, yd, ya) else "labels differ"), v))
                break
    if not found:
        return "undetermined", None, None, 0
    found.sort()
    return found[0][1], found[0][2], found[0][0], len(found)


def main():
    rng = np.random.default_rng(20261029)
    e12 = json.load(open(os.path.join(ROOT, "results", "e1_e2.json")))
    cases = []
    for name in NAMES:
        d = e12["datasets"][name]
        if not d["matches"]:
            continue
        mv = d["matches"][0]["variant"]
        X, y, _ = read_arff([p for p in dami_files(name) if p.endswith("/" + mv + ".arff")][0])
        raw = "_norm" not in mv
        perm = rng.permutation(len(y))
        others = [x["variant"] for x in d["variants"] if x.get("parsed") and x["variant"] != mv
                  and (x.get("d") == X.shape[1])]
        planted = [
            ("row permutation", "comparison: none (correspondence-invariant)", X[perm], y[perm],
             ("matched", mv, "V0")),
            ("label inversion", "adapter: label orientation", X, 1 - y, ("labels differ", mv, "V0")),
            ("permutation and label inversion", "adapter: label orientation", X[perm], 1 - y[perm],
             ("labels differ", mv, "V0")),
            ("duplicated row", "comparison: no producer variant", np.vstack([X, X[:1]]), np.append(y, y[0]),
             ("undetermined", None, None)),
            ("rounding to 6 decimals plus 1e-9 noise", "adapter: numeric representation",
             X + 1e-9 * rng.standard_normal(X.shape), y, ("matched", mv, "V1")),
        ]
        if raw:
            s = rng.uniform(0.5, 5.0, X.shape[1])
            t = rng.uniform(-3.0, 3.0, X.shape[1])
            planted.append(("affine rescaling of every attribute", "adapter: feature scaling", X * s + t, y,
                            ("matched", mv, "V2")))
        if others:
            ov = others[int(rng.integers(len(others)))]
            Xo, yo, _ = read_arff([p for p in dami_files(name) if p.endswith("/" + ov + ".arff")][0])
            planted.append(("substituted variant " + ov, "comparison: other producer variant", Xo, yo,
                            ("matched", ov, None)))
        for label, cause, Xp, yp, expected in planted:
            got = attribute(Xp, yp, name)
            ok = got[0] == expected[0] and (expected[1] is None or got[1] == expected[1]) and \
                (expected[2] is None or got[2] == expected[2])
            g2 = attribute_all(Xp, yp, name)
            ok2 = g2[0] == expected[0] and (expected[1] is None or g2[1] == expected[1]) and \
                (expected[2] is None or g2[2] == expected[2])
            # a substituted variant may legitimately equal another file (identical variants); accept equal data
            cases.append({"name": name, "perturbation": label, "planted_cause": cause,
                          "expected": list(expected), "obtained": list(got), "correct": bool(ok),
                          "obtained_all_matches_rule": list(g2), "correct_all_matches_rule": bool(ok2)})
    summary = {"cases": len(cases), "correct": sum(c["correct"] for c in cases),
               "correct_all_matches_rule": sum(c["correct_all_matches_rule"] for c in cases),
               "undetermined_when_wrong": sum((not c["correct"]) and c["obtained"][0] == "undetermined" for c in cases),
               "by_perturbation": {}}
    for c in cases:
        key = c["perturbation"].split(" ")[0] if c["perturbation"].startswith("substituted") else c["perturbation"]
        b = summary["by_perturbation"].setdefault(key, [0, 0])
        b[0] += c["correct"]; b[1] += 1
    json.dump({"summary": summary, "cases": cases}, open(os.path.join(ROOT, "results", "e7_planted.json"), "w"),
              indent=1)
    print(json.dumps(summary, indent=1))
    for c in cases:
        if not c["correct"]:
            print("MISS", c["name"], c["perturbation"], c["expected"], c["obtained"], "| all-matches:",
                  c["obtained_all_matches_rule"], c["correct_all_matches_rule"])


if __name__ == "__main__":
    main()
