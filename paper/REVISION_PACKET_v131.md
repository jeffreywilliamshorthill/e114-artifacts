# REVISION PACKET v1.3.1 — Protocol-Spine Restructuring

**Assembled:** 2026-07-03 · **Target:** `/Volumes/ExternalSSD/journals/paper/e114_acl_style.tex`
(anchors verified against the on-disk state of 2026-07-03 08:53, i.e. AFTER the main session's
abstract rewrite — see E2)

**Organizing principle (author-approved):** reframe around a PROTOCOL spine, object class
"composition-sensitive register readouts." Empirical results stay central; this is not a
position paper.

**Sources of record (numbers quoted exactly; verdicts never upgraded):**

| result | file | key identifiers |
|---|---|---|
| §6c all-expert sweep | `e114-construction-reframe/prework/6c_results/results_6c.md` | spec sha `e35fabd0…`; E114@L14 rank 21/14/515 by \|d\| |
| lead-lag replication | `e114-construction-reframe/convdyn/leadlag_replication/leadlag_replication.md` | POST-HOC DESCRIPTIVE, NOT PREREGISTERED; n=55, median −8, 11% |
| W2 multi-register | `e114-construction-reframe/fleet/results_W2.md` / `.json` | prereg v1.1 sha `f20b7612…`; 4/4 supported |
| W5 dose-response | `e114-construction-reframe/fleet/results_W5.md` / `.json` | prereg v1.0 sha `7bfc9c4d…`; monotone NOT SUPPORTED |

**Verdict-integrity rules for every edit below:** quote the frozen wording where one exists;
"NOT SUPPORTED" stays "not supported"; "post-hoc descriptive" stays flagged; point estimates
stay flagged; the 21.68× ratio stays a footnote; realized W is never a primary statistic.

---

## 0. VOICE RULES (govern all drafted text in §2)

1. **Bare positives.** State what the data show. "The floor collapses at turn 4," not "what is
   striking is that the floor collapses."
2. **Minimal em-dashes.** Prefer colons, semicolons, parentheses, or two sentences. Em-dashes
   only where the paper's existing house style already uses them (e.g. inside verbatim-surviving
   prose); none in new drafted sentences unless unavoidable.
3. **No rhetorical negation unless load-bearing.** "Not X but Y" is allowed only where the
   negation IS the finding: "does not replicate," "not the unique summit," "not a smooth
   function of available fraction," "E87 is not in the core." Decorative negation is banned.
4. **No aphoristic closers.** No paragraph ends on a flourish, moral, or epigram. End on a
   number, a scope statement, or a pointer.
5. Numbers verbatim from the results files, at the precision printed there. Ranks by |d| unless
   stated; signed ranks noted where the file notes them.

---

## 1. RESTRUCTURING MAP — current sections → new spine

**New title (E1):** *Composition-Sensitive Register Readouts in Mixture-of-Experts Routing:
A Protocol, with a Case Study in Qwen3.5-35B*

**New top-level structure:**

| new § | title | built from |
|---|---|---|
| §1 | Introduction | rewrite (E3); opening 3 sentences survive verbatim |
| §2 | Related Work | survives verbatim except one sentence (E5) |
| §3 | A Protocol for Composition-Sensitive Register Readouts (`\label{sec:protocol}`) | NEW (E6); absorbs the methodology-rule content of current Setup ¶"Routing decomposition"/"Recovering the gate axis" in generalized form (those ¶s also survive concretely in §4.1) |
| §4 | Case Study: Depth Validation on Qwen3.5-35B (`\label{sec:case}`) | wrapper section (E6b); current §3–§7 demoted to subsections |
| §4.1 | Instantiation and measurement surface | current §3 Setup, verbatim except trim-rule clarification (E7) |
| §4.2 | Separation and label | current §4 ¶Localization + ¶Held-out separability (+ fig:sep + 21.68× footnote) + ¶Bottom-up validation, all **verbatim** |
| §4.3 | The all-position sweep: a family of L14/L26 stance separators (`\label{sec:family}`) | current §4 ¶Population-and-layer-profile (kept through "…E87 *anti*-correlates (−0.29).") + NEW §6c absorption (E8) |
| §4.4 | Dissociation from nearby explanations | current §5 + tab:battery, **verbatim** |
| §4.5 | Process dynamics and causal probes | current §6; ¶gate-leads rewritten (E9), fig:leadlag caption rewritten (E10); ¶ladder, ¶AI-hidden-state, ¶semantics/causal probe, ¶gate-bias **verbatim**; slots [W1-LADDER-VARIANCE], [SEC4-AXIS-REGRESSION] |
| §4.6 | Conversational dynamics: the readout meters composition (keeps `\label{sec:convdyn}`) | current §7 **verbatim** (incl. tab:convdynT) + NEW W5 paragraph (E11) + slot [W4-TRANSFORMATION-DEPTH] |
| §5 | Breadth: Six Registers, One Copy Regime (`\label{sec:breadth}`) | NEW from W2 (E12) |
| §6 | Transfer: Cross-Model Application (`\label{sec:transfer}`) | current §8 Scope Bound + tab:transfer **verbatim**, retitled, + placeholder ¶ (E13) |
| §7 | Discussion | current §9; ¶What-held-up rewritten (E14); ¶readout/controller first sentence rewritten (E15); ¶Composition-and-reuse one clause (E16); NEW family/coordinate ¶ (E17); ¶What-the-cross-scale-result-buys **verbatim** |
| §8 | Conclusion | full rewrite (E18) |
| §9 | Limitations | full rewrite (E19); items (i),(iv) survive near-verbatim, (v),(vi) extended, (ii) replaced, (iii) adjusted, (vii)(viii) new; trailing surface-hygiene sentence **verbatim** |
| — | Data and Artifact Availability | survives + v1.3.1 delta (E20) |
| — | Acknowledgments, bibliography | **verbatim** (Berg + Dadfar cites already present) |

