# Token-level register × freshness interaction model

**Post-hoc / descriptive. NOT preregistered.** Model per surface (never pooled), per expert
(L14 router logits), per freshness coding:

```
E_logit ~ const + register + fresh + register×fresh + pos_frac + turn_c
```

- binary coding: `fresh = 1[max_ngram < 8]`; continuous: `fresh = -log2(1+max_ngram)`
  (both oriented so higher = fresher).
- Copy metric machinery verbatim from `convdyn/analyze_copy.py` (suffix n-gram vs prior
  assistant turns of the same dialogue, cap 32, threshold 8, trimmed track).
- OLS; CR1 cluster-robust SEs in parentheses, clusters = capture (dialogue-turn).
- convdyn primary: arms A_register vs B_technical (greedy grid; D hybrids excluded);
  secondary adds C_vocabulary. W2 primary: REG vs TECH per sampler; secondary 6-register FE.
- convdyn E114 router column validated exactly against `scalars.npz` (`gen_logit14`).

## Surface: convdyn grid (A vs B, greedy; groups = orderings)

### binary freshness coding

| expert | register | fresh | register×fresh | pos_frac | turn_c | R² main | R² +int | ΔR² | int sign consistency | int t (CR1) |
|---|---|---|---|---|---|---|---|---|---|---|
| E114 | -0.3340 (0.0648) | +0.4755 (0.0726) | **+0.9859 (0.0981)** | -0.1676 (0.0381) | -0.0092 (0.0062) | 0.4597 | 0.4825 | +0.0228 | 3/3 (orderings) | +10.0 |
| E189 | -0.9034 (0.0726) | -0.0874 (0.0675) | **+2.1006 (0.1160)** | -0.2988 (0.0520) | -0.0322 (0.0081) | 0.4445 | 0.5024 | +0.0579 | 3/3 (orderings) | +18.1 |
| E87 | +0.0963 (0.1233) | -0.7351 (0.1450) | **-0.2276 (0.1409)** | -0.0041 (0.0293) | +0.0280 (0.0084) | 0.4182 | 0.4196 | +0.0014 | 3/3 (orderings) | -1.6 |

### continuous freshness coding

| expert | register | fresh | register×fresh | pos_frac | turn_c | R² main | R² +int | ΔR² | int sign consistency | int t (CR1) |
|---|---|---|---|---|---|---|---|---|---|---|
| E114 | +0.9429 (0.0868) | +0.1078 (0.0163) | **+0.2652 (0.0232)** | -0.1393 (0.0380) | -0.0008 (0.0065) | 0.4607 | 0.5091 | +0.0484 | 3/3 (orderings) | +11.5 |
| E189 | +1.6889 (0.1064) | -0.0355 (0.0172) | **+0.5387 (0.0291)** | -0.2618 (0.0506) | -0.0264 (0.0081) | 0.4098 | 0.5215 | +0.1117 | 3/3 (orderings) | +18.5 |
| E87 | -0.2792 (0.0764) | -0.1653 (0.0254) | **-0.0863 (0.0252)** | -0.0242 (0.0309) | +0.0196 (0.0086) | 0.4382 | 0.4439 | +0.0057 | 3/3 (orderings) | -3.4 |

### Per-ordering interaction betas (binary coding)

| expert | o1 | o2 | o3 | pooled |
|---|---|---|---|---|
| E114 | +1.472 | +0.634 | +1.270 | +0.986 |
| E189 | +1.850 | +2.292 | +3.007 | +2.101 |
| E87 | -0.540 | -0.007 | -0.615 | -0.228 |

### Secondary: C_vocabulary-included variant (binary coding), interaction terms

| expert | armA×fresh | armC×fresh |
|---|---|---|
| E114 | +0.9987 (0.0980) | -0.5469 (0.0946) |
| E189 | +2.1157 (0.1202) | -0.0279 (0.1003) |
| E87 | -0.2283 (0.1421) | +0.2877 (0.1805) |

## Surface: W2 (REG vs TECH; groups = samplers g / t07)

### binary freshness coding

