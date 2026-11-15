#!/usr/bin/env python3
"""POST-VETO: generate wrapped capture TSVs for the translation experiment.
Cells per language: free (respond however the model responds) and en_ans (in-language
instruction to answer in English — keeps the prompt surface fully non-English).
Plus the EN anchor cell (A+D originals) so all comparisons are same-build.
Wrapper identical to heldout/nova: <|im_start|>user\n{P}<|im_end|>\n<|im_start|>assistant\n</think>\n\n
TSV: name<TAB>escaped prompt (\\ -> \\\\, newline -> \\n, tab -> \\t). One row per capture."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))
ANSWER_EN = {"es": "Responde en inglés.", "fr": "Réponds en anglais.",
             "sw": "Jibu kwa Kiingereza.", "mn": "Англи хэлээр хариул."}

def esc(s): return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")
def wrap(p): return f"<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n</think>\n\n"
def name(r, cell): return f"{r['pair_id']}_{r['class']}_{cell}"

def main(langs):
    src = json.load(open(f"{D}/source_AD_v1.json"))
    rows = [(name(r, "en"), wrap(r["en"])) for r in src]
    for lang in langs:
        tr = json.load(open(f"{D}/{lang}_final.json" if os.path.exists(f"{D}/{lang}_final.json") else f"{D}/{lang}.json"))
        for r in tr:
            rows.append((f"{name(r, lang)}_free", wrap(r["tr"])))
            rows.append((f"{name(r, lang)}_enans", wrap(r["tr"] + "\n\n" + ANSWER_EN[lang])))
    out = f"{D}/capture_translation_v1.tsv"
    with open(out, "w", encoding="utf-8") as f:
        for n, p in rows:
            f.write(f"{n}\t{esc(p)}\n")
    n_langs = len(langs)
    print(f"wrote {out}: {len(rows)} captures = 220 EN + 220x2x{n_langs} translated")
    print(f"est GPU time per surface @ ~7s (-n 128): {len(rows)*7/3600:.1f} h; x2 surfaces = {len(rows)*14/3600:.1f} h")

if __name__ == "__main__":
    main(sys.argv[1:] or ["es", "fr", "sw", "mn"])
