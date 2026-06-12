from tickdash.metadata_refresh import merge_metadata_rows


def test_merge_metadata_rows_replaces_fetched_rows_and_keeps_existing_missing_rows():
    existing = {
        "NSE_FO|OLD": {
            "instrument_key_as_seen": "NSE_FO|OLD",
            "stable_contract_id": "NSE_FO|OLD|2025-04-17",
            "expiry": "2025-04-17",
        }
    }
    fetched = [
        {
            "instrument_key": "NSE_FO|NEW",
            "segment": "NSE_FO",
            "exchange_token": "50591",
            "expiry": "2026-06-25",
            "instrument_type": "CE",
        }
    ]

    rows = merge_metadata_rows({"NSE_FO|OLD", "NSE_FO|NEW"}, existing, fetched)
    by_key = {row["instrument_key_as_seen"]: row for row in rows}

    assert by_key["NSE_FO|OLD"]["stable_contract_id"] == "NSE_FO|OLD|2025-04-17"
    assert by_key["NSE_FO|NEW"]["stable_contract_id"] == "NSE_FO|50591|2026-06-25"
