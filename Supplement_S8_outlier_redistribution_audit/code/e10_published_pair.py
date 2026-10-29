"""E10: attribute the gap between two published KNN scores for the same dataset name:
ADBench (Han et al. 2022, Table D4, unsupervised KNN, ROC AUC) versus DAMI (Campos et al. 2016, native KNN).
ADBench's KNN is PyOD's default (distance to the 5th nearest training neighbour) on min-max scaled features;
DAMI's label k = 4 equals the 5th neighbour with the query point excluded (amendment A1)."""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e3_e4_scores import native_auc
from s8_lib import NAMES, ROOT, knn_distances, minmax, read_adbench, roc_auc
import csv, gzip

ADB_NAME = {"Glass": "glass", "PenDigits": "pendigits", "Shuttle": "shuttle", "Annthyroid": "annthyroid"}
t = open(os.path.join(ROOT, "raw", "adbench", "adbench_arxiv_2206.09426_html.html"), errors="ignore").read()
t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
hdr = "Datasets PCA OCSVM LOF CBLOF COF HBOS KNN SOD COPOD ECOD Deep SVDD DA GMM LODA IForest"
seg = t[t.index(hdr):][:12000]
assert "AUCROC of 14 unsupervised algorithms" in t[max(0, t.index(hdr) - 400):t.index(hdr)]
e12 = json.load(open(os.path.join(ROOT, "results", "e1_e2.json")))


def dami_knn(variant, k):
    path = os.path.join(ROOT, "raw", "dami_eval", variant + ".evaluation.csv.gz")
    with gzip.open(path, "rt") as f:
        for r in csv.DictReader(f):
            if r["Algorithm"] == "KNN" and int(r["k"]) == k:
                return float(r["ROC AUC"])


out = {}
for n in NAMES:
    a = ADB_NAME.get(n, n)
    m = re.search(r"\b" + re.escape(a) + r"\s+((?:[\d.]+\(\d+\)\s*){14})", seg)
    if not m:
        out[n] = {"adbench_published": None}
        continue
    pub = float(re.findall(r"([\d.]+)\(\d+\)", m.group(1))[6]) / 100.0
    X, y, _, _ = read_adbench(n)
    raw = roc_auc(knn_distances(X, 5)[:, 5], y)
    mm = roc_auc(knn_distances(minmax(X), 5)[:, 5], y)
    rec = {"adbench_published": pub, "ours_stored_k5": raw, "ours_minmax_k5": mm}
    if e12["datasets"][n]["matches"]:
        v = e12["datasets"][n]["matches"][0]["variant"]
        rec.update({"dami_variant": v, "dami_published_k5": dami_knn(v, 4)})
    out[n] = rec
    print("%-16s ADB_pub %.3f  ours_minmax %.3f  ours_stored %.3f  DAMI_pub %s" % (
        n, pub, mm, raw, "%.3f" % rec["dami_published_k5"] if "dami_published_k5" in rec else "-"))
json.dump(out, open(os.path.join(ROOT, "results", "e10_published_pair.json"), "w"), indent=1)
