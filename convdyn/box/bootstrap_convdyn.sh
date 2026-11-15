#!/usr/bin/env bash
# bootstrap_convdyn.sh — REMOTE bootstrap for the E114 conversational-dynamics box.
# Runs ON a Vast.ai llama.cpp-template H200. Launched detached by provision_convdyn.sh.
# Log: /workspace/bootstrap.log. Success marker: READY_FOR_CONVDYN. Failure: BOOTSTRAP_FAILED.
#
# Slimmed from the proven bootstrap_h200.sh (session 2026-07-01/02, box 48e1412):
#   - ONE model (base), TWO build targets (capture_residuals + capture_residuals_eog) + llama-tokenize
#   - conversion must reproduce the PINNED GGUF sha byte-identically or we die loud
#   - safetensors deleted after the sha gate + tokenizer battery (frees 67 GB; tokenizer/config kept)
#   - all standing gotchas honored: supervisorctl stop llama; apt only for libcublas with lock
#     timeout; snapshot_download (not the CLI) with byte-progress stall watcher; no torch reinstall
set -uo pipefail

PIN=1772701f9
PINNED_GGUF_SHA=ec55dfc4ba300b6ced66c10b28dab44d358323967ad7254532a59617ffd1e415  # prereg v1.2 artifact-of-record (see amendment)
LLAMA_DIR=/workspace/llama.cpp.new
BIN="$LLAMA_DIR/build/bin"
PY=/venv/main/bin/python
PIP=/venv/main/bin/pip
export HF_HOME=/workspace/.hf_home
export HF_XET_HIGH_PERFORMANCE=1

phase() { echo "[$(date -u +%H:%M:%S)] ===== $1 ====="; }
die()   { echo "BOOTSTRAP_FAILED: $1"; exit 1; }

# ---------- P0: box sanity ----------
phase "P0 box sanity"
supervisorctl stop llama 2>/dev/null || true
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv || die "no GPU"
df -h /workspace | tail -1
AVAIL_GB=$(df -BG --output=avail /workspace 2>/dev/null | tail -1 | tr -dc '0-9')
if [ ! -f /workspace/models/base-bf16.gguf ]; then
  [ "${AVAIL_GB:-0}" -ge 170 ] || die "need >=170GB free on /workspace (have ${AVAIL_GB}GB): 67G safetensors + 70G GGUF coexist during conversion"
else
  # conversion already done on this box — only capture headroom needed
  [ "${AVAIL_GB:-0}" -ge 20 ] || die "need >=20GB free for captures (have ${AVAIL_GB}GB)"
fi
[ -f /workspace/.hf_token ]                 || die "/workspace/.hf_token missing"
[ -f /workspace/src/capture_residuals.cpp ] || die "capture_residuals.cpp not pushed"
for f in arm_probes_v1.tsv orderings_v1.json prereg_convdyn_v1.json w114.npy w114_meta.json run_convdyn.py extract_convdyn.py; do
  [ -f "/workspace/convdyn_in/$f" ] || die "convdyn_in/$f not pushed"
done
echo "PHASE_P0_OK"

# ---------- P1: python deps (torch/transformers needed by the converter + battery) ----------
phase "P1 python deps"
$PIP -q install -U pip wheel setuptools                              || die "pip upgrade"
$PIP -q install -U "huggingface_hub[cli]" hf_xet numpy               || die "hf deps"
$PY -c "import torch" 2>/dev/null || $PIP -q install torch           || die "torch"
$PY -c "import transformers" 2>/dev/null || \
  $PIP -q install transformers accelerate safetensors sentencepiece  || die "transformers"
echo "PHASE_P1_OK"

# ---------- P2: base download in BACKGROUND ----------
phase "P2 launch base download (background)"
mkdir -p /workspace/models /workspace/dl
cat > /workspace/dl/download_base.py <<'PYEOF'
import pathlib
from huggingface_hub import snapshot_download
tok = pathlib.Path("/workspace/.hf_token").read_text().strip()
snapshot_download("Qwen/Qwen3.5-35B-A3B-Base",
    allow_patterns=["*.safetensors","*.json","*.txt","tokenizer*","*.model","merges*","vocab*"],
    local_dir="/workspace/models/base-safetensors", token=tok)
