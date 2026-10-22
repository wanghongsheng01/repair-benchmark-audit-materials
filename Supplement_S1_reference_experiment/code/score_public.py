#!/usr/bin/env python3
"""Independent record scorer. Imports no repair/generator code.
Strictly checks input hashes, unique complete coverage, outcome flags, saved timing,
and the sole current declaration checker. Frozen frozen receives explicitly limited arithmetic checking.
"""
import argparse,collections,csv,hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODELS={'no_change','leave_catalog_out_constant','expression_scan','unqualified_rebuild','direct_declaration_rebuild','certified_minimal_patch'}
def require(condition,reason):
 if not condition:raise ValueError(reason)
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def counts(edges):return collections.Counter(canonical(x) for x in edges)
def pairs(items):
 result={}
 for k,v in items:
  require(k not in result,'DUPLICATE_JSON_KEY: '+k);result[k]=v
 return result
def invalid(value):raise ValueError('NONFINITE_JSON_NUMBER: '+value)
def parse(s):return json.loads(s,object_pairs_hook=pairs,parse_constant=invalid)
def load(path):return parse(path.read_text())
def lines(path):return [parse(s) for s in path.read_text().splitlines() if s.strip()]
def check_frozen_certificate(task,pred):
 """Historical frozen evidence arithmetic only; does not claim current schema acceptance."""
 c=pred['certificate'];cur=counts(task['current_edges']);gold=counts(task['gold_edges'])
 require(c['authority_digest']==digest({'contract':task['contract'],'registry':task['registry']}),'FROZEN_AUTHORITY_DIGEST')
 require(c['observed_adjacency_digest']==digest(sorted(task['current_edges'],key=canonical)),'FROZEN_OBSERVED_DIGEST')
 require(c['metric']==task['metric_id'],'FROZEN_IDENTITY')
 require(counts(c['removed'])==cur-gold and counts(c['added'])==gold-cur and counts(c['preserved'])==cur&gold,'FROZEN_DELTA')
 require(counts(c['preserved'])+counts(c['added'])==gold and counts(pred['edges'])==gold,'FROZEN_REPLAY')
