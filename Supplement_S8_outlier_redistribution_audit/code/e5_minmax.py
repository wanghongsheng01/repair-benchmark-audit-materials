"""Additional analysis E5 (amendment A3): scores after whole-file min-max scaling."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import NAMES, ROOT, dami_files, knn_distances, minmax, read_adbench, read_arff, roc_auc


def score(X, y):
    d = knn_distances(minmax(X), 11)
    # KNN10 / KNNW10: query point excluded, 10th neighbour; KNN10_native: 11th neighbour, which reproduces
    # the published DAMI values labelled k = 10 (amendment A1)
    return {"KNN10": roc_auc(d[:, 10], y), "KNNW10": roc_auc(d[:, 1:11].sum(axis=1), y),
            "KNN10_native": roc_auc(d[:, 11], y)}


def main():
    out = {}
    for name in NAMES:
        Xa, ya, _, _ = read_adbench(name)
        rec = {"adbench": score(Xa, ya), "variants": {}}
        for p in dami_files(name):
            try:
                Xd, yd, _ = read_arff(p)
            except ValueError:
                continue
            rec["variants"][os.path.basename(p)[:-5]] = score(Xd, yd)
        out[name] = rec
        print(name, "%.4f" % rec["adbench"]["KNN10"], flush=True)
        with open(os.path.join(ROOT, "results", "e5_minmax.json"), "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