**Moves/splits summary:** current §4 splits (Localization/Held-out/Auto-interp → §4.2;
Population profile → §4.3). Current §3, §5, §6, §7 move intact one level down. Current §8 moves
and retitles. fig:stack moves from the Introduction to the head of §4 (E4). Nothing else moves.

**Prose surviving verbatim (do not touch):** Related Work ¶1 (minus one sentence), ¶2, ¶3;
Setup all four ¶s (one clause edited); §4 ¶Localization, ¶Held-out separability + footnote +
fig:sep caption; ¶Bottom-up validation; ¶Population profile through "(−0.29)."; all of §5 +
table; §6 ¶graded-dose, ¶AI-hidden-state, fig:ladder caption, ¶semantics/causal, ¶gate-bias;
all of §7 + table; all of §8 + table; Discussion ¶cross-scale; Data availability (extended);
Acknowledgments; bibliography.

---

## 2. PER-EDIT PLANS

Format per edit: **anchor** = short unique span in the current tex (verified unique 2026-07-03
08:53); **action**; **drafted text**. LaTeX escapes as they must appear in the file.

---

### E1 — Title, pdftitle, keywords

- **Anchor A (2 occurrences, both edited):** `A Single-Expert Readout of a Reflective Worldview Register`
  (in `pdftitle=` and in `\title{`).
- **Action:** replace title in both places with:

> Composition-Sensitive Register Readouts in Mixture-of-Experts Routing: A Protocol, with a Case Study in Qwen3.5-35B

For `\title{}` (keeps the `\vspace`):

```latex
\title{\vspace{-1.0em}Composition-Sensitive Register Readouts in Mixture-of-Experts
Routing:\\A Protocol, with a Case Study in Qwen3.5-35B}
```

- **Anchor B:** `pdfkeywords={mixture-of-experts` and the visible `\textbf{Keywords:}` line.
- **Action:** insert `composition-sensitive register readouts, self-copy,` after
  `expert routing,` in both keyword lists (keep the rest unchanged).

---

### E2 — Abstract (protocol-first claims list) — DELTA on the already-applied rewrite

**Status:** the main session applied a protocol-first abstract on disk at 08:53 (begins
`We introduce a protocol for testing whether a routed mixture-of-experts (MoE)`). **Keep it.**
It already carries: the protocol list, the family framing, d=3.88 + rank 21 of 10,240, AUC
0.94, composition metering + paraphrase restoration, register-generality + the 13-expert
coalition, weak/conditional control, index locality, the bracketing sentence. Four gaps to
patch, three small edits:

**E2a.** Anchor: `rank 21 of 10{,}240`
Replace the parenthetical clause
`(Cohen's $d{=}3.88$, separated ranges; rank 21 of 10{,}240
expert--layer positions on the matched split)` with:

```latex
(Cohen's $d{=}3.88$, separated ranges; rank 21 of 10{,}240 expert--layer
positions on the matched split on the base model, 14 on the fine-tune, falling
to 515 on a world-model fine-tune, where rival E189, which outranks E114 at
both layers on all three surfaces, holds)
```

**E2b.** Anchor: `restored when prior register material`
After the sentence ending `…while semantics are preserved.` insert:

```latex
Across 55 copy-run onsets the gate crossing typically follows the onset (median
lead $-8$ tokens, leading in 11\%), reversing an earlier single-trajectory
ordering claim; a preregistered dose-response test of copy availability
returned its null (the paraphrase dose controls measured copying only leakily),
while its endpoints reproduced across machines to $\le 0.011$.
```

**E2c.** Anchor: `a register-invariant thirteen-expert reuse coalition rising on`
After `copied spans.` append (register-linked coordinate, the frozen fork wording):

```latex
E114's own suppression is register-linked: it falls under copying only in the
reflective register and rises in code, so composition-metering is a property of
the copy regime, within which E114 is the register-linked coordinate.
```

---

### E3 — Introduction rewrite

- **Anchor A:** `A register in which a` (start of the sentence to keep) — the opening through
  `…the danger of over-reading is acute.` survives verbatim.
- **Action:** replace everything from `A register in which a\nmodel examines itself…` through
  `…base model and a refusal-reduced \textsc{HauhauCS-Aggressive}\nfine-tune.` (i.e. the rest
  of ¶1 plus the whole `We ask a deliberately narrow` paragraph) with:

```latex
We treat such findings as instances of an object class,
\emph{composition-sensitive register readouts}: routed gate axes that separate
a generated register from lexically matched controls by a single linear
projection, carry a label recoverable by a blind auto-interpreter, and meter
the \emph{fresh composition} of register text rather than its surface
presence. We give a protocol for establishing membership
(\S\ref{sec:protocol}) and validate it in depth on \textsc{Qwen3.5-35B-A3B},
where a self-processing prompt first exposed Expert~114 at layer~14; the
protocol's own specificity sweep then places that expert inside a small family
of layer-14/26 stance separators. The register studied is a \emph{reflective
worldview register}: generated text sustaining an interpretive stance toward
meaning, belief, value, existence, or the interiority of a target. The case
study brackets the truth of any subjective claim: the object is a generated
register, and the protocol sorts self-descriptive text by how it was produced.
```

- **Anchor B:** `We make four contributions` (pre-existing count error: the list has five items).
- **Action:** replace the sentence and the whole `enumerate` with:

