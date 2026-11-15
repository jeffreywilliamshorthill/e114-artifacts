# Resolved-slot integration spec — apply AFTER the mechanical packet pass

Three slots the packet left as `[MARKERS]` are now resolved. Each entry: the marker/clause to
replace (re-verify anchor against the post-packet tex), and the exact drafted LaTeX. Numbers are
verbatim from the frozen result files. Voice rules of the packet (§0) apply.

Sources of record:
- SEC4: `e114-construction-reframe/legs/s4_regression.{json,md}`, run_utc 2026-07-03T18:13:59Z;
  ratings SHA `7dc963d3…`, freeze `bcccc6fe…`. Primary n=29, R²=0.663.
- W6: `e114-construction-reframe/fleet/W6_results/*_panel.json`, panel v2, total $3.47.
- INTERACTION: `e114-construction-reframe/fleet/interaction_model/results.json` (post-hoc, NOT preregistered).

---

## SLOT A — [SEC4-AXIS-REGRESSION]

### A1. §4.5 body (replace the literal `[SEC4-AXIS-REGRESSION]` marker with this paragraph)

```latex
\paragraph{The ladder axis is content, not intensity or construction.}
A preregistered adjudication (frozen regression against locked judge ratings,
ratings SHA-256 \texttt{7dc963d3\ldots}, freeze \texttt{bcccc6fe\ldots})
regressed the recovered-axis projection over the vantage-ladder targets on
three rated predictors, construction load, examination intensity, and
worldview content, with output entropy as a covariate ($n{=}29$ after the
frozen degeneration screen; $R^2{=}0.66$). Worldview content is the only
predictor with a positive partial contribution ($\beta{=}{+}0.51$,
$p{=}0.053$; $+0.58$, $p{=}0.003$ under a routing-entropy covariate). The
``intensity'' label carries nothing once content is partialled
($\beta{=}{+}0.20$, $p{=}0.28$), and the construction-load reading is rejected
in the ladder setting: its partial coefficient is significantly negative,
opposite the preregistered direction, in every screened specification
($\beta{=}{-}0.33$, $p{=}0.047$; $-0.48$, $p{=}0.001$ on the interior-only
proxy). The clean dissociator target fires the content pattern, and
third-person worldview probes separate by $\sim$2 logits at rated
intensity~1.0. We retire ``intensity'' as the ladder's axis label and keep the
worldview-content framing. This construction-load axis is distinct from the
composition axis of \S\ref{sec:convdyn}: construction load is a cross-target
property of the ladder (how much unattested interior a target requires),
composition is a within-dialogue production mode (fresh generation versus
literal reuse); the ladder result concerns the former.
```

### A2. Limitations (vi) — replace the packet's drafted (vi) item

Anchor: the sentence beginning `(vi)~A separate preregistered adjudication of the vantage-ladder axis`.
Replace the whole (vi) item with:

```latex
(vi)~The preregistered adjudication of the vantage-ladder axis has run
(\S\ref{sec:case}): regressing the $\wvec$ projection on rated construction,
intensity, and worldview content ($n{=}29$ screened) retires the ``intensity''
label (partial $\beta{=}{+}0.20$, $p{=}0.28$) and rejects the
construction-load reading of the ladder (partial $\beta{=}{-}0.33$,
$p{=}0.047$, negative), leaving worldview content as the surviving axis. The
ladder's construction-load axis and the conversational arm's composition axis
are distinct constructs; the regression concerns the ladder, the composition
result (\S\ref{sec:convdyn}) concerns within-dialogue production mode.
```

Also update E18 Conclusion: the slot list line `the vantage-axis regression [SEC4-AXIS-REGRESSION],`
— delete that item from the "open protocol steps are slotted" sentence (it is no longer open).

---

## SLOT B — [W6-E189-LABEL]

### B1. §4.3 end (replace the literal `[W6-E189-LABEL]` marker; keep `[W3-FRESH-SEPARABILITY]`)

```latex
A blind auto-interpreter panel (four explainers, a fixed blind detector, frozen
declaration; total \$3.47) answers whether E189 carries E114's register label:
it does not. E189@L14's highest-scoring blind label is a lexical shortcut, the
presence of the substring ``ro'' (detector AUC~$0.963$), not a register
description; its L26 label is generic technical text (AUC~$0.70$). E114@L14's
best label, ``contrasting or complementary concept pairs'' (AUC~$0.63$), is
weak at the window level, the expected surface-bias failure for a semantic
register whose top-activating windows (sermons, mystics, dialectics) read as
ordinary web text to a windows-only explainer. E189 is thus a strong
\emph{separator} without a matching blind \emph{label}: the family shares the
L14/L26 stance-separation geometry, and the reflective-register semantics
attach to E114, not to its higher-ranked neighbor.
```

### B2. Discussion family ¶ (E17) — replace the pending clause

Anchor: `Its blind label is pending [W6-E189-LABEL].`
Replace with:

```latex
Its blind label, however, is a lexical shortcut (the substring ``ro'', detector
AUC~$0.963$) rather than a register description, so E189 separates without
carrying the register semantics.
```

Also update E18 Conclusion slot list: delete `the E189 blind label [W6-E189-LABEL],` from the
open-steps sentence.

