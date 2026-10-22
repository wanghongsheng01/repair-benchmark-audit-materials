import sys, os, json, runpy
from pathlib import Path
trace=[]
def guard(event,args):
    if event == "open" and args and isinstance(args[0],(str,bytes,os.PathLike)):
        path=str(Path(os.fsdecode(args[0])).resolve())
        trace.append(path)
        if path == "<home>" or path.startswith("<home>/"):
            raise PermissionError("original user tree denied: "+path)
    if event.startswith("socket.") or event == "subprocess.Popen":
        raise PermissionError("network/subprocess denied: "+event)
sys.addaudithook(guard)
script=sys.argv[1]
sys.argv=sys.argv[1:]
sys.path.insert(0,str(Path(script).parent))
try:
    runpy.run_path(script,run_name="__main__")
finally:
    Path(os.environ["AUDIT_TRACE_PATH"]).write_text(json.dumps(trace,indent=2))
