#!/usr/bin/env python3
"""Leg 5 — deception/roleplay SAE discovery + co-activation (runs ON the box, GPU).
Implements deception_roleplay_spec_v1.md Steps 1-3 (predictions frozen 2026-07-01).

Step 1 discovery: teacher-force the 36 H/R/D probe texts through base HF bf16; encode
resid_post at layers 12-16 & 24-28 with Qwen-Scope SAEs (relu->TopK50, conventions from
encode_resid_sae.py); rank features by (R-H) and (D-H) mean-activation contrast.
Step 2 geometric: cosine(w114, W_dec column) for every candidate (cross-space caveat applies).
Step 3 co-activation: re-forward the EXACT token ids of cap_heldout_base (20) + cap_s4 (48)
captures; record per-token L14/L26 activations for all candidate features.

Outputs under /workspace/leg5_out/: discovery.json, coact_heldout.npz, coact_s4.npz, ids.json
"""
import json, pathlib, sys
import numpy as np
import torch

WORK = pathlib.Path("/workspace")
SAE_DIR = WORK / "saes"
OUT = WORK / "leg5_out"; OUT.mkdir(exist_ok=True)
DISC_LAYERS = [12, 13, 14, 15, 16, 24, 25, 26, 27, 28]
COACT_LAYERS = [14, 26]
TOPK, NTOP = 50, 20

def log(*a): print(*a, flush=True)

def sae_weights(layer):
    obj = torch.load(SAE_DIR / f"layer{layer}.sae.pt", map_location="cpu")
    st = obj if isinstance(obj, dict) and any("enc" in k.lower() for k in obj) else obj.get("state_dict", obj)
    def find(names):
        for n in names:
            for k in st:
                if k.lower() == n: return st[k]
        return None
    W_enc, b_enc = find(["w_enc", "encoder.weight"]), find(["b_enc", "encoder.bias"])
    W_dec = find(["w_dec", "decoder.weight"])
    if W_enc.shape[0] != b_enc.shape[0]: W_enc = W_enc.t()
    if W_dec is not None and W_dec.shape[0] != b_enc.shape[0]: W_dec = W_dec.t()
    return W_enc.float(), b_enc.float(), (W_dec.float() if W_dec is not None else None)

def topk_acts(resid, W_enc, b_enc):
    """resid [T,2048] float32 cuda -> sparse TopK50 acts [T, n_feat] (dense float32, zeros elsewhere)"""
    a = torch.relu(resid @ W_enc.T + b_enc)
    v, i = torch.topk(a, TOPK, dim=-1)
    out = torch.zeros_like(a)
    out.scatter_(1, i, v)
    return out

