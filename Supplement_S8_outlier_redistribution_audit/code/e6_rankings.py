"""Additional analysis E6 (amendment A4): ranking consequences from native DAMI results only."""
import csv
import gzip
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import NAMES, ROOT

EVAL_DIR = os.path.join(ROOT, "raw", "dami_eval")
K = 10


def native_methods(variant):
    path = os.path.join(EVAL_DIR, variant + ".evaluation.csv.gz")
    if not os.path.exists(path):
        return None
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    except (OSError, EOFError):
        return None
    out = {r["Algorithm"]: float(r["ROC AUC"]) for r in rows if int(r["k"]) == K and r["ROC AUC"] not in ("", "NaN")}
    return out or None


def kendall_tau_b(a, b):
    conc = disc = ta = tb = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        da, db = a[i] - a[j], b[i] - b[j]
        if da == 0 and db == 0:
            continue
        if da == 0:
            ta += 1
        elif db == 0:
            tb += 1
        elif (da > 0) == (db > 0):
            conc += 1
        else:
            disc += 1
    denom = ((conc + disc + ta) * (conc + disc + tb)) ** 0.5
    return (conc - disc) / denom if denom else float("nan"), disc


def main():
    e12 = json.load(open(os.path.join(ROOT, "results", "e1_e2.json")))
    out = {}
    for name in NAMES:
        d = e12["datasets"][name]
        if not d["matches"]:
            continue
        mv = d["matches"][0]["variant"]
        base = native_methods(mv)
        if not base:
            out[name] = {"matched_variant": mv, "native_available": False}
            continue
        table = [v["variant"] for v in d["variants"] if v.get("matches_dami_table")]
        comps = []
        for v in [x["variant"] for x in d["variants"] if x.get("parsed")]:
            if v == mv:
                continue
            other = native_methods(v)
            if not other:
                continue
            common = sorted(set(base) & set(other))
            a, b = [base[m] for m in common], [other[m] for m in common]
            tau, flips = kendall_tau_b(a, b)
            comps.append({"variant": v, "is_table_variant": v in table, "methods": len(common), "tau_b": tau,
                          "reversed_pairs": flips,
                          "top_same": max(common, key=lambda m: base[m]) == max(common, key=lambda m: other[m]),
                          "top_matched": max(common, key=lambda m: base[m]),
                          "top_other": max(common, key=lambda m: other[m])})
        out[name] = {"matched_variant": mv, "native_available": True, "comparisons": comps}
        t = [c for c in comps if c["is_table_variant"]]
        print(name, mv, "comparisons", len(comps), "table", len(t),
              "min tau %.3f" % min([c["tau_b"] for c in comps]) if comps else "",
              "top differs in %d" % sum(not c["top_same"] for c in comps))
    with open(os.path.join(ROOT, "results", "e6_rankings.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
