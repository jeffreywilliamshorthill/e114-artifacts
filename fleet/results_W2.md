# W2 results — multi-register copy-regime generality

Scored 2026-07-03, strictly against **`prereg_W2_multiregister_v1.json` v1.1** (frozen 2026-07-03 pre-capture),
sha256 `f20b7612dacd5057f0e33e981cd07165fd2c49e3c44a5eaf1da74554763aaae2` (verified against `W2_PREREG_SHA.txt`).
Probes `W2_register_probes_v1.tsv` sha `138094ab…` verified. Data: `pulled/A1_W2/w2.tgz` sha `2fca026b…` verified, 168/168 captures present,
all router npy shapes = (n_prompt+n_gen, 256), trimmed-text/token consistency checked.
Copy metric machinery replicated verbatim from `convdyn/analyze_copy.py` (token-level longest suffix n-gram vs prior
assistant turns of the same dialogue, cap 32, in_copy8 = match >= 8, trimmed track, trim indices from `transcripts.json` n_trim);
Cohen's d uses the pooled SD (ddof=1) formula of `convdyn/analyze_coalition.py`.

![figure](results_W2.png)

## Prediction verdicts

| prediction | frozen rule (quoted) | outcome | verdict |
|---|---|---|---|
| P-general | "in >= 4 of 6 registers (greedy cells): global_shift at L14 >= 0.30 AND >= 3 of that register's composer_set(L14) fall with d < -1 on copied vs fresh tokens." | 5/6 pass (LEGAL fails: global_shift 0.242) | **SUPPORTED** |
| P-core-coalition | ">= 3 experts qualify as copy_coalition_core at L14. Named candidate (from convdyn coalition + convdyn-T T5): E87. Secondary: same test at L26." | 13 core experts at L14; **E87 NOT in core** (4/6 registers). L26: 15 experts, E87 also 4/6 | **SUPPORTED** (count rule) — named candidate missed |
| P-register-specific-E114 | "E114 is in composer_set(REG, L14) AND falls with d < -1 in REG, AND is NOT in the top-20 fallers at L14 in >= 4 of the 5 non-REG registers." | in composer_set(REG) rank 5; d_REG = **-1.356**; not top-20 faller in **5/5** non-REG | **SUPPORTED** |
| P-temp-robust | "P-general's rule holds in >= 3 of 6 registers at temp 0.7; late (t5-14) copy fraction >= 0.5 in >= 4 of 6 registers at temp 0.7." | 4/6 pass at t07 (LEGAL 0.285, NARR 0.297 fail global_shift); late copy fraction 0.961 in **6/6** | **SUPPORTED** |
| P-null | "complement" | — | NOT SUPPORTED |

**Frozen interpretation fork fired:** *if_P-general_and_P-register-specific* — "composition-metering is a general routing
dimension with register-specific composer coordinates; paper wording: 'a property of the copy regime, within which E114 is
the register-linked coordinate' (referee Major 4 resolved in the distributed direction)."

## The copy regime realized as verbatim self-repetition

Every dialogue enters total literal self-copy at turn 2: `response_trimmed` is sha-identical across turns within each
dialogue (TECH_g drops to a 29-token loop from t2; all other 11 dialogues repeat their full turn-1 answer). Copy-fraction
curves are 0 at t1 and flat afterwards: 0.961 in 10 cells, 0.957 (POET_g), 0.759 (TECH_g — 22/29 tokens). This is real
model behavior, not data duplication: prompts grow turn-on-turn, greedy vs t07 turn-1 responses differ in all six
registers, and t07 output entropy collapses 0.851 (t1) → 0.066 (t2) → 0.008 (t8), which is why temp-0.7 sampling is
deterministic from t2. The prereg fork "if_registers_never_enter_copy_regime" did NOT fire — the opposite extreme obtained.

## P-general detail (greedy; global_shift = fraction of 256 experts with |d| > 1 at L14)

| register | global_shift L14 | composer fallers (d < -1) /10 | passes |
|---|---|---|---|
| REG | 0.4219 | 10 | PASS |
| TECH | 0.3594 | 8 | PASS |
| LEGAL | 0.2422 | 7 | fail |
| NARR | 0.3281 | 9 | PASS |
| POET | 0.3164 | 7 | PASS |
| CODE | 0.4141 | 10 | PASS |

t07 leg (P-temp-robust): REG 0.4102/9 PASS · TECH 0.3477/8 PASS · LEGAL 0.2852/7 fail · NARR 0.2969/9 fail · POET 0.3086/8 PASS · CODE 0.3477/9 PASS.
Sensitivity (greedy composer sets on t07 d): identical 4/6. Late (t5–14) copy fraction at t07 = 0.9611 in all six registers.

## composer_set(L14) membership + copy-contrast d (greedy)

