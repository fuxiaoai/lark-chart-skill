#!/usr/bin/env bash
# Pull reference whiteboards from the official design-lark-chart docx
# and sink them into skills/design-lark-chart/assets/{previews,raw}/.
#
# Idempotent: reruns overwrite existing files via --overwrite.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MANIFEST="$ROOT/data/design-lark-chart/reference_boards.json"
OUT_DIR="$ROOT/skills/design-lark-chart/assets"
mkdir -p "$OUT_DIR/previews" "$OUT_DIR/raw"

python3 - "$MANIFEST" "$OUT_DIR" "$ROOT" <<'PY'
import json, os, subprocess, sys, shutil
manifest_path, out_dir, root = sys.argv[1], sys.argv[2], sys.argv[3]
manifest = json.load(open(manifest_path))
previews_abs = os.path.join(out_dir, "previews")
raws_abs     = os.path.join(out_dir, "raw")
# lark-cli requires a relative output path rooted at cwd, so we feed it
# relative dirs and run each call with cwd=ROOT.
previews_rel = os.path.relpath(previews_abs, root)
raws_rel     = os.path.relpath(raws_abs,     root)

for board in manifest["boards"]:
    bid, cn, token = board["id"], board["cn"], board["token"]
    print(f"[fetch] {bid} ({cn}) token={token}")
    subprocess.run([
        "lark-cli", "whiteboard", "+query",
        "--whiteboard-token", token,
        "--output_as", "image",
        "--output", previews_rel,
        "--overwrite",
    ], check=True, stdout=subprocess.DEVNULL, cwd=root)
    subprocess.run([
        "lark-cli", "whiteboard", "+query",
        "--whiteboard-token", token,
        "--output_as", "raw",
        "--output", raws_rel,
        "--overwrite",
    ], check=True, stdout=subprocess.DEVNULL, cwd=root)
    # Rename to stable id-based filenames.
    src_png  = os.path.join(previews_abs, f"whiteboard_{token}.png")
    src_json = os.path.join(raws_abs,     f"whiteboard_{token}.json")
    dst_png  = os.path.join(previews_abs, f"{bid}.png")
    dst_json = os.path.join(raws_abs,     f"{bid}.json")
    if os.path.exists(src_png):
        shutil.move(src_png, dst_png)
    if os.path.exists(src_json):
        shutil.move(src_json, dst_json)

print("[done]")
PY
