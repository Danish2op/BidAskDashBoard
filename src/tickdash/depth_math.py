from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np


def iqr_stats(values: Iterable[float | None]) -> dict[str, float | None]:
    clean = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not clean:
        return {
            "avg": None,
            "min": None,
            "max": None,
            "median": None,
            "q1": None,
            "q3": None,
            "iqr": None,
            "fence_lo": None,
            "fence_hi": None,
            "outlier_pct": None,
        }

    q1 = float(np.percentile(clean, 25))
    median = float(np.percentile(clean, 50))
    q3 = float(np.percentile(clean, 75))
    iqr = q3 - q1
    fence_lo = q1 - 1.5 * iqr
    fence_hi = q3 + 1.5 * iqr
    outliers = [v for v in clean if v < fence_lo or v > fence_hi]

    return {
        "avg": round(float(np.mean(clean)), 4),
        "min": round(float(np.min(clean)), 4),
        "max": round(float(np.max(clean)), 4),
        "median": round(median, 4),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "iqr": round(iqr, 4),
        "fence_lo": round(fence_lo, 4),
        "fence_hi": round(fence_hi, 4),
        "outlier_pct": round(len(outliers) / len(clean) * 100, 1),
    }


def fill_per_level(
    prices: Sequence[float],
    quantities: Sequence[int],
    side: str,
    order_qty: int,
    levels: Sequence[int],
) -> dict:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")

    ref = float(prices[0]) if prices else 0.0
    remaining = int(order_qty)
    cost = 0.0
    min_depth = None
    last_px = ref
    breakdown = []

    for level in sorted(levels):
        if remaining <= 0:
            break
        idx = level - 1
        px = float(prices[idx]) if idx < len(prices) else 0.0
        qty = int(quantities[idx]) if idx < len(quantities) else 0
        take = min(remaining, qty)
        if take > 0:
            cost += px * take
            last_px = px
        remaining -= take
        breakdown.append(
            {
                "level": level,
                "price": round(px, 2),
                "avail_qty": qty,
                "taken_qty": int(take),
            }
        )
        if remaining <= 0 and min_depth is None:
            min_depth = level

    fill_qty = int(order_qty) - remaining
    avg_price = round(cost / fill_qty, 4) if fill_qty > 0 else 0.0
    if side == "buy":
        weighted_slip = round(avg_price - ref, 4)
        sweep_slip = round(last_px - ref, 4)
    else:
        weighted_slip = round(ref - avg_price, 4)
        sweep_slip = round(ref - last_px, 4)

    return {
        "fill_qty": int(fill_qty),
        "unfilled": int(remaining),
        "filled": remaining <= 0,
        "avg_price": avg_price,
        "ref_price": round(ref, 4),
        "last_px": round(last_px, 4),
        "weighted_slip": weighted_slip,
        "sweep_slip": sweep_slip,
        "min_depth": min_depth,
        "breakdown": breakdown,
    }