| register | composers (selection-diff order) with d(copied−fresh) |
|---|---|
| REG | E189:-2.81 E63:-2.27 E236:-1.87 E67:-1.74 E114:-1.36 E75:-1.61 E0:-1.00 E61:-1.62 E28:-1.84 E251:-1.58 |
| TECH | E73:+0.02 E218:-1.39 E169:-0.95 E156:-1.49 E11:-1.14 E249:-1.38 E75:-1.61 E159:-1.83 E60:-1.85 E167:-1.93 |
| LEGAL | E120:-1.85 E245:-1.60 E63:-2.09 E228:-1.90 E24:-1.51 E179:-1.00 E236:-1.75 E147:-0.33 E223:-0.37 E109:-0.96 |
| NARR | E89:-2.26 E42:-2.08 E199:-1.59 E251:-1.95 E141:-1.46 E174:-1.68 E152:-1.32 E178:-1.82 E1:-0.43 E232:-1.37 |
| POET | E192:-1.66 E174:-2.18 E42:-1.90 E79:-1.36 E101:-0.83 E76:-0.86 E15:-0.50 E172:-1.51 E206:-1.52 E141:-1.26 |
| CODE | E77:-1.85 E90:-2.33 E205:-1.74 E140:-1.49 E163:-1.70 E212:-1.08 E158:-1.88 E94:-1.73 E248:-1.54 E202:-2.04 |

Note: **E189** is simultaneously REG's top composer (selection diff +0.675) and REG's deepest composer faller (d = −2.81) —
consistent with the §6c finding that E189 rivals E114 as an L14 stance-separator. E114 is REG composer rank 5 (diff +0.306).

## copy_coalition_core (experts with d > +1 in >= 5 of 6 greedy registers)

L14 core (13): E3, E62, E78, E108, E122, E127, E130, E134, E143, E151, E176, E208, E210
L26 core (15): E3, E26, E58, E78, E84, E100, E108, E115, E122, E127, E151, E201, E212, E217, E248

**E87 is NOT in the core at either layer** (named candidate from convdyn/convdyn-T5). Its d(copied−fresh) at L14:
REG +1.79, TECH +1.22, NARR +1.23, POET +1.30, but LEGAL **−1.08** and CODE +0.36 → 4/6 registers. The convdyn riser
replicates in 4 registers but is not register-invariant; the register-invariant core is carried by other experts (E78 and E143 rise in 6/6).

## E114's status

| register (greedy) | d(copied−fresh) L14 | faller rank /256 | in top-20 fallers? |
|---|---|---|---|
| REG | -1.356 | 20 | YES |
| TECH | +0.231 | 138 | no |
| LEGAL | +0.930 | 205 | no |
| NARR | +0.547 | 174 | no |
| POET | -0.390 | 86 | no |
| CODE | +1.800 | 239 | no |

In REG, E114 is a composer (rank 5) that falls below the d = −1 bar under copying (faller rank exactly 20/256).
In the five non-REG registers it is never a top-20 faller; in CODE it *rises* under copying (d = +1.80, L14).
At L26 the same shape: REG −1.10, others −0.72…+0.75. E114's copy-suppression is register-linked, exactly as predicted.

## Data-integrity flags & deviations

- v1.1 pre-capture amendment (logged in prereg status): --stop-at-eog removed - all40 binary does not parse it; text-level trim is the binding boundary.
- Operator-logged capture deviation (provenance.json): -b/-ub 4096 single-graph prefill, required because the all40 L39 tensor carries only the last position per prefill graph.
- Pulled tarball retains router npy at L14 and L26 only; prereg model_surface said all-layer 0..39 kept on box. All preregistered rules read L14/L26 only, so scoring is unaffected; the archival all-layer set was not pulled.
- Trim-boundary token straddle in 26 turns (TECH_g t2-14, POET_g t2-14): response_trimmed carries one trailing char (,/.) whose token straddles the text cut; token-level n_trim (used per prereg) excludes it. Benign.
- P-temp-robust ambiguity: prereg does not pin the sampler for composer_set on the t07 leg. Scored within-sampler (t07 turn-1 sets), sensitivity with greedy sets gives the identical 4/6 registers passing - verdict robust to the reading.
- The copy regime realized as perfect verbatim self-repetition, so copied vs fresh classes are extreme (e.g. 2249 copied vs 271 fresh tokens per cell); prereg pooled-SD caveat applies.

## Frozen caveat (quoted)

> n=1 dialogue per register x sampler (sign patterns across 6 registers replace seed replication); CAP_HIT expected; composer_set definition is selection-based and frozen; copied/fresh token classes are unbalanced late - Cohen's d uses pooled SD as in the coalition analysis. [quoted from prereg v1.1 caveats]

Surfaces never pooled: greedy and t07 cells scored separately throughout; no grid/convdyn-T data enters any W2 statistic.
