from tickdash.metadata import METADATA_FIELDS
from tickdash.metadata_store import MetadataSheetStore


class FakeWorksheet:
    def __init__(self, records=None):
        self.records = records or []
        self.appended = []
        self.cleared = False
        self.updated = []

    def get_all_records(self):
        return self.records

    def clear(self):
        self.cleared = True

    def update(self, range_name, values):
        self.updated.append((range_name, values))


def test_metadata_store_indexes_records_by_instrument_key():
    worksheet = FakeWorksheet(
        [
            {
                "instrument_key_as_seen": "NSE_FO|50591",
                "stable_contract_id": "NSE_FO|50591|2026-06-25",
            }
        ]
    )

    store = MetadataSheetStore(worksheet)

    assert store.load_by_instrument_key()["NSE_FO|50591"]["stable_contract_id"] == "NSE_FO|50591|2026-06-25"


def test_metadata_store_rewrites_header_and_rows_in_declared_order():
    worksheet = FakeWorksheet()
    row = {field: f"value-{field}" for field in METADATA_FIELDS}

    MetadataSheetStore(worksheet).replace_all([row])

    assert worksheet.cleared is True
    assert worksheet.updated == [
        (
            "A1",
            [
                METADATA_FIELDS,
                [row[field] for field in METADATA_FIELDS],
            ],
        )
    ]

