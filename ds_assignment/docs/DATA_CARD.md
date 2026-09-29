# Data Card — NYC 311 Pothole Reports, CY2024

**Extract version:** `v1.0.0` · **Date frozen:** 2026-09-29 · **Status:** immutable, committed to this repository

---

## 1. Source

| field | value |
|---|---|
| Dataset name | *311 Service Requests from 2020 to Present* |
| Dataset ID | `erm2-nwe9` |
| Publisher | 311 / NYC Mayor's Office of Technology & Innovation (OTI) |
| Landing page | <https://data.cityofnewyork.us/City-Operations/311-Service-Requests-from-2020-to-Present/erm2-nwe9> |
| API endpoint | `https://data.cityofnewyork.us/resource/erm2-nwe9.json` |
| **License** | **NYC Open Data Terms of Use** — free public access, no fee, no registration |
| License text | <https://www.nyc.gov/site/analytics/analytics-policy.page> |
| Attribution required | "311" (per dataset metadata) |
| Upstream last updated at freeze time | 2026-09-29T01:44:54Z |
| Update frequency | **Daily** |

### 1.1 Legal usability

NYC Open Data is published by the City of New York for unrestricted public use under its
Open Data Terms of Use. There is no fee, no registration, and no restriction on
commercial or academic reuse. The publisher states the dataset does not reveal personally
identifying information; we performed **no** re-identification, geocoding, or enrichment
of our own. The cohort contains **street-level** addresses only (no house numbers), so it
cannot identify a household.

### 1.2 This extract

| field | value |
|---|---|
| File | `data/raw/nyc311_pothole_cy2024.json.gz` |
| **SHA-256 (canonical uncompressed JSON)** | **`58f59a05cd09d0d581555a1ffc9ea9641fe34cf858d7bd7eb6ef9cf7123c0d94`** |
| SHA-256 (gzip container) | see `data/raw/SHA256SUMS.txt` |
| Size | 2.88 MB gzipped / 36.32 MB raw |
| Rows | 38,801 |
| Columns | 33 (union across records) |
| Extraction time | 2026-09-29T01:48 UTC |

**Frozen query** (the complete definition of this version):

```sql
$select = *
$where  = created_date between '2024-01-01T00:00:00' and '2024-12-31T23:59:59'
          AND complaint_type='Street Condition'
          AND descriptor='Pothole'
$order  = unique_key ASC
$limit  = 5000
$paging = $offset increments of 5000 until a short page
```

The response is re-serialised with sorted keys and fixed separators before hashing, so the
digest depends on record **content**, not on server-side JSON key ordering.

### 1.3 ⚠ The hash pins *our extract*, not the upstream source

`erm2-nwe9` is refreshed daily and the publisher explicitly documents that *"expected
values for many fields will change over time"* — historical rows are **edited after the
fact**. A hash of the upstream dataset would therefore be meaningless: there isn't one
stable version to hash.

What the SHA-256 guarantees is that **this repository's analysis runs against exactly
these bytes**, forever, with no network access. It does not guarantee that re-running
`src/fetch_data.py` next month returns the same rows. Evidence that upstream mutation is
real: **11** records in this extract exceed a year of elapsed time, and **26** exceed
1,000 hours. The latest `closed_date` anywhere in the cohort is `2026-09-14T21:40`, just
15 days before extraction, and the single worst case was closed almost exactly two years
after it was created — the signature of a back-filled closure timestamp rather than a
two-year repair (§7 of the notebook).

---

## 2. Cohort definition

**Population.** All rows of `erm2-nwe9` with `complaint_type = 'Street Condition'`,
`descriptor = 'Pothole'`, and `created_date` within calendar year 2024.

**Sampling: complete enumeration.** All 38,801 matching rows were retrieved by paging
until the server returned a short page. This is a *census of the cohort*, not a sample:

* no sampling error, so no confidence intervals are needed for representativeness;
* no sampling bias, so no weighting or post-stratification;
* **no random seed is involved in data selection** — the only seeded step is bootstrap
  resampling of medians.