| expert | register | fresh | register×fresh | pos_frac | turn_c | R² main | R² +int | ΔR² | int sign consistency | int t (CR1) |
|---|---|---|---|---|---|---|---|---|---|---|
| E114 (g) | +0.1148 (0.0633) | +0.1892 (0.1830) | **+0.7940 (0.3406)** | +0.2880 (0.0760) | +0.0553 (0.0100) | 0.2308 | 0.2883 | +0.0574 | 2/2 | +2.3 |
| E114 (t07) | -0.2034 (0.0741) | +0.0507 (0.1559) | **+0.8018 (0.3181)** | +0.0885 (0.0473) | +0.0601 (0.0117) | 0.2193 | 0.2789 | +0.0596 |  | +2.5 |
| E189 (g) | -0.5028 (0.1169) | +0.8348 (0.1969) | **+1.3558 (0.5153)** | -0.0369 (0.1463) | +0.0217 (0.0253) | 0.3989 | 0.4535 | +0.0546 | 2/2 | +2.6 |
| E189 (t07) | -0.7572 (0.1305) | +0.4844 (0.2014) | **+2.1100 (0.5493)** | +0.0913 (0.1122) | +0.0487 (0.0184) | 0.3557 | 0.4991 | +0.1433 |  | +3.8 |
| E87 (g) | -0.3009 (0.0912) | -1.0557 (0.3569) | **+0.1367 (0.4505)** | -0.3618 (0.0600) | +0.0051 (0.0129) | 0.2790 | 0.2803 | +0.0013 | 2/2 | +0.3 |
| E87 (t07) | -0.1458 (0.0465) | -1.0238 (0.4308) | **+0.1689 (0.5568)** | -0.2996 (0.0427) | -0.0137 (0.0071) | 0.2333 | 0.2354 | +0.0020 |  | +0.3 |

### continuous freshness coding

| expert | register | fresh | register×fresh | pos_frac | turn_c | R² main | R² +int | ΔR² | int sign consistency | int t (CR1) |
|---|---|---|---|---|---|---|---|---|---|---|
| E114 (g) | +1.0099 (0.2023) | +0.1069 (0.0350) | **+0.1540 (0.0471)** | +0.3700 (0.0693) | +0.0665 (0.0081) | 0.3263 | 0.3617 | +0.0354 | 2/2 | +3.3 |
| E114 (t07) | +0.7326 (0.1705) | +0.0398 (0.0280) | **+0.1895 (0.0384)** | +0.1401 (0.0501) | +0.0662 (0.0113) | 0.2623 | 0.3291 | +0.0668 |  | +4.9 |
| E189 (g) | +1.0979 (0.2249) | +0.2885 (0.0530) | **+0.2765 (0.0520)** | +0.0960 (0.1718) | +0.0429 (0.0279) | 0.5091 | 0.5464 | +0.0373 | 2/2 | +5.3 |
| E189 (t07) | +1.6681 (0.2678) | +0.1428 (0.0358) | **+0.4902 (0.0572)** | +0.1911 (0.1195) | +0.0600 (0.0199) | 0.4074 | 0.5626 | +0.1552 |  | +8.6 |
| E87 (g) | -0.0504 (0.2588) | -0.3637 (0.0558) | **+0.1169 (0.0637)** | -0.4307 (0.0664) | -0.0108 (0.0093) | 0.3660 | 0.3813 | +0.0153 | 2/2 | +1.8 |
| E87 (t07) | +0.0501 (0.3407) | -0.2862 (0.0580) | **+0.0396 (0.0692)** | -0.3926 (0.0485) | -0.0246 (0.0055) | 0.3439 | 0.3462 | +0.0023 |  | +0.6 |

### Secondary: 6-register fixed-effects variant (binary coding), register×fresh interactions

| expert | sampler | REG×fresh | LEGAL×fresh | NARR×fresh | POET×fresh | CODE×fresh |
|---|---|---|---|---|---|---|
| E114 | g | +0.801 | -0.218 | -0.247 | +0.348 | -0.357 |
| E114 | t07 | +0.802 | -0.199 | +0.089 | +0.335 | -0.229 |
| E189 | g | +1.348 | -0.326 | -0.628 | -0.588 | +0.463 |
| E189 | t07 | +2.110 | +0.187 | -0.010 | -0.055 | +0.899 |
| E87 | g | +0.128 | +1.508 | +0.406 | +0.440 | +0.830 |
| E87 | t07 | +0.169 | +1.510 | +0.227 | +0.406 | +0.829 |

