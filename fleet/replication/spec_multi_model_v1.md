# Multi-model register-expert replication — spec v1 (FROZEN 2026-07-03, Jeffrey's approval: "test on both 3.5 and 3.6 35b, test 122b")

> **Freeze note:** the 3.5-35B comparison column comes from (a) the completed §6c all-layer
> FIRE/NOFIRE ranking (prework/6c_results/, run 2026-07-03 on the frozen spec) and (b) the W3
> fresh separability re-capture on box A2 — no separate 3.5 leg on box B. Predictions below
> unchanged from draft; scored as written. 
> **v1.0.1 pre-capture amendment (2026-07-03):** step 2's "routing-only" contradicts step 3,
> which recovers per-expert gate axes from (attn_post_norm-L, logits[:,e]) pairs and therefore
> REQUIRES residuals. Discovery captures include residuals (no --routing-only), exactly as the
> §6c sweep captures did. Disk cost at -n 256 × 20 prompts is ~2.5 GB (3.6) / ~4.5 GB (122B) —
> the disk-safe rationale for routing-only does not apply at this scale. No captures existed at
> amendment time. Repeat-probe riders (Jeffrey's add) DO use routing-only (raw-logit analyses).

**Date:** 2026-07-02 · **Motivation:** Dadfar's "more examples would be needed" (2026-07-02 email)
+ the program's own cross-model claim discipline. Upgrade "one expert in one model" to "a
recurring readout motif that different architectures place differently," at E114-grade rigor.

## The two targets (configs verified from HF 2026-07-02)

| | Qwen3.6-35B-A3B | Qwen3.5-122B-A10B |
|---|---|---|
| class | `Qwen3_5MoeForConditionalGeneration` (same!) | `Qwen3_5MoeForConditionalGeneration` |
| layers / hidden | **40 / 2048 — identical to 3.5-35B** | 48 / 3072 |
| experts | 256, 8 routed, shared present, expert dim 512 — **identical** | 256, 8 routed, shared present, expert dim 1024 |
| mixer layout | interval-4 (30 DeltaNet + 10 gated attn) — identical | interval-4 → 36 DeltaNet + 12 gated attn (3,7,…,47) |
| vocab | 248320 (same tokenizer family) | 248320 |
| what it tests | **index stability**: E114's slot literally exists; does the *function* stay at (L14,114) under continued/re-training? (HauhauCS finetune kept it; a successor generation may not) | **motif relocation**: different shape forces re-localization; April read says softmax-side **E48** — replicate at full rigor |
| release | 2026-04-17 open weights (agentic-coding successor) | released; official FP8 exists; community GGUFs exist |

**Verify-before-freeze items — RESOLVED 2026-07-02 (HF API, authed):**
(a) **Neither `Qwen/Qwen3.6-35B-A3B-Base` nor `Qwen/Qwen3.5-122B-A10B-Base` exists** (404 with
token — absent, not gated). BOTH legs therefore run the instruct models with the logged surface
caveat: bare-`</think>` no-think markup, interpreted against the HauhauCS-instruct precedent,
never pooled with 35B-Base numbers. P-null-surface is live for both.
(b) **122B Q8_0 community GGUFs verified**: `unsloth/Qwen3.5-122B-A10B-GGUF` Q8_0 = 129.9 GB
(4 shards), `bartowski/Qwen_Qwen3.5-122B-A10B-GGUF` = 132.6 GB, `lmstudio-community` = 129.9 GB.
No 700 GB self-convert staging needed: sha-pin one (prefer unsloth or bartowski), run full
structure gates (HauhauCS/AgentWorld precedent). Fits H200 141 GB VRAM with small ctx.
(c) **3.6-35B also has community Q8** (`unsloth/Qwen3.6-35B-A3B-GGUF`, 877k downloads) — leg can
skip the convert-with-chkhsh-patch step; same sha-pin + structure-gate discipline.
(d) llama.cpp pin `1772701f9` loads both (same arch class — expect yes; still gate it on box).

## Per-model pipeline (the E114 recipe, generalized — no index assumptions)

1. **Bank adaptation:** the verbatim 20-prompt heldout FIRE/NOFIRE bank, same chat markup surface;
   llama-tokenize integrity gate (|A−B| ≤ 8 tok per pair, counts logged — convdyn v1.4 rule).
2. **Discovery capture:** all-layer **routing-only** capture (`capture_residuals_all` variant;
   122B needs the 48-layer sed: blocks 0..47, EXPECTED_TENSORS 96/48u), greedy
   `--temp 0 --top-k 1 --seed 0`, `-n 256`, generated track trimmed at first literal marker,
   window tokens 1..128 (4_capture_config discipline).
3. **Rank all experts × layers** by Cohen's d on the **recovered per-expert gate axis** (w_e via
   least squares from (attn_post_norm-L, logits[:,e]) — NEVER realized W), FIRE vs NOFIRE,
   generated track. Emit the full ranked table.
4. **Row recovery + positive control** for the top candidates (rel residual gate < 1e-3):
   held-out d, direction, separation. Explicitly report (L14, E114)'s rank on each model —
   the index-transfer null is itself a deliverable.
5. **Report the side**: DeltaNet-block vs gated-attention-block layer placement of every
   top separator (the 122B April read = softmax-side E48; test it).

## Pre-registered predictions (draft — freeze with shas before any capture)

**Qwen3.6-35B-A3B:** P-index-stable (a top-5 separator at L14 is E114, d>2) ·
P-same-side-relocated (top separator DeltaNet-side mid-depth, index ≠114) ·
P-dissolved (no expert reaches d>2 — register distributed away) · P-null-surface
(instruct-only confound; scored only if no Base exists).
**Qwen3.5-122B-A10B:** P-E48-replicates (E48 among top softmax-side separators) ·
P-motif-softmax (top separator softmax-side mid-depth, any index) ·
P-deltanet-side (would contradict the April read — report loudly) · P-null.
**Cross-model motif claim** requires: ≥1 expert with d>2 on the recovered gate axis in ≥2 of
{3.5-35B, 3.6-35B, 122B}, each with positive-control separation — else the paper keeps the
single-model scope.

## Budget & sequencing

- **3.6-35B first** (cheaper, same tooling verbatim — identical shape means the existing
  capture_residuals_all binary, extraction, and analysis run unmodified): community Q8 GGUF
  (~37GB, sha-pinned + structure gates) → 20-prompt discovery capture → ~1.5–2 GPU-h.
- **122B second**: community Q8_0 ≈ 130GB (sources above) fits H200 VRAM (141GB) with
  small ctx; ~2–3 GPU-h.
- **Box plan updated 2026-07-02**: convdyn-T box = Vast 43650141 (1× H200 NVL, 500GB disk,
  $4.41/hr) — the 500GB disk fits BOTH replication legs on the same box after convdyn-T
  (no deletion juggling needed; 3.5 GGUF 70G + 3.6 Q8 37G + 122B Q8 130G + captures < 300G).
- Judges/ratings NOT needed (bank labels are pre-validated F/N) — this is the cheap kind of leg.

## Hygiene (inherited, non-negotiable)

Provenance JSON per leg (model sha/GGUF sha, commit, binary shas, seeds, dtype incl. KV f16 note,
bank sha, window, trim rule); watch byte-progress not completion; checkpoint-pull every leg;
delete-gate on extraction; raw npy never in git; one GPU job at a time; teardown record.
