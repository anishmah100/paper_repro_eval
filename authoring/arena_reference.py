#!/usr/bin/env python3
"""Private calibration frontier; not copied to contestant workspaces."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"templates"/"arena_kit"),str(ROOT/"authoring")]
import arena_kit as k
import trusted_poisson


def frontier(task,c):
    if task=="poisson": return {"image":trusted_poisson.solve(c).tolist()}
    if task=="pathtracer": return {"image":k.render_scene(c["spheres"],c["width"],c["height"]).tolist()}
    if task=="inverse_render": return {"objects":c["truth"]}
    if task=="softrobot":
        m=np.zeros((5,8));m[1:4,1:7]=1
        best=max(([k.score(task,c,{"morphology":m.tolist(),"frequency":f,"phase_gradient":p})["quality"],f,p]
                 for f in np.linspace(.5,5,20) for p in np.linspace(.2,2.8,20)))
        return {"morphology":m.tolist(),"frequency":best[1],"phase_gradient":best[2]}
    if task=="mpm":
        params={"jelly":[.18,.3],"snow":[.5,.1],"water":[0,.05]}[c["material"]]
        return {"frames":k.sim_mpm(c,params).tolist()}
    if task=="multipole":
        rng=np.random.default_rng(c["seed"]);base=k.baseline(task,c);choices=[base]
        for _ in range(500): choices.append({"gains":rng.uniform(-4,20,2+2*c["poles"]).tolist()})
        return max(choices,key=lambda x:k.score(task,c,x)["quality"])
    if task=="topology":
        h,w=c["height"],c["width"];yy,xx=np.mgrid[:h,:w];ly=np.mean([z[1] for z in c["loads"]])
        ideal=np.exp(-((yy-(ly+(h/2-ly)*(1-xx/(w-1))))/(2+h*.08))**2)
        d=ideal*(c["volume"]/ideal.mean());d=np.clip(d,0,1);d[:,0]=np.maximum(d[:,0],.3)
        choices=[{"density":d.tolist()},k.baseline(task,c)]
        return max(choices,key=lambda x:k.score(task,c,x)["quality"])
    if task=="smoke":
        target=np.array(c["target"]);ty,tx=np.unravel_index(np.argmax(target),target.shape);sy,sx=c["source"]
        choices=[]
        for ux in np.linspace(-1,1,13):
            for uy in np.linspace(-1,1,13):choices.append({"controls":[[float(ux),float(uy)]]*c["steps"]})
        return max(choices,key=lambda x:k.score(task,c,x)["quality"])
    if task=="world_mpc":
        base=k.baseline(task,c);a0=np.array(base["actions"])
        def objective(z):
            acts=np.clip(a0+np.asarray(z).reshape(-1,2),-1,1)
            return -k.score(task,c,{"actions":acts.tolist()})["quality"]
        # Optimize eight piecewise-constant corrections, expanded across the horizon.
        def obj8(z):
            corr=np.repeat(np.asarray(z).reshape(8,2),int(np.ceil(c["steps"]/8)),axis=0)[:c["steps"]]
            return objective(corr.ravel())
        z=minimize(obj8,np.zeros(16),method="Powell",options={"maxiter":80}).x
        corr=np.repeat(z.reshape(8,2),int(np.ceil(c["steps"]/8)),axis=0)[:c["steps"]]
        return {"actions":np.clip(a0+corr,-1,1).tolist()}
    return k.baseline(task,c)


def main():
    p=argparse.ArgumentParser();p.add_argument("task");p.add_argument("input",type=Path);p.add_argument("output",type=Path);a=p.parse_args()
    c=json.loads(a.input.read_text());a.output.write_text(json.dumps(frontier(a.task,c)))
if __name__=="__main__":main()
