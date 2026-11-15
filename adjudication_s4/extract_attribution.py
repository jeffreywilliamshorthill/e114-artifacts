#!/usr/bin/env python3
"""Leg 3 — norm-folded writer attribution onto the w114 router logit (runs ON the box).

Per lit_recon_actions_v1.md item 1: raw dot-products through an unfolded RMSNorm are
invalid. Here the direct path is fully reconstructable offline, so we compute BOTH:
  - linearized attribution:  w114 · (γ ⊙ c) / rms(x)      (frozen-norm approximation)
  - EXACT direct-effect ablation:  logit(x) − logit(x − c) where logit(v) = w114·RMSNorm_γ(v)+b
    (the RMSNorm is the only nonlinearity between residual components and this logit,
     so numpy ablation is exact for the DIRECT path; routing-mediated indirect effects
     are a separate question handled by the patching legs.)

Input: a capture_activations output dir (l_out-L, attn_out-L, ffn_out-L, ffn_moe_logits-L
per layer). Components attributed: attn_out-0..14, ffn_out-0..13, embed-remainder.
Reconstruction: x = l_out-13 + attn_out-14 (residual entering L14's post-attn norm);
VALIDATED per token against the captured ffn_moe_logits-14[:,114] (gate: r > 0.999).
γ and eps read from the GGUF via gguf-py; w114/b from w114_meta.json (pushed after Leg 2).

Output: attribution_<capdir>.json — per prompt, per component: mean linearized attribution
and mean exact ablation over generated tokens, + top10-dim share (concentration diagnostic).
Small JSON; raw npy can be deleted after this runs.
"""
import json, pathlib, sys
import numpy as np

LAYER, EXPERT = 14, 114
GGUF = "/workspace/models/base-bf16.gguf"

def load_gamma_eps():
    sys.path.insert(0, "/workspace/llama.cpp.new/gguf-py")
    from gguf import GGUFReader
    r = GGUFReader(GGUF)
    gamma = None
    for t in r.tensors:
        if t.name == f"blk.{LAYER}.post_attention_norm.weight":
            gamma = np.array(t.data, dtype=np.float32)
    kv = {f.name: f for f in r.fields.values()}
    eps_field = kv.get("qwen35moe.attention.layer_norm_rms_epsilon")
    eps = float(eps_field.contents()) if eps_field else 1e-6
    assert gamma is not None, "post_attention_norm.weight not found"
    return gamma, eps

def rmsnorm(v, gamma, eps):
    return gamma * v / np.sqrt((v * v).mean(axis=-1, keepdims=True) + eps)

def main(cap_dir, w114_meta):
    cap = pathlib.Path(cap_dir)
    meta = json.loads(pathlib.Path(w114_meta).read_text())
    w = np.array(meta["w114"], dtype=np.float64); b = float(meta["bias"])
    gamma, eps = load_gamma_eps()
    gw = (gamma.astype(np.float64) * w)          # fold gamma into the readout once

    out = {}
    for pdir in sorted(p for p in cap.iterdir() if p.is_dir()):
        res = pdir / "layers"; rou = pdir / "router"   # capture_activations layout
        def L(name):
            f = res / f"{name}.npy"
            return np.load(f).astype(np.float64) if f.exists() else None
        # Telescoping decomposition in residual space — avoids per-head attn_output tensors
        # (which are (tokens*heads, head_dim), not residual contributions):
        #   attn contribution at layer l = l_out(l) - l_out(l-1) - ffn_out(l)
        #   residual read by L14's post-attn norm: x = l_out(14) - ffn_out(14)
        # Components sum to x EXACTLY by construction; the recon gate validates the identity.
        lo = {l: L(f"l_out-{l}") for l in range(LAYER + 1)}
        fo = {l: L(f"ffn_out-{l}") for l in range(LAYER + 1)}
        missing = [f"{n}-{l}" for n, d in (("l_out", lo), ("ffn_out", fo)) for l, v in d.items() if v is None]
        if missing:
            have = sorted(f.name for f in res.glob("*.npy"))[:12] if res.exists() else "(no layers dir)"
            raise SystemExit(f"ABORT {pdir.name}: missing {missing[:6]}; layers/ has: {have}")
        comps = {"embed+attn-0": lo[0] - fo[0], "ffn_out-0": fo[0]}
        for l in range(1, LAYER):
            comps[f"attn-{l}"] = lo[l] - lo[l - 1] - fo[l]
            comps[f"ffn_out-{l}"] = fo[l]
        x = lo[LAYER] - fo[LAYER]
        comps[f"attn-{LAYER}"] = x - lo[LAYER - 1]

        # end-to-end validation against the captured router logit
        logit_true = np.load(rou / f"ffn_moe_logits-{LAYER}.npy").astype(np.float64)[:, EXPERT]
        logit_rec = rmsnorm(x, gamma, eps) @ w + b
        r = np.corrcoef(logit_true, logit_rec)[0, 1]
        rms_x = np.sqrt((x * x).mean(axis=-1, keepdims=True) + eps)

        n_gen = sum(1 for _ in json.loads((pdir / "generated_tokens.json").read_text(errors="replace"))) \
                if (pdir / "generated_tokens.json").exists() else 0
        g = slice(len(x) - n_gen, len(x)) if n_gen else slice(0, len(x))

        rows = {}
        for name, c in comps.items():
            lin = (c[g] @ gw) / rms_x[g].squeeze(-1)
            abl = (rmsnorm(x[g], gamma, eps) @ w) - (rmsnorm(x[g] - c[g], gamma, eps) @ w)
            contrib = c[g] * gw                   # per-dim share of the linearized term
            top10 = np.sort(np.abs(contrib), axis=1)[:, -10:].sum(1) / (np.abs(contrib).sum(1) + 1e-12)
            rows[name] = dict(lin_mean=float(lin.mean()), abl_mean=float(abl.mean()),
                              lin_abl_ratio=float(lin.mean() / abl.mean()) if abs(abl.mean()) > 1e-9 else None,
                              top10_dim_share=float(top10.mean()))
        out[pdir.name] = dict(recon_r=round(float(r), 6), n_gen=n_gen, components=rows)
        print(f"  {pdir.name}: recon r={r:.5f} ({'OK' if r > 0.999 else 'FAIL'}), {len(comps)} components")

    dst = pathlib.Path(f"/workspace/attribution_{cap.name}.json")
    dst.write_text(json.dumps(out, indent=2))
    print(f"wrote {dst}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "/workspace/prework/w114_meta.json")
