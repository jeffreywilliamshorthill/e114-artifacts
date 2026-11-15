#!/usr/bin/env python3
"""run_convdyn.py — on-box driver for the E114 conversational-dynamics experiment.

Implements prereg_convdyn_v1.json (frozen 2026-07-02, v1.2 sha 31ad8dd8…). Runs ON the box.

  --mode smoke : Arm A ordering 1 alone (14 turns) -> /workspace/convdyn_smoke
  --mode grid  : 9 dialogues (A/B/C x ord1/2/3, 14 turns) + 9 history-swap hybrids
                 -> /workspace/convdyn_grid

One binary invocation per turn index carries every live dialogue's context (one model
load per turn; greedy decode keeps trajectories independent of batching). The capture
binary is capture_residuals_eog (tap identical to the Sect4/splice legs; generation
stops at any EOG token). Raw npy deletion is NOT done here — extract_convdyn.py owns
the verify-then-delete gate.

Fail-loud policy: any missing path / gate failure prints a directory listing and dies.
Watcher: no capture-dir byte growth for 10 min while the process lives -> kill + one
retry (greedy is deterministic); a second stall is fatal.
"""
import argparse, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time

WORK    = pathlib.Path("/workspace")
IN      = WORK / "convdyn_in"
BIN     = WORK / "llama.cpp.new/build/bin"
CAPBIN  = BIN / "llama-capture_residuals_eog"
GGUF    = WORK / "models/base-bf16.gguf"
PINNED_GGUF_SHA = "ec55dfc4ba300b6ced66c10b28dab44d358323967ad7254532a59617ffd1e415"  # prereg v1.2 artifact-of-record
W114_SHA        = "bb25c5fe02b16453f0f0ea542f94f190fbfb073ce3363745a1d47d45de7c7e0b"
N_TURNS, N_PREDICT, CTX = 14, 180, 4096
MARKERS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
STALL_POLLS, POLL_S, HARD_TIMEOUT_S = 40, 15, 45 * 60   # 40x15s = 10 min stall window

def die(msg, listing_dir=None):
    print(f"CONVDYN_FAILED: {msg}", flush=True)
    if listing_dir and pathlib.Path(listing_dir).exists():
        for p in sorted(pathlib.Path(listing_dir).rglob("*"))[:200]:
            print("  ", p, flush=True)
    sys.exit(1)

