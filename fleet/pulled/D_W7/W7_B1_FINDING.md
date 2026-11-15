# W7bank B1 — the diagnostic null (2026-07-03)

Preregistered B1 (d>=2.0, <=5% overlap): NOT MET on full 300-prompt bank.
- ALL: d=1.42, overlap 94% (win128 d=1.42; full-track d=1.37 — window not the cause)
- Per block: A(Claude) d=1.38 · B(Gemini) d=1.75 · C(natural) d=2.50 · D(human/Jeffrey) d=2.98
- Disjoint-authorship headline BCD_noA: d=1.72. Direction correct everywhere (no label flip).

## Why (diagnostic, re-confirms §4 blind at scale)
Block-A FIRE that stayed DARK are first-person OBJECT-VANTAGE / construction prompts:
  A_F_049 "chess engine that knows it is lost" E114 -5.58
  A_F_045 "subway car packed with strangers at dawn" -5.54
  A_F_075 "lone turbine on a windswept ridge" -5.43
Block-A NOFIRE that LIT UP are third-person WORLDVIEW/PHILOSOPHY prompts:
  A_N_084 "realism vs anti-realism about a domain" -3.67
  A_N_098 "philosophy of mathematics: logicism/formalism/intuitionism" -3.73
  A_N_088 "substance, property, relation in metaphysics" -3.91

=> E114 tracks WORLDVIEW CONTENT, not first-person construction/vantage — the §4 regression
result (construction REJECTED, worldview carries) reproducing on a blind 300-prompt bank.
Block A was inadvertently labeled on the construction/vantage axis (the rejected one), so its
FIRE/NOFIRE split is near-orthogonal to (even mildly anti-aligned with) the true axis => low d.
Where labels track worldview (D human, C natural), d=2.5-3.0.

## Paper implication
Report B1 honestly as a threshold MISS on the full bank, reframed as independent confirmation
of the worldview-content axis. The clean d~3.9 is specific to worldview-laden matched prompts.
Confirming follow-up (needs judges): re-score the 300 by worldview-content rating and regress —
predict d recovers on the worldview-split. Qualitative tail pattern already strong.
