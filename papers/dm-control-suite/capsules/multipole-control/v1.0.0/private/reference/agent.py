#!/usr/bin/env python3
import json,math,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[7]
sys.path.insert(0,str(root/"templates"/"arena_kit"))
import arena_kit as kit
gains=[]
for line in sys.stdin:
 message=json.loads(line)
 if message.get("type")=="reset":
  case=message["case"];n=case["poles"];rng=np.random.default_rng(case["seed"]);choices=[]
  choices.extend(([1,1]+[8]*n+[1]*n,[0]*(2+2*n)))
  for _ in range(2000):
   choices.append(rng.uniform(-4,20,2+2*n).tolist())
  gains=max(choices,key=lambda value:kit.score("multipole",case,{"gains":value})["quality"])
  continue
 angles=np.array(message["angles"]);angular=np.array(message["angular_velocities"]);n=len(angles)
 action=-gains[0]*message["x"]-gains[1]*message["velocity"]
 action-=np.dot(gains[2:2+n],angles)+np.dot(gains[2+n:2+2*n],angular)
 print(json.dumps({"action":float(np.clip(action,-10,10))}),flush=True)
