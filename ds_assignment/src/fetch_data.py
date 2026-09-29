"""
Fetch and freeze the analysis cohort from the NYC Open Data Socrata API.

This script is the ONLY component that touches the network. It produces an
immutable, content-addressed extract so that every downstream step (notebook,
PDF report, tables) runs offline against exactly the bytes recorded here.

Design notes
------------
* The upstream dataset ``erm2-nwe9`` is refreshed DAILY and NYC explicitly
  documents that "expected values for many fields will change over time".
  A hash of the upstream source would therefore be meaningless. The hash we
  record pins *our extract*, not the source. This distinction is stated in the
  data card.
* The extract is a COMPLETE ENUMERATION of a pre-declared cohort. There is no
  sampling step, therefore no sampling bias and no seed to tune.
* The response is re-serialised canonically (sorted keys, fixed separators)
  before hashing so that the SHA-256 depends on record *content* and not on
  JSON key ordering returned by the server.

Usage:  python src/fetch_data.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# FROZEN PARAMETERS -- change these only by creating a new version tag.
# --------------------------------------------------------------------------
API_RESOURCE = "erm2-nwe9"
API_URL = f"https://data.cityofnewyork.us/resource/{API_RESOURCE}.json"
API_SCHEMA_URL = f"https://data.cityofnewyork.us/api/views/{API_RESOURCE}.json"

COHORT_WHERE = (
    "created_date between '2024-01-01T00:00:00' and '2024-12-31T23:59:59'"
    " AND complaint_type='Street Condition'"
    " AND descriptor='Pothole'"
)
PAGE_SIZE = 5_000
MAX_PAGES = 200
HTTP_TIMEOUT = 120
HTTP_RETRIES = 5

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RAW_FILE = RAW_DIR / "nyc311_pothole_cy2024.json.gz"
SUM_FILE = RAW_DIR / "SHA256SUMS.txt"
META_FILE = RAW_DIR / "source_metadata.json"
SCHEMA_FILE = RAW_DIR / "source_schema.json"


def _get(url: str, params: dict | None = None, retries: int = HTTP_RETRIES) -> bytes:
    """GET with bounded exponential backoff. Returns raw bytes."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ds-assignment/1.0"})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
                return resp.read()
        except Exception as err:  # noqa: BLE001 - network is genuinely unreliable
            last_err = err
            wait = 2 ** attempt
            print(f"    ! attempt {attempt + 1}/{retries} failed ({err}); sleeping {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"GET failed after {retries} attempts: {url}") from last_err


def fetch_cohort() -> list[dict]:
    """Paginate the frozen cohort query to exhaustion, ordered by unique_key."""
    records: list[dict] = []
    offset = 0
    page = 0
    while page < MAX_PAGES:
        page += 1
        params = {
            "$select": "*",
            "$where": COHORT_WHERE,
            "$order": "unique_key ASC",
            "$limit": str(PAGE_SIZE),
            "$offset": str(offset),
        }
        chunk = json.loads(_get(API_URL, params).decode("utf-8"))
        if not isinstance(chunk, list):
            raise RuntimeError(f"unexpected payload type {type(chunk)} at offset {offset}")
        print(f"    page {page:>3}  offset={offset:<7} rows={len(chunk)}")
        records.extend(chunk)
        if len(chunk) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    else:
        raise RuntimeError(f"exceeded MAX_PAGES={MAX_PAGES}; cohort larger than expected")

    # Canonical ordering: unique_key is a zero-padded text id -> sort as int.
    records.sort(key=lambda r: int(r["unique_key"]))
    return records


def canonical_bytes(records: list[dict]) -> bytes:
    """Deterministic serialisation used for hashing and for the stored file."""
    return json.dumps(
        records, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[1/5] Fetching frozen cohort from {API_RESOURCE}")
    print(f"      $where = {COHORT_WHERE}")
    records = fetch_cohort()
    print(f"      complete enumeration -> {len(records):,} records")

    payload = canonical_bytes(records)
    sha256 = hashlib.sha256(payload).hexdigest()
    print(f"[2/5] Canonical SHA-256 = {sha256}")

    # gzip with mtime=0 so the *compressed* bytes are also reproducible.
    with gzip.GzipFile(RAW_FILE, "wb", compresslevel=9, mtime=0) as fh:
        fh.write(payload)
    gz_sha = hashlib.sha256(RAW_FILE.read_bytes()).hexdigest()
    print(f"[3/5] Wrote {RAW_FILE.relative_to(ROOT)} "
          f"({RAW_FILE.stat().st_size / 1e6:.2f} MB, gzip sha256 {gz_sha[:16]}...)")

    print("[4/5] Capturing upstream source metadata + schema")
    schema = json.loads(_get(API_SCHEMA_URL).decode("utf-8"))
    SCHEMA_FILE.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")

    meta = {
        "extract_name": RAW_FILE.name,
        "extract_sha256_uncompressed": sha256,
        "extract_sha256_gzip": gz_sha,
        "extract_bytes_uncompressed": len(payload),
        "n_records": len(records),
        "api_endpoint": API_URL,
        "frozen_query": {
            "$where": COHORT_WHERE,
            "$order": "unique_key ASC",
            "$limit": PAGE_SIZE,
            "paging": "$offset increments of 5000 until a short page",
            "selection": "complete enumeration (no sampling)",
        },
        "source": {
            "dataset_id": schema.get("id"),
            "dataset_name": schema.get("name"),
            "attribution": schema.get("attribution"),
            "publisher": "NYC Mayor's Office of Technology & Innovation (OTI) / 311",
            "source_rows_updated_at_epoch": schema.get("rowsUpdatedAt"),
            "source_rows_updated_at_utc": datetime.fromtimestamp(
                schema["rowsUpdatedAt"], tz=timezone.utc
            ).isoformat(),
            "source_is_mutable": True,
            "source_mutability_note": (
                "Upstream is refreshed daily and field values can be edited after "
                "the fact. The SHA-256 above pins OUR EXTRACT, not the upstream "
                "dataset. Re-running this script later will legitimately produce a "
                "different hash."
            ),
            "license": "NYC Open Data Terms of Use (free public access, no fee)",
            "license_url": "https://www.nyc.gov/site/analytics/analytics-policy.page",
            "dataset_page": "https://data.cityofnewyork.us/City-Operations/311-Service-Requests-from-2020-to-Present/erm2-nwe9",
            "personal_data_note": (
                "Upstream 311 data is published without personally identifying "
                "information; the publisher states PII is not revealed. We add no "
                "geocoding or enrichment of our own."
            ),
        },
        "extracted_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "python": sys.version.split()[0],
    }
    META_FILE.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

    print("[5/5] Writing SHA256SUMS.txt")
    SUM_FILE.write_text(
        f"{sha256}  {RAW_FILE.name} (canonical uncompressed JSON)\n"
        f"{gz_sha}  {RAW_FILE.name} (gzip container)\n",
        encoding="utf-8",
    )
    print("\nDone. Frozen extract is now immutable; re-running the notebook will "
          "not touch the network.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
