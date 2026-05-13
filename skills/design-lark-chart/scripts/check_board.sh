#!/usr/bin/env bash
# Run `whiteboard-cli --check` against a board.json and print structured issues.
#
# Usage:
#   scripts/check_board.sh <path/to/board.json>
#
# Exit codes:
#   0  check passed, no issues
#   1  check found issues (stdout has the report)
#   2  invocation / runtime error
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <board.json>" >&2
  exit 2
fi

INPUT="$1"
if [[ ! -f "$INPUT" ]]; then
  echo "error: $INPUT not found" >&2
  exit 2
fi

if [[ -n "${WHITEBOARD_CLI:-}" ]]; then
  read -r -a WB_CLI <<< "$WHITEBOARD_CLI"
elif command -v whiteboard-cli >/dev/null 2>&1; then
  WB_CLI=(whiteboard-cli)
else
  WB_CLI=(npx -y @larksuite/whiteboard-cli@^0.2.10)
fi

REPORT="$("${WB_CLI[@]}" -i "$INPUT" --check)" || {
  # If whiteboard-cli fails to run, treat as invocation/runtime error.
  echo "$REPORT"
  exit 2
}

echo "$REPORT"

# Gate A in this repo is strict: errors=0 AND warnings=0 AND issues=[].
REPORT_JSON="$REPORT" python3 - "$INPUT" <<'PY'
import json, os, sys

path = sys.argv[1]
raw = os.environ.get("REPORT_JSON", "")
try:
    obj = json.loads(raw)
except Exception as e:
    print(f"error: failed to parse whiteboard-cli output as JSON for {path}: {e}", file=sys.stderr)
    sys.exit(2)

check = ((obj.get("data") or {}).get("check") or {})
errors = int(check.get("errors") or 0)
warnings = int(check.get("warnings") or 0)
issues = check.get("issues") or []

if errors == 0 and warnings == 0 and issues == []:
    sys.exit(0)
sys.exit(1)
PY
