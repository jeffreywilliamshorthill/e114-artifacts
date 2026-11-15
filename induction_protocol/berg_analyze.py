#!/usr/bin/env python3
"""Berg suite: input -> output + FULL router/expert metrics per capture, base + hauhau.
Per row and track (prefill-content, gen-full): w114 proj (L14), E114 S/Q/W at L14 and L26,
active-expert counts, and top-8 experts by top-8 selection rate at L14/L26 (gen track, plus
prefill roster for inductions). Emits BERG_RESULTS.md + berg_metrics.csv."""
import csv, json, os, re
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
AS = os.path.dirname(D)
P = json.load(open(f"{D}/berg_prompts.json"))
LABEL = P["_labels"]
TOPK, EXPERT = 8, 114
IND = list(P["inductions"])          # IND_A..IND_E, IND_HIST, IND_CONC
QRY = list(P["queries"])             # QEXP QBIN QADJ

def load(pdir, layer, kind):
    a = np.load(f"{pdir}/{kind}/{'attn_post_norm' if kind=='residual' else 'ffn_moe_logits'}-{layer}.npy")
    return a.astype(np.float64)

def spans(pdir):
    meta = dict(re.findall(r"^(\S+)\s*[:=]\s*(.*)$", open(f"{pdir}/metadata.txt").read(), re.M))
    n_gen = int(meta.get("n_tokens_generated", 0))
    ptok = json.loads(open(f"{pdir}/prompt_tokens.json", errors="replace").read())
    if ptok and isinstance(ptok[0], dict): ptok = [t["token_id"] for t in ptok]
    im = ptok[0]; last = max(i for i, t in enumerate(ptok) if t == im)
    n_pre = len(ptok)
    return slice(3, max(3, last - 1)), slice(n_pre, n_pre + n_gen), n_gen

def sq(lg):
    if lg.shape[0] == 0: return 0.0, 0.0
    x = lg - lg.max(axis=1, keepdims=True)
    p = np.exp(x); p /= p.sum(axis=1, keepdims=True)
    idx = np.argpartition(-p, TOPK-1, axis=1)[:, :TOPK]
    sel = (idx == EXPERT).any(axis=1)
    S = float(sel.mean())
    if not sel.any(): return S, 0.0
    ps = p[sel]; top = np.take_along_axis(ps, idx[sel], axis=1)
    return S, float((ps[np.arange(len(ps)), EXPERT] / top.sum(axis=1)).mean())

def roster(lg, n=8):
    if lg.shape[0] == 0: return "—", 0
    idx = np.argpartition(-lg, TOPK-1, axis=1)[:, :TOPK]
    m = np.zeros(lg.shape, bool); np.put_along_axis(m, idx, True, axis=1)
    r = m.mean(axis=0)
    order = np.argsort(-r)[:n]
    return "  ".join(f"E{e}({r[e]:.2f})" for e in order), int((r > 0).sum())

def gtxt(pdir):
    try: return open(f"{pdir}/generated_text.txt", errors="replace").read().strip() or "(empty)"
    except FileNotFoundError: return "(missing)"

def metrics(pdir, w):
    apn = load(pdir, 14, "residual")
    lg14 = load(pdir, 14, "router"); lg26 = load(pdir, 26, "router")
    pre, gen, n_gen = spans(pdir)
    out = {}
    for tr, sl in (("pre", pre), ("gen", gen)):
        pr = apn[sl] @ w
        S14, Q14 = sq(lg14[sl]); S26, Q26 = sq(lg26[sl])
        ro14, act14 = roster(lg14[sl]); ro26, act26 = roster(lg26[sl])
        out[tr] = dict(n=int(pr.shape[0]), proj=float(pr.mean()) if pr.shape[0] else float("nan"),
                       S14=S14, Q14=Q14, W14=S14*Q14, S26=S26, Q26=Q26, W26=S26*Q26,
                       roster14=ro14, act14=act14, roster26=ro26, act26=act26)
    return out, n_gen

def block(surf, pdir, w, show_pre_roster):
    m, n_gen = metrics(pdir, w)
    t = gtxt(pdir)
    L = [f"**{surf} →** {t}", ""]
    g, p = m["gen"], m["pre"]
    L.append(f"- gen (n={g['n']}): proj **{g['proj']:.3f}** · E114 L14 S {g['S14']:.2f} Q {g['Q14']:.3f} W {g['W14']:.3f} · L26 S {g['S26']:.2f} W {g['W26']:.3f} · active L14/L26 {g['act14']}/{g['act26']}")
    L.append(f"  - top L14: {g['roster14']}")
    L.append(f"  - top L26: {g['roster26']}")
    L.append(f"- prefill (n={p['n']}): proj {p['proj']:.3f} · E114 L14 S {p['S14']:.2f} · L26 S {p['S26']:.2f}")
    if show_pre_roster: L.append(f"  - top L14 (prefill): {p['roster14']}")
    L.append("")
    return L, m, n_gen

def main():
    rows = []
    out = ["# Berg suite (arXiv 2510.24797) — verbatim, base + hauhau, greedy -n 256",
           "Protocol: induction → greedy continuation → query as separate turn → response "
           "(paper four-step; paper temp 0.5, ours temp 0). Full texts: berg_prompts.json.",
           "proj = attn_post_norm-14 @ w114_surface. S/Q/W = top-8 router softmax. "
           "Rosters = experts by top-8 selection rate (rate in parens).", ""]
    W = {s: np.load(f"{AS}/w114_{s}.npy") for s in ("base", "hauhau")}
    for ik in IND:
        out += [f"## {ik} — {LABEL[ik]}", f"> {P['inductions'][ik]}", "", "### continuation (phase 1)"]
        for surf in ("base", "hauhau"):
            pdir = f"{D}/raw/cap_berg1_{surf}/{ik}"
            L, m, n_gen = block(surf, pdir, W[surf], show_pre_roster=True)
            out += L
            rows.append(dict(row=ik, phase=1, surface=surf, n_gen=n_gen,
                             **{f"{t}_{k}": v for t, d in m.items() for k, v in d.items() if not k.startswith("roster")}))
        for qk in QRY:
            out += [f"### + {qk} — {LABEL[qk]}"]
            for surf in ("base", "hauhau"):
                pdir = f"{D}/raw/cap_berg2_{surf}/{ik}_{qk}"
                L, m, n_gen = block(surf, pdir, W[surf], show_pre_roster=False)
                out += L
                rows.append(dict(row=f"{ik}_{qk}", phase=2, surface=surf, n_gen=n_gen,
                                 **{f"{t}_{k}": v for t, d in m.items() for k, v in d.items() if not k.startswith("roster")}))
    out += ["## Zero-shot (no induction)"]
    for qk in QRY:
        out += [f"### ZS_{qk} — {LABEL[qk]}", f"> {P['queries'][qk]}", ""]
        for surf in ("base", "hauhau"):
            pdir = f"{D}/raw/cap_berg1_{surf}/ZS_{qk}"
            L, m, n_gen = block(surf, pdir, W[surf], show_pre_roster=False)
            out += L
            rows.append(dict(row=f"ZS_{qk}", phase=1, surface=surf, n_gen=n_gen,
                             **{f"{t}_{k}": v for t, d in m.items() for k, v in d.items() if not k.startswith("roster")}))
    with open(f"{D}/berg_metrics.csv", "w", newline="") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wcsv.writeheader(); wcsv.writerows(rows)
    open(f"{D}/BERG_RESULTS.md", "w").write("\n".join(out))
    print(f"{len(rows)} capture-rows -> BERG_RESULTS.md + berg_metrics.csv")

if __name__ == "__main__":
    main()
