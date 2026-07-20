#!/usr/bin/env python3
import json
import sys

import numpy as np

context = {}
for line in sys.stdin:
    message = json.loads(line)
    if message.get("type") == "reset":
        context = message
        continue
    if context.get("task") == "multipole":
        angles = np.array(message["angles"])
        angular = np.array(message["angular_velocities"])
        action = float(
            np.clip(
                4 * angles.sum() - 4 * angular.sum() - message["x"] - message["velocity"], -10, 10
            )
        )
    else:
        state = np.array(message["state"])
        target = np.array(message["target"])
        action = np.clip(3 * (target - state[:2]) - 1.4 * state[2:], -1, 1).tolist()
    print(json.dumps({"action": action}), flush=True)
