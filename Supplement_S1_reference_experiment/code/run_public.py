#!/usr/bin/env python3
"""Run six methods over pinned public synthetic tasks; preserve all five fresh timing samples."""
import argparse,collections,hashlib,json,platform,re,statistics,time
from pathlib import Path
from reference_repair import patch,rebuild
from verify_certificate import verify
ROOT=Path(__file__).resolve().parents[1]
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def adjacency(x):return sorted(canonical(e) for e in x)
def lines(path):return [json.loads(x) for x in path.read_text().splitlines()]
def expression(task):
 m=task['contract']['metric'];params=m.get('type_params',{})
 if m['type'].lower()!='derived':return {'edges':task['current_edges'],'answered':True}
 refs=params.get('metrics',[]);aliases={x if isinstance(x,str) else x.get('alias',x['name']):x if isinstance(x,str) else x['name'] for x in refs}
 out=[]
 for token in sorted(set(re.findall(r'\b[A-Za-z_][A-Za-z0-9_]*\b',params.get('expr','')))):
  target=aliases.get(token,token)
  if target in task['registry']['metrics']:out.append({'role':'depends_on','target':'metric:'+target,'qualifiers':{}})
 return {'edges':sorted(out,key=canonical),'answered':True}
def unqualified(task):
 pred=rebuild(task);pred['edges']=[dict(e,qualifiers={}) for e in pred['edges']];return pred
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output-dir',type=Path)
 args=parser.parse_args();root=args.root.resolve();out=args.output_dir or root/'results/new';out.mkdir(parents=True,exist_ok=True)
 contract=json.loads((root/'provenance/input_contract.json').read_text())
 for rec in contract['files']:
  raw=(root/rec['path']).read_bytes();assert len(raw)==rec['bytes'] and hashlib.sha256(raw).hexdigest()==rec['sha256'],'INPUT_HASH_MISMATCH'
 input_digest=hashlib.sha256(canonical(contract['files']).encode()).hexdigest()
 tasks=lines(root/'data/tasks.jsonl')+lines(root/'data/clean_controls.jsonl');assert len(tasks)==len({t['task_id'] for t in tasks})==854
 frozen=lines(root/'frozen/public_predictions.jsonl');old={(r['task_id'],r['model']):r['prediction']['edges'] for r in frozen};assert len(old)==5124
 catalogs=sorted({t['catalog_id'] for t in tasks})
 constants={cid:json.loads(collections.Counter(canonical(t['gold_edges']) for t in tasks if t['mutation']!='clean' and t['catalog_id']!=cid).most_common(1)[0][0]) for cid in catalogs}
 methods={'no_change':lambda t:{'edges':t['current_edges'],'answered':True},'leave_catalog_out_constant':lambda t:{'edges':constants[t['catalog_id']],'answered':True},'expression_scan':expression,'unqualified_rebuild':unqualified,'direct_declaration_rebuild':rebuild,'certified_minimal_patch':patch}
 records=[];certificate_count=0
 for method,fn in methods.items():
  for task in tasks:
   pred=fn(task);samples=[]
   for _ in range(5):
    start=time.perf_counter_ns();fn(task);samples.append(time.perf_counter_ns()-start)
   assert adjacency(pred['edges'])==adjacency(old[(task['task_id'],method)]),('ADJACENCY_REGRESSION',task['task_id'],method)
   if method=='certified_minimal_patch':
    assert verify(task,pred),('CERTIFICATE_REJECTED',task['task_id']);certificate_count+=1
   records.append({'schema':'audit-six-method-prediction','task_id':task['task_id'],'catalog_id':task['catalog_id'],'metric_id':task['metric_id'],'mutation':task['mutation'],'model':method,'prediction':pred,'exact':adjacency(pred['edges'])==adjacency(task['gold_edges']),'input_digest':input_digest,'timing_ns_5_repeats':samples,'median_cpu_us_5_repeats':statistics.median(samples)/1000})
 target=out/'predictions.jsonl';target.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records))
 receipt={'schema':'audit-public-run','mutations':696,'clean_controls':158,'predictions':len(records),'sole_independent_checker_acceptances':certificate_count,'adjacency_regression_equal_to_frozen':len(records),'input_digest':input_digest,'prediction_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'runtime':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()},'timing_scope':'NEW measurements: five synchronous in-memory calls, all five nanosecond samples saved per task; no source parsing, I/O, official compiler, SQL or network; not compared to old timing as speedup','scientific_scope':'Single-organization official example/test-fixture projection with synthetic mutations; not natural gold or production defects.'}
 (out/'run_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
