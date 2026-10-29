"""Paper table, figure and headline numbers for protocol S8 (reads results/*.json)."""
import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e3_e4_scores import KS, native_auc
from s8_lib import NAMES, ROOT

R = os.path.join(ROOT, "results")
e12 = json.load(open(os.path.join(R, "e1_e2.json")))
e34 = json.load(open(os.path.join(R, "e3_e4.json")))
e5 = json.load(open(os.path.join(R, "e5_minmax.json")))
e6 = json.load(open(os.path.join(R, "e6_rankings.json")))
KEY = "KNN|exclude_series|11"  # native DAMI convention for the label k = 10 (amendment A1)
MM = "KNN10_native"


def describe(v, name):
    s = v[len(name):]
    parts = ["deduplicated" if "withoutdupl" in s else "with duplicates"]
    parts.append("normalized" if "_norm" in s else ("IDF-coded" if "idf" in s else "raw"))
    m = re.search(r"_v(\d\d)$", s)
    if m:
        parts.append("version %d" % int(m.group(1)))
    m = re.search(r"_(\d\d)(_v\d\d)?$", s)
    if m and not re.search(r"_v\d\d$", s[:m.end()]) and not s.endswith("_v%s" % m.group(1)):
        parts.append("%d\\%% outliers" % int(m.group(1)))
    return ", ".join(parts)


def table_variants(name):
    return [v for v in e34[name]["table_variants"] if v in e34[name]["variants"]]


def rng(vals):
    lo, hi = min(vals), max(vals)
    return "%.3f" % lo if abs(hi - lo) < 5e-4 else "%.3f--%.3f" % (lo, hi)


rows, head = [], {}
for name in NAMES:
    d = e12["datasets"][name]
    a = d["adbench"]
    tv = table_variants(name)
    raw = [e34[name]["variants"][v]["implementation"][KEY] for v in tv]
    mm = [e5[name]["variants"][v][MM] for v in tv]
    if d["matches"]:
        m = d["matches"][0]
        corr = describe(m["variant"], name) + (" (6 decimals)" if m["interpretation"] == "V1" else "")
        intable = "yes" if m["variant"] in tv else "no"
    else:
        corr = "none"
        intable = "--"
    rows.append("%s & %s & %d & %s & %s & %.3f & %s & %.3f & %s \\\\" % (
        name, "{:,}".format(a["n"]), a["d"], "{:,}".format(a["outliers"]), corr, e34[name]["adbench"][KEY],
        rng(raw), e5[name]["adbench"][MM], rng(mm)) + "%% table-variant match: " + intable)

# headline numbers
matched = [n for n in NAMES if e12["datasets"][n]["matches"]]
not_table = [n for n in matched if e12["datasets"][n]["matches"][0]["variant"] not in table_variants(n)]
undet = [n for n in NAMES if not e12["datasets"][n]["matches"]]
v1 = [n for n in matched if e12["datasets"][n]["matches"][0]["interpretation"] == "V1"]
head["names"] = len(NAMES)
head["matched"] = len(matched)
head["matched_V0"] = len(matched) - len(v1)
head["matched_V1"] = v1
head["matched_not_table_variant"] = not_table
head["undetermined"] = undet
head["variants_parsed"] = sum(len(e34[n]["variants"]) for n in NAMES)
ex1 = ex2 = n1 = n2 = 0
m1 = m2 = 0.0
for n in NAMES:
    for v, dd in e34[n]["variants"].items():
        nat = native_auc(v)
        imp = dd["implementation"]
        for k in KS:
            if "KNN|%d" % k in nat:
                diff = abs(imp["KNN|exclude_series|%d" % (k + 1)] - nat["KNN|%d" % k])
                n1 += 1; ex1 += diff < 1e-9; m1 = max(m1, diff)
            if "KNNW|%d" % k in nat:
                diff = abs(imp["KNNW|exclude|%d" % k] - nat["KNNW|%d" % k])
                n2 += 1; ex2 += diff < 1e-9; m2 = max(m2, diff)
head["native_control"] = {"knn_values": n1, "knn_exact": ex1, "knn_max_diff": m1,
                          "knnw_values": n2, "knnw_exact": ex2, "knnw_max_diff": m2}
dev_raw, dev_mm = {}, {}
for n in matched:
    tv = [v for v in table_variants(n)]
    dev_raw[n] = max(abs(e34[n]["variants"][v]["implementation"][KEY] - e34[n]["adbench"][KEY]) for v in tv)
    dev_mm[n] = max(abs(e5[n]["variants"][v][MM] - e5[n]["adbench"][MM]) for v in tv)
