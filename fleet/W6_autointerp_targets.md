# W6 — blind auto-interp targets (box A1, first job; no new prereg needed — pipeline reuse)

Run the E114 auto-interp recipe verbatim (capture routing over ~390 raw Pile docs on the
base model, rank top-activating contexts, blind explainer on windows only, fresh blind
detector on shuffled top + random contrasts, report AUC / precision@40 / Spearman) for
each target:

| target | why |
|---|---|
| E87 @ L14 | copy-coalition top riser (convdyn d=+2.19; convdyn-T T5 d=+2.28); documented E114 anti-correlate — is its natural label quotation/verbatim continuation? |
| E87 @ L26 | dual-layer twin of the above (riser rank 5) |
| E34 @ L14 | cross-layer coalition riser (L13/L14/L26); §6c finds it anti-register at L14 (d −2.3..−3.7) |
| E189 @ L14 | **§6c rival**: outranks E114 at L14+L26 on all 3 surfaces (6/6); was the routing-matched control in the gate-bias run. Most-wanted label: same register? sharper? different construct? |
| E189 @ L26 | dual-layer twin of the rival |

One Pile capture pass serves all five targets (per-expert rankings from the same
all-layer routing tensors — capture once, rank five columns). Judges for explainer/
detector: non-Qwen, different vendors (same discipline as §4).

Output: fleet/W6_results/ with per-target AUC table + labels; compare E189's label and
top-document Jaccard against E114's published ones (AUC 0.937, contemplative/worldview).
