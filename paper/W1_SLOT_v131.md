# [W1-LADDER-VARIANCE] slot fill — data landed 2026-07-03 (box D)

Source: fleet/pulled/D_W1/W1_ladder_variance.json; prereg v1.0 SHA 08f7b804…; w1.tgz sha 596f885e…
Metric: raw router logit E114@L14 (== w114 projection, r=1.0), mean over trimmed generated track,
per rung, greedy + 10 temp-0.7 seeds. FINDING: greedy ladder reproduces but is largely
seed-noise; only coarse abstract>concrete + the God rung survive replication.

## §4.5 ladder ¶ — replace `[W1-LADDER-VARIANCE]` marker

```latex
Seed replication attaches variance to these previously single-generation points
(prereg v1.0, SHA-256 \texttt{08f7b804\ldots}: nine rungs under greedy plus ten
temperature-$0.7$ seeds; metric the raw E114@L14 logit, which equals the
recovered-axis projection). The greedy ordering reproduces (holding and
abstract vantages high, concrete objects low), but it is largely within
sampling noise: the per-rung seed SD ($\sim$0.30 logit) is roughly a third of
the full range across rung means ($\sim$0.8 logit), adjacent rungs overlap, and
the greedy and seed-mean orderings agree at only Spearman $0.50$. Only the
coarse contrast survives replication: the holding/abstract group sits about one
SD above the concrete group, and the God rung is the single rung cleanly
separated from concrete objects. The fine-grained rung ordering is not
resolvable at this sample size.
```

## Limitations (iii) — replace `ladder variance is pending [W1-LADDER-VARIANCE].`

```latex
seed replication of the ladder (ten temperature-$0.7$ seeds per rung) shows the
fine-grained rung ordering is largely within sampling noise (per-rung SD
$\sim$0.30 logit against a $\sim$0.8 logit range; greedy-versus-seed-mean
ordering Spearman $0.50$), with only the coarse abstract-over-concrete contrast
and the God rung surviving replication.
```

## E18 Conclusion slot list — change `ladder variance [W1-LADDER-VARIANCE],` to (drop it; now reported)
Remove the W1 item from the open-steps sentence.
