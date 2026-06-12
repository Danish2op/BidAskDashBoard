import csv

import pytest

from tickdash.csv_loader import (
    REQUIRED_COLUMNS,
    Snapshot,
    load_snapshots_for_instrument,
    load_snapshots_with_count,
    validate_market_tick_columns,
)


def test_validate_market_tick_columns_rejects_missing_depth_column():
    bad_columns = [c for c in REQUIRED_COLUMNS if c != "depth_30_ask_price"]

    with pytest.raises(ValueError, match="depth_30_ask_price"):
        validate_market_tick_columns(bad_columns)


def test_load_snapshots_for_instrument_builds_30_level_arrays_from_wide_csv(tmp_path):
    path = tmp_path / "ticks.csv"
    rows = []
    header = REQUIRED_COLUMNS
    row = {col: "0" for col in header}
    row.update(
        {
            "id": "1",
            "instrument_key": "NSE_FO|50591",
            "feed_timestamp_ms": "1781068073123",
            "received_at_utc": "2026-06-10T05:07:53.125681243Z",
            "last_traded_price": "103.85",
            "last_traded_time_ms": "1781068072593",
            "depth_levels_received": "30",
            "request_mode": "full_d30",
            "created_at": "2026-06-10 05:07:53",
        }
    )
    for level in range(1, 31):
        row[f"depth_{level}_bid_quantity"] = str(level * 10)
        row[f"depth_{level}_bid_price"] = str(100 - level)
        row[f"depth_{level}_ask_quantity"] = str(level * 20)
        row[f"depth_{level}_ask_price"] = str(100 + level)
    rows.append(row)

    other = dict(row)
    other["id"] = "2"
    other["instrument_key"] = "NSE_FO|OTHER"
    rows.append(other)

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    snapshots = load_snapshots_for_instrument(str(path), "NSE_FO|50591", downsample=1)

    assert snapshots == [
        Snapshot(
            ts="10:37:53",
            feed_timestamp_ms=1781068073123,
            ltp=103.85,
            bid_qty=[10 * i for i in range(1, 31)],
            bid_px=[100.0 - i for i in range(1, 31)],
            ask_qty=[20 * i for i in range(1, 31)],
            ask_px=[100.0 + i for i in range(1, 31)],
        )
    ]


def test_load_snapshots_downsamples_across_chunk_boundaries(tmp_path):
    path = tmp_path / "ticks.csv"
    header = REQUIRED_COLUMNS
    rows = []
    for row_id in range(1, 6):
        row = {col: "0" for col in header}
        row.update(
            {
                "id": str(row_id),
                "instrument_key": "NSE_FO|50591",
                "feed_timestamp_ms": str(row_id),
                "received_at_utc": f"2026-06-10T05:07:5{row_id}.000000000Z",
                "last_traded_price": str(100 + row_id),
                "last_traded_time_ms": str(row_id),
                "depth_levels_received": "30",
                "request_mode": "full_d30",
                "created_at": "2026-06-10 05:07:53",
            }
        )
        rows.append(row)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    snapshots = load_snapshots_for_instrument(str(path), "NSE_FO|50591", downsample=2, chunksize=3)

    assert [snap.feed_timestamp_ms for snap in snapshots] == [1, 3, 5]


def test_load_snapshots_with_count_returns_exact_matching_row_count(tmp_path):
    path = tmp_path / "ticks.csv"
    header = REQUIRED_COLUMNS
    rows = []
    for row_id in range(1, 6):
        row = {col: "0" for col in header}
        row.update(
            {
                "id": str(row_id),
                "instrument_key": "NSE_FO|50591",
                "feed_timestamp_ms": str(row_id),
                "received_at_utc": f"2026-06-10T05:07:5{row_id}.000000000Z",
                "last_traded_price": str(100 + row_id),
                "last_traded_time_ms": str(row_id),
                "depth_levels_received": "30",
                "request_mode": "full_d30",
                "created_at": "2026-06-10 05:07:53",
            }
        )
        rows.append(row)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    snapshots, total = load_snapshots_with_count(str(path), "NSE_FO|50591", downsample=2, chunksize=3)

    assert total == 5
    assert [snap.feed_timestamp_ms for snap in snapshots] == [1, 3, 5]
