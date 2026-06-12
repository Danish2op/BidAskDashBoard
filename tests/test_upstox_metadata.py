from tickdash.upstox_metadata import filter_upstox_instruments


def test_filter_upstox_instruments_keeps_only_requested_keys():
    instruments = [
        {"instrument_key": "NSE_FO|50591", "expiry": "2026-06-25"},
        {"instrument_key": "NSE_FO|OTHER", "expiry": "2026-06-25"},
    ]

    assert filter_upstox_instruments(instruments, {"NSE_FO|50591"}) == [
        {"instrument_key": "NSE_FO|50591", "expiry": "2026-06-25"}
    ]
