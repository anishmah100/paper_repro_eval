from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def estimate(points: list[list[float]]) -> dict[str, float]:
    slopes = [
        (right[1] - left[1]) / (right[0] - left[0])
        for index, left in enumerate(points)
        for right in points[index + 1 :]
        if right[0] != left[0]
    ]
    slope = statistics.median(slopes)
    intercept = statistics.median(point[1] - slope * point[0] for point in points)
    return {"slope": slope, "intercept": intercept}


if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:3])
    data = json.loads(source.read_text(encoding="utf-8"))
    destination.write_text(json.dumps(estimate(data["points"])), encoding="utf-8")
