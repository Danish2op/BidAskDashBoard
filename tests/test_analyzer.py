from tickdash.analyzer import KEY_DEPTHS, analyze_snapshots
from tickdash.csv_loader import Snapshot


def test_analyze_snapshots_builds_reference_payload_metrics():
    snapshots = [
        Snapshot(
            ts="10:00:00",
            feed_timestamp_ms=1,
            ltp=100.0,
            bid_qty=[65, 65] + [0] * 28,
            bid_px=[99.9, 99.8] + [0.0] * 28,
            ask_qty=[65, 65] + [0] * 28,
            ask_px=[100.1, 100.3] + [0.0] * 28,
        ),
        Snapshot(
            ts="10:00:01",
            feed_timestamp_ms=2,
            ltp=101.0,
            bid_qty=[130, 65] + [0] * 28,
            bid_px=[100.8, 100.6] + [0.0] * 28,
            ask_qty=[65, 130] + [0] * 28,
            ask_px=[101.2, 101.5] + [0.0] * 28,
        ),
    ]

    data = analyze_snapshots(snapshots, lot_size=65, order_lots=2, total_snapshots=10)

    assert data["key_depths"] == KEY_DEPTHS
    assert data["summary"]["total_snapshots"] == 10
    assert data["summary"]["sampled_snapshots"] == 2
    assert data["summary"]["time_start"] == "10:00:00"
    assert data["summary"]["time_end"] == "10:00:01"
    assert data["summary"]["ltp_latest"] == 101.0
    assert data["spread_series"] == [0.2, 0.4]
    assert data["cum_bid"]["1"] == [1.0, 2.0]
    assert data["cum_ask"]["2"] == [2.0, 3.0]
    assert data["per_level_buy"]["2"]["fill_qty"] == [2.0, 2.0]
    assert data["per_level_buy"]["1"]["fill_qty"] == [1.0, 1.0]
    assert data["per_level_sell"]["2"]["w_slip"][0] == 0.05
    assert data["min_depth_buy"] == [2, 2]
    assert data["min_depth_sell"] == [2, 1]
    assert data["ask_depth_slip"][:2] == [0.0, 0.3]
    assert data["bid_depth_slip"][:2] == [0.0, 0.2]
    assert data["allday"]["spread"]["median"] == 0.3
