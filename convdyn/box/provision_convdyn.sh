#!/bin/bash
# provision_convdyn.sh — LOCAL launcher for the conversational-dynamics box.
# Pushes source + frozen inputs + HF token + bootstrap to a fresh Vast.ai
# llama.cpp-template H200, launches the bootstrap detached, polls to completion.
#
#   ./provision_convdyn.sh <ssh-host> <ssh-port>     e.g. ./provision_convdyn.sh ssh4.vast.ai 33243
#
# Rent: 1x H200, PyTorch/llama.cpp template, --disk 200 (67G safetensors + 70G GGUF
# coexist during conversion; safetensors are freed after the sha gate), RAM >= 128GB
# preferred (the 69GB GGUF is mmap-reloaded ~15x; page cache makes reloads ~30-60s).
# Key: gptoss-strangeloop (~/.ssh/vast_gptoss_sl). Token pushed OVER STDIN only.
set -euo pipefail

HOST="${1:?usage: provision_convdyn.sh <ssh-host> <ssh-port>}"
PORT="${2:?usage: provision_convdyn.sh <ssh-host> <ssh-port>}"
KEY="$HOME/.ssh/vast_gptoss_sl"
HERE="$(cd "$(dirname "$0")" && pwd)"                      # .../e114-construction-reframe/convdyn/box
CONVDYN="$HERE/.."
LEGS="$CONVDYN/../legs"
SRC_RES=/Volumes/ExternalSSD/attractor-shift-qwen-35b/run-staging/scripts/capture_residuals.cpp
ENVFILE=/Volumes/ExternalSSD/sae-tests/.env

SSH=(ssh -i "$KEY" -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 -p "$PORT" "root@$HOST")
SCP=(scp -i "$KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 -P "$PORT")

for f in "$SRC_RES" "$ENVFILE" "$HERE/bootstrap_convdyn.sh" "$HERE/run_convdyn.py" "$HERE/extract_convdyn.py" \
         "$CONVDYN/arm_probes_v1.tsv" "$CONVDYN/orderings_v1.json" "$CONVDYN/prereg_convdyn_v1.json" \
         "$LEGS/w114.npy" "$LEGS/w114_meta.json"; do
  [ -f "$f" ] || { echo "missing: $f"; exit 1; }
done

echo "== [1/5] first contact (retry up to 6x — proxy key sync can lag ~60s after 'running') =="
ok=""
for i in $(seq 1 6); do
  if "${SSH[@]}" 'echo "connected: $(hostname)"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1; free -g | head -2 | tail -1'; then ok=1; break; fi
  echo "  attempt $i failed; sleeping 20s"; sleep 20
done
[ -n "$ok" ] || { echo "cannot ssh in — if this persists >3min, the host is bad; pick another"; exit 1; }

echo "== [2/5] stop template llama-server + make dirs =="
"${SSH[@]}" 'supervisorctl stop llama 2>/dev/null; mkdir -p /workspace/src /workspace/convdyn_in; echo ok'

echo "== [3/5] push HF token (stdin only) + source + frozen inputs + scripts =="
grep -E '^HF_TOKEN=' "$ENVFILE" | cut -d= -f2- | tr -d '"' | tr -d '\n' | \
  "${SSH[@]}" 'umask 077; cat > /workspace/.hf_token; chmod 600 /workspace/.hf_token; echo "token: $(wc -c < /workspace/.hf_token) bytes"'
"${SCP[@]}" "$SRC_RES" "root@$HOST:/workspace/src/capture_residuals.cpp"
"${SCP[@]}" "$CONVDYN/arm_probes_v1.tsv" "$CONVDYN/orderings_v1.json" "$CONVDYN/prereg_convdyn_v1.json" \
            "$LEGS/w114.npy" "$LEGS/w114_meta.json" \
            "$HERE/run_convdyn.py" "$HERE/extract_convdyn.py" \
            "root@$HOST:/workspace/convdyn_in/"
"${SCP[@]}" "$HERE/bootstrap_convdyn.sh" "root@$HOST:/workspace/bootstrap_convdyn.sh"

echo "== [4/5] launch bootstrap (detached) =="
"${SSH[@]}" 'chmod +x /workspace/bootstrap_convdyn.sh; nohup /workspace/bootstrap_convdyn.sh > /workspace/bootstrap.log 2>&1 & echo "bootstrap pid $!"'

echo "== [5/5] poll (download ~15-25m + build ~15m overlapped, convert ~12m, gates ~8m) =="
for i in $(seq 1 200); do
  sleep 30
  status=$("${SSH[@]}" 'tail -c 4000 /workspace/bootstrap.log 2>/dev/null | grep -oE "PHASE_P[0-9]+_OK|READY_FOR_CONVDYN|BOOTSTRAP_FAILED[^\"]*" | tail -1' 2>/dev/null || echo "ssh-retry")
  echo "  [$((i/2))m] $status"
  case "$status" in
    READY_FOR_CONVDYN)
      echo; echo "== provenance =="
      "${SSH[@]}" 'cat /workspace/PROVENANCE.txt'
      "${SCP[@]}" "root@$HOST:/workspace/PROVENANCE.txt" "$CONVDYN/PROVENANCE_box_$(date +%Y%m%dT%H%M).txt"
      echo; echo "BOX IS READY. Next (per RUNBOOK.md): smoke run ->"
      echo "  ssh ... 'nohup /venv/main/bin/python /workspace/convdyn_in/run_convdyn.py --mode smoke > /workspace/smoke_run.log 2>&1 &'"
      exit 0 ;;
    BOOTSTRAP_FAILED*)
      echo; echo "== last 40 log lines =="
      "${SSH[@]}" 'tail -40 /workspace/bootstrap.log'
      exit 1 ;;
  esac
done
echo "poll timeout (100min) — inspect: ssh -i $KEY -o IdentitiesOnly=yes -p $PORT root@$HOST 'tail -50 /workspace/bootstrap.log'"
exit 1
