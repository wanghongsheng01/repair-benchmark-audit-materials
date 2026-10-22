#!/usr/bin/env python3
"""Extension runs: repeated fresh-JVM executions of main-memory BART tasks with the
unchanged applied observation harness. No seed is set; BART's default RNG is used."""
from pathlib import Path
import argparse, datetime, hashlib, json, subprocess, xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--java', required=True); ap.add_argument('--task', required=True, type=Path)
    ap.add_argument('--runs', type=int, required=True); ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args()
    task = a.task.resolve(); tree = ET.parse(task).getroot()
    for side in ['source', 'target']:
        node = tree.find(side)
        if node is not None and node.findtext('type') != 'GENERATE': raise ValueError('main-memory GENERATE inputs only')
    if tree.findall('.//access-configuration'): raise ValueError('external access configuration forbidden')
    a.out = a.out.resolve()
    if a.out.exists(): raise SystemExit('refuse to overwrite ' + str(a.out))
    a.out.mkdir(parents=True)
    cp = str(ROOT / 'native_build/classes') + ':' + str(ROOT / 'upstream_local/source/lib/*')
    records = []
    for i in range(1, a.runs + 1):
        case = f'{task.stem}_run{i:02d}'; out = a.out / case; out.mkdir()
        cmd = [a.java, '-Xmx512m', '-Dlogback.configurationFile=' + str(ROOT / 'logback-audit.xml'), '-cp', cp, 'BartAppliedAuditHarness', str(task), str(out)]
        rec = {'case_id': case, 'task_file': task.name, 'task_sha256': sha(task), 'harness_sha256': sha(ROOT / 'BartAppliedAuditHarness.java'),
               'run_index': i, 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            r = subprocess.run(cmd, cwd=out, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
            (out / 'native.log').write_bytes(r.stdout); rec['returncode'] = r.returncode
            rec['completed'] = r.returncode == 0 and 'AUDIT_NATIVE_OBSERVATION_COMPLETE' in r.stdout.decode(errors='replace')
        except subprocess.TimeoutExpired as e:
            (out / 'native.log').write_bytes(e.stdout or b''); rec.update(completed=False, error='TIMEOUT_120_SECONDS')
        rec['ended_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (out / 'run_receipt.json').write_text(json.dumps(rec, indent=2) + '\n'); records.append(rec)
        print(case, rec.get('returncode'), rec['completed'], flush=True)
    (a.out / 'run_manifest.json').write_text(json.dumps(records, indent=2) + '\n')
if __name__ == '__main__': main()
