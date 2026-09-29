# AI Use Log

**Disclosure for the NYC 311 pothole cohort analysis (`v1.0.0`, 2026-09-29).**

---

## 1. Disclosure

| item | detail |
|---|---|
| **Tool** | `opencode`, an AI coding agent, running as model **`big-pickle`** (`opencode/big-pickle`) |
| **Interface** | terminal CLI in the author's local workspace; full read/write access to the repository and shell |
| **Sessions** | one continuous working session covering dataset selection, extraction, analysis design, coding, debugging, documentation, and packaging |
| **Extent of involvement** | **Substantial and continuous.** The agent wrote `src/fetch_data.py`, `src/build_notebook.py`, `src/make_data_dictionary.py`, and `src/make_report.sh`; selected the cohort; designed every check; executed the analysis; produced the figures; and drafted this repository's documents. The human's contribution was: the task brief, the decision to use NYC 311, the decision to keep artifacts local rather than publish, the requirement to expose errors rather than hide them, and final review. |
| **Data used for training / sent to a third party** | The 38,801 public 311 records, downloaded from the NYC Open Data API. No credentials, keys, or personal data were ever transmitted, requested, or exposed. No dataset row was uploaded anywhere for any purpose. |
| **Fabrication** | None. Every number in this repository derives from the frozen extract, which is committed and hash-verified. No experiment, user, execution, or result was invented. Where a step failed, the failure is recorded below and in `results/`. |

---

## 2. Tasks delegated to the AI, and what was accepted

| # | Task | AI proposal | Disposition |
|---|---|---|---|
| 1 | Dataset selection | Propose NYC 311 over Adult/COMPAS, on the grounds that it offers a genuine measurement counterexample rather than a textbook one | **Accepted.** Human chose it after weighing reproducibility risk against counterexample strength. |
| 2 | Cohort design | Use a **complete enumeration** of a narrow cohort (`Street Condition` + `Pothole` + CY2024) rather than a sample of a broad one, eliminating sampling bias entirely | **Accepted.** N = 38,801; completeness independently confirmed by a server-side `count(*)`. |
| 3 | Primary framing | Make `status='Closed'` conflating several dispositions the headline issue, and test whether the borough ranking survives a repair-only definition | **Accepted** — this became §9–§10 and the report's central result. |
| 4 | Leakage framing | Note that the outcome is *defined by* `resolution_description`, making the obvious model trivially circular; build a field-availability audit | **Accepted.** Produced the 100%-vs-72.1% leakage demonstration. |
| 5 | Statistics | Use numpy percentile bootstrap, seeded, rather than adding SciPy/sklearn | **Accepted.** Keeps the dependency set small and the inference transparent. |
| 6 | Tooling | Skip LaTeX (not installed); export HTML via nbconvert then print with headless Chromium | **Accepted.** 44-page PDF, no extra system dependency. |
| 7 | Rigour | Retain null results, sensitivity analyses, and explicit prohibited claims rather than reporting only the significant finding | **Accepted.** §11 and §12 exist because of this. |

---

## 3. Advice and output that was **rejected** or corrected

These are recorded because the assignment requires evidence that challenges the work,
including challenges to the agent's own contribution.

### 3.1 A proposed counterexample that the data killed

> **AI proposal (rejected).** The strong counterexample would be **geocoding**: requests
> the geocoder could place would be routed faster, so a borough with poor geocoding would
> show an artificially bad median. Proposed as the centrepiece of §10.

**Why rejected:** the first cohort probe showed `community_board` populated for
**100%** of pothole records — administrative geocoding never fails for this cohort, so
geocoding cannot discriminate between boroughs. The proposal was discarded and replaced
with the closure-mix counterexample, which *is* supported by the data.

The follow-up hypothesis — that address availability affects repair latency — was then
tested as **H1** and came back **null** (+0.02 h, 95% CI −0.24 … +0.28). That null is
reported in §11 as a rejected hypothesis, and it is load-bearing: it removes geocoding as
a rival explanation for the borough differences.

### 3.2 Two outright factual errors by the AI, caught by verification

**(a) "The dataset has 24 columns."** The agent read `records[0].keys()` and concluded 24
columns. Wrong. Socrata omits null fields **per record**, so a single row cannot reveal
the table's width. The union across all 38,801 records is **33** columns, of which 15
declared source columns are absent entirely.

