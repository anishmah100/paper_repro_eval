#!/usr/bin/env python3
import json,sys
for line in sys.stdin:
 message=json.loads(line)
 if message.get("type")=="reset":continue
 print(json.dumps({"action":0 if "angles" in message else [0,0]}),flush=True)
