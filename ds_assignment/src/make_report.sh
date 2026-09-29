#!/usr/bin/env bash
# Build the PDF report from the EXECUTED notebook.
#
# Pipeline: executed .ipynb -> static HTML (nbconvert) -> PDF (headless Chromium).
# This deliberately avoids a LaTeX toolchain, which is not installed and would
# add a large, fragile dependency for zero analytical value.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="$ROOT/.venv/bin/python"
NB="notebooks/311_pothole_analysis.ipynb"
HTML="reports/311_pothole_report.html"
PDF="reports/311_pothole_report.pdf"

BROWSER=""
for c in "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
         "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium"; do
  [ -x "$c" ] && BROWSER="$c" && break
done
if [ -z "$BROWSER" ]; then
  echo "ERROR: no Chromium-family browser found for PDF export." >&2
  exit 1
fi

echo "==> HTML from executed notebook"
"$PY" -m jupyter nbconvert --to html --template lab --output-dir reports \
      --output "311_pothole_report" "$NB"

# Page-break and print CSS so tables/figures do not split across pages.
cat > reports/report.css <<'CSS'
@page { size: A4; margin: 14mm 11mm; }
h1,h2,h3 { break-after: avoid; }
table { break-inside: auto; font-size: 8.4pt; }
tr { break-inside: avoid; }
img { max-width: 100%; break-inside: avoid; }
pre { white-space: pre-wrap; font-size: 7.6pt; break-inside: avoid; }
CSS

# nbconvert cannot take an extra stylesheet, so link it into the <head>.
"$PY" - "$HTML" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1]); h = p.read_text(encoding="utf-8")
if "report.css" not in h:
    h = h.replace("</head>", '<link rel="stylesheet" href="report.css">\n</head>', 1)
    p.write_text(h, encoding="utf-8")
    print("==> linked report.css into", p.name)
PY

echo "==> PDF via $BROWSER"
"$BROWSER" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --virtual-time-budget=20000 \
  --print-to-pdf="$ROOT/$PDF" "file://$ROOT/$HTML" 2>/dev/null || true

for _ in $(seq 1 30); do [ -s "$PDF" ] && break; sleep 1; done
[ -s "$PDF" ] || { echo "ERROR: PDF was not produced." >&2; exit 1; }

echo "==> done"
ls -l "$PDF"
"$PY" - <<'PY'
import re, pathlib
b = pathlib.Path("reports/311_pothole_report.pdf").read_bytes()
print(f"PDF pages: {len(re.findall(rb'/Type\s*/Page[^s]', b))}   bytes: {len(b):,}")
print("header:", b[:8])
PY