*Correction:* the §3 schema cell now unions keys across all records and reports the
per-record key range (19–32). The error is documented in §3 of the notebook and in
`docs/DATA_DICTIONARY.md` rather than quietly deleted.

**(b) A silent all-NaN parse.** `pd.to_datetime(..., format="%Y-%m-%dT%H:%M:%S",
errors="coerce")` was used on values that carry **milliseconds** (`...T01:24:43.000`).
Every row coerced to `NaN` **without raising any error**, and the notebook ran to
completion producing an empty analysis set (`analysis_set_n: 0`) and a full set of
confidently-printed `NaN` results.

*How it was caught:* inspecting `results/metrics.json` after execution and noticing
`analysis_set_n: 0`. *Correction:* the format string was replaced with `format="ISO8601"`,
and — the durable fix — §7 now **asserts** that `elapsed_h` is not entirely null. A parse
failure can no longer pass silently.

### 3.3 Four further defects found and fixed during execution

| defect | symptom | fix |
|---|---|---|
| variable shadowing | `observed` (the extract SHA-256) was rebound in the §3 loop, so `metrics.json` recorded `"extract_sha256": "object"` | renamed to `EXTRACT_SHA256` / `obs_dtype` |
| `rank().astype(int)` on nulls | `IntCastingNaNError` — borough `Unspecified` has **zero** repair-only records, so its median is null and unrankable | nullable `Int64`; ranks restricted to the five named boroughs |
| `Accept: text/csv` ignored | two fetches silently returned JSON parsed as CSV, producing a garbage single-column header | switched to the canonical JSON representation, which is better provenance anyway (explicit nulls) |
| **unit error in a threshold** | an anomaly was labelled `elapsed > 365 days` while the test was `elapsed_h > 365` — i.e. **365 hours ≈ 15.25 days**. The count (116) was an order of magnitude above the true >365-day count (11) | both thresholds now reported separately with units in the label; `results/tables/anomalies.csv` |

The last one is the most serious, because a mislabelled unit is invisible in the number
itself — only cross-checking the label against the code reveals it. It was caught by
re-deriving every figure quoted in `DATA_CARD.md` against the raw extract rather than
against the committed CSVs, which is why that audit existed.

### 3.4 A claim the AI wanted to make and did not

During drafting, the AI proposed stating that the Queens/Manhattan ordering "changes
depending on definition" without qualifying it. On inspection the significance is real
but the **effect size under the naive definition is +0.62 hours** — about 37 minutes on a
20-hour median. That is statistically robust and operationally trivial.

The claim was therefore **not** made as stated. §11 now carries an explicit caution that
statistical significance is not operational salience, and the counterexample is framed as
a question of *validity* rather than as a large performance difference.

### 3.5 Overstated framing, corrected

The AI initially described borough differences as if they might reflect "service
quality". The word **performance** was removed from the conclusions: with crew identity,
workload, severity, and dispatch policy all unobserved, no such attribution is available.
All five borough comparisons are reported as **descriptive under a stated definition**,
and "crews are underperforming" is listed as a prohibited claim.

---

## 4. Independent verification performed

Verification was deliberately adversarial: the goal was to find reasons to *not* trust the
headline result.

