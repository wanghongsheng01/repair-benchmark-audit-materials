"""Collect the numbers reported in the revised Section 6 (E3b, E3c, E6b, E7, E8, E9) with binomial tests."""
import json
import os
import sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import ROOT

R = os.path.join(ROOT, "results")
ld = lambda f: json.load(open(os.path.join(R, f)))
e6b = ld("e6b_rankings_robust.json")


def tail(k, n, p):
    return sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


rank = {}
for m, s in e6b["summary"].items():
    fl = s["floor_all_version_pairs"]
    floor = fl["material"] / fl["n"]
    prep, rep = s["preparation"], s["replicate"]
    rank[m] = {"floor_rate": floor, "floor_pairs": fl["n"], "floor_tau_median": fl["tau_median"],
               "preparation": prep, "preparation_one_sided_binomial_p": tail(prep["material"], prep["n"], floor),
               "tenth_downsample": rep, "tenth_downsample_rate": rep["material"] / rep["n"],
               "detectors_with_all_k": None}
e7 = ld("e7_planted.json")
res3 = ld("e3b_residuals.json")["summary"]
out = {"rankings": rank, "planted": e7["summary"], "residuals": res3,
       "glass_per_object": ld("e3c_glass_per_object.json")["all_labels_equal_k_plus_1_th_neighbor_excluding_query"],
       "aloi": {k: v for k, v in ld("e8_aloi_rows.json").items() if k != "nearest_pairs"},
       "adbench_cited": {n: r["reference_number"] for n, r in ld("e9_adbench_sources.json")["names"].items()}}
json.dump(out, open(os.path.join(R, "headline_revision.json"), "w"), indent=1)
print(json.dumps({m: {k: v for k, v in r.items() if k in ("floor_rate", "preparation_one_sided_binomial_p",
                                                           "tenth_downsample_rate")} for m, r in rank.items()}, indent=1))
