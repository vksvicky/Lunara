#!/bin/bash
# Compile Lunara with build stats and write test_output/memory_report.html.
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
SDK_DIR="$HOME/Library/Application Support/Garmin/ConnectIQ/Sdks"
SDK_PATH="$(ls -td "$SDK_DIR"/connectiq-sdk-mac-* 2>/dev/null | head -n 1)"
KEY_PATH="$ROOT/developer_key.der"

if [ -z "${SDK_PATH}" ] || [ ! -f "$KEY_PATH" ]; then
    echo "SDK or developer_key.der is missing."
    exit 1
fi

DEVICES=(
    "fenix7s:117162"
    "fenix7:117162"
    "fr255:117162"
    "enduro3:117162"
    "venu2s:117162"
    "epix2pro42mm:117162"
    "venu2:117162"
    "venu3:131072"
    "fenix847mm:131072"
    "fenix9pro51mm:131072"
)

mkdir -p "$ROOT/bin" "$ROOT/test_output"
REPORT="$ROOT/test_output/memory_report.html"
ROWS=""
FAILURES=0

echo "========================================================"
echo "LUNARA MEMORY PROFILE"
echo "========================================================"

for ENTRY in "${DEVICES[@]}"; do
    DEV="${ENTRY%%:*}"
    LIMIT="${ENTRY##*:}"
    echo "Profiling $DEV (limit $((LIMIT / 1024)) KB)"
    STATS=$("$SDK_PATH/bin/monkeyc" -f "$ROOT/monkey.jungle" -o "$ROOT/bin/profile_$DEV.prg" -y "$KEY_PATH" -d "$DEV" --build-stats 0 2>&1) || true
    DATA_BYTES=$(echo "$STATS" | awk '/Data:/ {in_data=1} in_data && /Foreground:/ {print $2; in_data=0}')
    CODE_BYTES=$(echo "$STATS" | awk '/Code:/ {in_code=1} in_code && /Foreground:/ {print $2; in_code=0}')
    PRG_BYTES=$(echo "$STATS" | awk '/Total PRG Size:/ {print $4}')
    if [ -z "$DATA_BYTES" ] || [ -z "$CODE_BYTES" ]; then
        echo "Could not read memory stats for $DEV"
        FAILURES=$((FAILURES + 1))
        ROWS="${ROWS}<tr><td>${DEV}</td><td colspan='5' class='fail'>stats unavailable</td></tr>"
        continue
    fi
    TOTAL=$((DATA_BYTES + CODE_BYTES))
    PERCENT=$(awk "BEGIN {printf \"%.1f\", ($TOTAL / $LIMIT) * 100}")
    STATUS="PASS"
    CLASS="pass"
    if [ "$TOTAL" -gt "$LIMIT" ]; then
        STATUS="OVER LIMIT"
        CLASS="fail"
        FAILURES=$((FAILURES + 1))
    elif [ "$TOTAL" -gt $((LIMIT - 10240)) ]; then
        STATUS="CLOSE"
        CLASS="warn"
    fi
    echo "  data $DATA_BYTES  code $CODE_BYTES  total $TOTAL ($PERCENT%)  prg ${PRG_BYTES:-?}  $STATUS"
    ROWS="${ROWS}<tr><td>${DEV}</td><td>${DATA_BYTES}</td><td>${CODE_BYTES}</td><td>${TOTAL} (${PERCENT}%)</td><td>${PRG_BYTES:-?}</td><td class='${CLASS}'>${STATUS}</td></tr>"
done

rm -f "$ROOT"/bin/profile_*.prg

cat > "$REPORT" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Lunara Memory Report</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#0f172a; color:#f1f5f9; margin:0; padding:24px; }
    h1 { color:#38bdf8; text-align:center; }
    table { width:100%; border-collapse:collapse; margin-top:24px; }
    th, td { text-align:left; padding:10px 12px; border-top:1px solid #334155; }
    th { color:#7dd3fc; }
    .pass { color:#4ade80; font-weight:700; }
    .warn { color:#fbbf24; font-weight:700; }
    .fail { color:#f87171; font-weight:700; }
  </style>
</head>
<body>
  <h1>Lunara Memory Report</h1>
  <p>Foreground is data plus code, checked against the watch-face limit. PRG is the packaged file, which also holds the dial and moon bitmaps.</p>
  <table>
    <thead><tr><th>Device</th><th>Data</th><th>Code</th><th>Foreground</th><th>PRG</th><th>Status</th></tr></thead>
    <tbody>
    ${ROWS}
    </tbody>
  </table>
</body>
</html>
EOF

echo "Report → $REPORT"
exit "$FAILURES"
