from tickdash.ui_model import chart_key, make_fill_rows, make_ladder_rows, preferred_default_key, select_snapshot_index


def test_preferred_default_key_uses_first_fo_contract_before_equity():
    assert preferred_default_key(["NSE_EQ|ABC", "NSE_FO|50591", "NSE_FO|50592"]) == "NSE_FO|50591"


def test_chart_key_is_stable_for_streamlit_button_state():
    assert chart_key("Spread with IQR bands") == "chart_spread_with_iqr_bands"


def test_select_snapshot_index_returns_first_timestamp_at_or_after_input():
    assert select_snapshot_index(["10:00:00", "10:00:03", "10:00:05"], "10:00:02") == 1
    assert select_snapshot_index(["10:00:00", "10:00:03"], "") == -1
    assert select_snapshot_index(["10:00:00"], "11:00:00") == 0


def test_make_ladder_rows_uses_selected_levels_and_converts_quantities_to_lots():
    snap = {
        "bp": [100.0, 99.5],
        "bq": [65, 130],
        "ap": [100.5, 101.0],
        "aq": [195, 65],
    }

    rows = make_ladder_rows(snap, [1, 2], lot_size=65)

    assert rows == [
        {"level": 1, "bid_lots": 1.0, "bid_price": 100.0, "ask_price": 100.5, "ask_lots": 3.0},
        {"level": 2, "bid_lots": 2.0, "bid_price": 99.5, "ask_price": 101.0, "ask_lots": 1.0},
    ]


def test_make_fill_rows_tracks_running_fill_lots():
    snap = {
        "ap": [100.5, 101.0, 101.5],
        "aq": [65, 130, 999],
        "bp": [100.0, 99.5, 99.0],
        "bq": [65, 130, 999],
    }

    result = make_fill_rows(snap, side="buy", lots=2, lot_size=65, levels=[1, 2, 3])

    assert result["stats"]["fill_qty"] == 130
    assert result["rows"] == [
        {"level": 1, "price": 100.5, "avail_lots": 1.0, "taken_lots": 1.0, "running_fill_lots": 1.0},
        {"level": 2, "price": 101.0, "avail_lots": 2.0, "taken_lots": 1.0, "running_fill_lots": 2.0},
    ]
