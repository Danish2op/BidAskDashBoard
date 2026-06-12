from __future__ import annotations

from statistics import mean

from tickdash.csv_loader import Snapshot
from tickdash.depth_math import fill_per_level, iqr_stats


KEY_DEPTHS = [1, 2, 3, 4, 5, 10, 15, 20, 30]


def _safe_spread(snapshot: Snapshot) -> float:
    bid = snapshot.bid_px[0] if snapshot.bid_px else 0.0
    ask = snapshot.ask_px[0] if snapshot.ask_px else 0.0
    if bid <= 0 or ask <= 0:
        return 0.0
    return round(ask - bid, 4)


def analyze_snapshots(
    snapshots: list[Snapshot],
    lot_size: int = 65,
    order_lots: int = 100,
    total_snapshots: int | None = None,
    key_depths: list[int] | None = None,
) -> dict:
    depths = key_depths or KEY_DEPTHS
    order_qty = order_lots * lot_size
    sampled_count = len(snapshots)

    per_level = {
        "buy": {d: {"qty": [], "fill_qty": [], "w_slip": [], "s_slip": [], "avg_px": []} for d in depths},
        "sell": {d: {"qty": [], "fill_qty": [], "w_slip": [], "s_slip": [], "avg_px": []} for d in depths},
    }
    cum_bid = {d: [] for d in depths}
    cum_ask = {d: [] for d in depths}
    min_depth_buy = []
    min_depth_sell = []
    compact = []
    ts_labels = []
    ltp_series = []
    spread_series = []

    for snap in snapshots:
        ts_labels.append(snap.ts)
        ltp_series.append(snap.ltp)
        spread = _safe_spread(snap)
        spread_series.append(spread)
        compact.append(
            {
                "ts": snap.ts,
                "ltp": snap.ltp,
                "bp": [round(price, 2) for price in snap.bid_px],
                "bq": snap.bid_qty,
                "ap": [round(price, 2) for price in snap.ask_px],
                "aq": snap.ask_qty,
                "spread": spread,
            }
        )

        for depth in depths:
            bid_qty = sum(snap.bid_qty[:depth])
            ask_qty = sum(snap.ask_qty[:depth])
            cum_bid[depth].append(round(bid_qty / lot_size, 2))
            cum_ask[depth].append(round(ask_qty / lot_size, 2))

            buy = fill_per_level(snap.ask_px, snap.ask_qty, "buy", order_qty, list(range(1, depth + 1)))
            sell = fill_per_level(snap.bid_px, snap.bid_qty, "sell", order_qty, list(range(1, depth + 1)))
            for side, result, qty in (("buy", buy, ask_qty), ("sell", sell, bid_qty)):
                per_level[side][depth]["qty"].append(round(qty / lot_size, 2))
                per_level[side][depth]["fill_qty"].append(round(result["fill_qty"] / lot_size, 2))
                per_level[side][depth]["w_slip"].append(result["weighted_slip"])
                per_level[side][depth]["s_slip"].append(result["sweep_slip"])
                per_level[side][depth]["avg_px"].append(result["avg_price"])

        buy_30 = fill_per_level(snap.ask_px, snap.ask_qty, "buy", order_qty, list(range(1, 31)))
        sell_30 = fill_per_level(snap.bid_px, snap.bid_qty, "sell", order_qty, list(range(1, 31)))
        min_depth_buy.append(buy_30["min_depth"])
        min_depth_sell.append(sell_30["min_depth"])

    allday = {"buy": {}, "sell": {}}
    for side in ("buy", "sell"):
        for depth in depths:
            allday[side][str(depth)] = {
                "qty": iqr_stats(per_level[side][depth]["qty"]),
                "fill": iqr_stats(per_level[side][depth]["fill_qty"]),
                "w_slip": iqr_stats(per_level[side][depth]["w_slip"]),
                "s_slip": iqr_stats(per_level[side][depth]["s_slip"]),
            }
    allday["min_depth_buy"] = iqr_stats([x for x in min_depth_buy if x])
    allday["min_depth_sell"] = iqr_stats([x for x in min_depth_sell if x])
    allday["spread"] = iqr_stats(spread_series)

    latest = snapshots[-1] if snapshots else None
    bid_depth_slip = []
    ask_depth_slip = []
    if latest:
        bid_depth_slip = [round(latest.bid_px[0] - latest.bid_px[i], 4) for i in range(30)]
        ask_depth_slip = [round(latest.ask_px[i] - latest.ask_px[0], 4) for i in range(30)]

    spread_stats = allday["spread"]
    summary = {
        "total_snapshots": total_snapshots if total_snapshots is not None else sampled_count,
        "sampled_snapshots": sampled_count,
        "time_start": ts_labels[0] if ts_labels else "",
        "time_end": ts_labels[-1] if ts_labels else "",
        "ltp_latest": latest.ltp if latest else 0,
        "spread_median": spread_stats["median"],
        "spread_q1": spread_stats["q1"],
        "spread_q3": spread_stats["q3"],
        "spread_iqr": spread_stats["iqr"],
        "spread_fence_hi": spread_stats["fence_hi"],
        "spread_outlier_pct": spread_stats["outlier_pct"],
        "spread_avg": spread_stats["avg"],
        "spread_min": spread_stats["min"],
        "spread_max": spread_stats["max"],
        "lot_size": lot_size,
        "default_lots": order_lots,
        "default_qty": order_qty,
        "ltp_min": round(float(min(ltp_series)), 2) if ltp_series else 0,
        "ltp_max": round(float(max(ltp_series)), 2) if ltp_series else 0,
        "ltp_avg": round(float(mean(ltp_series)), 2) if ltp_series else 0,
    }

    return {
        "summary": summary,
        "key_depths": depths,
        "allday": allday,
        "snapshots": compact,
        "ts_labels": ts_labels,
        "ltp_series": ltp_series,
        "spread_series": spread_series,
        "cum_bid": {str(k): v for k, v in cum_bid.items()},
        "cum_ask": {str(k): v for k, v in cum_ask.items()},
        "per_level_buy": {str(d): per_level["buy"][d] for d in depths},
        "per_level_sell": {str(d): per_level["sell"][d] for d in depths},
        "min_depth_buy": min_depth_buy,
        "min_depth_sell": min_depth_sell,
        "bid_depth_slip": bid_depth_slip,
        "ask_depth_slip": ask_depth_slip,
    }
