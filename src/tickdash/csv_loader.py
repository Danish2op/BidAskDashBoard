from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from typing import Iterable

import pandas as pd


BASE_COLUMNS = [
    "id",
    "instrument_key",
    "feed_timestamp_ms",
    "request_mode",
    "depth_levels_received",
    "received_at_utc",
    "last_traded_price",
    "last_traded_time_ms",
    "last_traded_quantity",
    "close_price",
    "average_traded_price",
    "volume_traded_today",
    "open_interest",
    "implied_volatility",
    "total_buy_quantity",
    "total_sell_quantity",
    "option_delta",
    "option_theta",
    "option_gamma",
    "option_vega",
    "option_rho",
]

DEPTH_COLUMNS = [
    f"depth_{level}_{side}_{field}"
    for level in range(1, 31)
    for side in ("bid", "ask")
    for field in ("quantity", "price")
]

REQUIRED_COLUMNS = BASE_COLUMNS + DEPTH_COLUMNS + ["created_at"]


@dataclass(frozen=True)
class Snapshot:
    ts: str
    feed_timestamp_ms: int
    ltp: float
    bid_qty: list[int]
    bid_px: list[float]
    ask_qty: list[int]
    ask_px: list[float]


def validate_market_tick_columns(columns: Iterable[str]) -> None:
    present = set(columns)
    missing = [col for col in REQUIRED_COLUMNS if col not in present]
    if missing:
        raise ValueError(f"Missing market tick columns: {', '.join(missing)}")


def _time_label_ist(received_at_utc: str) -> str:
    ts = pd.to_datetime(received_at_utc, utc=True, errors="coerce")
    if pd.isna(ts):
        return ""
    return ts.tz_convert("Asia/Kolkata").strftime("%H:%M:%S")


def row_to_snapshot(row: pd.Series) -> Snapshot:
    return Snapshot(
        ts=_time_label_ist(str(row["received_at_utc"])),
        feed_timestamp_ms=int(row["feed_timestamp_ms"]),
        ltp=float(row["last_traded_price"]),
        bid_qty=[int(row[f"depth_{level}_bid_quantity"]) for level in range(1, 31)],
        bid_px=[float(row[f"depth_{level}_bid_price"]) for level in range(1, 31)],
        ask_qty=[int(row[f"depth_{level}_ask_quantity"]) for level in range(1, 31)],
        ask_px=[float(row[f"depth_{level}_ask_price"]) for level in range(1, 31)],
    )


def load_snapshots_for_instrument(
    csv_path: str,
    instrument_key: str,
    downsample: int = 20,
    chunksize: int = 100_000,
) -> list[Snapshot]:
    if downsample < 1:
        raise ValueError("downsample must be >= 1")

    snapshots: list[Snapshot] = []
    seen_header = False
    matched_index = 0
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):
        if not seen_header:
            validate_market_tick_columns(chunk.columns)
            seen_header = True
        selected = chunk.loc[chunk["instrument_key"] == instrument_key]
        if selected.empty:
            continue
        for _, row in selected.iterrows():
            if matched_index % downsample == 0:
                snapshots.append(row_to_snapshot(row))
            matched_index += 1
    return snapshots


def load_snapshots_with_count(
    csv_path: str,
    instrument_key: str,
    downsample: int = 20,
    chunksize: int = 100_000,
) -> tuple[list[Snapshot], int]:
    if downsample < 1:
        raise ValueError("downsample must be >= 1")

    snapshots: list[Snapshot] = []
    total = 0
    seen_header = False
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):
        if not seen_header:
            validate_market_tick_columns(chunk.columns)
            seen_header = True
        selected = chunk.loc[chunk["instrument_key"] == instrument_key]
        if selected.empty:
            continue
        for _, row in selected.iterrows():
            if total % downsample == 0:
                snapshots.append(row_to_snapshot(row))
            total += 1
    return snapshots, total


def list_instrument_keys(csv_path: str, chunksize: int = 100_000) -> list[str]:
    keys: set[str] = set()
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, usecols=["instrument_key"]):
        keys.update(chunk["instrument_key"].astype(str).unique().tolist())
    return sorted(keys)
