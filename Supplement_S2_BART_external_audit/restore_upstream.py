#!/usr/bin/env python3
"""Restore pinned upstream bytes; never compile or execute downloaded content."""
import argparse,hashlib,json,urllib.request,zipfile,io
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();group=ap.add_mutually_exclusive_group(required=True);group.add_argument('--download',action='store_true');group.add_argument('--archive',type=Path);args=ap.parse_args()
 m=json.loads((ROOT/'source_manifest.json').read_text());dest=ROOT/'upstream_local/source'
 if dest.exists():raise SystemExit('Refuse overwrite existing upstream source')
 data=urllib.request.urlopen(m['source_archive_url'],timeout=120).read() if args.download else args.archive.read_bytes()
 if hashlib.sha256(data).hexdigest()!=m['source_archive_sha256']:raise SystemExit('Source archive checksum mismatch')
 z=zipfile.ZipFile(io.BytesIO(data));prefix='BART-'+m['commit']+'/'
 for info in z.infolist():
  if not info.filename.startswith(prefix):raise ValueError('unexpected archive prefix')
  rel=Path(info.filename[len(prefix):])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe archive path')
  if not rel.parts or rel.parts[0] not in ['Bart_Engine','lib','LICENSE','README.md']:continue
  if (info.external_attr>>16)&0o170000==0o120000:raise ValueError('symlink archive member refused')
  path=dest/rel
  if info.is_dir():path.mkdir(parents=True,exist_ok=True)
  else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(info))
 for rec in m['files']+m['dependency_jars']+m['build_sources']:
  path=dest/rec['path']
  if hashlib.sha256(path.read_bytes()).hexdigest()!=rec['sha256']:raise ValueError('restored file checksum mismatch '+rec['path'])
 print('RESTORE_OK: pinned source and dependency hashes verified; nothing executed')
if __name__=='__main__':main()
