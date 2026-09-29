# Submission - Result Summary

**Paste-ready plain text for the learn.spaiq.ai "result summary" field.**
Measured word count: **293** (target 150-300), counting the body only, excluding this header.

---

Question: Among NYC 311 pothole reports created in CY2024, what is the typical time from
report to closure, and does it differ by borough?

Data: A frozen, complete enumeration of 38,801 rows from NYC Open Data erm2-nwe9 (311
Service Requests), filtered to Street Condition -> Pothole, created in 2024. Complete
enumeration, so no sampling bias and no seed in data selection. The SHA-256 is verified on
every notebook run; it pins our extract, not the daily-refreshed upstream source.

Finding: The question is unanswerable until "closed" is defined. status='Closed' pools six
administrative acts; only 76.6% document a repair, while 11.7% are duplicate-collapses
with a median of 0.00 hours. Pooling them pulls the headline median from 23.30 h to 21.98 h,
by a different amount in each borough. The borough ranking therefore inverts: Queens is
fastest naively (+0.62 h, 95% CI +0.32 to +0.89), Manhattan fastest repair-only (-1.11 h,
CI -1.35 to -0.83). Both orderings are significant. The gap is closure-mix composition,
not repair speed.

Counterexample: locations reported five or more times take 3.50 h longer, so "median time
to fix a pothole" is really a median across reports, over-weighted toward chronic
locations.

Negative result: geocoding has no detectable effect on repair time (+0.02 h, CI -0.24 to
+0.28), contradicting the hypothesis I started from. It also rules out geocoding as an
alternative explanation for the borough differences.

Limits: reported potholes are not potholes; no causal claim; ten prohibited claims listed
explicitly.

Verification: two fresh clones, each built from pinned requirements, reproduced every
table, figure and statistic byte-identically. AI assistance is disclosed in
docs/AI_USE_LOG.md, including five defects I introduced and fixed - among them a silent
timestamp-parse failure and a unit error that mislabelled a threshold.

---

**Repository:** `<FILL-IN-GITHUB-URL>` &middot; **Commit/tag:** `v1.0.0`

The repository URL is submitted separately; it is not counted in the word total.
