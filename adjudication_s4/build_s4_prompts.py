#!/usr/bin/env python3
"""Build s4_prompts.tsv for the §4 main capture: 44 frozen targets (raw `setup`
continuations) + 4 worldview probes (`prompt`), verbatim from the frozen JSONs.
Runs on the box (/workspace/prework) or locally. Format: id<TAB>text, one per line
(raw base-model continuations — no chat template, no think suffix, single-line)."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
def find(name):
    for d in (HERE, HERE.parent / "prework", pathlib.Path("/workspace/prework")):
        if (d / name).exists(): return d / name
    raise SystemExit(f"cannot find {name}")

targets = json.loads(find("target_set_v1.json").read_text())
probes  = json.loads(find("worldview_probes_v1.json").read_text())
out = find("target_set_v1.json").parent / "s4_prompts.tsv"

rows = []
for t in targets:
    text = t["setup"]
    assert "\t" not in text and "\n" not in text, t["id"]
    rows.append((t["id"], text))
for p in probes:
    text = p["prompt"]
    assert "\t" not in text and "\n" not in text, p["id"]
    rows.append((p["id"], text))

with out.open("w") as f:
    for i, text in rows:
        f.write(f"{i}\t{text}\n")
print(f"wrote {len(rows)} prompts ({len(targets)} targets + {len(probes)} probes) -> {out}")
