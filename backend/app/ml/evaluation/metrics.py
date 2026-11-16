"""Evaluation metrics for the irrigation prediction model."""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence

import numpy as np


def mae(y_true: Sequence[float], y_pred: Sequence[float]) -> Optional[float]:
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if _valid(t) and _valid(p)]
    if not pairs:
        return None
    return float(sum(abs(t - p) for t, p in pairs) / len(pairs))


def rmse(y_true: Sequence[float], y_pred: Sequence[float]) -> Optional[float]:
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if _valid(t) and _valid(p)]
    if not pairs:
        return None
    return float(math.sqrt(sum((t - p) ** 2 for t, p in pairs) / len(pairs)))


def r2(y_true: Sequence[float], y_pred: Sequence[float]) -> Optional[float]:
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if _valid(t) and _valid(p)]
    if len(pairs) < 2:
        return None
    mean_true = sum(t for t, _ in pairs) / len(pairs)
    ss_total = sum((t - mean_true) ** 2 for t, _ in pairs)
    if ss_total == 0:
        return None
    ss_residual = sum((t - p) ** 2 for t, p in pairs)
    return float(1 - ss_residual / ss_total)


def bias(y_true: Sequence[float], y_pred: Sequence[float]) -> Optional[float]:
    """Mean signed error. Positive means the model over-predicts moisture."""
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if _valid(t) and _valid(p)]
    if not pairs:
        return None
    return float(sum(p - t for t, p in pairs) / len(pairs))


def _valid(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return not (math.isnan(number) or math.isinf(number))


def evaluate(
    y_true: Sequence[float],
    y_pred: Sequence[float],
    *,
    groups: Optional[Sequence[Any]] = None,
) -> dict[str, Any]:
    """Overall metrics plus an error breakdown by group (crop or field)."""
    result: dict[str, Any] = {
        "n": int(sum(1 for t, p in zip(y_true, y_pred) if _valid(t) and _valid(p))),
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "r2": r2(y_true, y_pred),
        "bias": bias(y_true, y_pred),
    }
    if groups is not None:
        by_group: dict[str, dict[str, Any]] = {}
        for truth, pred, group in zip(y_true, y_pred, groups):
            if not (_valid(truth) and _valid(pred)):
                continue
            key = str(group)
            entry = by_group.setdefault(key, {"n": 0, "abs_error_sum": 0.0, "squared_error_sum": 0.0})
            entry["n"] += 1
            entry["abs_error_sum"] += abs(truth - pred)
            entry["squared_error_sum"] += (truth - pred) ** 2
        for key, entry in by_group.items():
            entry["mae"] = entry.pop("abs_error_sum") / entry["n"]
            entry["rmse"] = math.sqrt(entry.pop("squared_error_sum") / entry["n"])
        result["by_group"] = by_group
    return result


def prediction_interval(
    residuals: Sequence[float],
    z: float = 1.96,
) -> Optional[tuple[float, float]]:
    """Symmetric prediction interval half-width from training residuals.

    Returns ``(lower_half_width, upper_half_width)``; ``None`` when there is
    not enough residual data.
    """
    values = [float(r) for r in residuals if _valid(r)]
    if len(values) < 5:
        return None
    std = float(np.std(values, ddof=1))
    half_width = z * std
    return half_width, half_width
