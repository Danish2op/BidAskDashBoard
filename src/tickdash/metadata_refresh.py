from __future__ import annotations

from tickdash.metadata import normalise_upstox_instrument


def merge_metadata_rows(
    instrument_keys: set[str],
    existing_by_key: dict[str, dict],
    fetched_instruments: list[dict],
) -> list[dict]:
    fetched_by_key = {}
    for item in fetched_instruments:
        key = item.get("instrument_key")
        if key not in instrument_keys:
            continue
        try:
            fetched_by_key[key] = normalise_upstox_instrument(item, source="upstox_current_master")
        except ValueError:
            continue
    merged = []
    for key in sorted(instrument_keys):
        if key in fetched_by_key:
            merged.append(fetched_by_key[key])
        elif key in existing_by_key:
            merged.append(existing_by_key[key])
    return merged
