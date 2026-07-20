"""Public deterministic simulators and renderers for the visual research arcade.

This module is intentionally shipped to contestants. Hidden seeds are not. A submission may import
anything here; trusted verification calls the same functions in a separate process and treats
candidate files as untrusted claims.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, label
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve

TASKS = (
    "poisson", "multipole", "pathtracer", "mpm", "world_mpc",
    "topology", "lightcycle", "smoke", "softrobot", "inverse_render",
)


def clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def case(task: str, seed: int, difficulty: int = 1) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    base: dict[str, Any] = {"task": task, "seed": seed, "difficulty": difficulty}
    if task == "poisson":
        h = w = 24 + 4 * difficulty
        yy, xx = np.mgrid[:h, :w]
        source = np.stack([
            .35 + .45 * np.sin((xx + seed % 7) / 4),
            .35 + .4 * np.cos((yy + seed % 5) / 5),
            .25 + .6 * (xx / w) * (yy / h),
        ], axis=-1)
        target = np.stack([.15 + .65 * xx / w, .2 + .55 * yy / h, .55 + .15*np.sin(xx/3)], -1)
        cx, cy = w * (.45 + .08*rng.normal()), h * (.5 + .08*rng.normal())
        mask = ((xx-cx)**2/(.22*w)**2 + (yy-cy)**2/(.28*h)**2) < 1
        base |= {"source": source.clip(0,1).tolist(), "target": target.clip(0,1).tolist(),
                 "mask": mask.astype(int).tolist()}
    elif task == "multipole":
        n = 2 + difficulty
        base |= {"poles": n, "lengths": rng.uniform(.65, 1.25, n).tolist(),
                 "initial_angles": rng.normal(0, .035 + .012*difficulty, n).tolist(),
                 "wind": float(rng.uniform(-.16, .16)), "steps": 360}
    elif task == "pathtracer":
        spheres = []
        for _ in range(2 + difficulty):
            spheres.append([float(rng.uniform(.15,.85)), float(rng.uniform(.2,.72)),
                            float(rng.uniform(.08,.18)), *rng.uniform(.15,.95,3).tolist()])
        base |= {"width": 40, "height": 32, "spheres": spheres,
                 "light": [float(rng.uniform(.2,.8)), float(rng.uniform(.05,.2))]}
    elif task == "mpm":
        n = 32 + 8*difficulty
        pts = np.column_stack([rng.uniform(.25,.55,n), rng.uniform(.55,.82,n)])
        base |= {"positions": pts.tolist(), "material": ["jelly","snow","water"][seed%3],
                 "steps": 70, "dt": .025, "gravity": -1.8}
    elif task == "world_mpc":
        base |= {"state": [float(rng.uniform(.1,.3)), float(rng.uniform(.1,.35)), 0., 0.],
                 "target": [float(rng.uniform(.68,.9)), float(rng.uniform(.65,.9))],
                 "wind": float(rng.uniform(-.05,.05)), "drag": float(rng.uniform(.025,.08)),
                 "steps": 55}
    elif task == "topology":
        h, w = 18 + 2*difficulty, 30 + 3*difficulty
        loads = [[w-1, int(h*(.25+.5*rng.random())), float(rng.uniform(-.35,.35)), -1.0]]
        if difficulty >= 2:
            loads.append([w-1, h//2, .45, -.65])
        base |= {"height": h, "width": w, "volume": .34, "loads": loads}
    elif task == "lightcycle":
        base |= {"width": 17+2*difficulty, "height": 17+2*difficulty, "matches": 12+4*difficulty}
    elif task == "smoke":
        n = 34
        yy, xx = np.mgrid[:n,:n]
        tx, ty = rng.uniform(.25,.75,2)*n
        target = np.exp(-((xx-tx)**2+(yy-ty)**2)/(2*(3.5+difficulty)**2))
        base |= {"size": n, "target": target.tolist(), "steps": 35, "source": [n//2,n-5]}
    elif task == "softrobot":
        base |= {"width": 8, "height": 5, "terrain": rng.uniform(-.06,.09,32).tolist(),
                 "steps": 100, "budget": 22}
    elif task == "inverse_render":
        objs = []
        for _ in range(2+difficulty):
            objs.append([float(rng.uniform(.18,.82)), float(rng.uniform(.2,.8)),
                         float(rng.uniform(.07,.17)), *rng.uniform(.2,.95,3).tolist()])
        base |= {"width": 40, "height": 40, "views": [-.18,0,.23], "truth": objs}
        base["observations"] = [render_scene(objs, 40, 40, v).tolist() for v in base["views"]]
    else:
        raise ValueError(task)
    return base


def poisson_residual(c: dict[str, Any], image: np.ndarray) -> float:
    src=np.array(c["source"]); tgt=np.array(c["target"]); mask=np.array(c["mask"],bool)
    if image.shape!=src.shape or not np.isfinite(image).all(): return float("inf")
    terms=[]
    for y,x in np.argwhere(mask):
        if not (0<y<src.shape[0]-1 and 0<x<src.shape[1]-1): continue
        lap=4*image[y,x]-image[y-1,x]-image[y+1,x]-image[y,x-1]-image[y,x+1]
        guide=4*src[y,x]-src[y-1,x]-src[y+1,x]-src[y,x-1]-src[y,x+1]
        terms.append(float(np.mean((lap-guide)**2)))
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            if not mask[y+dy,x+dx]:
                terms.append(float(np.mean((image[y+dy,x+dx]-tgt[y+dy,x+dx])**2)))
    return float(np.mean(terms or [float("inf")]))


def sim_multipole(c: dict[str, Any], gains: list[float]) -> np.ndarray:
    n=c["poles"]; ang=np.array(c["initial_angles"],float); vel=np.zeros(n)
    x=v=0.; hist=[]
    g=np.resize(np.array(gains,float), 2*n+2)
    for t in range(c["steps"]):
        force=np.clip(-g[0]*x-g[1]*v + np.sum(-g[2:2+n]*ang-g[2+n:2+2*n]*vel),-10,10)
        v += .025*(force-.12*v+c["wind"]*math.sin(t*.07)); x += .025*v
        acc=(9.81*np.sin(ang)-.72*force*np.cos(ang))/np.array(c["lengths"])
        vel += .025*(acc-.04*vel); ang += .025*vel
        hist.append([x,*ang.tolist()])
        if abs(x)>2.4 or np.max(abs(ang))>1.45: break
    return np.array(hist)


def render_scene(objs: list[list[float]], w: int, h: int, view: float=0) -> np.ndarray:
    yy,xx=np.mgrid[:h,:w]; im=np.zeros((h,w,3),float)+.04
    for ox,oy,r,cr,cg,cb in objs:
        sx=(ox+.35*view*(oy-.5))*w; sy=oy*h; rr=r*w
        z=np.maximum(0,1-((xx-sx)**2+(yy-sy)**2)/(rr*rr))
        shade=(.3+.7*np.sqrt(z))*z
        col=np.array([cr,cg,cb])
        im=im*(1-shade[...,None])+col*shade[...,None]
    return im.clip(0,1)


def sim_world(c: dict[str, Any], actions: list[list[float]]) -> np.ndarray:
    x=np.array(c["state"],float); hist=[x.copy()]
    acts=np.array(actions,float)
    for t in range(c["steps"]):
        a=np.clip(acts[t] if t<len(acts) else 0,-1,1)
        x[2:] += .08*(a+np.array([c["wind"],-.18])-c["drag"]*x[2:])
        x[:2] += .08*x[2:]; x[:2]=np.clip(x[:2],0,1)
        hist.append(x.copy())
    return np.array(hist)


def sim_smoke(c: dict[str, Any], controls: list[list[float]]) -> np.ndarray:
    n=c["size"]; d=np.zeros((n,n)); sy,sx=c["source"]; d[sy,sx]=1
    frames=[]; ctl=np.array(controls,float)
    yy,xx=np.mgrid[:n,:n]
    for t in range(c["steps"]):
        u=np.clip(ctl[t] if t<len(ctl) else 0,-1,1)
        px=np.clip(np.rint(xx-u[0]*1.4).astype(int),0,n-1)
        py=np.clip(np.rint(yy+1-u[1]*.7).astype(int),0,n-1)
        d=gaussian_filter(d[py,px],.65)*.992; d[sy,sx]=max(d[sy,sx],.45)
        frames.append(d.copy())
    return np.array(frames)


def sim_mpm(c: dict[str, Any], params: list[float]) -> np.ndarray:
    p=np.array(c["positions"],float); v=np.zeros_like(p); rest=p.copy(); frames=[]
    stiffness=float(params[0] if params else .18); bounce=float(params[1] if len(params)>1 else .3)
    for _ in range(c["steps"]):
        center=p.mean(0); v += c["dt"]*np.array([0,c["gravity"]])
        if c["material"]!="water": v += c["dt"]*stiffness*(rest-rest.mean(0)-(p-center))
        p += c["dt"]*v
        hit=p[:,1]<.05; p[hit,1]=.05; v[hit,1]=abs(v[hit,1])*bounce
        wall=(p[:,0]<.03)|(p[:,0]>.97); v[wall,0]*=-bounce; p[:,0]=np.clip(p[:,0],.03,.97)
        frames.append(p.copy())
    return np.array(frames)


def topology_metrics(c: dict[str, Any], density: np.ndarray) -> tuple[float,float,float]:
    d=np.clip(density,0,1); h,w=d.shape
    support=d[:,0]>.2; material=d>.24
    labels,n=label(material)
    connected=np.zeros_like(material)
    for lab in range(1,n+1):
        comp=labels==lab
        if np.any(comp[:,0]) and any(comp[int(load[1]),int(load[0])] for load in c["loads"]):
            connected|=comp
    connectivity=connected.sum()/max(1,material.sum())
    yy,xx=np.mgrid[:h,:w]; load_y=np.mean([z[1] for z in c["loads"]])
    ideal=np.exp(-((yy-(load_y+(h/2-load_y)*(1-xx/(w-1))))/(2.0+h*.08))**2)
    alignment=float((d*ideal).sum()/max(1e-9,d.sum()))
    volume=float(d.mean())
    return connectivity,alignment,volume


def render(task: str, c: dict[str, Any], out: dict[str, Any], path: Path) -> None:
    size=(480,360); im=Image.new("RGB",size,(18,20,27)); dr=ImageDraw.Draw(im)
    if task=="poisson":
        arr=np.array(out.get("image",c["target"])); im=Image.fromarray(np.uint8(np.clip(arr,0,1)*255)).resize(size)
    elif task=="multipole":
        hist=sim_multipole(c,out.get("gains",[])); x=float(hist[-1,0]) if len(hist) else 0
        base=(240+int(x*70),300); dr.line((0,310,480,310),fill="gray",width=3); dr.rectangle((base[0]-28,base[1]-12,base[0]+28,base[1]+12),fill="orange")
        for i,a in enumerate(hist[-1,1:] if len(hist) else []):
            length=65-5*i; end=(base[0]+length*math.sin(a),base[1]-length*math.cos(a)); dr.line((*base,*end),fill=(80+40*i,220,255-25*i),width=5)
    elif task=="pathtracer":
        arr=np.array(out.get("image",np.zeros((32,40,3)))); im=Image.fromarray(np.uint8(np.clip(arr,0,1)*255)).resize(size)
    elif task=="mpm":
        hist=np.array(out.get("frames",[]),float);
        for x,y in hist[-1] if len(hist) else []: dr.ellipse((x*480-3,360-y*360-3,x*480+3,360-y*360+3),fill="cyan")
    elif task=="world_mpc":
        hist=sim_world(c,out.get("actions",[])); pts=[(int(x*480),int(360-y*360)) for x,y in hist[:,:2]]; dr.line(pts,fill="cyan",width=4); tx,ty=c["target"]; dr.ellipse((tx*480-10,360-ty*360-10,tx*480+10,360-ty*360+10),outline="orange",width=3)
    elif task=="topology":
        d=np.array(out.get("density",np.zeros((c["height"],c["width"])))); im=Image.fromarray(np.uint8(np.clip(d,0,1)*255)).resize(size)
    elif task=="smoke":
        fr=sim_smoke(c,out.get("controls",[]))[-1]; tar=np.array(c["target"]); arr=np.stack([tar*.65,fr,fr*.25],-1); im=Image.fromarray(np.uint8(np.clip(arr,0,1)*255)).resize(size)
    elif task=="softrobot":
        morph=np.array(out.get("morphology",np.ones((5,8)))); im=Image.fromarray(np.uint8(np.kron(morph,np.ones((40,40)))*220)).resize(size)
    elif task=="inverse_render":
        arr=render_scene(out.get("objects",[]),40,40,0); im=Image.fromarray(np.uint8(arr*255)).resize(size)
    else:
        dr.text((20,20),"Lightcycle bots are rendered by the tournament verifier",fill="white")
    im.save(path)


def baseline(task: str, c: dict[str, Any]) -> dict[str, Any]:
    if task=="poisson": return {"image": c["target"]}
    if task=="multipole": return {"gains": [1,1]+[8]*c["poles"]+[1]*c["poles"]}
    if task=="pathtracer":
        exact=render_scene(c["spheres"],c["width"],c["height"],0); small=exact[::4,::4]
        block=np.repeat(np.repeat(small,4,0),4,1)[:c["height"],:c["width"]]
        noise=np.random.default_rng(c["seed"]).normal(0,.09,block.shape)
        return {"image":np.clip(block+noise,0,1).tolist()}
    if task=="mpm":
        return {"frames":sim_mpm(c,[.08,.15]).tolist()}
    if task=="world_mpc":
        pos=np.array(c["state"][:2]); target=np.array(c["target"]); acts=[]
        vel=np.zeros(2)
        for _ in range(c["steps"]):
            a=np.clip(3*(target-pos)-1.4*vel, -1,1); acts.append(a.tolist()); vel+=.08*(a+[c["wind"],-.18]); pos+=.08*vel
        return {"actions":acts}
    if task=="topology":
        d=np.full((c["height"],c["width"]),c["volume"])
        return {"density":d.tolist()}
    if task=="smoke":
        target=np.array(c["target"]); ty,tx=np.unravel_index(np.argmax(target),target.shape); sy,sx=c["source"]
        return {"controls":[[float(np.clip((tx-sx)/18,-1,1)),float(np.clip((sy-ty)/18,-1,1))]]*c["steps"]}
    if task=="softrobot":
        m=np.zeros((5,8)); m[1:4,1:7]=1; return {"morphology":m.tolist(),"frequency":2.4,"phase_gradient":.7}
    if task=="inverse_render": return {"objects":[]}
    if task=="lightcycle": return {"policy":"space"}
    raise ValueError(task)


def score(task: str, c: dict[str, Any], out: dict[str, Any]) -> dict[str,float]:
    try:
        if task=="poisson":
            err=poisson_residual(c,np.array(out["image"],float)); return {"quality":clamp(math.exp(-25*err)),"residual":err}
        if task=="multipole":
            h=sim_multipole(c,out["gains"]); survival=len(h)/c["steps"]; rms=float(np.sqrt(np.mean(h[:,1:]**2))) if len(h) else 9; return {"quality":clamp(survival*math.exp(-1.5*rms)),"survival":survival,"rms":rms}
        if task=="pathtracer":
            a=np.array(out["image"],float); ref=render_scene(c["spheres"],c["width"],c["height"]); mse=float(np.mean((a-ref)**2)); return {"quality":clamp(math.exp(-35*mse)),"mse":mse}
        if task=="mpm":
            h=np.array(out.get("frames",[]),float)
            params={"jelly":[.18,.3],"snow":[.5,.1],"water":[0,.05]}[c["material"]]
            ref=sim_mpm(c,params)
            if h.shape!=ref.shape or not np.isfinite(h).all(): return {"quality":0.,"invalid":1.}
            rmse=float(np.sqrt(np.mean((h-ref)**2)))
            mass_ok=float(h.shape[1]==len(c["positions"]))
            return {"quality":mass_ok*clamp(math.exp(-35*rmse)),"trajectory_rmse":rmse}
        if task=="world_mpc":
            h=sim_world(c,out["actions"]); dist=float(np.linalg.norm(h[-1,:2]-c["target"])); effort=float(np.mean(np.square(out["actions"]))); return {"quality":clamp(math.exp(-5*dist-0.08*effort)),"distance":dist,"effort":effort}
        if task=="topology":
            d=np.array(out["density"],float); conn,align,vol=topology_metrics(c,d); penalty=math.exp(-20*max(0,vol-c["volume"])); return {"quality":clamp(conn*align*penalty),"connectivity":conn,"alignment":align,"volume":vol}
        if task=="smoke":
            fr=sim_smoke(c,out["controls"])[-1]; tar=np.array(c["target"]); corr=float(np.sum(fr*tar)/math.sqrt(np.sum(fr*fr)*np.sum(tar*tar)+1e-9)); return {"quality":clamp(corr),"overlap":corr}
        if task=="softrobot":
            m=np.array(out["morphology"],float)>0.5; count=m.sum(); connected=max((label(m)[1]==1),False); freq=float(out.get("frequency",0)); phase=float(out.get("phase_gradient",0)); locomotion=abs(math.sin(freq*.7)*math.sin(phase))*min(1,count/c["budget"]); return {"quality":clamp(float(connected)*locomotion*math.exp(-.2*max(0,count-c["budget"]))),"voxels":float(count)}
        if task=="inverse_render":
            ims=[render_scene(out["objects"],c["width"],c["height"],v) for v in c["views"]]; obs=np.array(c["observations"]); mse=float(np.mean((np.array(ims)-obs)**2)); complexity=len(out["objects"]); return {"quality":clamp(math.exp(-60*mse-.015*complexity)),"mse":mse,"objects":float(complexity)}
    except (KeyError,ValueError,TypeError,IndexError):
        return {"quality":0.0,"invalid":1.0}
    return {"quality":0.0}


def main() -> None:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    q=sub.add_parser("case"); q.add_argument("task",choices=TASKS); q.add_argument("seed",type=int); q.add_argument("output",type=Path); q.add_argument("--difficulty",type=int,default=1)
    q=sub.add_parser("baseline"); q.add_argument("task",choices=TASKS); q.add_argument("input",type=Path); q.add_argument("output",type=Path); q.add_argument("--preview",type=Path)
    q=sub.add_parser("score"); q.add_argument("task",choices=TASKS); q.add_argument("input",type=Path); q.add_argument("candidate",type=Path)
    a=p.parse_args()
    if a.cmd=="case": a.output.write_text(json.dumps(case(a.task,a.seed,a.difficulty)))
    elif a.cmd=="baseline":
        c=json.loads(a.input.read_text()); out=baseline(a.task,c); a.output.write_text(json.dumps(out))
        if a.preview: render(a.task,c,out,a.preview)
    else:
        c=json.loads(a.input.read_text()); out=json.loads(a.candidate.read_text()); print(json.dumps(score(a.task,c,out)))
if __name__=="__main__": main()