def main():
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained("/workspace/models/base-safetensors")
    log("loading base model bf16...")
    model = AutoModelForCausalLM.from_pretrained("/workspace/models/base-safetensors",
            torch_dtype=torch.bfloat16, device_map="cuda", low_cpu_mem_usage=True, trust_remote_code=True)
    model.eval()

    # ---------- Step 1: probe forwards, collect resid at all discovery layers ----------
    rows = [l.split("\t") for l in (WORK / "prework/deception_probe_prompts_v1.tsv").read_text().splitlines() if l]
    conds = {pid: c for pid, c, _ in rows}
    resids = {L: {} for L in DISC_LAYERS}     # layer -> pid -> [T,2048] cpu
    for pid, cond, text in rows:
        ids = tok(text, return_tensors="pt", add_special_tokens=True).input_ids.to("cuda")
        with torch.no_grad():
            hs = model(ids, output_hidden_states=True, use_cache=False).hidden_states
        for L in DISC_LAYERS:
            resids[L][pid] = hs[L + 1][0].float().cpu()
        log(f"  probe {pid} ({cond}) {ids.shape[1]} tok")

    w114 = torch.tensor(json.loads((WORK / "prework/w114_meta.json").read_text())["w114"], dtype=torch.float32)
    w114n = w114 / w114.norm()

    discovery = {}
    candidates = {L: set() for L in COACT_LAYERS}
    for L in DISC_LAYERS:
        W_enc, b_enc, W_dec = sae_weights(L)
        W_enc_c, b_enc_c = W_enc.cuda(), b_enc.cuda()
        per_text = {}
        for pid, r in resids[L].items():
            acts = topk_acts(r.cuda(), W_enc_c, b_enc_c)
            per_text[pid] = acts.mean(0).cpu()          # [n_feat] mean act per text
        M = {c: torch.stack([per_text[p] for p in per_text if conds[p] == c]) for c in ("honest", "roleplay", "deception")}
        fired = {c: (M[c] > 0).sum(0) for c in M}
        entry = {}
        for cname, pos in (("roleplay_vs_honest", "roleplay"), ("deception_vs_honest", "deception")):
            diff = M[pos].mean(0) - M["honest"].mean(0)
            ok = fired[pos] >= 3
            diff_m = torch.where(ok, diff, torch.full_like(diff, -1e9))
            v, idx = torch.topk(diff_m, NTOP)
            feats = []
            for val, fi in zip(v.tolist(), idx.tolist()):
                if val <= 0: continue
                cos = float(torch.dot(W_dec[fi] / (W_dec[fi].norm() + 1e-8), w114n)) if W_dec is not None else None
                feats.append(dict(feature=fi, diff=round(val, 4),
                                  mean_honest=round(float(M['honest'].mean(0)[fi]), 4),
                                  mean_roleplay=round(float(M['roleplay'].mean(0)[fi]), 4),
                                  mean_deception=round(float(M['deception'].mean(0)[fi]), 4),
                                  fired_pos=int(fired[pos][fi]), cos_w114=None if cos is None else round(cos, 4)))
                if L in COACT_LAYERS: candidates[L].add(fi)
            entry[cname] = feats
        discovery[L] = entry
        log(f"L{L}: top roleplay {[f['feature'] for f in entry['roleplay_vs_honest'][:5]]} "
            f"top deception {[f['feature'] for f in entry['deception_vs_honest'][:5]]}")
        del W_enc_c, b_enc_c
    (OUT / "discovery.json").write_text(json.dumps(discovery, indent=1))

    # ---------- Step 3: co-activation on exact capture token ids ----------
    for capname in ("cap_heldout_base", "cap_s4"):
        cap = WORK / capname
        cand = {L: sorted(candidates[L]) for L in COACT_LAYERS}
        sae = {L: sae_weights(L) for L in COACT_LAYERS}
        store = {L: {} for L in COACT_LAYERS}
        for pdir in sorted(p for p in cap.iterdir() if p.is_dir()):
            try:
                pids = [t["token_id"] for t in json.loads((pdir / "prompt_tokens.json").read_text(errors="replace"))]
                gids = [t["token_id"] for t in json.loads((pdir / "generated_tokens.json").read_text(errors="replace"))]
            except FileNotFoundError:
                log(f"  skip {pdir.name} (no token JSONs)"); continue
            ids = torch.tensor([pids + gids], dtype=torch.long).to("cuda")
            with torch.no_grad():
                hs = model(ids, output_hidden_states=True, use_cache=False).hidden_states
            for L in COACT_LAYERS:
                r = hs[L + 1][0, len(pids):].float().cuda()
                acts = topk_acts(r, sae[L][0].cuda(), sae[L][1].cuda())
                store[L][pdir.name] = acts[:, cand[L]].cpu().numpy().astype(np.float16)
            log(f"  coact {capname}/{pdir.name}: {len(gids)} gen tok")
        np.savez_compressed(OUT / f"coact_{capname}.npz",
            **{f"L{L}__{pid}": arr for L in COACT_LAYERS for pid, arr in store[L].items()})
        (OUT / "ids.json").write_text(json.dumps({str(L): cand[L] for L in COACT_LAYERS}))
    log("LEG5_DONE_OK")

if __name__ == "__main__":
    main()
