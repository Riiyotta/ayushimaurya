#!/usr/bin/env python3
"""Prove that extraction/verify_all.py catches drift.

    python3 extraction/prove_drift.py

For each case: copy design-repo/ to a fresh OS temp directory, inject one drift, run verify_all
there and require exit 1 with the expected check FAILing. Finally the untouched copy must pass.
When the sibling site exists, SOURCE_SITE_DIR points the copy at it so citation / classifier /
budget / pattern re-derivation checks run too; otherwise those cases are reported as SKIP.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def jedit(rel, fn):
    def run(tmp):
        p = os.path.join(tmp, rel)
        d = json.load(open(p, encoding="utf-8"))
        fn(d)
        json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return run


def tedit(rel, old, new):
    def run(tmp):
        p = os.path.join(tmp, rel)
        s = open(p, encoding="utf-8").read()
        if old not in s:
            raise RuntimeError(f"drift anchor not found in {rel}: {old!r}")
        open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
    return run


def both(*fns):
    def run(tmp):
        for f in fns:
            f(tmp)
    return run


def touch(rel, text=""):
    def run(tmp):
        open(os.path.join(tmp, rel), "w").write(text)
    return run


def first_block_section(d, route, section):
    for b in d["sectionHeights"]["routes"][route]["blocks"]:
        if b["section"] == section:
            return b


DRIFTS = [
    dict(name="phantom allowlist entry", check="allowlist.parity",
         run=jedit("tokens/llm/component-allowlist.json", lambda d: d["primitives"].append("primitive.phantom"))),
    dict(name="orphan section contract (no allowlist entry)", check="allowlist.parity",
         run=lambda t: shutil.copy(os.path.join(t, "sections/conversion.closing.json"), os.path.join(t, "sections/conversion.closing-copy.json"))),
    dict(name="out-of-range citation", check="citations.ranges", sibling=True,
         run=jedit("sections/casestudy.chapter.json", lambda d: d["source"].update(lines="9000-9010", citation=d["source"]["file"] + ":9000-9010"))),
    dict(name="in-range citation at the wrong lines", check="citations.content", sibling=True,
         run=jedit("sections/home.hero.json", lambda d: d["source"].update(
             lines="%d-%s" % (int(d["source"]["lines"].split("-")[0]) + 3, d["source"]["lines"].split("-")[1]),
             citation="%s:%d-%s" % (d["source"]["file"], int(d["source"]["lines"].split("-")[0]) + 3, d["source"]["lines"].split("-")[1])))),
    dict(name="responsive cite not on an @media rule", check="citations.content", sibling=True,
         run=jedit("sections/casestudy.chapter-nav.json", lambda d: d["responsive"][0].update(cite="css/styles.css:9"))),
    dict(name="wrong manifest count", check="manifest",
         run=jedit("registry.manifest.json", lambda d: d["counts"].update(sections=d["counts"]["sections"] + 1))),
    dict(name="README count hand-edited", check="manifest", run=lambda t: tedit("README.md", "| 29 | section contracts |", "| 30 | section contracts |")(t)),
    dict(name="allowlistVersion drift", check="manifest", run=jedit("registry.manifest.json", lambda d: d.update(allowlistVersion="9.9.9"))),
    dict(name="availability edited in the registry", check="assets.availability-pins",
         run=jedit("assets/asset-roles.json", lambda d: d["roles"]["brand.wordmark-logo"].update(availability="generation-safe"))),
    dict(name="pin removed from the semantic validator", check="assets.availability-pins",
         run=tedit("schema/semantic_validate.py", '    "brand.wordmark-logo": "blocked-for-generation",\n', "")),
    dict(name="contract + allowlist flipped together (runtime UI made retrievable)", check="retrieval.pins",
         run=both(jedit("sections/utility.lock-modal.json", lambda d: d.update(retrievalEligible=True)),
                  jedit("tokens/llm/component-allowlist.json", lambda d: [e.update(retrievalEligible=True) for e in d["sections"] if e["id"] == "utility.lock-modal"]))),
    dict(name="retrieval pin removed from the validator", check="retrieval.pins",
         run=tedit("schema/semantic_validate.py", '"utility.mobile-menu", "utility.lock-modal", "utility.desktop-hint",', '"utility.mobile-menu", "utility.desktop-hint",')),
    dict(name="policy content-hash drift (token policy edited)", check="manifest",
         run=jedit("tokens/llm/token-policy.json", lambda d: d["supportedFonts"].append("font.family.text"))),
    dict(name="token file changed, catalog not regenerated", check="tokens.catalog+policy",
         run=jedit("tokens/00-foundation/spacing.json", lambda d: d["tokens"]["space.5"].update(value="1.4rem"))),
    dict(name="catalog edited alone (token removed)", check="tokens.catalog+policy",
         run=jedit("tokens/llm/token-catalog.json", lambda d: d["tokens"].pop(0))),
    dict(name="invented palette value (file + catalog both edited)", check="tokens.catalog+policy",
         run=both(jedit("tokens/00-foundation/color.json", lambda d: d["tokens"]["palette.day.accent-primary"].update(value="#ff00aa")),
                  jedit("tokens/llm/token-catalog.json", lambda d: [t.update(value="#ff00aa") for t in d["tokens"] if t["id"] == "palette.day.accent-primary"]))),
    dict(name="token policy category that does not exist in the catalog", check="tokens.catalog+policy",
         run=jedit("tokens/llm/token-policy.json", lambda d: d["slots"]["radius"].update(category="borderRadius"))),
    dict(name="stale wrapper whitelist", check="wrapper-gate",
         run=jedit("extraction/wrapper-whitelist.json", lambda d: d["entries"][0].update(measuredHeightPx=2400))),
    dict(name="whitelist cap below the measurement", check="wrapper-gate",
         run=jedit("extraction/wrapper-whitelist.json", lambda d: d["entries"][0].update(maxHeightPx=2500))),
    dict(name="measurement no longer matches the classified sequence", check="wrapper-gate",
         run=jedit("extraction/measured-values.json", lambda d: first_block_section(d, "visit-clinic.html", "casestudy.summary").update(section="casestudy.chapter"))),
    dict(name="graph rule without validator implementation", check="graph.agreement",
         run=jedit("compatibility/graph.json", lambda d: d["rules"].append({"id": "NO_TWO_CTAS", "severity": "error", "description": "x", "exceptions": []}))),
    dict(name="motion fallback loosened in motion-patterns.json", check="motion",
         run=jedit("tokens/00-foundation/motion-patterns.json", lambda d: d["patterns"]["scroll-console"].update(reducedMotionFallback="none"))),
    dict(name="route removed from the route table", check="templates.routes",
         run=jedit("templates/routes.json", lambda d: d["routes"].pop())),
    dict(name="route assigned to a template it does not fit", check="templates.routes",
         run=jedit("templates/routes.json", lambda d: [r.update(template="template.case-study-brief") for r in d["routes"] if r["route"] == "hybrid-diagnostic.html"])),
    dict(name="copy budget hand-edited", check="copy-budgets.rederive", sibling=True,
         run=jedit("sections/casestudy.chapter.json", lambda d: d["content"]["fields"]["heading"].update(maxWords=40))),
    dict(name="source pattern removed from the brand registry", check="source-brand.rederive", sibling=True,
         run=jedit("policy/source-brand.json", lambda d: d["sourceBrand"]["patterns"]["person"].pop(0))),
    dict(name="classifier rule changed", check="classifier.rerun", sibling=True,
         run=tedit("extraction/classifier-rules.json", '"variantByClass": [["tint", "tint"]]', '"variantByClass": [["tint", "dark"]]')),
    dict(name="entry point outside the package", check="manifest.entryPoints",
         run=jedit("registry.manifest.json", lambda d: d["entryPoints"].update(ia="../ia.json"))),
    dict(name="absolute machine path in a doc", check="hygiene.absolute-paths",
         run=lambda t: open(os.path.join(t, "CHANGELOG.md"), "a").write("\nbuilt in /" + "Us" + "ers/someone/work/design-repo\n")),
    dict(name="junk file", check="hygiene.junk", run=touch(".DS_Store")),
    dict(name="generated example leaks the owner's name", check="examples",
         run=jedit("schema/examples/generated.home.json", lambda d: d["nodes"][-1]["content"].update(name="Ayushi Maurya"))),
]


def run_verify(tmp, env):
    p = subprocess.run([sys.executable, os.path.join(tmp, "extraction", "verify_all.py")], capture_output=True, text=True, env=env, timeout=600)
    return p.returncode, p.stdout + p.stderr


def main():
    sys.path.insert(0, HERE)
    import classify_routes
    root = classify_routes.source_root()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if root:
        env["SOURCE_SITE_DIR"] = root
    base = tempfile.mkdtemp(prefix="prove-drift-")
    ok_all = True
    try:
        for i, d in enumerate(DRIFTS):
            if d.get("sibling") and not root:
                print(f"SKIP  {d['name']:66} (needs the sibling site)")
                continue
            tmp = os.path.join(base, f"case{i}", "design-repo")
            shutil.copytree(REPO, tmp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            d["run"](tmp)
            rc, out = run_verify(tmp, env)
            failed_checks = {m.group(1) for m in re.finditer(r"^FAIL\s+(\S+)", out, re.M)}
            caught = rc == 1 and d["check"] in failed_checks
            ok_all &= caught
            print(f"{'PASS' if caught else 'FAIL'}  {d['name']:66} -> verify_all exit {rc}, FAIL {sorted(failed_checks)}")
            shutil.rmtree(os.path.dirname(tmp), ignore_errors=True)
        tmp = os.path.join(base, "clean", "design-repo")
        shutil.copytree(REPO, tmp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        rc, out = run_verify(tmp, env)
        print(f"{'PASS' if rc == 0 else 'FAIL'}  {'clean copy (no drift)':66} -> verify_all exit {rc}")
        if rc != 0:
            print(out[-2000:])
        ok_all &= rc == 0
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print(f"\nprove_drift: {len(DRIFTS)} drift cases, {'all caught, clean copy passes' if ok_all else 'NOT all caught'}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