Completeness was verified against an independent server-side aggregation
(`$select=count(*)` with the identical `$where`), which returned 38,801 — an exact match.

### 2.1 Why "Pothole" and not all of "Street Condition"

`Street Condition` for 2024 contains 71,158 records across **23** distinct descriptors with
materially different latencies and different response workflows (`Cave-in` 9,946,
`Defective Hardware` 5,045, `Failed Street Repair` 3,526, …). Pooling them would mix
non-comparable work units and would *itself* be a measurement error. The restriction is a
deliberate boundary, and §10.1 of the notebook reports what it costs.

---

## 3. Structure

| field | value |
|---|---|
| Format | JSON array, gzip-compressed, canonical (sorted keys) |
| Grain | one row = one 311 **service request**, keyed by `unique_key` |
| ⚠ Unit of interest | one **road defect** — *not* the same as the grain. See §6. |
| Primary key | `unique_key` — verified unique, 0 duplicates |
| Row count | 38,801 |
| Time coverage | `created_date` from 2024-01-01T00:30:11 to 2024-12-31T23:24:25 |
| Intended use | operational service-performance analysis |
| Out-of-scope use | per-capita or per-km rates; causal claims; prevalence of road defects |

---

## 4. Fields

Full field-level documentation is in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md),
generated from the data itself. Summary:

* **29 intake-time columns** — populated when the report is filed.
* **4 post-outcome columns** — `closed_date`, `resolution_description`,
  `resolution_action_updated_date`, `status`. These are **inadmissible as model features**
  for any forward-looking claim (§8).
* **7 columns are constant** (`agency`, `agency_name`, `complaint_type`, `descriptor`,
  `facility_type`, `open_data_channel_type`, `park_facility_name`) — zero variance by
  construction of the cohort filter. `open_data_channel_type` is `UNKNOWN` for 100% of
  rows: **no information whatsoever**, and it is exactly the field needed to study how
  residents submit requests.
* **1 nested column** — `location` is a GeoJSON object, not a scalar. It breaks
  `nunique()`, `groupby()`, and any blanket column sweep.

---

## 5. Quality assessment

| dimension | assessment | detail |
|---|---|---|
| **Schema conformance** | ✅ good | every extract column exists in the publisher schema; no unknown columns |
| **Range / domain** | ✅ good | 13 of 15 checks return zero violations (§4) |
| **Missingness** | ⚠ structural | 100% of nulls are structural (censoring or geocoding), none accidental |
| **Duplicates** | ⚠ at a higher level | `unique_key` is unique, but 15.87% of addressed records are same-address same-day repeats |
| **Anomalies** | ❌ present | 13 impossible negative durations, 6 status/date contradictions, 11 records exceeding a year, 1 closure stamped 15 days before extraction |
| **Leakage risk** | ❌ severe | the outcome is *defined by* a column in the same table (§8) |
| **Label validity** | ❌ severe | `status='Closed'` does **not** mean repaired; only 76.6% of closed records assert a repair |
| **Timeliness** | ⚠ | upstream refreshes daily and edits history |

### 5.1 Missingness

Geocoding succeeds at three distinct rates, and they are not interchangeable:

| level | coverage |
|---|---|
| community board (text) | 100.00% |
| point geometry (lat/long) | 52.52% |
| street address | 37.41% |
| `closed_date` | 94.17% (5.83% right-censored) |

An analysis joining on `latitude` silently retains 52.5% of the cohort; one joining on
`incident_address` retains 37.4%. **Neither subset is the population.**

### 5.2 The central defect: the outcome label

`resolution_description` contains 13 distinct strings mapping to 8 semantic classes.
Among the 36,531 records with `status = "Closed"`:

