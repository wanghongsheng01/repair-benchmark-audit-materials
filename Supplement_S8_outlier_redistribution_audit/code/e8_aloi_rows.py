"""Diagnostic E8 (amendment A5): what differs between the ADBench ALOI file and the deduplicated raw DAMI variant."""
import json
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import ROOT, dami_files, read_adbench, read_arff, round6

Xa, ya, _, _ = read_adbench("ALOI")
Xd, yd, _ = read_arff([p for p in dami_files("ALOI") if p.endswith("/ALOI_withoutdupl.arff")][0])
A, D = round6(Xa), round6(Xd)
ca = Counter(map(bytes, np.ascontiguousarray(A)))
cd = Counter(map(bytes, np.ascontiguousarray(D)))
only_a = list((ca - cd).elements())
only_d = list((cd - ca).elements())
ra = [np.frombuffer(b, dtype=np.float64) for b in only_a]
rd = [np.frombuffer(b, dtype=np.float64) for b in only_d]
pairs = []
for r in ra:
    diffs = [np.abs(r - s) for s in rd]
    j = int(np.argmin([d.sum() for d in diffs]))
    dd = diffs[j]
    pairs.append({"attributes_differing": int((dd > 0).sum()), "max_abs_diff": float(dd.max()),
                  "positions": [int(i) for i in np.nonzero(dd > 0)[0]]})
# labels of the unmatched rows
def lab(rows, X6, y):
    keys = {bytes(np.ascontiguousarray(x)): int(v) for x, v in zip(X6, y)}
    return Counter(keys[b] for b in rows)
out = {"rows_only_in_adbench": len(only_a), "rows_only_in_dami": len(only_d),
       "labels_only_in_adbench": dict(lab(only_a, A, ya)), "labels_only_in_dami": dict(lab(only_d, D, yd)),
       "nearest_pairs": pairs,
       "adbench_duplicate_rows": int(len(A) - len(np.unique(A, axis=0)))}
json.dump(out, open(os.path.join(ROOT, "results", "e8_aloi_rows.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "nearest_pairs"}, indent=1))
print(Counter((p["attributes_differing"], round(p["max_abs_diff"], 6)) for p in pairs).most_common(8))