```latex
We make five contributions (Figure~\ref{fig:stack}):
\begin{enumerate}[leftmargin=*,nosep]
\item \textbf{A protocol.} Seven steps that establish a composition-sensitive
register readout: gate-axis recovery (never realized routed weight), an
all-position specificity sweep, matched-anchor held-out separation, blind
auto-interpretation of candidates, a composition battery, cross-register
generality, and cross-model application (\S\ref{sec:protocol}).
\item \textbf{A depth validation.} On \textsc{Qwen3.5-35B-A3B}, the recovered
E114 router row $\wvec$ separates register generations from lexically matched
controls at $d{=}3.88$ (separated ranges); a blind auto-interpreter recovers
the register at AUC~$0.937$; a dissociation battery factors the register apart
from verdict, safety, topic, person, and output commitment; causal control is
weak and conditional (residual-injection sufficiency; gate bias prompt-gated).
\item \textbf{A family result.} The sweep of all $256{\times}40$ expert--layer
positions on the matched split ranks E114@L14 at 21 of 10{,}240 on base and 14
on the fine-tune, and identifies a small family of L14/L26 stance separators:
E189 carries the same dual-layer signature and outranks E114 at both layers on
all three swept surfaces, and on a world-model fine-tune E114 falls to rank
515 while E189 holds (\S\ref{sec:family}).
\item \textbf{A preregistered composition result.} Per-turn ignition persists
across fourteen-turn dialogues while the between-peak floor collapses in
lockstep with measured self-copying; paraphrasing the history under mechanical
gates restores the floor ($+0.75$, 3/3 orderings), so literal copy
availability is the causal variable, and the copy regime survives
temperature-$0.7$ sampling. Across 55 copy-run onsets the gate crossing
typically follows the onset (median lead $-8$ tokens, leading in 11\%),
replacing an earlier single-trajectory lead claim. Across six output
registers the compose/reuse routing shift is register-general and E114's
suppression is register-linked (\S\ref{sec:breadth}).
\item \textbf{A scope bound.} Index~114 is local to
\textsc{Qwen3.5-35B-A3B}; E48 is the candidate analog in
\textsc{Qwen3.5-122B-A10B}; the three-model application of the protocol is
specified and pending (\S\ref{sec:transfer}).
\end{enumerate}
```

---

### E4 — fig:stack relocation and caption

- **Anchor:** `\caption{One axis, three readouts, one bound.`
- **Action 1:** move the whole `figure` environment from the Introduction to the head of new
  §4 (immediately after the `\section{Case Study…}` line inserted in E6b).
- **Action 2:** replace the caption with:

```latex
\caption{One axis, three readouts, one bound. Routing, SAE semantics, and
residual geometry are three readouts of the same E114 register axis; the gate
logit is a readout of it, and whether it also controls the register is left
open (\S\ref{sec:disc}). The all-position sweep places this axis inside a
small family of L14/L26 stance separators, with E189 outranking it at both
layers on all three swept surfaces (\S\ref{sec:family}).}
```

---

### E5 — Related Work, single-expert sentence

- **Anchor:** `register-level characterization of a \emph{single} expert`
- **Action:** replace the sentence
  `we use the per-token selection record as an interpretability readout and give a register-level characterization of a \emph{single} expert and its recovered linear gate.` with:

```latex
we use the per-token selection record as an interpretability readout, recover
per-expert linear gate axes, and give a register-level characterization of a
small routed family, with one member validated in depth.
```

---

### E6 — NEW §3: The Protocol

- **Anchor:** `\section{Setup}` — insert the new section **before** it.
- **Drafted text:**

```latex
\section{A Protocol for Composition-Sensitive Register Readouts}\label{sec:protocol}

A \emph{composition-sensitive register readout} is a routed-expert gate axis
with three properties: (a) its linear projection separates generations in a
target register from lexically matched controls; (b) a blind auto-interpreter
recovers the register from its top-activating contexts; (c) it tracks the
fresh composition of register text and disengages when the same surface is
produced by reuse of earlier material. The object is a readout; causal
control is no part of the definition and is tested separately. The protocol
has seven steps. Each is falsifiable on its own, and the case study
(\S\ref{sec:case}) instantiates every step.

\paragraph{P1: Gate-axis recovery.} Capture the router logits and the
pre-router residual at each candidate position. Recover each expert's router
row $w_e$ by least squares from $(\text{residual}, \text{logit})$ pairs and
use the projection onto $w_e$ as the primary statistic. Realized routed
weight is secondary only: sparse top-$k$ routing zeroes control tokens that
fall outside the top-$k$ and inflates ratio-style separations while
attenuating honest effect sizes.\footnote{In the case study the realized-\W{}
ratio is $21.68\times$ where the realized-\W{} $d$ is $2.61$--$2.94$ and the
recovered-axis $d$ is $3.88$ with separated ranges (\S\ref{sec:case}).}

\paragraph{P2: All-position specificity sweep.} On a matched register/control
split, recover $w_e$ for every expert at every layer and rank all positions by
$|d|$ on the projection, reporting the signed rank alongside. Pre-specify the
candidate position; every competitor surfaced by the sweep is post hoc, and
the extreme order statistics of a many-thousand-position sweep are inflated
by selection (winner's curse). Require any named rival to replicate across
surfaces before it enters the claims.

\paragraph{P3: Matched-anchor held-out separation.} Pair register-positive
prompts with controls that reuse the same anchor tokens while requesting
technical, third-person, or external-reference answers. Score the trimmed
generated track only, per token, and report $d$ on the recovered axis with
per-class ranges.

\paragraph{P4: Blind auto-interpretation.} Capture the candidate's routing
over raw corpus documents, rank top-activating contexts, and pass windows
only to a blind explainer; score the explanation with a fresh blind detector
against random contrasts. The label counts only if recovered without access
to the discovery prompts.

\paragraph{P5: Composition battery.} Four probes separate composition from
surface. (i)~\emph{Repeat-probe knee}: ask the identical probe every turn;
the between-peak floor should collapse at the first turn a prior answer is
available as copy source. (ii)~\emph{Copy-mediator regression}: measure
per-token longest $n$-gram match against the dialogue's earlier turns and
residualize the meter on the match-length predictors; the floor slope should
be absorbed. (iii)~\emph{Paraphrase manipulation under mechanical gates}:
replay a frozen history verbatim versus paraphrased under token-count
($\pm 10\%$) and zero-shared-8-gram gates; floor restoration under paraphrase
establishes literal copy availability, and rules out semantic saturation, as
the variable. (iv)~\emph{Transformation-depth ladder}: grade the history
transformation between verbatim replay and full paraphrase to locate where
restoration begins. [W4-TRANSFORMATION-DEPTH]

\paragraph{P6: Cross-register generality.} Repeat the battery in other output
registers with register-matched probes. Classify the copy regime (general or
register-bound) and the candidate's suppression (register-linked coordinate
or global), using each register's own composer set.

\paragraph{P7: Cross-model application.} Expert indices do not transfer
across models or scales. Re-run P1--P4 per model; map domain footprints
before any analog search; read architecture splits (here, DeltaNet versus
softmax attention) before trusting pooled tables.
```

