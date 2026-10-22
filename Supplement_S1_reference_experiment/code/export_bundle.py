#!/usr/bin/env python3
"""Build portable reviewer ZIP without upstream originals or source-derived task declarations.
The fixed task files are restored byte-exact by generate_public.py after pinned-source recovery.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def eligible(path,root):
 parts=path.relative_to(root).parts
 return path.is_file() and not any(p in ('__pycache__','sources','data','.git') for p in parts) and path.suffix not in ('.pyc','.zip') and path.name!='BUNDLE_MANIFEST.json'
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();root=args.root.resolve();files=[p for p in sorted(root.rglob('*')) if eligible(p,root)]
 manifest={'schema':'audit-public-portable-bundle','upstream_originals_redistributed':False,'source_derived_input_declarations_redistributed':False,'source_recovery':'code/restore_sources.py + code/generate_public.py','files':[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
 args.output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,str(p.relative_to(root)))
  z.writestr('BUNDLE_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'zip':str(args.output),'files':len(files)+1,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'excluded':'All original YAML, all fixed source-derived task files, __pycache__; exact restoration commands included.'},indent=2))
if __name__=='__main__':main()
