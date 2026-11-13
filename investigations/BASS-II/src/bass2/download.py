"""Downloads from the NASA PSI repository through presigned S3 URLs.

Discovered endpoint (public, no authentication):
    GET https://psi.nasa.gov/geode-py/ws/studies/PSI-25/download?file=<name>&redirect=false
    -> returns a presigned S3 URL as plain text (expires within minutes).

Downloaded files are UNTRUSTED DATA: they are never executed; they are stored under
data/raw/<test_id>/ and only read through decoders (ffmpeg/opencv/rawpy).
"""
from __future__ import annotations

import time
import urllib.parse
from pathlib import Path

import requests
from tqdm import tqdm

from .config import load_config

CHUNK = 1 << 20


def presigned_url(file_name: str, session: requests.Session | None = None) -> str:
    cfg = load_config()
    s = session or requests.Session()
    q = urllib.parse.quote(file_name)
    r = s.get(f"{cfg['nasa']['download_url']}?file={q}&redirect=false", timeout=60)
    r.raise_for_status()
    url = r.text.strip().strip('"')
    if not url.startswith("https://"):
        raise RuntimeError(f"Unexpected response for {file_name!r}: {url[:200]}")
    return url


def download_file(file_name: str, dest_dir: str | Path, expected_size: int | None = None,
                  retries: int = 4) -> Path:
    """Resumable download (HTTP Range). Skipped if the file already exists with the expected size."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / file_name.replace("PSI-25_Raw Data_", "").replace("PSI-25_", "")
    if out.exists() and expected_size and out.stat().st_size == expected_size:
        return out
    part = out.with_suffix(out.suffix + ".part")
    s = requests.Session()
    for attempt in range(retries):
        try:
            have = part.stat().st_size if part.exists() else 0
            url = presigned_url(file_name, s)  # request a fresh URL every attempt (they expire)
            headers = {"Range": f"bytes={have}-"} if have else {}
            with s.get(url, headers=headers, stream=True, timeout=120) as r:
                if r.status_code == 416:  # already complete
                    break
                r.raise_for_status()
                mode = "ab" if have and r.status_code == 206 else "wb"
                total = expected_size or (int(r.headers.get("Content-Length", 0)) + (have if mode == "ab" else 0))
                with open(part, mode) as fh, tqdm(total=total, initial=have if mode == "ab" else 0,
                                                  unit="B", unit_scale=True, desc=out.name[:40]) as bar:
                    for chunk in r.iter_content(CHUNK):
                        fh.write(chunk)
                        bar.update(len(chunk))
            break
        except (requests.RequestException, OSError) as e:
            wait = 2 ** attempt
            print(f"[download] attempt {attempt + 1} failed ({e}); retrying in {wait}s")
            time.sleep(wait)
    else:
        raise RuntimeError(f"Could not download {file_name}")
    if expected_size and part.stat().st_size != expected_size:
        raise RuntimeError(f"Wrong size {part.stat().st_size} != {expected_size} ({file_name})")
    part.replace(out)
    return out


def download_test(test_id: str, kinds: tuple[str, ...] = ("main_video",),
                  max_bytes: int | None = None) -> list[Path]:
    """Download the files of one test filtered by kind (see catalog.classify_file)."""
    from .catalog import build_inventory

    inv = build_inventory(write=False)
    sel = inv[(inv.test_id == test_id) & (inv.kind.isin(kinds))]
    if max_bytes:
        sel = sel[sel.size_bytes <= max_bytes]
    dest = load_config().path("raw") / test_id
    return [download_file(r.file_name, dest, r.size_bytes) for r in sel.itertuples()]


def fetch_docs() -> list[Path]:
    """Download the non-Raw-Data documents to data/docs/."""
    from .catalog import fetch_investigation

    inv = fetch_investigation()
    files = [f for f in inv["added"] if f.get("visible", True)
             and f["remote_path"].split("/")[4] != "Raw Data"]
    files += inv.get("experimentalTable", []) + inv.get("images", [])
    dest = load_config().path("catalog").parent / "docs"
    return [download_file(f["file_name"], dest, int(f.get("file_size") or 0) or None) for f in files]
