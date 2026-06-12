from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse
import zipfile


def kaggle_auth(url: str, env: dict[str, str]) -> tuple[str, str] | None:
    parsed = urlparse(url.strip())
    username = env.get("KAGGLE_USERNAME", "").strip()
    key = env.get("KAGGLE_KEY", "").strip()
    if parsed.netloc == "www.kaggle.com" and username and key:
        return username, key
    return None


def materialize_uploaded_csv(filename: str, raw_bytes: bytes, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(raw_bytes).hexdigest()[:16]
    suffix = Path(filename).suffix or ".csv"
    path = cache_dir / f"upload_{digest}{suffix}"
    if not path.exists():
        path.write_bytes(raw_bytes)
    return path


def kaggle_dataset_download_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.netloc != "www.kaggle.com":
        return url.strip()
    if parsed.path.startswith("/api/v1/datasets/download/"):
        return url.strip()
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "datasets":
        return f"https://www.kaggle.com/api/v1/datasets/download/{parts[1]}/{parts[2]}"
    return url.strip()


def materialize_downloaded_file(url: str, raw_bytes: bytes, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256((url + str(len(raw_bytes))).encode("utf-8") + raw_bytes[:1024]).hexdigest()[:16]
    suffix = Path(urlparse(url).path).suffix.lower() or ".csv"

    if suffix == ".zip":
        zip_path = cache_dir / f"download_{digest}.zip"
        if not zip_path.exists():
            zip_path.write_bytes(raw_bytes)
        with zipfile.ZipFile(zip_path) as zf:
            csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
            if not csv_names:
                raise ValueError("Downloaded zip has no CSV file")
            output = cache_dir / f"download_{digest}_{Path(csv_names[0]).name}"
            if not output.exists():
                output.write_bytes(zf.read(csv_names[0]))
            return output

    if suffix not in {".csv", ".gz"}:
        suffix = ".csv"
    path = cache_dir / f"download_{digest}{suffix}"
    if not path.exists():
        path.write_bytes(raw_bytes)
    return path
