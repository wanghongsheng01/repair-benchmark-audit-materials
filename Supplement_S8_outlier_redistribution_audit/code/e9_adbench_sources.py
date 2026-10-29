"""E9: extract the source that ADBench's dataset table cites for each of the 19 names, from the arXiv HTML
of Han et al. (2022), saved as raw/adbench/adbench_arxiv_2206.09426_html.html (hash in results)."""
import hashlib
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from s8_lib import NAMES, ROOT

PATH = os.path.join(ROOT, "raw", "adbench", "adbench_arxiv_2206.09426_html.html")
ADB_NAME = {"Glass": "glass", "PenDigits": "pendigits", "Shuttle": "shuttle", "Annthyroid": "annthyroid"}
t = open(PATH, errors="ignore").read()
t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
seg = t[t.index("Data # Samples # Features # Anomaly % Anomaly Category Reference"):][:6000]
out = {"source_html_sha256": hashlib.sha256(open(PATH, "rb").read()).hexdigest(), "names": {}}
for n in NAMES:
    a = ADB_NAME.get(n, n)
    m = re.search(r"\b" + re.escape(a) + r"\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([A-Za-z]+)\s+\[\s*(\d+)\s*\]", seg)
    ref = m.group(6)
    rm = re.search(r"\[" + ref + r"\]\s+([^\[]{0,160})", t)
    out["names"][n] = {"table_row": list(m.groups()[:5]), "reference_number": int(ref),
                       "reference": rm.group(1).strip() if rm else None}
json.dump(out, open(os.path.join(ROOT, "results", "e9_adbench_sources.json"), "w"), indent=1)
for n, r in out["names"].items():
    print(n, r["reference_number"], (r["reference"] or "")[:60])
