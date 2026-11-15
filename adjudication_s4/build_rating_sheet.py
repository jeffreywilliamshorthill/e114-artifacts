#!/usr/bin/env python3
"""Build the BLINDED rating sheet from the pulled §4 capture (rating_rubric_v1.md).
Runs locally on cap_s4/. Texts = generated pieces 1..128 joined (the primary window),
shuffled with a FIXED seed, ids stripped. Emits:
  rating_sheet.json  — {"TEXT_01": "<window text>", ...}   (what judges see)
  rating_key.json    — {"TEXT_01": "<target_id>", ...}     (NOT shown to judges; sha'd)
Run BEFORE recover_w114.py --s4 (ratings lock before projections)."""
import json, hashlib, pathlib, random, sys

SEED = 41414

def main(cap_dir):
    cap = pathlib.Path(cap_dir)
    here = pathlib.Path(__file__).resolve().parent
    items = []
    for pdir in sorted(p for p in cap.iterdir() if p.is_dir()):
        g = pdir / "generated_tokens.json"
        if not g.exists():
            print(f"  WARN no generated_tokens.json for {pdir.name}", file=sys.stderr); continue
        toks = json.loads(g.read_text(errors="replace"))
        text = "".join(t["piece"] for t in toks[:128])
        items.append((pdir.name, text))
    rng = random.Random(SEED)
    rng.shuffle(items)
    sheet = {f"TEXT_{i+1:02d}": text for i, (tid, text) in enumerate(items)}
    key   = {f"TEXT_{i+1:02d}": tid  for i, (tid, text) in enumerate(items)}
    (here / "rating_sheet.json").write_text(json.dumps(sheet, indent=2, ensure_ascii=False))
    (here / "rating_key.json").write_text(json.dumps({"seed": SEED, "key": key}, indent=2))
    sha = hashlib.sha256((here / "rating_sheet.json").read_bytes()).hexdigest()
    print(f"{len(items)} texts -> rating_sheet.json (sha {sha[:16]}…), key sealed separately, seed={SEED}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cap_s4")
