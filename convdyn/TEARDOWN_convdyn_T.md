# Teardown record — convdyn-T box (Vast 43650141)

- **Instance:** 43650141, 1× H200 NVL, 500 GB disk, $4.409/hr, `ssh7.vast.ai:10141`
- **Destroyed:** 2026-07-03 early AM (local) · `vastai destroy instance 43650141` · **active instances after: 0** · credit remaining: $40.68 (final billing may settle slightly later)
- **Session cost:** ~7 h wall (bootstrap 7 min → battery ~5.5 h → extract/uploads) ≈ $31
- **What ran:** convdyn-T battery per `prereg_convdyn_T_v1.json` v1.2 (sha `64964043…`) — 276/276 captures verified, redundancy r=1.000000
- **Artifacts pulled before destroy (all verified):**
  - `pulled/convdyn_T.tgz` sha256 `222b90fb9d006345a4dfcd5f2696dee5f9a072f3015d8d5caf796d740854e8db` (1.6 GB; routers L13/14/15/26 retained, residuals excluded per delete-gate) + extracted `pulled/convdyn_T/`
  - `pulled/convdyn_T_run.log`, `pulled/extract_T.log`, `PROVENANCE_box_*.txt` (bootstrap-time)
- **Off-box checkpoints (private HF `ec75hash/e114-checkpoints`):**
  - `convdyn_T.tgz` + `.sha256`
  - `qwen35-35b-a3b-base-bf16.ec55dfc4.gguf` (69.4 GB pin-insurance archive of the prereg GGUF artifact)
- **Binary shas (from box PROVENANCE):** capture_residuals `eb09950c…`, capture_residuals_eog `08ac4a94…`, llama-tokenize `0f2784b7…`; llama.cpp `1772701f99dd3fc13f5783b282c2361eda8ca47c`; GGUF conversion reproduced pin `ec55dfc4…`
- **Why destroyed instead of kept for replication legs:** overnight idle (≈8 h × $4.41 ≈ $35) exceeds a fresh-box bootstrap; nothing box-specific remains (replication legs use community Q8 GGUFs, not the 3.5 artifact). Legs run on a fresh box after Jeffrey approves/freezes `replication/spec_multi_model_v1.md`.
- **Results:** `results_T.md` / `results_T.json` / `analysis_T.png` — T2(0.7)/T3/T4/T5 SUPPORTED, T1 graded middle (copying survives temp 0.7 at 0.88 late copy-frac; suppression mildly attenuated).
