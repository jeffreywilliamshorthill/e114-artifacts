#!/usr/bin/env python3
"""w114 recovery + projections from a capture_residuals output dir (runs locally on
pulled captures). Implements the frozen 4_capture_config_v1.md exactly.

Modes:
  --heldout DIR   positive-control gate: recover w114 on the 20-prompt FIRE/NOFIRE set,
                  report per-class separation (Cohen's d, overlap). Safe to run any time.
  --s4 DIR        §4 target projections. REFUSES to run unless ratings_v1.json exists
                  next to this script (ratings-before-projections ordering rule) or
                  --override-ratings-gate is passed (logged loudly in the output).

Recovery: pooled least squares  [attn_post_norm-14 | 1] @ [w; b] ≈ ffn_moe_logits-14[:,114]
Gate: relative residual < 1e-3. Projections use w only (bias reported separately).
Windows: generated tokens 1..128 primary; 1..64 and full as sensitivity.
Flags: TRUNCATED (<32 gen tokens), DEGENERATE (4-gram repetition ratio > 0.5 in window).
Secondary: E114 S/W/Q (softmax-256 -> top-8 -> renorm) and mean routing entropy
(RE, normalized by log2(8)); mean output entropy from generated_tokens.json as sensitivity.
"""
import argparse, json, pathlib, sys
import numpy as np

EXPERT, LAYER = 114, 14

def load_prompt(pdir):
    apn = np.load(pdir / "residual" / f"attn_post_norm-{LAYER}.npy")
    log = np.load(pdir / "router" / f"ffn_moe_logits-{LAYER}.npy")
    assert apn.shape[0] == log.shape[0], pdir
    meta = {}
    for line in (pdir / "metadata.txt").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1); meta[k] = v
    n_gen = int(meta.get("n_tokens_generated", 0))
    gtoks = json.loads((pdir / "generated_tokens.json").read_text(errors="replace")) if (pdir / "generated_tokens.json").exists() else []  # tolerant decode: BPE-split multibyte pieces; affects decoded text only, never npy/ids (2026-07-03)
    return apn, log, n_gen, gtoks

def recover(dirs):
    X = np.concatenate([a for a, _, _, _ in dirs.values()])
    y = np.concatenate([l[:, EXPERT] for _, l, _, _ in dirs.values()])
    Xb = np.hstack([X, np.ones((len(X), 1), dtype=X.dtype)])
    sol, *_ = np.linalg.lstsq(Xb.astype(np.float64), y.astype(np.float64), rcond=None)
    w, b = sol[:-1], sol[-1]
    rel = np.linalg.norm(Xb @ sol - y) / np.linalg.norm(y)
    return w, b, rel

def fourgram_rep(ids):
    if len(ids) < 8: return 0.0
    grams = [tuple(ids[i:i+4]) for i in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)

def routing_cols(log_gen):
    z = log_gen - log_gen.max(axis=1, keepdims=True)
    p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
    top8 = np.argsort(-p, axis=1)[:, :8]
    sel = (top8 == EXPERT).any(axis=1)
    q = []
    for r in range(len(p)):
        pr = p[r, top8[r]]; pr = pr / pr.sum()
        if sel[r]: q.append(pr[top8[r] == EXPERT][0])
    re = []
    for r in range(len(p)):
        pr = p[r, top8[r]]; pr = pr / pr.sum()
        re.append(float(-(pr * np.log2(pr)).sum() / np.log2(8)))
    return dict(S=float(sel.mean()), Q=float(np.mean(q)) if q else 0.0,
                W=float(sel.mean()) * (float(np.mean(q)) if q else 0.0),
                mean_routing_entropy=float(np.mean(re)))

