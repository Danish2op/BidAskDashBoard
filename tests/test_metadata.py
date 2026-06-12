import pytest

from tickdash.metadata import build_stable_contract_id, normalise_upstox_instrument


def test_stable_contract_id_includes_expiry_to_avoid_reused_exchange_token():
    meta = {
        "segment": "NSE_FO",
        "exchange_token": "50591",
        "expiry": "2026-06-25",
    }

    assert build_stable_contract_id(meta) == "NSE_FO|50591|2026-06-25"


def test_stable_contract_id_rejects_missing_expiry():
    with pytest.raises(ValueError, match="expiry"):
        build_stable_contract_id({"segment": "NSE_FO", "exchange_token": "50591"})


def test_stable_contract_id_allows_no_expiry_for_equity():
    meta = {"segment": "NSE_EQ", "exchange_token": "12345", "expiry": ""}

    assert build_stable_contract_id(meta) == "NSE_EQ|12345|NO_EXPIRY"


def test_normalise_upstox_instrument_keeps_original_key_and_contract_fields():
    raw = {
        "instrument_key": "NSE_FO|50591",
        "segment": "NSE_FO",
        "exchange_token": "50591",
        "expiry": "2026-06-25",
        "instrument_type": "CE",
        "trading_symbol": "NIFTY26JUN25000CE",
        "underlying_key": "NSE_INDEX|Nifty 50",
        "underlying_symbol": "NIFTY",
        "strike_price": 25000,
        "lot_size": 65,
        "tick_size": 5,
    }

    meta = normalise_upstox_instrument(raw, source="upstox_current_master")

    assert meta["instrument_key_as_seen"] == "NSE_FO|50591"
    assert meta["stable_contract_id"] == "NSE_FO|50591|2026-06-25"
    assert meta["instrument_type"] == "CE"
    assert meta["strike_price"] == 25000
    assert meta["metadata_source"] == "upstox_current_master"
