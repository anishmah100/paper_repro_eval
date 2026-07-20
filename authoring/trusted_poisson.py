"""Private sparse Poisson reference used only by trusted verification."""

import math
from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve


def solve(case: dict[str, Any]) -> np.ndarray:
    src, tgt, mask = (
        np.array(case["source"]),
        np.array(case["target"]),
        np.array(case["mask"], bool),
    )
    h, w, _ = src.shape
    ids = -np.ones((h, w), int)
    ids[mask] = np.arange(mask.sum())
    rows = []
    cols = []
    vals = []
    rhs = np.zeros((mask.sum(), 3))
    for y, x in np.argwhere(mask):
        i = ids[y, x]
        rows.append(i)
        cols.append(i)
        vals.append(4.0)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                rhs[i] += src[y, x] - src[ny, nx]
                if mask[ny, nx]:
                    rows.append(i)
                    cols.append(ids[ny, nx])
                    vals.append(-1.0)
                else:
                    rhs[i] += tgt[ny, nx]
    matrix = csr_matrix((vals, (rows, cols)), shape=(mask.sum(), mask.sum()))
    out = tgt.copy()
    for channel in range(3):
        out[:, :, channel][mask] = spsolve(matrix, rhs[:, channel])
    return out.clip(0, 1)


def score(case: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    ref = solve(case)
    actual = np.array(candidate.get("image", []), float)
    mse = float(np.mean((actual - ref) ** 2)) if actual.shape == ref.shape else float("inf")
    return {"quality": max(0.0, min(1.0, math.exp(-80 * mse))), "mse": mse}