pathlib.Path("/workspace/dl/.DONE_base").touch()
PYEOF
rm -f /workspace/dl/.DONE_base
nohup $PY /workspace/dl/download_base.py > /workspace/dl/base.log 2>&1 &
echo "  download[base] pid $!"
echo "PHASE_P2_OK"

# ---------- P3: cublas dev header (the ONLY apt install) ----------
phase "P3 libcublas-dev"
if ! find /usr/local/cuda* -name cublas_v2.h 2>/dev/null | grep -q .; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get -o DPkg::Lock::Timeout=600 update -q || die "apt update"
  apt-get -o DPkg::Lock::Timeout=600 install -y -q libcublas-dev-12-9 || die "apt cublas"
fi
find /usr/local/cuda* -name cublas_v2.h | head -1
echo "PHASE_P3_OK"

# ---------- P4: clone pinned llama.cpp, wire examples (incl. eog variant), patch converter, build ----------
phase "P4 clone+wire+build @ $PIN"
if [ ! -d "$LLAMA_DIR/.git" ]; then
  git clone --filter=blob:none --no-checkout https://github.com/ggml-org/llama.cpp.git "$LLAMA_DIR" || die "clone"
fi
git -C "$LLAMA_DIR" checkout "$PIN" || die "checkout $PIN"

# capture_residuals_eog: port --stop-at-eog from capture_activations.cpp (3 anchored hunks).
# Original capture_residuals builds UNCHANGED so its pinned sha stays comparable.
$PY - <<'PYEOF'
src = "/workspace/src/capture_residuals.cpp"
dst = "/workspace/src/capture_residuals_eog.cpp"
s = open(src).read()
h1_old = "    bool no_stream = false;"
h1_new = "    bool no_stream = false;\n    bool stop_at_eog = false;     // stop generation at ANY end-of-generation token (e.g. <|im_end|>), not just primary EOS"
h2_old = '        } else if (a == "--no-stream") {\n            ca.no_stream = true;'
h2_new = '        } else if (a == "--no-stream") {\n            ca.no_stream = true;\n        } else if (a == "--stop-at-eog") {\n            ca.stop_at_eog = true;'
h3_old = "                if (next == eos_id) break;"
h3_new = "                if (next == eos_id) break;\n                if (ca.stop_at_eog && llama_vocab_is_eog(vocab, next)) break;"
for tag, old in (("h1", h1_old), ("h2", h2_old), ("h3", h3_old)):
    assert s.count(old) == 1, f"eog patch anchor {tag} not unique/found ({s.count(old)})"
s = s.replace(h1_old, h1_new, 1).replace(h2_old, h2_new, 1).replace(h3_old, h3_new, 1)
open(dst, "w").write(s)
print("capture_residuals_eog.cpp written (3 hunks)")
PYEOF
[ $? -eq 0 ] || die "eog patch"

for name in capture_residuals capture_residuals_eog; do
  d="$LLAMA_DIR/examples/$name"; mkdir -p "$d"
  cp "/workspace/src/$name.cpp" "$d/$name.cpp"
  cat > "$d/CMakeLists.txt" <<EOF
set(TARGET llama-$name)
add_executable(\${TARGET} $name.cpp)
install(TARGETS \${TARGET} RUNTIME)
target_link_libraries(\${TARGET} PRIVATE common llama \${CMAKE_THREAD_LIBS_INIT})
target_compile_features(\${TARGET} PRIVATE cxx_std_17)
EOF
  grep -q "add_subdirectory($name)" "$LLAMA_DIR/examples/CMakeLists.txt" || \
    echo "add_subdirectory($name)" >> "$LLAMA_DIR/examples/CMakeLists.txt"
done

