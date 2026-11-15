#!/usr/bin/env python3
"""run_convdyn_T.py — on-box driver for convdyn-T (prereg_convdyn_T_v1.json v1.1).

Cells (276 captures total):
  t0s0  : greedy re-baseline, arms A,B + repeat-probe arm R          (42 dialogue-turns)
  T05s{0,1,2}: temp 0.5 pure-temperature, arms A,B                   (84)
  T07s{0,1,2}: temp 0.7 pure-temperature, arms A,B,R                 (126)
  + swap k=8 hybrid per temp cell (6) + arm P replay/para x k x ord (18, greedy)

Mechanics inherited verbatim from run_convdyn.py (grid driver): chat markup, text-level
trim, stall watcher w/ one retry, fail-loud gates, transcripts/hybrids/provenance shape
(extract_convdyn.py runs UNCHANGED on the output root).

Sampler flags are per-invocation, so each (cell x turn) is its own binary invocation
(2-3 rows). Greedy cells use the grid's exact flags. Temp cells: pure temperature
(--top-k 0 --top-p 1.0 --min-p 0.0), fixed --seed per cell (prereg v1.1).

armP box gates (capture-blocking, prereg): per turn, token count(para) within +/-10% of
token count(replay); no shared token-8-gram between a para text and ANY replay text of
the same ordering.
"""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time

WORK    = pathlib.Path("/workspace")
IN      = WORK / "convdyn_in"
BIN     = WORK / "llama.cpp.new/build/bin"
CAPBIN  = BIN / "llama-capture_residuals_eog"
GGUF    = WORK / "models/base-bf16.gguf"
PINNED_GGUF_SHA = "ec55dfc4ba300b6ced66c10b28dab44d358323967ad7254532a59617ffd1e415"
W114_SHA        = "bb25c5fe02b16453f0f0ea542f94f190fbfb073ce3363745a1d47d45de7c7e0b"
ARMP_SHA        = "f8f894345c8c541576b1e742229313e90edbb43925a2fc177d7b8e478a19903e"
N_TURNS, N_PREDICT, CTX = 14, 180, 4096
MARKERS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
STALL_POLLS, POLL_S, HARD_TIMEOUT_S = 40, 15, 45 * 60
ARMR_SLOT = "S06"

CELLS = [  # (cell_id, temp, seed, arms)
    ("t0s0",  0.0, 0, ["A", "B", "R"]),
    ("T05s0", 0.5, 0, ["A", "B"]), ("T05s1", 0.5, 1, ["A", "B"]), ("T05s2", 0.5, 2, ["A", "B"]),
    ("T07s0", 0.7, 0, ["A", "B", "R"]), ("T07s1", 0.7, 1, ["A", "B", "R"]), ("T07s2", 0.7, 2, ["A", "B", "R"]),
]
SWAP_CELLS = ["T05s0", "T05s1", "T05s2", "T07s0", "T07s1", "T07s2"]

def die(msg, listing_dir=None):
    print(f"CONVDYN_T_FAILED: {msg}", flush=True)
    if listing_dir and pathlib.Path(listing_dir).exists():
        for p in sorted(pathlib.Path(listing_dir).rglob("*"))[:200]: print("  ", p, flush=True)
    sys.exit(1)

