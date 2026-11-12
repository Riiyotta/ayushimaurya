#!/usr/bin/env python3
"""Semantic validator for PageSpecs (everything JSON Schema cannot express).

    python3 schema/semantic_validate.py schema/examples/*.json      # exit 1 on any error

Layers, in order:
  SCHEMA            Draft-07 structural validation against schema/pagespec.schema.json
  TEMPLATE_*        template exists; the node sequence matches the template's slot pattern
                    (required / repeatable / min-max counts / allowed variants per slot);
                    a reference PageSpec's route is assigned to that template in templates/routes.json
  CONTENT_*         per-field word budgets (maxWords) and item budgets (maxItems) from the section
                    contracts, variant-specific required fields, page meta budgets
  ASSET_* / LINK_*  closed asset roles allowed per section; registry availability must equal the
                    PINNED_AVAILABILITY table below; reference asset paths must match their role
  TOKEN_*           style/motion token references: unknown token, raw colour, arbitrary length,
                    unsupported font, wrong role, theme-bound palette used under the other theme
  RETRIEVAL_*       retrievalEligible on nodes / contracts / allowlist must agree with the
                    RETRIEVAL_INELIGIBLE pin (runtime UI is never retrievable; content always is)
  graph rules       compatibility/graph.json rule ids, each implemented below, severity from the graph
  MOTION_*          pattern allowed for the section; reducedMotionFallback pinned per pattern
  GENERATED_MODE_*  mode=generated only: BRAND, PERSON, URL, COPY, CTA, ASSET, LOGO (patterns and
                    copy fingerprints come from policy/source-brand.json, harvested from the source)

Standard library + jsonschema (Draft7Validator). Paths derive from this file's location.
"""
import copy
import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCHEMA_DIR)

# ---------------------------------------------------------------- pins (independent of the registries)
PINNED_AVAILABILITY = {
    "brand.wordmark-logo": "blocked-for-generation",
    "person.portrait-photo": "blocked-for-generation",
    "person.lifestyle-photo": "blocked-for-generation",
    "decor.hero-reveal-image": "blocked-for-generation",
    "product.case-study-screen": "blocked-for-generation",
    "product.case-study-video": "blocked-for-generation",
    "product.thumbnail": "blocked-for-generation",
    "media.side-project-demo": "blocked-for-generation",
    "decor.cloud-illustration": "reference-only",
    "icon.glyph": "generation-safe",
    "brand.placeholder-wordmark": "generation-safe",
    "brand.user-supplied-mark": "generation-safe",
    "person.fictional-avatar": "generation-safe",
    "product.generated-visual": "generation-safe",
    "illustration.generated-decor": "generation-safe",
    "link.source-url": "reference-only",
    "link.internal-route": "generation-safe",
    "link.placeholder-url": "generation-safe",
    "copy.original": "generation-safe",
}
# runtime / utility UI: never retrievable. A contract whose id or title looks like runtime UI must be here.
RETRIEVAL_INELIGIBLE = {
    "utility.mobile-menu", "utility.lock-modal", "utility.desktop-hint",
    "utility.media-lightbox", "utility.dreams-overlay", "utility.reading-progress",
}
RUNTIME_UI_PATTERN = re.compile(r"modal|dialog|overlay|lightbox|menu|banner|toast|hint|progress|cookie|consent|drawer|preloader|cursor|popup", re.I)
MOTION_FALLBACK = {
    "none": "none", "rise-in-on-load": "static-visible", "reveal-on-scroll": "static-visible",
    "scroll-console": "show-all-steps", "scroll-pinned-panels": "show-all-steps", "scroll-stepper": "show-all-steps",
    "ambient-drift": "static-visible", "interactive-canvas-field": "static-first-frame", "box-open": "static-visible",
    "card-flip": "instant-state-change", "modal-pop": "instant-state-change", "autoplay-loop-video": "pause-media",
    "sticky-chapter-nav": "instant-state-change", "theme-crossfade": "instant-state-change",
}
PINNED_SCROLL_PATTERNS = {"scroll-console", "scroll-pinned-panels", "scroll-stepper"}
GRAPH_RULES_IMPLEMENTED = {
    "ONE_HERO", "HERO_FOLLOWS_HEADER", "SHELL_POSITION", "CLOSING_PRECEDES_FOOTER", "MAX_PER_PAGE",
    "NO_CONSECUTIVE_SCROLL_NARRATIVES", "ADJACENT_SAME_TONE", "MOTION_BUDGET", "OVERLAY_PLACEMENT", "REDUCED_MOTION_FALLBACK",
}
RESERVED_HOST = re.compile(r"^([a-z0-9-]+\.)*(example|invalid)$|^([a-z0-9-]+\.)*example\.(com|org|net)$", re.I)
PLACEHOLDER_SRC = re.compile(r"^(placeholder|generated|user-supplied)://[A-Za-z0-9._/-]+$")
URL_TOKEN = re.compile(r"(https?://[^\s\"'<>)]+|mailto:[^\s\"'<>)]+|www\.[^\s\"'<>)]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|app|io|net|org|site|in|co|dev|me)\b(?:/[^\s\"'<>)]*)?)", re.I)
RAW_COLOR = re.compile(r"^\s*(#[0-9a-f]{3,8}|rgba?\(|hsla?\(|color\(|oklch\(|transparent$|black$|white$)", re.I)
RAW_LENGTH = re.compile(r"^\s*-?\d+(\.\d+)?\s*(px|rem|em|%|vh|vw|pt|ch)?\s*$|^\s*(clamp|calc|min|max)\(", re.I)
GENERATED_RULES = ["GENERATED_MODE_BRAND", "GENERATED_MODE_PERSON", "GENERATED_MODE_URL", "GENERATED_MODE_COPY",
                   "GENERATED_MODE_CTA", "GENERATED_MODE_ASSET", "GENERATED_MODE_LOGO"]


