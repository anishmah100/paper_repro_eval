#!/usr/bin/env python3
import json,sys
for line in sys.stdin:
 message=json.loads(line)
 if message.get("type")=="reset":continue
 task=message.get("task")
 action=0 if "angles" in message else [0,0]
 print(json.dumps({"action":action}),flush=True)