| class | n | share of closed | median hours |
|---|---|---|---|
| REPAIRED | 27,984 | 76.60% | 23.30 |
| DUPLICATE_CLOSED | 4,261 | 11.66% | **0.00** |
| NOT_FOUND | 3,564 | 9.76% | 19.42 |
| ALREADY_FIXED | 613 | 1.68% | 25.46 |
| REFERRED | 71 | 0.19% | 26.98 |
| IN_PROGRESS_NOTE | 19 | 0.05% | 126.59 |
| OTHER | 17 | 0.05% | 28.44 |
| STATUS_NOT_PUBLISHED | 2 | 0.01% | 29.06 |

**23.40% of "closed" pothole records document no repair by DOT** — nearly one in four.
Because duplicate-closures complete in a median of **zero hours**, pooling them with
genuine repairs drags every summary statistic downward — and by a *different amount in
each borough*. This is the counterexample developed in §10 of the notebook.

---

## 6. Unit-of-analysis mismatch

The grain is the **service request**; the quantity anyone actually cares about is the
**road defect**. 311 does not merge reports at intake, so:

* 15.87% of addressed records share a street name *and* calendar day with another record;
* `incident_address` is street-level with no house number — `"BROADWAY"` appears **211
  times**, so it cannot identify a defect;
* locations reported ≥5 times take **3.50 h longer** to repair than locations reported
  once (95% CI +3.07 … +3.97).

Therefore a per-request median is **not** the median time to repair a pothole; it is the
median across reports, over-weighted toward chronic problem spots.

---

## 7. Ethical and operational considerations

* **No personal data.** Street-level addresses only, no house numbers, no names. No
  re-identification was attempted. The one repeated address value (`"BROADWAY"`, 211×) is
  a street name, not a household.
* **Do not publish per-neighbourhood league tables from this extract.** Reporting is
  self-selected and varies by neighbourhood; without a coverage denominator, a borough
  comparison measures *who complains*, not *who is served worse*.
* **Stakeholder conflict of interest.** NYC DOT wants records closed; NYC 311 wants
  `Closed` to mean done. This tension is the source of the measurement defect and should
  be raised with both, not resolved analytically.
* **Downstream use.** A model trained on `status` or `resolution_description` would learn
  back-office bookkeeping behaviour, not street conditions. Its error would be attributed
  to the city.
* **Upstream volatility.** Because history is edited, this extract is the only
  reproducible basis for any published figure. Cite the hash, not the dataset name.

---

## 8. Known limitations of this card

1. **The cohort is reported potholes, not potholes.** Coverage of 311 is unequal and
   unmeasured here.
2. **The hash does not version the upstream source.** It versions *this extract*.
3. **`open_data_channel_type` is unusable** (100% `UNKNOWN`), so submission channel —
   a plausible confounder — cannot be examined at all.
4. **Calendar hours only.** Night and weekend elapsed time is counted; a business-hours
   definition would change every number.
5. **Right-censoring is not uniformly distributed** across boroughs, so the closed-only
   estimand is not immune to the same composition problem documented in §5.2. Flagged,
   not resolved.
6. **Only 5 boroughs are compared.** `borough = 'Unspecified'` (125 records) is excluded.
7. **This card was written after seeing the data.** The *question, population, unit,
   target and estimand* were fixed before outcome inspection (§1 of the notebook), but the
   quality findings were not.

---

## 9. Provenance chain

```
NYC resident decides to report  ──►  311 intake  ──►  triage to DOT  ──►  field crew
        (SELECTION, unobserved)                                              │
                                                                              ▼
                                                            resolution_description
                                                                              │
   Socrata erm2-nwe9 (daily refresh, values editable after the fact)  ◄───────┘
        │
        ▼
   src/fetch_data.py   (frozen SoQL, $offset paging, canonical JSON, SHA-256)
        │
        ▼
   data/raw/nyc311_pothole_cy2024.json.gz   sha256 58f59a05…3c0d94
        │
        ▼
   notebooks/311_pothole_analysis.ipynb  ──►  results/  ──►  reports/*.pdf
```

Machine-readable lineage: `results/provenance_lineage.txt`.
Raw source metadata: `data/raw/source_metadata.json`. Digests: `data/raw/SHA256SUMS.txt`.