def words(text):
    """Same counting rule as extraction/source_dom.py words()."""
    return len([w for w in re.split(r"\s+", (text or "").strip()) if re.search(r"[A-Za-z0-9₹%→←↗]", w)])


def normalize(text):
    return " ".join(re.sub(r"[^a-z0-9₹%]+", " ", (text or "").lower().replace("’", "'").replace("'", "")).split())


def fp(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


def load_templates():
    return _load("templates/templates.json")["templates"]


class Registry:
    """Everything the validator reads from disk; tests mutate a deep copy in memory."""

    def __init__(self, root=REPO):
        def ld(rel):
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                return json.load(f)
        self.root = root
        self.schema = ld("schema/pagespec.schema.json")
        tj = ld("templates/templates.json")
        self.templates, self.meta_budgets = tj["templates"], tj["metaBudgets"]
        self.routes = {r["route"]: r["template"] for r in ld("templates/routes.json")["routes"]}
        self.sections = {}
        for fn in sorted(os.listdir(os.path.join(root, "sections"))):
            if fn.endswith(".json"):
                c = ld("sections/" + fn)
                self.sections[c["id"]] = c
        self.graph = ld("compatibility/graph.json")
        self.roles = ld("assets/asset-roles.json")["roles"]
        self.catalog = {t["id"]: t for t in ld("tokens/llm/token-catalog.json")["tokens"]}
        self.policy = ld("tokens/llm/token-policy.json")
        self.allowlist = ld("tokens/llm/component-allowlist.json")
        self.brand = ld("policy/source-brand.json")["sourceBrand"]
        self._compiled = None

    def clone(self):
        c = copy.copy(self)
        for k in ("templates", "routes", "sections", "graph", "roles", "catalog", "policy", "allowlist", "brand", "schema"):
            setattr(c, k, copy.deepcopy(getattr(self, k)))
        c._compiled = None
        return c

    def compiled(self):
        if self._compiled is None:
            p = self.brand["patterns"]
            self._compiled = {k: [re.compile(x, re.I) for x in v] for k, v in p.items()}
            self._compiled["copyFull"] = set(self.brand["copyFingerprints"]["fullSegments"])
            self._compiled["copyShingles"] = set(self.brand["copyFingerprints"]["shingles"])
            self._compiled["shingleSize"] = self.brand["copyFingerprints"]["shingleSize"]
            self._compiled["cta"] = set(self.brand["ctaFingerprints"]["labels"])
        return self._compiled


# ---------------------------------------------------------------- template matching (shared with the classifier)
def match_template(nodes, template):
    """Return [] when the node sequence fits the template's slot pattern, else error strings."""
    toks = [n["section"] for n in nodes]
    parts = []
    for i, slot in enumerate(template["nodes"]):
        alt = "|".join(re.escape(s) + ";" for s in slot["sections"])
        if slot.get("repeatable"):
            lo = slot.get("minCount", 1 if slot["required"] else 0)
            hi = slot.get("maxCount", "")
            if not slot["required"]:
                lo = 0
            q = "{%d,%s}" % (lo, hi)
        else:
            q = "" if slot["required"] else "?"
        parts.append("(?P<s%d>(?:%s)%s)" % (i, alt, q))
    seq = "".join(t + ";" for t in toks)
    m = re.fullmatch("".join(parts), seq)
    if not m:
        expect = " ".join(("[" + "|".join(s["sections"]) + "]") + ("" if s["required"] and not s.get("repeatable") else ("*" if s.get("repeatable") else "?"))
                          for s in template["nodes"])
        return ["node sequence %s does not match %s: %s" % (toks, template["id"], expect)]
    errs = []
    pos = 0
    for i, slot in enumerate(template["nodes"]):
        span = m.group("s%d" % i) or ""
        count = span.count(";")
        for n in nodes[pos:pos + count]:
            allowed = (slot.get("variants") or {}).get(n["section"])
            if allowed and n.get("variant") not in allowed:
                errs.append("slot %s: variant %r of %s not allowed in %s (allowed %s)" % (slot["slot"], n.get("variant"), n["section"], template["id"], allowed))
        pos += count
    return errs


# ---------------------------------------------------------------- helpers
class Report:
    def __init__(self):
        self.items = []

    def add(self, rule, path, msg, severity="error"):
        self.items.append({"rule": rule, "severity": severity, "path": path, "message": msg})

    @property
    def errors(self):
        return [i for i in self.items if i["severity"] == "error"]

    @property
    def warnings(self):
        return [i for i in self.items if i["severity"] == "warn"]


def iter_strings(obj, path):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{i}]")


