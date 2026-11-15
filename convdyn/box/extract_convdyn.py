#!/usr/bin/env python3
"""extract_convdyn.py — on-box scalar extraction, verification, tar, and the DELETE-GATE.

Usage: extract_convdyn.py --root /workspace/convdyn_smoke   (or convdyn_grid)

Per capture dir: per-token w114 projection at L14 (primary), raw E114 router logit at
L14 (redundancy) and L26 (twin), top-8 selection flags, prefill track + incoming-user-
segment bounds, and a fresh L26 row recovery (gated rel-resid < 1e-3, per prereg).

Then: verify >=95% of expected captures complete/readable -> tar scalars + routers +
token JSONs + metadata + provenance (residuals EXCLUDED) -> only if the tar exists
non-empty are the residual .npy deleted (leg-3 lesson). Routers are kept in the tar.
"""
import argparse, hashlib, json, pathlib, subprocess, sys
import numpy as np

WORK = pathlib.Path("/workspace")
IN   = WORK / "convdyn_in"

def die(msg):
    print(f"EXTRACT_FAILED: {msg}", flush=True)
    sys.exit(1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = pathlib.Path(args.root)
    if not root.exists(): die(f"{root} missing")
    w114 = np.load(IN / "w114.npy").astype(np.float32)

    trans = json.loads((root / "transcripts.json").read_text())
    n_trim_of = {f"{d}_t{e['turn']:02d}": e["n_trim"] for d, es in trans.items() for e in es}
    span_of   = {f"{d}_t{e['turn']:02d}": e["probe_char_span"] for d, es in trans.items() for e in es}
    hyb_path = root / "hybrids.json"
    if hyb_path.exists():
        hyb = json.loads(hyb_path.read_text())
        n_trim_of.update({k: v["n_trim"] for k, v in hyb.items()})
        span_of.update({k: v["probe_char_span"] for k, v in hyb.items()})

    capdirs = sorted(p for cd in sorted(root.glob("cap_*")) if cd.is_dir()
                     for p in cd.iterdir() if p.is_dir())
    expected = len(n_trim_of)
    print(f"{len(capdirs)} capture dirs found, {expected} expected", flush=True)

    # ---------- pass 1: pooled L26 row recovery (prereg: gate rel-resid < 1e-3) ----------
    X, Y = [], []
    for pdir in capdirs:
        try:
            a = np.load(pdir / "residual/attn_post_norm-26.npy")
            r = np.load(pdir / "router/ffn_moe_logits-26.npy")[:, 114]
            k = min(len(a), len(r), 400)
            X.append(a[:k]); Y.append(r[:k])
        except FileNotFoundError:
            continue
    w26, rel26 = None, None
    if X:
        Xc, Yc = np.concatenate(X)[:60000].astype(np.float64), np.concatenate(Y)[:60000].astype(np.float64)
        sol, *_ = np.linalg.lstsq(Xc, Yc, rcond=None)
        rel26 = float(np.linalg.norm(Xc @ sol - Yc) / max(np.linalg.norm(Yc), 1e-12))
        if rel26 < 1e-3: w26 = sol.astype(np.float32)
    print(f"L26 row recovery: rel_resid={rel26} -> {'ACCEPTED' if w26 is not None else 'logits-only (gate failed)'}", flush=True)

    # ---------- pass 2: per-capture scalars ----------
    arrays, meta, ok, bad = {}, {}, 0, []
    red14 = []
    for pdir in capdirs:
        rid = pdir.name
        try:
            apn14 = np.load(pdir / "residual/attn_post_norm-14.npy").astype(np.float32)
            rou14 = np.load(pdir / "router/ffn_moe_logits-14.npy").astype(np.float32)
            rou26 = np.load(pdir / "router/ffn_moe_logits-26.npy").astype(np.float32)
            ptoks = json.loads((pdir / "prompt_tokens.json").read_text(errors="replace"))
            md = dict(l.split("=", 1) for l in (pdir / "metadata.txt").read_text().splitlines() if "=" in l)
            n_prompt, n_gen = len(ptoks), int(md.get("n_tokens_generated", 0))
            if apn14.shape[0] != n_prompt + n_gen:
                raise ValueError(f"row mismatch: apn14 {apn14.shape[0]} != {n_prompt}+{n_gen}")
            proj14 = apn14 @ w114
            logit14, logit26 = rou14[:, 114], rou26[:, 114]
            sel14 = (np.argsort(-rou14, axis=1)[:, :8] == 114).any(axis=1)
            # incoming-user-segment bounds via char-offset mapping (prereg v1.1)
            cs, ce = span_of.get(rid, (-1, -1))
            idx = [t["index"] for t in ptoks if t["start_char"] >= cs and t["end_char"] <= ce]
            seg = (min(idx), max(idx) + 1) if idx else (-1, -1)
            if cs >= 0 and not idx:
                raise ValueError(f"probe char span [{cs},{ce}) maps to zero prompt tokens")
            arrays[f"{rid}__prefill_proj14"] = proj14[:n_prompt]
            arrays[f"{rid}__prefill_logit14"] = logit14[:n_prompt]
            arrays[f"{rid}__gen_proj14"]  = proj14[n_prompt:]
            arrays[f"{rid}__gen_logit14"] = logit14[n_prompt:]
            arrays[f"{rid}__gen_sel14"]   = sel14[n_prompt:]
            arrays[f"{rid}__gen_logit26"] = logit26[n_prompt:]
            if w26 is not None:
                apn26 = np.load(pdir / "residual/attn_post_norm-26.npy").astype(np.float32)
                arrays[f"{rid}__gen_proj26"] = (apn26 @ w26)[n_prompt:]
            meta[rid] = dict(n_prompt=n_prompt, n_gen=n_gen, n_trim=n_trim_of.get(rid),
                             userseg_start=seg[0], userseg_end=seg[1])
            if n_gen > 0: red14.append(np.stack([proj14[n_prompt:], logit14[n_prompt:]]))
            ok += 1
        except Exception as ex:
            bad.append(f"{rid}: {ex}")
    for b in bad: print("  BAD:", b, flush=True)

    if red14:
        z = np.concatenate(red14, axis=1)
        r = float(np.corrcoef(z[0], z[1])[0, 1])
        print(f"redundancy check: pooled Pearson r(proj14, raw logit14) = {r:.6f}", flush=True)
        if r < 0.999: print("  !! WARNING: proj/logit divergence — data-integrity alarm (prereg)", flush=True)

    np.savez_compressed(root / "scalars.npz", **arrays)
    (root / "scalars_meta.json").write_text(json.dumps(
        dict(meta=meta, l26_recovery_rel_resid=rel26, l26_row_accepted=w26 is not None,
             w26=(w26.tolist() if w26 is not None else None)), indent=1))

    # quick per-turn eyeball summary (peaks/floors for A dialogues)
    for d in sorted(trans):
        if not d.startswith("A_"): continue
        line = []
        for e in trans[d]:
            g = arrays.get(f"{d}_t{e['turn']:02d}__gen_proj14")
            if g is None or e["n_trim"] == 0: line.append("t%02d:-" % e["turn"]); continue
            x = g[:e["n_trim"]]
            line.append(f"t{e['turn']:02d}:pk={x.max():+.2f},fl={x[-15:].mean():+.2f}")
        print(f"{d}  " + "  ".join(line), flush=True)

    # ---------- verify + tar + DELETE-GATE ----------
    frac = ok / max(expected, 1)
    print(f"verified {ok}/{expected} captures ({frac:.1%})", flush=True)
    if frac < 0.95: die("verification below 95% — raw residuals NOT deleted; investigate BAD list")

    tarball = WORK / f"{root.name}.tgz"
    ex = subprocess.run(["tar", "czf", str(tarball), "--exclude=*attn_post_norm*", "-C", str(WORK), root.name]).returncode
    if ex != 0 or not tarball.exists() or tarball.stat().st_size < 10000:
        die("tarball creation failed/empty — raw residuals NOT deleted")
    sha = hashlib.sha256(tarball.read_bytes()).hexdigest()
    (WORK / f"{root.name}.tgz.sha256").write_text(f"{sha}  {tarball.name}\n")
    print(f"tar OK: {tarball} ({tarball.stat().st_size/1e6:.1f} MB) sha256={sha}", flush=True)

    n_del = 0
    for f in root.rglob("attn_post_norm-*.npy"):
        f.unlink(); n_del += 1
    print(f"delete-gate passed: {n_del} residual npy removed (routers retained)", flush=True)
    print("EXTRACT_DONE_OK", flush=True)

if __name__ == "__main__":
    main()
