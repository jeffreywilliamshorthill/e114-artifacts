#!/usr/bin/env python3
"""S6c all-expert register/control sweep — frozen spec: prework/6c_sweep_spec.md.

Implements, per surface (base / hauhau / agentworld — NEVER pooled):
  For each of the 256x40 (expert, layer) positions, recover the per-expert linear gate
  axis w_e by least squares from that position's (residual attn_post_norm-L, router
  logit column ffn_moe_logits-L[:,e]) pairs; project residuals onto w_e.
  PRIMARY metric: Cohen's d on the w_e projection between the 10 register-positive (F*)
  and 10 control (N*) GENERATIONS (per-prompt mean over the trimmed generated track,
  pooled-SD d, the d=3.88 statistic generalized).
  Realized-W separation = SECONDARY column only (top-k zeroing inflates it).

Conventions inherited verbatim from the program's canonical implementation
(legs/recover_w114.py, which implements the frozen 4_capture_config_v1.md):
  - lstsq with intercept: [X | 1] @ [w; b] ~= logits[:, e]; recovery pooled over ALL
    captured rows (prefill + generation, untrimmed) — the router map is exactly linear,
    so extra rows only condition the solve.
  - rel_resid = ||fit - y|| / ||y|| per expert column; gate < 1e-3
    (entries above the gate are flagged logits_only).
  - Projection uses w only (no bias; Cohen's d is invariant to the intercept anyway).
  - Cohen's d = (mean_F - mean_N) / sqrt((var_F + var_N)/2), ddof=1 (10 v 10).
  - Generated track = LAST n_gen rows of every tensor (layer 39 carries only the final
    prefill position -> rows n_gen+1; all other layers rows n_prompt+n_gen).
  - Trim at first literal <|im_start|> / <|im_end|> / <|endoftext|> in DECODED text
    (established rule; base emits <|im_end|> as a BPE-literal 6-token sequence, never
    the single token 248046, so token-id scans would be silent no-ops).

Ranking: the spec says "Rank all 10,240 positions by d". Read strictly, an
anti-register separator (large negative d) also "separates"; we therefore emit BOTH
rank_abs (by |d|, the stricter/headline baseline) and rank_signed (by d descending).

Outputs (all NEW files under prework/6c_results/):
  ranking_full.json
  6c_register_control_sweep_{base,hauhau,agentworld}.json  (spec-named deliverable)
"""
import datetime
import hashlib
import json
import pathlib

import numpy as np

ROOT = pathlib.Path("/Volumes/ExternalSSD/e114-construction-reframe")
OUT = ROOT / "prework" / "6c_results"
SURFACES = ["base", "hauhau", "agentworld"]
MARKERS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
N_LAYERS, N_EXPERTS, D_MODEL = 40, 256, 2048
REL_RESID_GATE = 1e-3