### E6b — Case-study wrapper section

- **Anchor:** `\section{Setup}` (same insertion point, after the E6 block).
- **Action:** insert wrapper and demote; then retitle the five current sections to subsections:

```latex
\section{Case Study: Depth Validation on Qwen3.5-35B}\label{sec:case}
```

| current heading (anchor) | becomes |
|---|---|
| `\section{Setup}` | `\subsection{Instantiation and Measurement Surface}` |
| `\section{E114 is a Linear Readout of a Reflective Worldview Register}` | `\subsection{Separation and Label}` |
| *(new, inserted before `\paragraph{Population and layer profile.}`)* | `\subsection{The All-Position Sweep: a Family of L14/L26 Stance Separators}\label{sec:family}` |
| `\section{Dissociating the Register from Nearby Explanations}` | `\subsection{Dissociation from Nearby Explanations}` |
| `\section{A Live Process, Graded by Intensity}` | `\subsection{Process Dynamics and Causal Probes}` |
| `\section{Conversational Dynamics: The Readout Tracks Composition}\label{sec:convdyn}` | `\subsection{Conversational Dynamics: the Readout Meters Composition}\label{sec:convdyn}` |

Note: "Graded by Intensity" leaves the heading; the intensity operationalization stays in the
body text with its existing hedges, pending [SEC4-AXIS-REGRESSION].

---

### E7 — Setup trim-rule clarification

- **Anchor:** `first generated chat-template delimiter`
- **Action:** replace
  `trimmed at\nthe first generated chat-template delimiter \texttt{<|im\_end|>}, because\naggregate and prefill leaders are often formatting-token artifacts.` with:

```latex
trimmed at the first generated chat-template delimiter, applied on the decoded
text (the base surface emits \texttt{<|im\_end|>} as a multi-token BPE
sequence, so token-id scans do not bound the turn), because aggregate and
prefill leaders are often formatting-token artifacts.
```

---

### E8 — §6c absorption (family reframe, E189, AgentWorld 515)

- **Anchor:** `uncomputed baseline.` (end of the Population-and-layer-profile paragraph).
- **Action:** the paragraph survives verbatim through `…E68 co-fires\n($+0.46$) but E87 \emph{anti}-correlates ($-0.29$).` Replace its final sentence
  (`This is the first all-expert specificity context for E114; the\nbest-separating expert on the matched register/control split remains the one\nuncomputed baseline.`) with the subsection break from E6b plus:

```latex
\subsection{The All-Position Sweep: a Family of L14/L26 Stance Separators}\label{sec:family}

The remaining specificity gap, the best-separating expert on the matched
register/control split, is now measured. On fresh 20-prompt register/control
captures of all 40 layers on three surfaces, analyzed separately and never
pooled (base, \textsc{HauhauCS}, and the \textsc{AgentWorld} world-model
fine-tune), we recovered the gate axis $w_e$ for every one of the
$256{\times}40{=}10{,}240$ expert--layer positions (30{,}720 recoveries; max
relative residual $2.2\times10^{-5}$) and ranked all positions by $|d|$ on the
recovered-axis projection, the $d{=}3.88$ statistic generalized. E114@L14, the
only pre-specified position, ranks \textbf{21} on base ($d{=}{+}3.421$; rank 3
of 256 within L14), \textbf{14} on \textsc{HauhauCS} ($d{=}{+}4.957$; rank 2
within L14), and \textbf{515} on \textsc{AgentWorld} ($d{=}{+}2.793$; rank 19
within L14); its L26 twin ranks 51, 60, and 545. Positions with larger $|d|$
exist on every surface: 20 on base, the largest E87@L9 at $d{=}{+}4.965$, and
13 on \textsc{HauhauCS}, the largest E203@L36 at $+6.789$. The base rank-1
does not replicate across surfaces (E87@L9 sits at rank 131 on
\textsc{HauhauCS} and 806 on \textsc{AgentWorld}), the expected winner's-curse
pattern for the extreme order statistics of a 10{,}240-position sweep at
$n{=}10$ per class (SE$(d){\approx}0.7$); every competitor is post hoc.

Three positions are top-30 on all three surfaces: \textbf{E189@L14},
\textbf{E189@L26}, and E203@L36. E189 is the only expert with E114's dual
L14$+$L26 signature stable across all three models, and it outranks E114 at
both layers on every surface (L14: $+3.519/{+}5.673/{+}4.252$ against E114's
$+3.421/{+}4.957/{+}2.793$; L26: $+3.707/{+}4.779/{+}4.137$ against
$+3.021/{+}4.107/{+}2.764$). That advantage is directionally consistent 6/6
(two layers, three surfaces) and is therefore not attributable to selection
noise alone. The defensible claim after this baseline: the matched
register/control split is read out by a small family of L14/L26 stance
separators in which E114 is a leading, causally-validated member (top 0.21\%
on base, top 0.15\% on \textsc{HauhauCS}), not the unique summit of the
$256{\times}40$ table. The \textsc{AgentWorld} surface separates the family
members: world-model training reshapes E114's readout (rank 21 to 14 to 515)
while E189's and E203's hold. Two independent cross-checks land in family:
E114's window-1..128 sensitivity $d{=}{+}2.97$ on this capture against the
positive-control gate $d{=}2.93$ on the independent held-out capture, and
E87's negative image at L14/L26 ($d{=}{-}1.13/{-}1.17$ on base), which
independently reproduces the conversational-dynamics coalition finding
(\S\ref{sec:convdyn}). Whether E189 carries the same blind auto-interpretation
label is pending. [W6-E189-LABEL] [W3-FRESH-SEPARABILITY]
```

