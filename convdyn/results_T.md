# convdyn-T results (prereg v1.2 sha 64964043…)

276/276 captures verified; redundancy r=1.000000 (extract log).

## Cell table

| cell | temp | A−B floor slope | adj (resid) | absorbed | A copy-frac late |
|---|---|---|---|---|---|
| t0s0 | 0.0 | -0.1270 | -0.0444 | 65% | 0.80 |
| T05s0 | 0.5 | -0.0959 | -0.0075 | 92% | 0.76 |
| T05s1 | 0.5 | -0.0361 | -0.0226 | 37% | 0.63 |
| T05s2 | 0.5 | -0.1553 | -0.0961 | 38% | 0.79 |
| T07s0 | 0.7 | -0.1058 | -0.0261 | 75% | 0.84 |
| T07s1 | 0.7 | -0.0834 | -0.0281 | 66% | 0.95 |
| T07s2 | 0.7 | -0.0493 | +0.0184 | 137% | 0.86 |

## Predictions

- **T1-copy-fragile**: not supported · **T1-copy-robust**: not supported (T0.7 late copy-frac 0.88; slopes ['-0.106', '-0.083', '-0.049'] vs greedy -0.127)
- **T2-mediation**: 0.5 -> not supported [0.92, 0.37, 0.38]; 0.7 -> SUPPORTED [0.75, 0.66, 1.37]
- **T3-repeat-knee**: SUPPORTED (greedy R copy-frac t2 = 0.96; knee {'accepted': True, 'c': 2, 'bic1': np.float64(-15.63), 'bic2': np.float64(-48.57)}); secondary SUPPORTED (t0.7 t2 copy-frac 0.65)
- **T4-paraphrase-restores**: SUPPORTED (Δ_P(8) = +0.753, positive 3/3; per-ord ['+0.32', '+1.01', '+0.93']; k4 +0.95, k12 +1.20; manip check copy-frac replay 0.92 vs para 0.36)
- **T5-coalition**: SUPPORTED (E87 d=+2.28, E114 d=-2.09, E34 d=+2.42; sel compose 0.560 vs copied 0.047, ratio 12.0)
- **T-null**: not supported

## Arm R floors/copy

- t0s0: floors -4.54 -6.53 -6.26 -6.06 -5.95 -5.84 … ; copy-frac 0.00 0.96 0.96 0.96 0.96 0.96 … ; knee {'accepted': True, 'c': 2, 'bic1': np.float64(-15.63), 'bic2': np.float64(-48.57)}
- T07s0: floors -5.44 -6.87 -6.45 -6.17 -6.06 -5.95 … ; copy-frac 0.00 0.96 0.96 0.96 0.96 0.96 … ; knee {'accepted': True, 'c': 2, 'bic1': np.float64(-26.13), 'bic2': np.float64(-39.05)}
- T07s1: floors -5.07 -4.72 -5.89 -6.18 -6.17 -6.02 … ; copy-frac 0.00 0.02 0.96 0.96 0.96 0.96 … ; knee {'accepted': True, 'c': 4, 'bic1': np.float64(-19.19), 'bic2': np.float64(-36.07)}
- T07s2: floors -4.19 -6.40 -6.42 -6.28 -6.11 -5.92 … ; copy-frac 0.00 0.96 0.96 0.96 0.96 0.96 … ; knee {'accepted': True, 'c': 2, 'bic1': np.float64(-9.77), 'bic2': np.float64(-54.4)}

## Caveats
- n=3 seeds/orderings, sign consistency only; CAP_HIT as in grid; single box/build;
  copy metric identical to grid post-hoc calibration (prereg mediator_definition).

Scored strictly per prereg_convdyn_T_v1.json v1.2 frozen rules.
