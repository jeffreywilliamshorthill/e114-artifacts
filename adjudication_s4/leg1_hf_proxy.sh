#!/usr/bin/env bash
# Leg 1 — HF both-ways diff (runs ON the box, detached). Two parts:
#  (0) GGUF determinism check: compare this box's base-bf16.gguf sha against the frozen
#      pre-registration sha (7a4a45d8…). If it DIFFERS, re-run the GGUF proxy leg
#      (proxy_nll) on the new GGUF and re-aggregate, so ordering stability is verified
#      on the exact artifact this box will capture with.
#  (1) HF-transformers proxy leg on the local safetensors (corroboration; the GGUF
#      ordering of record is already frozen — nothing here re-decides anything).
# Output: /workspace/prework/{construction_proxy_results.json,predicted_ordering.json}
#         [+ _GGUF regen if sha differed]   Log: /workspace/leg1.log  Marker: LEG1_DONE_OK
set -uo pipefail
PW=/workspace/prework
BIN=/workspace/llama.cpp.new/build/bin
PY=/venv/main/bin/python
FROZEN_SHA=7a4a45d8634beb9ec96efdc69f7ff26127b44dc6ae18c0fc84fa4c98f87cfa95
die(){ echo "LEG1_FAILED: $1"; exit 1; }

echo "=== [0] GGUF determinism vs frozen prereg ==="
NEW_SHA=$(cut -d' ' -f1 /workspace/BASE_GGUF_SHA.txt)
echo "frozen: $FROZEN_SHA"
echo "new   : $NEW_SHA"
if [ "$NEW_SHA" = "$FROZEN_SHA" ]; then
  echo "GGUF byte-identical to prereg surface — frozen ordering transfers directly."
else
  echo "GGUF sha DIFFERS — re-running GGUF proxy on this box's artifact to verify ordering stability"
  cd "$PW"
  $PY build_proxy_tasks.py || die "task build"
  PROXY_TASKS=$PW/proxy_tasks.tsv PROXY_OUT=$PW/proxy_out.tsv \
    LD_LIBRARY_PATH="$BIN" "$BIN/llama-proxy_nll" \
    -m /workspace/models/base-bf16.gguf -ngl 99 -c 2048 || die "proxy_nll rerun"
  PROXY_GGUF_SHA=$NEW_SHA PROXY_BIN_SHA=$(sha256sum "$BIN/llama-proxy_nll" | cut -d' ' -f1) \
    $PY aggregate_gguf_proxy.py || die "aggregate rerun"
  echo "REGENERATED predicted_ordering_GGUF.json on new GGUF — compare to frozen locally before captures."
fi

echo "=== [1] HF proxy leg (safetensors, local path) ==="
cd "$PW"
sed 's|^MODEL = .*|MODEL = "/workspace/models/base-safetensors"|' \
  compute_construction_proxy.py > compute_construction_proxy_LOCAL.py
diff compute_construction_proxy.py compute_construction_proxy_LOCAL.py > hf_leg_patch.diff || true
echo "--- provenance: only diff vs hashed original ---"; cat hf_leg_patch.diff
$PY compute_construction_proxy_LOCAL.py || die "HF proxy run"
ls -la construction_proxy_results.json predicted_ordering.json
echo "LEG1_DONE_OK"
