from __future__ import annotations

from typing import Any, Iterable

import gspread
from google.oauth2.service_account import Credentials

from tickdash.metadata import METADATA_FIELDS


SHEETS_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]


class MetadataSheetStore:
    def __init__(self, worksheet: Any):
        self.worksheet = worksheet

    def load_by_instrument_key(self) -> dict[str, dict[str, Any]]:
        records = self.worksheet.get_all_records()
        return {
            str(record.get("instrument_key_as_seen")): record
            for record in records
            if record.get("instrument_key_as_seen")
        }

    def replace_all(self, rows: Iterable[dict[str, Any]]) -> None:
        values = [METADATA_FIELDS]
        for row in rows:
            values.append([row.get(field, "") for field in METADATA_FIELDS])
        self.worksheet.clear()
        self.worksheet.update("A1", values)


def open_metadata_store(service_account_json: str, spreadsheet_id: str, tab_name: str) -> MetadataSheetStore:
    creds = Credentials.from_service_account_file(service_account_json, scopes=SHEETS_SCOPE)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)
    try:
        worksheet = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=1000, cols=len(METADATA_FIELDS))
        worksheet.update("A1", [METADATA_FIELDS])
    return MetadataSheetStore(worksheet)

