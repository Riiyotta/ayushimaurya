#!/usr/bin/env python3
"""Recompute registry.manifest.json (counts, entry points, policy hash) and the README/CHANGELOG
count blocks from what is on disk. Never hand-edit those numbers; verify_all.py recomputes them
with compute_counts() and fails on any difference.

    python3 extraction/update_manifest.py
"""
import glob
import importlib.util
import json
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import policy_hash  # noqa: E402

REPOSITORY_VERSION = "1.0.0"
PAGESPEC_VERSION = "1.0.0"

ENTRY_POINTS = {
    "manifest": "registry.manifest.json",
    "readme": "README.md",
    "changelog": "CHANGELOG.md",
    "pageSpecSchema": "schema/pagespec.schema.json",
    "sectionContractSchema": "schema/section-contract.schema.json",
    "semanticValidator": "schema/semantic_validate.py",
    "adversarialTests": "schema/tests/adversarial_test.py",
    "examples": "schema/examples",
    "templates": "templates/templates.json",
    "routes": "templates/routes.json",
    "sections": "sections",
    "primitives": "primitives",
    "components": "components",
    "compatibilityGraph": "compatibility/graph.json",
    "assetRoles": "assets/asset-roles.json",
    "tokenCatalog": "tokens/llm/token-catalog.json",
    "tokenPolicy": "tokens/llm/token-policy.json",
    "componentAllowlist": "tokens/llm/component-allowlist.json",
    "motionPatterns": "tokens/00-foundation/motion-patterns.json",
    "themes": "tokens/themes",
    "designPolicy": "policy/design-policy.json",
    "sourceBrandRegistry": "policy/source-brand.json",
    "measuredValues": "extraction/measured-values.json",
    "verifyAll": "extraction/verify_all.py",
    "wrapperGate": "extraction/wrapper_gate.py",
    "wrapperWhitelist": "extraction/wrapper-whitelist.json",
    "proveDrift": "extraction/prove_drift.py",
    "classifier": "extraction/classify_routes.py",
    "classifierRules": "extraction/classifier-rules.json",
    "builder": "extraction/build_repo.py",
    "harvester": "extraction/harvest_source_patterns.py",
    "policyHash": "extraction/policy_hash.py",
    "measureTool": "extraction/measure_sections.mjs",
}


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


