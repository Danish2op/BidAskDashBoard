from pathlib import Path
import zipfile

from tickdash.app_helpers import (
    kaggle_auth,
    kaggle_dataset_download_url,
    materialize_downloaded_file,
    materialize_uploaded_csv,
)


def test_materialize_uploaded_csv_writes_stable_temp_file(tmp_path):
    path1 = materialize_uploaded_csv("ticks.csv", b"a,b\n1,2\n", tmp_path)
    path2 = materialize_uploaded_csv("ticks.csv", b"a,b\n1,2\n", tmp_path)

    assert path1 == path2
    assert path1.name.startswith("upload_")
    assert path1.read_text() == "a,b\n1,2\n"


def test_materialize_uploaded_csv_changes_path_when_content_changes(tmp_path):
    path1 = materialize_uploaded_csv("ticks.csv", b"a,b\n1,2\n", tmp_path)
    path2 = materialize_uploaded_csv("ticks.csv", b"a,b\n3,4\n", tmp_path)

    assert path1 != path2


def test_kaggle_dataset_download_url_converts_dataset_page():
    url = kaggle_dataset_download_url("https://www.kaggle.com/datasets/danish2op/bidaskdashboard")

    assert url == "https://www.kaggle.com/api/v1/datasets/download/danish2op/bidaskdashboard"


def test_kaggle_dataset_download_url_leaves_api_url_unchanged():
    url = "https://www.kaggle.com/api/v1/datasets/download/danish2op/bidaskdashboard"

    assert kaggle_dataset_download_url(url) == url


def test_kaggle_auth_returns_basic_auth_tuple_only_for_kaggle_urls():
    env = {"KAGGLE_USERNAME": "alice", "KAGGLE_KEY": "secret"}

    assert kaggle_auth("https://www.kaggle.com/api/v1/datasets/download/a/b", env) == ("alice", "secret")
    assert kaggle_auth("https://example.test/file.csv", env) is None


def test_kaggle_auth_ignores_incomplete_credentials():
    env = {"KAGGLE_USERNAME": "alice"}

    assert kaggle_auth("https://www.kaggle.com/api/v1/datasets/download/a/b", env) is None


def test_materialize_downloaded_file_extracts_first_csv_from_zip(tmp_path):
    zip_path = tmp_path / "dataset.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("notes.txt", "ignore")
        zf.writestr("market_ticks.csv", "a,b\n1,2\n")

    csv_path = materialize_downloaded_file("https://example.test/data.zip", zip_path.read_bytes(), tmp_path)

    assert csv_path.name.endswith(".csv")
    assert csv_path.read_text() == "a,b\n1,2\n"


def test_materialize_downloaded_file_extracts_zip_bytes_without_zip_suffix(tmp_path):
    zip_path = tmp_path / "dataset.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("market_ticks.csv", "a,b\n1,2\n")

    csv_path = materialize_downloaded_file("https://www.kaggle.com/api/v1/datasets/download/a/b", zip_path.read_bytes(), tmp_path)

    assert csv_path.name.endswith(".csv")
    assert csv_path.read_text() == "a,b\n1,2\n"


def test_materialize_downloaded_file_stores_csv_bytes(tmp_path):
    csv_path = materialize_downloaded_file("https://example.test/market_ticks.csv", b"a,b\n1,2\n", tmp_path)

    assert csv_path.name.endswith(".csv")
    assert csv_path.read_text() == "a,b\n1,2\n"
