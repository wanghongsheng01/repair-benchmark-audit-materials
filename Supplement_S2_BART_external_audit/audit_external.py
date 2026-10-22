#!/usr/bin/env python3
"""Independent, standard-library audit of saved native BART observations.
No BART code, study repairer, diff-derived event labels, network or randomness.
"""
from pathlib import Path
import argparse,csv,hashlib,json,copy

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stable_hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def unique_object(pairs):
 out={}
 for key,value in pairs:
  if key in out:raise ValueError('duplicate JSON key: '+key)
  out[key]=value
 return out
def read(p):return json.loads(p.read_text(),object_pairs_hook=unique_object)
def unexplained_keys(clean,dirty,event_refs):
 require(clean.keys()==dirty.keys(),'control identity/schema drift')
 return [k for k in clean if clean[k]!=dirty[k] and k[1]+'.'+k[2] not in event_refs]
def require(x,msg):
 if not x:raise ValueError(msg)
def flat(snapshot):
 out={}
 for table,rows in snapshot.items():
  ids=set()
  for row in rows:
   oid=row['oid'];require(isinstance(oid,str) and oid not in ids,'duplicate/invalid OID');ids.add(oid)
   for attr,value in row['cells'].items():
    require(value['null_reference'] is False and value['runtime_class']=='speedy.model.database.ConstantValue' and isinstance(value['text'],str),'unsupported null/nontext CSV cell')
    key=(table,oid,attr);require(key not in out,'duplicate cell');out[key]=value['text']
 return out
def csv_matches_snapshot(path,snapshot,table):
 with path.open(newline='') as f:rows=list(csv.reader(f,strict=True))
 require(bool(rows),'missing CSV header');head=rows[0];require(len(head)==len(set(head)),'duplicate CSV header')
 expected=snapshot[table];require(len(rows)-1==len(expected),'row count mismatch')
 for actual,origin in zip(rows[1:],expected):
  require(set(head)==set(origin['cells']),'CSV schema mismatch')
  require(len(actual)==len(head),'CSV width mismatch')
  require(actual==[origin['cells'][h]['text'] for h in head],'CSV order/value not corroborated by native sidecar')
 return rows

