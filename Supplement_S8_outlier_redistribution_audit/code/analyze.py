"""Summaries of E1-E4 for protocol S8 (reads results/e1_e2.json and results/e3_e4.json)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e3_e4_scores import KS, native_auc
from s8_lib import NAMES, ROOT


def native_control(rec, variants):
    """Max |implementation - native| per convention over the given variants, KNN and KNNW separately."""
    res = {"n_variants_with_native": 0, "KNN_exclude": 0.0, "KNN_include": 0.0, "KNN_shift": 0.0,
           "KNNW_exclude": 0.0, "KNNW_include": 0.0, "missing_native": []}
    for v in variants:
        nat = native_auc(v)
        if not nat:
            res["missing_native"].append(v)
            continue
        res["n_variants_with_native"] += 1
        imp = rec["variants"][v]["implementation"]
        for k in KS:
            n1, nw = nat.get("KNN|%d" % k), nat.get("KNNW|%d" % k)
            if n1 is not None:
                res["KNN_exclude"] = max(res["KNN_exclude"], abs(imp["KNN|exclude|%d" % k] - n1))
                res["KNN_include"] = max(res["KNN_include"], abs(imp["KNN|include|%d" % k] - n1))
                res["KNN_shift"] = max(res["KNN_shift"], abs(imp["KNN|exclude_series|%d" % (k + 1)] - n1))
            if nw is not None:
                res["KNNW_exclude"] = max(res["KNNW_exclude"], abs(imp["KNNW|exclude|%d" % k] - nw))
                res["KNNW_include"] = max(res["KNNW_include"], abs(imp["KNNW|include|%d" % k] - nw))
    return res


def main():
    e12 = json.load(open(os.path.join(ROOT, "results", "e1_e2.json")))
    e34 = json.load(open(os.path.join(ROOT, "results", "e3_e4.json")))
    rows, summary = [], {}
    for name in NAMES:
        d12, d34 = e12["datasets"][name], e34[name]
        parsed = list(d34["variants"])
        table = [v for v in d34["table_variants"] if v in d34["variants"]]
        matched = d34["matched_variants"]
        frozen = sorted(set(table) | set(matched))
        nc_frozen = native_control(d34, frozen)
        nc_all = native_control(d34, parsed)
        a = d34["adbench"]
        key = "KNN|exclude|10"
        keyw = "KNNW|exclude|10"
        tab_auc = [d34["variants"][v]["implementation"][key] for v in table]
        all_auc = [d34["variants"][v]["implementation"][key] for v in parsed]
        tab_aucw = [d34["variants"][v]["implementation"][keyw] for v in table]
        flips = sum(1 for v in parsed
                    if (d34["variants"][v]["implementation"][key] > d34["variants"][v]["implementation"][keyw])
                    != (a[key] > a[keyw]))
        row = {"name": name, "adbench_n": d12["adbench"]["n"], "adbench_d": d12["adbench"]["d"],
               "adbench_outliers": d12["adbench"]["outliers"], "outcome": d12["outcome"],
               "matched": [(m["variant"], m["interpretation"]) for m in d12["matches"]],
               "matched_is_table_variant": any(m["variant"] in table for m in d12["matches"]),
               "n_variants": len(parsed), "n_table_variants": len(table),
               "dami_table": d12["dami_table"],
               "auc_knn10_adbench": a[key], "auc_knnw10_adbench": a[keyw],
               "auc_knn10_table_min": min(tab_auc) if tab_auc else None,
               "auc_knn10_table_max": max(tab_auc) if tab_auc else None,
               "auc_knnw10_table_min": min(tab_aucw) if tab_aucw else None,
               "auc_knnw10_table_max": max(tab_aucw) if tab_aucw else None,
               "auc_knn10_all_min": min(all_auc), "auc_knn10_all_max": max(all_auc),
               "knn_vs_knnw_order_differs_from_adbench_in_variants": flips,
               "native_control_frozen": nc_frozen, "native_control_all": nc_all,
               "diagnostic": d12["diagnostic"][:3]}
        rows.append(row)
    agg = {"names": len(rows),
           "matched": sum(r["outcome"] == "matched" for r in rows),
           "undetermined": [r["name"] for r in rows if r["outcome"] == "undetermined"],
           "matched_not_table_variant": [r["name"] for r in rows if r["outcome"] == "matched"
                                         and not r["matched_is_table_variant"]],
           "variants_parsed": sum(r["n_variants"] for r in rows),
           "variants_with_native": sum(r["native_control_all"]["n_variants_with_native"] for r in rows),
           "max_abs_native_diff_all": {c: max(r["native_control_all"][c] for r in rows)
                                       for c in ("KNN_exclude", "KNN_include", "KNN_shift", "KNNW_exclude",
                                                 "KNNW_include")},
           "max_abs_native_diff_frozen": {c: max(r["native_control_frozen"][c] for r in rows)
                                          for c in ("KNN_exclude", "KNN_include", "KNN_shift", "KNNW_exclude",
                                                    "KNNW_include")}}
    summary = {"aggregate": agg, "rows": rows}
    with open(os.path.join(ROOT, "results", "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(agg, indent=1))
    for r in rows:
        print("%-16s %-12s n=%-6d %-40s tab=%-3d AUC_adb=%.3f table=[%s] all=[%.3f,%.3f] natmiss=%d" % (
            r["name"], r["outcome"], r["adbench_n"], r["matched"][:1], r["n_table_variants"],
            r["auc_knn10_adbench"],
            "%.3f,%.3f" % (r["auc_knn10_table_min"], r["auc_knn10_table_max"]) if r["auc_knn10_table_min"] is not None else "-",
            r["auc_knn10_all_min"], r["auc_knn10_all_max"], len(r["native_control_all"]["missing_native"])))


if __name__ == "__main__":
    main()