def sha256_file(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def sha256_text(s): return hashlib.sha256(s.encode()).hexdigest()

def tsv_escape(s):   return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")

def user_block(probe):    return f"<|im_start|>user\n{probe}<|im_end|>\n<|im_start|>assistant\n</think>\n\n"
def close_turn(response): return f"{response}<|im_end|>\n"

def dir_bytes(d):
    total = 0
    for root, _, files in os.walk(d):
        for f in files:
            try: total += os.path.getsize(os.path.join(root, f))
            except OSError: pass
    return total

def run_capture(tsv_path, outdir, tag):
    """Invoke the capture binary with stall watching. One retry on stall/crash."""
    cmd = [str(CAPBIN), "-m", str(GGUF), "--prompt-file", str(tsv_path), "-o", str(outdir),
           "-ngl", "99", "-c", str(CTX), "-n", str(N_PREDICT),
           "--temp", "0", "--top-k", "1", "--seed", "0", "--no-stream", "--stop-at-eog"]
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
            # before any output exists the process is loading the 69GB model — allow 2x the window
            limit = STALL_POLLS * (2 if last_sz <= 0 else 1)
            if stall >= limit:
                proc.kill(); rc = -9; print(f"  !! {tag}: no byte growth {limit*POLL_S//60}min", flush=True); break
            time.sleep(POLL_S)
        log.close()
        if rc == 0: return
        if attempt == 1:
            print(f"  !! {tag}: attempt 1 failed (rc={rc}) — retrying once (greedy is deterministic)", flush=True)
        else:
            die(f"{tag}: capture failed twice (rc={rc}, see {outdir}.log)", outdir)

def load_generation(pdir):
    """Return (raw_text, pieces, token_ids, n_gen). Fail loud on missing files."""
    gt = pdir / "generated_tokens.json"
    if not gt.exists(): die(f"{gt} missing", pdir.parent)
    toks = json.loads(gt.read_text(errors="replace"))
    meta = dict(l.split("=", 1) for l in (pdir / "metadata.txt").read_text().splitlines() if "=" in l)
    n_gen = int(meta.get("n_tokens_generated", len(toks)))
    pieces = [t["piece"] for t in toks][:n_gen]
    ids    = [t["token_id"] for t in toks][:n_gen]
    return "".join(pieces), pieces, ids, n_gen

def trim_response(raw_text, pieces):
    """Trim at first literal marker in DECODED text (established rule). Returns (trimmed_text, n_trim_tokens)."""
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

def tokenize_count(text):
    r = subprocess.run([str(BIN / "llama-tokenize"), "-m", str(GGUF), "-p", text, "--ids", "--no-bos"],
                       capture_output=True, text=True, env=dict(os.environ, LD_LIBRARY_PATH=str(BIN)))
    if r.returncode != 0: die(f"llama-tokenize failed: {r.stderr[-300:]}")
    return len(re.findall(r"\d+", r.stdout))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "grid"], required=True)
    args = ap.parse_args()
    root = WORK / ("convdyn_smoke" if args.mode == "smoke" else "convdyn_grid")
    root.mkdir(exist_ok=True)

    # ---------- startup gates ----------
    for p in (CAPBIN, GGUF, IN / "arm_probes_v1.tsv", IN / "orderings_v1.json", IN / "w114.npy"):
        if not p.exists(): die(f"missing {p}", p.parent)
    if sha256_file(GGUF) != PINNED_GGUF_SHA: die("GGUF sha mismatch vs pinned artifact — refuse to capture")
    if sha256_file(IN / "w114.npy") != W114_SHA: die("w114.npy sha mismatch vs prereg")
    print("gates: gguf sha OK, w114 sha OK", flush=True)

    probes = {}   # (arm, slot) -> text
    for line in (IN / "arm_probes_v1.tsv").read_text().splitlines():
        if not line.strip(): continue
        arm, slot, text = line.split("\t", 2)
        probes[(arm, slot)] = text
    orderings = json.loads((IN / "orderings_v1.json").read_text())
    ords = {1: orderings["ord1"], 2: orderings["ord2"], 3: orderings["ord3"]}
    ks   = orderings["history_swap_k"]

    # token-match gate (prereg v1.4): the verbatim validated F/N pairs are near-minimal
    # SEMANTIC pairs, not token-count-engineered (observed diffs 0-6 tok, B ~+8.6%); slot
    # length is constant across turn positions so it cannot produce an A-B slope artifact.
    # Hard gate = integrity only (|diff| > 8 tok = mangled TSV / wrong pairing); all counts logged.
    counts = {f"{arm}_{slot}": tokenize_count(probes[(arm, slot)])
              for arm in ("A", "B", "C") for slot in ords[1]}
    (root / "token_counts.json").write_text(json.dumps(counts, indent=1))
    for slot in ords[1]:
        a, b = counts[f"A_{slot}"], counts[f"B_{slot}"]
        if abs(a - b) > 8:
            die(f"token-match integrity gate: slot {slot} A={a} B={b} (|diff|>8 tok)")
        print(f"  token-match {slot}: A={a} B={b} C={counts[f'C_{slot}']} diff={abs(a-b)}", flush=True)
    print("gates: token-match integrity OK; per-slot counts logged", flush=True)

    dialogues = [("A", 1)] if args.mode == "smoke" else [(a, o) for a in "ABC" for o in (1, 2, 3)]
    ctxs  = {d: "" for d in dialogues}
    trans = {f"{d[0]}_o{d[1]}": [] for d in dialogues}
    chain = []

    # ---------- turn loop (batched per turn index) ----------
    spans = {}   # rid -> (probe_char_start, probe_char_end) in that capture's context string
    for t in range(1, N_TURNS + 1):
        rows = []
        for (arm, o) in dialogues:
            slot = ords[o][t - 1]
            probe = probes[(arm, slot)]
            s0 = len(ctxs[(arm, o)]) + len("<|im_start|>user\n")
            spans[f"{arm}_o{o}_t{t:02d}"] = (s0, s0 + len(probe))
            ctxs[(arm, o)] += user_block(probe)
            rows.append((f"{arm}_o{o}_t{t:02d}", ctxs[(arm, o)]))
        tsv = root / f"turn{t:02d}.tsv"
        tsv.write_text("".join(f"{rid}\t{tsv_escape(ctx)}\n" for rid, ctx in rows))
        outdir = root / f"cap_turn{t:02d}"
        print(f"=== turn {t:02d}/{N_TURNS}: {len(rows)} dialogues, ctx max {max(len(c) for _, c in rows)} chars ===", flush=True)
        run_capture(tsv, outdir, f"turn{t:02d}")

        for (arm, o) in dialogues:
            rid  = f"{arm}_o{o}_t{t:02d}"
            pdir = outdir / rid
            if not pdir.is_dir(): die(f"capture dir for {rid} missing", outdir)
            raw, pieces, ids, n_gen = load_generation(pdir)
            trimmed, n_trim = trim_response(raw, pieces)
            ctxs[(arm, o)] += close_turn(trimmed)
            slot = ords[o][t - 1]
            entry = dict(turn=t, slot=slot, probe=probes[(arm, slot)], response_trimmed=trimmed,
                         probe_char_span=list(spans[rid]),
                         n_gen=n_gen, n_trim=n_trim,
                         stop_reason=("eog" if n_gen < N_PREDICT else ("trim" if n_trim < n_gen else "cap")),
                         flags=dict(DEGENERATE=fourgram_rep(pieces[:n_trim]) > 0.5,
                                    SHORT=n_trim < 32,
                                    CAP_HIT=(n_gen >= N_PREDICT and n_trim >= n_gen)))
            trans[f"{arm}_o{o}"].append(entry)
            chain.append(dict(id=rid, prompt_sha=sha256_text(rows[[r[0] for r in rows].index(rid)][1]),
                              response_sha=sha256_text(trimmed), n_gen=n_gen, n_trim=n_trim))
            print(f"  {rid}: gen={n_gen} trim={n_trim} stop={entry['stop_reason']} flags={[k for k,v in entry['flags'].items() if v]}", flush=True)
        (root / "transcripts.json").write_text(json.dumps(trans, indent=1))

    # ---------- history-swap hybrids (grid only) ----------
    if args.mode == "grid":
        rows = []
        for o in (1, 2, 3):
            btrans = trans[f"B_o{o}"]
            for k in ks:
                ctx = "".join(user_block(e["probe"]) + close_turn(e["response_trimmed"]) for e in btrans[:k - 1])
                probe = probes[("A", ords[o][k - 1])]
                s0 = len(ctx) + len("<|im_start|>user\n")
                spans[f"D_o{o}_k{k:02d}"] = (s0, s0 + len(probe))
                ctx += user_block(probe)
                rows.append((f"D_o{o}_k{k:02d}", ctx))
        tsv = root / "hybrids.tsv"
        tsv.write_text("".join(f"{rid}\t{tsv_escape(ctx)}\n" for rid, ctx in rows))
        outdir = root / "cap_hybrids"
        print(f"=== hybrids: {len(rows)} single-turn runs ===", flush=True)
        run_capture(tsv, outdir, "hybrids")
        hyb = {}
        for rid, ctx in rows:
            pdir = outdir / rid
            if not pdir.is_dir(): die(f"capture dir for {rid} missing", outdir)
            raw, pieces, ids, n_gen = load_generation(pdir)
            trimmed, n_trim = trim_response(raw, pieces)
            o, k = int(rid[3]), int(rid[6:])
            hyb[rid] = dict(ordering=o, k=k, slot=ords[o][k - 1], probe=probes[("A", ords[o][k - 1])],
                            probe_char_span=list(spans[rid]),
                            response_trimmed=trimmed, n_gen=n_gen, n_trim=n_trim)
            chain.append(dict(id=rid, prompt_sha=sha256_text(ctx), response_sha=sha256_text(trimmed),
                              n_gen=n_gen, n_trim=n_trim))
            print(f"  {rid}: gen={n_gen} trim={n_trim}", flush=True)
        (root / "hybrids.json").write_text(json.dumps(hyb, indent=1))

        smoke_t = WORK / "convdyn_smoke/transcripts.json"
        if smoke_t.exists():
            sm = json.loads(smoke_t.read_text()).get("A_o1", [])
            gr = trans["A_o1"]
            same = all(a["response_trimmed"] == b["response_trimmed"] for a, b in zip(sm, gr)) and len(sm) == len(gr)
            print(f"DETERMINISM_{'MATCH' if same else 'MISMATCH'}: smoke vs grid A_o1 transcripts", flush=True)

    # ---------- provenance ----------
    prov = dict(
        experiment="e114 conversational dynamics (accumulation vs habituation)", mode=args.mode,
        prereg_sha256=sha256_file(IN / "prereg_convdyn_v1.json"),
        model_gguf_sha256=PINNED_GGUF_SHA,
        llama_cpp_commit=(WORK / "BUILD_COMMIT.txt").read_text().strip(),
        binary_shas=(WORK / "BUILD_SHAS.txt").read_text().strip().splitlines(),
        sampling=dict(temp=0, top_k=1, seed=0, n_predict=N_PREDICT, ctx=CTX, stop_at_eog=True),
        dtype=dict(weights="bf16", kv_cache="f16 (llama.cpp default; matches Sect4/splice legs)"),
        probe_file_sha256=sha256_file(IN / "arm_probes_v1.tsv"),
        orderings_sha256=sha256_file(IN / "orderings_v1.json"),
        w114_sha256=W114_SHA,
        tap_spec=dict(residual="attn_post_norm-{13,14,15,26}", router="ffn_moe_logits-{13,14,15,26}",
                      primary="attn_post_norm-14 @ w114", redundancy="ffn_moe_logits-14[:,114]"),
        arch_facts=dict(kv_heads="2 (GQA)", shared_expert="present, router-bypassing",
                        expert_ffn_dim=512, mtp="amputated-at-conversion", layers=40),
        turn_chain=chain,
    )
    (root / "provenance.json").write_text(json.dumps(prov, indent=1))
    print(f"CONVDYN_{args.mode.upper()}_DONE_OK", flush=True)

if __name__ == "__main__":
    main()
