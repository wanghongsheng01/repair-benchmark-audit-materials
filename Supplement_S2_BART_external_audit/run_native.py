#!/usr/bin/env python3
"""Run only the four frozen original BART in-memory tasks; no installation/network."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
TASKS=['employees/employees-egtask.xml','employees/employees-random-egtask.xml','employees/employees-symmetrictest-egtask.xml','misc/synthetic_01-egtask.xml']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--java',required=True);ap.add_argument('--run-id',default='native_run_01');ap.add_argument('--applied',action='store_true');args=ap.parse_args()
 java=Path(args.java).resolve();src=ROOT/'upstream_local/source';outroot=ROOT/args.run_id
 if outroot.exists():raise SystemExit('Refuse overwrite existing native run')
 outroot.mkdir()
 harness='BartAppliedAuditHarness' if args.applied else 'BartAuditHarness'
 cp=str(ROOT/'native_build/classes')+':'+str(src/'lib/*')
 records=[]
 for rel in TASKS:
  task=src/'Bart_Engine/misc/resources'/rel;tree=ET.parse(task).getroot()
  for side in ['source','target']:
   node=tree.find(side)
   if node is not None and node.findtext('type')!='GENERATE':raise ValueError('Non-memory input forbidden')
  if tree.findall('.//access-configuration'):raise ValueError('External access configuration forbidden')
  case=task.stem;out=outroot/case;out.mkdir();cmd=[str(java),'-Xmx512m','-Dlogback.configurationFile='+str(ROOT/'logback-audit.xml'),'-cp',cp,harness,str(task),str(out)]
  record={'case_id':case,'upstream_task':rel,'task_sha256':sha(task),'harness_sha256':sha(ROOT/(harness+'.java')),'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'original_task_unchanged':True,'runtime_adaptation':({'applyCellChanges':True,'exportCleanDB':True,'exportDirtyDB':True,'exportCellChanges':True,'export_paths':'isolated case directory'} if args.applied else {})}
  try:
   result=subprocess.run(cmd,cwd=out,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
   (out/'native.log').write_bytes(result.stdout);record['returncode']=result.returncode;record['completed']='AUDIT_NATIVE_OBSERVATION_COMPLETE' in result.stdout.decode(errors='replace') and result.returncode==0
  except subprocess.TimeoutExpired as e:
   (out/'native.log').write_bytes(e.stdout or b'');record.update(completed=False,error='TIMEOUT_120_SECONDS')
  record['ended_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();records.append(record)
  (out/'run_receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(case,record.get('returncode'),record['completed'],flush=True)
 (outroot/'run_manifest.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':main()
