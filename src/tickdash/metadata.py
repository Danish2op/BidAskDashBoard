from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


METADATA_FIELDS = [
    "instrument_key_as_seen",
    "stable_contract_id",
    "segment",
    "exchange_token",
    "expiry",
    "instrument_type",
    "trading_symbol",
    "underlying_key",
    "underlying_symbol",
    "strike_price",
    "lot_size",
    "tick_size",
    "metadata_source",
    "metadata_fetched_at",
]


def build_stable_contract_id(meta: dict[str, Any]) -> str:
    segment = str(meta.get("segment") or "").strip()
    exchange_token = str(meta.get("exchange_token") or "").strip()
    expiry = str(meta.get("expiry") or "").strip()
    if segment == "NSE_EQ" and not expiry:
        expiry = "NO_EXPIRY"
    missing = [
        name
        for name, value in (
            ("segment", segment),
            ("exchange_token", exchange_token),
            ("expiry", expiry),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Cannot build stable contract id without {', '.join(missing)}")
    return f"{segment}|{exchange_token}|{expiry}"


def normalise_upstox_instrument(raw: dict[str, Any], source: str) -> dict[str, Any]:
    meta = {
        "instrument_key_as_seen": raw.get("instrument_key", ""),
        "segment": raw.get("segment", ""),
        "exchange_token": raw.get("exchange_token", ""),
        "expiry": raw.get("expiry", ""),
        "instrument_type": raw.get("instrument_type", ""),
        "trading_symbol": raw.get("trading_symbol", raw.get("tradingsymbol", "")),
        "underlying_key": raw.get("underlying_key", ""),
        "underlying_symbol": raw.get("underlying_symbol", ""),
        "strike_price": raw.get("strike_price", ""),
        "lot_size": raw.get("lot_size", ""),
        "tick_size": raw.get("tick_size", ""),
        "metadata_source": source,
        "metadata_fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    meta["stable_contract_id"] = build_stable_contract_id(meta)
    return {field: meta.get(field, "") for field in METADATA_FIELDS}
