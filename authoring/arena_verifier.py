"""Generic trusted evaluator for the deterministic visual arenas."""

from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"templates"/"arena_kit"))
import arena_kit as kit  # noqa: E402

import trusted_poisson
import control_verifier

NATIVE_BATCH={
    "poisson":("run_case.sh",True),
    "pathtracer":("render.sh",False),
    "mpm":("simulate.sh",True),
    "topology":("optimize.sh",True),
    "smoke":("control.sh",False),
    "softrobot":("design.sh",False),
    "inverse_render":("recover.sh",True),
}


def native_command(task: str, inp: Path, out: Path) -> tuple[list[str], Path | None]:
    if task not in NATIVE_BATCH:
        return [sys.executable,"solve.py",str(inp),str(out)],None
    script,directory_output=NATIVE_BATCH[task]
    if directory_output:
        target=out.parent/(out.stem+"-files");target.mkdir()
        return ["bash",script,str(inp),str(target)],target/"result.json"
    if task=="pathtracer":
        return ["bash",script,str(inp),str(out),str(out.with_suffix(".metrics.json"))],None
    return ["bash",script,str(inp),str(out)],None


def invoke(task:str,sub:Path,inp:Path,out:Path,timeout:float=12)->tuple[dict[str,Any]|None,str,float]:
    start=time.monotonic()
    try:
        command,directory_result=native_command(task,inp,out)
        p=subprocess.run(command,cwd=sub,
            capture_output=True,text=True,timeout=timeout,check=False,
            env={**os.environ,"PYTHONHASHSEED":"0"})
        if directory_result is not None and directory_result.is_file():
            out.write_bytes(directory_result.read_bytes())
        elapsed=time.monotonic()-start
        if p.returncode or not out.is_file():
            return None,f"exit={p.returncode}; stderr={p.stderr[-600:]}",elapsed
        return json.loads(out.read_text()),"",elapsed
    except Exception as exc:
        return None,str(exc),time.monotonic()-start