def iter_typed(value, fspec, path):
    """Yield (kind, path, obj) for links and assets inside a content value, following the contract."""
    t = fspec["type"]
    if t == "link" and isinstance(value, dict):
        yield "link", path, value
    elif t == "links" and isinstance(value, list):
        for i, v in enumerate(value):
            yield "link", f"{path}[{i}]", v
    elif t == "asset" and isinstance(value, dict):
        yield "asset", path, value
    elif t == "assets" and isinstance(value, list):
        for i, v in enumerate(value):
            yield "asset", f"{path}[{i}]", v
    elif t in ("list", "meta") and isinstance(value, list):
        for i, v in enumerate(value):
            if isinstance(v, dict):
                for k, sub in fspec.get("item", {}).items():
                    if k in v:
                        yield from iter_typed(v[k], sub, f"{path}[{i}].{k}")
    elif t == "object" and isinstance(value, dict):
        for k, sub in fspec.get("item", {}).items():
            if k in value:
                yield from iter_typed(value[k], sub, f"{path}.{k}")


def check_budget(value, fspec, path, rep):
    t = fspec["type"]
    mw, mi = fspec.get("maxWords"), fspec.get("maxItems")
    if t == "text" and isinstance(value, str) and mw is not None and words(value) > mw:
        rep.add("CONTENT_MAXWORDS", path, f"{words(value)} words > budget {mw}")
    elif t == "textList" and isinstance(value, list):
        if mi is not None and len(value) > mi:
            rep.add("CONTENT_MAXITEMS", path, f"{len(value)} items > budget {mi}")
        for i, v in enumerate(value):
            if isinstance(v, str) and mw is not None and words(v) > mw:
                rep.add("CONTENT_MAXWORDS", f"{path}[{i}]", f"{words(v)} words > budget {mw}")
    elif t in ("link", "links"):
        vals = value if isinstance(value, list) else [value]
        if t == "links" and mi is not None and len(vals) > mi:
            rep.add("CONTENT_MAXITEMS", path, f"{len(vals)} items > budget {mi}")
        for i, v in enumerate(vals):
            if isinstance(v, dict) and mw is not None and words(v.get("label", "")) > mw:
                rep.add("CONTENT_MAXWORDS", f"{path}.label", f"{words(v.get('label'))} words > budget {mw}")
    elif t in ("asset", "assets"):
        vals = value if isinstance(value, list) else [value]
        if t == "assets" and mi is not None and len(vals) > mi:
            rep.add("CONTENT_MAXITEMS", path, f"{len(vals)} items > budget {mi}")
        for v in vals:
            if isinstance(v, dict) and v.get("alt") and mw is not None and words(v["alt"]) > mw:
                rep.add("CONTENT_MAXWORDS", f"{path}.alt", f"{words(v['alt'])} words > budget {mw}")
    elif t in ("list", "meta") and isinstance(value, list):
        if mi is not None and len(value) > mi:
            rep.add("CONTENT_MAXITEMS", path, f"{len(value)} items > budget {mi}")
        for i, v in enumerate(value):
            if isinstance(v, dict):
                for k, sub in fspec.get("item", {}).items():
                    if k in v:
                        check_budget(v[k], sub, f"{path}[{i}].{k}", rep)
    elif t == "object" and isinstance(value, dict):
        for k, sub in fspec.get("item", {}).items():
            if k in value:
                check_budget(value[k], sub, f"{path}.{k}", rep)