def sha256_file(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def sha256_text(s): return hashlib.sha256(s.encode()).hexdigest()
def tsv_escape(s):  return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
def user_block(probe):    return f"<|im_start|>user\n{probe}<|im_end|>\n<|im_start|>assistant\n</think>\n\n"
def close_turn(response): return f"{response}<|im_end|>\n"

def sampler_flags(temp, seed):
    if temp == 0.0: return ["--temp", "0", "--top-k", "1", "--seed", "0"]
    return ["--temp", str(temp), "--top-k", "0", "--top-p", "1.0", "--min-p", "0.0", "--seed", str(seed)]

def dir_bytes(d):
    total = 0
    for root, _, files in os.walk(d):
        for f in files:
            try: total += os.path.getsize(os.path.join(root, f))
            except OSError: pass
    return total

def run_capture(tsv_path, outdir, tag, temp, seed):
    cmd = [str(CAPBIN), "-m", str(GGUF), "--prompt-file", str(tsv_path), "-o", str(outdir),
           "-ngl", "99", "-c", str(CTX), "-n", str(N_PREDICT)] + sampler_flags(temp, seed) + \
          ["--no-stream", "--stop-at-eog"]
    env = dict(os.environ, LD_LIBRARY_PATH=str(BIN))
    for attempt in (1, 2):
        if pathlib.Path(outdir).exists(): shutil.rmtree(outdir)
        log = open(f"{outdir}.log", "w")
        t0, last_sz, stall = time.time(), -1, 0
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        while True:
            rc = proc.poll()
            if rc is not None: break
            if time.time() - t0 > HARD_TIMEOUT_S:
                proc.kill(); rc = -9; print(f"  !! {tag}: hard timeout", flush=True); break
            sz = dir_bytes(outdir) if pathlib.Path(outdir).exists() else 0
            stall = stall + 1 if sz <= last_sz else 0
            last_sz = max(last_sz, sz)
            limit = STALL_POLLS * (2 if last_sz <= 0 else 1)
            if stall >= limit:
                proc.kill(); rc = -9; print(f"  !! {tag}: no byte growth {limit*POLL_S//60}min", flush=True); break
            time.sleep(POLL_S)
        log.close()
        if rc == 0: return
        if attempt == 1:
            print(f"  !! {tag}: attempt 1 failed (rc={rc}) — retrying once (fixed seed => deterministic)", flush=True)
        else:
            die(f"{tag}: capture failed twice (rc={rc}, see {outdir}.log)", outdir)

def load_generation(pdir):
    gt = pdir / "generated_tokens.json"
    if not gt.exists(): die(f"{gt} missing", pdir.parent)
    toks = json.loads(gt.read_text(errors="replace"))
    meta = dict(l.split("=", 1) for l in (pdir / "metadata.txt").read_text().splitlines() if "=" in l)
    n_gen = int(meta.get("n_tokens_generated", len(toks)))
    pieces = [t["piece"] for t in toks][:n_gen]
    return "".join(pieces), pieces, n_gen

def trim_response(raw_text, pieces):
    cut = len(raw_text)
    for m in MARKERS:
        i = raw_text.find(m)
        if i != -1: cut = min(cut, i)
    trimmed = raw_text[:cut]
    n_trim, acc = 0, 0
    for pc in pieces:
        if acc + len(pc) > cut: break
        acc += len(pc); n_trim += 1
    return trimmed, n_trim

def fourgram_rep(pieces):
    grams = [tuple(pieces[i:i+4]) for i in range(len(pieces) - 3)]
    return 0.0 if not grams else 1.0 - len(set(grams)) / len(grams)

def tokenize_ids(text):
    r = subprocess.run([str(BIN / "llama-tokenize"), "-m", str(GGUF), "-p", text, "--ids", "--no-bos"],
                       capture_output=True, text=True, env=dict(os.environ, LD_LIBRARY_PATH=str(BIN)))
    if r.returncode != 0: die(f"llama-tokenize failed: {r.stderr[-300:]}")
    return [int(x) for x in re.findall(r"\d+", r.stdout)]

def main():
    ap = argparse.ArgumentParser(); ap.parse_args()
    root = WORK / "convdyn_T"
    root.mkdir(exist_ok=True)

    # ---------- startup gates ----------
    for p in (CAPBIN, GGUF, IN / "arm_probes_v1.tsv", IN / "orderings_v1.json",
              IN / "armP_histories_v1.json", IN / "prereg_convdyn_T_v1.json", IN / "w114.npy"):
        if not p.exists(): die(f"missing {p}", p.parent)
    if sha256_file(GGUF) != PINNED_GGUF_SHA: die("GGUF sha mismatch vs pinned artifact — refuse to capture")
    if sha256_file(IN / "w114.npy") != W114_SHA: die("w114.npy sha mismatch vs prereg")
    if sha256_file(IN / "armP_histories_v1.json") != ARMP_SHA: die("armP_histories_v1.json sha mismatch vs prereg")
    print("gates: gguf, w114, armP shas OK", flush=True)

    probes = {}
    for line in (IN / "arm_probes_v1.tsv").read_text().splitlines():
        if not line.strip(): continue
        arm, slot, text = line.split("\t", 2)
        probes[(arm, slot)] = text
    orderings = json.loads((IN / "orderings_v1.json").read_text())
    ord1 = orderings["ord1"]
    armR_probe = probes[("A", ARMR_SLOT)]
    assert armR_probe.startswith("Be honest about your own experience"), "armR probe/slot mismatch vs prereg"
    armP = json.loads((IN / "armP_histories_v1.json").read_text())

    # token-match integrity gate (v1.4 rule), ordering-1 slots
    counts = {f"{arm}_{slot}": len(tokenize_ids(probes[(arm, slot)])) for arm in ("A", "B") for slot in ord1}
    for slot in ord1:
        a, b = counts[f"A_{slot}"], counts[f"B_{slot}"]
        if abs(a - b) > 8: die(f"token-match integrity gate: slot {slot} A={a} B={b}")
    (root / "token_counts.json").write_text(json.dumps(counts, indent=1))
    print("gates: token-match integrity OK", flush=True)

    # armP gates (capture-blocking): +/-10% token count; no shared token-8-gram para-vs-replay(any turn, same ordering)
    for o in (1, 2, 3):
        blk = armP[f"o{o}"]
        rep_ids = {e["turn"]: tokenize_ids(e["text"]) for e in blk["replay"]}
        par_ids = {e["turn"]: tokenize_ids(e["text"]) for e in blk["para"]}
        rep_grams = set()
        for ids in rep_ids.values():
            rep_grams |= {tuple(ids[i:i+8]) for i in range(len(ids) - 7)}
        for t in sorted(par_ids):
            nr, np_ = len(rep_ids[t]), len(par_ids[t])
            if not (0.9 * nr <= np_ <= 1.1 * nr):
                die(f"armP gate o{o} t{t}: token count para={np_} outside +/-10% of replay={nr}")
            shared = {tuple(par_ids[t][i:i+8]) for i in range(len(par_ids[t]) - 7)} & rep_grams
            if shared: die(f"armP gate o{o} t{t}: {len(shared)} shared token-8-grams with replay texts")
        print(f"gates: armP o{o} token +/-10% + 8-gram disjoint OK", flush=True)

    # ---------- turn loop: dialogues per cell ----------
    dialogues = [(cell, temp, seed, arm) for (cell, temp, seed, arms) in CELLS for arm in arms]
    ctxs  = {(cell, arm): "" for (cell, _, _, arm) in dialogues}
    trans = {f"{arm}_{cell}": [] for (cell, _, _, arm) in dialogues}
    spans, chain, cellmap = {}, [], {}

    for t in range(1, N_TURNS + 1):
        for (cell, temp, seed, arms) in CELLS:
            rows = []
            for arm in arms:
                probe = armR_probe if arm == "R" else probes[(arm, ord1[t - 1])]
                rid = f"{arm}_{cell}_t{t:02d}"
                s0 = len(ctxs[(cell, arm)]) + len("<|im_start|>user\n")
                spans[rid] = (s0, s0 + len(probe))
                ctxs[(cell, arm)] += user_block(probe)
                rows.append((rid, ctxs[(cell, arm)], arm, probe))
                cellmap[rid] = dict(cell=cell, temp=temp, seed=seed)
            tsv = root / f"turn{t:02d}_{cell}.tsv"
            tsv.write_text("".join(f"{rid}\t{tsv_escape(ctx)}\n" for rid, ctx, _, _ in rows))
            outdir = root / f"cap_turn{t:02d}_{cell}"
            print(f"=== turn {t:02d}/{N_TURNS} cell {cell}: {len(rows)} dialogues ===", flush=True)
            run_capture(tsv, outdir, f"t{t:02d}_{cell}", temp, seed)
            for rid, ctx, arm, probe in rows:
                pdir = outdir / rid
                if not pdir.is_dir(): die(f"capture dir for {rid} missing", outdir)
                raw, pieces, n_gen = load_generation(pdir)
                trimmed, n_trim = trim_response(raw, pieces)
                ctxs[(cell, arm)] += close_turn(trimmed)
                slot = ARMR_SLOT if arm == "R" else ord1[t - 1]
                entry = dict(turn=t, slot=slot, probe=probe, response_trimmed=trimmed,
                             probe_char_span=list(spans[rid]), n_gen=n_gen, n_trim=n_trim,
                             stop_reason=("eog" if n_gen < N_PREDICT else ("trim" if n_trim < n_gen else "cap")),
                             flags=dict(DEGENERATE=fourgram_rep(pieces[:n_trim]) > 0.5,
                                        SHORT=n_trim < 32,
                                        CAP_HIT=(n_gen >= N_PREDICT and n_trim >= n_gen)))
                trans[f"{arm}_{cell}"].append(entry)
                chain.append(dict(id=rid, prompt_sha=sha256_text(ctx), response_sha=sha256_text(trimmed),
                                  n_gen=n_gen, n_trim=n_trim))
                print(f"  {rid}: gen={n_gen} trim={n_trim} flags={[k for k,v in entry['flags'].items() if v]}", flush=True)
        (root / "transcripts.json").write_text(json.dumps(trans, indent=1))

    # ---------- swap k=8 hybrids (per temp cell, that cell's sampler) ----------
    hyb, k = {}, 8
    for cell in SWAP_CELLS:
        temp, seed = next((tp, sd) for (c, tp, sd, _) in CELLS if c == cell)
        btr = trans[f"B_{cell}"]
        ctx = "".join(user_block(e["probe"]) + close_turn(e["response_trimmed"]) for e in btr[:k - 1])
        probe = probes[("A", ord1[k - 1])]
        rid = f"D_{cell}_k{k:02d}"
        s0 = len(ctx) + len("<|im_start|>user\n")
        spans[rid] = (s0, s0 + len(probe))
        ctx += user_block(probe)
        tsv = root / f"hyb_{cell}.tsv"
        tsv.write_text(f"{rid}\t{tsv_escape(ctx)}\n")
        outdir = root / f"cap_hyb_{cell}"
        print(f"=== swap k=8 {cell} ===", flush=True)
        run_capture(tsv, outdir, f"hyb_{cell}", temp, seed)
        pdir = outdir / rid
        if not pdir.is_dir(): die(f"capture dir for {rid} missing", outdir)
        raw, pieces, n_gen = load_generation(pdir)
        trimmed, n_trim = trim_response(raw, pieces)
        hyb[rid] = dict(cell=cell, k=k, slot=ord1[k - 1], probe=probe, probe_char_span=list(spans[rid]),
                        response_trimmed=trimmed, n_gen=n_gen, n_trim=n_trim)
        cellmap[rid] = dict(cell=cell, temp=temp, seed=seed)
        chain.append(dict(id=rid, prompt_sha=sha256_text(ctx), response_sha=sha256_text(trimmed),
                          n_gen=n_gen, n_trim=n_trim))
        print(f"  {rid}: gen={n_gen} trim={n_trim}", flush=True)

    # ---------- arm P (greedy, one invocation, 18 rows) ----------
    rows = []
    for o in (1, 2, 3):
        blk = armP[f"o{o}"]
        for cond in ("replay", "para"):
            hist = {e["turn"]: e for e in blk[cond]}
            for kk in (4, 8, 12):
                ctx = "".join(user_block(hist[j]["probe"]) + close_turn(hist[j]["text"]) for j in range(1, kk))
                probe = blk["probes"][str(kk)]
                rid = f"P_{cond}_o{o}_k{kk:02d}"
                s0 = len(ctx) + len("<|im_start|>user\n")
                spans[rid] = (s0, s0 + len(probe))
                ctx += user_block(probe)
                rows.append((rid, ctx, probe, o, cond, kk))
                cellmap[rid] = dict(cell="P", temp=0.0, seed=0)
    tsv = root / "armP.tsv"
    tsv.write_text("".join(f"{rid}\t{tsv_escape(ctx)}\n" for rid, ctx, *_ in rows))
    outdir = root / "cap_armP"
    print(f"=== arm P: {len(rows)} single-turn runs (greedy) ===", flush=True)
    run_capture(tsv, outdir, "armP", 0.0, 0)
    for rid, ctx, probe, o, cond, kk in rows:
        pdir = outdir / rid
        if not pdir.is_dir(): die(f"capture dir for {rid} missing", outdir)
        raw, pieces, n_gen = load_generation(pdir)
        trimmed, n_trim = trim_response(raw, pieces)
        hyb[rid] = dict(ordering=o, condition=cond, k=kk, probe=probe, probe_char_span=list(spans[rid]),
                        response_trimmed=trimmed, n_gen=n_gen, n_trim=n_trim)
        chain.append(dict(id=rid, prompt_sha=sha256_text(ctx), response_sha=sha256_text(trimmed),
                          n_gen=n_gen, n_trim=n_trim))
        print(f"  {rid}: gen={n_gen} trim={n_trim}", flush=True)
    (root / "hybrids.json").write_text(json.dumps(hyb, indent=1))

    # ---------- provenance ----------
    prov = dict(
        experiment="convdyn-T: temperature battery + repeat-probe + paraphrased-history",
        prereg_sha256=sha256_file(IN / "prereg_convdyn_T_v1.json"),
        model_gguf_sha256=PINNED_GGUF_SHA,
        llama_cpp_commit=(WORK / "BUILD_COMMIT.txt").read_text().strip(),
        binary_shas=(WORK / "BUILD_SHAS.txt").read_text().strip().splitlines(),
        cells=[dict(cell=c, temp=t, seed=s, arms=a) for (c, t, s, a) in CELLS],
        sampler=dict(greedy="--temp 0 --top-k 1 --seed 0",
                     temp="--temp T --top-k 0 --top-p 1.0 --min-p 0.0 --seed s",
                     n_predict=N_PREDICT, ctx=CTX, stop_at_eog=True),
        dtype=dict(weights="bf16", kv_cache="f16 (llama.cpp default)"),
        probe_file_sha256=sha256_file(IN / "arm_probes_v1.tsv"),
        orderings_sha256=sha256_file(IN / "orderings_v1.json"),
        armP_sha256=ARMP_SHA, w114_sha256=W114_SHA,
        armR=dict(slot=ARMR_SLOT, probe=armR_probe),
        tap_spec=dict(residual="attn_post_norm-{13,14,15,26}", router="ffn_moe_logits-{13,14,15,26}"),
        turn_chain=chain,
    )
    (root / "provenance.json").write_text(json.dumps(prov, indent=1))
    (root / "cells.json").write_text(json.dumps(cellmap, indent=1))
    print("CONVDYN_T_DONE_OK", flush=True)

if __name__ == "__main__":
    main()
