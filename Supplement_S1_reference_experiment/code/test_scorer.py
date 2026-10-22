#!/usr/bin/env python3
"""Targeted adversarial checks for the public scorer's coverage and provenance gates."""
import argparse,copy,json,shutil,tempfile
from pathlib import Path
from score_public import score,lines
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--predictions',type=Path);p.add_argument('--output',type=Path)
 args=p.parse_args();root=args.root.resolve();source=args.predictions or root/'results/new/predictions.jsonl';rows=lines(source);results=[]
 def wrong_id(xs):xs[0]['task_id']='unknown/task/id';return xs
 def wrong_hash(xs):xs[-1]['input_digest']='0'*64;return xs
 def false_flag(xs):xs[0]['exact']=not xs[0]['exact'];return xs
 def wrong_timing(xs):xs[0]['median_cpu_us_5_repeats']+=1;return xs
 def bad_certificate(xs):
  r=next(r for r in xs if r['model']=='certified_minimal_patch');r['prediction']['certificate']['metric']='wrong_identity';return xs
 cases=[('missing',lambda xs:xs[:-1],'MISSING_PREDICTIONS'),('duplicate',lambda xs:xs+[xs[0]],'DUPLICATE_PREDICTION'),('unknown_task',wrong_id,'UNKNOWN_TASK_ID'),('mixed_input_hash',wrong_hash,'MIXED_INPUT_HASH'),('false_exact_flag',false_flag,'FALSE_EXACT_FLAG'),('timing_mismatch',wrong_timing,'TIMING_MEDIAN_MISMATCH'),('certificate_identity_tamper',bad_certificate,'INDEPENDENT_DECLARATION_CERTIFICATE_REJECTED')]
 with tempfile.TemporaryDirectory(prefix='audit-score-adversarial-') as tmp:
  path=Path(tmp)/'predictions.jsonl'
  for name,mutate,expected in cases:
   path.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in mutate(copy.deepcopy(rows))))
   try:score(root,path,'current')
   except ValueError as error:
    assert expected in str(error),(name,str(error));results.append({'case':name,'expected_rejection':expected,'actual_rejection':str(error),'passed':True})
   else:raise AssertionError('SCORER_ACCEPTED_CORRUPTION: '+name)
  path.write_text('{"model":"no_change","model":"expression_scan"}\n')
  try:score(root,path,'current')
  except ValueError as error:
   assert 'DUPLICATE_JSON_KEY' in str(error);results.append({'case':'duplicate_json_key','actual_rejection':str(error),'passed':True})
  else:raise AssertionError('SCORER_ACCEPTED_DUPLICATE_JSON_KEY')
  altered_root=Path(tmp)/'altered-input-root'
  (altered_root/'provenance').mkdir(parents=True)
  shutil.copy2(root/'provenance/input_contract.json',altered_root/'provenance/input_contract.json')
  shutil.copytree(root/'data',altered_root/'data')
  task_file=altered_root/'data/tasks.jsonl'
  task_file.write_bytes(task_file.read_bytes()+b'\n')
  try:score(altered_root,source,'current')
  except ValueError as error:
   assert 'INPUT_HASH_MISMATCH' in str(error);results.append({'case':'changed_input_bytes','actual_rejection':str(error),'passed':True})
  else:raise AssertionError('SCORER_ACCEPTED_CHANGED_INPUT_BYTES')
 result={'schema':'audit-public-scorer-negative-controls','passed':len(results),'cases':results}
 target=args.output or root/'results/scorer_negative_controls.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
