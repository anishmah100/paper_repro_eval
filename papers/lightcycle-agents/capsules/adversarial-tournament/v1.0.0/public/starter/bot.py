#!/usr/bin/env python3
"""Legal space-seeking baseline. Replace with a stronger persistent bot."""
import json,sys
D={"U":(0,-1),"D":(0,1),"L":(-1,0),"R":(1,0)}
for line in sys.stdin:
 s=json.loads(line)
 if s.get("type")=="reset": continue
 w,h=s["board"]; x,y=s["you"]; occ={tuple(q) for q in s["occupied"]}; legal=[]
 for m,(dx,dy) in D.items():
  q=(x+dx,y+dy)
  if 0<=q[0]<w and 0<=q[1]<h and q not in occ: legal.append((m,q))
 def space(q):
  seen={q}; stack=[q]
  while stack:
   a=stack.pop()
   for dx,dy in D.values():
    b=(a[0]+dx,a[1]+dy)
    if 0<=b[0]<w and 0<=b[1]<h and b not in occ and b not in seen: seen.add(b);stack.append(b)
  return len(seen)
 print(json.dumps({"move":max(legal,key=lambda z:space(z[1]))[0] if legal else "X"}),flush=True)