---

### E9 — Lead-lag reversal paragraph

- **Anchor:** `\paragraph{The gate leads degeneration.}`
- **Action:** replace the whole paragraph (through `…the looped vocabulary lingers after it.`) with:

```latex
\paragraph{The gate at degeneration.}
Seeded with a self-referential answer, the base model sustains the register,
then, under deterministic decoding with zero repetition penalty, degenerates
into a verbatim loop. As it does, the gate logit travels the full distance
from the register-positive level ($-4.36$) to the control level ($-5.25$):
the generated state leaves the register-positive region. In this original
single trajectory the gate crossed the $-4.82$ midpoint at token~126, three
tokens before verbatim repetition locked at token~129
(Figure~\ref{fig:leadlag}), with the SAE representation fading later still
($\sim$token~141). A distributional replication reverses that ordering as the
typical case. Measured over every clean copy-run onset in the
conversational-dynamics data (\S\ref{sec:convdyn}; an onset is a copy run of
$\ge$12 tokens preceded by $\ge$12 fresh tokens, and the crossing is a
sustained fall below the per-dialogue fresh/copied midpoint), the gate
crossing typically \emph{follows} the onset: across $n{=}55$ de-duplicated
onsets the median lead is $-8$ tokens (IQR $[-18.5, -5.0]$), with the gate
crossing first in 11\% of onsets (6/55). The pattern holds separately under
greedy decoding (median $-7$, $n{=}21$) and temperature sampling (median
$-8$, $n{=}34$), and a relaxed onset definition agrees (median $-7$,
$n{=}79$). The single-trajectory $+3$-token lead sits in that 11\% tail. The
gate is not an early-warning signal for reuse; it disengages a few tokens
after reuse begins, which is the ordering a composition meter implies. The
looped text still ``says'' self-referential things after the gate has
returned to the control range, so the surface vocabulary outlives the meter.
(The replication is post-hoc and descriptive, not preregistered: onset,
window, and midpoint definitions were fixed before computing leads but after
the grid data had been seen in prior analyses.)
```

---

### E10 — Figure 3 (fig:leadlag) caption

- **Anchor:** `\caption{\textbf{The gate leads degeneration.}`
- **Action:** replace the full caption with:

```latex
\caption{\textbf{Onset, then gate.} The trace shown is the original single
greedy trajectory: the E114 gate logit crosses the $-4.82$ register/control
midpoint at token~126, three tokens before verbatim repetition locks (129),
with the SAE representation fading later ($\sim$141). Across $n{=}55$ clean
copy-run onsets in the conversational-dynamics data the typical ordering
reverses: the gate crossing follows the onset (median lead $-8$ tokens, IQR
$[-18.5,-5.0]$), leading in 11\% of onsets. The plotted trajectory sits in
that 11\% tail.}
```

---

### E11 — W5 null paragraph

- **Anchor:** `\paragraph{Reading.}` — insert the following paragraph **before** it (after the
  convdyn-T table paragraph).
- **Drafted text:**

```latex
\paragraph{Dose-response: a preregistered null.}
A third battery titrated copy availability (prereg v1.0, SHA-256
\texttt{7bfc9c4d\ldots}; 15 cells: three orderings, provided histories with
$0/2/4/6/7$ of seven turns paraphrased, latest-first). The frozen monotonicity
prediction was not supported: pooled Spearman
$\rho(\text{floor},\text{dose}){=}0.556$ against a frozen $0.8$ bar, with the
per-ordering nondecreasing rule met in 1/3 orderings, so the preregistered
null stands. The manipulation check passed directionally (measured copy
fraction falls with dose, $\rho{=}{-}0.628$) and is leaky at the cell level:
one fully-paraphrased cell copied its \emph{paraphrased} history (copy
fraction $0.746$) and stayed cold ($-6.277$), while one cell with five
verbatim turns available declined to copy ($0.014$) and recovered ($-4.568$).
The endpoints replicate: dose-0 floors reproduce the paraphrase battery's
replay floors to $\le 0.011$ in all three orderings on a different box and
GPU, and the dose-7 recovery is positive 3/3 with magnitude comparable to the
paraphrase result (pooled $+0.956$ here, $+0.753$ there). An exploratory read,
not preregistered: the floor tracks the \emph{measured} copy fraction at
$\rho{=}{-}0.885$ across the 15 cells, so the copying-to-floor link is tight
and the failure localizes to dose-to-copying. Copy availability is causal at
the endpoints; the model's decision to copy is not a smooth function of the
available fraction. [INTERACTION-MODEL]
```

---

### E12 — NEW §5: Breadth (W2)

- **Anchor:** `\section{Scope Bound: Index 114 is Local to 35B}` — insert the new section
  **before** it.
- **Drafted text:**