head["max_dev_matched_raw"] = max(dev_raw.items(), key=lambda x: x[1])
head["max_dev_matched_minmax"] = max(dev_mm.items(), key=lambda x: x[1])
head["max_dev_undetermined_minmax"] = max(((n, max(abs(e5[n]["variants"][v][MM] - e5[n]["adbench"][MM])
                                                 for v in table_variants(n))) for n in undet), key=lambda x: x[1])


def normed(v):
    return "_norm" in v


comp_all, comp_same = [], []
for n, r in e6.items():
    if not r.get("native_available"):
        continue
    for c in r["comparisons"]:
        if c["is_table_variant"]:
            comp_all.append(c)
            if normed(c["variant"]) == normed(r["matched_variant"]):
                comp_same.append(c)
for label, cs in (("rank_table_all", comp_all), ("rank_table_same_scaling", comp_same)):
    t = sorted(c["tau_b"] for c in cs)
    nt = len(t)
    head[label] = {"comparisons": len(cs), "names": None, "top_differs": sum(not c["top_same"] for c in cs),
                   "tau_median": t[nt // 2] if nt % 2 else (t[nt // 2 - 1] + t[nt // 2]) / 2, "tau_min": t[0], "max_reversed_pairs": max(c["reversed_pairs"] for c in cs)}
head["rank_table_all"]["names"] = sorted(n for n, r in e6.items() if r.get("native_available")
                                         and any(c["is_table_variant"] for c in r["comparisons"]))
with open(os.path.join(R, "headline.json"), "w") as f:
    json.dump(head, f, indent=1)
with open(os.path.join(R, "table_s8.tex"), "w") as f:
    f.write("\n".join(rows) + "\n")
print(json.dumps(head, indent=1))

# Figure: KNN (k = 10) ROC AUC of every DAMI variant versus the ADBench file, raw features.
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "font.size": 8,
                     "pdf.fonttype": 42, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "svg.hashsalt": "s8"})
GREY, INK, ACCENT = "#9A9A9A", "#222222", "#0072B2"
order = NAMES[::-1]
fig, axes = plt.subplots(1, 2, figsize=(5.2, 4.3), sharey=True)
for ax, source, title in ((axes[0], "raw", "Stored features"), (axes[1], "mm", "After min-max scaling")):
    for i, n in enumerate(order):
        vals = ([e34[n]["variants"][v]["implementation"][KEY] for v in e34[n]["variants"]] if source == "raw"
                else [e5[n]["variants"][v][MM] for v in e5[n]["variants"]])
        tv = table_variants(n)
        tvals = ([e34[n]["variants"][v]["implementation"][KEY] for v in tv] if source == "raw"
                 else [e5[n]["variants"][v][MM] for v in tv])
        adb = e34[n]["adbench"][KEY] if source == "raw" else e5[n]["adbench"][MM]
        ax.plot([min(vals), max(vals)], [i, i], color="#DDDDDD", lw=2.2, solid_capstyle="round", zorder=1)
        ax.scatter(vals, [i] * len(vals), s=7, color=GREY, linewidths=0, zorder=2)
        ax.scatter(tvals, [i] * len(tvals), s=22, facecolors="white", edgecolors=INK, linewidths=0.7, zorder=3)
        ax.scatter([adb], [i], s=30, marker="D", color=ACCENT, edgecolors="white", linewidths=0.6, zorder=4)
    ax.set_title(title, fontsize=8)
    ax.set_xlim(0.28, 1.02)
    ax.set_xlabel("ROC AUC, KNN (DAMI k = 10)")
    ax.grid(axis="x", color="#EEEEEE", lw=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_yticks(range(len(order)))
axes[0].set_yticklabels([n + ("*" if n in undet else "") for n in order])
h1 = axes[1].scatter([], [], s=7, color=GREY, linewidths=0, label="any DAMI variant")
h2 = axes[1].scatter([], [], s=22, facecolors="white", edgecolors=INK, linewidths=0.7, label="DAMI table variant")
h3 = axes[1].scatter([], [], s=30, marker="D", color=ACCENT, edgecolors="white", linewidths=0.6, label="ADBench file")
fig.legend(handles=[h1, h2, h3], loc="lower center", ncol=3, frameon=False, fontsize=7.5, bbox_to_anchor=(0.55, -0.01))
fig.tight_layout(rect=(0, 0.05, 1, 1))
out = os.path.join(R, "Fig2.pdf")
fig.savefig(out, metadata={"CreationDate": None, "ModDate": None})
fig.savefig(out.replace(".pdf", ".png"), dpi=200)
print("wrote", out)