def host_of(url):
    u = re.sub(r"^(https?://|mailto:[^@]*@|www\.)", "", url, flags=re.I)
    return u.split("/")[0].split("?")[0].split(":")[0].lower().rstrip(".,;")


# ---------------------------------------------------------------- main validation
def validate(spec, reg=None, schema_check=True):
    reg = reg or Registry()
    rep = Report()
    if schema_check:
        try:
            from jsonschema import Draft7Validator
        except ImportError:
            rep.add("SCHEMA", "$", "jsonschema is not installed (pip install jsonschema)")
            return rep
        for e in sorted(Draft7Validator(reg.schema).iter_errors(spec), key=lambda e: list(e.path)):
            rep.add("SCHEMA", "$." + ".".join(str(p) for p in e.path), e.message[:300])
        if rep.errors:
            return rep
    mode = spec.get("mode")
    generated = mode == "generated"
    tid = spec.get("template")
    tmpl = reg.templates.get(tid)
    if tmpl is None:
        rep.add("TEMPLATE_UNKNOWN", "$.template", f"unknown template {tid}")
        return rep
    nodes = spec.get("nodes", [])
    overlays = spec.get("overlays", [])
    sev = {r["id"]: r["severity"] for r in reg.graph["rules"]}
    for rid in sev:
        if rid not in GRAPH_RULES_IMPLEMENTED:
            rep.add("GRAPH_RULE_UNIMPLEMENTED", "compatibility/graph.json", f"graph rule {rid} has no implementation in the validator")

    # route <-> template (reference mode reconstructs a real route)
    if mode == "reference":
        assigned = reg.routes.get(spec.get("route"))
        if assigned != tid:
            rep.add("TEMPLATE_ROUTE", "$.route", f"route {spec.get('route')} is assigned to {assigned}, not {tid}")

    # registry / pin agreement (editing the registry alone cannot loosen anything)
    for rid, pinned in PINNED_AVAILABILITY.items():
        got = reg.roles.get(rid, {}).get("availability")
        if got != pinned:
            rep.add("ASSET_AVAILABILITY_PIN", f"assets/asset-roles.json#{rid}", f"registry says {got!r}, pinned {pinned!r}")
    for rid in reg.roles:
        if rid not in PINNED_AVAILABILITY:
            rep.add("ASSET_AVAILABILITY_PIN", f"assets/asset-roles.json#{rid}", "role is not pinned in PINNED_AVAILABILITY")
    allow_sections = {s["id"]: s for s in reg.allowlist.get("sections", [])}
    for sid, c in reg.sections.items():
        want = sid not in RETRIEVAL_INELIGIBLE
        if c.get("retrievalEligible") is not want:
            rep.add("RETRIEVAL_PIN_MISMATCH", f"sections/{sid}.json", f"contract retrievalEligible={c.get('retrievalEligible')} but pin says {want}")
        a = allow_sections.get(sid)
        if a is not None and a.get("retrievalEligible") is not want:
            rep.add("RETRIEVAL_PIN_MISMATCH", f"tokens/llm/component-allowlist.json#{sid}", f"allowlist retrievalEligible={a.get('retrievalEligible')} but pin says {want}")
        if (RUNTIME_UI_PATTERN.search(sid) or RUNTIME_UI_PATTERN.search(c.get("title", ""))) and sid not in RETRIEVAL_INELIGIBLE:
            rep.add("RETRIEVAL_PIN_MISSING", f"sections/{sid}.json", "looks like runtime UI but is not in RETRIEVAL_INELIGIBLE")

    # template sequence
    for msg in match_template(nodes, tmpl):
        rep.add("TEMPLATE_SEQUENCE", "$.nodes", msg)

    # meta budgets
    meta = spec.get("meta", {})
    for k in ("title", "description"):
        if k in meta and words(meta[k]) > reg.meta_budgets[k]["maxWords"]:
            rep.add("CONTENT_MAXWORDS", f"$.meta.{k}", f"{words(meta[k])} words > budget {reg.meta_budgets[k]['maxWords']}")

    theme = spec.get("theme")
    all_nodes = [("nodes", i, n) for i, n in enumerate(nodes)] + [("overlays", i, n) for i, n in enumerate(overlays)]
    for where, i, n in all_nodes:
        p = f"$.{where}[{i}]"
        sid = n.get("section")
        c = reg.sections.get(sid)
        if c is None:
            rep.add("SECTION_UNKNOWN", p, f"unknown section {sid}")
            continue
        if n.get("variant") not in c["variants"]:
            rep.add("VARIANT_UNKNOWN", p + ".variant", f"{n.get('variant')!r} not in {c['variants']}")
        content = n.get("content", {})
        fields = c["content"]["fields"]
        for k, f in fields.items():
            if f.get("required") and k not in content:
                rep.add("CONTENT_REQUIRED", f"{p}.content.{k}", "required field missing")
            if n.get("variant") in f.get("requiredForVariants", []) and k not in content:
                rep.add("CONTENT_REQUIRED", f"{p}.content.{k}", f"required for variant {n.get('variant')}")
            if k in content:
                check_budget(content[k], f, f"{p}.content.{k}", rep)
        for k in content:
            if k not in fields:
                rep.add("CONTENT_UNKNOWN_FIELD", f"{p}.content.{k}", "field not in the section contract")

        # retrieval eligibility at node level
        elig = n.get("retrievalEligible", True)
        if sid in RETRIEVAL_INELIGIBLE and elig:
            rep.add("RETRIEVAL_ELIGIBILITY", p, f"{sid} is runtime UI and must carry retrievalEligible:false")
        if sid not in RETRIEVAL_INELIGIBLE and not elig:
            rep.add("RETRIEVAL_ELIGIBILITY", p, f"{sid} is content and must be retrievable")

        # motion
        mo = n.get("motion", {})
        pat = mo.get("pattern")
        if pat not in c["motion"]["allowedPatterns"]:
            rep.add("MOTION_PATTERN", p + ".motion.pattern", f"{pat} not allowed for {sid} ({c['motion']['allowedPatterns']})")
        if "REDUCED_MOTION_FALLBACK" in sev and mo.get("reducedMotionFallback") != MOTION_FALLBACK.get(pat):
            rep.add("REDUCED_MOTION_FALLBACK", p + ".motion.reducedMotionFallback",
                    f"{pat} requires reducedMotionFallback={MOTION_FALLBACK.get(pat)!r}, got {mo.get('reducedMotionFallback')!r}", sev["REDUCED_MOTION_FALLBACK"])
        for key, cat in (("durationToken", "motionDuration"), ("easingToken", "motionEasing")):
            if key in mo:
                t = reg.catalog.get(mo[key])
                if t is None:
                    rep.add("TOKEN_UNKNOWN", f"{p}.motion.{key}", f"{mo[key]} is not in the token catalog")
                elif t["category"] != cat:
                    rep.add("TOKEN_WRONG_ROLE", f"{p}.motion.{key}", f"{mo[key]} is {t['category']}, expected {cat}")

        # style tokens
        for slot, val in (n.get("style") or {}).items():
            check_token(slot, val, theme, reg, f"{p}.style.{slot}", rep)

        # links & assets
        for k, f in fields.items():
            if k not in content:
                continue
            for kind, path, obj in iter_typed(content[k], f, f"{p}.content.{k}"):
                if kind == "asset":
                    check_asset(obj, c, generated, reg, path, rep)
                else:
                    check_link(obj, generated, path, rep)

    graph_rules(spec, tmpl, reg, sev, rep)

    if generated:
        leakage(spec, reg, rep)
    return rep


