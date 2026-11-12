#!/usr/bin/env python3
"""One-shot verification of the whole design-repo.

    python3 extraction/verify_all.py          # exit 1 on any FAIL

Works in a design-repo-only copy: checks that need the sibling site (citation needles, classifier
re-run, copy-budget and source-pattern re-derivation) degrade to WARN when it is absent.
Proven to catch drift by extraction/prove_drift.py (each injected drift must make this script fail).

Pins kept here independently of the registries AND of the semantic validator (both are compared):
PINNED_AVAILABILITY, RETRIEVAL_INELIGIBLE, MOTION_FALLBACK, wrapper-gate thresholds (wrapper_gate.py).
"""
import glob
import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "schema"))

PINNED_AVAILABILITY = {
    "brand.wordmark-logo": "blocked-for-generation", "person.portrait-photo": "blocked-for-generation",
    "person.lifestyle-photo": "blocked-for-generation", "decor.hero-reveal-image": "blocked-for-generation",
    "product.case-study-screen": "blocked-for-generation", "product.case-study-video": "blocked-for-generation",
    "product.thumbnail": "blocked-for-generation", "media.side-project-demo": "blocked-for-generation",
    "decor.cloud-illustration": "reference-only", "icon.glyph": "generation-safe",
    "brand.placeholder-wordmark": "generation-safe", "brand.user-supplied-mark": "generation-safe",
    "person.fictional-avatar": "generation-safe", "product.generated-visual": "generation-safe",
    "illustration.generated-decor": "generation-safe", "link.source-url": "reference-only",
    "link.internal-route": "generation-safe", "link.placeholder-url": "generation-safe", "copy.original": "generation-safe",
}
RETRIEVAL_INELIGIBLE = {"utility.mobile-menu", "utility.lock-modal", "utility.desktop-hint", "utility.media-lightbox",
                        "utility.dreams-overlay", "utility.reading-progress"}
MOTION_FALLBACK = {
    "none": "none", "rise-in-on-load": "static-visible", "reveal-on-scroll": "static-visible", "scroll-console": "show-all-steps",
    "scroll-pinned-panels": "show-all-steps", "scroll-stepper": "show-all-steps", "ambient-drift": "static-visible",
    "interactive-canvas-field": "static-first-frame", "box-open": "static-visible", "card-flip": "instant-state-change",
    "modal-pop": "instant-state-change", "autoplay-loop-video": "pause-media", "sticky-chapter-nav": "instant-state-change",
    "theme-crossfade": "instant-state-change",
}
RUNTIME_UI = re.compile(r"modal|dialog|overlay|lightbox|menu|banner|toast|hint|progress|cookie|consent|drawer|preloader|cursor|popup", re.I)
CITE = re.compile(r"^((?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:html|css|js|mjs)):(\d+)(?:-(\d+))?$")
_U, _P = "Us" + "ers", "pri" + "vate"   # split so this file does not itself contain the patterns it hunts
ABS_PATH = re.compile(r"/%s/[A-Za-z0-9._-]+/|/home/[A-Za-z0-9._-]+/|/%s/(tmp|var)/|C:\\%s\\" % (_U, _P, _U))

results = []


def rec(status, check, msg):
    results.append((status, check, msg))


def load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


def source_root():
    import classify_routes
    return classify_routes.source_root()


