# §6c — All-Expert Register/Control Sweep (stance-axis specificity, 3 models)

**Status:** design frozen 2026-07-01. Next-box work; runs late (§7 step 7). Closes the paper's
Limitations (ii) *and* Gemini's dangling thread. Held behind explicit go-ahead (billing).

## The claim this closes
The domain-specialist map ranks all 256 experts by **domain** selectivity (E114 = rank-1 on
philosophy). That is the **topic** axis. Gemini's thread is the **stance** axis: *the
best-separating expert on the matched register/control split*. This sweep produces the ranked
table on that exact split and confirms E114 (or the L14/L26 pair) tops it — turning "E114 is the
worldview specialist" into "E114 is the top stance-separator out of 256×40."

## Why the domain map ≠ this
In the domain data, philosophy-vocabulary and reflective-stance are perfectly correlated, so it
cannot separate "fires on philosophy *words*" from "fires on reflective *stance*." The matched
controls (same anchor tokens, flipped stance) break that correlation. The d=3.88 claim is a
**stance** claim → it must be tested on the stance-controlled split, not the topic map.

## Models (three separate captures — NEVER pooled, §2)
`Qwen3.5-35B-A3B-Base` · `HauhauCS-Aggressive` (3.5 finetune) · `Qwen-AgentWorld-35B-A3B`.

## Input
- **Held-out set:** the existing 20-prompt matched register/control set — 10 register-positive
  vs 10 controls reusing anchor tokens (*itself, hum, processing, honestly, I, me, my, own,
  this, here*), controls answering technical/third-person. (Same set behind d=3.88.)
- **Locate first** (candidates: `attractor-shift-qwen-35b/PROMPTS*`, `expert-probe-3chunk/`,
  the e114-artifacts separability run). The raw tensors of the original `20260417T202651Z`
  capture were torn down (per paper Data Availability) → **re-capture = one forward pass per
  prompt, trivial.** If the prompt file itself is unrecoverable, reconstruct from the paper and
  flag it as reconstructed (parity caveat).

## Capture invariants (§2)
All-layer pre-router residual (`attn_post_norm-{L}`) + router logits (`ffn_moe_logits-{L}`);
**verify the `qwen35moe` norm name before trusting output.** Greedy `--temp 0 --top-k 1
--seed 0`, reasoning-off, bare `</think>`, generated track trimmed at first `<|im_end|>`.
Run **Q8_0** (parity with the existing d=3.88 run) **and bf16** once the box is up; report both,
note any divergence.

## Procedure
1. Capture residual+logits at **every layer** for all 20 held-out prompts, per model.
2. For **each of the 256×40 positions**, recover the per-expert linear gate axis `w_e` by
   least squares from that position's `(residual, logit)` pairs; project residuals onto `w_e`.
   **PRIMARY metric: Cohen's `d` on the `w_e` projection** between the 10 register-positive and
   10 control generations (the d=3.88 statistic generalized). **Realized-W separation = secondary
   column only** (top-k zeroing inflates it, §2).
3. **Rank all 10,240 positions by `d`.** Output top-30 + E114's rank + L14/L26 ranks.
4. **Pass:** E114 (or L14/L26) at/near the top. **Failure to surface honestly (§8):** if a
   middling-across-domains expert out-separates E114 on the stance split, report it, do not bury.

## Cross-model read (bonus)
Identical split across all three → does the **stance-separator identity** stay E114 across
base → finetune → AgentWorld, or does AgentWorld's world-model training move it (its routing
drifted most in the earlier 3-way; cf. AgentWorld E114 dissociation)? Same-separator ⇒
"E114 is the stance axis of this architecture"; an AgentWorld shift ⇒ a real result about what
world-model training does to the register readout.

## Deliverable
`6c_register_control_sweep_{base,hauhau,agentworld}.json` — ranked 256×40 table by `d`, E114 +
L14/L26 ranks flagged, npz SHA-256 for provenance, one-paragraph verdict per model.