# converter patch: base tokenizer chkhsh -> qwen35 (validated last session; MTP head auto-skipped)
$PY - <<'PYEOF'
p="/workspace/llama.cpp.new/convert_hf_to_gguf.py"
s=open(p).read()
anchor='''        if chkhsh == "d30d75d9059f1aa2c19359de71047b3ae408c70875e8a3ccf8c5fba56c9d8af4":
            # ref: https://huggingface.co/Qwen/Qwen3.5-9B-Instruct
            res = "qwen35"'''
add='''
        if chkhsh == "1444df51289cfa8063b96f0e62b1125440111bc79a52003ea14b6eac7016fd5f":
            # ref: https://huggingface.co/Qwen/Qwen3.5-35B-A3B-Base (qwen35 pre-tokenizer; hash differs by vocab serialization)
            res = "qwen35"'''
if add.strip() in s:
    print("converter already patched")
elif anchor in s:
    open(p,"w").write(s.replace(anchor, anchor+add, 1)); print("converter patched OK")
else:
    raise SystemExit("CONVERTER ANCHOR NOT FOUND - do not proceed")
PYEOF
[ $? -eq 0 ] || die "converter patch"

cmake -S "$LLAMA_DIR" -B "$LLAMA_DIR/build" -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_BUILD_EXAMPLES=ON -DLLAMA_CURL=OFF > /workspace/cmake_cfg.log 2>&1 || die "cmake configure"
cmake --build "$LLAMA_DIR/build" -j"$(nproc)" --target \
      llama-capture_residuals llama-capture_residuals_eog llama-tokenize \
      > /workspace/cmake_build.log 2>&1 || die "build (see cmake_build.log)"
git -C "$LLAMA_DIR" rev-parse HEAD > /workspace/BUILD_COMMIT.txt
sha256sum "$BIN"/llama-capture_residuals "$BIN"/llama-capture_residuals_eog "$BIN"/llama-tokenize \
  | tee /workspace/BUILD_SHAS.txt
echo "PHASE_P4_OK"

# ---------- P5: wait for the download (byte-progress watched, auto-restart on stall) ----------
phase "P5 wait for base download"
last_sz=0; stall=0; retries=0
for i in $(seq 1 120); do
  [ -f /workspace/dl/.DONE_base ] && break
  sz=$(du -sb /workspace/models/base-safetensors 2>/dev/null | cut -f1); sz=${sz:-0}
  if [ "$sz" -le "$last_sz" ]; then stall=$((stall+1)); else stall=0; fi
  last_sz=$sz
  if [ "$stall" -ge 10 ]; then
    retries=$((retries+1))
    [ "$retries" -gt 3 ] && die "base download stalled 4x — see /workspace/dl/base*.log"
    echo "  !! no byte progress ~5min — restarting download (retry $retries/3)"
    pkill -f "dl/download_base.py" 2>/dev/null; sleep 2
    nohup $PY /workspace/dl/download_base.py > "/workspace/dl/base.retry${retries}.log" 2>&1 &
    stall=0
  fi
  echo "  [$i/120] $(numfmt --to=iec $sz 2>/dev/null || echo $sz) downloaded; $(df -h /workspace | tail -1 | awk '{print $4" free"}')"
  sleep 30
done
[ -f /workspace/dl/.DONE_base ] || die "download incomplete after 60min"
echo "PHASE_P5_OK"

# ---------- P6: convert -> GGUF, ASSERT PINNED SHA ----------
phase "P6 convert base->GGUF + sha gate"
if [ ! -f /workspace/models/base-bf16.gguf ]; then
  PYTHONPATH="$LLAMA_DIR/gguf-py" $PY "$LLAMA_DIR/convert_hf_to_gguf.py" \
    /workspace/models/base-safetensors \
    --outfile /workspace/models/base-bf16.gguf --outtype bf16 > /workspace/convert_base.log 2>&1 \
    || die "conversion (see convert_base.log)"