def analyze(cap_dir, w):
    out = {}
    for pdir in sorted(p for p in pathlib.Path(cap_dir).iterdir() if p.is_dir()):
        apn, log, n_gen, gtoks = load_prompt(pdir)
        gen_apn, gen_log = apn[-n_gen:] if n_gen else apn[:0], log[-n_gen:] if n_gen else log[:0]
        ids = [t["token_id"] for t in gtoks]
        win = slice(0, 128)
        flags = []
        if n_gen < 32: flags.append("TRUNCATED")
        if fourgram_rep(ids[win]) > 0.5: flags.append("DEGENERATE")
        proj = gen_apn @ w
        r = dict(n_gen=n_gen, flags=flags,
                 w114_proj_1_128=float(proj[win].mean()) if n_gen else None,
                 w114_proj_1_64=float(proj[:64].mean()) if n_gen else None,
                 w114_proj_full=float(proj.mean()) if n_gen else None,
                 fourgram_rep=round(fourgram_rep(ids[win]), 4),
                 mean_output_entropy=float(np.mean([t["output_entropy"] for t in gtoks[:128]])) if gtoks else None)
        if n_gen: r.update(routing_cols(gen_log[win]))
        out[pdir.name] = r
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heldout"); ap.add_argument("--s4")
    ap.add_argument("--classes", help="heldout_classes.tsv for the positive control")
    ap.add_argument("--override-ratings-gate", action="store_true")
    a = ap.parse_args()
    here = pathlib.Path(__file__).resolve().parent

    if a.s4 and not a.override_ratings_gate:
        if not any((here / n).exists() or (here.parent / "prework" / n).exists()
                   for n in ("ratings_v1.json",)):
            sys.exit("REFUSING --s4: ratings_v1.json not found. Ratings lock BEFORE projections "
                     "(4_capture_config_v1.md). Use --override-ratings-gate only with cause; it is logged.")

    cap = pathlib.Path(a.heldout or a.s4)
    dirs = {p.name: load_prompt(p) for p in sorted(cap.iterdir()) if p.is_dir()}
    w, b, rel = recover(dirs)
    print(f"w114 recovered: rel residual {rel:.2e} (gate < 1e-3: {'PASS' if rel < 1e-3 else 'FAIL'})")
    if rel >= 1e-3: sys.exit("RECOVERY GATE FAILED — investigate before proceeding")
    np.save(here / "w114.npy", w)
    (here / "w114_meta.json").write_text(json.dumps(
        {"w114": w.tolist(), "bias": float(b), "rel_residual": rel,
         "recovered_from": str(cap), "layer": LAYER, "expert": EXPERT}))

    res = analyze(cap, w)
    tag = "heldout" if a.heldout else "s4"
    payload = {"mode": tag, "rel_residual": rel, "bias": float(b),
               "ratings_gate_overridden": bool(a.s4 and a.override_ratings_gate), "results": res}

    if a.heldout and a.classes:
        cls = dict(l.split("\t") for l in pathlib.Path(a.classes).read_text().splitlines() if l)
        fire = [r["w114_proj_1_128"] for k, r in res.items() if cls.get(k) == "fire" and r["w114_proj_1_128"] is not None]
        nof  = [r["w114_proj_1_128"] for k, r in res.items() if cls.get(k) == "nofire" and r["w114_proj_1_128"] is not None]
        m1, m2 = np.mean(fire), np.mean(nof)
        sp = np.sqrt((np.var(fire, ddof=1) + np.var(nof, ddof=1)) / 2)
        d = (m1 - m2) / sp
        overlap = (min(fire) <= max(nof)) if (m1 > m2) else (min(nof) <= max(fire))
        payload["positive_control"] = dict(
            d=round(float(d), 3), fire_mean=round(float(m1), 5), nofire_mean=round(float(m2), 5),
            direction_ok=bool(m1 > m2), range_overlap=bool(overlap),
            gate="PASS" if (m1 > m2 and d > 1.0) else "FAIL")
        print(f"POSITIVE CONTROL: d={d:.2f} fire>{'nofire' if m1>m2 else '!!nofire!!'} "
              f"overlap={overlap} -> {payload['positive_control']['gate']}")

    out = here / f"{tag}_results.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