## 2×2 cell means (binary coding, greedy cells)

| surface | expert | register/fresh | register/copied | control/fresh | control/copied | interaction (diff-in-diff) |
|---|---|---|---|---|---|---|
| convdyn | E114 | -4.850 (n=1857) | -6.381 (n=5043) | -5.551 (n=7182) | -6.064 (n=226) | +1.018 |
| convdyn | E189 | -4.749 (n=1857) | -6.957 (n=5043) | -6.082 (n=7182) | -6.132 (n=226) | +2.158 |
| convdyn | E87 | -5.934 (n=1857) | -4.845 (n=5043) | -5.716 (n=7182) | -4.855 (n=226) | -0.228 |
| w2 | E114 | -5.158 (n=271) | -5.832 (n=2249) | -6.058 (n=271) | -5.916 (n=286) | +0.816 |
| w2 | E189 | -4.882 (n=271) | -6.978 (n=2249) | -5.736 (n=271) | -6.479 (n=286) | +1.353 |
| w2 | E87 | -5.677 (n=271) | -4.800 (n=2249) | -5.524 (n=271) | -4.537 (n=286) | +0.109 |

(W2 t07 cell means are in results.json under `cell_means_binary_t07`.)

Cell-count caveat: the 2×2 is strongly unbalanced by design — copying dominates the
register arms late (convdyn A: 73% copied; W2 REG: 89% copied) while convdyn B has only
226 copied tokens (3%); W2 TECH copies heavily too (286/557, register-general copy regime).
Cell means are token means; SE bars are capture-level.

## Verdicts (descriptive)

**1. Does the interaction term carry (E114)?** convdyn binary β = +0.986 (t=+10.0, sign 3/3 orderings, ΔR² = +0.0228); W2 greedy β = +0.794 (t=+2.3), t07 β = +0.802, sampler sign 2/2, ΔR²(g) = +0.0574.

**2. E189 vs E114 interaction strength (binary coding):**

- convdyn: raw β_int E189 +2.101 vs E114 +0.986 (E189 stronger raw: True); standardized (β_int / SD of the expert's logit) E189 +2.101 vs E114 +1.318 (E189 stronger std: True).
- W2 greedy: raw β_int E189 +1.356 vs E114 +0.794 (E189 stronger raw: True); standardized (β_int / SD of the expert's logit) E189 +1.381 vs E114 +1.416 (E189 stronger std: False).
- W2 t07: raw β_int E189 +2.110 vs E114 +0.802 (E189 stronger raw: True); standardized (β_int / SD of the expert's logit) E189 +2.444 vs E114 +1.577 (E189 stronger std: True).

**3. Does E87 invert?** Two channels:

- convdyn: interaction β E87 -0.228 vs E114 +0.986 → interaction INVERTED; fresh main effect E87 -0.735 (t=-5.1) vs E114 +0.475 → main effect INVERTED (rises on copy).
- w2_g: interaction β E87 +0.137 vs E114 +0.794 → interaction NOT inverted; fresh main effect E87 -1.056 (t=-3.0) vs E114 +0.189 → main effect INVERTED (rises on copy).
- w2_t07: interaction β E87 +0.169 vs E114 +0.802 → interaction NOT inverted; fresh main effect E87 -1.024 (t=-2.4) vs E114 +0.051 → main effect INVERTED (rises on copy).

Reading: E87's copy response is register-GENERAL — it lives in the fresh main effect
(negative on both surfaces: it rises on copied tokens in register and control arms alike),
while its register×fresh interaction is near zero (weakly negative on convdyn only).
E114/E189's freshness response is register-CONDITIONAL (the interaction carries it).

---

Figure: `fig.png` (2×2 cell means, binary coding, greedy cells, capture-level SE bars).
All numbers descriptive; token-level observations are autocorrelated within captures —
CR1 SEs cluster on capture, but no preregistered decision rule attaches to these fits.
