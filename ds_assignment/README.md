# NYC 311 Pothole Reports (CY2024) — feasibility, data quality, and a testable question

Assignment artifact set: frozen dataset, executable notebook, PDF report, data card,
data dictionary, AI-use log, and a results summary.

> **One-line result.** `status = "Closed"` does not mean "repaired" — only 76.6% of closed
> pothole records document a repair, and 11.7% are duplicate-collapses that close in a
> median of **zero hours**. Pooling them **inverts** the borough ranking: Queens is fastest
> under the naive definition, Manhattan under a repair-only definition, and both orderings
> are statistically significant. The gap is a measurement artifact, not a performance
> difference.

---

## Contents

| path | what it is |
|---|---|
| `notebooks/311_pothole_analysis.ipynb` | **primary deliverable** — 43 cells, executed top-to-bottom, 0 errors, 4 figures |
| `reports/311_pothole_report.pdf` | exported report, 51 pages |
| `docs/DATA_CARD.md` | data card: source, license, cohort, quality, limits, ethics |
| `docs/DATA_DICTIONARY.md` | field-level dictionary, generated from the data |
| `docs/AI_USE_LOG.md` | AI tool/task, accepted and **rejected** advice, verification |
| `docs/SUBMISSION_SUMMARY.md` | 234-word result summary for submission |
| `src/fetch_data.py` | the only network-touching code; defines the frozen version |
| `src/build_notebook.py` | regenerates the notebook from reviewable Python source |
| `src/make_data_dictionary.py` | regenerates the data dictionary from the data |
| `src/make_report.sh` | PDF export pipeline |
| `data/raw/` | **frozen extract + SHA-256 + source metadata** (committed) |
| `results/` | every number: tables, figures, metrics, environment manifest |
| `requirements.txt` | pinned dependencies |

---

## Data version

| item | value |
|---|---|
| Source | NYC Open Data `erm2-nwe9` — *311 Service Requests from 2020 to Present* |
| Publisher | 311 / NYC Mayor's Office of Technology & Innovation |
| **License** | **NYC Open Data Terms of Use** — free public access, no fee |
| Extract | `data/raw/nyc311_pothole_cy2024.json.gz` (2.88 MB) |
| **SHA-256** | **`58f59a05cd09d0d581555a1ffc9ea9641fe34cf858d7bd7eb6ef9cf7123c0d94`** |
| N | 38,801 — complete enumeration, no sampling |
| Version | `v1.0.0` |

**The hash pins this extract, not the upstream dataset.** `erm2-nwe9` refreshes daily and
the publisher documents that historical values change. The notebook asserts the digest on
load and aborts on mismatch.

---

## Reproduce

```bash
git clone <repo-url> && cd <repo>
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# verify the frozen extract (offline, no network needed)
.venv/bin/python -c "import gzip,hashlib,pathlib; \
  print(hashlib.sha256(gzip.decompress(pathlib.Path('data/raw/nyc311_pothole_cy2024.json.gz').read_bytes())).hexdigest())"
# expect: 58f59a05cd09d0d581555a1ffc9ea9641fe34cf858d7bd7eb6ef9cf7123c0d94

# run the notebook top-to-bottom
.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=900 --ExecutePreprocessor.kernel_name=python3 \
  notebooks/311_pothole_analysis.ipynb

# rebuild the PDF (needs Chrome/Chromium/Edge for headless printing)
./src/make_report.sh

# regenerate the data dictionary
.venv/bin/python src/make_data_dictionary.py
```

Rebuilding the notebook from source instead of editing it in place:

```bash
.venv/bin/python src/build_notebook.py
```

### Re-fetching from the API (optional)

Only needed to create a new version. ⚠ Upstream history is edited, so a later fetch will
**legitimately** differ; the new digest must be recorded in `docs/DATA_CARD.md` and the
notebook regenerated.

```bash
.venv/bin/python src/fetch_data.py     # rewrites data/raw/ + SHA256SUMS.txt + source_metadata.json
```

### Determinism

| control | status |
|---|---|
| data version | SHA-256 asserted on load |
| sampling | none — complete enumeration |
| seed | `20240101`, bootstrap only |
| bootstrap draws | 4,000, fixed |
| dependencies | pinned in `requirements.txt` |
| network | not touched by any notebook cell |
| environment manifest | `results/environment_used.json` |

---

## Notebook map

| § | contents |
|---|---|
| §0 | setup, seeds, environment capture |
| §1 | question, stakeholder, population, unit, target, estimand, boundaries, **DGP diagram**, **provenance lineage** |
| §2 | load frozen extract, **verify SHA-256**, confirm enumeration completeness |
| §3 | schema validation (48 declared / 33 present / 15 absent; nested-object trap) |
| §4 | range and domain checks (15 checks) |
| §5 | missingness and the three-tier geocoding problem |
| §6 | duplicates and the **unit-of-analysis mismatch** |
| §7 | anomalies (7 classes, including back-filled closure stamps) |
| §8 | **leakage audit** — field availability and a demonstrated 100% vs 72.1% leak |
| §9 | outcome taxonomy and the primary estimand under two definitions |
| §10 | **the counterexample**, sensitivity S1–S5b, unit-of-analysis effect |
| §11 | **negative results** and evidence against the author's own framing |
| §12 | **10 prohibited claims** and the one supported claim |
| §13 | results manifest |
| §14 | reproduction instructions |

---

## Headline numbers

| quantity | value |
|---|---|
| Cohort | 38,801 records, complete enumeration |
| Analysis set (closed, chronologically valid) | 36,518 |
| Median hours to **any** administrative closure | **21.99 h** |
| Median hours to a **recorded repair** | **23.30 h** |
| Share of closed records documenting a repair | 76.60% |
| Manhattan − Queens, naive | **+0.62 h** (95% CI +0.32 … +0.89) → Queens faster |
| Manhattan − Queens, repair-only | **−1.11 h** (95% CI −1.35 … −0.83) → Manhattan faster |
| Ranking changes under definition | **yes** |
| Impossible negative durations | 13 |
| Exactly-zero durations | 4,374 |
| Records with no street address | 14,517 (37.41%) |
| Still pending | 2,270 (5.85%) |
| H1 geocoding effect on repair time | +0.02 h (95% CI −0.24 … +0.28) — **null** |

All values are written to `results/tables/*.csv` and `results/metrics.json`.

**Clean-room reproduction was verified.** A fresh clone with a new virtualenv built from
`requirements.txt` alone re-executed the notebook and produced **byte-identical**
`metrics.json` and all 14 table CSVs, with 0 error outputs.

---

## Honest limits

1. These are **reported** potholes, not potholes. 311 coverage is unequal and unmeasured.
2. **No causal claim.** Every comparison is descriptive under a stated definition.
3. Right-censoring is **not uniform** across boroughs, so the closed-only estimand is not
   immune to the same composition problem. Flagged in §10.1, not resolved.
4. Bootstrap intervals assume exchangeable records, which repeat-reporting (§10.2) shows
   is not strictly true — the intervals are mildly optimistic for clustered addresses.
5. Verification was performed by the same agent that produced the analysis, using
   independent code paths. It is **not** third-party reproduction. See
   `docs/AI_USE_LOG.md` §4.1.
6. The PDF was verified structurally; nobody has eyeballed every page.