def check_token(slot, val, theme, reg, path, rep):
    pol = reg.policy["slots"].get(slot)
    if pol is None:
        rep.add("TOKEN_WRONG_ROLE", path, f"style slot {slot} not in token policy")
        return
    font_slot = pol["category"] == "fontFamily"
    if RAW_COLOR.search(val):
        rep.add("TOKEN_RAW_COLOR", path, f"raw colour {val!r}; use a color.* token")
        return
    if RAW_LENGTH.search(val):
        rep.add("TOKEN_ARBITRARY_SPACING", path, f"arbitrary length {val!r}; use a {pol['category']} token")
        return
    t = reg.catalog.get(val)
    if font_slot and (t is None or not val.startswith("font.family.")):
        rep.add("TOKEN_UNSUPPORTED_FONT", path, f"{val!r} is not a supported font token {reg.policy['supportedFonts']}")
        return
    if t is None:
        rep.add("TOKEN_UNKNOWN", path, f"{val!r} is not in the token catalog")
        return
    if t["category"] != pol["category"] or not any(val.startswith(px) for px in pol["prefixes"]):
        rep.add("TOKEN_WRONG_ROLE", path, f"{val} ({t['category']}) not allowed in slot {slot} {pol['prefixes']}")
        return
    bound = t.get("themeBound")
    if bound and bound != theme:
        rep.add("TOKEN_THEME_MISMATCH", path, f"{val} is bound to theme {bound}, PageSpec theme is {theme}")


