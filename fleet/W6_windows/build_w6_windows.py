#!/usr/bin/env python3
"""W6 blind-labeling materials: per-target top-40 activation windows + 40 random
contrast windows, from w6_targets.npz raw router logits.

NO interpretation anywhere in outputs -- materials only, explainer stays blind.
"""
import json
import os
from bisect import bisect_right

import numpy as np

SRC = "/Volumes/ExternalSSD/e114-construction-reframe/fleet/pulled/A1_W6/w6"
OUT = "/Volumes/ExternalSSD/e114-construction-reframe/fleet/W6_windows"
NPZ_SHA_SHORT = "1c8b8892"  # w6.tgz sha256 1c8b8892eea50c9ec1ec028bf9676662d03c1339bd8393cfd7a179c6fdf7a178
SEED = 41414
CTX = 60          # chars each side of argmax token
N_TOP = 40
N_RAND = 40
EXCLUDE_TOP = 100  # random contrasts drawn from docs outside the top-100

# expert columns in npz order
COLS = [114, 87, 34, 189]

# fixed target order (drives per-target rng substream: default_rng([SEED, idx]))
TARGETS = [
    ("E87_L14",  "l14", "sel14", COLS.index(87)),
    ("E34_L14",  "l14", "sel14", COLS.index(34)),
    ("E189_L14", "l14", "sel14", COLS.index(189)),
    ("E114_L14", "l14", "sel14", COLS.index(114)),  # reference
    ("E87_L26",  "l26", "sel26", COLS.index(87)),
    ("E189_L26", "l26", "sel26", COLS.index(189)),
]


def unescape(s: str) -> str:
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "n":
                out.append("\n"); i += 2; continue
            if n == "t":
                out.append("\t"); i += 2; continue
            if n == "\\":
                out.append("\\"); i += 2; continue
        out.append(c)
        i += 1
    return "".join(out)


def load_docs():
    docs = {}
    # newline='' : docs contain raw \r that universal-newline mode would mangle
    with open(os.path.join(SRC, "pile390.tsv"), encoding="utf-8", newline="") as f:
        for line in f.read().split("\n"):
            if not line:
                continue
            did, txt = line.split("\t", 1)
            docs[did] = unescape(txt)
    return docs


def load_tokens(did):
    # some pieces are raw partial-UTF8 byte fragments -> file not valid UTF-8;
    # we only use start_char/end_char (byte offsets), so replace is safe
    with open(os.path.join(SRC, "tokens", f"{did}.prompt_tokens.json"),
              encoding="utf-8", errors="replace") as f:
        return json.load(f)


def byte_starts(text):
    """cumulative byte offset of each char; starts[i] = byte offset of char i."""
    starts = [0]
    for ch in text:
        starts.append(starts[-1] + len(ch.encode("utf-8")))
    return starts  # len = len(text)+1; starts[-1] = total bytes


def window_for(text, starts, sb, eb):
    """Window = 60 chars before + token + 60 chars after.
    sb/eb are BYTE offsets of the token; map to char indices (snapping into
    the containing char if a token boundary splits a multibyte char)."""
    cs = bisect_right(starts, sb) - 1          # char containing byte sb
    ce = bisect_right(starts, max(eb - 1, sb)) - 1 + 1  # char after char containing byte eb-1
    ws = max(0, cs - CTX)
    we = min(len(text), ce + CTX)
    return text[ws:we], text[cs:ce], cs, ce


