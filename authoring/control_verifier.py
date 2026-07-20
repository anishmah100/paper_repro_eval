"""Trusted persistent-controller evaluation for control arenas."""
import json,math,subprocess
from pathlib import Path
from typing import Any
import numpy as np

def quality(task:str,sub:Path,case:dict[str,Any])->tuple[float,dict[str,Any]]:
    try:
        proc=subprocess.Popen(["bash","agent.sh"],cwd=sub,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,text=True,bufsize=1)
        assert proc.stdin and proc.stdout
        proc.stdin.write(json.dumps({"type":"reset","task":task,"case":case})+"\n");proc.stdin.flush()
        if task=="multipole":
            n=case["poles"];angles=np.array(case["initial_angles"],float);angular=np.zeros(n)
            x=velocity=0.;history=[]
            for step in range(case["steps"]):
                obs={"type":"observation","x":x,"velocity":velocity,"angles":angles.tolist(),
                     "angular_velocities":angular.tolist(),"step":step}
                proc.stdin.write(json.dumps(obs)+"\n");proc.stdin.flush()
                force=float(json.loads(proc.stdout.readline()).get("action",0));force=float(np.clip(force,-10,10))
                velocity+=.025*(force-.12*velocity+case["wind"]*math.sin(step*.07));x+=.025*velocity
                acceleration=(9.81*np.sin(angles)-.72*force*np.cos(angles))/np.array(case["lengths"])
                angular+=.025*(acceleration-.04*angular);angles+=.025*angular;history.append(angles.copy())
                if abs(x)>2.4 or np.max(abs(angles))>1.45:break
            survival=len(history)/case["steps"];rms=float(np.sqrt(np.mean(np.square(history))))
            value=survival*math.exp(-1.5*rms);metrics={"survival":survival,"rms":rms}
        else:
            state=np.array(case["state"],float);target=np.array(case["target"]);effort=[]
            for step in range(case["steps"]):
                obs={"type":"observation","state":state.tolist(),"target":target.tolist(),"step":step}
                proc.stdin.write(json.dumps(obs)+"\n");proc.stdin.flush()
                action=np.clip(np.array(json.loads(proc.stdout.readline()).get("action",[0,0]),float),-1,1)
                state[2:]+=.08*(action+np.array([case["wind"],-.18])-case["drag"]*state[2:])
                state[:2]+=.08*state[2:];state[:2]=np.clip(state[:2],0,1);effort.append(float(action@action))
            distance=float(np.linalg.norm(state[:2]-target));energy=float(np.mean(effort))
            value=math.exp(-5*distance-.08*energy);metrics={"distance":distance,"effort":energy}
        proc.kill();return min(1.,value),metrics
    except Exception as exc:return 0.,{"error":str(exc)}