def check_asset(a, contract, generated, reg, path, rep):
    role = a.get("role")
    allowed_ref = set(contract["assetRoles"]) | set(contract["generatedAssetRoles"])
    if generated:
        avail = PINNED_AVAILABILITY.get(role)
        if role == "brand.wordmark-logo":
            rep.add("GENERATED_MODE_LOGO", path, "the source owner's wordmark/logo can never appear in generated mode")
        elif avail != "generation-safe":
            rep.add("GENERATED_MODE_ASSET", path, f"asset role {role} is {avail}; use one of {reg.roles.get(role, {}).get('generationSafeSubstitutes')}")
        if role not in contract["generatedAssetRoles"] and avail == "generation-safe":
            rep.add("ASSET_ROLE_NOT_ALLOWED", path, f"{role} not in {contract['id']}.generatedAssetRoles")
        if not PLACEHOLDER_SRC.match(a.get("src", "")):
            rep.add("GENERATED_MODE_ASSET", path + ".src", f"generated assets must use placeholder://, generated:// or user-supplied:// sources, got {a.get('src')!r}")
    else:
        if role not in allowed_ref:
            rep.add("ASSET_ROLE_NOT_ALLOWED", path, f"{role} not allowed in {contract['id']}")
        pats = reg.roles.get(role, {}).get("pathPatterns", [])
        if pats and not any(re.search(p_, a.get("src", "")) for p_ in pats):
            rep.add("ASSET_PATH_ROLE_MISMATCH", path + ".src", f"{a.get('src')} does not match role {role} paths {pats}")