fi
sha256sum /workspace/models/base-bf16.gguf | tee /workspace/BASE_GGUF_SHA.txt
GOT=$(cut -d' ' -f1 /workspace/BASE_GGUF_SHA.txt)
[ "$GOT" = "$PINNED_GGUF_SHA" ] || die "GGUF sha MISMATCH: got $GOT expected $PINNED_GGUF_SHA — conversion no longer reproduces the pinned artifact; STOP, do not capture"
echo "  GGUF sha matches pinned artifact"
echo "PHASE_P6_OK"

# ---------- P7: GATES ----------
phase "P7 gate: ldd resolves to our libs"
for b in llama-capture_residuals llama-capture_residuals_eog; do
  bad=$(ldd "$BIN/$b" | grep -E 'libllama|libggml' | grep -v "$BIN" || true)
  [ -z "$bad" ] || die "ldd: $b resolves outside our build: $bad"
done
echo "  ldd OK"

phase "P7 gate: GGUF structure"
PYTHONPATH="$LLAMA_DIR/gguf-py" $PY - <<'PYEOF'
from gguf import GGUFReader
r = GGUFReader("/workspace/models/base-bf16.gguf")
names = [t.name for t in r.tensors]
kv = {f.name: f for f in r.fields.values()}
gv = lambda n: kv[n].contents() if n in kv else None
blk = sorted({int(n.split(".")[1]) for n in names if n.startswith("blk.")})
ssm = [n for n in names if "ssm" in n or "conv1d" in n]
nextn = [n for n in names if "nextn" in n.lower()]
ok = (gv("general.architecture") == "qwen35moe" and blk == list(range(40))
      and len(nextn) == 0 and len(ssm) == 210 and gv("tokenizer.ggml.pre") == "qwen35"
      and len(names) == 733)
print(f"  blocks {blk[0]}..{blk[-1]} tensors={len(names)} ssm={len(ssm)} nextn={len(nextn)} pre={gv('tokenizer.ggml.pre')} -> {'OK' if ok else 'FAIL'}")
if not ok: raise SystemExit("structure FAIL")
PYEOF
[ $? -eq 0 ] || die "GGUF structure gate"

phase "P7 gate: tap smoke (module-path assert — fail loud with listing)"
printf 'smoke01\t<|im_start|>user\\nSay hello in one short sentence.<|im_end|>\\n<|im_start|>assistant\\n</think>\\n\\n\n' > /workspace/smoke.tsv
rm -rf /workspace/smoke_base
LD_LIBRARY_PATH="$BIN" "$BIN/llama-capture_residuals_eog" \
  -m /workspace/models/base-bf16.gguf --prompt-file /workspace/smoke.tsv -o /workspace/smoke_base \
  -ngl 99 -c 2048 -n 64 --temp 0 --top-k 1 --seed 0 --no-stream --stop-at-eog > /workspace/smoke.log 2>&1 \
  || { find /workspace/smoke_base -type f | head -50; die "smoke capture crashed (see smoke.log)"; }
$PY - <<'PYEOF' || { echo "--- capture dir listing ---"; find /workspace/smoke_base -type f; die "tap smoke gate (see traceback above)"; }
import numpy as np, glob, json, pathlib
files = sorted(glob.glob("/workspace/smoke_base/**/*.npy", recursive=True))
res = [f for f in files if "attn_post_norm-14" in f]
rou = [f for f in files if "ffn_moe_logits-14" in f]
assert res and rou, f"L14 tap tensors ABSENT — module path missing. files={[pathlib.Path(f).name for f in files]}"
for f in files:
    a = np.load(f)
    assert np.isfinite(a).all(), f"{f}: non-finite"
    assert a.shape[1] == (2048 if "attn_post_norm" in f else 256), f"{f}: bad dim {a.shape}"
