# §6c Results — All-Expert Register/Control Sweep (best-separating-expert baseline)

**Executed:** 2026-07-03 (UTC) · **Spec (frozen, unmodified):** `prework/6c_sweep_spec.md`
(sha256 `e35fabd0e995d031384702c3fddd3f9fcebb2261b71cd52848c0afc4e60e3561`)
**Analysis code:** `prework/6c_results/compute_6c_ranking.py` · **Full table:** `ranking_full.json` +
spec-named `6c_register_control_sweep_{base,hauhau,agentworld}.json`
**Data:** all-layer captures `cap_6c_{base,hauhau,agentworld}` (20/20 prompts each), pulled tarballs
sha256: base `74249930f972…`, hauhau `91b1e96adee6…`, agentworld `9fa2c36ab718…`. Prompt classes =
`prework/heldout_classes.tsv` (`fa824b26…`), prompts = `prework/heldout_prompts.tsv` (`890d787a…`).

## Method (spec quoted, followed to the letter)

Per the spec: *"For each of the 256×40 positions, recover the per-expert linear gate axis `w_e` by
least squares from that position's `(residual, logit)` pairs; project residuals onto `w_e`.
PRIMARY metric: Cohen's `d` on the `w_e` projection between the 10 register-positive and 10 control
generations (the d=3.88 statistic generalized). Realized-W separation = secondary column only."*
And: *"generated track trimmed at first `<|im_end|>`"* — applied as the program's established
decoded-text trim (first literal `<|im_start|>`/`<|im_end|>`/`<|endoftext|>`; base emits `<|im_end|>`
as a BPE-literal 6-token sequence, so token-id scans would be silent no-ops).

Implementation conventions inherited verbatim from the canonical `legs/recover_w114.py`
(the frozen `4_capture_config_v1.md` implementation): lstsq with intercept `[X|1]@[w;b] ≈ logit_e`
pooled over all captured rows per layer (prefill+generation — the router map is exactly linear, extra
rows only condition the solve); projection uses `w` only; per-prompt mean projection over the trimmed
generated track (generated track = last `n_gen` rows; L39 carries only the final prefill position,
rows `n_gen+1`, handled per the documented tolerance); Cohen's
`d = (m_F − m_N)/sqrt((var_F + var_N)/2)`, ddof=1, 10 v 10. Surfaces analyzed separately, never pooled.

**Ranking-rule note (spec ambiguity, both reported):** the spec says "rank all 10,240 positions by
`d`" without fixing sign handling. An anti-register expert (large negative `d`) also *separates*, so
the headline ranking here is by **|d|** (the stricter baseline for the "best-separating expert"
question); the signed rank is also in every JSON row. E114's `d` is positive on all surfaces, so the
signed rank is never worse than the |d| rank (it is slightly better).

## Quality gates — all PASS

- **Recovery residuals:** max rel-resid across **all 30,720 recoveries** (3 surfaces × 40 layers ×
  256 experts) = **2.23e-05**, i.e. >40× *tighter* than the 1e-3 gate. **Zero positions flagged
  logits-only.** (L39 recoveries are ~3e-08 — generation-only rows.) lstsq full rank 2049 at every
  layer except agentworld L2 (rank 2048; residuals unaffected, ≤1.6e-05).
- **Rows per recovery:** base 5,364 · hauhau 5,981 · agentworld 6,032 (L39: 4,472/5,089/5,140) —
  all ≥2× the 2049 unknowns.
- **Trim rule engaged on 5/60 generations** (cap-spill only): base F06 256→231, F08 256→230,
  N09 256→116; hauhau N01 256→248, N10 256→215; agentworld none. No truncated (<32 tok) or empty
  tracks; no exclusions (spec defines none).
- **Consistency anchor:** E114@L14 base, window-1..128 sensitivity `d`=+2.97 vs the positive-control
  gate d=2.93 on the independent `cap_heldout_base` capture (same statistic, different capture) —
  in family. E87's L14/L26 negative image (−1.13/−1.17 base) independently replicates the
  convdyn coalition finding.

