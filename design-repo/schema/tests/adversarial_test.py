#!/usr/bin/env python3
"""Adversarial suite: every mutation must be rejected (or, for warn-level rules, flagged);
every control must pass with zero errors.

    python3 schema/tests/adversarial_test.py        # exit 1 on any unexpected result

Controls: every example under schema/examples/ (reference examples keep their real assets) plus
one control synthesized generically from each template's own node list (so a new template is
covered with no new test code). Mutations cover the generated-mode leakage rules (R2/R5),
asset availability pins (R3), retrieval eligibility at node/contract/allowlist level (R8), the
wrapper gate (R9), the token policy (R10), template/node mismatches, word budgets and motion.
"""
import copy
import glob
import json
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
TESTS = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.dirname(TESTS)
REPO = os.path.dirname(SCHEMA_DIR)
sys.path.insert(0, SCHEMA_DIR)
sys.path.insert(0, os.path.join(REPO, "extraction"))
import semantic_validate as sv  # noqa: E402

EX = os.path.join(SCHEMA_DIR, "examples")


def ex(name):
    with open(os.path.join(EX, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def node(spec, section, k=0):
    hits = [n for n in spec["nodes"] if n["section"] == section]
    return hits[k]


# ---------------------------------------------------------------- synthesized controls
def synth_value(f, slot, reg_roles):
    t = f["type"]
    if t == "text":
        return " ".join(["Sample", "text", "here"][: max(1, min(3, f.get("maxWords") or 1))])
    if t == "boolean":
        return False
    if t == "textList":
        return ["Sample item"][: f.get("maxItems", 1)] if (f.get("maxWords") or 0) >= 2 else ["Sample"]
    if t == "link":
        return {"label": "Open", "href": "#top", "role": "link.internal-route"}
    if t == "links":
        return [{"label": "Open", "href": "#top", "role": "link.internal-route"}]
    if t in ("asset", "assets"):
        a = {"role": reg_roles[0], "src": f"placeholder://sample/{slot}", "mediaType": "image"}
        return a if t == "asset" else [a]
    if t in ("list", "meta", "object"):
        item = {k: synth_value(v, slot, reg_roles) for k, v in f["item"].items() if v.get("required")}
        return item if t == "object" else [item]
    raise ValueError(t)


def synthesize(tid, reg):
    t = reg.templates[tid]
    nodes = []
    for slot in t["nodes"]:
        count = max(slot.get("minCount", 1), 1) if slot["required"] else 0
        for _ in range(count):
            sid = slot["sections"][0]
            c = reg.sections[sid]
            variant = (slot.get("variants") or {}).get(sid, c["variants"])[0]
            roles = c["generatedAssetRoles"] or ["product.generated-visual"]
            content = {}
            for k, f in c["content"]["fields"].items():
                if f.get("required") or variant in f.get("requiredForVariants", []):
                    content[k] = synth_value(f, slot["slot"], roles)
            if sid == "shell.header":
                content["themeToggle"] = True
            pat = c["motion"]["default"]
            nodes.append({"section": sid, "variant": variant, "content": content,
                          "motion": {"pattern": pat, "reducedMotionFallback": sv.MOTION_FALLBACK[pat]}})
    return {"pageSpecVersion": "1.0.0", "mode": "generated", "template": tid, "route": "/sample-" + tid.split(".")[1],
            "theme": "night", "meta": {"title": "Sample page"}, "nodes": nodes}


# ---------------------------------------------------------------- mutation helpers
def M(name, base, fn, expect, reg_fn=None, severity="error"):
    return {"name": name, "kind": "mutation", "base": base, "fn": fn, "expect": set(expect), "reg_fn": reg_fn, "severity": severity}


def set_path(path, value):
    def fn(s):
        o = s
        for k in path[:-1]:
            o = o[k]
        o[path[-1]] = value
    return fn


def build_cases():
    cases = []
    for p in sorted(glob.glob(os.path.join(EX, "*.json"))):
        cases.append({"name": "control:" + os.path.basename(p)[:-5], "kind": "control", "base": os.path.basename(p)[:-5]})
    reg = sv.Registry()
    for tid in sorted(reg.templates):
        cases.append({"name": "control:synthesized:" + tid, "kind": "control", "synth": tid})

    G_HOME, G_BRIEF, G_CHAP, G_RES, G_IDX, G_NDA = ("generated.home", "generated.case-study-brief", "generated.case-study-chaptered",
                                                   "generated.resume", "generated.project-index", "generated.notice")
    R_BRIEF = "reference.case-study-brief"

    def hero(s): return node(s, "home.hero")
    def cshero(s): return node(s, "casestudy.hero")

    # ---- R2/R5 generated-mode leakage
    cases += [
        M("leak:brand-employer", G_HOME, lambda s: hero(s)["content"].update(support="Built at Visit Health for five years."), ["GENERATED_MODE_BRAND"]),
        M("leak:brand-product-name", G_CHAP, lambda s: cshero(s)["content"].update(title="Digital Clinic, redesigned for crews"), ["GENERATED_MODE_BRAND"]),
        M("leak:logo", G_HOME, lambda s: node(s, "shell.header")["content"].update(brandMark={"role": "brand.wordmark-logo", "src": "assets/logo-ayushi-maurya-transparent.png", "mediaType": "image"}), ["GENERATED_MODE_LOGO"]),
        M("leak:person-owner-name", G_HOME, lambda s: node(s, "shell.footer")["content"].update(name="Ayushi Maurya"), ["GENERATED_MODE_PERSON"]),
        M("leak:person-in-copy", G_CHAP, lambda s: node(s, "casestudy.chapter")["content"]["paragraphs"].append("Dr. Rajesh Neti reviewed the flow."), ["GENERATED_MODE_PERSON"]),
        M("leak:contact-phone", G_RES, lambda s: node(s, "resume.header")["content"]["contacts"].append({"term": "Phone", "value": "9876543210"}), ["GENERATED_MODE_PERSON"]),
        M("leak:source-profile-url", G_HOME, lambda s: node(s, "shell.footer")["content"]["links"].append({"label": "Profile", "href": "https://www.linkedin.com/in/someone", "role": "link.placeholder-url"}), ["GENERATED_MODE_URL"]),
        M("leak:source-domain-in-text", G_CHAP, lambda s: cshero(s)["content"].update(dek="Read the long version at ayushimaurya.vercel.app before the call."), ["GENERATED_MODE_URL"]),
        M("leak:source-url-role", G_BRIEF, lambda s: node(s, "conversion.closing")["content"]["ctas"].append({"label": "Live", "href": "https://getvisitapp.com/", "role": "link.source-url"}), ["GENERATED_MODE_URL"]),
        M("leak:store-url", G_HOME, lambda s: node(s, "home.featured-project")["content"].update(cta={"label": "Get the app", "href": "https://apps.apple.com/app/id000", "role": "link.placeholder-url"}), ["GENERATED_MODE_URL"]),
        M("leak:non-reserved-placeholder", G_IDX, lambda s: node(s, "index.page-header")["content"].update(contactLink={"label": "Write", "href": "https://rowan-vale.com/", "role": "link.placeholder-url"}), ["GENERATED_MODE_URL"]),
        M("leak:source-copy-verbatim", G_HOME, lambda s: hero(s)["content"].update(statement="I design products for people who don't have time to figure things out."), ["GENERATED_MODE_COPY"]),
        M("leak:source-copy-run", G_CHAP, lambda s: node(s, "casestudy.chapter")["content"]["paragraphs"].append("Honestly, most health apps sell full body checkup packages these days."), ["GENERATED_MODE_COPY"]),
        M("leak:source-cta", G_BRIEF, lambda s: node(s, "conversion.closing")["content"]["ctas"].__setitem__(0, {"label": "Talk about this project", "href": "contact.html", "role": "link.internal-route"}), ["GENERATED_MODE_CTA"]),
        M("leak:proprietary-screen", G_CHAP, lambda s: node(s, "casestudy.chapter")["content"]["figures"].__setitem__(0, {"role": "product.case-study-screen", "src": "assets/case-studies/hybrid/h03.webp", "mediaType": "image"}), ["GENERATED_MODE_ASSET"]),
        M("leak:proprietary-src-under-safe-role", G_CHAP, lambda s: node(s, "casestudy.chapter")["content"]["figures"].__setitem__(0, {"role": "product.generated-visual", "src": "assets/screens/v3/booking.webp", "mediaType": "image"}), ["GENERATED_MODE_ASSET"]),
        M("leak:personal-photo", G_HOME, lambda s: node(s, "about.intro")["content"]["photos"][0].update(image={"role": "person.portrait-photo", "src": "assets/little-world/booth-1.jpg", "mediaType": "image"}), ["GENERATED_MODE_ASSET"]),
        M("leak:case-study-video", G_BRIEF, lambda s: cshero(s)["content"].update(media={"role": "product.case-study-video", "src": "generated://video/x", "mediaType": "video"}), ["GENERATED_MODE_ASSET"]),
        M("leak:meta-title-brand", G_IDX, lambda s: s["meta"].update(title="Projects like Maths Jenga"), ["GENERATED_MODE_BRAND"]),
    ]
    # ---- R3 availability pins (registry edit alone cannot loosen)
    cases += [
        M("pin:registry-loosened-logo", G_HOME, lambda s: None, ["ASSET_AVAILABILITY_PIN"],
          reg_fn=lambda r: r.roles["brand.wordmark-logo"].update(availability="generation-safe")),
        M("pin:registry-loosened-screens", G_HOME, lambda s: None, ["ASSET_AVAILABILITY_PIN"],
          reg_fn=lambda r: r.roles["product.case-study-screen"].update(availability="reference-only")),
        M("pin:unpinned-role-added", G_HOME, lambda s: None, ["ASSET_AVAILABILITY_PIN"],
          reg_fn=lambda r: r.roles.__setitem__("brand.any-logo", {"availability": "generation-safe"})),
    ]
    # ---- R8 retrieval eligibility
    cases += [
        M("r8:node-flip-overlay-eligible", G_HOME, lambda s: s["overlays"][0].update(retrievalEligible=True), ["RETRIEVAL_ELIGIBILITY"]),
        M("r8:node-overlay-default-eligible", G_HOME, lambda s: s["overlays"][0].pop("retrievalEligible"), ["RETRIEVAL_ELIGIBILITY"]),
        M("r8:content-marked-ineligible", G_HOME, lambda s: hero(s).update(retrievalEligible=False), ["RETRIEVAL_ELIGIBILITY"]),
        M("r8:contract-flip", G_HOME, lambda s: None, ["RETRIEVAL_PIN_MISMATCH"], reg_fn=lambda r: r.sections["utility.lock-modal"].update(retrievalEligible=True)),
        M("r8:allowlist-flip", G_HOME, lambda s: None, ["RETRIEVAL_PIN_MISMATCH"],
          reg_fn=lambda r: [e.update(retrievalEligible=True) for e in r.allowlist["sections"] if e["id"] == "utility.dreams-overlay"]),
        M("r8:contract-content-made-ineligible", G_HOME, lambda s: None, ["RETRIEVAL_PIN_MISMATCH"], reg_fn=lambda r: r.sections["home.hero"].update(retrievalEligible=False)),
        M("r8:runtime-ui-unpinned", G_HOME, lambda s: None, ["RETRIEVAL_PIN_MISSING"],
          reg_fn=lambda r: r.sections.__setitem__("utility.cookie-banner", dict(copy.deepcopy(r.sections["utility.lock-modal"]), id="utility.cookie-banner", title="Cookie banner", retrievalEligible=True))),
    ]
    # ---- R10 token policy
    def style(sec, **kw):
        return lambda s: node(s, sec).setdefault("style", {}).update(kw)
    cases += [
        M("token:unknown", G_CHAP, style("casestudy.chapter", surface="color.surface.mystery"), ["TOKEN_UNKNOWN"]),
        M("token:raw-hex", G_CHAP, style("casestudy.chapter", accent="#6a4bd6"), ["TOKEN_RAW_COLOR"]),
        M("token:raw-rgb", G_BRIEF, style("casestudy.chapter", surface="rgb(20, 17, 24)"), ["TOKEN_RAW_COLOR"]),
        M("token:arbitrary-spacing", G_IDX, style("index.project-grid", gap="37px"), ["TOKEN_ARBITRARY_SPACING"]),
        M("token:arbitrary-radius", G_IDX, style("index.project-grid", radius="1.3rem"), ["TOKEN_ARBITRARY_SPACING"]),
        M("token:unsupported-font-literal", G_HOME, style("home.hero", headingFont="Comic Sans MS"), ["TOKEN_UNSUPPORTED_FONT"]),
        M("token:unsupported-font-token", G_HOME, style("home.hero", headingFont="font.family.serif"), ["TOKEN_UNSUPPORTED_FONT"]),
        M("token:theme-mismatch", G_IDX, style("index.project-grid", surface="palette.night.surface-page"), ["TOKEN_THEME_MISMATCH"]),
        M("token:wrong-role", G_IDX, style("index.project-grid", radius="color.accent.primary"), ["TOKEN_WRONG_ROLE"]),
        M("token:unknown-motion-duration", G_HOME, lambda s: hero(s)["motion"].update(durationToken="motion.duration.glacial"), ["TOKEN_UNKNOWN"]),
    ]
    # ---- templates / structure
    def drop(sec):
        return lambda s: s["nodes"].remove(node(s, sec))
    cases += [
        M("tmpl:template-node-mismatch", G_BRIEF, lambda s: s.update(template="template.case-study-chaptered"), ["TEMPLATE_SEQUENCE"]),
        M("tmpl:missing-required-closing", G_BRIEF, drop("conversion.closing"), ["TEMPLATE_SEQUENCE"]),
        M("tmpl:duplicate-hero", G_BRIEF, lambda s: s["nodes"].insert(2, copy.deepcopy(cshero(s))), ["TEMPLATE_SEQUENCE", "ONE_HERO"]),
        M("tmpl:hero-variant-not-in-slot", G_BRIEF, lambda s: cshero(s).update(variant="journey"), ["TEMPLATE_SEQUENCE"]),
        M("tmpl:reordered", G_BRIEF, lambda s: s["nodes"].__setitem__(slice(2, 4), [s["nodes"][3], s["nodes"][2]]), ["TEMPLATE_SEQUENCE"]),
        M("tmpl:utility-in-flow", G_HOME, lambda s: s["nodes"].insert(1, s["overlays"][0]), ["TEMPLATE_SEQUENCE", "OVERLAY_PLACEMENT"]),
        M("tmpl:overlay-not-in-template", G_NDA, lambda s: s.setdefault("overlays", []).append(
            {"section": "utility.dreams-overlay", "variant": "constellation", "retrievalEligible": False, "content": {"kicker": "Wishes", "title": "Small wishes"},
             "motion": {"pattern": "modal-pop", "reducedMotionFallback": "instant-state-change"}}), ["OVERLAY_PLACEMENT"]),
        M("tmpl:reference-route-wrong-template", R_BRIEF, lambda s: s.update(route="index.html"), ["TEMPLATE_ROUTE"]),
        M("tmpl:consecutive-scroll-narratives", G_CHAP, lambda s: s["nodes"].insert(s["nodes"].index(node(s, "casestudy.scroll-narrative")) + 1,
                                                                               copy.deepcopy(node(s, "casestudy.scroll-narrative"))), ["NO_CONSECUTIVE_SCROLL_NARRATIVES"]),
        M("tmpl:chaptered-too-short", G_CHAP, lambda s: s.update(nodes=[n for n in s["nodes"] if n["section"] not in ("casestudy.chapter", "casestudy.problem-statement")]), ["TEMPLATE_SEQUENCE"]),
        M("tmpl:brief-too-long", G_BRIEF, lambda s: [s["nodes"].insert(2, copy.deepcopy(node(s, "casestudy.chapter"))) for _ in range(2)], ["TEMPLATE_SEQUENCE"]),
        M("tmpl:adjacent-same-tone", G_CHAP, lambda s: s["nodes"].insert(s["nodes"].index(node(s, "casestudy.chapter", 1)) + 1, copy.deepcopy(node(s, "casestudy.chapter", 1))),
          ["ADJACENT_SAME_TONE"], severity="warn"),
        M("tmpl:unknown-template", G_BRIEF, lambda s: s.update(template="template.landing"), ["SCHEMA"]),
        M("graph:rule-without-implementation", G_HOME, lambda s: None, ["GRAPH_RULE_UNIMPLEMENTED"],
          reg_fn=lambda r: r.graph["rules"].append({"id": "NO_TWO_CTAS", "severity": "error"})),
    ]
    # ---- content budgets / schema layer
    cases += [
        M("content:maxwords-overflow", G_HOME, lambda s: hero(s)["content"].update(statement=" ".join(["calm"] * 40)), ["CONTENT_MAXWORDS"]),
        M("content:maxwords-item-overflow", G_CHAP, lambda s: node(s, "casestudy.problem-statement")["content"]["constraints"][0].update(text=" ".join(["detail"] * 30)), ["CONTENT_MAXWORDS"]),
        M("content:maxitems-overflow", G_CHAP, lambda s: node(s, "casestudy.chapter-nav")["content"].update(links=[{"label": f"Part {i}", "href": f"#p{i}", "role": "link.internal-route"} for i in range(7)]), ["SCHEMA", "CONTENT_MAXITEMS"]),
        M("content:meta-title-overflow", G_RES, lambda s: s["meta"].update(title=" ".join(["word"] * 12)), ["CONTENT_MAXWORDS"]),
        M("content:missing-required-field", G_BRIEF, lambda s: cshero(s)["content"].pop("title"), ["SCHEMA"]),
        M("content:invented-field", G_BRIEF, lambda s: cshero(s)["content"].update(subtitleExtra="x"), ["SCHEMA"]),
        M("content:variant-required-missing", G_CHAP, lambda s: node(s, "casestudy.decision")["content"].pop("steps"), ["CONTENT_REQUIRED"]),
        M("schema:mode-missing", G_HOME, lambda s: s.pop("mode"), ["SCHEMA"]),
        M("schema:mode-invalid", G_HOME, lambda s: s.update(mode="draft"), ["SCHEMA"]),
        M("schema:unknown-asset-role", G_HOME, lambda s: node(s, "home.featured-project")["content"]["media"].update(role="asset.random"), ["SCHEMA"]),
        M("schema:unknown-section-type", G_HOME, lambda s: hero(s).update(section="home.hero-alias"), ["SCHEMA"]),
        M("ref:link-role-mismatch", R_BRIEF, lambda s: node(s, "conversion.closing")["content"]["ctas"][0].update(href="https://example.org/x"), ["LINK_ROLE_MISMATCH"]),
        M("ref:asset-path-role-mismatch", R_BRIEF, lambda s: cshero(s)["content"]["media"].update(role="person.portrait-photo"), ["ASSET_PATH_ROLE_MISMATCH", "ASSET_ROLE_NOT_ALLOWED"]),
    ]
    # ---- motion
    cases += [
        M("motion:missing-reducedMotionFallback", G_HOME, lambda s: hero(s)["motion"].pop("reducedMotionFallback"), ["SCHEMA"]),
        M("motion:wrong-fallback", G_CHAP, lambda s: node(s, "casestudy.chapter")["motion"].update(reducedMotionFallback="pause-media"), ["REDUCED_MOTION_FALLBACK"]),
        M("motion:pattern-not-allowed", G_HOME, lambda s: hero(s)["motion"].update(pattern="scroll-stepper", reducedMotionFallback="show-all-steps"), ["SCHEMA", "MOTION_PATTERN"]),
        M("motion:invented-field", G_HOME, lambda s: hero(s)["motion"].update(inventedAnimation="spin"), ["SCHEMA"]),
    ]
    # ---- R9 wrapper gate (run against a scratch copy of the measured data)
    def gate(name, mutate, expect_tokens, severity="error"):
        return {"name": name, "kind": "gate", "gate_fn": mutate, "expect": set(expect_tokens), "severity": severity}

    def heights(mv):
        return mv["sectionHeights"]["routes"]

    def set_block(route, section, h):
        def fn(mv, wl):
            for b in heights(mv)[route]["blocks"]:
                if b["section"] == section:
                    b["heightPx"] = h
                    return
        return fn

    cases += [
        gate("r9:hero-1900-warns", set_block("hybrid-diagnostic.html", "casestudy.hero", 1900), ["HERO_TALL"], severity="warn"),
        gate("r9:hero-3100-fails", set_block("hybrid-diagnostic.html", "casestudy.hero", 3100), ["HERO_FAIL"]),
        gate("r9:majority-share-fails", set_block("claim-approval.html", "casestudy.chapter", 2100), ["SHARE_FAIL"]),
        gate("r9:missing-measurement", lambda mv, wl: heights(mv).pop("wallet-ui.html"), ["MISSING_MEASUREMENT"]),
        gate("r9:missing-block-height", lambda mv, wl: heights(mv)["nda.html"]["blocks"][1].pop("heightPx"), ["MISSING_MEASUREMENT"]),
        gate("r9:wrong-viewport", lambda mv, wl: mv["sectionHeights"]["viewport"].update(width=1280), ["WRONG_VIEWPORT"]),
        gate("r9:whitelist-missing-justification", lambda mv, wl: wl["entries"][0].update(justification=""), ["WHITELIST_INVALID"]),
        gate("r9:whitelist-agent-not-labelled", lambda mv, wl: wl["entries"][0].update(reviewedBy="automated agent"), ["WHITELIST_INVALID"]),
        gate("r9:whitelist-over-cap", set_block("projects.html", "index.project-grid", 3500), ["WHITELIST_OVER_CAP"]),
        gate("r9:whitelist-removed", lambda mv, wl: wl.update(entries=[]), ["SHARE_FAIL"]),
    ]
    return cases


def run_gate_case(case):
    import wrapper_gate
    tmp = tempfile.mkdtemp(prefix="adv-gate-")
    try:
        for rel in ("extraction/measured-values.json", "extraction/wrapper-whitelist.json", "templates/routes.json"):
            os.makedirs(os.path.join(tmp, os.path.dirname(rel)), exist_ok=True)
            shutil.copy(os.path.join(REPO, rel), os.path.join(tmp, rel))
        shutil.copytree(os.path.join(REPO, "sections"), os.path.join(tmp, "sections"))
        mvp, wlp = os.path.join(tmp, "extraction/measured-values.json"), os.path.join(tmp, "extraction/wrapper-whitelist.json")
        mv, wl = json.load(open(mvp)), json.load(open(wlp))
        case["gate_fn"](mv, wl)
        json.dump(mv, open(mvp, "w"))
        json.dump(wl, open(wlp, "w"))
        errors, warnings = wrapper_gate.run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    pool = errors if case["severity"] == "error" else warnings
    hit = any(any(e.startswith(tok) or tok + ":" in e or f"({tok})" in e for tok in case["expect"]) for e in pool)
    if case["severity"] == "warn":
        ok = hit and not errors
    else:
        ok = hit
    return ok, (errors + warnings)[:2]


def main():
    reg = sv.Registry()
    cases = build_cases()
    failures = 0
    counts = {"control": 0, "mutation": 0, "gate": 0}
    for c in cases:
        counts[c["kind"]] += 1
        if c["kind"] == "gate":
            ok, detail = run_gate_case(c)
            print(f"{'PASS' if ok else 'FAIL'}  {c['name']:44} {'flagged' if ok else 'NOT flagged'}: {detail[0][:110] if detail else ''}")
            failures += not ok
            continue
        if c["kind"] == "control":
            spec = synthesize(c["synth"], reg) if c.get("synth") else ex(c["base"])
            rep = sv.validate(spec, reg)
            ok = not rep.errors
            print(f"{'PASS' if ok else 'FAIL'}  {c['name']:44} control: {len(rep.errors)} errors, {len(rep.warnings)} warnings"
                  + ("" if ok else f" {[(i['rule'], i['path']) for i in rep.errors[:3]]}"))
            failures += not ok
            continue
        spec = copy.deepcopy(ex(c["base"]))
        r = reg.clone() if c["reg_fn"] else reg
        if c["reg_fn"]:
            c["reg_fn"](r)
        c["fn"](spec)
        rep = sv.validate(spec, r)
        pool = rep.errors if c["severity"] == "error" else rep.warnings
        got = {i["rule"] for i in pool}
        ok = bool(got & c["expect"]) and (c["severity"] == "error" or not rep.errors)
        print(f"{'PASS' if ok else 'FAIL'}  {c['name']:44} {'rejected' if c['severity'] == 'error' else 'warned'} by {sorted(got & c['expect']) or sorted(got)[:3]}")
        failures += not ok
    total = len(cases)
    print(f"\nadversarial: {total} cases ({counts['mutation']} mutations, {counts['gate']} wrapper-gate mutations, {counts['control']} controls), {failures} unexpected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