def score(root,predictions,mode):
 contract=load(root/'provenance/input_contract.json');require(set(contract['models'])==MODELS,'METHOD_CONTRACT')
 for row in contract['files']:
  raw=(root/row['path']).read_bytes();require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'INPUT_HASH_MISMATCH: '+row['path'])
 input_digest=digest(contract['files']);tasks=lines(root/'data/tasks.jsonl')+lines(root/'data/clean_controls.jsonl')
 index={t['task_id']:t for t in tasks};require(len(tasks)==len(index)==854,'TASK_COVERAGE_OR_DUPLICATE')
 require(sum(t['mutation']=='clean' for t in tasks)==158,'CLEAN_COVERAGE')
 clean={(t['catalog_id'],t['metric_id']):t for t in tasks if t['mutation']=='clean'}
 for t in tasks:
  if t['mutation']=='clean':require(counts(t['gold_edges'])==counts(t['current_edges']),'CLEAN_GOLD_MISMATCH')
  else:
   base=clean[(t['catalog_id'],t['metric_id'])]
   require(t['contract']==base['contract'] and t['registry']==base['registry'] and counts(t['gold_edges'])==counts(base['gold_edges']),'MUTATION_AUTHORITY_OR_GOLD_MISMATCH')
   minus=counts(t['gold_edges'])-counts(t['current_edges']);plus=counts(t['current_edges'])-counts(t['gold_edges'])
   require(sum(minus.values())==1 and sum(plus.values())==(0 if t['mutation']=='delete' else 1),'MUTATION_CARDINALITY')
 records=lines(predictions);seen=set();stats=collections.defaultdict(collections.Counter);timings=collections.defaultdict(list);categories=collections.defaultdict(collections.Counter);edit=collections.Counter();certificates=0
 if mode=='current':
  from verify_certificate import verify
 for row in records:
  method=row['model'];tid=row['task_id'];key=(method,tid)
  require(method in MODELS,'UNKNOWN_METHOD');require(tid in index,'UNKNOWN_TASK_ID');require(key not in seen,'DUPLICATE_PREDICTION');seen.add(key)
  task=index[tid];pred=row['prediction'];require(type(pred['answered']) is bool and type(row['exact']) is bool,'NONBOOLEAN_FLAG')
  require(row['catalog_id']==task['catalog_id'] and row['mutation']==task['mutation'],'PREDICTION_METADATA_MISMATCH')
  exact=counts(pred['edges'])==counts(task['gold_edges']);changed=counts(pred['edges'])!=counts(task['current_edges']);require(row['exact']==exact,'FALSE_EXACT_FLAG')
  elapsed=row['median_cpu_us_5_repeats'];require(isinstance(elapsed,(int,float)) and math.isfinite(elapsed) and elapsed>=0,'INVALID_TIMING')
  if mode=='current':
   require(row.get('schema')=='audit-six-method-prediction','WRONG_PREDICTION_SCHEMA');require(row.get('input_digest')==input_digest,'MIXED_INPUT_HASH')
   samples=row.get('timing_ns_5_repeats');require(isinstance(samples,list) and len(samples)==5 and all(type(x) is int and x>=0 for x in samples),'MISSING_RAW_TIMING_SAMPLES')
   require(statistics.median(samples)/1000==elapsed,'TIMING_MEDIAN_MISMATCH')
  subset='clean' if task['mutation']=='clean' else 'mutations'
  for cid in (task['catalog_id'],'ALL'):
   k=(method,subset,cid);stats[k].update(n=1,exact=int(exact),answered=int(pred['answered']),changed=int(changed),wrong_changed=int(changed and not exact));timings[k].append(elapsed)
  categories[(task['mutation'],method)].update(n=1,exact=int(exact),wrong_changed=int(changed and not exact))
  if method=='certified_minimal_patch':
   if mode=='current':require(verify(task,pred),'INDEPENDENT_DECLARATION_CERTIFICATE_REJECTED')
   else:check_frozen_certificate(task,pred)
   certificates+=1
   if subset=='mutations':
    for field in ('added','removed','preserved'):edit[field]+=len(pred['certificate'][field])
    edit['gold_occurrences']+=len(task['gold_edges']);edit['observed_occurrences']+=len(task['current_edges'])
 require(seen=={(m,t) for m in MODELS for t in index},'MISSING_PREDICTIONS')
 require(len(records)==5124,'PREDICTION_COUNT')
 table=[]
 for key,value in sorted(stats.items()):
  method,subset,cid=key;ts=timings[key];table.append({'method':method,'subset':subset,'catalog_id':cid,**value,'median_cpu_us':round(statistics.median(ts),3),'p95_cpu_us':round(sorted(ts)[math.ceil(.95*len(ts))-1],3)})
 category_table=[{'mutation':k[0],'method':k[1],**v} for k,v in sorted(categories.items())]
 expected_exact={'no_change':(0,158),'leave_catalog_out_constant':(0,0),'expression_scan':(99,116),'unqualified_rebuild':(365,100),'direct_declaration_rebuild':(696,158),'certified_minimal_patch':(696,158)}
 for method,(mutation_exact,clean_exact) in expected_exact.items():
  require(stats[(method,'mutations','ALL')]['exact']==mutation_exact and stats[(method,'clean','ALL')]['exact']==clean_exact,'FROZEN_OUTCOME_REGRESSION')
 return {'schema':'audit-independent-public-score','mode':mode,'tasks':696,'clean_controls':158,'unique_complete_predictions':len(records),'method_count':len(MODELS),'certificates_checked':certificates,'certificate_scope':'independent authority parsing and typed registry resolution' if mode=='current' else 'frozen gold-based arithmetic only; not current acceptance','input_digest':input_digest,'prediction_sha256':hashlib.sha256(predictions.read_bytes()).hexdigest(),'mutation_edit_volume':dict(edit),'public_table_rows':len(table),'category_rows':len(category_table),'aggregate_rows':[r for r in table if r['catalog_id']=='ALL'],'timing_scope':'Saved frozen per-task five-call medians; no original raw call times exist' if mode=='frozen' else 'Fresh current per-task five-call medians independently recomputed from all saved nanosecond samples'},table,category_table

def compare_csv(path,rows,keys):
 expected={tuple(str(r[k]) for k in keys):r for r in rows}
 with path.open() as f:actual=list(csv.DictReader(f))
 seen=set()
 for row in actual:
  key=tuple(row[k] for k in keys);require(key in expected and key not in seen,'TABLE_COVERAGE_OR_DUPLICATE');seen.add(key);want=expected[key]
  for field in want:
   if field not in keys:
    require(field in row and float(row[field])==float(want[field]),'TABLE_VALUE_MISMATCH: '+str(key)+' '+field)
 require(seen==set(expected),'MISSING_TABLE_ROW')
def write_csv(path,rows):
 with path.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--predictions',type=Path);parser.add_argument('--mode',choices=('current','frozen'),default='current');parser.add_argument('--output-dir',type=Path)
 args=parser.parse_args();root=args.root.resolve();predictions=args.predictions or root/('results/new/predictions.jsonl' if args.mode=='current' else 'frozen/public_predictions.jsonl')
 receipt,table,categories=score(root,predictions,args.mode)
 if args.mode=='frozen':
  compare_csv(root/'frozen/public_tables.csv',table,('method','subset','catalog_id'));compare_csv(root/'frozen/category_results.csv',categories,('mutation','method'));receipt['frozen_csv_rows_matched']=len(table)+len(categories)
 out=args.output_dir or root/'results'/('score' if args.mode=='current' else 'score_frozen');out.mkdir(parents=True,exist_ok=True)
 write_csv(out/'public_tables.csv',table);write_csv(out/'category_results.csv',categories);(out/'score_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
