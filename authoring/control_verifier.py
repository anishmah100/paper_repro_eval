"""Trusted persistent-controller evaluation for control arenas."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from paper_repro_eval.tournament import BotProcess


def quality(
    task: str,
    submission: Path,
    case: dict[str, Any],
    *,
    turn_timeout: float = 0.25,
) -> tuple[float, dict[str, Any]]:
    bot: BotProcess | None = None
    try:
        bot = BotProcess.start(submission, "agent.sh")
        bot.send({"type": "reset", "task": task, "case": case})
        protocol_errors = 0
        timeouts = 0
        if task == "multipole":
            count = case["poles"]
            angles = np.array(case["initial_angles"], dtype=float)
            angular_velocity = np.zeros(count)
            cart = cart_velocity = 0.0
            history = []
            for step in range(case["steps"]):
                response, error = bot.response(
                    {
                        "type": "observation",
                        "x": cart,
                        "velocity": cart_velocity,
                        "angles": angles.tolist(),
                        "angular_velocities": angular_velocity.tolist(),
                        "step": step,
                    },
                    10.0 if step == 0 else turn_timeout,
                )
                if error is not None or response is None:
                    protocol_errors += 1
                    timeouts += int(error == "timeout")
                    break
                force = float(np.clip(response.get("action", 0), -10, 10))
                cart_velocity += 0.025 * (
                    force - 0.12 * cart_velocity + case["wind"] * math.sin(step * 0.07)
                )
                cart += 0.025 * cart_velocity
                acceleration = (9.81 * np.sin(angles) - 0.72 * force * np.cos(angles)) / np.array(
                    case["lengths"]
                )
                angular_velocity += 0.025 * (acceleration - 0.04 * angular_velocity)
                angles += 0.025 * angular_velocity
                history.append(angles.copy())
                if abs(cart) > 2.4 or np.max(abs(angles)) > 1.45:
                    break
            survival = len(history) / case["steps"]
            rms = float(np.sqrt(np.mean(np.square(history)))) if history else 9.0
            value = survival * math.exp(-1.5 * rms)
            metrics = {"survival": survival, "rms": rms}
        else:
            state = np.array(case["state"], dtype=float)
            target = np.array(case["target"])
            effort = []
            for step in range(case["steps"]):
                response, error = bot.response(
                    {
                        "type": "observation",
                        "state": state.tolist(),
                        "target": target.tolist(),
                        "step": step,
                    },
                    10.0 if step == 0 else turn_timeout,
                )
                if error is not None or response is None:
                    protocol_errors += 1
                    timeouts += int(error == "timeout")
                    break
                action = np.clip(np.array(response.get("action", [0, 0]), dtype=float), -1, 1)
                if action.shape != (2,) or not np.isfinite(action).all():
                    protocol_errors += 1
                    break
                state[2:] += 0.08 * (
                    action + np.array([case["wind"], -0.18]) - case["drag"] * state[2:]
                )
                state[:2] += 0.08 * state[2:]
                state[:2] = np.clip(state[:2], 0, 1)
                effort.append(float(action @ action))
            distance = float(np.linalg.norm(state[:2] - target))
            energy = float(np.mean(effort)) if effort else 9.0
            value = math.exp(-5 * distance - 0.08 * energy)
            metrics = {"distance": distance, "effort": energy}
        if protocol_errors:
            value = 0.0
        return min(1.0, value), {
            **metrics,
            "protocol_errors": protocol_errors,
            "timeouts": timeouts,
        }
    except (OSError, TypeError, ValueError) as exc:
        return 0.0, {"error": str(exc), "protocol_errors": 1, "timeouts": 0}
    finally:
        if bot is not None:
            bot.close()
