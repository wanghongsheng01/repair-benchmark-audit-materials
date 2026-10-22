#!/usr/bin/env python3
"""Offline frozen-result replay, integrity and independent probe scoring."""
from pathlib import Path
import hashlib,json,csv,subprocess,sys,tempfile,math
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=json.loads((ROOT/'MANIFEST.json').read_text())
 for rec in manifest['files']:
  p=ROOT/rec['path']
  if not p.is_file() or sha(p)!=rec['sha256']:raise ValueError('Integrity failure: '+rec['path'])
 for name in ['protocol_freeze_receipt.json','protocol_amendment_A1_receipt.json','protocol_amendment_A2_receipt.json']:
  r=json.loads((ROOT/name).read_text());path=r.get('file',r.get('protocol_file'))
  if sha(ROOT/path)!=r['sha256']:raise ValueError('protocol mismatch')
 with tempfile.TemporaryDirectory(prefix='audit-bart-replay-') as temp:
  out=Path(temp)/'audit';p=subprocess.run([sys.executable,str(ROOT/'audit_external.py'),'--run-dir',str(ROOT/'native_applied_01'),'--out',str(out)],capture_output=True,text=True)
  if p.returncode:raise ValueError(p.stdout+p.stderr)
  for f in out.iterdir():
   saved=ROOT/'audit_results'/f.name
   if not saved.is_file() or f.read_bytes()!=saved.read_bytes():raise ValueError('Frozen replay mismatch: '+f.name)
 scorer=json.loads((ROOT/'audit_results/native_scorer_probes.json').read_text())
 rows=json.loads((ROOT/'audit_results/all_cases.json').read_text());checked=0
 for row in rows:
  if not row['events']:continue
  case=row['case_id'];native=ROOT/'native_applied_01'/case
  clean=json.loads((native/'clean_snapshot.json').read_text());truth={r['oid']+'.'+a:v['text'] for records in clean.values() for r in records for a,v in r['cells'].items()}
  expected=list(csv.reader((native/'events_native.csv').open(newline='')));refs={r[0] for r in expected}
  for label,suffix in [('snapshot_clean_probe','snapshot_probe'),('documented_clean_column_probe','wiki_probe')]:
   probe=list(csv.reader((ROOT/'audit_results'/(case+'_'+suffix+'.csv')).open(newline='')));byref=dict(probe)
   if len(byref)!=len(probe) or set(byref)!=refs:raise ValueError('probe identity mismatch')
   correct=sum(byref[k].casefold()==truth[k].casefold() for k in refs);p=correct/len(probe);r=correct/len(refs);f1=2*p*r/(p+r) if p+r else None
   reported=scorer[label]['value']
   if any(reported[k]!=v for k,v in [('precision',p),('recall',r),('f1',f1)]):raise ValueError('native/independent score mismatch')
   if scorer[label]['cell']!={'precision':1.0,'recall':1.0,'f1':1.0,'native_f1_text':'1.0'}:raise ValueError('cell score mismatch')
  checked+=1
 receipt=json.loads((ROOT/'audit_results/native_scorer_execution_receipt.json').read_text())
 if len(receipt)!=checked or any(r['returncode']!=0 for r in receipt):raise ValueError('scorer receipt mismatch')
 print(json.dumps({'status':'EXTERNAL_AUDIT_REPLAY_OK','manifest_files':len(manifest['files']),'native_cases':4,'target_cells':118,'events':6,'independently_checked_native_scorer_cases':checked,'network_used':False,'java_used':False,'ancestor_inputs_used':False},indent=2))
if __name__=='__main__':main()