def audit_case(case,out):
 clean_snapshot=read(case/'clean_snapshot.json');dirty_snapshot=read(case/'dirty_crosswalk_before_export.json')
 require(dirty_snapshot==read(case/'dirty_crosswalk_after_export.json'),'unstable dirty iterator/order')
 require(clean_snapshot==read(case/'clean_crosswalk_after_export.json'),'unstable clean iterator/order')
 clean=flat(clean_snapshot);dirty=flat(dirty_snapshot);require(clean.keys()==dirty.keys(),'identity/schema drift')
 csv_clean={};csv_dirty={};positional=0;reordered_rows=0
 for table in clean_snapshot:
  csv_clean[table]=csv_matches_snapshot(case/f'clean_{table}.csv',clean_snapshot,table)
  csv_dirty[table]=csv_matches_snapshot(case/f'dirty_{table}.csv',dirty_snapshot,table)
  require(csv_clean[table][0]==csv_dirty[table][0],'schema order drift')
  positional+=sum(a!=b for r,s in zip(csv_clean[table][1:],csv_dirty[table][1:]) for a,b in zip(r,s))
  reordered_rows+=sum(a['oid']!=b['oid'] for a,b in zip(clean_snapshot[table],dirty_snapshot[table]))
 refkeys={}
 for key in clean:
  ref=key[1]+'.'+key[2];require(ref not in refkeys,'ambiguous event identity across tables');refkeys[ref]=key
 events=read(case/'events_native.json');byref={}
 for e in events:
  require(all(e[v]['null_reference'] is False and e[v]['runtime_class']=='speedy.model.database.ConstantValue' and isinstance(e[v]['text'],str) for v in ['original','new']),'unsupported event value type')
  ref=e['cell_ref'];require(ref not in byref,'duplicate event identity');require(ref in refkeys,'unresolved event identity');byref[ref]=e
  require(e['oid']+'.'+e['attribute']==ref,'event identity inconsistent')
  require(e['original']['text']==clean[refkeys[ref]],'event original differs from independent clean snapshot')
 with (case/'events_native.csv').open(newline='') as f:csv_events=list(csv.reader(f,strict=True))
 csv_refs={};documented_bad=0;implementation_bad=0
 for r in csv_events:
  require(len(r)==3,'unrecognized event CSV schema');ref=r[0];require(ref not in csv_refs,'duplicate exported event');require(ref in byref,'unrecorded exported event');csv_refs[ref]=r
  key=refkeys[ref];documented_bad+=(r[1]!=clean[key] or r[2]!=dirty[key])
  implementation_bad+=(r[1]!=dirty[key] or r[2]!=clean[key])
 require(set(csv_refs)=={r for r,e in byref.items() if e['exported']},'event export filter mismatch')
 records=[];unexplained=unexplained_keys(clean,dirty,set(byref));unrealized=[];wrong_value=[];noop=[]
 for key in sorted(clean):
  ref=key[1]+'.'+key[2];e=byref.get(ref);changed=clean[key]!=dirty[key]
  if e is not None:
   if e['new']['text']==clean[key]:noop.append(key)
   elif not changed:unrealized.append(key)
   if e['new']['text']!=dirty[key]:wrong_value.append(key)
  records.append({'case_id':case.name,'table':key[0],'oid':key[1],'attribute':key[2],'clean':clean[key],'dirty':dirty[key],'changed':changed,'authorized':e is not None,'expected_new':e['new']['text'] if e else clean[key],'event_basis':'events_native.json; observed native ICellChange, not diff' if e else 'absence from native ICellChange records'})
 require(read(case/'source_before.json')==read(case/'source_after.json'),'authoritative source changed')
 with (out/(case.name+'_cells.jsonl')).open('w') as f:
  for row in records:f.write(json.dumps(row,sort_keys=True)+'\n')
 # Author-defined control interventions are separate from external cases.
 non_target=next(k for k in sorted(clean) if k[1]+'.'+k[2] not in byref)
 controls=[{'control_id':case.name+'/clean_identity','kind':'correct negative wrapper','expected_unexplained':0,'actual_unexplained':len(unexplained_keys(clean,copy.deepcopy(clean),set())),'input_sha256':stable_hash(clean_snapshot),'event_basis':'empty event list; clean snapshot paired with identical copy'},
 {'control_id':case.name+'/one_unrecorded_cell','kind':'positive sensitivity wrapper','base_snapshot':'dirty_crosswalk_before_export.json','base_sha256':sha(case/'dirty_crosswalk_before_export.json'),'intervention':{'table':non_target[0],'oid':non_target[1],'attribute':non_target[2],'old':dirty[non_target],'new':dirty[non_target]+'::AUDIT_SENSITIVITY::'},'expected_unexplained':1,'actual_unexplained':len(unexplained_keys(clean,{k:dirty[k]+('::AUDIT_SENSITIVITY::' if k==non_target else '') for k in dirty},set(byref))),'event_basis':'unchanged native event identities'}]
 for c in controls:require(c['actual_unexplained']==c['expected_unexplained'],'control failed')
 # Actual probe inputs: clean value comes from independent before-state.
 if csv_events:
  with (out/(case.name+'_snapshot_probe.csv')).open('w',newline='') as f:
   w=csv.writer(f);w.writerows((r,clean[refkeys[r]]) for r in sorted(csv_refs))
  with (out/(case.name+'_wiki_probe.csv')).open('w',newline='') as f:
   w=csv.writer(f);w.writerows((r,csv_refs[r][1]) for r in sorted(csv_refs))
 row={'case_id':case.name,'rows':sum(len(r) for r in clean_snapshot.values()),'cells':len(clean),'events':len(events),'realized_changes':sum(clean[k]!=dirty[k] for k in clean),'unexplained_changes':len(unexplained),'unrealized_nonnoop_events':len(unrealized),'event_value_mismatches':len(wrong_value),'noop_events':len(noop),'exported_events':len(csv_events),'wiki_contract_mismatches':documented_bad,'implementation_contract_mismatches':implementation_bad,'reordered_rows':reordered_rows,'positional_cell_differences':positional,'source_preserved':True,'eligible_applied_pair':True,'execution_basis':'A2 exploratory native APriori apply/export, one run','input_hashes':{p.name:sha(p) for p in sorted(case.iterdir()) if p.is_file()}}
 return row,controls

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run-dir',type=Path,default=Path(__file__).resolve().parent/'native_applied_01');ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'audit_results');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 manifest=read(args.run_dir/'run_manifest.json');require(len(manifest)==4,'expected all four fixed cases');require(len({r['case_id'] for r in manifest})==4,'duplicate case')
 expected={'employees-egtask':'employees/employees-egtask.xml','employees-random-egtask':'employees/employees-random-egtask.xml','employees-symmetrictest-egtask':'employees/employees-symmetrictest-egtask.xml','synthetic_01-egtask':'misc/synthetic_01-egtask.xml'}
 require({r['case_id'] for r in manifest}==set(expected),'unexpected fixed case set')
 root=Path(__file__).resolve().parent; provenance=read(root/'source_manifest.json');pins={r['path']:r['sha256'] for r in provenance['files']}
 for rec in manifest:
  require(read(args.run_dir/rec['case_id']/'run_receipt.json')==rec,'receipt differs from manifest')
  rel=expected[rec['case_id']];require(rec['upstream_task']==rel,'upstream task mapping mismatch')
  require(rec['task_sha256']==pins['Bart_Engine/misc/resources/'+rel],'source XML hash mismatch')
  require(rec['harness_sha256']==sha(root/'BartAppliedAuditHarness.java'),'applied harness hash mismatch')
  require(rec['runtime_adaptation']=={'applyCellChanges':True,'exportCleanDB':True,'exportDirtyDB':True,'exportCellChanges':True,'export_paths':'isolated case directory'},'unexpected applied configuration')
 rows=[];controls=[];excluded=[]
 for rec in manifest:
  if not rec['completed']:excluded.append({'case_id':rec['case_id'],'reason':'native execution failed','receipt':rec});continue
  row,ctrl=audit_case(args.run_dir/rec['case_id'],args.out);rows.append(row);controls+=ctrl
 summary={'schema':'audit-bart-external-audit','scope':'A2 exploratory; all four shipped main-memory tasks adapted only to enable native apply/export','planned_cases':4,'eligible_cases':len(rows),'excluded':excluded,'total_rows':sum(r['rows'] for r in rows),'total_cells':sum(r['cells'] for r in rows),'native_events':sum(r['events'] for r in rows),'unexplained_changes':sum(r['unexplained_changes'] for r in rows),'unrealized_nonnoop_events':sum(r['unrealized_nonnoop_events'] for r in rows),'event_value_mismatches':sum(r['event_value_mismatches'] for r in rows),'zero_event_native_cases':sum(r['events']==0 for r in rows),'positional_false_alarm_native_zero_event_cases':sum(r['events']==0 and r['positional_cell_differences']>0 for r in rows),'wiki_contract_mismatches':sum(r['wiki_contract_mismatches'] for r in rows),'implementation_contract_mismatches':sum(r['implementation_contract_mismatches'] for r in rows),'wrapper_controls_passed':len(controls),'checker_sha256':sha(Path(__file__)),'native_run_manifest_sha256':sha(args.run_dir/'run_manifest.json')}
 (args.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(args.out/'all_cases.json').write_text(json.dumps(rows,indent=2)+'\n');(args.out/'controls.json').write_text(json.dumps(controls,indent=2)+'\n')
 cols=[k for k in rows[0] if k!='input_hashes'] if rows else []
 with (args.out/'all_cases.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,cols);w.writeheader();w.writerows({k:r[k] for k in cols} for r in rows)
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
