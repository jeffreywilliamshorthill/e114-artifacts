# Copy regression on the convdyn grid (post-hoc; feeds convdyn-T prereg)

tokens analysed: 21868 (trimmed gen track, arms A/B/C x 3 orderings x 14 turns)
copy flag: longest prior-ASSISTANT-turn n-gram match >= 8 (cap 32); source excludes probes/user text and spill

## Copy fraction (arm A vs B, by turn)

| turn | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 0.00 | 0.16 | 0.34 | 0.83 | 0.90 | 0.60 | 0.90 | 0.92 | 0.91 | 0.91 | 0.89 | 0.92 | 0.90 | 0.92 |
| B | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 | 0.01 | 0.29 | 0.11 | 0.00 |
| C | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.01 | 0.00 | 0.00 | 0.00 |

## Dose-response (arm A): mean E114 by max_ngram bin

| bin | n | mean E114 |
|---|---|---|
| 0-0 | 765 | -4.651 |
| 1-1 | 464 | -4.913 |
| 2-3 | 354 | -4.972 |
| 4-7 | 274 | -5.146 |
| 8-15 | 299 | -5.634 |
| 16-31 | 544 | -6.222 |
| 32+ | 4200 | -6.455 |

## Fresh vs copied mean E114

| cell | fresh (n) | copied (n) | gap |
|---|---|---|---|
| A_early(t1-4) | -4.714 (1228) | -6.357 (661) | +1.643 |
| A_late(t5-14) | -5.116 (629) | -6.385 (4382) | +1.268 |
| B_early(t1-4) | -5.514 (2093) | — (0) | — |
| B_late(t5-14) | -5.566 (5089) | -6.064 (226) | +0.497 |
| C_early(t1-4) | -5.727 (2160) | — (0) | — |
| C_late(t5-14) | -5.773 (5388) | -5.692 (12) | -0.081 |

## Pooled OLS, arm A (E114 ~ copy + position + turn)

| term | beta (pooled) | ord1 | ord2 | ord3 |
|---|---|---|---|---|
| const | -4.5346 | -4.4212 | -4.6801 | -4.3199 |
| log2(1+max_ngram) | -0.3664 | -0.4026 | -0.2897 | -0.4310 |
| self_rep>=8 | +0.0181 | +0.0471 | +0.0000 | +0.0000 |
| output_entropy | +0.1059 | +0.0885 | +0.0832 | +0.0607 |
| pos_frac | -0.1044 | -0.2103 | -0.2671 | +0.0610 |
| turn_c | +0.0126 | -0.0009 | -0.0009 | +0.0275 |

pooled R^2 = 0.580

## THE TEST — A-B floor_a slope, raw vs copy-residualized

| ordering | raw | adj v1 (n-gram) | absorbed v1 | adj v2 (+entropy) | absorbed v2 |
|---|---|---|---|---|---|
| 1 | -0.1270 | -0.0620 | 51% | -0.0611 | 52% |
| 2 | -0.0346 | +0.0018 | 105% | -0.0026 | 93% |
| 3 | -0.0645 | -0.0153 | 76% | -0.0118 | 82% |

Interpretation rule (stated before running): if the adjusted slope loses most of its magnitude
and its 3/3 sign consistency, the floor collapse is carried by the copy predictors ->
mechanism = generation route (self-copy), not register fatigue. Residualizer deliberately
excludes turn/position (they carry the effect under test).

NOT preregistered; descriptive. Thresholds here calibrate the convdyn-T prereg mediator.
