"""Endpoints E3 (native control) and E4 (score sensitivity) of protocol S8."""
import csv
import gzip
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import NAMES, ROOT, dami_files, knn_distances, knn_scores, read_adbench, read_arff, roc_auc

KS = [1, 5, 10, 20, 50]
CONVENTIONS = ["exclude", "include"]
EVAL_DIR = os.path.join(ROOT, "raw", "dami_eval")


def scores_for(X, y):
    """Query-excluded KNN for k = 1..51 and KNNW for k = 1..50 (amendment A1), plus the frozen
    conventions at the protocol k values."""
    dist = knn_distances(X, max(KS) + 1)
    res = {}
    for conv in CONVENTIONS:
        for k in KS:
            knn, knnw = knn_scores(dist, k, conv)
            res["KNN|%s|%d" % (conv, k)] = roc_auc(knn, y)
            res["KNNW|%s|%d" % (conv, k)] = roc_auc(knnw, y)
    for k in range(1, max(KS) + 2):
        res["KNN|exclude_series|%d" % k] = roc_auc(dist[:, k], y)
    return res


def native_auc(variant):
    path = os.path.join(EVAL_DIR, variant + ".evaluation.csv.gz")
    if not os.path.exists(path):
        return None
    out = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Algorithm"] in ("KNN", "KNNW") and int(row["k"]) in KS:
                out["%s|%s" % (row["Algorithm"], row["k"])] = float(row["ROC AUC"])
    return out


def main():
    e12 = json.load(open(os.path.join(ROOT, "results", "e1_e2.json")))
    only = set(sys.argv[1:])
    path_out = os.path.join(ROOT, "results", "e3_e4.json")
    out = json.load(open(path_out)) if os.path.exists(path_out) else {}
    for name in NAMES:
        if only and name not in only:
            continue
        rec = {"adbench": None, "variants": {}}
        Xa, ya, _, _ = read_adbench(name)
        rec["adbench"] = scores_for(Xa, ya)
        for path in dami_files(name):
            v = os.path.basename(path)[:-5]
            try:
                Xd, yd, _ = read_arff(path)
            except ValueError:
                continue
            rec["variants"][v] = {"implementation": scores_for(Xd, yd), "native": native_auc(v)}
        rec["table_variants"] = [x["variant"] for x in e12["datasets"][name]["variants"]
                                 if x.get("matches_dami_table")]
        rec["matched_variants"] = [m["variant"] for m in e12["datasets"][name]["matches"]]
        out[name] = rec
        print(name, "variants", len(rec["variants"]), "adbench KNN k10 excl %.4f" % rec["adbench"]["KNN|exclude|10"],
              flush=True)
        with open(path_out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
