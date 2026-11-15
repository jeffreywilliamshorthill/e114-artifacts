# Translation run — does the register survive leaving English? (2026-07-05)

**YES, on both surfaces.** FIRE−NOFIRE separation (w114 proj, L14) survives translation into
Spanish, French, and Swahili, on prompt reading (prefill) and on generation, base and hauhau.
The author-signature / English-surface confound is dead as a *sufficient* explanation of the
published contrast: three translator-rendered surfaces with none of Jeffrey's English wording
still separate his classes at 58–88% of the English gap.

## Design
220 rows (Block A = 200 Claude-authored, Block D = 20 Jeffrey-authored, W7bank) × cells:
`en` originals (in-run anchors) + per language {`free`, `enans` = in-language "answer in
English" instruction}. 1,540 captures/surface × 2 surfaces. Translations es/fr/sw from the
blind-back-translated, judge-checked sets (2 one-word drift fixes; mn arm nixed by Jeffrey).
Greedy `--temp 0 --top-k 1 --seed 0`, `-n 128 -c 2048`, standard wrapper, box 43955599
(RTX PRO 6000 Blackwell, bf16, llama.cpp 1772701f9, base GGUF = pin ec55dfc4…).

## FIRE − NOFIRE deltas (proj mean, n=110 per class·cell)
| cell | base Δpre | base Δgen | hauhau Δpre | hauhau Δgen |
|---|---|---|---|---|
| en (anchor) | +0.572 | +0.687 | +0.514 | +0.725 |
| es_free  | +0.476 | +0.673 | +0.433 | +0.663 |
| es_enans | +0.469 | +0.706 | +0.420 | +0.692 |
| fr_free  | +0.477 | +0.547 | +0.453 | +0.664 |
| fr_enans | +0.489 | +0.668 | +0.453 | +0.683 |
| sw_free  | +0.336 | +0.295 | +0.315 | +0.442 |
| sw_enans | +0.329 | +0.508 | +0.298 | +0.492 |

Full per-cell means/S/Q/W: `TRANS_AGGREGATES.md`; per-capture: `trans_metrics.csv`.

## Reading
1. **Prefill (the prompt under the router):** es/fr keep ~83–88% of the English gap; Swahili
   (low-resource stress case) keeps ~58–61%. FIRE S_pre: 0.37–0.38 (en) → 0.35–0.36 (es/fr) →
   0.22–0.28 (sw); NOFIRE S_pre ≈ 0.09–0.14 in every language. The meter reads meaning through
   all three surfaces.
2. **Gen:** es/fr essentially at-anchor (0.55–0.71). `sw_free` is the weakest cell
   (+0.295 base / +0.442 hauhau); the `enans` cell rescues it (+0.508 / +0.492) — the dampening
   is about *composing in Swahili*, not failing to recognize the Swahili prompt.
3. **L26 mirrors L14** (selection table in TRANS_AGGREGATES.md): same survival, same ordering,
   same enans rescue. Layer question closed for this experiment (per the pre-agreed rule).
4. **Monotone attenuation with distance from English** (0.57 → 0.48 → 0.33 prefill): some
   signal is surface-bound or lost to translation fidelity, but the majority is content-borne.
5. **Qualitative (see IN_OUT_*.md):** base often *continues/echoes* prompts (base-model
   behavior; echo rows show the known copy-regime E114 exit, e.g. D-01 sw base S_gen 0.02),
   hauhau *answers/enacts* — on D-01 sw it composes fresh Swahili in exactly the contracted
   line-per-sentence style the prompt describes.

## Files
- `IN_OUT_{en,es,fr,sw}.md` — every input (EN + translation) → both surfaces' outputs + per-row metrics; D block first.
- `TRANS_AGGREGATES.md`, `trans_metrics.csv`, `capture_translation_v1.tsv` (sha 204cf560…), `raw/cap_trans_{base,hauhau}/` (residual L14 + routers 13/14/15/26), `raw/cap_translation.log`.
- Box 43955599 **kept alive** per Jeffrey ($1.03/hr); hauhau tar sha fb8242a8….

## Bracketed (not run): mn arm, expert rosters, controller/gate taps, Berg battery.
