"""Pin RESET-05 part-2 implementation files via the existing SHA ledger format."""
import hashlib
import json
from pathlib import Path

from research.platform import sha_ledger

REPO = Path(__file__).resolve().parents[1]
WITNESS = REPO / "docs/PROJECT_RESET_20261030/06_RESET05_LEDGER_PART2_SHA_WITNESS.jsonl"


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def test_part2_witness_is_chained_and_pins_implementation():
    lines = WITNESS.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    events = [json.loads(line) for line in lines]
    assert sha_ledger.verify(events) == events[-1]["record_sha256"]
    payload = events[-1]["payload"]
    assert payload["phase"] == "RESET05_LEDGER_PART2"
    assert payload["live_allowed"] is False
    for path, expected_blob in payload["git_blobs"].items():
        assert git_blob_sha(REPO / path) == expected_blob, path
