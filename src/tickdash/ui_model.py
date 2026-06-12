from __future__ import annotations

from tickdash.depth_math import fill_per_level


def chart_key(title: str) -> str:
    chars = [c.lower() if c.isalnum() else "_" for c in title.strip()]
    compact = "_".join(part for part in "".join(chars).split("_") if part)
    return f"chart_{compact}"


def preferred_default_key(keys: list[str]) -> str:
    for key in keys:
        if key.startswith("NSE_FO|"):
            return key
    return keys[0]


def select_snapshot_index(labels: list[str], time_input: str) -> int:
    target = time_input.strip()
    if not target:
        return -1
    for idx, label in enumerate(labels):
        if label >= target:
            return idx
    return len(labels) - 1 if labels else -1


def make_ladder_rows(snap: dict, levels: list[int], lot_size: int) -> list[dict]:
    rows = []
    for level in levels:
        idx = level - 1
        rows.append(
            {
                "level": level,
                "bid_lots": round((snap["bq"][idx] if idx < len(snap["bq"]) else 0) / lot_size, 2),
                "bid_price": snap["bp"][idx] if idx < len(snap["bp"]) else 0,
                "ask_price": snap["ap"][idx] if idx < len(snap["ap"]) else 0,
                "ask_lots": round((snap["aq"][idx] if idx < len(snap["aq"]) else 0) / lot_size, 2),
            }
        )
    return rows


def make_fill_rows(
    snap: dict,
    side: str,
    lots: int,
    lot_size: int,
    levels: list[int],
) -> dict:
    prices = snap["ap"] if side == "buy" else snap["bp"]
    quantities = snap["aq"] if side == "buy" else snap["bq"]
    order_qty = lots * lot_size
    stats = fill_per_level(prices, quantities, side, order_qty, levels)
    rows = []
    running = 0
    remaining = order_qty
    for level in levels:
        if remaining <= 0:
            break
        idx = level - 1
        price = prices[idx] if idx < len(prices) else 0
        available = quantities[idx] if idx < len(quantities) else 0
        taken = min(remaining, available)
        running += taken
        remaining -= taken
        rows.append(
            {
                "level": level,
                "price": round(price, 2),
                "avail_lots": round(available / lot_size, 2),
                "taken_lots": round(taken / lot_size, 2),
                "running_fill_lots": round(running / lot_size, 2),
            }
        )
        if remaining <= 0:
            remaining = 0
    return {"stats": stats, "rows": rows}
