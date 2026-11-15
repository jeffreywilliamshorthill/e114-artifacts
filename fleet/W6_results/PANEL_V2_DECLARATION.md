# W6 auto-interp explainer-panel v2 — pre-declared 2026-07-03 (before any v2 call)

Motivation: v1's single blind explainer (gpt-5.5) described corpus surface-format instead of
theme on 5/6 targets (AUC dragged toward chance) while its detector correctly rewarded the one
surface-true label (E189_L14, 0.886). v2 varies ONLY the explainer model.

- Explainer instruction: FROZEN v1 prompt verbatim (no revision).
- Detector: FIXED = the v1 Gemini detector, same shuffle seed 41414, same scoring.
- Explainer panel (non-Qwen; exact OpenRouter slugs recorded at call time): (1) openai/gpt-5.5
  [= the v1 run, carried in as panel member 1, NOT re-run], (2) google gemini latest pro,
  (3) deepseek latest flagship chat, (4) meta llama latest largest instruct. If a slug is
  unavailable, substitute the vendor's newest flagship and record it.
- Outputs per target: every panel label + its detector AUC / P@40 / Spearman, side by side.
- HEADLINE RULE (frozen now): per target, the reported label = the panel label with the highest
  detector AUC; ALL labels and AUCs published; v1 results never discarded.
- Blinding invariants unchanged: explainers see the 40 top windows' text only (no scores, no
  target identity, no activations); detector never sees which windows were top.
- Cross-panel note: explainers run independently; no explainer sees another's label.
