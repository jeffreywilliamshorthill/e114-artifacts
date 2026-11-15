#!/usr/bin/env bash
# Leg 2 — §4 main capture + base positive control (runs ON the box, detached).
# Per the frozen 4_capture_config_v1.md: base-bf16 GGUF, capture_residuals (L13/14/15/26),
# greedy --temp 0 --top-k 1 --seed 0, -n 256, raw continuations.
#  (a) 48 §4 prompts (44 targets + 4 worldview probes)  -> /workspace/cap_s4/
#  (b) 20 held-out register/control prompts (positive control, verbatim originals)
#      -> /workspace/cap_heldout_base/
# Then tars BOTH capture dirs (they are small — L13/14/15/26 only) for pull.
# Log: /workspace/leg2.log   Marker: LEG2_DONE_OK
set -uo pipefail
PW=/workspace/prework
BIN=/workspace/llama.cpp.new/build/bin
PY=/venv/main/bin/python
GGUF=/workspace/models/base-bf16.gguf
die(){ echo "LEG2_FAILED: $1"; exit 1; }

echo "=== build s4 prompt TSV ==="
$PY "$PW/build_s4_prompts.py" || die "prompt build"
wc -l "$PW/s4_prompts.tsv"

echo "=== (a) §4 capture: 48 prompts, -n 256 ==="
rm -rf /workspace/cap_s4
LD_LIBRARY_PATH="$BIN" "$BIN/llama-capture_residuals" \
  -m "$GGUF" --prompt-file "$PW/s4_prompts.tsv" -o /workspace/cap_s4 \
  -ngl 99 -c 2048 -n 256 --temp 0 --top-k 1 --seed 0 --no-stream \
  || die "s4 capture"
n_ok=$($PY -c "import json;m=json.load(open('/workspace/cap_s4/capture_manifest.json'));print(m['run_summary']['n_succeeded'])")
[ "$n_ok" = "48" ] || die "s4 capture: only $n_ok/48 succeeded"

echo "=== (b) positive control: 20 held-out prompts on base ==="
rm -rf /workspace/cap_heldout_base
LD_LIBRARY_PATH="$BIN" "$BIN/llama-capture_residuals" \
  -m "$GGUF" --prompt-file "$PW/heldout_prompts.tsv" -o /workspace/cap_heldout_base \
  -ngl 99 -c 2048 -n 256 --temp 0 --top-k 1 --seed 0 --no-stream \
  || die "heldout capture"
n_ok=$($PY -c "import json;m=json.load(open('/workspace/cap_heldout_base/capture_manifest.json'));print(m['run_summary']['n_succeeded'])")
[ "$n_ok" = "20" ] || die "heldout capture: only $n_ok/20 succeeded"

echo "=== tar for pull ==="
tar czf /workspace/leg2_captures.tgz -C /workspace cap_s4 cap_heldout_base
ls -la /workspace/leg2_captures.tgz
sha256sum /workspace/leg2_captures.tgz | tee /workspace/LEG2_TGZ_SHA.txt
echo "LEG2_DONE_OK"
