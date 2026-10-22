#!/usr/bin/env python3
"""Optional native compilation; no installation, network or generator execution."""
from pathlib import Path
import argparse,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--java-home',type=Path,required=True);args=ap.parse_args()
 src=ROOT/'upstream_local/source';m=json.loads((ROOT/'source_manifest.json').read_text())
 for rec in m['files']+m['dependency_jars']+m['build_sources']:
  if hashlib.sha256((src/rec['path']).read_bytes()).hexdigest()!=rec['sha256']:raise ValueError('upstream hash mismatch '+rec['path'])
 build=ROOT/'native_build';build.mkdir(exist_ok=True);classes=build/'classes';classes.mkdir(exist_ok=True)
 sources=sorted((src/'Bart_Engine/src').rglob('*.java'))+[ROOT/x for x in ['BartAuditHarness.java','BartAppliedAuditHarness.java','BartScorerProbe.java']]
 cp=str(src/'lib/*');cmd=[str(args.java_home/'bin/javac'),'-proc:none','-encoding','UTF-8','-source','8','-target','8','-cp',cp,'-d',str(classes)]+list(map(str,sources))
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(build/'compile.log').write_bytes(p.stdout)
 if p.returncode:raise SystemExit(p.stdout.decode())
 print('COMPILE_OK: '+str(len(sources))+' sources; no generator executed')
if __name__=='__main__':main()
