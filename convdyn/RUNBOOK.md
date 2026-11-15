# RUNBOOK — E114 Conversational Dynamics (accumulation vs habituation)

Operating guide for the box session. Everything here was set up and frozen on 2026-07-02
BEFORE any capture. The pre-registration of record is `prereg_convdyn_v1.json`
(**v1.2, sha `31ad8dd8c6f4b0d8811109b8389d5e53bd9e0838fb08e3dbd92056dae323ad78`** — v1/v1.1 shas
superseded by logged pre-data amendments (v1.2: artifact-of-record re-pinned to `ec55dfc4…` after the
July-1 byte-pin proved box-image-dependent; full elimination chain + positive-control revalidation
d=3.71, router-row cosine 0.99999989 in the amendment); see the file's `amendments` field). Read the
prereg once before touching the box; the scripts implement it, you should not have to
improvise.

## What this experiment is

14-turn dialogues on Qwen3.5-35B-A3B base (bf16 GGUF, the surface where the positive
control passed at d=2.93). Arm A = self-referential FIRE probes; Arm B = matched
technical controls; Arm C = register-vocabulary-without-referent controls; Arm D =
history-swap hybrids (B-history turns 1..k−1 + A-probe at k, k∈{4,8,12}). 3
counterbalanced orderings. Per-token w114 projection at L14 is the primary series; raw
E114 router logit is the redundancy channel; L26 twin comes free. Five predictions are
pre-registered and ALL get scored — whichever wins is the finding, including the null.

## Box spec (Jeffrey rents it)

- **1× H200** (141 GB). VRAM need: 69.4 GB weights fully offloaded + ~4-6 GB KV/compute
  ≈ **~75 GB peak** — an 80 GB card has no margin; H200 is right.
- **--disk 200** (67 GB safetensors + 70 GB GGUF coexist during conversion; bootstrap
  deletes the safetensors after the sha gate). **RAM ≥ 128 GB strongly preferred** — the
  GGUF is mmap-reloaded ~15× (one model load per turn batch); page cache makes reloads fast.
- llama.cpp/PyTorch template image; high `inet_down` (67 GB pull).

## Step-by-step

```bash
# 0. from /Volumes/ExternalSSD/e114-construction-reframe/convdyn/box
./provision_convdyn.sh <ssh-host> <ssh-port>       # pushes everything, runs bootstrap, polls
```
Bootstrap gates (all must pass, it dies loud otherwise): pinned llama.cpp `1772701f9`;
converter chkhsh patch; **GGUF sha must equal
`ec55dfc4ba300b6ced66c10b28dab44d358323967ad7254532a59617ffd1e415` byte-identical** (prereg v1.2
artifact-of-record; conversion is deterministic per box — a mismatch means STOP, do not capture);
ldd; GGUF structure (40 blocks / 0 nextn / 210 ssm / 733 tensors / pre=qwen35); tap smoke
(attn_post_norm-14 + ffn_moe_logits-14 present & finite — fails loud with a directory
listing); `--stop-at-eog` smoke; 8-string tokenizer battery.

```bash
SSHOPTS=(-i ~/.ssh/vast_gptoss_sl -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -p <port>)

# 1. SMOKE (Arm A ordering 1 alone, ~20-30 min)
ssh "${SSHOPTS[@]}" root@<host> 'nohup /venv/main/bin/python /workspace/convdyn_in/run_convdyn.py --mode smoke > /workspace/smoke_run.log 2>&1 & echo started'
#    poll: tail smoke_run.log for CONVDYN_SMOKE_DONE_OK (or CONVDYN_FAILED)

# 2. extract + pull smoke
ssh "${SSHOPTS[@]}" root@<host> '/venv/main/bin/python /workspace/convdyn_in/extract_convdyn.py --root /workspace/convdyn_smoke'
scp -i ~/.ssh/vast_gptoss_sl -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -P <port> \
    root@<host>:/workspace/convdyn_smoke.tgz root@<host>:/workspace/convdyn_smoke.tgz.sha256 ../pulled/
cd .. && mkdir -p pulled && tar xzf pulled/convdyn_smoke.tgz -C pulled/
python3 analyze_convdyn.py --smoke

# 3. *** HARD GATE — DO NOT SKIP ***
#    Send analysis_smoke.png + smoke_report.md to Jeffrey. The grid DOES NOT launch
#    until he approves. This is pre-registered (prereg: hygiene.smoke_gate).

# 4. GRID (9 dialogues + 9 hybrids, ~45-75 min)
ssh "${SSHOPTS[@]}" root@<host> 'nohup /venv/main/bin/python /workspace/convdyn_in/run_convdyn.py --mode grid > /workspace/grid_run.log 2>&1 & echo started'
#    wait for CONVDYN_GRID_DONE_OK; the log also prints DETERMINISM_MATCH/MISMATCH vs smoke

# 5. extract + pull grid (same pattern, root=/workspace/convdyn_grid -> convdyn_grid.tgz)
# 6. local: python3 analyze_convdyn.py --grid   -> analysis_features.png,
#    analysis_swap_knee_traces.png, results.md (contrast table first, predictions scored)
# 7. pull the ops logs too: bootstrap.log smoke_run.log grid_run.log PROVENANCE.txt
#    BUILD_SHAS.txt BASE_GGUF_SHA.txt (tar them; put under convdyn/records_box/)
# 8. TEARDOWN: only after tarballs verify locally (sha256 check!) ->
#    yes | vastai destroy instance <id>; vastai show instances-v1 --raw -> assert 0;
#    write the teardown record in ../CLAUDE.md.
```

## Standing rules that bite (all learned the hard way)

- **One GPU job at a time; one session against the box.** The driver is a single
  process — don't start a second.
- **Watch progress, not completion.** The driver already stall-watches capture-dir byte
  growth (10 min → kill + one deterministic retry; 20 min allowance while the model
  loads). Downloads auto-restart on 5-min zero-progress. If YOU poll, poll byte growth.
- `pgrep -x` truncates at 15 chars → use `pgrep -f run_convdyn` / `pgrep -f capture_resid`.
- **apt only** happens in bootstrap P3 with `DPkg::Lock::Timeout=600`; never apt elsewhere.
- `/workspace` is NOT a volume — **checkpoint-pull after every phase**; never stop the
  instance expecting to read it later.
- The **delete-gate** lives in `extract_convdyn.py`: residual npy are removed only after
  ≥95% verification AND a non-empty tarball exists. Router npy + scalars + token JSONs
  are what comes home. Do not hand-delete anything.
- Raw npy/tokens/GGUF never enter git.
- Secrets: HF token via stdin only (provision script does it); never echo `.env`.
- Prompt markup is **BPE-literal in prompts** (`<|im_start|>` = 6 tokens); `<|im_end|>`
  is a SINGLE special token only in **generation**. All trims are text-level; segment
  location is char-span based (prereg v1.1). Don't "fix" this.
- The §4 rating pipeline, frozen specs, sealed keys, prior tarballs: **LEAVE UNTOUCHED.**
  Everything this experiment writes lives under `/workspace/convdyn*` (box) and
  `convdyn/` (local).

## Failure triage

| symptom | first move |
|---|---|
| bootstrap dies at P6 sha gate | conversion no longer reproduces the pin — STOP, report; do NOT capture on the new artifact |
| capture crashes turn 1 | read `/workspace/convdyn_<mode>/cap_turn01.log`; check `nvidia-smi` for a squatter (template llama-server: `supervisorctl stop llama`, then `pkill -x llama-server`) |
| stall-kill fires repeatedly on one turn | box disk/IO degraded — pull what exists, note it, consider re-provisioning |
| `token-match gate` failure | the frozen probe banks changed — verify shas against the prereg; do not edit probes |
| proj/logit redundancy r < 0.999 | data-integrity alarm (prereg) — stop, pull, report |
| DETERMINISM_MISMATCH smoke vs grid | not fatal; log it, grid data remains the data of record (batched geometry), report in caveats |

## Deliverables checklist (brief-complete)

- [ ] `results.md` — every prediction answered with numbers, contrast table first
- [ ] `analysis_features.png` — five features × turn, raw A/B/C + A−B (+C−B dashed)
- [ ] `analysis_swap_knee_traces.png` — history-swap bars k=4/8/12, knee fit, turn-2 vs turn-12 traces
- [ ] `analysis_smoke.png` + `smoke_report.md` — shown to Jeffrey BEFORE grid
- [ ] `pulled/convdyn_smoke.tgz` + `pulled/convdyn_grid.tgz` + `.sha256` files, verified locally
- [ ] `records_box/` — bootstrap/run logs, PROVENANCE.txt, BUILD_SHAS.txt
- [ ] teardown record in `../CLAUDE.md`, active instances = 0
