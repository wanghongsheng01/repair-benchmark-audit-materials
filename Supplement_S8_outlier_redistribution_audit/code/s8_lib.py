"""Shared readers, matching and detectors for protocol S8 (NumPy only)."""
import gzip
import hashlib
import os
import re

import numpy as np

NAMES = ["ALOI", "Glass", "Ionosphere", "Lymphography", "PenDigits", "Shuttle", "Waveform", "WBC",
         "WDBC", "WPBC", "Annthyroid", "Cardiotocography", "Hepatitis", "InternetAds", "PageBlocks",
         "Pima", "SpamBase", "Stamps", "Wilt"]
LITERATURE = {"ALOI", "Glass", "Ionosphere", "Lymphography", "PenDigits", "Shuttle", "Waveform", "WBC",
              "WDBC", "WPBC"}
ADBENCH_FILE = {"ALOI": "1_ALOI", "Glass": "14_glass", "Ionosphere": "18_Ionosphere",
                "Lymphography": "21_Lymphography", "PenDigits": "28_pendigits", "Shuttle": "32_shuttle",
                "Waveform": "41_Waveform", "WBC": "42_WBC", "WDBC": "43_WDBC", "WPBC": "46_WPBC",
                "Annthyroid": "2_annthyroid", "Cardiotocography": "7_Cardiotocography",
                "Hepatitis": "15_Hepatitis", "InternetAds": "17_InternetAds", "PageBlocks": "27_PageBlocks",
                "Pima": "29_Pima", "SpamBase": "35_SpamBase", "Stamps": "37_Stamps", "Wilt": "44_Wilt"}
# Counts published in the DAMI web table (instances, outliers, attributes as printed).
DAMI_TABLE = {"ALOI": (50000, 1508), "Glass": (214, 9), "Ionosphere": (351, 126),
              "Lymphography": (148, 6), "PenDigits": (9868, 20), "Shuttle": (1013, 13),
              "Waveform": (3443, 100), "WBC": (454, 10), "WDBC": (367, 10), "WPBC": (198, 47),
              "Annthyroid": (7200, 534), "Cardiotocography": (2126, 471), "Hepatitis": (80, 13),
              "InternetAds": (3264, 454), "PageBlocks": (5473, 560), "Pima": (768, 268),
              "SpamBase": (4601, 1813), "Stamps": (340, 31), "Wilt": (4839, 261)}
# Counts printed in the ADBench README table (samples, features, anomalies).
ADBENCH_README = {"ALOI": (49534, 27, 1508), "Glass": (214, 7, 9), "Ionosphere": (351, 32, 126),
                  "Lymphography": (148, 18, 6), "PenDigits": (6870, 16, 156), "Shuttle": (49097, 9, 3511),
                  "Waveform": (3443, 21, 100), "WBC": (223, 9, 10), "WDBC": (367, 30, 10),
                  "WPBC": (198, 33, 47), "Annthyroid": (7200, 6, 534), "Cardiotocography": (2114, 21, 466),
                  "Hepatitis": (80, 19, 13), "InternetAds": (1966, 1555, 368), "PageBlocks": (5393, 10, 510),
                  "Pima": (768, 8, 268), "SpamBase": (4207, 57, 1679), "Stamps": (340, 9, 31),
                  "Wilt": (4819, 5, 257)}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAMI_DIR = os.path.join(ROOT, "raw", "dami", "x")
ADB_DIR = os.path.join(ROOT, "raw", "adbench")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dami_files(name):
    group = "literature" if name in LITERATURE else "semantic"
    d = os.path.join(DAMI_DIR, group, name)
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".arff"))


