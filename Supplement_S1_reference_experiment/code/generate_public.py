#!/usr/bin/env python3
"""Pinned-source adapter/generator. Executes no upstream source code or SQL."""
from __future__ import annotations
import argparse,collections,copy,hashlib,json,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)

def edgekey(e):return canonical(e)

def ordered(es):return sorted(es,key=edgekey)

def name(x):return x if isinstance(x,str) else x['name']

def qualifiers(x):return {} if isinstance(x,str) else {k:v for k,v in x.items() if k!='name'}

def documents(path):
 for d in yaml.safe_load_all(path.read_text()):
  if not d:continue
  yield d

def load_catalogs():
 receipts=json.loads((ROOT/'provenance/public_sources.json').read_text())['files']
 cats=collections.defaultdict(lambda:{'metrics':[],'models':[],'sources':[]})
 start=time.perf_counter_ns()
 for r in receipts:
  p=ROOT/r['local_path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
  catalog='jaffle_shop' if r['repository'].endswith('jaffle-shop') else r['path'].split('semantic_manifest_yamls/')[1].split('/')[0]
  c=cats[catalog];c['sources'].append({k:r[k] for k in ('repository','commit','path','sha256')})
  for d in documents(p):
   c['metrics'].extend(d.get('metrics',[]));c['models'].extend(d.get('semantic_models',[]))
   if 'metric' in d:c['metrics'].append(d['metric'])
   if 'semantic_model' in d:c['models'].append(d['semantic_model'])
 for c in cats.values():
  explicit={m['name'] for m in c['metrics']}
  for sm in c['models']:
   for measure in sm.get('measures',[]):
    if measure.get('create_metric') and measure['name'] not in explicit:
     c['metrics'].append({'name':measure['name'],'type':'simple','type_params':{'measure':measure['name']},'_auto':True});explicit.add(measure['name'])
 return dict(cats),(time.perf_counter_ns()-start)/1e6

def projection(c):
 mids={m['name'] for m in c['metrics']};assert len(mids)==len(c['metrics']),'duplicate metric definitions'
 measures=collections.defaultdict(list)
 for sm in c['models']:
  for v in sm.get('measures',[]):measures[v['name']].append('measure:'+sm['name']+'.'+v['name'])
 targets={};issues=[]
 for m in c['metrics']:
  refs=[];typ=m['type'].lower();params=m.get('type_params',{})
  if typ in ('simple','cumulative'):refs.append(('measure_of',params['measure'],'measure'))
  elif typ=='ratio':refs.extend([('numerator_of',params['numerator'],'metric'),('denominator_of',params['denominator'],'metric')])
  elif typ=='derived':refs.extend(('depends_on',v,'metric') for v in params['metrics'])
  elif typ=='conversion':
   q=params['conversion_type_params'];refs.extend([('base_measure_of',q['base_measure'],'measure'),('conversion_measure_of',q['conversion_measure'],'measure')])
  else:issues.append({'metric':m['name'],'reason':'unsupported type '+typ});continue
  edges=[];valid=True
  for role,ref,targettype in refs:
   n=name(ref)
   if targettype=='metric':poss=['metric:'+n] if n in mids else []
   else:poss=measures[n]
   if len(poss)!=1:valid=False;issues.append({'metric':m['name'],'reason':'nonunique/missing '+targettype,'reference':n,'candidates':poss});continue
   edges.append({'role':role,'target':poss[0],'qualifiers':qualifiers(ref)})
  if valid:targets[m['name']]=ordered(edges)
 return targets,issues,dict(measures),sorted(mids)

def mutations(catalog,c,targets,registry):
 out=[];metric_lookup={m['name']:m for m in c['metrics']}
 for mid,gold in sorted(targets.items()):
  base={'catalog_id':catalog,'metric_id':mid,'contract':{'metric':copy.deepcopy(metric_lookup[mid]),'complete':True},'registry':registry}
  for i,e in enumerate(gold):
   for kind in ('delete','wrong_target','wrong_role','strip_qualifiers'):
    cur=copy.deepcopy(gold)
    if kind=='delete':cur.pop(i)
    elif kind=='wrong_target':
     type_=e['target'].split(':',1)[0];pool=['metric:'+n for n in registry['metrics']] if type_=='metric' else [x for vs in registry['measures'].values() for x in vs]
     alternatives=[x for x in sorted(pool) if x!=e['target']]
     if not alternatives:continue
     cur[i]['target']=alternatives[0]
    elif kind=='wrong_role':cur[i]['role']='depends_on' if e['role']!='depends_on' else 'numerator_of'
    else:
     if not e['qualifiers']:continue
     cur[i]['qualifiers']={}
    assert ordered(cur)!=gold
    out.append(dict(base,task_id=f'{catalog}/{mid}/{i}/{kind}',mutation=kind,mutated_binding_index=i,current_edges=ordered(cur),gold_edges=gold))
 return out


def main():
 global ROOT
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--root',type=Path,default=ROOT)
 parser.add_argument('--output-dir',type=Path,required=True)
 args=parser.parse_args(); ROOT=args.root.resolve(); out=args.output_dir.resolve()
 out.mkdir(parents=True,exist_ok=True)
 cats,parse_ms=load_catalogs(); tasks=[]; clean=[]; counts=[];issues=[]
 for cid,c in sorted(cats.items()):
  targets,errs,measures,mids=projection(c);issues.extend(dict(e,catalog_id=cid) for e in errs)
  registry={'metrics':mids,'measures':measures}
  tasks.extend(mutations(cid,c,targets,registry))
  lookup={m['name']:m for m in c['metrics']}
  for mid,gold in targets.items():
   clean.append({'catalog_id':cid,'metric_id':mid,'contract':{'metric':lookup[mid],'complete':True},'registry':registry,'current_edges':gold,'gold_edges':gold,'task_id':cid+'/'+mid+'/clean','mutation':'clean'})
  counts.append({'catalog_id':cid,'source_files':len(c['sources']),'declarations':len(c['metrics']),'eligible_metrics':len(targets),'bindings':sum(map(len,targets.values())),'unresolved':len(errs)})
 assert not issues,issues
 assert len(tasks)==696 and len(clean)==158 and sum(x['bindings'] for x in counts)==210
 for filename,rows in [('tasks.jsonl',tasks),('clean_controls.jsonl',clean)]:
  payload=''.join(json.dumps(t,sort_keys=True)+'\n' for t in rows).encode()
  expected=next(x for x in json.loads((ROOT/'provenance/input_contract.json').read_text())['files'] if Path(x['path']).name==filename)
  assert hashlib.sha256(payload).hexdigest()==expected['sha256'],('PINNED_TASK_REGENERATION_MISMATCH',filename)
  (out/filename).write_bytes(payload)
 receipt={'schema':'audit-pinned-source-regeneration','source_count':29,'mutations':len(tasks),'clean_controls':len(clean),'counts':counts,'byte_exact_to_frozen_inputs':True,'parser':{'package':'PyYAML','version':yaml.__version__},'parse_wall_ms_new_run':parse_ms,'scope':'Explicit declaration projection and deterministic synthetic mutations; not independent natural gold or upstream SQL semantics.'}
 (out/'regeneration_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