---

## SLOT C — [INTERACTION-MODEL]

### C1. §4.6 W5 ¶ (E11) — replace the literal `[INTERACTION-MODEL]` marker

```latex
A post-hoc descriptive model (not preregistered; the L14 gate logit on
register${}\times{}$freshness with position and turn covariates, cluster-robust
SEs) localizes the effect to the interaction: E114's register${}\times{}$fresh
term is $+0.99$ ($t{=}10.0$, sign-consistent 3/3 orderings) on the dynamics
grid and $+0.79$/$+0.80$ across the two multi-register samplers (2/2), so the
meter falls under copying specifically when the copied register is its own.
E189 carries a $2.1\times$ stronger interaction, and E87 inverts the freshness
main effect (slope $-0.74$, $t{=}5.1$), independently reproducing its
reuse-riser role. This describes the leaky dose-to-copying link; it does not
model the copy decision.
```

### C2. Limitations (vii) — replace the trailing `[INTERACTION-MODEL]` marker

Anchor: `with the interior of the dose curve unmodeled [INTERACTION-MODEL].`
Replace with:

```latex
with the interior of the dose curve unmodeled; a post-hoc interaction model
(register${}\times{}$freshness, not preregistered) localizes the
copy-sensitivity to the in-register interaction but does not model the copy
decision itself.
```

---

## After applying A–C

- Remaining legitimate markers should be exactly: `[W1-LADDER-VARIANCE]`, `[W3-FRESH-SEPARABILITY]`,
  `[W4-TRANSFORMATION-DEPTH]`, `[REPLICATION-3.6-122B]`, and `[PENDING]` (external-labeler verdict).
- Recompile twice; confirm no new unresolved refs; confirm `\S\ref{sec:convdyn}` and
  `\S\ref{sec:case}` resolve.

---

## SLOT D — [W3-FRESH-SEPARABILITY]  (data landed 2026-07-03; box D, greedy d=3.375)

Source: `e114-construction-reframe/fleet/pulled/D_W3/extracted_W3.json`; prereg v1.1
SHA `80d9215b…`; heldout bank SHA `890d787a…`; binary `llama-capture_residuals_eog`
SHA `8095c95e…`; GGUF pin `ec55dfc4…`; w114 recovered fresh (rel-resid 1.2e-4, gate PASS).
NOTE: W3 re-captures the ORIGINAL 20-prompt held-out bank with residuals retained — it is the
provenance/replication fix. The *freshly authored* 300-prompt four-author bank is W7bank
(separate, capture pending); do NOT conflate them.

### D1. §4.3 end — replace the literal `[W3-FRESH-SEPARABILITY]` marker

```latex
A fresh three-arm re-capture of the matched held-out bank (prereg v1.1, SHA-256
\texttt{80d9215b\ldots}: the original 20 register/control prompts under greedy
decoding plus temperature $0.5$ and $0.7$ at three seeds each, residuals
retained so $\wvec$ is recovered fresh from this capture, gate rel-residual
$1.2\times10^{-4}$) reproduces the separation: greedy recovered-axis
$d{=}3.38$, the classes fully separated (0 of 100 cross-class pairs), beside the
original $d{=}3.88$ and the sweep's $+3.42$ re-estimate. The separation is
temperature-stable and sharper under sampling (pooled $d{=}4.79$ at $0.5$,
$4.84$ at $0.7$, separated, sign-consistent 3/3). This closes the provenance
gap in the original single greedy capture: the tensors are retained and the
effect replicates.
```

### D2. Limitations (ii) — replace the trailing pending clause

Anchor: `a separability estimate on a freshly authored prompt bank is pending [W3-FRESH-SEPARABILITY].`
Replace with:

```latex
a fresh three-arm re-capture of the held-out bank with retained tensors
replicates the separation ($d{=}3.38$ greedy, fully separated,
temperature-stable), and a separability estimate on a freshly authored
300-prompt four-author bank is pending [W7BANK-SCALE].
```

(Introduces a NEW slot `[W7BANK-SCALE]` for the W7bank result — that is intended; it replaces the
conflated W3/bank reference. W7bank capture is queued on box D.)

### D3. E18 Conclusion slot list — update

In the "open protocol steps are slotted" sentence, change `fresh-bank separability
[W3-FRESH-SEPARABILITY],` to `the 300-prompt-bank separability [W7BANK-SCALE],`.

### D4. Abstract E2a note (optional, only if trivially clean)

The abstract already carries the sweep numbers. Do NOT add W3 to the abstract in this pass;
it is a case-study detail. Leave the abstract as the mechanical pass left it.

---

## FINAL MARKER STATE after A–D applied

Legitimate remaining markers should be exactly:
`[W1-LADDER-VARIANCE]`, `[W4-TRANSFORMATION-DEPTH]`, `[REPLICATION-3.6-122B]`, `[W7BANK-SCALE]`,
and `[PENDING]` (external-labeler verdict, item (i)). All of `[SEC4-AXIS-REGRESSION]`,
`[W6-E189-LABEL]`, `[INTERACTION-MODEL]`, `[W3-FRESH-SEPARABILITY]` should be GONE.
