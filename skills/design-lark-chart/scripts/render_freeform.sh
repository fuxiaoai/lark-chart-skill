#!/usr/bin/env bash
# render_freeform.sh — End-to-end gate for freeform-drawing sessions.
#
# Enforces the freeform pipeline so a single missing step can no longer slip into Feishu.
# Required session layout under <session-dir>:
#   freeform_brief.json   # design intent & contract
#   plan.json             # planning artifact (style_budget can override lint palette)
#   diagram.svg           # the only design source; this is what we ship
#
# Pipeline (any failing step aborts the run):
#   1) brief schema check                   (script-internal jq-free python validator)
#   2) whiteboard-cli -f svg --check        (Gate A.1: SVG -> board check)
#   3) lint_svg_quality.py --plan/--seed    (Gate A.2: palette + role + tag budget)
#   4) whiteboard-cli -f svg --to openapi   (produces board.openapi.json)
#
# Usage:
#   scripts/render_freeform.sh <session-dir> [--strict-budget]
#
# Outputs (next to the SVG):
#   board.openapi.json        # final OpenAPI nodes, ready for lark-cli whiteboard +update
#   render_freeform.report.json # consolidated gate report
#
# Exit codes:
#   0  all gates pass
#   1  a gate failed (see render_freeform.report.json)
#   2  invocation / IO error
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <session-dir> [--strict-budget]" >&2
  exit 2
fi

SESSION="$1"
shift || true
STRICT_BUDGET=0
for arg in "$@"; do
  case "$arg" in
    --strict-budget) STRICT_BUDGET=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ ! -d "$SESSION" ]]; then
  echo "error: session dir not found: $SESSION" >&2
  exit 2
fi

BRIEF="$SESSION/freeform_brief.json"
PLAN="$SESSION/plan.json"
SVG="$SESSION/diagram.svg"
OPENAPI="$SESSION/board.openapi.json"
REPORT="$SESSION/render_freeform.report.json"

for f in "$BRIEF" "$PLAN" "$SVG"; do
if [[ ! -f "$f" ]]; then
    echo "error: required artifact missing: $f" >&2
    exit 2
  fi
done

if [[ -n "${WHITEBOARD_CLI:-}" ]]; then
  read -r -a WB_CLI <<< "$WHITEBOARD_CLI"
elif command -v whiteboard-cli >/dev/null 2>&1; then
  WB_CLI=(whiteboard-cli)
else
  WB_CLI=(npx -y @larksuite/whiteboard-cli@^0.2.10)
fi

HERE_DIR="$(cd "$(dirname "$0")" && pwd)"
LINT_PY="$HERE_DIR/lint_svg_quality.py"

# --- Step 1: brief schema validation ---
BRIEF_PATH="$BRIEF" PLAN_PATH="$PLAN" python3 - <<'PY'
import json, os, sys

brief_path = os.environ["BRIEF_PATH"]
plan_path = os.environ["PLAN_PATH"]

REQUIRED_BRIEF = ["chart_type", "freeform_mode", "intent", "visual_anchor", "deliverables"]
ALLOWED_MODES = {"sankey", "roadmap", "prototype", "illustration", "custom"}

with open(brief_path, "r", encoding="utf-8") as f:
    brief = json.load(f)

missing = [k for k in REQUIRED_BRIEF if k not in brief]
if missing:
    print(json.dumps({"step": "brief_schema", "ok": False, "missing": missing}, ensure_ascii=False))
    sys.exit(1)

if brief.get("chart_type") != "freeform-drawing":
    print(json.dumps({"step": "brief_schema", "ok": False,
                      "reason": f"chart_type must be 'freeform-drawing', got {brief.get('chart_type')!r}"},
                     ensure_ascii=False))
    sys.exit(1)

mode = brief.get("freeform_mode")
if mode not in ALLOWED_MODES:
    print(json.dumps({"step": "brief_schema", "ok": False,
                      "reason": f"freeform_mode must be one of {sorted(ALLOWED_MODES)}, got {mode!r}"},
                     ensure_ascii=False))
    sys.exit(1)

with open(plan_path, "r", encoding="utf-8") as f:
    plan = json.load(f)

if "style_budget" not in plan:
    print(json.dumps({"step": "brief_schema", "ok": False,
                      "reason": "plan.json must contain 'style_budget' (list of hex or palette dict)"},
                     ensure_ascii=False))
    sys.exit(1)

print(json.dumps({"step": "brief_schema", "ok": True, "freeform_mode": mode}, ensure_ascii=False))
PY

MODE="$(python3 -c "import json,sys; print(json.load(open('$BRIEF'))['freeform_mode'])")"
SEED="$(python3 -c "import json; b=json.load(open('$BRIEF')); print(b.get('style_seed') or '')")"

