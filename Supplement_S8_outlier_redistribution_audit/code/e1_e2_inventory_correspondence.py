"""Endpoints E1 (inventory) and E2 (correspondence) of protocol S8."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import (ADBENCH_README, DAMI_TABLE, NAMES, ROOT, contained_fraction, dami_files, minmax,
                    multiset_equal, read_adbench, read_arff, round6, sha256)


def main():
    out = {"inputs": {}, "datasets": {}}
    for name in NAMES:
        Xa, ya, apath, adtype = read_adbench(name)
        out["inputs"][os.path.basename(apath)] = sha256(apath)
        rec = {"adbench": {"file": os.path.basename(apath), "dtype": adtype, "n": int(Xa.shape[0]),
                           "d": int(Xa.shape[1]), "outliers": int(ya.sum()),
                           "label_values": sorted(int(v) for v in np.unique(ya)),
                           "readme_counts": ADBENCH_README[name],
                           "matches_readme": [int(Xa.shape[0]), int(Xa.shape[1]), int(ya.sum())]
                           == list(ADBENCH_README[name])},
               "dami_table": DAMI_TABLE[name], "variants": [], "matches": [], "diagnostic": []}
        Xa6 = round6(Xa)
        for path in dami_files(name):
            v = os.path.basename(path)[:-5]
            try:
                Xd, yd, info = read_arff(path)
            except ValueError as e:
                rec["variants"].append({"variant": v, "parsed": False, "reason": str(e)})
                continue
            vr = {"variant": v, "parsed": True, "n": int(Xd.shape[0]), "d": int(Xd.shape[1]),
                  "outliers": int(yd.sum()),
                  "matches_dami_table": (int(Xd.shape[0]), int(yd.sum())) == tuple(DAMI_TABLE[name])}
            rec["variants"].append(vr)
            if Xd.shape != Xa.shape:
                continue
            tests = [("V0", Xd, Xa), ("V1", round6(Xd), Xa6)]
            if "_norm" not in v:
                tests.append(("V2", round6(minmax(Xd)), Xa6))
            for interp, A, B in tests:
                if multiset_equal(A, B):
                    labels_ok = multiset_equal(A, B, yd, ya)
                    rec["matches"].append({"variant": v, "interpretation": interp,
                                           "labels_agree": labels_ok})
                    break
            else:
                rec["diagnostic"].append({"variant": v, "fraction_adbench_rows_in_variant_V1":
                                          round(contained_fraction(Xa6, round6(Xd)), 6)})
        if rec["matches"]:
            rec["outcome"] = "matched" if all(m["labels_agree"] for m in rec["matches"]) else \
                "features matched but labels differ"
        else:
            rec["outcome"] = "undetermined"
            if not rec["diagnostic"]:
                # no variant of equal shape: report the best row containment over all same-d variants
                for path in dami_files(name):
                    try:
                        Xd, yd, info = read_arff(path)
                    except ValueError:
                        continue
                    if Xd.shape[1] == Xa.shape[1]:
                        rec["diagnostic"].append({"variant": os.path.basename(path)[:-5], "n": int(Xd.shape[0]),
                                                  "fraction_adbench_rows_in_variant_V1":
                                                  round(contained_fraction(Xa6, round6(Xd)), 6)})
        out["datasets"][name] = rec
        print(name, rec["adbench"]["n"], rec["adbench"]["d"], rec["outcome"],
              [(m["variant"], m["interpretation"], m["labels_agree"]) for m in rec["matches"]], flush=True)
    for g in ("literature", "semantic"):
        p = os.path.join(ROOT, "raw", "dami", g + ".tar.gz")
        out["inputs"][g + ".tar.gz"] = sha256(p)
    with open(os.path.join(ROOT, "results", "e1_e2.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
