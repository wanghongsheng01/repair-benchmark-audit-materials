#!/usr/bin/env python3
"""Restore the pinned BART engine from a git checkout and verify every pinned file hash.
Usage: git clone https://github.com/dbunibas/BART bart_src && git -C bart_src checkout 354f503f401d5360e9a6957f4edd096d3dc413f6
       python3 restore_from_git.py --checkout bart_src"""
import argparse, hashlib, json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--checkout', type=Path, required=True); a = ap.parse_args()
    m = json.loads((ROOT / 'source_manifest.json').read_text()); dest = ROOT / 'upstream_local/source'
    if dest.exists(): raise SystemExit('refuse to overwrite ' + str(dest))
    dest.mkdir(parents=True)
    for part in ['Bart_Engine', 'lib']:
        shutil.copytree(a.checkout / part, dest / part)
    for part in ['LICENSE', 'README.md']:
        shutil.copy2(a.checkout / part, dest / part)
    bad = [r['path'] for r in m['files'] + m['dependency_jars'] + m['build_sources'] if hashlib.sha256((dest / r['path']).read_bytes()).hexdigest() != r['sha256']]
    if bad: raise SystemExit('hash mismatch: ' + ', '.join(bad))
    print('RESTORE_OK: all pinned files verified')
if __name__ == '__main__': main()
