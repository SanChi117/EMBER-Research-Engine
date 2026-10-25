#!/usr/bin/env python3
"""Fetch and SHA-verify the 160 public original Binance USD-M 3m daily ZIPs."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PINNED = ROOT / "evidence/iso03/ISO03_ORIGINAL_BINANCE_160ZIP_MANIFEST.json"


def fetch(name, receipt, target):
    path = target / name
    if path.exists():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() == receipt["sha256"] and len(raw) == receipt["bytes"]:
            return name, True
    url = f"https://data.binance.vision/data/futures/um/daily/klines/{name.split('-', 1)[0]}/3m/{name}"
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Ember-research/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
            if not raw.startswith(b"PK") or len(raw) != receipt["bytes"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
                raise ValueError("ISO03_DOWNLOADED_SOURCE_MISMATCH")
            path.write_bytes(raw)
            return name, True
        except Exception:
            if attempt == 4:
                raise
            time.sleep(attempt + 1)


def main(target):
    target = Path(target); target.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(PINNED.read_text())
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch, name, receipt, target) for name, receipt in sorted(manifest.items())]
        for future in futures:
            print(*future.result())
    (target / "manifest.json").write_bytes(PINNED.read_bytes())
    print("ISO03_SOURCE_ARCHIVES_VERIFIED", len(manifest))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / "data")