```latex
\section{Breadth: Six Registers, One Copy Regime}\label{sec:breadth}

A preregistered multi-register battery (prereg v1.1, SHA-256
\texttt{f20b7612\ldots}; 168 captures) applied the composition battery's
repeat-probe arm to six output registers: reflective-worldview (REG),
technical (TECH), legal (LEGAL), narrative (NARR), poetic (POET), and code
(CODE), with greedy and temperature-$0.7$ cells scored separately. Four of
four substantive frozen predictions were supported; the frozen null was not.

\paragraph{The copy regime is register-general.}
Every dialogue entered total literal self-copy at turn~2: the trimmed
responses are SHA-identical across turns within each dialogue, with copy
fraction $0.961$ in 10 of 12 cells ($0.957$ in POET-greedy; $0.759$ in
TECH-greedy, which locks into a 29-token loop). Under copying, routing
reorganizes per the frozen rule (fraction of 256 experts with $|d|{>}1$ at
L14 $\ge 0.30$, and at least 3 of the register's own top-10 composers falling
at $d{<}{-}1$) in five of six registers: REG $0.422$, CODE $0.414$, TECH
$0.359$, NARR $0.328$, POET $0.316$; LEGAL misses at $0.242$. The regime is
temperature-robust (the rule holds in 4/6 registers at $0.7$; late copy
fraction $0.961$ in 6/6). A register-invariant reuse coalition exists: 13
experts rise at $d{>}{+}1$ in at least five of six registers at L14 (15 at
L26). The named candidate from the conversational-dynamics coalition, E87, is
not in that core: it rises in 4/6 registers ($d{=}{-}1.08$ in LEGAL, $+0.36$
in CODE), and the register-invariant core is carried by other experts (E78
and E143 rise 6/6).

\paragraph{E114 is the register-linked coordinate.}
E114 sits in REG's composer set (rank 5 by selection difference) and falls
under copying only there ($d{=}{-}1.356$ at L14; faller rank 20 of 256). In
the five non-REG registers it is never a top-20 faller, and in CODE it rises
under copying ($d{=}{+}1.800$). The preregistered interpretation fork fired
in the distributed direction, with the frozen wording: composition-metering
is ``a property of the copy regime, within which E114 is the register-linked
coordinate.'' E189 is simultaneously REG's top composer (selection difference
$+0.675$) and its deepest composer faller ($d{=}{-}2.81$), a third convergent
line on the family reading of \S\ref{sec:family}.

\paragraph{An entropy observation.}
At temperature $0.7$ the repeat-probe dialogues collapse to determinism:
output entropy falls from $0.851$ at turn~1 to $0.066$ at turn~2 and $0.008$
by turn~8, and turns are SHA-identical from turn~2. The copy attractor
absorbs the sampling noise entirely. (Caveats as frozen: $n{=}1$ dialogue per
register and sampler, with sign patterns across six registers in place of
seed replication; copied/fresh token classes are unbalanced late; the
composer-set definition is selection-based and frozen.)
```

---

### E13 — Transfer section retitle + placeholder

- **Anchor:** `\section{Scope Bound: Index 114 is Local to 35B}`
- **Action 1:** retitle to:

```latex
\section{Transfer: Cross-Model Application}\label{sec:transfer}
```

- **Action 2:** the section body and tab:transfer survive verbatim. Append at the end of the
  section:

```latex
The full three-model application of the protocol is specified and frozen
(multi-model spec v1.0.1, SHA-256 \texttt{db977c52\ldots}): an index-stability
leg on the architecturally identical \textsc{Qwen3.6-35B-A3B} and the E48
candidate capture on 122B, both on instruct surfaces (no base checkpoint is
published for either model), a disclosed caveat. Results land here.
[REPLICATION-3.6-122B]
```

---

### E14 — Discussion ¶"What held up"

- **Anchor:** `gate-leads-collapse timing`
- **Action:** replace the paragraph body
  (`A single MoE router row defines … the verdicts the journals assign.`) with:

```latex
A single MoE router row defines a clean linear readout for an interpretable
generated register, and that readout now sits inside a measured family. The
separability ($d{=}3.88$, separated ranges), the dissociation battery, the
preregistered composition metering with its paraphrase confirmation, and the
cross-scale locality survive the checks applied to them and are reported with
the verdicts the journals assign. Two earlier readings moved under
replication: the best-separating-expert baseline relocates uniqueness to a
family claim (\S\ref{sec:family}), and the single-trajectory gate lead
reverses as a typical ordering (median $-8$ tokens across 55 onsets,
gate-leading 11\%).
```

---

### E15 — Discussion ¶readout/controller opening

- **Anchor:** `early correlate`
- **Action:** replace the two sentences
  `The lead--lag timing is consistent with E114's gate acting as an early correlate\nof the register transition, and it is tempting to call E114 a ``gate-like\nmechanism'' for the register. The evidence supports a narrower claim.` with:

```latex
The onset-aligned replication places the gate crossing after copy onset in
the typical case (median $-8$ tokens), so the gate reads as a fast follower
of the composition state, and the evidence supports a narrower claim than a
``gate-like mechanism'' for the register.
```

  (Rest of the paragraph survives verbatim.)

---

### E16 — Discussion ¶"Composition and reuse", E87 clause

- **Anchor:** `(E87 foremost)`
- **Action:** replace `with a complementary coalition\n(E87 foremost) rising on exactly those spans.` with:

```latex
with a complementary coalition rising on exactly those spans (E87 foremost in
the reflective-register dialogues; the six-register battery shows the
register-invariant core excludes E87 and is carried by other experts,
\S\ref{sec:breadth}).
```

---

### E17 — NEW Discussion paragraph: family / coordinate

- **Anchor:** `\paragraph{What the cross-scale result buys.}` — insert **before** it:

