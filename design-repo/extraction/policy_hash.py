#!/usr/bin/env python3
"""Content hash of the files the design policy is enforced by.

    python3 extraction/policy_hash.py          # print sha256:<hex>
    python3 extraction/policy_hash.py --check  # exit 1 if registry.manifest.json / policy/design-policy.json disagree

hash = sha256 over sorted lines "<relative path>\\0<sha256 of file bytes>\\n" for POLICY_FILES.
verify_all.py recomputes it on every run.
"""
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_FILES = [
    "tokens/llm/token-policy.json",
    "compatibility/graph.json",
    "schema/pagespec.schema.json",
    "schema/semantic_validate.py",
]


def content_hash(root=REPO):
    h = hashlib.sha256()
    for rel in sorted(POLICY_FILES):
        with open(os.path.join(root, rel), "rb") as f:
            h.update(f"{rel}\0{hashlib.sha256(f.read()).hexdigest()}\n".encode())
    return "sha256:" + h.hexdigest()


def main(argv):
    hv = content_hash()
    if "--check" in argv:
        man = json.load(open(os.path.join(REPO, "registry.manifest.json")))
        pol = json.load(open(os.path.join(REPO, "policy", "design-policy.json")))
        ok = man["designPolicy"]["contentHash"] == hv and pol["enforcedBy"]["contentHash"] == hv
        print(("PASS" if ok else "FAIL") + f" policy contentHash {hv}")
        return 0 if ok else 1
    print(hv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