def sha256_file(path, block=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def trim_n(raw_text, pieces):
    """Established rule: cut decoded text at first literal marker; count whole pieces
    that fit strictly before the cut. Returns n_trim tokens."""
    cut = len(raw_text)
    for m in MARKERS:
        i = raw_text.find(m)
        if i != -1:
            cut = min(cut, i)
    n_trim, acc = 0, 0
    for pc in pieces:
        if acc + len(pc) > cut:
            break
        acc += len(pc)
        n_trim += 1
    return n_trim


def fourgram_rep(ids):
    if len(ids) < 8:
        return 0.0
    grams = [tuple(ids[i : i + 4]) for i in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)


def load_prompt_meta(pdir):
    meta = {}
    for line in (pdir / "metadata.txt").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            meta[k] = v
    gtoks = json.loads((pdir / "generated_tokens.json").read_text())
    text = (pdir / "generated_text.txt").read_text()
    pieces = [t["piece"] for t in gtoks]
    ids = [t["token_id"] for t in gtoks]
    n_gen = int(meta["n_tokens_generated"])
    n_prompt = int(meta["n_tokens_prompt"])
    assert len(pieces) == n_gen, (pdir, len(pieces), n_gen)
    assert "".join(pieces) == text, f"piece concat != text for {pdir}"
    nt = trim_n(text, pieces)
    return dict(
        n_prompt=n_prompt,
        n_gen=n_gen,
        n_trim=nt,
        trimmed=nt < n_gen,
        truncated=nt < 32,
        fourgram_rep=round(fourgram_rep(ids[:nt]), 4),
    )


def cohens_d(fire_vals, nofire_vals):
    """(m_F - m_N)/sqrt((var_F+var_N)/2), ddof=1 — canonical program convention."""
    m1, m2 = fire_vals.mean(axis=0), nofire_vals.mean(axis=0)
    sp = np.sqrt((fire_vals.var(axis=0, ddof=1) + nofire_vals.var(axis=0, ddof=1)) / 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        d = (m1 - m2) / sp
    # sp==0 & diff==0 (e.g. expert never routed in either class) -> define d = 0
    d = np.where((sp == 0) & (m1 == m2), 0.0, d)
    return d


def realized_w_means(logits_trimmed):
    """softmax-256 -> top-8 -> renorm -> realized weight (0 if unselected); mean over rows.
    Matches routing_cols() in legs/recover_w114.py, vectorized over all experts."""
    z = logits_trimmed - logits_trimmed.max(axis=1, keepdims=True)
    p = np.exp(z)
    p /= p.sum(axis=1, keepdims=True)
    idx8 = np.argpartition(-p, 8, axis=1)[:, :8]
    mask = np.zeros_like(p, dtype=bool)
    np.put_along_axis(mask, idx8, True, axis=1)
    pw = np.where(mask, p, 0.0)
    pw /= pw.sum(axis=1, keepdims=True)
    return pw.mean(axis=0)  # (256,)


def process_surface(surf):
    cap = ROOT / f"cap_6c_{surf}"
    pids = sorted(p.name for p in cap.iterdir() if p.is_dir())
    assert pids == [f"F{i:02d}" for i in range(1, 11)] + [f"N{i:02d}" for i in range(1, 11)]
    fire_idx = np.array([i for i, p in enumerate(pids) if p.startswith("F")])
    nof_idx = np.array([i for i, p in enumerate(pids) if p.startswith("N")])
    meta = {pid: load_prompt_meta(cap / pid) for pid in pids}

    d_proj = np.zeros((N_LAYERS, N_EXPERTS))
    d_proj_w128 = np.zeros((N_LAYERS, N_EXPERTS))
    d_realW = np.zeros((N_LAYERS, N_EXPERTS))
    rel_resid = np.zeros((N_LAYERS, N_EXPERTS))
    n_rows_recovery = np.zeros(N_LAYERS, dtype=int)
    lstsq_rank = np.zeros(N_LAYERS, dtype=int)

    for L in range(N_LAYERS):
        Xs, Ys, gen_slices = [], [], []
        for pid in pids:
            r = np.load(cap / pid / "residual" / f"attn_post_norm-{L}.npy")
            g = np.load(cap / pid / "router" / f"ffn_moe_logits-{L}.npy")
            m = meta[pid]
            exp_rows = (m["n_gen"] + 1) if L == N_LAYERS - 1 else (m["n_prompt"] + m["n_gen"])
            assert r.shape == (exp_rows, D_MODEL) and g.shape == (exp_rows, N_EXPERTS), (surf, pid, L)
            Xs.append(r)
            Ys.append(g)
        X = np.concatenate(Xs).astype(np.float64)
        Y = np.concatenate(Ys).astype(np.float64)
        Xb = np.hstack([X, np.ones((len(X), 1))])
        sol, _, rank, _ = np.linalg.lstsq(Xb, Y, rcond=None)
        rel_resid[L] = np.linalg.norm(Xb @ sol - Y, axis=0) / np.linalg.norm(Y, axis=0)
        n_rows_recovery[L] = len(X)
        lstsq_rank[L] = rank
        W = sol[:-1]  # (2048, 256) — projection uses w only, bias dropped (canonical)

        pm_full = np.zeros((len(pids), N_EXPERTS))  # per-prompt mean projection, full trimmed track
        pm_128 = np.zeros((len(pids), N_EXPERTS))  # sensitivity: trimmed track window 1..128
        pm_realW = np.zeros((len(pids), N_EXPERTS))
        for i, pid in enumerate(pids):
            m = meta[pid]
            gen_r = Xs[i][-m["n_gen"] :][: m["n_trim"]].astype(np.float64)
            gen_g = Ys[i][-m["n_gen"] :][: m["n_trim"]].astype(np.float64)
            assert len(gen_r) > 0, (surf, pid, "empty trimmed track")
            proj = gen_r @ W
            pm_full[i] = proj.mean(axis=0)
            pm_128[i] = proj[:128].mean(axis=0)
            pm_realW[i] = realized_w_means(gen_g)

        d_proj[L] = cohens_d(pm_full[fire_idx], pm_full[nof_idx])
        d_proj_w128[L] = cohens_d(pm_128[fire_idx], pm_128[nof_idx])
        d_realW[L] = cohens_d(pm_realW[fire_idx], pm_realW[nof_idx])
        print(f"  {surf} L{L:02d} rows={len(X)} rank={rank} max_rel={rel_resid[L].max():.2e} "
              f"top|d|={np.nanmax(np.abs(d_proj[L])):.2f}@e{int(np.nanargmax(np.abs(d_proj[L])))}",
              flush=True)

    flat_d = d_proj.reshape(-1)
    order_abs = np.argsort(-np.abs(flat_d), kind="stable")
    order_signed = np.argsort(-flat_d, kind="stable")
    rank_abs = np.empty(flat_d.size, dtype=int)
    rank_abs[order_abs] = np.arange(1, flat_d.size + 1)
    rank_signed = np.empty(flat_d.size, dtype=int)
    rank_signed[order_signed] = np.arange(1, flat_d.size + 1)

    entries = []
    for flat in order_abs:
        L, e = divmod(int(flat), N_EXPERTS)
        entries.append(dict(
            layer=L,
            expert=e,
            d=round(float(d_proj[L, e]), 4),
            rank_abs=int(rank_abs[flat]),
            rank_signed=int(rank_signed[flat]),
            d_w128=round(float(d_proj_w128[L, e]), 4),
            d_realized_W_secondary=round(float(d_realW[L, e]), 4),
            rel_resid=float(f"{rel_resid[L, e]:.3e}"),
            logits_only=bool(rel_resid[L, e] > REL_RESID_GATE),
        ))

    diag = dict(
        n_prompts=len(pids),
        prompt_meta={pid: meta[pid] for pid in pids},
        n_rows_recovery_per_layer=n_rows_recovery.tolist(),
        lstsq_rank_per_layer=lstsq_rank.tolist(),
        rel_resid_max_overall=float(f"{rel_resid.max():.3e}"),
        n_positions_logits_only=int((rel_resid > REL_RESID_GATE).sum()),
    )
    return entries, diag


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    provenance = dict(
        spec="prework/6c_sweep_spec.md",
        spec_sha256=sha256_file(ROOT / "prework" / "6c_sweep_spec.md"),
        heldout_classes_sha256=sha256_file(ROOT / "prework" / "heldout_classes.tsv"),
        heldout_prompts_sha256=sha256_file(ROOT / "prework" / "heldout_prompts.tsv"),
        capture_tarballs={
            f"leg4_6c_{s}.tgz": sha256_file(ROOT / f"leg4_6c_{s}.tgz") for s in SURFACES
        },
        generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    )
    print("provenance hashed", flush=True)

    header = dict(
        primary_metric=(
            "Cohen's d (10 fire v 10 nofire per-prompt means, pooled SD) on the projection of "
            "the trimmed generated-track residual onto the least-squares-recovered per-expert "
            "gate axis w_e — NEVER realized W (secondary column only)"
        ),
        track="generated track = last n_gen rows; trimmed at first literal "
              "<|im_start|>/<|im_end|>/<|endoftext|> in decoded text",
        recovery="lstsq [X|1]@[w;b]~=logit_e over all captured rows (prefill+gen, untrimmed), "
                 "pooled across the 20 prompts, per layer; projection uses w only",
        rel_resid_gate=REL_RESID_GATE,
        ranking="rank_abs = |d| descending (headline / stricter); rank_signed = d descending "
                "(spec-literal). Spec text 'rank by d' is ambiguous on sign; both reported.",
        d_w128="sensitivity only: same d on window 1..128 of the trimmed track "
               "(the 4_capture_config_v1 primary window)",
        provenance=provenance,
    )

    full = dict(header=header, surfaces={})
    for surf in SURFACES:
        print(f"== {surf} ==", flush=True)
        entries, diag = process_surface(surf)
        full["surfaces"][surf] = dict(diagnostics=diag, entries=entries)
        # spec-named per-model deliverable
        e114_l14 = next(x for x in entries if x["layer"] == 14 and x["expert"] == 114)
        e114_l26 = next(x for x in entries if x["layer"] == 26 and x["expert"] == 114)
        spec_payload = dict(
            header=header,
            surface=surf,
            e114_L14=e114_l14,
            e114_L26=e114_l26,
            top_30=entries[:30],
            diagnostics=diag,
            ranked_table=entries,
        )
        (OUT / f"6c_register_control_sweep_{surf}.json").write_text(
            json.dumps(spec_payload, indent=1))
        print(f"  E114@L14: d={e114_l14['d']} rank_abs={e114_l14['rank_abs']} "
              f"rank_signed={e114_l14['rank_signed']}", flush=True)

    (OUT / "ranking_full.json").write_text(json.dumps(full, indent=1))
    print("wrote", OUT / "ranking_full.json")


if __name__ == "__main__":
    main()