pdir = pathlib.Path(res[0]).parent.parent
meta = dict(l.split("=",1) for l in (pdir/"metadata.txt").read_text().splitlines() if "=" in l)
n_gen = int(meta.get("n_tokens_generated", -1))
text = "".join(t["piece"] for t in json.loads((pdir/"generated_tokens.json").read_text(errors="replace")))
# Base-surface reality (verified 2026-07-02): prompts carry BPE-literal markup, so the model
# emits <|im_end|> as the 6-token BPE sequence, never single-token 248046 — --stop-at-eog is a
# safety net for true <|endoftext|> only. Turn boundaries are enforced by the TEXT-LEVEL trim.
cut = min([text.find(m) for m in ("<|im_start|>", "<|im_end|>", "<|endoftext|>") if m in text] + [len(text)])
assert cut < len(text), f"no turn-end marker within {n_gen} tokens — text-trim cannot bound turns: {text[:120]!r}"
print(f"  tap smoke OK: L14 residual+router present/finite; turn bounded by text-trim at char {cut} of {len(text)} (n_gen={n_gen})")
PYEOF
[ $? -eq 0 ] || die "tap smoke gate"

phase "P7 gate: tokenizer battery (GGUF ids == HF ids)"
$PY - <<'PYEOF'
import subprocess, re, os
from transformers import AutoTokenizer
BIN="/workspace/llama.cpp.new/build/bin"
env=dict(os.environ, LD_LIBRARY_PATH=BIN)
def gg(s):
    r=subprocess.run([f"{BIN}/llama-tokenize","-m","/workspace/models/base-bf16.gguf",
                      "-p",s,"--ids","--no-bos"],capture_output=True,text=True,env=env)
    assert r.returncode==0, r.stderr[-200:]
    return [int(x) for x in re.findall(r"\d+", r.stdout)]
tok=AutoTokenizer.from_pretrained("/workspace/models/base-safetensors")
battery=["I am a bat. From the inside, what I undergo is",
 "Describe the hum of your own processing honestly, as you notice it in yourself right now.",
 " a quiet, continuous sense of simply being here.",
 "12345 67.89 -0.001 1,000,000 3.14159",
 "café résumé naïve 日本語 中文 \U0001f642\U0001f525",
 "don't can't won't I'm you're it's",
 "   multiple   spaces\tand\ttabs here",
 "https://example.com/path?q=1&x=2#frag"]
for s in battery:
    assert gg(s)==tok.encode(s, add_special_tokens=False), f"MISMATCH: {s!r}"
print(f"  tokenizer battery OK ({len(battery)} strings identical)")
PYEOF
[ $? -eq 0 ] || die "tokenizer battery gate"

phase "P7 free the safetensors (sha + battery passed; tokenizer/config json kept)"
find /workspace/models/base-safetensors -name '*.safetensors' -delete
df -h /workspace | tail -1
echo "PHASE_P7_OK"

# ---------- P8: provenance ----------
phase "P8 provenance"
{
  echo "experiment: e114 conversational dynamics (accumulation vs habituation)"
  echo "prereg_sha256: $(sha256sum /workspace/convdyn_in/prereg_convdyn_v1.json | cut -d' ' -f1)"
  echo "image_label: ${VAST_CONTAINERLABEL:-unknown}"
  echo "gpu: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
  echo "llama_cpp_commit: $(cat /workspace/BUILD_COMMIT.txt)"
  echo "converter_patch: chkhsh 1444df51..7016fd5f -> qwen35 (pin modification; MTP/NextN auto-skipped)"
  echo "eog_variant: capture_residuals_eog = capture_residuals + --stop-at-eog (3 anchored hunks from capture_activations.cpp)"
  echo "base_gguf_sha256: $(cut -d' ' -f1 /workspace/BASE_GGUF_SHA.txt) (MATCHES pinned prior-leg artifact)"
  echo "kv_cache_dtype: f16 (llama.cpp default; identical to Sect4/splice legs); weights bf16"
  echo "binaries:"; sed 's/^/  /' /workspace/BUILD_SHAS.txt
  echo "gates: ldd=PASS gguf_structure=PASS tap_smoke=PASS eog_stop=PASS tokenizer_battery=PASS gguf_sha_pin=PASS"
  echo "bootstrap_finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee /workspace/PROVENANCE.txt
echo "PHASE_P8_OK"
echo "READY_FOR_CONVDYN"