def read_arff(path):
    """Return (X float64, y int, info) or raise ValueError for a deviating file."""
    attrs, rows, in_data = [], [], False
    with open(path, encoding="utf-8", errors="strict") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("%"):
                continue
            if not in_data:
                low = s.lower()
                if low.startswith("@attribute"):
                    m = re.match(r"@attribute\s+('([^']*)'|\S+)\s+(.+)$", s, re.I)
                    attrs.append(((m.group(2) if m.group(2) is not None else m.group(1)), m.group(3).strip()))
                elif low.startswith("@data"):
                    in_data = True
                continue
            rows.append(s.split(","))
    names = [a[0] for a in attrs]
    if "outlier" not in names:
        raise ValueError("no outlier attribute")
    li = names.index("outlier")
    feat = [i for i, (n, t) in enumerate(attrs) if n not in ("id", "outlier")]
    bad = [attrs[i] for i in feat if attrs[i][1].lower() not in ("real", "numeric", "integer")]
    if bad:
        raise ValueError("non-numeric attributes: %s" % bad[:3])
    labels = [r[li].strip().strip("'") for r in rows]
    vals = set(labels)
    if not vals <= {"yes", "no"}:
        raise ValueError("label values %s" % sorted(vals)[:5])
    X = np.array([[float(r[i]) for i in feat] for r in rows], dtype=np.float64)
    y = np.array([1 if v == "yes" else 0 for v in labels], dtype=np.int64)
    return X, y, {"attributes": len(feat), "has_id": "id" in names}


def read_adbench(name):
    path = os.path.join(ADB_DIR, ADBENCH_FILE[name] + ".npz")
    with np.load(path, allow_pickle=False) as z:
        X = np.asarray(z["X"], dtype=np.float64)
        y = np.asarray(z["y"]).astype(np.int64).ravel()
        dtype = str(z["X"].dtype)
    return X, y, path, dtype


def round6(X):
    return np.round(X, 6) + 0.0  # +0.0 turns -0.0 into 0.0


def minmax(X):
    lo, hi = X.min(axis=0), X.max(axis=0)
    span = np.where(hi > lo, hi - lo, 1.0)
    return np.where(hi > lo, (X - lo) / span, 0.0)


def row_keys(X, y=None):
    A = np.ascontiguousarray(X if y is None else np.column_stack([X, y.astype(np.float64)]))
    v = A.view(np.dtype((np.void, A.dtype.itemsize * A.shape[1]))).ravel()
    return np.sort(v)


def multiset_equal(X1, X2, y1=None, y2=None):
    if X1.shape != X2.shape:
        return False
    return bool(np.array_equal(row_keys(X1, y1), row_keys(X2, y2)))


def contained_fraction(Xa, Xb):
    """Fraction of rows of Xa (as a multiset) that also occur in Xb."""
    from collections import Counter
    cb = Counter(map(bytes, np.ascontiguousarray(Xb)))
    hit = 0
    for r in map(bytes, np.ascontiguousarray(Xa)):
        if cb[r] > 0:
            cb[r] -= 1
            hit += 1
    return hit / len(Xa)


def knn_distances(X, kmax, chunk=512, margin=24):
    """Sorted Euclidean distances to the kmax+margin nearest points of each row, self included.

    Candidates come from the expanded squared-distance formula; their distances are recomputed exactly
    from coordinate differences, so ties among duplicates are exact zeros.
    """
    n = X.shape[0]
    m = min(n, kmax + 1 + margin)
    sq = np.einsum("ij,ij->i", X, X)
    out = np.empty((n, m))
    for s in range(0, n, chunk):
        e = min(n, s + chunk)
        D = sq[s:e, None] + sq[None, :] - 2.0 * (X[s:e] @ X.T)
        idx = np.argpartition(D, m - 1, axis=1)[:, :m] if m < n else np.tile(np.arange(n), (e - s, 1))
        diff = X[idx] - X[s:e, None, :]
        d = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))
        out[s:e] = np.sort(d, axis=1)
    return out  # column 0 is the query point itself (distance 0) or an exact duplicate


def knn_scores(dist, k, convention):
    """KNN and KNNW scores. convention 'exclude': neighbors exclude the query point;
    'include': the query point is its own first neighbor (ELKI style)."""
    if convention == "exclude":
        nb = dist[:, 1:k + 1]
    else:
        nb = dist[:, 0:k]
    return nb[:, -1], nb.sum(axis=1)


def roc_auc(scores, y):
    order = np.argsort(scores, kind="mergesort")
    s = scores[order]
    ranks = np.empty(len(s))
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[i:j + 1] = (i + j) / 2.0 + 1.0
        i = j + 1
    r = np.empty(len(s))
    r[order] = ranks
    pos = y == 1
    n1, n0 = int(pos.sum()), int((~pos).sum())
    return float((r[pos].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def read_native_eval(path):
    """Parse a DAMI *.evaluation.csv.gz file into {(method, k): {measure: value}} and the header."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f if l.strip()]
    return lines
