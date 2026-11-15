# W7bank prereg — pre-capture amendment v1.1 (logged 2026-07-03, BEFORE any W7bank capture)

Frozen prereg: `prereg_W7bank_scaled_v1_FROZEN.json` (sha 48508a13…), frozen 2026-07-03T20:28:57Z.

## Amendments (all pre-capture, no data seen)

1. **Primary capture binary: `capture_residuals_all40` (all 40 layers) instead of
   `capture_residuals_eog` (layers 13,14,15,26).** Reason: endpoint **B2 (rank-at-scale)**
   requires all-position gate-axis recovery across all 256 experts × 40 layers, which the
   4-layer eog binary cannot provide. The all40 binary retains residuals identically (w114 and
   every per-expert gate axis recovered fresh from this capture by least squares), so B1 and B2
   both come from one 300-prompt pass. Binary sha recorded on box at launch.

2. **Turn bounding by decoded-text trim** (first literal `<|im_start|>`/`<|im_end|>`/`<|endoftext|>`
   in `generated_text`) rather than the eog binary's `--stop-at-eog`. This is the identical
   trim rule used in the original §4 analysis and the 3.6-35B replication leg (repl36), and
   `-n 256` caps generation length. The base surface emits `<|im_end|>` as the BPE-literal
   6-token sequence (convdyn prereg v1.3 note), so text-trim is the correct bound regardless.

3. **Scope this session: PRIMARY ONLY (300 captures).** The 780-capture robustness grid (B3) is
   deferred to a credit top-up (credit $29.17 at launch; full 1080-capture run 6–8 GPU-h ≈ $27
   would exhaust it mid-run). B1/B2/B4 (separability, rank-at-scale, natural-block) are delivered
   now; B3 (Q8-vs-bf16 + temperature dose curve) follows on top-up. Deferral logged, not silent.

Class labels, bank contents, block structure, and all endpoint decision rules are UNCHANGED.
Bank sha (wrapped): 13351fb7… ; keymap: W7bank_keymap.json.
