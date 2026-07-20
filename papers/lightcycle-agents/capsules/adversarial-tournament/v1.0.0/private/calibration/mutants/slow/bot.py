#!/usr/bin/env python3
import json,sys,time
for line in sys.stdin:
 message=json.loads(line)
 if message.get("type")!="reset":time.sleep(1);print(json.dumps({"move":"U"}),flush=True)
