#!/usr/bin/env bash
# Render a board.json to PNG via whiteboard-cli.
#
# Usage:
#   scripts/render_preview.sh <board.json> <preview.png> [--scale N]
#
# Idempotent: overwrites the output file.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <board.json> <preview.png> [--scale N]" >&2
  exit 2
fi

INPUT="$1"
OUTPUT="$2"
shift 2

SCALE=2
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scale) SCALE="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

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

mkdir -p "$(dirname "$OUTPUT")"
"${WB_CLI[@]}" -i "$INPUT" -o "$OUTPUT" -s "$SCALE"
echo "rendered: $OUTPUT"
