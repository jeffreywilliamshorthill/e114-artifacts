#!/usr/bin/env python3
"""hf_checkpoint.py — upload artifacts to Jeffrey's PRIVATE HF dataset repo (transport, not publication).

Usage (on box): /venv/main/bin/python hf_checkpoint.py /workspace/convdyn_T.tgz [more files...]

Rationale (2026-07-02): box->HF runs at datacenter uplink speed, so the box becomes
destroyable the moment the upload verifies — the home connection drops off the billed
critical path, and a mid-run box death can no longer eat a finished leg. Raw npy stays
out of git as always; a private repo Jeffrey controls is transport only.
"""
import pathlib, sys
from huggingface_hub import HfApi

tok = pathlib.Path("/workspace/.hf_token").read_text().strip()
api = HfApi(token=tok)
user = api.whoami()["name"]
repo = f"{user}/e114-checkpoints"
api.create_repo(repo, repo_type="dataset", private=True, exist_ok=True)
info = api.repo_info(repo, repo_type="dataset")
assert info.private, f"{repo} is NOT private — refusing to upload"
for f in sys.argv[1:]:
    p = pathlib.Path(f)
    if not p.exists():
        print(f"SKIP missing {p}"); continue
    print(f"uploading {p.name} ({p.stat().st_size/1e6:.1f} MB) -> {repo} ...", flush=True)
    api.upload_file(path_or_fileobj=str(p), path_in_repo=p.name, repo_id=repo, repo_type="dataset")
    print(f"  OK {p.name}", flush=True)
print(f"CHECKPOINT_UPLOAD_DONE https://huggingface.co/datasets/{repo} (private)")
