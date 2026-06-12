from tickdash.depth_math import fill_per_level, iqr_stats


def test_iqr_stats_match_reference_dashboard_rules():
    stats = iqr_stats([1, 2, 3, 4, 5])

    assert stats == {
        "avg": 3.0,
        "min": 1.0,
        "max": 5.0,
        "median": 3.0,
        "q1": 2.0,
        "q3": 4.0,
        "iqr": 2.0,
        "fence_lo": -1.0,
        "fence_hi": 7.0,
        "outlier_pct": 0.0,
    }


def test_fill_per_level_buy_uses_asks_and_reports_weighted_and_sweep_slip():
    result = fill_per_level(
        prices=[100.0, 100.5, 101.0],
        quantities=[50, 50, 50],
        side="buy",
        order_qty=120,
        levels=[1, 2, 3],
    )

    assert result["fill_qty"] == 120
    assert result["unfilled"] == 0
    assert result["filled"] is True
    assert result["avg_price"] == 100.375
    assert result["ref_price"] == 100.0
    assert result["last_px"] == 101.0
    assert result["weighted_slip"] == 0.375
    assert result["sweep_slip"] == 1.0
    assert result["min_depth"] == 3


def test_fill_per_level_sell_uses_bids_and_reports_sell_slippage_direction():
    result = fill_per_level(
        prices=[99.8, 99.5],
        quantities=[20, 30],
        side="sell",
        order_qty=40,
        levels=[1, 2],
    )

    assert result["fill_qty"] == 40
    assert result["avg_price"] == 99.65
    assert result["weighted_slip"] == 0.15
    assert result["sweep_slip"] == 0.3
    assert result["min_depth"] == 2
