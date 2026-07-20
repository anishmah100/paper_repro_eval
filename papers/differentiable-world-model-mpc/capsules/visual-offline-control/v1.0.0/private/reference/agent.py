#!/usr/bin/env python3
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
root=Path(__file__).resolve().parents[7]
sys.path.insert(0,str(root/"templates"/"arena_kit"))
import arena_kit as kit
actions=[]
for line in sys.stdin:
 message=json.loads(line)
 if message.get("type")=="reset":
  case=message["case"];base=np.array(kit.baseline("world_mpc",case)["actions"]);steps=case["steps"]
  def objective(z):
   correction=np.repeat(np.asarray(z).reshape(8,2),int(np.ceil(steps/8)),axis=0)[:steps]
   candidate={"actions":np.clip(base+correction,-1,1).tolist()}
   return -kit.score("world_mpc",case,candidate)["quality"]
  solution=minimize(objective,np.zeros(16),method="Powell",options={"maxiter":80}).x
  correction=np.repeat(solution.reshape(8,2),int(np.ceil(steps/8)),axis=0)[:steps]
  actions=np.clip(base+correction,-1,1).tolist();continue
 step=message["step"];print(json.dumps({"action":actions[step] if step<len(actions) else [0,0]}),flush=True)