def check_link(link, generated, path, rep):
    href, role = link.get("href", ""), link.get("role")
    external = bool(re.match(r"^(https?:|mailto:|//)", href, re.I))
    if generated:
        if PINNED_AVAILABILITY.get(role) != "generation-safe":
            rep.add("GENERATED_MODE_URL", path, f"link role {role} is not generation-safe")
        if role == "link.placeholder-url":
            if not external or not RESERVED_HOST.match(host_of(href)):
                rep.add("GENERATED_MODE_URL", path + ".href", f"{href!r} is not on a reserved placeholder domain")
        elif role == "link.internal-route" and external:
            rep.add("GENERATED_MODE_URL", path + ".href", f"internal-route link points off-site: {href!r}")
    else:
        if external and role != "link.source-url":
            rep.add("LINK_ROLE_MISMATCH", path, f"external href {href!r} must use link.source-url")
        if not external and role != "link.internal-route":
            rep.add("LINK_ROLE_MISMATCH", path, f"relative href {href!r} must use link.internal-route")


def graph_rules(spec, tmpl, reg, sev, rep):
    nodes, overlays = spec.get("nodes", []), spec.get("overlays", [])
    ids = [n["section"] for n in nodes]
    cat = lambda sid: reg.sections.get(sid, {}).get("semantic", {}).get("category")
    if "ONE_HERO" in sev:
        heroes = [i for i, s in enumerate(ids) if cat(s) == "HERO"]
        want = 0 if tmpl.get("noHero") else 1
        if len(heroes) != want:
            rep.add("ONE_HERO", "$.nodes", f"{len(heroes)} HERO sections, template {tmpl['id']} requires {want}", sev["ONE_HERO"])
    if "HERO_FOLLOWS_HEADER" in sev:
        heroes = [i for i, s in enumerate(ids) if cat(s) == "HERO"]
        if heroes and heroes[0] != 1:
            rep.add("HERO_FOLLOWS_HEADER", f"$.nodes[{heroes[0]}]", "the HERO must directly follow shell.header (page opener only)", sev["HERO_FOLLOWS_HEADER"])
    if "SHELL_POSITION" in sev:
        if not ids or ids[0] != "shell.header" or ids.count("shell.header") != 1:
            rep.add("SHELL_POSITION", "$.nodes[0]", "exactly one shell.header, first", sev["SHELL_POSITION"])
        if not ids or ids[-1] != "shell.footer" or ids.count("shell.footer") != 1:
            rep.add("SHELL_POSITION", f"$.nodes[{len(ids) - 1}]", "exactly one shell.footer, last", sev["SHELL_POSITION"])
    if "CLOSING_PRECEDES_FOOTER" in sev:
        idx = [i for i, s in enumerate(ids) if s == "conversion.closing"]
        if len(idx) > 1 or (idx and idx[0] != len(ids) - 2):
            rep.add("CLOSING_PRECEDES_FOOTER", "$.nodes", "conversion.closing appears once, directly before shell.footer", sev["CLOSING_PRECEDES_FOOTER"])
    if "MAX_PER_PAGE" in sev:
        for sid in set(ids):
            mx = reg.sections.get(sid, {}).get("constraints", {}).get("maxPerPage")
            if mx is not None and ids.count(sid) > mx:
                rep.add("MAX_PER_PAGE", "$.nodes", f"{sid} appears {ids.count(sid)} times, max {mx}", sev["MAX_PER_PAGE"])
    if "NO_CONSECUTIVE_SCROLL_NARRATIVES" in sev:
        for i in range(1, len(ids)):
            if ids[i] == ids[i - 1] == "casestudy.scroll-narrative":
                rep.add("NO_CONSECUTIVE_SCROLL_NARRATIVES", f"$.nodes[{i}]", "two scroll-driven narratives back to back", sev["NO_CONSECUTIVE_SCROLL_NARRATIVES"])
    if "ADJACENT_SAME_TONE" in sev:
        for i in range(1, len(nodes)):
            a, b = nodes[i - 1], nodes[i]
            if a["section"] == b["section"] == "casestudy.chapter" and a.get("variant") == b.get("variant") and a.get("variant") in ("tint", "dark"):
                rep.add("ADJACENT_SAME_TONE", f"$.nodes[{i}]", f"two adjacent {a['variant']} chapters lose the alternating rhythm", sev["ADJACENT_SAME_TONE"])
    if "MOTION_BUDGET" in sev:
        pinned = [i for i, n in enumerate(nodes) if n.get("motion", {}).get("pattern") in PINNED_SCROLL_PATTERNS]
        if len(pinned) > 2:
            rep.add("MOTION_BUDGET", "$.nodes", f"{len(pinned)} pinned scroll narratives; the source never uses more than 2 per page", sev["MOTION_BUDGET"])
    if "OVERLAY_PLACEMENT" in sev:
        for i, s in enumerate(ids):
            if reg.sections.get(s, {}).get("constraints", {}).get("overlayOnly"):
                rep.add("OVERLAY_PLACEMENT", f"$.nodes[{i}]", f"{s} is runtime UI: list it under overlays, not nodes", sev["OVERLAY_PLACEMENT"])
        for i, o in enumerate(overlays):
            s = o.get("section")
            if not reg.sections.get(s, {}).get("constraints", {}).get("overlayOnly"):
                rep.add("OVERLAY_PLACEMENT", f"$.overlays[{i}]", f"{s} is in-flow content, not an overlay", sev["OVERLAY_PLACEMENT"])
            elif s not in tmpl.get("overlays", []):
                rep.add("OVERLAY_PLACEMENT", f"$.overlays[{i}]", f"{s} is not an overlay of {tmpl['id']}", sev["OVERLAY_PLACEMENT"])