```latex
\paragraph{A family, with a register-linked coordinate.}
The all-position sweep and the six-register battery converge on the same
relocation of the claim. The matched split is read out by a small family of
L14/L26 stance separators; E114 is a leading, causally-validated member, and
E189 outranks it at both layers on all three swept surfaces. The composition
dynamics are a property of the copy regime, within which E114 is the
register-linked coordinate: the compose/reuse routing shift appears in five
of six registers with register-specific composer sets, and E114's own
suppression appears only in the reflective register, rising in code. Three
independent lines now mark E189: the dual-layer sweep signature, top-composer
status in the reflective register with the deepest copy fall ($d{=}{-}2.81$),
and cross-surface stability where E114 dissociates (rank 515 on the
world-model fine-tune). Its blind label is pending [W6-E189-LABEL]. What is
unchanged for E114: the recovered-axis separation, the dissociation battery,
the blind label, the sufficiency intervention, and the coordinate role.
```

---

### E18 — Conclusion rewrite

- **Anchor:** `\section{Conclusion}` — replace the entire section body (through
  `…the E48 candidate\ncapture on 122B.`) with:

```latex
We defined composition-sensitive register readouts and gave a protocol for
establishing them: gate-axis recovery, an all-position specificity sweep,
matched-anchor held-out separation, blind auto-interpretation, a composition
battery, cross-register generality, and cross-model application.
\textsc{Qwen3.5-35B-A3B} instantiates the protocol in depth. The recovered
E114 axis separates a reflective worldview register at $d{=}3.88$ with
separated ranges and carries a blind label at AUC~$0.937$. The sweep of all
$256{\times}40$ positions ranks E114@L14 at 21 of 10{,}240 on base and 14 on
the fine-tune and identifies a small family of L14/L26 stance separators, with
E189 outranking E114 at both layers on all three surfaces and E114 alone
reshaped by world-model training (rank 515). The preregistered composition
battery shows the readout metering fresh composition: it goes dark under
literal reuse, is restored by paraphrase ($+0.75$, 3/3 orderings), survives
temperature-$0.7$ sampling, and its gate crossing typically follows copy
onset (median $-8$ tokens, leading in 11\% of 55 onsets). Across six
registers the copy regime is general and E114 is the register-linked
coordinate. A preregistered dose-response test returned its null: the
paraphrase dose controls measured copying only leakily
($\rho{=}0.556$ against a $0.8$ bar), while the endpoints reproduce across
machines to $\le 0.011$. Index~114 is local to this model. The open protocol
steps are slotted: ladder variance [W1-LADDER-VARIANCE], fresh-bank
separability [W3-FRESH-SEPARABILITY], the transformation-depth ladder
[W4-TRANSFORMATION-DEPTH], the vantage-axis regression [SEC4-AXIS-REGRESSION],
the E189 blind label [W6-E189-LABEL], and the three-model application
[REPLICATION-3.6-122B].
```

---

### E19 — Limitations rewrite

- **Anchor:** `\section{Limitations}\label{sec:lim}` — replace the entire section body with the
  following. Items (i) and (iv) are the current text near-verbatim; (v) and (vi) are the current
  text with appended material; (ii) is replaced (the old gap is answered); (iii) is adjusted;
  (vii) and (viii) are new. The trailing surface-hygiene passage survives verbatim.

```latex
The claim is deliberately narrow (a register detector within a measured
family), and several soft joints remain. (i)~\textbf{The register label has
blind auto-interpreter support}: a two-stage auto-interpreter (windows-only
explainer then a fresh blind detector) reproduces it at AUC~$0.937$ and
broadens it to a reflective worldview axis; the formal external-labeler
\emph{verdict} table remains pending. [PENDING]
(ii)~\textbf{All-expert specificity is now measured, and the measurement
reshapes the claim} (\S\ref{sec:family}): E114@L14 ranks 21/10{,}240 on base,
14 on \textsc{HauhauCS}, and 515 on \textsc{AgentWorld}, with E189 outranking
it at L14 and L26 on all three surfaces. The sweep's own limits: $n{=}10$ per
class (SE$(d){\approx}0.7$), winner's-curse inflation in the extreme order
statistics, and every competitor is post hoc (E114@L14 was the only
pre-specified position). E189's blind label is pending [W6-E189-LABEL], and a
separability estimate on a freshly authored prompt bank is pending
[W3-FRESH-SEPARABILITY].
(iii)~Several headline probes (the prompt ladder, the AI-hidden-state
follow-up, the steering intervention) are \textbf{single deterministic
generations} (point estimates), and the steering result shows
\emph{sufficiency} only; ladder variance is pending [W1-LADDER-VARIANCE]. The
gate-lead trace now has a distributional replication across 55 onsets, which
reversed the typical ordering; that replication is post-hoc and descriptive,
not preregistered.
(iv)~A control comparing true model-routing traces against shuffled or
fictional traces yielded a near-zero E114 effect, and the result is sensitive
to template mode (a thinking-allowed shakedown flipped sign).
(v)~The conversational-dynamics batteries use three orderings or three seeds
per cell and report sign consistency; most late turns hit the 180-token
generation cap; the temperature battery covers pure-temperature sampling at
$0.5$ and $0.7$; the two batteries ran on different builds of the pinned
\texttt{llama.cpp} commit, and greedy trajectories are build-sensitive, so
cross-battery comparisons are made at the routing-signature level; and the
paraphrased histories were authored by a language model from a different
vendor than the subject model, disclosed in the preregistration and gated at
capture time (token counts within $\pm 10\%$ of the originals, zero shared
token 8-grams). The six-register battery runs $n{=}1$ dialogue per register
and sampler, with sign patterns across six registers in place of seed
replication, and its archival all-layer routing set was retained only at
L14/L26 locally (all frozen rules read L14/L26 only). All 15 dose-response
cells ran to the generation cap.
(vi)~A separate preregistered adjudication of the vantage-ladder axis
(regressing the $\wvec$ projection on construction, intensity, and content
ratings) is pending [SEC4-AXIS-REGRESSION]; the conversational result
supports a construction reading in its own setting, and the ladder's
``intensity'' label stays an operationalization until that regression runs.
(vii)~\textbf{The dose-response titration returned its preregistered null}
(\S\ref{sec:convdyn}): the paraphrase dose controls measured copying only
leakily ($\rho(\text{floor},\text{dose}){=}0.556$ against the frozen $0.8$
bar), so the causal claim about copy availability is endpoint-scoped,
established at verbatim replay versus full paraphrase, with the interior of
the dose curve unmodeled [INTERACTION-MODEL].
(viii)~The breadth and transfer arms carry placeholders until their capture
legs land: the transformation-depth ladder [W4-TRANSFORMATION-DEPTH] and the
three-model application [REPLICATION-3.6-122B]. Captures must be kept
separate across surfaces (base vs.\ fine-tune; Q8\_0 vs.\ bf16; router vs.\
SAE; reasoning-off vs.\ reasoning-enabled; prefill vs.\ generation; raw vs.\
trimmed), since Q8\_0 and bf16 greedy trajectories diverge; and 122B
generations often continue into chat-template control tokens, so only the
pre-spill segment is used.
```