def main():
    os.makedirs(OUT, exist_ok=True)
    docs = load_docs()
    doc_ids = sorted(docs)
    z = np.load(os.path.join(SRC, "w6_targets.npz"))

    toks_by_doc = {d: load_tokens(d) for d in doc_ids}
    starts_by_doc = {d: byte_starts(docs[d]) for d in doc_ids}

    # alignment gate: npz T == token count, everywhere
    for d in doc_ids:
        T = z[d + "__l14"].shape[0]
        assert T == len(toks_by_doc[d]) == z[d + "__l26"].shape[0], (d, T, len(toks_by_doc[d]))

    summary_rows = []

    for ti, (name, lkey, skey, col) in enumerate(TARGETS):
        # per-doc max + argmax
        per_doc = []
        for d in doc_ids:
            a = z[f"{d}__{lkey}"][:, col]
            j = int(np.argmax(a))
            per_doc.append((d, float(a[j]), j))
        order = sorted(per_doc, key=lambda r: -r[1])  # stable: ties keep doc order

        top_entries = []
        for d, mx, j in order[:N_TOP]:
            tk = toks_by_doc[d][j]
            win, tok_txt, _, _ = window_for(docs[d], starts_by_doc[d],
                                            tk["start_char"], tk["end_char"])
            sel = bool(z[f"{d}__{skey}"][j, col])
            top_entries.append({
                "doc_id": d,
                "window": win,
                "max_logit": round(mx, 6),
                "argmax_token_index": j,
                "argmax_token_text": tok_txt,
                "top8_selected": sel,
            })

        # random contrasts: docs OUTSIDE top-100 for this target
        pool = [d for d, _, _ in order[EXCLUDE_TOP:]]
        rng = np.random.default_rng([SEED, ti])
        chosen = rng.choice(len(pool), size=N_RAND, replace=False)
        rand_entries = []
        for k in chosen:
            d = pool[int(k)]
            toks = toks_by_doc[d]
            j = int(rng.integers(0, len(toks)))
            tk = toks[j]
            win, tok_txt, _, _ = window_for(docs[d], starts_by_doc[d],
                                            tk["start_char"], tk["end_char"])
            a = z[f"{d}__{lkey}"][:, col]
            rand_entries.append({
                "doc_id": d,
                "window": win,
                "logit": round(float(a[j]), 6),
                "token_index": j,
                "token_text": tok_txt,
                "top8_selected": bool(z[f"{d}__{skey}"][j, col]),
                "doc_max_logit": round(float(a.max()), 6),
            })

        payload = {
            "target": name,
            "top": top_entries,
            "random": rand_entries,
            "provenance": {
                "npz_source": f"w6.tgz sha {NPZ_SHA_SHORT}…",
                "window_chars": 2 * CTX,
                "seed": SEED,
                "seed_derivation": f"np.random.default_rng([{SEED}, target_index={ti}]) over fixed target order "
                                   + ",".join(t[0] for t in TARGETS),
                "layer": int(lkey[1:]),
                "expert": COLS[col],
                "npz_column_index": col,
                "activation": "raw router logit (pre-top-k), not realized routing weight",
                "offsets_note": "token start_char/end_char are BYTE offsets into UTF-8 text; "
                                "windows are 60 chars each side after byte->char mapping",
                "corpus": "pile390.tsv (NeelNanda/pile-10k first 390 docs, 1200-char truncation)",
                "random_pool": f"docs ranked > {EXCLUDE_TOP} by this target's per-doc max logit",
            },
        }
        with open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)

        top_logits = np.array([e["max_logit"] for e in top_entries])
        rand_logits = np.array([e["logit"] for e in rand_entries])
        sel_rate = float(np.mean([e["top8_selected"] for e in top_entries]))
        overlap = bool(top_logits.min() <= rand_logits.max())
        summary_rows.append({
            "name": name, "layer": lkey, "expert": COLS[col],
            "top_mean": float(top_logits.mean()), "top_min": float(top_logits.min()),
            "top_max": float(top_logits.max()),
            "rand_mean": float(rand_logits.mean()), "rand_max": float(rand_logits.max()),
            "mean_diff": float(top_logits.mean() - rand_logits.mean()),
            "sel_rate": sel_rate,
            "overlap": overlap,
            "top5": [e["window"][:100] for e in top_entries[:5]],
        })

    # ---- summary.md (materials only, no interpretation) ----
    def esc(s):
        return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")

    lines = [
        "# W6 blind-labeling materials — summary",
        "",
        "Materials only. No interpretation of window content anywhere in this file or the JSONs;",
        "the explainer/judge must remain blind.",
        "",
        f"Source: `pulled/A1_W6/w6.tgz` (sha256 `1c8b8892eea50c9ec1ec028bf9676662d03c1339bd8393cfd7a179c6fdf7a178`) — "
        f"`w6_targets.npz`, 390 docs, expert columns [114, 87, 34, 189] at L14/L26.",
        f"Activations are **raw router logits** (pre-top-k), not realized routing weights — "
        f"logit ranges here are not on the published E114 realized-W scale (mean top ~0.46).",
        f"Windows: {2*CTX} context chars (60 each side of the argmax/center token; byte offsets mapped to chars). "
        f"Random contrasts: 40 windows at uniform-random token positions in docs outside that target's top-{EXCLUDE_TOP}, "
        f"seed {SEED} (per-target substream `default_rng([{SEED}, target_index])`).",
        "",
        "| target | top-40 mean logit | top-40 range | random mean logit (center token) | mean diff | top-8 sel rate (top-40 argmax) | top40/random overlap |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in summary_rows:
        lines.append(
            f"| {r['name']} | {r['top_mean']:.3f} | [{r['top_min']:.3f}, {r['top_max']:.3f}] | "
            f"{r['rand_mean']:.3f} | {r['mean_diff']:.3f} | {r['sel_rate']:.0%} | "
            f"{'YES' if r['overlap'] else 'no'} |"
        )
    lines.append("")
    flags = [r for r in summary_rows if r["overlap"]]
    lines.append("## Sanity gate")
    lines.append("")
    if flags:
        for r in flags:
            lines.append(
                f"- **FLAG {r['name']}**: top-40 max-logit range overlaps the random contrast range "
                f"(top-40 min {r['top_min']:.3f} <= random max {r['rand_max']:.3f}; "
                f"mean difference {r['mean_diff']:.3f}). Top and random windows are not cleanly separated "
                f"for this target — treat judge results with caution."
            )
    else:
        lines.append("- All targets: top-40 max logits are fully separated from random contrast logits "
                     "(every top-40 min > random max).")
    lines.append("")
    lines.append("Note: top-40 values are per-doc maxima while random values are single sampled tokens; "
                 "the comparison is the separation the judge will actually see, not a matched-statistic test.")
    lines.append("")
    for r in summary_rows:
        lines.append(f"## {r['name']} (expert {r['expert']}, layer {r['layer'][1:]})")
        lines.append("")
        lines.append(f"- top-8 selection rate among top-40 argmax tokens: **{r['sel_rate']:.0%}**")
        lines.append(f"- top-40 logit: mean {r['top_mean']:.3f}, range [{r['top_min']:.3f}, {r['top_max']:.3f}]; "
                     f"random contrast mean {r['rand_mean']:.3f} (max {r['rand_max']:.3f}); "
                     f"mean difference {r['mean_diff']:.3f}")
        lines.append("- top-5 windows (first 100 chars, escaped):")
        for i, w in enumerate(r["top5"], 1):
            lines.append(f"  {i}. `{esc(w)}`")
        lines.append("")

    with open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # console report for the final message
    for r in summary_rows:
        print(f"{r['name']}: top40_mean={r['top_mean']:.3f} rand_mean={r['rand_mean']:.3f} "
              f"diff={r['mean_diff']:.3f} sel_rate={r['sel_rate']:.0%} "
              f"top_range=[{r['top_min']:.3f},{r['top_max']:.3f}] rand_max={r['rand_max']:.3f} "
              f"overlap={'YES' if r['overlap'] else 'no'}")


if __name__ == "__main__":
    main()
