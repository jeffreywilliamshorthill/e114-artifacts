# E114 — Composition-Sensitive Register Readouts

Artifacts for **Composition-Sensitive Register Readouts in Mixture-of-Experts Routing: A Protocol, with a Case Study in Qwen3.5-35B**, by Jeffrey William Shorthill.

**Version 1.4.0 · July 6, 2026**

- [Read the paper](paper/e114_acl_style.pdf)
- [LaTeX source](paper/e114_acl_style.tex)
- [Canonical Zenodo record](https://zenodo.org/records/21213596) · [version DOI](https://doi.org/10.5281/zenodo.21213596) · [all versions](https://doi.org/10.5281/zenodo.20709736)
- [Citation metadata](CITATION.cff)

## Status of this record

The [Zenodo status update dated October 21, 2026](https://zenodo.org/records/21213596) identifies this as the June–July 2026 program compendium: a dated lab record whose interpretations developed during the work. Later checks narrowed three readings:

- Expert 114 belongs to a family of genre-selective experts at layer 14. October genre controls found larger, disjoint families for recipe and travel prose.
- Layer 26 in this checkpoint is a trained copy of layer 14, so the dual-layer signal represents one readout observed twice. See the [repeated-block scan](https://doi.org/10.5281/zenodo.23546828).
- The program's llama.cpp captures encoded chat markers as literal text (`parse_special=false`). The readout also replicates under that encoding.

The later [self-copy / availability paper](https://doi.org/10.5281/zenodo.21892999) cites this record's July 6 prediction about E114 disengagement during literal reuse and its v1.4.0 model-wide L14/L26 index-correspondence note. The original paper and experiment records are retained here with this status context.

## Contents and provenance

This repository preserves the history of the [original E114 artifact repository](https://github.com/jeffreywilliamportfolio/e114-artifacts) and assembles the files deposited in Zenodo record `21213596`:

| Component | Deposited source | Repository location |
|---|---|---|
| v1.4.0 manuscript | `e114_acl_style.pdf` and `e114_acl_style.tex` | [`paper/`](paper/) |
| Core durable artifacts | `release_artifacts-e114-v1.3.1.zip` | Original bundle layout at repository root |
| Translation robustness | `release_translation-robustness-v1.4.0.zip` | [`translation_robustness/`](translation_robustness/) |
| Induction protocol | `release_induction-protocol-v1.4.0.zip` | [`induction_protocol/`](induction_protocol/) |
| Figure-backing tensors | `release_data-e114-figure-tensors-v1.2.5.zip` | [Download from Zenodo](https://zenodo.org/records/21213596) |

The core bundle retains the paper-scoped run summaries, analysis scripts, prompt and class manifests, preregistrations, checksums, plots, and source journals. The two v1.4.0 directories add the translation-robustness and induction-protocol materials. The v1.4.0 paper also adds the model-wide L14/L26 correspondence bound and an Ethics Statement.

Raw activation tensors remain outside Git. The figure-backing archive is approximately 1.12 GB and is available with the paper on Zenodo. Follow the experiment-specific manifests and scripts for reproduction; the retained results include the preregistered null outcomes.

The deposited derived axis `adjudication_s4/w114.npy` also remains in the core Zenodo ZIP under the inherited `.npy` exclusion policy; its path and SHA-256 are recorded in the [import manifest](provenance/import-manifest.json).

Earlier versions of the documentation remain available in Git history. The [deposited core README](provenance/core-bundle-README-v1.3.1.md) preserves the v1.3.1 bundle documentation. The [Zenodo record snapshot](provenance/zenodo-record-21213596.json) and [source checksums](provenance/source-checksums.json) record the deposited sources for this copy.

## Citation and license

Use the [v1.4.0 DOI](https://doi.org/10.5281/zenodo.21213596) to identify this deposited version. The [concept DOI](https://doi.org/10.5281/zenodo.20709736) identifies the version family. Author, title, release date, and DOI metadata are available in [CITATION.cff](CITATION.cff).

MIT — see [LICENSE](LICENSE).
