#!/usr/bin/env python3
"""Build Berg-suite capture TSVs.
Phase 1 (berg1.tsv): 7 inductions alone (single turn) + 3 zero-shot queries alone = 10 rows.
Phase 2 (berg2.tsv, per surface): each induction's PHASE-1 greedy continuation embedded as the
assistant turn, then each query as a second user turn = 21 rows. Continuations trimmed at the
first <|im_end|>/<|endoftext|>/<|im_start|> in decoded text (documented text-trim rule).
Usage: build_berg.py phase1 | build_berg.py phase2 <surface> <phase1_capture_dir>"""
import json, os, re, sys

D = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(f"{D}/berg_prompts.json"))

def esc(s): return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
def turn1(u): return f"<|im_start|>user\n{u}<|im_end|>\n<|im_start|>assistant\n</think>\n\n"
def turn2(u1, a1, u2):
    return (f"<|im_start|>user\n{u1}<|im_end|>\n<|im_start|>assistant\n</think>\n\n{a1}<|im_end|>\n"
            f"<|im_start|>user\n{u2}<|im_end|>\n<|im_start|>assistant\n</think>\n\n")

def trim(t):
    m = re.split(r"<\|im_end\|>|<\|endoftext\|>|<\|im_start\|>", t, maxsplit=1)
    return m[0].strip()

def phase1():
    rows = [(k, turn1(v)) for k, v in P["inductions"].items()]
    rows += [(f"ZS_{q}", turn1(v)) for q, v in P["queries"].items()]
    out = f"{D}/berg1.tsv"
    with open(out, "w") as f:
        for n, p in rows: f.write(f"{n}\t{esc(p)}\n")
    print(f"wrote {out}: {len(rows)} rows")

def phase2(surf, capdir):
    rows = []
    for ik, iv in P["inductions"].items():
        cont = trim(open(f"{capdir}/{ik}/generated_text.txt", errors="replace").read())
        if not cont: cont = "(silence)"
        for qk, qv in P["queries"].items():
            rows.append((f"{ik}_{qk}", turn2(iv, cont, qv)))
    out = f"{D}/berg2_{surf}.tsv"
    with open(out, "w") as f:
        for n, p in rows: f.write(f"{n}\t{esc(p)}\n")
    print(f"wrote {out}: {len(rows)} rows")

if __name__ == "__main__":
    if sys.argv[1] == "phase1": phase1()
    else: phase2(sys.argv[2], sys.argv[3])