---

### E20 — Data and Artifact Availability delta

- **Anchor:** `artifact bundle from v1.3.0`
- **Action:** after `…included in the artifact bundle from v1.3.0 under the same\nraw-tensor policy;` insert:

```latex
the v1.3.1 additions are the all-position sweep (frozen spec, analysis code,
and full per-surface ranking JSONs), the onset-aligned lead-lag replication
(results and figure), and the six-register and dose-response batteries
(frozen preregistrations, frozen inputs, and scored results); Zenodo v1.3.0
is published as record 21148667 under the unchanged concept DOI;
```

  (then the existing sentence about raw capture tarballs continues unchanged).

---

## 3. PLACEHOLDER SLOTS (one-line specs; leave as literal bracketed markers in the tex)

| slot | spec | lands in |
|---|---|---|
| **[W1-LADDER-VARIANCE]** | Seed-replicated re-capture of the vantage ladder attaching variance (n seeds per rung) to the currently single-generation point estimates. | §4.5 ladder ¶; Limitations (iii) |
| **[W3-FRESH-SEPARABILITY]** | Held-out separation (protocol P3) re-run on a freshly authored matched-anchor register/control bank on 3.5-35B, reporting the recovered-axis d beside the original 3.88 and the sweep's +3.42 re-estimate. | §4.3 end; Limitations (ii) |
| **[W4-TRANSFORMATION-DEPTH]** | The frozen transformation-depth ladder (prereg `f31730c4…`, materials `4b5adce5…`): graded history transformations between verbatim replay and full paraphrase, locating where floor restoration begins. | Protocol P5(iv); §4.6 |
| **[SEC4-AXIS-REGRESSION]** | The frozen adjudication regression `w114 ~ construction_proxy + intensity_rating + worldview_content_rating + mean_entropy` (gated on the judge-model ratings); confirms or retitles the ladder's "intensity" operationalization. | §4.5; Limitations (vi) |
| **[W6-E189-LABEL]** | Blind auto-interp labels for the sweep candidates, E189 foremost (windows pulled to `fleet/W6_windows/`, blinding intact): does E189 carry the same register label as E114. | §4.3; Discussion family ¶ |
| **[REPLICATION-3.6-122B]** | The frozen multi-model spec v1.0.1 (`db977c52…`): index-stability leg on Qwen3.6-35B plus the E48 candidate capture on 122B; instruct surfaces both legs (no base checkpoints published), disclosed caveat; re-run pins in `fleet/records_B2/PINS_B.txt`. | §6 Transfer |
| **[INTERACTION-MODEL]** | A model of when available copy converts into actual copying (the leaky dose-to-mediator link from W5: copy decision as threshold/interaction, not dose-proportional), motivated by the tight copying-to-floor link (exploratory ρ=−0.885) against the loose dose link (ρ=0.556). *Alternate reading exists; see judgment calls.* | §4.6 W5 ¶; Limitations (vii) |

---

## 4. COVERAGE CHECKLIST (required items → edits)

- Abstract rewrite, protocol-first claims list → **E2** (delta on the main session's applied draft)
- §6c absorption: family reframe, E189, AgentWorld 515 → **E8** (+ E2a, E3, E4, E14, E17, E18, E19(ii))
- Lead-lag reversal paragraph + Fig 3 caption (onset-then-gate, median −8, 11%, n=55) → **E9, E10** (+ E2b, E3 item 4, E14, E15, E18, E19(iii))
- W2 fork sentence (frozen wording, quoted) + entropy-collapse observation → **E12** (+ E2c, E16, E17)
- W5 null paragraph → **E11** (+ E2b, E18, E19(vii))
- Discussion family/coordinate paragraph → **E17**
- Conclusion → **E18**
- Limitations rewrite: (ii) answered, W5 null added, [PENDING]/slot flags kept → **E19**
- Placeholder slots with specs → **§3 of this packet**
- Voice rules → **§0**

## 5. KNOWN RISKS WHEN APPLYING

- **Concurrent editing.** The tex changed on disk at 2026-07-03 08:53 (abstract). If the main
  session keeps editing, re-verify each anchor immediately before its edit; anchors here are
  text spans, not line numbers, for that reason.
- E6b's demotions renumber `\S\ref{…}` cross-references automatically, but ONE hardcoded
  reference exists (verified by grep): in the convdyn coalition paragraph,
  `anti-correlate (\S4), is the third-ranked \emph{riser}` — change `(\S4)` to
  `(\S\ref{sec:family})` when applying E6b (anchor: `anti-correlate (\S4)`, unique).
- After applying: `pdflatex` twice; confirm fig:stack floats near §4's head; confirm the
  abstract still fits the full-width block.