| # | check | method | outcome |
|---|---|---|---|
| 1 | **Data integrity** | SHA-256 of the extract computed at load time and asserted against `data/raw/SHA256SUMS.txt` | ✅ passes; analysis aborts on mismatch |
| 2 | **Enumeration completeness** | Re-asked the server the *same* question as an independent aggregation (`$select=count(*)`), a different query shape from the row pull | ✅ 38,801 = 38,801, exact |
| 3 | **Paging correctness** | Confirmed no duplicate or lost `unique_key` across 8 pages | ✅ 0 duplicates, 0 gaps |
| 4 | **Result reproducibility** | Headline statistics were first computed in a **standalone exploratory script outside the notebook**, then recomputed by the notebook | ✅ every figure agrees (21.99 h / 23.30 h / +0.62 / −1.11 / 13 / 4,374 / 14,517 / 2,270) |
| 5 | **Document claims vs. artifacts** | Every figure in `DATA_CARD.md` re-derived from `results/tables/*.csv` and the extract | ✅ 3 errors found and corrected (raw size 22.6→**36.32 MB**; 15→**23** descriptors; 6→**7** constant columns); a 4th table rebuilt from Closed-only counts |
| 6 | **Significance robustness** | Bootstrap CIs (4,000 draws, seed 20240101) computed per definition; both Queens/Manhattan contrasts exclude zero | ✅ flip is real, not noise |
| 7 | **Counter-mechanism check** | Closure-mix shares computed independently and compared against the observed rank flip | ✅ 5.02 pp excess duplicate-closure share in Queens ≈ 1.17 h of the 1.73 h swing |
| 8 | **Sensitivity** | S1–S5b (impossible durations, back-filled tail, `Unspecified` borough, zero-hour exclusion, censoring) | ✅ ranking flip is robust to all five; censoring flagged as an unresolved limit |
| 9 | **Notebook hygiene** | All 43 cells executed top-to-bottom; asserted 0 error outputs and monotonic execution order 1→19 | ✅ verified programmatically, not by eye |
| 10 | **PDF integrity** | `pdfinfo` / `pdftotext` on the exported report | ✅ 51 pages, 18 embedded images, 7 fonts, text layer extractable including the SHA-256 |
| 11 | **Clean-room reproduction** | Cloned the tagged repo to two separate fresh directories, built a virtualenv from `requirements.txt` alone, re-executed the notebook, and compared every artifact against the committed ones | ✅ `results/metrics.json` byte-identical; all 14 table CSVs byte-identical; **all 4 figures byte-identical**; 0 error outputs; execution order 1→19; `src/build_notebook.py` regenerates the notebook **source** byte-identically (58,395 bytes) in both repos |
| 12 | **Re-execution stability** | Re-ran the notebook three times in the working copy and diffed against the committed outputs | ✅ `metrics.json`, all tables and all figures unchanged |

### 4.0 A verification check that was itself wrong

The clean-room notebook-source comparison (§11, last clause) **first reported a false
pass**. The comparison helper mishandled nbformat's list-of-lines `source` field, both
sides raised `TypeError`, and `diff` compared two empty outputs — exiting zero and
printing "IDENTICAL". A green check that never compared anything is worse than no check.

It was re-run with a corrected helper that normalises `source` to text, and only then
confirmed the genuine 58,395-byte match. Recorded here because the failure mode —
*verification that silently verifies nothing* — is exactly the class of error this
assignment is about, and it happened here.

### 4.1 Honest limits of this verification

* Verification was performed by the **same agent that produced the analysis**, using
  **independent code paths and independent query shapes** (checks 2 and 4), but it is
  **not** independent of the AI. A genuinely third-party re-implementation has **not**
  been carried out.
* **No second person** has reviewed this work. "Human-in-the-loop" here means a human set
  the brief, chose the dataset, and reviewed the outputs — not that a second analyst
  reproduced the numbers.
* The PDF was verified **structurally** (`pdfinfo`, `pdftotext`, image-XObject count).
  Neither the author nor the agent can visually inspect page layout in this environment,
  so **minor typographic issues in the PDF are possible** and should be eyeballed once.
* Bootstrap intervals are percentile intervals on the median. They are appropriate here
  (the median is the estimand) but they assume records are exchangeable, which the
  repeat-reporting structure (§10.2) shows is **not** strictly true. The intervals are
  therefore mildly optimistic for clustered addresses.

---

## 5. Reproducibility of the AI-assisted process

The AI's contribution is not a hidden intermediate. Everything it wrote is committed:

* `src/fetch_data.py` — the only network-touching code; frozen query is visible in source.
* `src/build_notebook.py` — generates the notebook, so cell sources are reviewable as
  ordinary Python rather than hand-edited JSON.
* `src/make_data_dictionary.py` — regenerates the dictionary from the data, so the
  documentation cannot silently diverge from the dataset.
* `src/make_report.sh` — the exact PDF pipeline.
* `results/` — every number, table, figure, and environment manifest.

Any reviewer can therefore inspect, modify, and re-run every step. No step depends on a
prompt, a hidden state, or an agent-only action.