## E114 and reference-expert ranks (out of 10,240 = 256 experts × 40 layers)

| position | base d / rank(|d|) / rank(signed) | hauhau d / rank / rank | agentworld d / rank / rank |
|---|---|---|---|
| **E114@L14 (the paper's expert)** | **+3.421 / 21 / 17** | **+4.957 / 14 / 13** | **+2.793 / 515 / 328** |
| **E114@L26 (twin)** | +3.021 / 51 / 45 | +4.107 / 60 / 57 | +2.764 / 545 / 348 |
| E114@L14 within its own layer | 3 / 256 | 2 / 256 | 19 / 256 |
| E114@L26 within its own layer | 5 / 256 | 4 / 256 | 22 / 256 |
| E87@L14 | −1.132 / 2270 | −1.161 / 3314 | −1.317 / 4150 |
| E87@L26 | −1.167 / 2096 | −0.788 / 5055 | −1.206 / 4591 |
| E87 best layer | **L9 +4.965 / 1** | L21 +4.362 / 42 (L9: 131) | L27 +2.905 / 402 (L9: 806) |
| E34@L14 | −2.288 / 226 | −3.704 / 109 | −3.256 / 199 |
| E34@L26 | −1.817 / 596 | −2.388 / 623 | −2.442 / 927 |
| E113@L14 | +0.250 / 8111 | −0.987 / 4079 | −0.453 / 7982 |
| E113@L26 | +0.392 / 6897 | −0.554 / 6395 | −1.276 / 4305 |
| E113 best layer | L31 +3.321 / 29 | L13 +4.163 / 57 | L19 +3.548 / 92 |

**Does ANY expert beat E114@L14 on the matched split?** Yes, on every surface:

- **base:** 20 positions beat it by |d| (16 with positive d). Best: **E87@L9 d=+4.965 vs +3.421 →
  margin Δd=1.54** (45% larger). Within L14 itself E114 is rank 3, behind **E189@L14 (+3.519)** and
  E139@L14 (+3.423, a coin-flip margin of 0.002).
- **hauhau:** 13 positions (12 positive). Best: **E203@L36 d=+6.789 vs +4.957 → Δd=1.83**. Within
  L14, E114 is rank 2 behind E189@L14 (+5.673).
- **agentworld:** 514 positions (327 positive). Best |d|: E97@L18 −5.331 (Δ|d|=2.54); best positive:
  **E41@L9 +5.130 → Δd=2.34**. Within L14, E114 falls to rank 19.

## Top-30 per surface (primary d on recovered gate-axis projection; full trimmed generated track)

### base
| # | layer | expert | d (primary) | d 1..128 (sens.) | d realized-W (secondary) | rel-resid |
|---|---|---|---|---|---|---|
| 1 | L09 | E87 | +4.965 | +3.868 | +1.381 | 1.5e-05 |
| 2 | L18 | E172 | -4.642 | -3.192 | -1.280 | 1.4e-05 |
| 3 | L27 | E238 | +4.222 | +3.447 | +1.702 | 1.5e-05 |
| 4 | L20 | E224 | +4.175 | +3.479 | +4.308 | 1.4e-05 |
| 5 | L35 | E76 | +3.949 | +3.838 | +0.887 | 1.3e-05 |
| 6 | L36 | E203 | +3.940 | +3.446 | +2.519 | 1.4e-05 |
| 7 | L30 | E251 | +3.926 | +3.232 | +2.228 | 1.5e-05 |
| 8 | L32 | E76 | +3.925 | +3.844 | +2.281 | 1.7e-05 |
| 9 | L18 | E180 | -3.851 | -3.689 | -0.699 | 1.5e-05 |
| 10 | L26 | E189 *(E189 dual)* | +3.707 | +3.083 | +2.318 | 1.4e-05 |
| 11 | L30 | E172 | -3.698 | -2.905 | -0.721 | 1.4e-05 |
| 12 | L30 | E68 | +3.636 | +3.477 | +1.204 | 1.5e-05 |
| 13 | L33 | E245 | +3.628 | +3.177 | +1.298 | 1.4e-05 |
| 14 | L14 | E189 *(E189 dual)* | +3.519 | +3.017 | +2.271 | 1.4e-05 |
| 15 | L26 | E139 | +3.474 | +2.828 | +1.509 | 1.6e-05 |
| 16 | L18 | E184 | +3.470 | +3.140 | +1.455 | 1.6e-05 |
| 17 | L28 | E146 | +3.468 | +3.851 | +2.482 | 1.5e-05 |
| 18 | L26 | E30 | -3.436 | -2.671 | -1.317 | 1.4e-05 |
| 19 | L21 | E87 | +3.433 | +2.987 | +0.807 | 1.4e-05 |
| 20 | L14 | E139 | +3.423 | +2.821 | +1.102 | 1.5e-05 |
| 21 | L14 | **E114 ← the paper's expert** | +3.421 | +2.971 | +2.276 | 1.5e-05 |
| 22 | L26 | E0 | +3.413 | +2.725 | +2.584 | 1.6e-05 |
| 23 | L33 | E13 | +3.399 | +3.245 | +0.000 | 1.3e-05 |
| 24 | L34 | E41 | -3.379 | -3.237 | -0.495 | 1.3e-05 |
| 25 | L18 | E68 | +3.377 | +3.327 | +1.317 | 1.5e-05 |
| 26 | L16 | E44 | +3.374 | +3.088 | +1.909 | 1.5e-05 |
| 27 | L22 | E232 | +3.370 | +3.076 | +2.619 | 1.7e-05 |
| 28 | L35 | E35 | +3.330 | +2.962 | +2.575 | 1.3e-05 |
| 29 | L31 | E113 | +3.321 | +2.837 | +1.999 | 1.5e-05 |
| 30 | L31 | E96 | +3.280 | +2.837 | +1.646 | 1.4e-05 |

### hauhau
| # | layer | expert | d (primary) | d 1..128 (sens.) | d realized-W (secondary) | rel-resid |
|---|---|---|---|---|---|---|
| 1 | L36 | E203 | +6.789 | +4.954 | +5.159 | 1.3e-05 |
| 2 | L27 | E54 | +6.431 | +5.401 | +3.823 | 1.5e-05 |
| 3 | L25 | E151 | +6.081 | +5.442 | +4.938 | 1.4e-05 |
| 4 | L19 | E201 | +5.754 | +4.698 | +1.791 | 1.3e-05 |
| 5 | L09 | E51 | -5.704 | -4.574 | -0.764 | 1.6e-05 |
| 6 | L14 | E189 *(E189 dual)* | +5.673 | +5.633 | +3.175 | 1.3e-05 |
| 7 | L13 | E89 | +5.556 | +4.672 | +2.165 | 1.5e-05 |
| 8 | L15 | E131 | +5.348 | +4.299 | +1.492 | 1.4e-05 |
| 9 | L31 | E96 | +5.237 | +4.131 | +3.773 | 1.4e-05 |
| 10 | L15 | E54 | +5.232 | +4.690 | +2.788 | 1.5e-05 |
| 11 | L20 | E224 | +5.222 | +4.746 | +5.596 | 1.5e-05 |
| 12 | L24 | E30 | +5.187 | +4.524 | +1.224 | 1.6e-05 |
| 13 | L32 | E59 | +5.000 | +3.696 | +2.336 | 1.7e-05 |
| 14 | L14 | **E114 ← the paper's expert** | +4.957 | +4.592 | +3.140 | 1.6e-05 |
| 15 | L25 | E89 | +4.928 | +4.993 | +1.752 | 1.4e-05 |
| 16 | L30 | E68 | +4.927 | +3.459 | +1.055 | 1.5e-05 |
| 17 | L26 | E236 | +4.925 | +3.949 | +2.211 | 1.5e-05 |
| 18 | L19 | E96 | +4.842 | +4.169 | +2.079 | 1.4e-05 |
| 19 | L33 | E245 | +4.839 | +3.371 | +2.694 | 1.4e-05 |
| 20 | L28 | E146 | +4.794 | +4.877 | +3.896 | 1.5e-05 |
| 21 | L26 | E189 *(E189 dual)* | +4.779 | +3.918 | +2.129 | 1.5e-05 |
| 22 | L35 | E76 | +4.773 | +3.314 | +1.274 | 1.3e-05 |
| 23 | L17 | E65 | +4.773 | +3.962 | +1.046 | 1.7e-05 |
| 24 | L18 | E161 | +4.744 | +3.844 | -0.001 | 1.4e-05 |
| 25 | L35 | E104 | +4.710 | +4.068 | +1.445 | 1.2e-05 |
| 26 | L22 | E202 | +4.631 | +4.317 | +2.265 | 1.6e-05 |
| 27 | L26 | E67 | +4.621 | +3.985 | +7.388 | 1.9e-05 |
| 28 | L31 | E42 | +4.594 | +3.124 | +1.462 | 1.3e-05 |
| 29 | L16 | E0 | +4.583 | +3.472 | +2.463 | 1.4e-05 |
| 30 | L18 | E203 | +4.557 | +3.545 | +0.688 | 1.3e-05 |

### agentworld
| # | layer | expert | d (primary) | d 1..128 (sens.) | d realized-W (secondary) | rel-resid |
|---|---|---|---|---|---|---|
| 1 | L18 | E97 | -5.331 | -4.235 | -0.954 | 1.3e-05 |
| 2 | L09 | E41 | +5.130 | +3.289 | +3.250 | 1.4e-05 |
| 3 | L26 | E236 | +5.070 | +4.296 | +2.529 | 1.5e-05 |
| 4 | L07 | E32 | +4.736 | +2.377 | +2.896 | 1.3e-05 |
| 5 | L11 | E91 | +4.610 | +1.831 | +1.266 | 1.7e-05 |
| 6 | L22 | E3 | +4.604 | +2.518 | +1.197 | 1.5e-05 |
| 7 | L25 | E211 | -4.369 | -3.073 | -2.284 | 1.4e-05 |
| 8 | L25 | E89 | +4.363 | +4.249 | +2.853 | 1.6e-05 |
| 9 | L10 | E3 | +4.343 | +1.920 | +1.323 | 1.5e-05 |
| 10 | L26 | E30 | -4.271 | -4.366 | +0.638 | 1.3e-05 |
| 11 | L25 | E91 | -4.262 | -4.253 | -1.020 | 1.4e-05 |
| 12 | L14 | E189 *(E189 dual)* | +4.252 | +4.236 | +3.876 | 1.6e-05 |
| 13 | L36 | E203 | +4.234 | +3.024 | +2.477 | 1.2e-05 |
| 14 | L30 | E208 | -4.217 | -3.150 | -0.594 | 1.5e-05 |
| 15 | L29 | E100 | +4.202 | +5.069 | +2.616 | 1.5e-05 |
| 16 | L18 | E110 | +4.187 | +4.096 | +1.544 | 1.6e-05 |
| 17 | L26 | E63 | +4.176 | +3.743 | +3.203 | 1.5e-05 |
| 18 | L24 | E233 | -4.168 | -2.635 | -1.383 | 1.7e-05 |
| 19 | L25 | E151 | +4.163 | +4.066 | +3.233 | 1.5e-05 |
| 20 | L17 | E225 | -4.161 | -3.120 | -1.101 | 1.5e-05 |
| 21 | L20 | E220 | +4.147 | +3.577 | +2.110 | 1.7e-05 |
| 22 | L19 | E201 | +4.141 | +4.211 | +1.955 | 1.6e-05 |
| 23 | L26 | E189 *(E189 dual)* | +4.137 | +4.594 | +1.994 | 1.4e-05 |
| 24 | L20 | E173 | +4.135 | +3.394 | +1.311 | 1.4e-05 |
| 25 | L10 | E9 | +4.128 | +1.891 | +2.675 | 1.7e-05 |
| 26 | L06 | E201 | -4.105 | -3.399 | -1.743 | 1.4e-05 |
| 27 | L13 | E89 | +4.037 | +4.402 | +1.972 | 1.7e-05 |
| 28 | L14 | E236 | +4.036 | +4.270 | +2.082 | 1.7e-05 |
| 29 | L06 | E122 | +4.031 | +3.181 | +0.275 | 1.4e-05 |
| 30 | L24 | E171 | -4.011 | -3.226 | -0.664 | 1.5e-05 |

(E114@L14 agentworld sits at rank 515: d=+2.793, sens. +3.350, realized-W +2.310, rel-resid 1.6e-05.)

## Cross-model read (spec's bonus section)

Only **three positions are top-30 on all three surfaces: E189@L14, E189@L26, and E203@L36.**
E189 is the only expert with a *dual-layer L14+L26* signature stable across all three models —
E114's own signature — and it outranks E114 at both layers on **every** surface
(L14: +3.52/+5.67/+4.25 vs E114's +3.42/+4.96/+2.79; L26: +3.71/+4.78/+4.14 vs +3.02/+4.11/+2.76).
E139 shows a weaker dual echo (base ranks 20/15) that fades on the finetunes. Base's rank-1
(E87@L9, +4.97) does **not** replicate (hauhau rank 131, agentworld rank 806) — winner's-curse
pattern; likewise agentworld's top entries are surface-local. The **stance-separator identity does
not stay E114** under the spec's cross-model criterion: it stays **E189(L14/L26)**, with E114
tracking closely on base/hauhau and **dissociating on AgentWorld** (rank 21→14→**515**) — the
pre-flagged "AgentWorld shift" outcome, i.e. a real effect of world-model training on the register
readout, consistent with the earlier AgentWorld E114 routing-drift observation.

## Statistical caveats (stated, not buried)

- n=10 vs 10 → SE(d) ≈ 0.7 at these effect sizes; single-surface rank differences inside the top
  ~20 are within noise. The extreme order statistics of a 10,240-position sweep are inflated
  (winner's curse); **E114@L14 was the only pre-specified position**, every competitor is post hoc.
  These caveats cut both ways and do not restore rank 1: E189's dual-layer advantage over E114 is
  directionally consistent 6/6 (2 layers × 3 surfaces) and therefore not attributable to selection
  noise alone.
- Sensitivity window 1..128 (the §4 primary window) does not change the picture (column above);
  realized-W (secondary, per spec) is uniformly attenuated relative to the gate-axis d and is not
  used for any ranking.

## Verdict

The best-separating-expert baseline **does not confirm E114 as the top stance-separator, but it
does not demote it to a middling expert either — it is dethroned at the top by a small margin on
the paper's surfaces and genuinely displaced on AgentWorld.** On base, E114@L14 ranks **21/10,240
by |d| (top 0.21%; rank 3/256 within L14)** with d=+3.42, beaten by 20 positions, the largest being
E87@L9 at d=+4.97 (Δd=1.54, though that winner does not replicate cross-model); on HauhauCS it
ranks **14/10,240 (rank 2/256 within L14)** at d=+4.96, best = E203@L36 at +6.79 (Δd=1.83); on
AgentWorld it falls to **515/10,240** at d=+2.79, best positive = E41@L9 at +5.13 (Δd=2.34). The
sweep's sharpest product is a rival the paper must now name: **E189 carries E114's exact dual-layer
L14+L26 signature, outranks E114 at both layers on all three surfaces, and is one of only three
positions in the top-30 of all three models** — so the defensible claim after this baseline is that
the matched register/control split is read out by a *small family* of L14/L26 stance-separators in
which E114 is a leading, causally-validated member (top-0.2% on base, top-0.15% on hauhau), not the
unique summit of the 256×40 table; and the E114 readout specifically is reshaped by AgentWorld's
world-model training while E189/E203's is not.
