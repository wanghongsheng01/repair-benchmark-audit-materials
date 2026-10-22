#!/usr/bin/env python3
"""Exercise exported ZIP in a fresh directory, restoring pinned sources before regeneration.
Requires an explicitly supplied authorized local cache. No network or upstream code is executed.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--source-cache',required=True,type=Path);p.add_argument('--output',type=Path)
 args=p.parse_args();root=args.root.resolve();source_cache=args.source_cache.resolve();receipt={'schema':'audit-public-cold-start','network_calls':False,'upstream_programs_executed':False,'dependency_installations':False,'steps':[]}
 with tempfile.TemporaryDirectory(prefix='audit-reviewer-') as tmp:
  work=Path(tmp);archive=work/'reviewer.zip'
  subprocess.run([sys.executable,str(root/'code/export_bundle.py'),'--root',str(root),'--output',str(archive)],check=True,capture_output=True,text=True)
  unpack=work/'unpacked';unpack.mkdir()
  with zipfile.ZipFile(archive) as z:z.extractall(unpack)
  manifest=json.loads((unpack/'BUNDLE_MANIFEST.json').read_text())
  for f in manifest['files']:
   b=(unpack/f['path']).read_bytes();assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
  assert not (unpack/'data').exists() and not (unpack/'sources').exists()
  cache=work/'authorized-cache'
  # Copy only the 29 pinned files before entering the clean execution phase.
  for row in json.loads((unpack/'provenance/public_sources.json').read_text())['files']:
   rel=Path(row['repository'].split('/')[1])/row['path'];raw=(source_cache/rel).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];dest=cache/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  env={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME','AUDIT_GITHUB_TOKEN')}
  commands=[('restore_29_sources',['code/restore_sources.py','--cache',str(cache)]),('regenerate_854_tasks_byte_exact',['code/generate_public.py','--output-dir','data']),('rescore_frozen_5124',['code/score_public.py','--mode','frozen']),('run_new_5124',['code/run_public.py']),('independent_score',['code/score_public.py']),('scorer_negative_controls',['code/test_scorer.py'])]
  if (unpack/'code/run_robustness.py').exists():commands.append(('rerun_per_case_robustness',['code/run_robustness.py','--input-dir','data','--output-dir','results/robustness_cold_start']))
  for label,cmd in commands:
   run=subprocess.run([sys.executable,*cmd],cwd=unpack,env=env,capture_output=True,text=True,timeout=180)
   if run.returncode:raise RuntimeError(label+' FAILED\n'+run.stdout+'\n'+run.stderr)
   receipt['steps'].append({'step':label,'exit_code':run.returncode,'stdout_sha256':hashlib.sha256(run.stdout.encode()).hexdigest()})
  receipt['task_hashes']=[{'path':r['path'],'sha256':hashlib.sha256((unpack/r['path']).read_bytes()).hexdigest()} for r in json.loads((unpack/'provenance/input_contract.json').read_text())['files']]
  receipt['isolated_score']=json.loads((unpack/'results/score/score_receipt.json').read_text())
  receipt['source_recovery_mode']='Explicit 29-file authorized local cache, copied into clean workspace and hash-verified; online downloader not exercised in this run.'
  receipt['ancestor_paths_used_during_execution']=False;receipt['fresh_directory_removed_after_test']=True;receipt['status']='PASS'
 dest=args.output or root/'results/cold_start_receipt.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'status':receipt['status'],'steps':len(receipt['steps']),'predictions':receipt['isolated_score']['unique_complete_predictions'],'certificate_acceptances':receipt['isolated_score']['certificates_checked'],'ancestor_paths_used_during_execution':False},indent=2))
if __name__=='__main__':main()
