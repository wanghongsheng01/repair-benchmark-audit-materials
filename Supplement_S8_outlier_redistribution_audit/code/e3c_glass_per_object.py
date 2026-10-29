"""E3c: locate the KNN offset at score level with DAMI's per-object results for Glass_withoutdupl_norm."""
import gzip
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import ROOT, dami_files, knn_distances, read_arff

PATH = os.path.join(ROOT, "raw", "dami_eval_results_Glass.csv.gz")  # .../literature/Glass/Glass_withoutdupl_norm.results.csv.gz
X, y, _ = read_arff([p for p in dami_files("Glass") if p.endswith("Glass_withoutdupl_norm.arff")][0])
d = knn_distances(X, 101)
rows = {}
with gzip.open(PATH, "rt") as f:
    for line in f:
        p = line.split()
        if p and p[0].startswith(("KNN-", "bylabel")):
            rows[p[0]] = np.array(list(map(float, p[1:])))
res = {"sha256": hashlib.sha256(open(PATH, "rb").read()).hexdigest(), "labels_equal": bool(
    np.array_equal(rows["bylabel"].astype(int), y)), "knn_label_to_neighbor_rank": {}}
for k in range(1, 101):
    s = rows.get("KNN-%03d" % k)
    if s is None:
        continue
    hit = [j for j in range(d.shape[1]) if np.allclose(s, d[:, j], rtol=0, atol=1e-9)]
    res["knn_label_to_neighbor_rank"][k] = hit
ok = all(v and v[0] == k + 1 for k, v in ((int(k), v) for k, v in res["knn_label_to_neighbor_rank"].items()))
res["all_labels_equal_k_plus_1_th_neighbor_excluding_query"] = ok
json.dump(res, open(os.path.join(ROOT, "results", "e3c_glass_per_object.json"), "w"), indent=1)
print(ok, res["labels_equal"], len(res["knn_label_to_neighbor_rank"]))
