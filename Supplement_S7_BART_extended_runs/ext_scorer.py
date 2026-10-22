#!/usr/bin/env python3
"""Additional analysis (not a frozen endpoint): score the two value-orientation probes of
every event-bearing extension run with BART's unmodified native scorer."""
from pathlib import Path
import argparse, json, subprocess
ROOT = Path(__file__).resolve().parent
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--java', required=True); ap.add_argument('--out', type=Path, required=True); a = ap.parse_args()
    cp = str(ROOT / 'native_build/classes') + ':' + str(ROOT / 'upstream_local/source/lib/*'); results = []
    for task in sorted((ROOT / 'audit').iterdir()):
        for row in json.loads((task / 'cases.json').read_text()):
            if not row['events']: continue
            case = row['case_id']; out = a.out / task.name; out.mkdir(parents=True, exist_ok=True); o = out / (case + '_scores.json')
            cmd = [a.java, '-Xmx256m', '-Dlogback.configurationFile=' + str(ROOT / 'logback-audit.xml'), '-cp', cp, 'BartScorerProbe',
                   str(ROOT / 'runs' / task.name / case / 'events_native.csv'), str(task / (case + '_snapshot_probe.csv')), str(task / (case + '_wiki_probe.csv')), str(o)]
            r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            if r.returncode: raise SystemExit(r.stdout.decode())
            results.append({'task': task.name, 'case_id': case, 'events': row['events'], **json.loads(o.read_text())})
    (a.out / 'all_scores.json').write_text(json.dumps(results, indent=1) + '\n')
if __name__ == '__main__': main()