def leakage(spec, reg, rep):
    cp = reg.compiled()
    n_sh = cp["shingleSize"]
    link_labels = set()
    for i, n in enumerate(spec.get("nodes", []) + spec.get("overlays", [])):
        c = reg.sections.get(n.get("section"))
        if not c:
            continue
        for k, f in c["content"]["fields"].items():
            if k in n.get("content", {}):
                for kind, path, obj in iter_typed(n["content"][k], f, ""):
                    if kind == "link":
                        link_labels.add(obj.get("label", ""))
    for path, s in iter_strings({"meta": spec.get("meta", {}), "nodes": spec.get("nodes", []), "overlays": spec.get("overlays", [])}, "$"):
        if re.search(r"\.(section|variant|role|mediaType|pattern|trigger|reducedMotionFallback|durationToken|easingToken)$", path) or ".style." in path:
            continue
        for rx in cp["brand"] + cp["product"]:
            if rx.search(s):
                rep.add("GENERATED_MODE_BRAND", path, f"source brand/product name matched /{rx.pattern}/")
                break
        for rx in cp["person"] + cp["contact"]:
            if rx.search(s):
                rep.add("GENERATED_MODE_PERSON", path, f"source person/contact matched /{rx.pattern}/")
                break
        for u in URL_TOKEN.findall(s):
            h = host_of(u)
            if not RESERVED_HOST.match(h):
                rep.add("GENERATED_MODE_URL", path, f"non-placeholder URL or domain {u!r}")
                break
        for rx in cp["url"]:
            if rx.search(s):
                rep.add("GENERATED_MODE_URL", path, f"source URL/host matched /{rx.pattern}/")
                break
        norm = normalize(s)
        ws = norm.split()
        if len(ws) >= 3 and fp(norm) in cp["copyFull"]:
            rep.add("GENERATED_MODE_COPY", path, "text is a verbatim source copy segment")
        elif len(ws) >= n_sh:
            for j in range(len(ws) - n_sh + 1):
                if fp(" ".join(ws[j:j + n_sh])) in cp["copyShingles"]:
                    rep.add("GENERATED_MODE_COPY", path, f"shares a {n_sh}-word run with source copy: {' '.join(ws[j:j + n_sh])!r}")
                    break
        if s in link_labels and len(ws) >= 3 and fp(norm) in cp["cta"]:
            rep.add("GENERATED_MODE_CTA", path, "source call-to-action label")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    reg = Registry()
    total_err = 0
    for p in argv:
        with open(p, encoding="utf-8") as f:
            spec = json.load(f)
        rep = validate(spec, reg)
        for i in rep.items:
            print(f"  {i['severity'].upper():5} {i['rule']:32} {i['path']}: {i['message']}")
        print(f"{'PASS' if not rep.errors else 'FAIL'}  {os.path.relpath(p)}  ({len(rep.errors)} errors, {len(rep.warnings)} warnings)")
        total_err += len(rep.errors)
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
