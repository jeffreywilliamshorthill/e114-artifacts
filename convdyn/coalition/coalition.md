# Copy-coalition contrast (arm A, convdyn grid; post-hoc)

tokens: 6900 (copy 5043 / compose 1857); late-only scope: copy 4382 / compose 629
d = Cohen's d of router logit, COPY minus COMPOSE. Positive = rises when copying.

## all_turns

### L13 — max|d| 2.40, experts |d|>1: 110
- E114: d=+0.437, riser-rank 88/256, z=+0.52
- E87:  d=-1.556, riser-rank 224/256
- top risers: E34(+2.35), E233(+2.18), E218(+2.15), E128(+1.99), E80(+1.98), E246(+1.89)
- top fallers: E92(-2.40), E81(-2.26), E18(-2.23), E175(-2.19), E228(-2.18), E113(-2.17)

### L14 — max|d| 2.78, experts |d|>1: 139
- E114: d=-2.434, riser-rank 238/256, z=-1.54
- E87:  d=+2.190, riser-rank 3/256
- top risers: E34(+2.49), E113(+2.49), E87(+2.19), E233(+2.02), E151(+1.99), E211(+1.92)
- top fallers: E37(-2.78), E75(-2.78), E14(-2.71), E169(-2.69), E218(-2.69), E156(-2.67)

### L15 — max|d| 2.71, experts |d|>1: 149
- E114: d=-0.255, riser-rank 116/256, z=+0.10
- E87:  d=-1.647, riser-rank 201/256
- top risers: E164(+2.71), E196(+2.34), E107(+2.28), E205(+2.24), E253(+2.22), E246(+2.12)
- top fallers: E192(-2.69), E71(-2.68), E110(-2.61), E250(-2.60), E142(-2.58), E113(-2.56)

### L26 — max|d| 2.90, experts |d|>1: 154
- E114: d=-2.448, riser-rank 230/256, z=-1.35
- E87:  d=+2.096, riser-rank 5/256
- top risers: E217(+2.38), E219(+2.21), E34(+2.20), E248(+2.11), E87(+2.10), E122(+2.06)
- top fallers: E37(-2.90), E11(-2.88), E156(-2.86), E169(-2.84), E75(-2.82), E220(-2.78)

## late_only (t5-14)

### L13 — max|d| 2.45, experts |d|>1: 102
- E114: d=+0.319, riser-rank 85/256, z=+0.51
- E87:  d=-1.889, riser-rank 241/256
- top risers: E34(+2.40), E218(+1.99), E80(+1.86), E233(+1.84), E128(+1.84), E205(+1.80)
- top fallers: E18(-2.45), E160(-2.39), E81(-2.35), E92(-2.26), E113(-2.25), E48(-2.12)

### L14 — max|d| 2.63, experts |d|>1: 130
- E114: d=-2.157, riser-rank 232/256, z=-1.46
- E87:  d=+1.640, riser-rank 5/256
- top risers: E113(+2.18), E34(+2.04), E70(+1.81), E248(+1.71), E87(+1.64), E78(+1.60)
- top fallers: E75(-2.63), E61(-2.60), E37(-2.59), E169(-2.58), E218(-2.54), E14(-2.49)

### L15 — max|d| 2.63, experts |d|>1: 137
- E114: d=-0.078, riser-rank 102/256, z=+0.28
- E87:  d=-1.817, riser-rank 219/256
- top risers: E164(+2.41), E196(+2.02), E107(+2.00), E205(+1.98), E139(+1.93), E111(+1.89)
- top fallers: E110(-2.63), E71(-2.51), E192(-2.51), E88(-2.51), E250(-2.41), E113(-2.41)

### L26 — max|d| 2.71, experts |d|>1: 133
- E114: d=-2.126, riser-rank 226/256, z=-1.27
- E87:  d=+1.551, riser-rank 5/256
- top risers: E217(+1.96), E219(+1.96), E248(+1.78), E212(+1.75), E87(+1.55), E70(+1.53)
- top fallers: E220(-2.71), E37(-2.70), E169(-2.64), E75(-2.62), E156(-2.62), E11(-2.54)

## Selection level (L14, E114 in top-8)
- P(selected | compose) = 0.388 · P(selected | copied) = 0.023

Read: 'coalition' = experts with large POSITIVE d (rise during copying). E114 expected among
top fallers. Generic-shift control: if E114's z is modest (|z|<2), its drop is part of a
broad routing shift, not a targeted anti-alignment; if |z|>3 it is an outlier. Late-only
scope controls the turn confound. NOT preregistered; candidates named here get frozen
predictions in the convdyn-T prereg.
