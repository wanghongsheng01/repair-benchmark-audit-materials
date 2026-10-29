"""Additional analysis E6b (amendment A5): ranking consequences with a replicate noise floor,
a tolerance, three measures and per-name aggregation. Native DAMI results only."""
import csv
import gzip
import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e6_rankings import kendall_tau_b
from s8_lib import NAMES, ROOT

EVAL_DIR = os.path.join(ROOT, "raw", "dami_eval")
EPS = 0.01
MEASURES = ("ROC AUC k=10", "Average Precision k=10", "ROC AUC mean over k=1..50")


def parse(name, v):
    s = v[len(name):]
    return {"dedup": "withoutdupl" in s, "norm": "_norm" in s,
            "coding": next((c for c in ("idf", "catremoved", "1ofn") if c in s), ""),
            "pct": (re.search(r"_(\d\d)(?:_v\d\d)?$", s) or [None, ""])[1] if not re.search(r"_v\d\d$", s)
            or re.search(r"_(\d\d)_v\d\d$", s) else "",
            "version": (re.search(r"_v(\d\d)$", s) or [None, ""])[1]}


def scores(variant):
    path = os.path.join(EVAL_DIR, variant + ".evaluation.csv.gz")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {m: {} for m in MEASURES}
    sums = {}
    for r in rows:
        a, k = r["Algorithm"], int(r["k"])
        try:
            auc, ap = float(r["ROC AUC"]), float(r["Average Precision"])
        except ValueError:
            continue
        if k == 10:
            out["ROC AUC k=10"][a] = auc
            out["Average Precision k=10"][a] = ap
        if k <= 50:
            sums.setdefault(a, {})[k] = auc
    out["ROC AUC mean over k=1..50"] = {a: sum(v.values()) / len(v) for a, v in sums.items() if len(v) == 50}
    return out


def compare(sa, sb):
    common = sorted(set(sa) & set(sb))
    if len(common) < 2:
        return None
    a, b = [sa[m] for m in common], [sb[m] for m in common]
    tau, rev = kendall_tau_b(a, b)
    ta, tb = max(common, key=lambda m: (sa[m], m)), max(common, key=lambda m: (sb[m], m))
    # material: the other file's winner is more than EPS below the best in at least one file
    material = (sb[tb] - sb[ta] > EPS) or (sa[ta] - sa[tb] > EPS)
    return {"methods": len(common), "tau_b": tau, "reversed_pairs": rev, "top_a": ta, "top_b": tb,
            "top_differs": ta != tb, "material_change": material}


def classify(pa, pb):
    same_prep = (pa["dedup"], pa["norm"], pa["coding"]) == (pb["dedup"], pb["norm"], pb["coding"])
    same_sample = (pa["pct"], pa["version"]) == (pb["pct"], pb["version"])
    if same_prep and pa["pct"] == pb["pct"] and pa["version"] != pb["version"]:
        return "replicate"
    if same_sample and not same_prep:
        return "preparation"
    return "other"


def main():
    e12 = json.load(open(os.path.join(ROOT, "results", "e1_e2.json")))
    res = {"eps": EPS, "names": {}}
    for name in NAMES:
        d = e12["datasets"][name]
        variants = [x["variant"] for x in d["variants"] if x.get("parsed")
                    and os.path.exists(os.path.join(EVAL_DIR, x["variant"] + ".evaluation.csv.gz"))]
        sc = {v: scores(v) for v in variants}
        meta = {v: parse(name, v) for v in variants}
        rec = {"matched": d["matches"][0]["variant"] if d["matches"] else None, "vs_matched": [], "floor": []}
        if rec["matched"] in sc:
            mv = rec["matched"]
            for v in variants:
                if v == mv:
                    continue
                cls = classify(meta[mv], meta[v])
                rec["vs_matched"].append({"variant": v, "class": cls,
                                          **{m: compare(sc[mv][m], sc[v][m]) for m in MEASURES}})
        # replicate noise floor: all pairs of versions within one preparation and outlier percentage
        groups = {}
        for v in variants:
            p = meta[v]
            if p["version"]:
                groups.setdefault((p["dedup"], p["norm"], p["coding"], p["pct"]), []).append(v)
        for g in groups.values():
            for a, b in itertools.combinations(sorted(g), 2):
                rec["floor"].append({m: compare(sc[a][m], sc[b][m]) for m in MEASURES})
        res["names"][name] = rec

    def summarize(items, m):
        if not items:
            return None
        items = [x for x in items if x[m] is not None]
        t = sorted(x[m]["tau_b"] for x in items)
        n = len(t)
        med = t[n // 2] if n % 2 else (t[n // 2 - 1] + t[n // 2]) / 2
        return {"n": n, "top_differs": sum(x[m]["top_differs"] for x in items),
                "material": sum(x[m]["material_change"] for x in items), "tau_median": med}

    summ = {}
    for m in MEASURES:
        s = {}
        for cls in ("preparation", "replicate", "other"):
            items = [c for r in res["names"].values() for c in r["vs_matched"] if c["class"] == cls]
            s[cls] = summarize(items, m)
            per = []
            for r in res["names"].values():
                cs = [c for c in r["vs_matched"] if c["class"] == cls and c[m] is not None]
                if cs:
                    per.append(sum(c[m]["material_change"] for c in cs) / len(cs))
            if s[cls]:
                s[cls]["names"] = len(per)
                s[cls]["name_averaged_material_share"] = sum(per) / len(per)
                s[cls]["names_with_any_material"] = sum(p > 0 for p in per)
        s["floor_all_version_pairs"] = summarize([c for r in res["names"].values() for c in r["floor"]
                                                  if c[m] is not None], m)
        summ[m] = s
    res["summary"] = summ
    json.dump(res, open(os.path.join(ROOT, "results", "e6b_rankings_robust.json"), "w"), indent=1)
    print(json.dumps(summ, indent=1))
    for n, r in res["names"].items():
        prep = [c for c in r["vs_matched"] if c["class"] == "preparation"]
        if prep:
            print(n, r["matched"], [(c["variant"], c["ROC AUC k=10"]["material_change"],
                                     round(c["ROC AUC k=10"]["tau_b"], 2)) for c in prep if c["ROC AUC k=10"]])


if __name__ == "__main__":
    main()