# --- Step 2: whiteboard-cli --check ---
CHECK_RAW="$("${WB_CLI[@]}" -f svg -i "$SVG" --check)" || {
  echo "$CHECK_RAW"
  echo "error: whiteboard-cli --check failed to run" >&2
  exit 2
}

CHECK_OK="$(BRIEF_PATH="$BRIEF" REPORT_JSON="$CHECK_RAW" python3 - <<'PY'
import json, os, sys
raw = os.environ.get("REPORT_JSON", "")
brief_path = os.environ["BRIEF_PATH"]
try:
    obj = json.loads(raw)
except Exception as e:
    print(json.dumps({"ok": False, "reason": f"non-json: {e}"}))
    sys.exit(0)
try:
    brief = json.load(open(brief_path, encoding="utf-8"))
except Exception:
    brief = {}
allow = set(brief.get("allowed_check_warnings") or [])
check = ((obj.get("data") or {}).get("check") or {})
errors = int(check.get("errors") or 0)
warnings = int(check.get("warnings") or 0)
issues = check.get("issues") or []

disallowed = [i for i in issues if not (i.get("severity") == "warn" and i.get("type") in allow)]
ok = (errors == 0 and not disallowed)
print(json.dumps({
    "ok": ok,
    "errors": errors,
    "warnings": warnings,
    "issues_count": len(issues),
    "allowed_warning_types": sorted(allow),
    "disallowed_issue_count": len(disallowed),
    "disallowed_sample": disallowed[:3],
}))
PY
)"

# --- Step 3: lint_svg_quality.py ---
LINT_ARGS=(--mode "$MODE" --plan "$PLAN")
if [[ -n "$SEED" ]]; then
  LINT_ARGS+=(--style-seed "$SEED")
fi
if [[ "$STRICT_BUDGET" == "1" ]]; then
  LINT_ARGS+=(--strict-budget)
fi

set +e
LINT_RAW="$(python3 "$LINT_PY" "$SVG" "${LINT_ARGS[@]}")"
LINT_EXIT=$?
set -e

LINT_OK="$([[ "$LINT_EXIT" == "0" ]] && echo true || echo false)"

# --- Step 4: convert to OpenAPI ---
set +e
CONVERT_RAW="$("${WB_CLI[@]}" -f svg -i "$SVG" --to openapi -o "$OPENAPI" 2>&1)"
CONVERT_EXIT=$?
set -e

CONVERT_OK="$([[ "$CONVERT_EXIT" == "0" && -f "$OPENAPI" ]] && echo true || echo false)"

# --- Aggregate report ---
ALL_OK=true
if [[ "$(echo "$CHECK_OK" | python3 -c "import json,sys;print(json.load(sys.stdin)['ok'])")" != "True" ]]; then ALL_OK=false; fi
if [[ "$LINT_OK" != "true" ]]; then ALL_OK=false; fi
if [[ "$CONVERT_OK" != "true" ]]; then ALL_OK=false; fi

CHECK_RAW="$CHECK_RAW" CHECK_OK="$CHECK_OK" LINT_RAW="$LINT_RAW" LINT_OK="$LINT_OK" \
CONVERT_RAW="$CONVERT_RAW" CONVERT_OK="$CONVERT_OK" ALL_OK="$ALL_OK" \
SESSION="$SESSION" SVG="$SVG" OPENAPI="$OPENAPI" \
python3 - > "$REPORT" <<'PY'
import json, os
def loads(x):
    try: return json.loads(x)
    except Exception: return {"raw": x}

report = {
    "ok": os.environ["ALL_OK"] == "true",
    "session": os.environ["SESSION"],
    "svg": os.environ["SVG"],
    "openapi": os.environ["OPENAPI"] if os.environ["CONVERT_OK"] == "true" else None,
    "gates": {
        "whiteboard_check": {"ok": loads(os.environ["CHECK_OK"]).get("ok", False),
                              "summary": loads(os.environ["CHECK_OK"]),
                              "raw": loads(os.environ["CHECK_RAW"])},
        "svg_lint": {"ok": os.environ["LINT_OK"] == "true",
                     "report": loads(os.environ["LINT_RAW"])},
        "openapi_convert": {"ok": os.environ["CONVERT_OK"] == "true",
                             "stdout_tail": os.environ["CONVERT_RAW"][-2000:]},
    },
}
print(json.dumps(report, ensure_ascii=False, indent=2))
PY

if [[ "$ALL_OK" == "true" ]]; then
  echo "render_freeform: PASS  -> $REPORT"
  exit 0
else
  echo "render_freeform: FAIL  -> $REPORT" >&2
  exit 1
fi