def main():
    root = source_root()
    if root is None:
        rec("WARN", "sibling-site", "sibling source site not present: citation needles, classifier re-run, budget and pattern re-derivation skipped")

    # ---------------------------------------------------------------- hygiene / self-containment
    files = [os.path.join(d, f) for d, _, fs in os.walk(REPO) for f in fs]
    junk = [os.path.relpath(p, REPO) for p in files if os.path.basename(p) in (".DS_Store", "Thumbs.db", "desktop.ini") or "__pycache__" in p or "__MACOSX" in p or p.endswith(".pyc")]
    rec("FAIL" if junk else "PASS", "hygiene.junk", junk[:5] if junk else "no .DS_Store/__pycache__/__MACOSX/pyc files")
    abs_hits = []
    for p in files:
        if p.endswith((".json", ".md", ".py", ".mjs", ".txt")) or os.path.basename(p) == ".gitignore":
            with open(p, encoding="utf-8", errors="ignore") as f:
                if ABS_PATH.search(f.read()):
                    abs_hits.append(os.path.relpath(p, REPO))
    rec("FAIL" if abs_hits else "PASS", "hygiene.absolute-paths", abs_hits or "no absolute machine paths")
    bad_json = []
    for p in files:
        if p.endswith(".json"):
            try:
                json.load(open(p, encoding="utf-8"))
            except Exception as e:
                bad_json.append(f"{os.path.relpath(p, REPO)}: {e}")
    rec("FAIL" if bad_json else "PASS", "hygiene.json-parse", bad_json or f"{sum(1 for p in files if p.endswith('.json'))} JSON files parse")
    man = load("registry.manifest.json")
    eps = man["entryPoints"]
    bad_ep = [v for v in eps.values() if v.startswith("..") or os.path.isabs(v) or not os.path.exists(os.path.join(REPO, v))]
    rec("FAIL" if bad_ep else "PASS", "manifest.entryPoints", bad_ep or f"{len(eps)} entry points, all inside design-repo and present")

    # ---------------------------------------------------------------- section contracts
    from jsonschema import Draft7Validator
    cschema = load("schema/section-contract.schema.json")
    sections = {}
    errs = []
    for p in sorted(glob.glob(os.path.join(REPO, "sections", "*.json"))):
        c = json.load(open(p, encoding="utf-8"))
        fn = os.path.basename(p)[:-5]
        for e in Draft7Validator(cschema).iter_errors(c):
            errs.append(f"{fn}: {e.message[:120]}")
        if c.get("id") != fn or c.get("semantic", {}).get("id") != fn:
            errs.append(f"{fn}: id / semantic.id must equal the filename")
        if c.get("source", {}).get("id") == c.get("semantic", {}).get("id"):
            errs.append(f"{fn}: source.id must not equal semantic.id")
        sections[fn] = c
    rec("FAIL" if errs else "PASS", "contracts.schema+provenance", errs[:6] or f"{len(sections)} contracts valid; source/semantic split holds")

    # ---------------------------------------------------------------- citations
    def check_range(cite):
        m = CITE.match(cite)
        if not m:
            return f"malformed citation {cite!r}"
        if root is None:
            return None
        path = os.path.join(root, m.group(1))
        if not os.path.isfile(path):
            return f"{cite}: file missing in source"
        n = len(open(path, encoding="utf-8").read().split("\n"))
        a, b = int(m.group(2)), int(m.group(3) or m.group(2))
        if not (1 <= a <= b <= n):
            return f"{cite}: range outside 1-{n}"
        return None

    def lines_of(rel):
        return open(os.path.join(root, rel), encoding="utf-8").read().split("\n")

    cite_errs, n_cites = [], 0
    for p in files:
        if not p.endswith(".json") or os.path.basename(p) == "source-brand.json":
            continue
        data = json.load(open(p, encoding="utf-8"))
        stack = [data]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                stack.extend(o.values())
            elif isinstance(o, list):
                stack.extend(o)
            elif isinstance(o, str) and CITE.match(o):
                n_cites += 1
                err = check_range(o)
                if err:
                    cite_errs.append(f"{os.path.relpath(p, REPO)}: {err}")
    if root is None:
        rec("WARN", "citations.ranges", f"{n_cites} citations found; ranges not checked (no sibling site)")
    else:
        rec("FAIL" if cite_errs else "PASS", "citations.ranges", cite_errs[:6] or f"{n_cites} path:line citations resolve inside their real files")
    if root is not None:
        errs = []
        for sid, c in sections.items():
            s = c["source"]
            m = CITE.match(s["citation"])
            if not m or s["citation"] != f"{s['file']}:{s['lines']}":
                errs.append(f"{sid}: citation/file/lines disagree")
                continue
            ls = lines_of(s["file"])
            a, b = int(m.group(2)), int(m.group(3) or m.group(2))
            if not (1 <= a <= b <= len(ls)):
                errs.append(f"{sid}: {s['citation']} outside the file")
                continue
            if s["file"].endswith(".html"):
                start = ls[a - 1]
                classes = [x for x in s["selector"].split(".")[1:] if x]
                if f"<{s['tag']}" not in start or any(cl not in start for cl in classes):
                    errs.append(f"{sid}: <{s['tag']}> with {classes} not at {s['citation']}")
                if f"</{s['tag']}>" not in ls[b - 1] and not ls[b - 1].strip().endswith(">"):
                    errs.append(f"{sid}: cited range does not end at a closing tag ({s['citation']})")
            else:
                if not any(s["tag"] in ln for ln in ls[a - 1:b]):
                    errs.append(f"{sid}: needle {s['tag']!r} not in {s['citation']}")
            for r in c.get("responsive", []):
                m2 = CITE.match(r["cite"])
                if m2 and m2.group(1).endswith(".css") and (int(m2.group(2)) > len(lines_of(m2.group(1))) or "@media" not in lines_of(m2.group(1))[int(m2.group(2)) - 1]):
                    errs.append(f"{sid}: responsive cite {r['cite']} does not start at an @media rule")
        mv = load("extraction/measured-values.json")
        for fact in mv.get("citations", []):
            m = CITE.match(fact["cite"])
            if not m or int(m.group(2)) > len(lines_of(m.group(1))) or fact["needle"] not in lines_of(m.group(1))[int(m.group(2)) - 1]:
                errs.append(f"measured-values citation {fact['cite']} no longer contains its needle")
        rec("FAIL" if errs else "PASS", "citations.content", errs[:6] or "source tags/classes at every contract citation; @media at every responsive cite; every measured-values needle found")

    # ---------------------------------------------------------------- allowlist parity
    allow = load("tokens/llm/component-allowlist.json")
    schema = load("schema/pagespec.schema.json")
    errs = []
    for kind, d in (("primitives", "primitives"), ("components", "components")):
        on_disk = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(REPO, d, "*.json"))}
        listed = set(allow[kind])
        if on_disk != listed:
            errs.append(f"{kind}: phantom {sorted(listed - on_disk)} orphan {sorted(on_disk - listed)}")
    listed = {s["id"] for s in allow["sections"]}
    if listed != set(sections):
        errs.append(f"sections: phantom {sorted(listed - set(sections))} orphan {sorted(set(sections) - listed)}")
    for s in allow["sections"]:
        c = sections.get(s["id"])
        if c and (s["variants"] != c["variants"] or s["settableContentFields"] != sorted(c["content"]["fields"]) or s["allowedMotion"] != c["motion"]["allowedPatterns"]):
            errs.append(f"{s['id']}: allowlist entry disagrees with the contract")
    node_props = sorted(schema["definitions"]["node"]["properties"])
    if sorted(allow["nodeProperties"]) != node_props:
        errs.append(f"nodeProperties {allow['nodeProperties']} != schema {node_props}")
    if sorted(allow["motionProperties"]) != sorted(schema["definitions"]["motion"]["properties"]):
        errs.append("motionProperties disagree with schema")
    policy = load("tokens/llm/token-policy.json")
    if sorted(allow["styleSlots"]) != sorted(schema["definitions"]["style"]["properties"]) or sorted(allow["styleSlots"]) != sorted(policy["slots"]):
        errs.append("styleSlots disagree between allowlist, schema and token policy")
    rec("FAIL" if errs else "PASS", "allowlist.parity", errs[:6] or "allowlist == primitives/components/sections on disk == schema node/motion/style properties")

    # ---------------------------------------------------------------- manifest
    import update_manifest
    import policy_hash
    errs = []
    if man.get("allowlistVersion") != allow["version"]:
        errs.append(f"allowlistVersion {man.get('allowlistVersion')} != allowlist {allow['version']}")
    if man.get("pageSpecVersion") != schema["properties"]["pageSpecVersion"]["const"]:
        errs.append("pageSpecVersion != schema const")
    counts = update_manifest.compute_counts()
    if man.get("counts") != counts:
        diff = {k: (man.get("counts", {}).get(k), v) for k, v in counts.items() if man.get("counts", {}).get(k) != v}
        errs.append(f"manifest counts drift (manifest, disk): {diff}")
    block = update_manifest.count_block(counts)
    for doc in ("README.md", "CHANGELOG.md"):
        if not os.path.exists(os.path.join(REPO, doc)):
            errs.append(f"{doc} missing")
        elif block not in open(os.path.join(REPO, doc), encoding="utf-8").read():
            errs.append(f"{doc} count block is not the one recomputed from disk")
    if man.get("status") != "design-review-pending" or man.get("productionApproved") is not False:
        errs.append("status must be design-review-pending and productionApproved false")
    hv = policy_hash.content_hash()
    pol = load("policy/design-policy.json")
    if man.get("designPolicy", {}).get("contentHash") != hv or pol["enforcedBy"]["contentHash"] != hv:
        errs.append(f"policy contentHash drift: manifest {man.get('designPolicy', {}).get('contentHash')} / policy {pol['enforcedBy']['contentHash']} / recomputed {hv}")
    if pol["classification"]["approval"]["status"] != "defined-pending-architecture-review" or pol["classification"]["approval"]["architectureDecisionRecorded"] is not False:
        errs.append("policy approval must stay defined-pending-architecture-review / architectureDecisionRecorded false")
    if man.get("category") != pol["classification"]["category"]:
        errs.append("manifest category != policy classification")
    readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read() if os.path.exists(os.path.join(REPO, "README.md")) else ""
    wording = (readme + json.dumps(man) + json.dumps(pol)).lower()
    if "s" + "aas" in wording:
        errs.append("non-applicable business-category wording found in README/manifest/policy")
    rec("FAIL" if errs else "PASS", "manifest", errs[:6] or f"versions, counts {counts['sections']} sections/{counts['tokens']} tokens, README/CHANGELOG blocks, status and policy hash {hv[:19]}... all agree")

    # ---------------------------------------------------------------- tokens
    errs = []
    token_files = sorted(p for d in ("00-foundation", "10-semantic", "20-component", "30-layout") for p in glob.glob(os.path.join(REPO, "tokens", d, "*.json"))
                         if not p.endswith("motion-patterns.json"))
    derived = {}
    palette = load("tokens/00-foundation/color.json")["tokens"]
    for p in token_files:
        for tid, t in json.load(open(p, encoding="utf-8"))["tokens"].items():
            if tid in derived:
                errs.append(f"duplicate token id {tid}")
            if "themes" in t and "/10-semantic/" in p:
                vals = {}
                for th, ref in t["themes"].items():
                    r = ref.strip("{}")
                    if r not in palette:
                        errs.append(f"{tid}: reference {ref} does not resolve")
                    else:
                        vals[th] = palette[r]["value"]
                derived[tid] = ("themes", vals)
            elif "themes" in t:
                derived[tid] = ("themes", t["themes"])
            else:
                derived[tid] = ("value", t.get("value"))
    cat = load("tokens/llm/token-catalog.json")
    catalog = {t["id"]: t for t in cat["tokens"]}
    if set(catalog) != set(derived):
        errs.append(f"catalog ids out of sync: only in catalog {sorted(set(catalog) - set(derived))[:4]}, only in files {sorted(set(derived) - set(catalog))[:4]}")
    for tid, (kind, v) in derived.items():
        c = catalog.get(tid)
        if c is not None and c.get(kind) != v:
            errs.append(f"catalog value drift for {tid}: catalog {c.get(kind)} files {v}")
    if cat.get("count") != len(cat["tokens"]):
        errs.append("catalog count field wrong")
    for th in ("night", "day"):
        tf = load(f"tokens/themes/{th}.json")
        for sid, val in tf["resolves"].items():
            if derived.get(sid, (None, {}))[1].get(th) != val:
                errs.append(f"themes/{th}.json {sid}={val} disagrees with semantic tokens")
    if not load("tokens/themes/night.json")["default"] or man.get("defaultTheme") != "night":
        errs.append("night must be the default theme (measured: inline head script)")
    # values come from measured custom properties (no invented values)
    mv = load("extraction/measured-values.json")
    site = mv["resolvedCustomProperties"]["site"]
    for tid, t in palette.items():
        prop = t.get("cssProperty", "")
        if re.fullmatch(r"--[a-z0-9-]+", prop):
            th = t.get("theme", "day")
            if site[th].get(prop, "").lower().replace(" ", "") != t["value"].lower().replace(" ", ""):
                errs.append(f"{tid}={t['value']} not equal to measured {prop} ({th}) {site[th].get(prop)}")
    # policy categories and prefixes resolve against the real catalog
    cats = {t["category"] for t in cat["tokens"]}
    for slot, s in policy["slots"].items():
        if s["category"] not in cats:
            errs.append(f"token-policy slot {slot}: category {s['category']} not in catalog categories")
        for px in s["prefixes"]:
            if not any(t.startswith(px) for t in catalog):
                errs.append(f"token-policy slot {slot}: prefix {px} matches no token")
    for f_ in policy["supportedFonts"]:
        if f_ not in catalog:
            errs.append(f"supported font {f_} not in catalog")
    used = set()
    for c in sections.values():
        used |= set(c["tokens"])
    for d in ("primitives", "components"):
        for p in glob.glob(os.path.join(REPO, d, "*.json")):
            used |= set(json.load(open(p, encoding="utf-8"))["tokens"])
    missing = sorted(u for u in used if u not in catalog)
    if missing:
        errs.append(f"contracts reference unknown tokens {missing[:5]}")
    fams = set(mv["styleHistograms"]["themes"]["night"]["fontFamily"])
    if fams != {"Inter", "Outfit"}:
        errs.append(f"measured font families {fams} differ from the two catalogued families")
    rec("FAIL" if errs else "PASS", "tokens.catalog+policy", errs[:6] or f"{len(catalog)} catalog tokens == token files; themes resolve; palette == measured custom properties; policy categories/prefixes/fonts resolve")

    # ---------------------------------------------------------------- asset roles (pinned)
    import semantic_validate as sv
    roles = load("assets/asset-roles.json")["roles"]
    errs = []
    if sv.PINNED_AVAILABILITY != PINNED_AVAILABILITY:
        errs.append("semantic_validate.PINNED_AVAILABILITY differs from verify_all's pin")
    for rid, want in PINNED_AVAILABILITY.items():
        got = roles.get(rid, {}).get("availability")
        if got != want:
            errs.append(f"{rid}: registry availability {got!r}, pinned {want!r}")
    for rid, r in roles.items():
        if rid not in PINNED_AVAILABILITY:
            errs.append(f"{rid}: not pinned")
        if r["availability"] != "generation-safe":
            subs = r.get("generationSafeSubstitutes") or []
            if not subs or any(PINNED_AVAILABILITY.get(s) != "generation-safe" for s in subs):
                errs.append(f"{rid}: needs generation-safe substitutes, has {subs}")
    if roles.get("brand.wordmark-logo", {}).get("generationPolicy") in ("must-reuse-exact", "may-generate-new"):
        errs.append("brand.wordmark-logo must never be reusable or generatable")
    asset_enum = set(schema["definitions"]["asset"]["properties"]["role"]["enum"])
    link_enum = set(schema["definitions"]["link"]["properties"]["role"]["enum"])
    if asset_enum != {k for k, v in roles.items() if v["appliesTo"] == "asset"} or link_enum != {k for k, v in roles.items() if v["appliesTo"] == "link"}:
        errs.append("schema asset/link role enums differ from the registry")
    for sid, c in sections.items():
        for r in c["assetRoles"] + c["generatedAssetRoles"]:
            if r not in roles:
                errs.append(f"{sid}: unknown asset role {r}")
        for r in c["generatedAssetRoles"]:
            if PINNED_AVAILABILITY.get(r) != "generation-safe":
                errs.append(f"{sid}: generatedAssetRoles contains non-generation-safe {r}")
    rec("FAIL" if errs else "PASS", "assets.availability-pins", errs[:6] or f"{len(roles)} roles == PINNED_AVAILABILITY (here and in the validator); substitutes generation-safe; schema enums agree")

    # ---------------------------------------------------------------- retrieval eligibility (pinned)
    errs = []
    if sv.RETRIEVAL_INELIGIBLE != RETRIEVAL_INELIGIBLE:
        errs.append("semantic_validate.RETRIEVAL_INELIGIBLE differs from verify_all's pin")
    allow_s = {s["id"]: s for s in allow["sections"]}
    for sid, c in sections.items():
        want = sid not in RETRIEVAL_INELIGIBLE
        if c["retrievalEligible"] is not want:
            errs.append(f"{sid}: contract retrievalEligible={c['retrievalEligible']}, pin says {want}")
        if allow_s.get(sid, {}).get("retrievalEligible") is not want:
            errs.append(f"{sid}: allowlist retrievalEligible disagrees with pin")
        if (RUNTIME_UI.search(sid) or RUNTIME_UI.search(c["title"])) and sid not in RETRIEVAL_INELIGIBLE:
            errs.append(f"{sid}: looks like runtime UI but is not pinned ineligible")
        if not want and len(c.get("retrievalReason", "")) < 30:
            errs.append(f"{sid}: retrievalReason missing or < 30 chars")
    for sid in RETRIEVAL_INELIGIBLE:
        if sid not in sections:
            errs.append(f"pinned {sid} has no contract")
    rec("FAIL" if errs else "PASS", "retrieval.pins", errs[:6] or f"{len(RETRIEVAL_INELIGIBLE)} runtime-UI sections ineligible in contracts, allowlist and both pins")

    # ---------------------------------------------------------------- motion
    errs = []
    mp = load("tokens/00-foundation/motion-patterns.json")["patterns"]
    if sv.MOTION_FALLBACK != MOTION_FALLBACK:
        errs.append("semantic_validate.MOTION_FALLBACK differs from verify_all's pin")
    if {k: v["reducedMotionFallback"] for k, v in mp.items()} != MOTION_FALLBACK:
        errs.append("motion-patterns.json fallbacks differ from the pin")
    if sorted(schema["definitions"]["motion"]["properties"]["pattern"]["enum"]) != sorted(mp):
        errs.append("schema motion pattern enum differs from motion-patterns.json")
    if schema["definitions"]["motion"].get("additionalProperties") is not False or "reducedMotionFallback" not in schema["definitions"]["motion"]["required"]:
        errs.append("motion schema must be closed and require reducedMotionFallback")
    for sid, c in sections.items():
        if not set(c["motion"]["allowedPatterns"]) <= set(mp) or c["motion"]["default"] not in c["motion"]["allowedPatterns"]:
            errs.append(f"{sid}: motion patterns not closed over motion-patterns.json")
    rec("FAIL" if errs else "PASS", "motion", errs[:6] or f"{len(mp)} patterns, fallbacks pinned in 3 places, schema closed")

    # ---------------------------------------------------------------- graph <-> validator agreement
    graph = load("compatibility/graph.json")
    gids = {r["id"] for r in graph["rules"]}
    bad = [r["id"] for r in graph["rules"] if r["severity"] not in ("error", "warn")]
    if gids != sv.GRAPH_RULES_IMPLEMENTED or bad:
        rec("FAIL", "graph.agreement", f"graph-only {sorted(gids - sv.GRAPH_RULES_IMPLEMENTED)}, validator-only {sorted(sv.GRAPH_RULES_IMPLEMENTED - gids)}, bad severity {bad}")
    else:
        rec("PASS", "graph.agreement", f"{len(gids)} graph rules == validator implementations")

    # ---------------------------------------------------------------- templates / routes (R11)
    templates = load("templates/templates.json")["templates"]
    routes = load("templates/routes.json")["routes"]
    errs = []
    names = [r["route"] for r in routes]
    if len(names) != len(set(names)):
        errs.append("a route is mapped more than once")
    for tid, t in templates.items():
        if sorted(t["routes"]) != sorted(r["route"] for r in routes if r["template"] == tid):
            errs.append(f"{tid}: template routes disagree with routes.json")
        for n in t["nodes"]:
            for s in n["sections"]:
                if s not in sections:
                    errs.append(f"{tid}: unknown section {s}")
        for o in t["overlays"]:
            if not sections.get(o, {}).get("constraints", {}).get("overlayOnly"):
                errs.append(f"{tid}: overlay {o} is not an overlay-only contract")
    for r in routes:
        nodes = [{"section": x.split("[")[0], "variant": x.split("[")[1].rstrip("]")} for x in r["classifiedSequence"]]
        m = sv.match_template(nodes, templates[r["template"]])
        if m:
            errs.append(f"{r['route']}: recorded sequence does not fit {r['template']}: {m[0][:120]}")
        others = [tid for tid, t in templates.items() if tid != r["template"] and not sv.match_template(nodes, t)]
        if others:
            errs.append(f"{r['route']}: also matches {others} (templates must be disjoint)")
    if root is not None:
        served = sorted(os.path.basename(p) for p in glob.glob(os.path.join(root, "*.html")))
        if served != sorted(names):
            errs.append(f"route table != served pages: unmapped {sorted(set(served) - set(names))}, missing {sorted(set(names) - set(served))}")
    rec("FAIL" if errs else "PASS", "templates.routes", errs[:6] or f"{len(routes)} routes mapped exactly once; every recorded sequence fits exactly its own template")
    if root is not None:
        import classify_routes
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = classify_routes.main(["--check"])
        tail = [ln for ln in buf.getvalue().splitlines() if ln.startswith("FAIL")]
        rec("FAIL" if rc else "PASS", "classifier.rerun", tail[:4] or "classifier re-run on the live DOM reproduces every recorded sequence and template match")

    # graph rules hold on the real sequences (rules checked against the files they describe)
    errs, warns = [], []
    reg = sv.Registry()
    for r in routes:
        nodes = []
        for x in r["classifiedSequence"]:
            sid, var = x.split("[")[0], x.split("[")[1].rstrip("]")
            pat = sections[sid]["motion"]["default"]
            nodes.append({"section": sid, "variant": var, "content": {}, "motion": {"pattern": pat, "reducedMotionFallback": MOTION_FALLBACK[pat]}})
        rep = sv.Report()
        sev = {g["id"]: g["severity"] for g in graph["rules"]}
        sv.graph_rules({"nodes": nodes, "overlays": []}, templates[r["template"]], reg, sev, rep)
        errs += [f"{r['route']}: {i['rule']} {i['message']}" for i in rep.errors]
        warns += [f"{r['route']}: {i['rule']}" for i in rep.warnings]
    rec("FAIL" if errs else "PASS", "graph.on-real-sequences", errs[:4] or f"every error-severity rule holds on all {len(routes)} real route sequences ({len(warns)} warn-level notices)")

    # ---------------------------------------------------------------- examples (schema + semantic)
    errs = []
    ex = sorted(glob.glob(os.path.join(REPO, "schema", "examples", "*.json")))
    seen = {}
    for p in ex:
        spec = json.load(open(p, encoding="utf-8"))
        rep = sv.validate(spec, reg)
        if rep.errors:
            errs.append(f"{os.path.basename(p)}: {[(i['rule'], i['path']) for i in rep.errors[:3]]}")
        seen.setdefault(spec["template"], set()).add(spec["mode"])
    for tid in templates:
        if seen.get(tid) != {"reference", "generated"}:
            errs.append(f"{tid}: needs one reference and one generated example (has {seen.get(tid)})")
    rec("FAIL" if errs else "PASS", "examples", errs[:6] or f"{len(ex)} examples pass Draft-07 + semantic validation; every template has a reference and a generated example")

    # ---------------------------------------------------------------- wrapper gate (R9)
    import wrapper_gate
    g_err, g_warn = wrapper_gate.run(REPO)
    for w in g_warn:
        rec("WARN", "wrapper-gate", w)
    rec("FAIL" if g_err else "PASS", "wrapper-gate", g_err[:6] or "every route measured at 1440px; no unreviewed HERO > 3000px or section > 60% of its page")

    # ---------------------------------------------------------------- re-derivation from the source (R16)
    if root is not None:
        import build_repo
        import classify_routes
        src = build_repo.Source(root)
        rules = classify_routes.load_rules()
        classified = {r: classify_routes.classify(root, r, rules) for r in names}
        budgets = build_repo.compute_budgets(src, classified)
        errs = []

        def cmp(sid, path, fspec, b):
            for k in ("maxWords", "maxItems"):
                if fspec.get(k) != b.get(k):
                    errs.append(f"{sid}.{path}: contract {k}={fspec.get(k)} source says {b.get(k)}")
            for k, sub in (fspec.get("item") or {}).items():
                cmp(sid, f"{path}.{k}", sub, (b.get("item") or {}).get(k, {}))

        for sid, c in sections.items():
            if sid not in budgets:
                errs.append(f"{sid}: contract has no evidence spec in extraction/build_spec.py")
                continue
            for k, f in c["content"]["fields"].items():
                if k not in budgets[sid]:
                    errs.append(f"{sid}.{k}: field has no evidence spec")
                    continue
                cmp(sid, k, f, budgets[sid][k])
        rec("FAIL" if errs else "PASS", "copy-budgets.rederive", errs[:5] or "every maxWords/maxItems equals a fresh measurement of the source DOM")
        import harvest_source_patterns
        fresh = harvest_source_patterns.harvest(root)
        rec("PASS" if fresh == load("policy/source-brand.json") else "FAIL", "source-brand.rederive",
            "policy/source-brand.json equals a fresh harvest" if fresh == load("policy/source-brand.json") else "policy/source-brand.json differs from a fresh harvest of the source")
        secret = re.search(r"const PASSWORD = '([^']+)'", open(os.path.join(root, "js", "lock.js"), encoding="utf-8").read())
        if secret:
            leaked = [os.path.relpath(p, REPO) for p in files if secret.group(1) in open(p, encoding="utf-8", errors="ignore").read()]
            rec("FAIL" if leaked else "PASS", "secret.not-copied", leaked or "the locked-project password (read at runtime from the source, never stored) appears in no repo file")

    # ---------------------------------------------------------------- report
    for status, check, msg in results:
        print(f"{status:4}  {check:28} {msg}")
    fails = sum(1 for s, _, _ in results if s == "FAIL")
    warns = sum(1 for s, _, _ in results if s == "WARN")
    print(f"\nverify_all: {len(results) - fails - warns} pass, {fails} fail, {warns} warn")
    return 1 if fails else 0


def run():
    try:
        return main()
    except Exception as e:  # a crash is a failure, never a silent pass; print what was checked so far
        import traceback
        rec("FAIL", "verify_all.crash", f"{type(e).__name__}: {e} | {traceback.format_exc().splitlines()[-3].strip()}")
        for status, check, msg in results:
            print(f"{status:4}  {check:28} {msg}")
        print("\nverify_all: crashed (counted as FAIL)")
        return 1


if __name__ == "__main__":
    sys.exit(run())
