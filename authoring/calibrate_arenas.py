#!/usr/bin/env python3
"""Fast deterministic calibration audit for the nine batch arenas."""
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"templates"/"arena_kit"))
import arena_kit as k

def main():
    rows=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        for task in (x for x in k.TASKS if x!="lightcycle"):
            c=k.case(task,90210,2);ip=td/f"{task}.json";op=td/f"{task}-out.json";ip.write_text(json.dumps(c))
            subprocess.run([sys.executable,str(ROOT/"authoring"/"arena_reference.py"),task,str(ip),str(op)],check=True)
            ref=k.score(task,c,json.loads(op.read_text()))["quality"]
            if task=="poisson":
                sys.path.insert(0,str(ROOT/"authoring"));import trusted_poisson
                ref=trusted_poisson.score(c,json.loads(op.read_text()))["quality"]
                base=trusted_poisson.score(c,k.baseline(task,c))["quality"]
            else:base=k.score(task,c,k.baseline(task,c))["quality"]
            assert 0<=base<=1 and 0<=ref<=1 and ref+1e-8>=base,(task,base,ref)
            rows.append({"task":task,"malformed":0.0,"baseline":base,"frontier":ref})
    print(json.dumps(rows,indent=2))
if __name__=="__main__":main()
