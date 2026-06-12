from __future__ import annotations

import gzip
import json
from typing import Iterable

import requests


CURRENT_INSTRUMENTS_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"


def filter_upstox_instruments(
    instruments: Iterable[dict],
    requested_keys: set[str],
) -> list[dict]:
    return [item for item in instruments if item.get("instrument_key") in requested_keys]


def fetch_current_instrument_master(url: str = CURRENT_INSTRUMENTS_URL, timeout: int = 45) -> list[dict]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return json.loads(gzip.decompress(response.content).decode("utf-8"))


def fetch_current_metadata_for_keys(instrument_keys: set[str]) -> list[dict]:
    return filter_upstox_instruments(fetch_current_instrument_master(), instrument_keys)
