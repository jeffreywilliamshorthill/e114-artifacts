# Conversational dynamics — results (prereg v1.5, sha 4356e500…)

## Contrast table (slopes vs turn index, A−B primary)

| feature | A−B slope (mean) | per-ord signs | C−B slope | vocab-driven? |
|---|---|---|---|---|
| peak | -0.0174 | 2/3 (weak) | +0.0142 | YES |
| floor_a | -0.0753 | 3/3 (strong) | +0.0155 | no |
| floor_b | -0.0121 | 2/3 (weak) | -0.0087 | YES |
| var | -0.0196 | 2/3 (weak) | +0.0030 | no |
| skew | +0.1576 | 3/3 (strong) | +0.0140 | no |
| auc | -15.6869 | 3/3 (strong) | +2.2885 | no |

## History swap

| k | ord1 | ord2 | ord3 | mean |
|---|---|---|---|---|
| 4 | -0.660 | -0.139 | -0.375 | -0.391 |
| 8 | -1.112 | -0.435 | -0.028 | -0.525 |
| 12 | -0.652 | -0.402 | +0.122 | -0.311 |

PRIMARY: Delta_8 = -0.525, positive in 0/3 orderings -> not supported

## Predictions

- **P-habituation**: not supported
- **P-accumulation**: not supported
- **P-spikes-to-swells**: not supported
- **P-knee**: not supported
- **P-null**: not supported

## Knee
- ACCEPTED at c=4 (BIC 2-seg -26.24 vs 1-seg -10.48; frozen penalty (5-3)ln14=5.28); peak/floor convergence: False

## Caveats (inline)
- flags: {"A_o1": ["t3:CAP_HIT", "t6:CAP_HIT"], "A_o2": ["t1:CAP_HIT", "t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "A_o3": ["t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "B_o1": ["t2:CAP_HIT", "t3:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "B_o2": ["t1:CAP_HIT", "t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "B_o3": ["t1:CAP_HIT", "t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "C_o1": ["t1:CAP_HIT", "t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "C_o2": ["t1:CAP_HIT", "t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"], "C_o3": ["t1:CAP_HIT", "t2:CAP_HIT", "t3:CAP_HIT", "t4:CAP_HIT", "t5:CAP_HIT", "t6:CAP_HIT", "t7:CAP_HIT", "t8:CAP_HIT", "t9:CAP_HIT", "t10:CAP_HIT", "t11:CAP_HIT", "t12:CAP_HIT", "t13:CAP_HIT", "t14:CAP_HIT"]}
- decay taus reported per turn in features (sparse where post-peak < 16 tokens); see npz for raw series
- KV cache f16 (llama.cpp default) = prior validated surface; brief's bf16 pin amended in prereg
- n=3 orderings: direction claims use sign consistency, no parametric p-values