def _count_module(rel, attr):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return 0
    spec = importlib.util.spec_from_file_location("m_" + attr, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    val = getattr(mod, attr)
    return len(val() if callable(val) else val)


def compute_counts():
    secs = [_load(os.path.relpath(p, REPO)) for p in sorted(glob.glob(os.path.join(REPO, "sections", "*.json")))]
    ex = sorted(glob.glob(os.path.join(REPO, "schema", "examples", "*.json")))
    token_files = [p for d in ("00-foundation", "10-semantic", "20-component", "30-layout", "themes")
                   for p in glob.glob(os.path.join(REPO, "tokens", d, "*.json"))]
    return {
        "tokens": len(_load("tokens/llm/token-catalog.json")["tokens"]),
        "tokenFiles": len(token_files),
        "primitives": len(glob.glob(os.path.join(REPO, "primitives", "*.json"))),
        "components": len(glob.glob(os.path.join(REPO, "components", "*.json"))),
        "sections": len(secs),
        "sectionsRetrievalIneligible": sum(1 for s in secs if s["retrievalEligible"] is False),
        "templates": len(_load("templates/templates.json")["templates"]),
        "routes": len(_load("templates/routes.json")["routes"]),
        "assetRoles": len(_load("assets/asset-roles.json")["roles"]),
        "motionPatterns": len(_load("tokens/00-foundation/motion-patterns.json")["patterns"]),
        "graphRules": len(_load("compatibility/graph.json")["rules"]),
        "examples": len(ex),
        "referenceExamples": sum(1 for p in ex if os.path.basename(p).startswith("reference.")),
        "generatedExamples": sum(1 for p in ex if os.path.basename(p).startswith("generated.")),
        "adversarialCases": _count_module("schema/tests/adversarial_test.py", "build_cases"),
        "driftCases": _count_module("extraction/prove_drift.py", "DRIFTS"),
    }


def manifest(counts):
    allow = _load("tokens/llm/component-allowlist.json")
    sf = _load("extraction/measured-values.json")["sourceSite"]["files"]
    return {
        "repositoryId": "ayushimaurya-portfolio-design-repo",
        "repositoryVersion": REPOSITORY_VERSION,
        "pageSpecVersion": PAGESPEC_VERSION,
        "allowlistVersion": allow["version"],
        "versionFieldNote": "allowlistVersion is machine-checked (verify_all fails unless it equals tokens/llm/component-allowlist.json version). pageSpecVersion is machine-checked against the schema's const. repositoryVersion is documentation-only and hand-maintained; nothing checks it.",
        "status": "design-review-pending",
        "productionApproved": False,
        "approvalNote": "Production approval is a human sign-off; no review has been recorded.",
        "category": "portfolio",
        "categoryEvidence": "policy/design-policy.json#classification.decidedFrom",
        "designPolicy": {
            "policyId": "n0-design-constraints-common",
            "policyVersion": "0.1.0",
            "commonIrVersion": "0.5",
            "enforcementMode": "hard-and-soft",
            "domain": "personal-product-design-portfolio",
            "localExtension": "policy/design-policy.json#localExtension",
            "approval": "defined-pending-architecture-review",
            "architectureDecisionRecorded": False,
            "contentHash": policy_hash.content_hash(),
            "contentHashOf": policy_hash.POLICY_FILES,
        },
        "sourceStack": {
            "documentationOnly": True,
            "kind": "hand-written static HTML + plain CSS + vanilla JavaScript; no framework, no build step, no package manifest",
            "detail": "%d HTML routes, %d stylesheets (%d lines), %d scripts (%d lines), per extraction/measured-values.json#sourceSite; fonts self-hosted locally (Inter, Outfit)" % (
                sf["html"], sf["css"], sf["cssLines"], sf["js"], sf["jsLines"]),
        },
        "defaultTheme": "night",
        "schemaValidatedThemes": ["night", "day"],
        "counts": counts,
        "entryPoints": ENTRY_POINTS,
        "ir": "No IR exists for this repo and none was generated (BASELINE R13).",
        "freshCloneVerification": "Not possible: the source project is not under version control (no git repository), so R14's fresh-clone check could not be run. The design-repo-alone empty-directory run was performed instead.",
    }


COUNT_LABELS = [
    ("tokens", "tokens in the LLM catalog"), ("tokenFiles", "token files (foundation, semantic, component, layout, themes)"),
    ("primitives", "primitives"), ("components", "components"), ("sections", "section contracts"),
    ("sectionsRetrievalIneligible", "of which runtime UI (retrievalEligible: false)"), ("templates", "templates"),
    ("routes", "routes (each mapped exactly once)"), ("assetRoles", "asset/link/copy roles"), ("motionPatterns", "motion patterns"),
    ("graphRules", "compatibility rules"), ("examples", "example PageSpecs"), ("referenceExamples", "of which reference"),
    ("generatedExamples", "of which generated"), ("adversarialCases", "adversarial cases (mutations + controls)"), ("driftCases", "drift cases"),
]


def count_block(counts):
    lines = ["<!-- counts:start (written by extraction/update_manifest.py from disk; verify_all checks it) -->", "", "| count | what |", "|---:|---|"]
    lines += [f"| {counts[k]} | {label} |" for k, label in COUNT_LABELS]
    lines += ["", "<!-- counts:end -->"]
    return "\n".join(lines)


def replace_block(rel, block):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return
    text = open(path, encoding="utf-8").read()
    a, b = text.find("<!-- counts:start"), text.find("<!-- counts:end -->")
    if a < 0 or b < 0:
        return
    text = text[:a] + block + text[b + len("<!-- counts:end -->"):]
    open(path, "w", encoding="utf-8").write(text)


def main(argv):
    counts = compute_counts()
    with open(os.path.join(REPO, "registry.manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest(counts), f, indent=2)
        f.write("\n")
    pol_path = os.path.join(REPO, "policy", "design-policy.json")
    pol = json.load(open(pol_path, encoding="utf-8"))
    pol["enforcedBy"]["contentHash"] = policy_hash.content_hash()
    with open(pol_path, "w", encoding="utf-8") as f:
        json.dump(pol, f, indent=2)
        f.write("\n")
    block = count_block(counts)
    replace_block("README.md", block)
    replace_block("CHANGELOG.md", block)
    print("update_manifest:", json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