def lightcycle_quality(sub:Path,c:dict[str,Any],evidence:Path)->tuple[float,dict[str,Any]]:
    # A persistent bot receives the complete board and must return U/D/L/R as JSONL.
    cmd=["bash","bot.sh"]
    try: proc=subprocess.Popen(cmd,cwd=sub,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,text=True,bufsize=1)
    except OSError as exc: return 0.,{"error":str(exc)}
    rng=__import__("random").Random(c["seed"]); wins=draws=illegal=0; replays=[]
    dirs={"U":(0,-1),"D":(0,1),"L":(-1,0),"R":(1,0)}
    for match in range(c["matches"]):
        w,h=c["width"],c["height"]; me=[2,h//2]; foe=[w-3,h//2]
        occupied={tuple(me),tuple(foe)}; frames=[]
        for turn in range(w*h):
            state={"board":[w,h],"you":me,"opponents":[foe],"occupied":[list(x) for x in occupied],"turn":turn}
            try:
                assert proc.stdin and proc.stdout
                proc.stdin.write(json.dumps(state)+"\n"); proc.stdin.flush()
                line=proc.stdout.readline(); move=str(json.loads(line).get("move",""))
            except Exception: move=""
            legal=[]
            for name,(dx,dy) in dirs.items():
                q=(me[0]+dx,me[1]+dy)
                if 0<=q[0]<w and 0<=q[1]<h and q not in occupied: legal.append(name)
            if move not in legal:
                illegal+=1; break
            dx,dy=dirs[move]; me=[me[0]+dx,me[1]+dy]
            flegal=[]
            for name,(ax,ay) in dirs.items():
                q=(foe[0]+ax,foe[1]+ay)
                if 0<=q[0]<w and 0<=q[1]<h and q not in occupied and q!=tuple(me): flegal.append(name)
            if not flegal: wins+=1; break
            # Fixed opponent mixes greedy pursuit and seeded unpredictability.
            fm=min(flegal,key=lambda z: abs(foe[0]+dirs[z][0]-me[0])+abs(foe[1]+dirs[z][1]-me[1])+.2*rng.random())
            ax,ay=dirs[fm]; foe=[foe[0]+ax,foe[1]+ay]
            if tuple(foe)==tuple(me): draws+=1; break
            occupied|={tuple(me),tuple(foe)}
            if match==0: frames.append({"you":me[:],"foe":foe[:],"occupied":[list(x) for x in occupied]})
        else: draws+=1
        if match==0: replays=frames
    proc.kill()
    (evidence/"tournament.json").write_text(json.dumps({"wins":wins,"draws":draws,"illegal":illegal,"replay":replays},indent=2))
    q=max(0.,(wins+.35*draws)/c["matches"]-.08*illegal)
    return min(1.,q),{"wins":wins,"draws":draws,"illegal":illegal}


def result(cid:str,score:float,summary:str,measure:dict[str,Any],evidence:list[str]=[])->dict[str,Any]:
    score=max(0,min(1,score))
    status="passed" if score==1 else ("failed" if score==0 else "partial")
    return {"id":cid,"status":status,"score":score,
            "summary":summary,"measurements":measure,"evidence":evidence}


def main()->None:
    p=argparse.ArgumentParser(); p.add_argument("--task",required=True); p.add_argument("--context",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    ctx=json.loads(a.context.read_text()); sub=Path(ctx["submission_dir"]); art=Path(ctx["artifact_dir"]); ev=Path(ctx["evidence_dir"]); private=Path(ctx["private_dir"])
    specs=yaml.safe_load((private/"checks.yaml").read_text())["checks"]; ids=[x["id"] for x in specs]
    report=(sub/"REPORT.md").is_file(); artifact_ok=(art/"preview.png").is_file() and (art/"result.json").is_file()
    qualities=[]; details=[]; elapsed=0.; successful=True
    for item in json.loads((private/"hidden_inputs"/"cases.json").read_text()):
        c=kit.case(a.task,int(item["seed"]),int(item["difficulty"])); cp=ev/f'{item["name"]}-input.json'; op=ev/f'{item["name"]}-output.json'; pp=ev/f'{item["name"]}-preview.png'
        public_case=dict(c)
        if a.task=="inverse_render":
            public_case.pop("truth",None)
        cp.write_text(json.dumps(public_case))
        if a.task in {"multipole","world_mpc"}:
            q,m=control_verifier.quality(a.task,sub,c);out={"controller":"interactive"};err=""
        elif a.task=="lightcycle":
            q,m=lightcycle_quality(sub,c,ev); out={"policy":"interactive"}; err=""
        else:
            out,err,sec=invoke(a.task,sub,cp,op); elapsed+=sec
            if out is None: q=0.;m={"error":err};successful=False;out={}
            else:
                m=trusted_poisson.score(c,out) if a.task=="poisson" else kit.score(a.task,c,out)
                q=float(m.get("quality",0))
                kit.render(a.task,c,out,pp)
        qualities.append(q);details.append({"case":item["name"],"quality":q,**m})
    quality=float(__import__("math").prod(max(1e-6,x) for x in qualities)**(1/max(1,len(qualities))))
    (ev/"metrics.json").write_text(json.dumps({"objective_score":quality,"cases":details,"elapsed_seconds":elapsed},indent=2))
    checks=[]
    for i,cid in enumerate(ids):
        if i==0: checks.append(result(cid,float(successful and (artifact_ok or a.task=="lightcycle")),"Candidate protocol and canonical artifacts",{"successful":successful,"artifacts":artifact_ok},["metrics.json"]))
        elif i==len(ids)-1: checks.append(result(cid,float(report),"Human review report present",{"report":report}))
        else:
            adj=quality
            if "efficiency" in cid or "throughput" in cid: adj=quality*min(1,12/max(.1,elapsed))
            checks.append(result(cid,adj,f"Hidden {a.task} metric",{"objective_score":quality,"cases":details},["metrics.json"]))
    a.output.write_text(json.dumps({"schema_version":1,"checks":checks,"warnings":[]},indent=2))
if __name__=="__main__": main()
