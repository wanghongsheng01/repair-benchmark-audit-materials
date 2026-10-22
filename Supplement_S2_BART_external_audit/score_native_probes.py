#!/usr/bin/env python3
"""Re-score saved probes with BART. No generation, network or database use."""
from pathlib import Path
import argparse,subprocess,json,hashlib,datetime
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--java',required=True);args=ap.parse_args();rows=json.loads((ROOT/'audit_results/all_cases.json').read_text());receipts=[]
 cp=str(ROOT/'native_build/classes')+':'+str(ROOT/'upstream_local/source/lib/*')
 for row in rows:
  if not row['events']:continue
  case=row['case_id'];expected=ROOT/'native_applied_01'/case/'events_native.csv';observed=ROOT/'audit_results'/(case+'_snapshot_probe.csv');wiki=ROOT/'audit_results'/(case+'_wiki_probe.csv')
  output=ROOT/'audit_results/native_scorer_probes.json'
  cmd=[str(Path(args.java).resolve()),'-Xmx256m','-Dlogback.configurationFile='+str(ROOT/'logback-audit.xml'),'-cp',cp,'BartScorerProbe',str(expected),str(observed),str(wiki),str(output)]
  start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);end=datetime.datetime.now(datetime.timezone.utc).isoformat()
  log=ROOT/'audit_results/native_scorer_stdout.log';log.write_bytes(r.stdout)
  receipt={'case_id':case,'started_at_utc':start,'ended_at_utc':end,'command':cmd,'returncode':r.returncode,'operation':'deterministic re-score saved six-event probes; no native generation','inputs':{p.name:sha(p) for p in [expected,observed,wiki,ROOT/'BartScorerProbe.java']},'output_sha256':sha(output),'stdout_sha256':sha(log),'upstream_commit':'354f503f401d5360e9a6957f4edd096d3dc413f6'}
  receipts.append(receipt)
  if r.returncode:raise SystemExit(r.stdout.decode())
 (ROOT/'audit_results/native_scorer_execution_receipt.json').write_text(json.dumps(receipts,indent=2)+'\n');print((ROOT/'audit_results/native_scorer_probes.json').read_text())
if __name__=='__main__':main()
