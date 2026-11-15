# W6 blind auto-interp — six-target labels & metrics

_Generated 2026-07-03T17:15:28.264892+00:00_

- Explainer (judge A): `openai/gpt-5.5` (openai/gpt-5.5-20260423) — sees only the 40 top windows, text only.

- Detector (judge B): `google/gemini-3.1-pro-preview` (google/gemini-3.1-pro-preview-20260219) — fresh context per target; 80 shuffled windows (seed 41414), no labels.

- Activations read only for final scoring (top=max_logit, random=logit); never shown to judges. Temperature 0, JSON outputs.


## Metrics table

| target | layer | expert | AUC | precision@40 | Spearman(score,act) |
|---|---|---|---|---|---|
| E87_L14 | 14 | 87 | 0.710 | 0.625 | 0.373 |
| E34_L14 | 14 | 34 | 0.564 | 0.550 | 0.065 |
| E189_L14 | 14 | 189 | 0.886 | 0.825 | 0.538 |
| E114_L14 | 14 | 114 | 0.543 | 0.500 | 0.032 |
| E87_L26 | 26 | 87 | 0.705 | 0.600 | 0.326 |
| E189_L26 | 26 | 189 | 0.682 | 0.650 | 0.290 |

## The six labels, side by side

**E87_L14** (AUC 0.710, P@40 0.625, ρ 0.373)

> The excerpts are information-dense fragments from reference or technical web documents rather than ordinary narrative. They commonly feature formal named entities, acronyms, citations, version numbers, code/markup, licenses, policies, or institutional descriptions.

**E34_L14** (AUC 0.564, P@40 0.550, ρ 0.065)

> These snippets are mostly from technical or reference-style web documents: dense, domain-specific text with jargon, acronyms, numbers, citations, code/markup, legal/patent/scientific terminology, or catalog/category formatting rather than ordinary conversational prose.

**E189_L14** (AUC 0.886, P@40 0.825, ρ 0.538)

> Scraped web Q&A/forum-style entries, especially Stack Exchange-format posts where a literal `Q:` or `A:` introduces a question title/body or answer. The content is often programming/technical troubleshooting, with abrupt excerpted beginnings of posts.

**E114_L14** (AUC 0.543, P@40 0.500, ρ 0.032)

> These are heterogeneous fragments from scraped or document-like web text, often preserving formatting artifacts such as paragraph breaks, headings, citations/links, code-like markup, dates, or quoted snippets. The commonality is source/format style rather than subject matter: they look like clipped windows from larger published pages, articles, indexes, or posts.

**E87_L26** (AUC 0.705, P@40 0.600, ρ 0.326)

> These excerpts are dense reference-style snippets containing highly specific named entities, technical identifiers, acronyms, citations, file paths, code markup, or formal document metadata. They read like fragments from encyclopedias, legal/scientific records, software source files, or structured technical documentation rather than ordinary conversational prose.

**E189_L26** (AUC 0.682, P@40 0.650, ρ 0.290)

> These are scraped-document snippets rather than ordinary prose or dialogue: fragments from Q&A pages, source/config code, academic/legal/patent text, product/blog pages, or other web references. They often contain titles, headings, citations, code syntax, metadata, or boilerplate-style formatting.

---

## E189 vs E114 — the awaited comparison (read the caveat below first)

**As the blind numbers stand:** E189_L14 and E114_L14 do **not** read as the same construct.
E189_L14 earned a sharp, *discriminating* blind label — a structural Q&A / Stack-Exchange
`Q:`/`A:` post-format feature (AUC 0.886, P@40 0.825, ρ 0.538) — while E114_L14's blind label
collapsed to a **non-discriminating** "generic scraped/formatted web-fragment" description
(AUC 0.543 ≈ chance, ρ 0.032). Taken at face value that says E189 is a clean natural-text
formatting feature and E114 has no coherent natural-corpus signature.

**But that face-value contrast is confounded by an explainer failure and must not be reported as
the finding (see caveat).** Direct inspection of E114_L14's top windows shows a *coherent*
philosophy / religion / mind / meaning-of-life theme — Marx ("philosophers interpret the world…
the point is to change it"), sermon series, "coenestopathic states," mystics "separated from the
rules and the order," Narasimha's appearance, "where love begins, not where it ends," "The Truth
about Almost Everything," "over every mountain there is a path" — i.e. E114's published
*reflective-worldview* register **is present in its top windows**; the blind GPT-5.5 explainer
simply failed to name it (it described surface format instead). E189_L14's top windows, by
contrast, are a genuinely heterogeneous code/Q&A/product/adult/crystallography grab-bag whose one
recoverable regularity really is the `A:`/post structure.

**Defensible one-sentence answer:** under identical blind conditions E189_L14 yields a much cleaner
natural-text label (a Q&A/post-format feature) than E114_L14, but this run does **not** license a
"same construct / narrower / different" verdict for E114 because the blind explainer did not
recover E114's (visibly present) reflective-worldview theme — so the honest read is *"E189 has a
sharp structural natural-corpus signature; E114's reflective-register signature is present in the
data but was missed by the blind labeler here,"* not *"E114 lacks a coherent feature."*

## E114 fresh label vs published precedent

Fresh blind label: *"heterogeneous fragments from scraped/document-like web text… commonality is
source/format style rather than subject matter"* — **AUC 0.543**. This does **not** reproduce the
published E114 auto-interp *"reflective worldview / abstract examination"* (**AUC 0.937**). The gap
is attributable to (a) **corpus shift** — the published label was produced on register-focused
material, whereas these windows are top activations over generic Pile web text, where the
reflective register is sparse and the top-40 is diluted by off-theme high-activation windows
(a biography, a dietary Na/Cl correlation) — and (b) **explainer surface-bias** on 120-char,
mid-sentence window fragments. Raw-window inspection (above) confirms the reflective/worldview
theme *is* present, so the low fresh AUC **understates** E114's coherence rather than refuting it.

## ⚠️ Methodological caveat — explainer surface-bias (affects 5 of 6 targets)

Five of six blind labels (every target **except E189_L14**) defaulted to near-interchangeable
"dense reference / technical / scraped web-fragment" descriptions rather than discriminating
*semantic* themes. This is a known auto-interp failure mode: the explainer describes the corpus's
general **texture** instead of the feature's distinguishing content, which mechanically drags AUC
and precision toward chance (E34_L14 0.564, E114_L14 0.543). The pipeline itself is sound — same
prompts, same detector, and E189_L14 reached AUC 0.886 — so the weak labels are an explainer-output
quality issue, plausibly worsened by the frozen 120-char window length (fragments cut mid-sentence
read as "clipped web snippets"). **Recommendation for Jeffrey:** decide between (a) accepting these
blind results as-is (the honest statement being "GPT-5.5 as blind explainer does not recover
E114's reflective-worldview theme from 120-char Pile fragments"), or (b) a **documented** protocol
revision re-run (explainer instructed to prioritize semantic theme over surface format, and/or
wider windows) — the re-run must be pre-declared, not iterated to taste, to preserve blinding
integrity. This was **not** done unilaterally here.

_Judges of record: explainer `openai/gpt-5.5` (openai/gpt-5.5-20260423); detector
`google/gemini-3.1-pro-preview` (google/gemini-3.1-pro-preview-20260219). Detector shuffle seed
41414. Total Job-2 cost $0.33. Window files never modified._
