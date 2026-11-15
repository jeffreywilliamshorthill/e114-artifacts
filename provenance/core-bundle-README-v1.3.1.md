# E114 — Artifact Bundle

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20709736.svg)](https://doi.org/10.5281/zenodo.20709736)

Durable artifacts for the paper *"Composition-Sensitive Register Readouts in
Mixture-of-Experts Routing: A Protocol, with a Case Study in Qwen3.5-35B"*
(versions before 1.3.1 carry the earlier title *"A Single-Expert Readout of a
Reflective Worldview Register in a Mixture-of-Experts Language Model"*).

**DOI:** [10.5281/zenodo.20709736](https://doi.org/10.5281/zenodo.20709736) (concept DOI — resolves to the latest deposited version). This release is **v1.3.1**.

This is the **paper-scoped** bundle: only the Qwen3.5-35B-A3B (and 122B transfer)
runs behind the paper's claims. Legacy DeepSeek / Ling / GPT-OSS material is *not*
included.

## What's new in v1.3.1
This release retitles the work around the protocol object (composition-sensitive
register readouts) and reports every preregistered outcome with its frozen
verdict, including the nulls. New material, each with frozen
preregistrations/specs, inputs, analysis code, and scored results:

- **All-position specificity sweep** (`sweep6c/`): every one of the 256×40
  expert–layer gate axes recovered and ranked on three surfaces (base,
  HauhauCS, AgentWorld). E114@L14 ranks 21/14/515; E189 outranks it at L14+L26
  on all three; full per-surface ranking JSONs included.
- **Onset-aligned lead–lag replication** (`convdyn/leadlag_replication/`):
  across 55 copy-run onsets the gate crossing typically *follows* copy onset
  (median −8 tokens, leading in 11%), reversing the earlier single-trajectory
  ordering claim.
- **Six-register generality battery** and **dose–response titration** with its
  preregistered null (`fleet/results_W2.*`, `fleet/results_W5.*`,
  `fleet/pulled/A1_W2`, `fleet/pulled/A1_W5`, `fleet/interaction_model/`).
- **Vantage-ladder axis adjudication** (`adjudication_s4/`): locked blind
  ratings, frozen regression — worldview content carries the ladder
  (β=+0.51); the intensity label and the construction-load reading are retired.
- **E189/E114 blind auto-interpreter panel** (`fleet/W6_results/`,
  `fleet/W6_windows/`, `fleet/pulled/A1_W6`): E189 separates without carrying
  the register label.
- **Ladder seed-variance** (`fleet/pulled/D_W1`) and **transformation-depth**
  (`fleet/pulled/D_W4`) batteries: fine rung ordering is within sampling noise;
  copy-vs-compose is a threshold, not a dial.
- **Three-arm held-out re-capture** (`fleet/pulled/D_W3`): d=3.38 greedy,
  fully separated, temperature-stable — closes the original provenance gap.
- **300-prompt four-author scaled bank** (`fleet/W7bank_*`,
  `fleet/pulled/D_W7`): preregistration, keymap, per-block and worldview-clean
  results; a diagnostic aggregate null (pooled d=1.42) with strong separation
  on worldview-clean labels (human d=3.0, natural d=2.5; E114 top-ranked at
  both its layers on the clean subset).
- **Qwen3.6-35B index-stability capture** (`fleet/pulled/D_repl36`): E114
  recovers at the same indices in the successor generation (d=4.32 at L14,
  rank 35/10,240); index locality is architecture-family-level.

## What's new in v1.3.0
Added the conversational-dynamics section and its artifacts: the fourteen-turn
grid (prereg v1.5), the token-level copy mechanism, the convdyn-T temperature
battery (prereg v1.2; paraphrase causal test), and the Berg/Dadfar
related-work positioning. (The v1.3.0 zip shipped with a stale README header;
this file is authoritative from v1.3.1.)

## What's new in v1.2.5
This release supersedes v1.2.4 with the same paper/data content and release-prefixed
zip filenames so the standalone manuscript PDF is the default Zenodo page preview.

## What's new in v1.2.4
This release corrects the framing of the coherent-window ladder: the ladder uses
target-directed vantages over rock, river, tree, thermostat, cat, person,
all-holding, and God, while model-directed prompts serve the discovery and
dissociation stages. It also adds the AI-hidden-state follow-up rung, its compact
provenance bundle, and the regenerated ladder figure.

## What's new in v1.2.3
This release removes contrastive abstract prose from the paper framing while
preserving the v1.2.2 title and named official Zenodo metadata.

## Named release from v1.2.1
The paper and citation metadata identify the author as Jeffrey W. Shorthill, with
contact email `jws299792@icloud.com`.

## Sanitized sharing copy
The refreshed standalone anonymous DOI,
[`10.5281/zenodo.21042938`](https://doi.org/10.5281/zenodo.21042938), mirrors
the v1.2.3 title and framing while using `Anonymous` in the paper and metadata
and excluding the short manuscript. The v1.2.2 anonymous DOI,
[`10.5281/zenodo.21042440`](https://doi.org/10.5281/zenodo.21042440), and the older v1.2.0 sanitized DOI,
[`10.5281/zenodo.21040909`](https://doi.org/10.5281/zenodo.21040909), remains
available as legacy direct versions.

## Framing lineage from v1.2.0
Version 1.2.0 moved the paper away from a self-referential-register label. This
release names the broader target a **reflective worldview register**: a stance
toward meaning, belief, value, existence, or a target's interiority. In the
current framing, model-directed prompts locate and dissociate the signal, and the
coherent-window ladder tests target-directed vantages over rock, river, tree,
thermostat, cat, person, all-holding, and God.

## Technical additions from v1.1.0
Three results were added to the paper and the bundle in v1.1.0 (the
v1.0.0/1.0.1 claims are unchanged; these strengthen two of the paper's own
acknowledged gaps):
- **Bottom-up auto-interp** (`runs/35b/qwen3.5-35b-a3b-114-autointerp/`) — a blind
  two-stage labeler reproduces E114's register at AUC 0.937 and broadens it to an
  reflective worldview axis, with abstract examination/philosophical-worldview
  language as supporting description; cross-model Jaccard 0.92. Closes the "labels
  were author-assigned" gap.
- **All-expert npz profile** (`runs/35b/qwen3.5-35b-a3b-huahua-expert-identification/DOCS/RESULTS_e114_npz_characterization.md`)
  — E114's dual L14/L26 readout (same axis, r = +0.99) and 20-domain selectivity
  across all 256 experts; E87 anti-correlates with the prior four-expert
  "philosophy cluster" framing. Partially closes the cross-expert
  specificity gap.
- **Controlled causal gate-bias run** (`runs/35b/qwen3.5-35b-a3b-huahua-114-causal-gate-bias/`)
  — a necessity-direction probe: lowering E114's gate keeps the blind-rated
  register near baseline (a matched control mimics the small nudge), while forcing
  it open flips only directly experiential prompts. Gate-forcing is prompt-gated
  as a conditional effect (n = 1 greedy/cell; stochastic follow-up pending).

## Policy
Per the project's standing rule, **raw activation tensors (`.npy`) are kept out of
git.** The durable artifacts here are per-run results (JSON/CSV/TSV), analysis
scripts, prompt/class manifests, plots, checksums, and the journals. The raw tensors
(~18 GB) are archived separately as a Zenodo dataset — see `ZENODO-TENSORS.md`.

## Layout
```
paper/      the manuscript (LaTeX source, figures, compiled PDF)
journals/   primary-source experiment journals + the master synthesis (NOTES.md)
runs/35b/   curated Qwen3.5-35B-A3B run results (tensor-free); includes the v1.1.0
            additions: 114-autointerp (bottom-up label) and
            114-causal-gate-bias (Phase-1 controlled causal test)
runs/122b/  Qwen3.5-122B-A10B scope-bound runs (E114 local; E48 candidate)
runs/sae/   SAE vantage-ladder run (durable provenance + analysis)
staging/    E114 discovery bundle (probe/anchor CSVs, SAE feature map, plots)
steering/   inference-time SAE feature-steering source + MANIFEST
```

## Reproducibility pointers
- Capture binary: local llama.cpp fork with `capture_residuals` tapping
  `ffn_moe_logits-{L}` and `attn_post_norm-{L}` (the pre-router norm for `qwen35moe`).
  Greedy decode `--temp 0 --top-k 1 --seed 0`.
- SAE: public Qwen-Scope `SAE-Res-Qwen3.5-35B-A3B-Base-W32K-L0_50` (TopK-50).
- The headline statistic is the linear axis `w114` (Cohen's d = 3.88, separated ranges),
  recovered by least squares from any `(residual, logit)` capture.
- v1.1.0 additions: bottom-up auto-interp re-scorable from
  `runs/35b/qwen3.5-35b-a3b-114-autointerp/results/` via `METHOD/score_autointerp.py`;
  the npz domain profile reproducible via
  `runs/35b/qwen3.5-35b-a3b-huahua-expert-identification/METHOD/analyze_e114_npz.py`;
  the Phase-1 causal tables via
  `runs/35b/qwen3.5-35b-a3b-huahua-114-causal-gate-bias/METHOD/analyze_p1.py`.

## Citation
Cite the named release via the **concept DOI** [10.5281/zenodo.20709736](https://doi.org/10.5281/zenodo.20709736)
(resolves to the latest deposited named version). Per-version DOIs: v1.2.5 =
[`10.5281/zenodo.21048828`](https://doi.org/10.5281/zenodo.21048828);
v1.2.4 =
[`10.5281/zenodo.21048676`](https://doi.org/10.5281/zenodo.21048676);
v1.2.3 =
[`10.5281/zenodo.21042937`](https://doi.org/10.5281/zenodo.21042937);
v1.2.3 anonymous sharing copy =
[`10.5281/zenodo.21042938`](https://doi.org/10.5281/zenodo.21042938);
v1.2.2 =
[`10.5281/zenodo.21041914`](https://doi.org/10.5281/zenodo.21041914);
v1.2.2 anonymous sharing copy =
[`10.5281/zenodo.21042440`](https://doi.org/10.5281/zenodo.21042440);
v1.2.1 =
[`10.5281/zenodo.21041653`](https://doi.org/10.5281/zenodo.21041653);
v1.2.0 legacy sanitized copy =
[`10.5281/zenodo.21040909`](https://doi.org/10.5281/zenodo.21040909);
v1.1.0 = [`10.5281/zenodo.21015922`](https://doi.org/10.5281/zenodo.21015922);
v1.0.1 = `10.5281/zenodo.20785773`. See `CITATION.cff` for the full record.

## License
MIT (see `LICENSE`).
