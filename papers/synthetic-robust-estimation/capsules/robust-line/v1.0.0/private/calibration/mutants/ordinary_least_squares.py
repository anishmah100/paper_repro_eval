"""Deliberately wrong mutant: least squares is not the specified median-slope estimator."""

from __future__ import annotations


def estimate(points: list[list[float]]) -> dict[str, float]:
    mean_x = sum(point[0] for point in points) / len(points)
    mean_y = sum(point[1] for point in points) / len(points)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / sum(
        (x - mean_x) ** 2 for x, _ in points
    )
    return {"slope": slope, "intercept": mean_y - slope * mean_x}
