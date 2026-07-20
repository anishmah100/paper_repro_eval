#!/usr/bin/env python3
import json,sys
for line in sys.stdin:
 message=json.loads(line)
 if message.get("type")!="reset":print(json.dumps({"move":"X"}),flush=True)
