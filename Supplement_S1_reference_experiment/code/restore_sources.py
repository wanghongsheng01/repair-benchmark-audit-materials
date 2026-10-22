#!/usr/bin/env python3
"""Restore the 29 pinned YAML inputs from an authorized local cache or personal GitHub identity.
No dependency install, upstream code execution, or credential persistence occurs.
"""
import argparse,base64,hashlib,json,os,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs): raise RuntimeError('REDIRECT_REJECTED')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,default=ROOT)
 mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--cache',type=Path,help='Existing authorized source cache containing jaffle-shop/ and metricflow/')
 mode.add_argument('--github-user',help='Explicit personal GitHub username; reads AUDIT_GITHUB_TOKEN environment variable')
 args=p.parse_args();root=args.root.resolve();manifest=json.loads((root/'provenance/public_sources.json').read_text())
 opener=urllib.request.build_opener(NoRedirect)
 def get(url):
  req=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['AUDIT_GITHUB_TOKEN'],'Accept':'application/vnd.github+json'})
  with opener.open(req,timeout=30) as res:
   if res.url!=url:raise RuntimeError('URL_MISMATCH')
   return json.load(res)
 if args.github_user:
  if get('https://api.github.com/user').get('login')!=args.github_user:raise RuntimeError('PERSONAL_IDENTITY_MISMATCH')
 records=[]
 for row in manifest['files']:
  if args.cache:raw=(args.cache/row['repository'].split('/')[1]/row['path']).read_bytes()
  else:
   response=get(row['api_url'])
   if response.get('type')!='file' or response.get('encoding')!='base64' or response.get('size',1048577)>1048576:raise RuntimeError('INVALID_SOURCE_RESPONSE')
   raw=base64.b64decode(response['content'])
  if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('SOURCE_HASH_MISMATCH: '+row['path'])
  raw.decode('utf8');dest=root/row['local_path'];dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists() and dest.read_bytes()!=raw:raise RuntimeError('REFUSE_OVERWRITE_DIFFERENT_SOURCE')
  dest.write_bytes(raw);records.append({'path':row['local_path'],'sha256':row['sha256'],'verified':True})
 receipt={'schema':'audit-source-restore','mode':'authorized-local-cache' if args.cache else 'personal-authenticated-github','restored':len(records),'files':records,'source_code_executed':False,'license_note':'Restore does not confer redistribution permission. Preserve upstream terms; original YAML excluded from delivery.'}
 out=root/'results/source_restore_receipt.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'restored':len(records),'all_pinned_hashes_match':True}))
if __name__=='__main__':main()
