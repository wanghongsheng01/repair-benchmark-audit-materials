"""Diagnostic for E3 residuals: are non-exact native values associated with tied detector scores?"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e3_e4_scores import KS, native_auc
from s8_lib import NAMES, ROOT, dami_files, knn_distances, read_arff

e34 = json.load(open(os.path.join(ROOT, "results", "e3_e4.json")))
rows = []
for name in NAMES:
    for p in dami_files(name):
        v = os.path.basename(p)[:-5]
        if v not in e34[name]["variants"]:
            continue
        X, y, _ = read_arff(p)
        d = knn_distances(X, max(KS) + 1)
        nat = native_auc(v)
        imp = e34[name]["variants"][v]["implementation"]
        for k in KS:
            knn = d[:, k + 1]
            knnw = d[:, 1:k + 1].sum(axis=1)
            for det, s, key in (("KNN", knn, "KNN|exclude_series|%d" % (k + 1)), ("KNNW", knnw, "KNNW|exclude|%d" % k)):
                tied = 1.0 - len(np.unique(s)) / len(s)
                diff = abs(imp[key] - nat["%s|%d" % (det, k)])
                rows.append({"variant": v, "detector": det, "k": k, "tied_share": tied, "diff": diff,
                             "duplicates": int(len(X) - len(np.unique(X, axis=0)))})
out = {}
for det in ("KNN", "KNNW"):
    r = [x for x in rows if x["detector"] == det]
    ex = [x for x in r if x["diff"] < 1e-9]
    ne = [x for x in r if x["diff"] >= 1e-9]
    out[det] = {"values": len(r), "exact": len(ex), "nonexact": len(ne),
                "nonexact_with_tied_scores": sum(x["tied_share"] > 0 for x in ne),
                "exact_with_tied_scores": sum(x["tied_share"] > 0 for x in ex),
                "nonexact_without_tied_scores": sum(x["tied_share"] == 0 for x in ne),
                "max_diff_without_ties": max([x["diff"] for x in r if x["tied_share"] == 0] or [0.0])}
json.dump({"summary": out, "rows": rows}, open(os.path.join(ROOT, "results", "e3b_residuals.json"), "w"))
print(json.dumps(out, indent=1))
