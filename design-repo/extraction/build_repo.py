#!/usr/bin/env python3
"""Builds the design-repo contracts from real evidence.

    python3 extraction/build_repo.py [--heights H.json --styles S.json --scoped C.json]

Inputs
  * extraction/build_spec.py           declarative mapping (fields + evidence selectors, token roles)
  * the sibling site (<design-repo>/.. or $SOURCE_SITE_DIR)   REQUIRED for a build: copy budgets,
    citations (found by needle, never hand-typed line numbers) and reference examples come from it
  * captures from extraction/measure_sections.mjs (heights / styles / scoped). When omitted, the
    measured data already in extraction/measured-values.json is reused.

Outputs: tokens/*, primitives/*, components/*, sections/*, templates/*, compatibility/graph.json,
assets/asset-roles.json, schema/pagespec.schema.json, schema/section-contract.schema.json,
schema/examples/reference.*.json, extraction/measured-values.json, registry.manifest.json counts.
Hand-written files (validators, generated examples, README prose) are not touched except the
README/CHANGELOG count blocks, which are recomputed from disk.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_spec as S  # noqa: E402
import classify_routes  # noqa: E402
import source_dom  # noqa: E402

REPO_VERSION = "1.0.0"
PAGESPEC_VERSION = "1.0.0"
ALLOWLIST_VERSION = "1.0.0"
TOKENS_VERSION = "1.0.0"


def wjson(rel, data):
    path = os.path.join(REPO, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def rjson(rel, default=None):
    path = os.path.join(REPO, rel)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ citations
class Source:
    def __init__(self, root):
        self.root = root
        self._lines = {}
        self._media = {}

    def lines(self, rel):
        if rel not in self._lines:
            with open(os.path.join(self.root, rel), encoding="utf-8") as f:
                self._lines[rel] = f.read().split("\n")
        return self._lines[rel]

    def find(self, rel, needle):
        for i, line in enumerate(self.lines(rel), 1):
            if needle in line:
                return i
        raise SystemExit(f"citation needle not found: {rel}: {needle!r}")

    def cite(self, rel, needle):
        if rel == "css/*":
            for p in sorted(glob.glob(os.path.join(self.root, "css", "*.css"))):
                r = os.path.relpath(p, self.root)
                if any(needle in ln for ln in self.lines(r)):
                    return f"{r}:{self.find(r, needle)}"
            raise SystemExit(f"citation needle not found in any css file: {needle!r}")
        return f"{rel}:{self.find(rel, needle)}"

    def media_blocks(self, rel):
        if rel not in self._media:
            text = "\n".join(self.lines(rel))
            blocks = []
            for m in re.finditer(r"@media[^{]*\{", text):
                depth, j = 1, m.end()
                while depth and j < len(text):
                    depth += {"{": 1, "}": -1}.get(text[j], 0)
                    j += 1
                blocks.append((text[:m.start()].count("\n") + 1, text[:j].count("\n") + 1))
            self._media[rel] = blocks
        return self._media[rel]

    def media_cite(self, rel, needle):
        """Cite the innermost @media block containing the first in-media occurrence of the needle
        (JS sources: the needle's line)."""
        if not rel.endswith(".css"):
            return f"{rel}:{self.find(rel, needle)}"
        for i, line in enumerate(self.lines(rel), 1):
            if needle not in line:
                continue
            best = None
            for a, b in self.media_blocks(rel):
                if a <= i <= b and (best is None or a >= best[0]):
                    best = (a, b)
            if best is not None:
                return f"{rel}:{best[0]}-{best[1]}" if best[1] > best[0] else f"{rel}:{best[0]}"
        raise SystemExit(f"needle not found inside any @media block: {rel}: {needle!r}")


# ------------------------------------------------------------------ copy budgets
def _text_of(n, attr=None):
    if attr:
        return n.attrs.get(attr, "") or ""
    return n.text()


def js_values(src, rel, key):
    text = "\n".join(src.lines(rel))
    vals = re.findall(r"\b%s:\s*'((?:[^'\\]|\\.)*)'" % re.escape(key), text)
    vals += re.findall(r'\b%s:\s*"((?:[^"\\]|\\.)*)"' % re.escape(key), text)
    return [v for v in vals if not v.startswith("[ADD")]


def js_template_words(src, rel, needle, words):
    line_no = src.find(rel, needle)
    if words is not None:
        return words, f"{rel}:{line_no}"
    line = src.lines(rel)[line_no - 1]
    idx = line.index(needle)
    rest = line[idx + len(needle):]
    if ">" in rest:
        txt = rest.split(">", 1)[1].split("<", 1)[0]
    else:
        q = re.search(r"(['\"`])([^'\"`]*%s[^'\"`]*)\1" % re.escape(needle), line)
        txt = q.group(2) if q else needle
    return source_dom.words(txt), f"{rel}:{line_no}"


def field_budget(src, fspec, scopes):
    """Return (budget dict) for one field over a list of scope elements."""
    ev = fspec.get("evidence") or {}
    t = fspec["type"]
    out = {}
    if t == "boolean":
        return out
    if "jsField" in ev:
        rel, key = ev["jsField"]
        vals = js_values(src, rel, key)
        if not vals:
            raise SystemExit(f"jsField evidence empty: {ev}")
        out["maxWords"] = max(source_dom.words(v) for v in vals)
        if t == "textList":
            out["maxItems"] = len(vals)
        out["evidence"] = {"jsField": f"{rel}:{key}", "observed": len(vals), "cite": f"{rel}:{src.find(rel, key + ':')}"}
        return out
    if "jsCount" in ev:
        rel, key = ev["jsCount"]
        n = len(re.findall(r"\b%s:\s*['\"]" % re.escape(key), "\n".join(src.lines(rel))))
        out["maxItems"] = n
        out["evidence"] = {"jsCount": f"{rel}:{key}", "observed": n, "cite": f"{rel}:{src.find(rel, key + ':')}"}
        sub = {}
        for k, v in (fspec.get("item") or {}).items():
            sub[k] = field_budget(src, v, [])
        out["item"] = sub
        return out
    if "jsTemplate" in ev:
        rel, needle, words = ev["jsTemplate"]
        w, cite = js_template_words(src, rel, needle, words)
        out["maxWords"] = w
        out["evidence"] = {"jsTemplate": cite}
        return out
    sel, attr = ev.get("selector"), ev.get("attr")
    if not sel:
        raise SystemExit(f"field without evidence: {fspec}")
    per_scope = [source_dom.select(s, sel) for s in scopes]
    matched = [m for ms in per_scope for m in ms]
    if not matched:
        raise SystemExit(f"evidence selector matched nothing: {sel!r}")
    out["evidence"] = {"selector": sel, **({"attr": attr} if attr else {}), "observedElements": len(matched),
                       "observedBlocks": sum(1 for ms in per_scope if ms)}
    if t in ("text",):
        if fspec.get("joinMatches"):
            out["maxWords"] = max(source_dom.words(" ".join(_text_of(m, attr) for m in ms)) for ms in per_scope if ms)
        else:
            out["maxWords"] = max(source_dom.words(_text_of(m, attr)) for m in matched)
    elif t in ("textList",):
        out["maxWords"] = max(source_dom.words(_text_of(m, attr)) for m in matched)
        out["maxItems"] = max(len(ms) for ms in per_scope)
    elif t in ("link",):
        out["maxWords"] = max(source_dom.words(_text_of(m, attr)) for m in matched)
    elif t in ("links",):
        out["maxWords"] = max(source_dom.words(_text_of(m, attr)) for m in matched)
        out["maxItems"] = max(len(ms) for ms in per_scope)
    elif t in ("asset",):
        out["maxWords"] = max(source_dom.words(_text_of(m, attr or "alt")) for m in matched)
    elif t in ("assets",):
        out["maxWords"] = max(source_dom.words(_text_of(m, attr or "alt")) for m in matched)
        out["maxItems"] = max(len(ms) for ms in per_scope)
    elif t in ("list", "meta", "object"):
        if t != "object":
            out["maxItems"] = max(len(ms) for ms in per_scope)
        sub = {}
        for k, v in fspec["item"].items():
            if v["type"] == "boolean":
                sub[k] = {}
                continue
            if "jsTemplate" in (v.get("evidence") or {}) or "jsField" in (v.get("evidence") or {}):
                sub[k] = field_budget(src, v, [])
            else:
                sub[k] = field_budget(src, v, matched)
        out["item"] = sub
    else:
        raise SystemExit(f"unknown field type {t}")
    return out


def section_scopes(classified, sid):
    out = []
    for route, (seq, dom) in classified.items():
        blks = source_dom.blocks(dom)
        for s, b in zip(seq, blks):
            if s["section"] == sid:
                out.append((route, s, b))
    return out


def utility_scopes(src, classified, spec):
    rel, tag, sel = spec["source"]
    if rel.endswith(".js"):
        return []
    out = []
    for route, (seq, dom) in classified.items():
        for n in source_dom.select(dom, sel):
            out.append((route, None, n))
    return out


def compute_budgets(src, classified):
    budgets = {}
    for sid, spec in S.SECTIONS.items():
        scopes = utility_scopes(src, classified, spec) if spec.get("overlay") else section_scopes(classified, sid)
        elems = [b for _, _, b in scopes]
        budgets[sid] = {}
        for k, v in spec["fields"].items():
            try:
                budgets[sid][k] = field_budget(src, v, elems)
            except SystemExit as e:
                raise SystemExit(f"{sid}.{k}: {e}")
    return budgets


# ------------------------------------------------------------------ measured data ingest
def ingest(heights, styles, scoped, classified):
    mv = rjson("extraction/measured-values.json", {}) or {}
    if heights:
        with open(heights) as f:
            H = json.load(f)
        sh = {"viewport": {"width": 1440, "height": 900}, "measuredWith": "extraction/measure_sections.mjs heights",
              "measuredAt": H["measuredAt"], "routes": {}}
        page = {}
        for route in S.ROUTES:
            seq = classified[route][0]
            m = H["routes"][route]["1440"]
            if len(m["blocks"]) != len(seq):
                raise SystemExit(f"{route}: measured {len(m['blocks'])} blocks, classifier {len(seq)}")
            blocks = []
            for i, (b, s) in enumerate(zip(m["blocks"], seq)):
                if b["tag"] != s["tag"] or b["classes"] != s["classes"]:
                    raise SystemExit(f"{route}: block {i} signature mismatch {b['classes']} vs {s['classes']}")
                blocks.append({"index": i, "section": s["section"], "variant": s["variant"],
                               "sourceSignature": s["tag"] + "".join("." + c for c in s["classes"]),
                               "topPx": b["top"], "heightPx": b["height"], "position": b["position"]})
            sh["routes"][route] = {"pageHeightPx": m["scrollHeight"], "blocks": blocks}
            page[route] = {w: H["routes"][route][w]["scrollHeight"] for w in ("1440", "768", "390")}
        mv["sectionHeights"] = sh
        mv["pageHeights"] = {"viewports": {"1440": "1440x900", "768": "768x1024", "390": "390x844"}, "routes": page,
                             "note": "document scrollHeight after a full scroll pass (lazy media loaded)."}
    if styles:
        with open(styles) as f:
            ST = json.load(f)
        site = {t: ST["routes"]["index.html"][t]["vars"] for t in ("night", "day")}
        story = {t: ST["routes"]["offline-doctor-consultation.html"][t]["vars"] for t in ("night", "day")}
        mv["resolvedCustomProperties"] = {"note": "getComputedStyle(:root) per theme, extraction/measure_sections.mjs styles",
                                          "site": site, "story-page": story}
        hist = {}
        for theme in ("night", "day"):
            agg = {}
            for route in S.ROUTES:
                for k, c in ST["routes"][route][theme]["hist"].items():
                    for v, n in c.items():
                        agg.setdefault(k, {}).setdefault(v, 0)
                        agg[k][v] += n
            hist[theme] = {k: dict(sorted(c.items(), key=lambda kv: -kv[1])[:16]) for k, c in agg.items()}
        mv["styleHistograms"] = {"note": "counts of visible elements per computed value, all 12 routes, 1440x900", "themes": hist}
    if scoped:
        with open(scoped) as f:
            SC = json.load(f)
        mv["resolvedScopedProperties"] = {"note": "getComputedStyle(scope) per theme", "scopes": SC["scopes"]}
    return mv


# ------------------------------------------------------------------ tokens
def norm(v):
    return re.sub(r"\s+", " ", v.strip().lower())


def css_decl_cite(src, prop, value=None, files=None):
    """Cite the declaration of a custom property; prefer the line whose literal value matches."""
    files = files or sorted(os.path.relpath(p, src.root) for p in glob.glob(os.path.join(src.root, "css", "*.css")))
    first = None
    for rel in files:
        for i, line in enumerate(src.lines(rel), 1):
            m = re.search(r"(^|[;{\s])%s\s*:\s*([^;]+);" % re.escape(prop), line)
            if not m:
                continue
            if first is None:
                first = f"{rel}:{i}"
            if value is not None and norm(m.group(2)).replace(" !important", "") == norm(value):
                return f"{rel}:{i}"
    if first is None:
        raise SystemExit(f"no declaration for {prop}")
    if value is not None:
        # declared through an alias (e.g. --text: var(--n-ink)): cite the custom property that holds the literal
        for rel in files:
            for i, line in enumerate(src.lines(rel), 1):
                for m in re.finditer(r"(--[A-Za-z0-9-]+)\s*:\s*([^;]+);", line):
                    if norm(m.group(2)).replace(" !important", "") == norm(value):
                        return f"{rel}:{i}"
    return first


SEMANTIC_COLOR = {
    # semantic id: custom property (resolved per theme on :root)
    "color.text.primary": "--text", "color.text.secondary": "--text-muted", "color.text.faint": "--text-faint",
    "color.surface.page": "--bg", "color.surface.tint": "--ground-tint", "color.surface.raised": "--surface",
    "color.border.default": "--n-line", "color.border.strong": "--n-line-2", "color.action.hover": "--n-hover",
    "color.accent.primary": "--p", "color.accent.hover": "--p-hover", "color.accent.ink": "--p-ink",
    "color.accent.tint": "--p-tint", "color.accent.line": "--p-line",
    "color.status.ok": "--ok", "color.status.ok-tint": "--ok-tint", "color.status.warn": "--warn", "color.status.warn-tint": "--warn-tint",
    "color.status.err": "--err", "color.status.err-tint": "--err-tint", "color.status.info": "--info", "color.status.info-tint": "--info-tint",
    "color.decor.pink": "--a-pink", "color.decor.pink-deep": "--a-pink-deep", "color.decor.yellow": "--a-yellow",
    "color.decor.purple": "--a-purple", "color.decor.purple-deep": "--a-purple-deep",
}
# the case-study v3 scope's dark band: --tint/--paper are scope tokens; the inverse surface is the v3 console colour
SCOPE_COLOR = {"main.v3": {"color.surface.inverse": None}}


def build_tokens(src, mv):
    site = mv["resolvedCustomProperties"]["site"]
    story = mv["resolvedCustomProperties"]["story-page"]
    scopes = mv["resolvedScopedProperties"]["scopes"]
    files = {}

    # -- foundation colour palette (theme-bound) + semantic references
    palette, semantic = {}, {}
    for sid, prop in SEMANTIC_COLOR.items():
        n, d = site["night"][prop], site["day"][prop]
        short = sid.split(".", 1)[1].replace(".", "-")
        if norm(n) == norm(d):
            pid = f"palette.shared.{short}"
            palette[pid] = {"value": d, "cssProperty": prop, "cite": css_decl_cite(src, prop, d)}
            semantic[sid] = {"night": "{%s}" % pid, "day": "{%s}" % pid}
        else:
            for theme, val in (("night", n), ("day", d)):
                pid = f"palette.{theme}.{short}"
                palette[pid] = {"value": val, "cssProperty": prop, "theme": theme, "cite": css_decl_cite(src, prop, val)}
            semantic[sid] = {"night": "{palette.night.%s}" % short, "day": "{palette.day.%s}" % short}
    # inverse (dark band / console) surface, measured from the case-study scope
    v3n, v3d = scopes["main.v3"]["night"], scopes["main.v3"]["day"]
    palette["palette.night.surface-inverse"] = {"value": "#221d29", "cssProperty": ".v3-dark background (night override)",
                                                "theme": "night", "cite": src.cite("css/theme.css", "html[data-theme=\"night\"] :is(.v3-dark, .v3-ways-one, .vc-lesson) { background: #221d29")}
    palette["palette.day.surface-inverse"] = {"value": v3d["--ink"], "cssProperty": ".v3-dark background: var(--ink) (case-study scope, day)",
                                              "theme": "day", "cite": src.cite("css/visit-clinic-v3.css", ".v3-dark { background: var(--ink);")}
    semantic["color.surface.inverse"] = {"night": "{palette.night.surface-inverse}", "day": "{palette.day.surface-inverse}"}
    files["tokens/00-foundation/color.json"] = {"$description": "Raw colour values resolved from the real :root custom properties per theme (measure_sections.mjs styles). palette.night.* / palette.day.* are theme-bound; palette.shared.* are identical in both themes.", "tokens": palette}
    files["tokens/10-semantic/color.json"] = {"$description": "Semantic colour roles; each resolves to a foundation palette token per theme (reference, never a duplicated value).", "tokens": {k: {"themes": v} for k, v in semantic.items()}}

    # -- typography
    typo = {
        "font.family.display": {"value": "'Outfit', 'Inter', system-ui, sans-serif", "cssProperty": "--font-display", "cite": css_decl_cite(src, "--font-display")},
        "font.family.text": {"value": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif", "cssProperty": "--font-sans", "cite": css_decl_cite(src, "--font-sans")},
    }
    for name in ("xs", "sm", "base", "md", "lg", "xl", "2xl", "3xl", "hero"):
        prop = f"--text-{name}"
        typo[f"font.size.{name}"] = {"value": site["day"][prop], "cssProperty": prop, "cite": css_decl_cite(src, prop)}
    for name in ("h1", "h2", "h3", "lead", "body"):
        prop = f"--cs-{name}"
        typo[f"font.size.cs-{name}"] = {"value": site["day"][prop], "cssProperty": prop, "cite": css_decl_cite(src, prop)}
    for name in ("tight", "snug", "normal", "relaxed"):
        prop = f"--leading-{name}"
        typo[f"font.line-height.{name}"] = {"value": site["day"][prop], "cssProperty": prop, "cite": css_decl_cite(src, prop)}
    wh = mv["styleHistograms"]["themes"]["day"]["fontWeight"]
    for w in ("400", "500", "600", "700"):
        typo[f"font.weight.{w}"] = {"value": w, "measuredCount": wh.get(w, 0), "cite": "extraction/measured-values.json#styleHistograms"}
    files["tokens/00-foundation/typography.json"] = {"$description": "Two families only (Outfit display, Inter text), measured: the computed fontFamily histogram has exactly these two. Sizes are the real custom properties; weights are the measured top weights.", "tokens": typo}

    # -- spacing
    space = {}
    for i in range(1, 12):
        prop = f"--sp-{i}"
        space[f"space.{i}"] = {"value": site["day"][prop], "cssProperty": prop, "cite": css_decl_cite(src, prop)}
    files["tokens/00-foundation/spacing.json"] = {"$description": "4px-based spacing scale from the real --sp-* custom properties.", "tokens": space}

    # -- radius (measured histogram values, cited by first declaration)
    rh = mv["styleHistograms"]["themes"]["day"]["borderRadius"]
    radius = {}
    for tid, val, needle_file, needle in [
        ("radius.pill", "999px", "css/cta.css", "--cta-radius: 999px;"),
        ("radius.xs", "2px", "css/*", "border-radius: 2px"),
        ("radius.sm", "4px", "css/*", "border-radius: 4px"),
        ("radius.md", "12px", "css/*", "border-radius: 12px"),
        ("radius.card", "20px", "css/*", "border-radius: 20px"),
        ("radius.lg", "16px", "css/*", "border-radius: 16px"),
        ("radius.xl", "24px", "css/*", "border-radius: 24px"),
        ("radius.circle", "50%", "css/*", "border-radius: 50%"),
    ]:
        radius[tid] = {"value": val, "measuredCount": rh.get(val, 0), "cite": src.cite(needle_file, needle)}
    files["tokens/00-foundation/radius.json"] = {"$description": "Radius scale from the measured computed border-radius histogram (counts recorded); cited at a real declaration.", "tokens": radius}

    # -- motion
    motion = {
        "motion.duration.fast": {"value": site["day"]["--dur-fast"], "cssProperty": "--dur-fast", "cite": css_decl_cite(src, "--dur-fast")},
        "motion.duration.base": {"value": site["day"]["--dur-base"], "cssProperty": "--dur-base", "cite": css_decl_cite(src, "--dur-base")},
        "motion.duration.slow": {"value": site["day"]["--dur-slow"], "cssProperty": "--dur-slow", "cite": css_decl_cite(src, "--dur-slow")},
        "motion.duration.control": {"value": "200ms", "cssProperty": "--cta-ease (0.2s)", "cite": css_decl_cite(src, "--cta-ease")},
        "motion.duration.theme": {"value": "400ms", "cite": src.cite("css/theme.css", ".theme-anim, .theme-anim * { transition: background-color .4s ease")},
        "motion.duration.reveal": {"value": "600ms", "cite": src.cite("css/styles.css", "transition: opacity 0.6s var(--ease), transform 0.6s var(--ease);")},
        "motion.duration.reveal-long": {"value": "700ms", "cite": src.cite("css/oc-story.css", ".has-js .rv { opacity: 0;")},
        "motion.duration.reveal-soft": {"value": "900ms", "cite": src.cite("css/little-world.css", "html.has-js .lw-r { opacity: 0;")},
        "motion.easing.standard": {"value": site["day"]["--ease"], "cssProperty": "--ease", "cite": css_decl_cite(src, "--ease", site["day"]["--ease"])},
        "motion.easing.soft": {"value": scopes["section.lw"]["day"]["--soft"], "cssProperty": "--soft", "cite": css_decl_cite(src, "--soft")},
        "motion.easing.story": {"value": story["day"]["--ease"], "cssProperty": "--ease (story page)", "cite": css_decl_cite(src, "--ease", story["day"]["--ease"], ["css/oc-story.css"])},
        "motion.easing.reveal": {"value": "cubic-bezier(.2,.7,.2,1)", "cite": src.cite("css/visit-clinic-v3.css", ".v3-rv { opacity: 0;")},
        "motion.easing.spring": {"value": story["day"]["--spring"], "cssProperty": "--spring (story page)", "cite": css_decl_cite(src, "--spring", story["day"]["--spring"], ["css/oc-story.css"])},
        "motion.easing.spring-playful": {"value": scopes["section.lw"]["day"]["--spring"], "cssProperty": "--spring (little-world scope)", "cite": css_decl_cite(src, "--spring", None, ["css/little-world.css"])},
    }
    files["tokens/00-foundation/motion.json"] = {"$description": "Durations and easings from real custom properties and real transition declarations.", "tokens": motion}

    # -- breakpoints (from the @media histogram)
    bps = {}
    for tid, val, needle_file, needle in [
        ("bp.narrow", "560px", "css/cta.css", "@media (max-width: 560px)"),
        ("bp.mobile", "640px", "css/case.css", "@media (max-width: 640px)"),
        ("bp.tablet", "760px", "css/ai-feature.css", "@media (max-width: 760px)"),
        ("bp.nav", "860px", "css/styles.css", "@media (min-width: 860px)"),
        ("bp.content", "900px", "css/case.css", "@media (max-width: 900px)"),
        ("bp.desktop", "980px", "css/visit-clinic-v3.css", "@media (min-width: 980px)"),
        ("bp.wide", "1024px", "css/base.css", "@media (min-width: 1024px)"),
    ]:
        bps[tid] = {"value": val, "cite": src.cite(needle_file, needle)}
    files["tokens/00-foundation/breakpoint.json"] = {"$description": "Breakpoints from the real @media queries (counts in extraction/measured-values.json#breakpointHistogram). 979/980px is the mobile/desktop split also used by js/main.js.", "tokens": bps}

    # -- elevation (theme-bound story-page shadow)
    elev = {
        "elevation.story-card": {"themes": {"night": story["night"]["--shadow"], "day": story["day"]["--shadow"]}, "cssProperty": "--shadow (story page)", "cite": css_decl_cite(src, "--shadow", None, ["css/oc-story.css"])},
    }
    files["tokens/00-foundation/elevation.json"] = {"$description": "Only elevation expressed as a token in the source (story page --shadow), per theme.", "tokens": elev}

    # -- layout
    layout = {
        "layout.container-max": {"value": site["day"]["--container-max"], "cssProperty": "--container-max", "cite": css_decl_cite(src, "--container-max")},
        "layout.measure": {"value": site["day"]["--measure"], "cssProperty": "--measure", "cite": css_decl_cite(src, "--measure")},
        "layout.nav-height": {"value": site["day"]["--nav-height"], "cssProperty": "--nav-height", "cite": css_decl_cite(src, "--nav-height")},
        "layout.story-wrap": {"value": story["day"]["--wrap"], "cssProperty": "--wrap (story page)", "cite": css_decl_cite(src, "--wrap", None, ["css/oc-story.css"])},
    }
    files["tokens/30-layout/layout.json"] = {"$description": "Container, reading measure, nav height and the story page's wrap width.", "tokens": layout}

    # -- component tokens
    cta = {}
    for tid, prop in [("component.cta.height", "--cta-h"), ("component.cta.height-sm", "--cta-h-sm"), ("component.cta.padding-x", "--cta-px"),
                      ("component.cta.padding-x-sm", "--cta-px-sm"), ("component.cta.radius", "--cta-radius"), ("component.cta.border", "--cta-border")]:
        cta[tid] = {"value": site["day"][prop], "cssProperty": prop, "cite": css_decl_cite(src, prop)}
    files["tokens/20-component/cta.json"] = {"$description": "Button sizing from css/cta.css custom properties.", "tokens": cta}
    storyt = {}
    for tid, prop in [("story.surface.page", "--bg"), ("story.surface.alt", "--bg-2"), ("story.surface.card", "--card"), ("story.surface.card-2", "--card-2"),
                      ("story.text.primary", "--ink"), ("story.text.secondary", "--ink-2"), ("story.text.faint", "--ink-3"), ("story.border", "--line"),
                      ("story.highlight", "--hl"), ("story.paper", "--paper"), ("story.paper-ink", "--paper-ink"), ("story.warn", "--warn")]:
        storyt[tid] = {"themes": {"night": story["night"][prop], "day": story["day"][prop]}, "cssProperty": prop + " (story page)",
                       "cite": css_decl_cite(src, prop, story["night"][prop], ["css/oc-story.css"])}
    for tid, prop in [("story.font-size.hero", "--fs-hero"), ("story.font-size.h2", "--fs-h2"), ("story.font-size.h3", "--fs-h3"), ("story.font-size.lead", "--fs-lead")]:
        storyt[tid] = {"value": story["day"][prop], "cssProperty": prop, "cite": css_decl_cite(src, prop, None, ["css/oc-story.css"])}
    files["tokens/20-component/story-page.json"] = {"$description": "Page-local token set of the long-form story case study (it loads only css/oc-story.css); same Night-default/Day mechanism.", "tokens": storyt}
    v3 = {}
    for tid, prop in [("casestudy.accent", "--acc"), ("casestudy.accent-2", "--acc-2"), ("casestudy.accent-tint", "--acc-tint"), ("casestudy.text", "--ink"),
                      ("casestudy.muted", "--muted"), ("casestudy.line", "--line"), ("casestudy.paper", "--paper"), ("casestudy.tint", "--tint")]:
        v3[tid] = {"themes": {"night": v3n[prop], "day": v3d[prop]}, "cssProperty": prop + " (case-study scope)",
                   "cite": css_decl_cite(src, prop, None, ["css/visit-clinic-v3.css"])}
    files["tokens/20-component/case-study.json"] = {"$description": "Scope tokens of the chaptered case-study layout (main.v3), resolved per theme.", "tokens": v3}

    # -- themes
    for theme in ("night", "day"):
        resolved = {}
        for sid, refs in semantic.items():
            ref = refs[theme].strip("{}")
            resolved[sid] = palette[ref]["value"]
        files[f"tokens/themes/{theme}.json"] = {
            "theme": theme, "default": theme == "night",
            "$description": ("Default theme: an inline head script sets data-theme=night unless sessionStorage 'site-theme' is 'day'." if theme == "night"
                             else "Day theme: chosen with the header switch; remembered for the session only."),
            "cite": src.cite("index.html", "sessionStorage.getItem('site-theme')!=='day'"),
            "resolves": resolved,
        }
    return files


def flatten_catalog(files):
    cat = []
    for rel, data in sorted(files.items()):
        if "/themes/" in rel:
            continue
        tier = rel.split("/")[1].split("-", 1)[1]
        for tid, t in data["tokens"].items():
            entry = {"id": tid, "category": token_category(tid), "tier": tier, "file": rel}
            if "themes" in t:
                if tier == "semantic":
                    entry["themes"] = {th: files["tokens/00-foundation/color.json"]["tokens"][r.strip("{}")]["value"] for th, r in t["themes"].items()}
                    entry["references"] = t["themes"]
                else:
                    entry["themes"] = t["themes"]
            else:
                entry["value"] = t["value"]
            if tid.startswith("palette.night."):
                entry["themeBound"] = "night"
            elif tid.startswith("palette.day."):
                entry["themeBound"] = "day"
            cat.append(entry)
    return cat


def token_category(tid):
    for prefix, cat in [("palette.", "color"), ("color.", "color"), ("font.family.", "fontFamily"), ("font.size.", "fontSize"),
                        ("font.weight.", "fontWeight"), ("font.line-height.", "lineHeight"), ("space.", "spacing"), ("radius.", "radius"),
                        ("motion.duration.", "motionDuration"), ("motion.easing.", "motionEasing"), ("bp.", "breakpoint"), ("elevation.", "elevation"),
                        ("layout.", "layout"), ("component.", "component"), ("story.", "component"), ("casestudy.", "component")]:
        if tid.startswith(prefix):
            return cat
    raise SystemExit(f"uncategorised token {tid}")


# ------------------------------------------------------------------ JSON Schema
def field_schema(f, budget):
    t = f["type"]
    if t == "text":
        return {"type": "string", "minLength": 1}
    if t == "boolean":
        return {"type": "boolean"}
    if t == "textList":
        return {"type": "array", "minItems": 1, "maxItems": budget.get("maxItems", 1), "items": {"type": "string", "minLength": 1}}
    if t == "link":
        return {"$ref": "#/definitions/link"}
    if t == "links":
        return {"type": "array", "minItems": 1, "maxItems": budget["maxItems"], "items": {"$ref": "#/definitions/link"}}
    if t == "asset":
        return {"$ref": "#/definitions/asset"}
    if t == "assets":
        return {"type": "array", "minItems": 1, "maxItems": budget["maxItems"], "items": {"$ref": "#/definitions/asset"}}
    if t in ("list", "meta", "object"):
        props, req = {}, []
        for k, v in f["item"].items():
            props[k] = field_schema(v, budget["item"].get(k, {}))
            if v.get("required"):
                req.append(k)
        obj = {"type": "object", "additionalProperties": False, "properties": props}
        if req:
            obj["required"] = req
        if t == "object":
            return obj
        return {"type": "array", "minItems": 1, "maxItems": budget["maxItems"], "items": obj}
    raise SystemExit(t)


def build_pagespec_schema(sections, catalog):
    style_slots = ["surface", "text", "accent", "paddingBlock", "gap", "radius", "headingFont", "bodyFont"]
    node_branches = []
    for sid, c in sections.items():
        props, req = {}, []
        for k, f in c["content"]["fields"].items():
            props[k] = field_schema(f, f)
            if f.get("required"):
                req.append(k)
        content = {"type": "object", "additionalProperties": False, "properties": props}
        if req:
            content["required"] = req
        node_branches.append({"if": {"properties": {"section": {"const": sid}}, "required": ["section"]},
                              "then": {"properties": {"variant": {"enum": c["variants"]}, "content": content,
                                                      "motion": {"properties": {"pattern": {"enum": c["motion"]["allowedPatterns"]}}}}}})
    asset_roles = sorted(S.ASSET_ROLES)
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "pagespec.schema.json",
        "title": "PageSpec",
        "description": "Machine contract for one page composed from this design-repo. Structural layer only: schema/semantic_validate.py enforces template sequences, word budgets, token policy, retrieval eligibility, motion fallbacks and generated-mode leakage rules.",
        "type": "object",
        "additionalProperties": False,
        "required": ["pageSpecVersion", "mode", "template", "route", "theme", "meta", "nodes"],
        "properties": {
            "pageSpecVersion": {"const": PAGESPEC_VERSION},
            "mode": {"enum": ["reference", "generated"], "description": "reference = faithful reconstruction of the source (real brand/copy/assets allowed as evidence); generated = a new page for someone else, nothing from the source's identity or content."},
            "template": {"enum": sorted(S.TEMPLATES)},
            "route": {"type": "string", "pattern": "^([a-z0-9-]+\\.html|/[a-z0-9\\-/]*)$"},
            "theme": {"enum": ["night", "day"]},
            "meta": {"type": "object", "additionalProperties": False, "required": ["title"],
                     "properties": {"title": {"type": "string", "minLength": 1}, "description": {"type": "string", "minLength": 1}}},
            "nodes": {"type": "array", "minItems": 1, "items": {"$ref": "#/definitions/node"}},
            "overlays": {"type": "array", "items": {"$ref": "#/definitions/node"}},
        },
        "definitions": {
            "node": {
                "type": "object", "additionalProperties": False,
                "required": ["section", "variant", "content", "motion"],
                "properties": {
                    "section": {"enum": sorted(sections)},
                    "variant": {"type": "string"},
                    "retrievalEligible": {"type": "boolean"},
                    "content": {"type": "object"},
                    "motion": {"$ref": "#/definitions/motion"},
                    "style": {"$ref": "#/definitions/style"},
                },
                "allOf": node_branches,
            },
            "motion": {
                "type": "object", "additionalProperties": False, "required": ["pattern", "reducedMotionFallback"],
                "properties": {
                    "pattern": {"enum": sorted(S.MOTION_PATTERNS)},
                    "trigger": {"enum": S.TRIGGERS},
                    "reducedMotionFallback": {"enum": S.REDUCED_MOTION_FALLBACKS},
                    "durationToken": {"type": "string", "pattern": "^motion\\.duration\\.[a-z0-9-]+$"},
                    "easingToken": {"type": "string", "pattern": "^motion\\.easing\\.[a-z0-9-]+$"},
                },
            },
            "style": {"type": "object", "additionalProperties": False, "properties": {k: {"type": "string", "minLength": 1} for k in style_slots}},
            "asset": {"type": "object", "additionalProperties": False, "required": ["role", "src", "mediaType"],
                      "properties": {"role": {"enum": asset_roles}, "src": {"type": "string", "minLength": 1}, "alt": {"type": "string"},
                                     "mediaType": {"enum": ["image", "video"]}}},
            "link": {"type": "object", "additionalProperties": False, "required": ["label", "href", "role"],
                     "properties": {"label": {"type": "string", "minLength": 1}, "href": {"type": "string", "minLength": 1},
                                    "role": {"enum": sorted(S.LINK_ROLES)}}},
        },
    }


SECTION_CONTRACT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "section-contract.schema.json",
    "title": "Section contract",
    "type": "object", "additionalProperties": False,
    "required": ["id", "title", "description", "source", "semantic", "retrievalEligible", "variants", "content", "constraints", "motion", "responsive",
                 "assetRoles", "generatedAssetRoles", "components", "tokens"],
    "properties": {
        "id": {"type": "string", "pattern": "^[a-z]+\\.[a-z0-9-]+$"},
        "title": {"type": "string"}, "description": {"type": "string"},
        "source": {"type": "object", "additionalProperties": False, "required": ["id", "file", "tag", "selector", "lines", "citation"],
                   "properties": {"id": {"type": "string", "pattern": "^src\\."}, "file": {"type": "string"}, "tag": {"type": "string"},
                                  "selector": {"type": "string"}, "lines": {"type": "string", "pattern": "^[0-9]+(-[0-9]+)?$"},
                                  "citation": {"type": "string", "pattern": "^[^:]+:[0-9]+(-[0-9]+)?$"},
                                  "observedIn": {"type": "array", "items": {"type": "string"}}}},
        "semantic": {"type": "object", "additionalProperties": False, "required": ["id", "category"],
                     "properties": {"id": {"type": "string"}, "category": {"enum": S.CATEGORIES}}},
        "retrievalEligible": {"type": "boolean"},
        "retrievalReason": {"type": "string", "minLength": 30},
        "variants": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "content": {"type": "object", "required": ["fields"], "additionalProperties": False, "properties": {"fields": {"type": "object"}}},
        "constraints": {"type": "object", "additionalProperties": False,
                        "properties": {"maxPerPage": {"type": "integer"}, "overlayOnly": {"type": "boolean"}, "usedByTemplates": {"type": "array", "items": {"type": "string"}}}},
        "motion": {"type": "object", "additionalProperties": False, "required": ["allowedPatterns", "default"],
                   "properties": {"allowedPatterns": {"type": "array", "items": {"enum": sorted(S.MOTION_PATTERNS)}}, "default": {"enum": sorted(S.MOTION_PATTERNS)}}},
        "responsive": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["breakpoint", "query", "change", "cite"],
                                                    "properties": {"breakpoint": {"type": "string", "pattern": "^bp\\."}, "query": {"type": "string"},
                                                                   "change": {"enum": ["swap-nav-for-menu", "hide-element", "resize-type", "reflow-spacing", "horizontal-scroll",
                                                                                       "resize-element", "stack-columns", "reduce-columns", "compact-controls", "unpin-sticky",
                                                                                       "shorten-scroll-track", "show-only-below"]},
                                                                   "cite": {"type": "string", "pattern": "^[^:]+:[0-9]+(-[0-9]+)?$"}}}},
        "responsiveNote": {"type": "string"},
        "assetRoles": {"type": "array", "items": {"type": "string"}},
        "generatedAssetRoles": {"type": "array", "items": {"type": "string"}},
        "components": {"type": "array", "items": {"type": "string"}},
        "tokens": {"type": "array", "items": {"type": "string"}},
    },
    "allOf": [{"if": {"properties": {"retrievalEligible": {"const": False}}}, "then": {"required": ["retrievalReason"]}}],
}


# ------------------------------------------------------------------ reference extraction
def role_for_path(path):
    for rid, r in S.ASSET_ROLES.items():
        for p in r["pathPatterns"]:
            if re.search(p, path):
                return rid
    return None


def media_of(n):
    for d in [n] + list(n.iter()):
        if d.tag in ("img", "video", "source"):
            src = d.attrs.get("src") or ""
            if not src and d.tag == "video":
                s = next((x for x in d.iter() if x.tag == "source"), None)
                src = s.attrs.get("src", "") if s else ""
            if src:
                return d, src.split("?")[0], ("video" if src.split("?")[0].endswith(".mp4") else "image")
    return None, None, None


def link_of(n, attr=None):
    a = n if n.tag in ("a", "button") else next((d for d in n.iter() if d.tag == "a"), n)
    label = " ".join((n.attrs.get(attr) if attr else a.text()).split()).strip(" →↗←")
    href = a.attrs.get("href") or "#"
    role = "link.source-url" if re.match(r"^(https?:|mailto:)", href) else "link.internal-route"
    return {"label": label or "Link", "href": href, "role": role}


def fill(fields, scope, budgets):
    out = {}
    for k, f in fields.items():
        ev = f.get("evidence") or {}
        sel = ev.get("selector")
        t = f["type"]
        if t == "boolean" or not sel:
            continue
        ms = source_dom.select(scope, sel)
        if not ms:
            continue
        attr = ev.get("attr")
        if t == "text":
            txt = " ".join(m.text() for m in ms) if f.get("joinMatches") else ms[0].text()
            if attr and t == "text" and not txt:
                txt = ms[0].attrs.get(attr, "")
            if txt.strip():
                out[k] = " ".join(txt.split())
        elif t == "textList":
            vals = [" ".join(m.text().split()) for m in ms if m.text().strip()]
            if vals:
                out[k] = vals
        elif t == "link":
            out[k] = link_of(ms[0], attr)
        elif t == "links":
            out[k] = [link_of(m, attr) for m in ms]
        elif t in ("asset", "assets"):
            items = []
            for m in ms:
                el, src_, mt = media_of(m)
                if not src_:
                    continue
                role = role_for_path(src_)
                if role is None:
                    continue
                a = {"role": role, "src": src_, "mediaType": mt}
                alt = (el.attrs.get("alt") or el.attrs.get("aria-label") or m.attrs.get("aria-label") or "").strip()
                if alt:
                    a["alt"] = alt
                items.append(a)
            if items:
                out[k] = items[0] if t == "asset" else items
        elif t in ("list", "meta", "object"):
            sub = [fill(f["item"], m, budgets) for m in ms]
            sub = [s for s in sub if s]
            for s_ in sub:
                for bk, bv in f["item"].items():
                    if bv["type"] == "boolean" and bk not in s_:
                        s_[bk] = False
            if sub:
                out[k] = sub[0] if t == "object" else sub
    return out


def trim_to_budget(content, contract_fields):
    """Reference examples carry real copy; lists are trimmed to their item budget only."""
    for k, f in contract_fields.items():
        if k not in content:
            continue
        if f["type"] in ("list", "meta", "links", "assets", "textList") and isinstance(content[k], list):
            content[k] = content[k][: f.get("maxItems", len(content[k]))]
            if f["type"] in ("list", "meta"):
                for it in content[k]:
                    trim_to_budget(it, f["item"])
        if f["type"] == "object" and isinstance(content[k], dict):
            trim_to_budget(content[k], f["item"])


def data_js_projects(src):
    text = "\n".join(src.lines("js/data.js"))
    chunks = text.split("slug: '")[1:]
    out = []
    for ch in chunks:
        title = re.search(r"\btitle:\s*'((?:[^'\\]|\\.)*)'", ch)
        one = re.search(r"\boneLiner:\s*'((?:[^'\\]|\\.)*)'", ch)
        page = re.search(r"\bpageUrl:\s*'([^']*)'", ch)
        ext = re.search(r"\bexternalUrl:\s*'([^']*)'", ch)
        locked = re.search(r"\blocked:\s*true", ch.split("title:")[0]) is not None
        if not title:
            continue
        href = page.group(1) if page else (ext.group(1) if ext else "projects.html")
        item = {"title": title.group(1).replace("\\'", "'"), "locked": locked,
                "link": {"label": "View in detail", "href": href, "role": "link.source-url" if href.startswith("http") else "link.internal-route"}}
        if one:
            item["oneLiner"] = one.group(1).replace("\\'", "'")
        out.append(item)
    return out


def reference_example(src, classified, contracts, template_id, route):
    seq, dom = classified[route]
    blks = source_dom.blocks(dom)
    nodes = []
    for s, b in zip(seq, blks):
        c = contracts[s["section"]]
        content = fill(S.SECTIONS[s["section"]]["fields"], b, None)
        if s["section"] == "shell.header":
            content["themeToggle"] = True
        if s["section"] == "resume.header" and "contacts" in content:
            # privacy: the owner's phone number is not copied into the repo, even in reference mode
            content["contacts"] = [c_ for c_ in content["contacts"] if not re.search(r"(?<!\d)[6-9]\d{9}(?!\d)", c_.get("value", ""))]
        if s["section"] == "home.work-showcase":
            content["projects"] = data_js_projects(src)
            content["filters"] = js_values(src, "js/data.js", "label")
        trim_to_budget(content, c["content"]["fields"])
        pattern = c["motion"]["default"]
        node = {"section": s["section"], "variant": s["variant"], "content": content,
                "motion": {"pattern": pattern, "trigger": S.PATTERN_TRIGGER[pattern], "reducedMotionFallback": S.MOTION_PATTERNS[pattern][0]}}
        nodes.append(node)
    title = source_dom.find_first(dom, "title").text()
    meta = {"title": title}
    desc = next((n.attrs.get("content") for n in dom.iter() if n.tag == "meta" and n.attrs.get("name") == "description"), None)
    if desc:
        meta["description"] = desc
    overlays = []
    for oid in S.TEMPLATES[template_id]["overlays"]:
        spec = S.SECTIONS[oid]
        rel, tag, sel = spec["source"]
        if rel != route:
            continue
        ms = source_dom.select(dom, sel)
        if not ms:
            continue
        content = fill(spec["fields"], ms[0], None)
        trim_to_budget(content, contracts[oid]["content"]["fields"])
        pattern = contracts[oid]["motion"]["default"]
        overlays.append({"section": oid, "variant": spec["variants"][0], "retrievalEligible": False, "content": content,
                         "motion": {"pattern": pattern, "trigger": S.PATTERN_TRIGGER[pattern], "reducedMotionFallback": S.MOTION_PATTERNS[pattern][0]}})
    spec = {"pageSpecVersion": PAGESPEC_VERSION, "mode": "reference", "template": template_id, "route": route, "theme": "night",
            "meta": meta, "nodes": nodes}
    if overlays:
        spec["overlays"] = overlays
    return spec


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heights")
    ap.add_argument("--styles")
    ap.add_argument("--scoped")
    args = ap.parse_args()
    root = classify_routes.source_root()
    if root is None:
        raise SystemExit("build_repo.py needs the sibling site (set SOURCE_SITE_DIR)")
    src = Source(root)
    rules = classify_routes.load_rules()
    classified = {r: classify_routes.classify(root, r, rules) for r in S.ROUTES}
    for r, (seq, _) in classified.items():
        bad = [x for x in seq if x["section"] is None]
        if bad:
            raise SystemExit(f"{r}: unclassified blocks {bad}")

    mv = ingest(args.heights, args.styles, args.scoped, classified)
    budgets = compute_budgets(src, classified)

    # ---------- sections
    contracts = {}
    for sid, spec in S.SECTIONS.items():
        if spec.get("overlay"):
            rel, tag, sel = spec["source"]
            if rel.endswith(".js"):
                line = src.find(rel, "hint.className = 'desktop-hint';")
                end = src.find(rel, "setTimeout(maybeShow, 500);")
                source = {"id": "src." + sid.split(".")[1], "file": rel, "tag": "desktop-hint", "selector": "div.desktop-hint (created by script)",
                          "lines": f"{line}-{end}", "citation": f"{rel}:{line}-{end}"}
            else:
                n = source_dom.select(classified[rel][1], sel)[0]
                source = {"id": "src." + sel.strip(".").replace(".", "-"), "file": rel, "tag": n.tag, "selector": n.tag + "." + ".".join(n.classes),
                          "lines": f"{n.line}-{n.end_line}", "citation": f"{rel}:{n.line}-{n.end_line}"}
                obs = []
                for route, (seq, dom) in classified.items():
                    for m in source_dom.select(dom, sel):
                        obs.append(f"{route}:{m.line}")
                source["observedIn"] = obs
            used = [tid for tid, t in S.TEMPLATES.items() if sid in t["overlays"]]
        else:
            scopes = section_scopes(classified, sid)
            if not scopes:
                raise SystemExit(f"section {sid} never observed")
            route, s, b = scopes[0]
            source = {"id": "src." + (b.tag + "-" + "-".join(b.classes) if b.classes else b.tag), "file": route, "tag": b.tag,
                      "selector": b.tag + "".join("." + c for c in b.classes), "lines": f"{b.line}-{b.end_line}",
                      "citation": f"{route}:{b.line}-{b.end_line}", "observedIn": [f"{r}:{bb.line}" for r, _, bb in scopes]}
            used = [tid for tid, t in S.TEMPLATES.items() if any(sid in n["sections"] for n in t["nodes"])]
        fields = {}
        for k, f in spec["fields"].items():
            fields[k] = merge_budget(f, budgets[sid][k])
        c = {
            "id": sid, "title": spec["title"], "description": spec["description"], "source": source,
            "semantic": {"id": sid, "category": spec["category"]},
            "retrievalEligible": not spec.get("overlay", False),
        }
        if spec.get("overlay"):
            c["retrievalReason"] = spec["retrievalReason"]
        c.update({
            "variants": spec["variants"],
            "content": {"fields": fields},
            "constraints": {"usedByTemplates": used, **({"overlayOnly": True} if spec.get("overlay") else {})},
            "motion": {"allowedPatterns": spec["motion"], "default": spec["defaultMotion"]},
            "responsive": [{"breakpoint": bp, "query": q, "change": ch, "cite": src.media_cite(rel, needle)} for bp, q, ch, (rel, needle) in spec["responsive"]],
        })
        if spec.get("responsiveNote"):
            c["responsiveNote"] = spec["responsiveNote"]
        c.update({"assetRoles": spec["assetRoles"], "generatedAssetRoles": spec["generatedAssetRoles"],
                  "components": spec["components"], "tokens": spec["tokens"]})
        if sid in ("casestudy.summary", "casestudy.chapter-nav"):
            c["constraints"]["maxPerPage"] = 1
        if spec["category"] in ("HERO",):
            c["constraints"]["maxPerPage"] = 1
        contracts[sid] = c
    for old in glob.glob(os.path.join(REPO, "sections", "*.json")):
        os.remove(old)
    for sid, c in contracts.items():
        wjson(f"sections/{sid}.json", c)

    # ---------- primitives / components
    for d in ("primitives", "components"):
        for old in glob.glob(os.path.join(REPO, d, "*.json")):
            os.remove(old)
    for pid, p in S.PRIMITIVES.items():
        wjson(f"primitives/{pid}.json", {"id": pid, "kind": "primitive", "description": p["description"], "props": p["props"], "tokens": p["tokens"],
                                         "cites": [src.cite(r, n) for r, n in p["cites"]]})
    for cid, p in S.COMPONENTS.items():
        wjson(f"components/{cid}.json", {"id": cid, "kind": "component", "description": p["description"], "composes": p["composes"], "props": p["props"],
                                         "tokens": p["tokens"], "cites": [src.cite(r, n) for r, n in p["cites"]]})

    # ---------- allowlist (every settable property of a node, every contract id)
    wjson("tokens/llm/component-allowlist.json", {
        "version": ALLOWLIST_VERSION,
        "note": "Closed list of what a generator may set. verify_all checks parity with primitives/, components/, sections/ (no phantom entries, no orphans), with the PageSpec schema's node/motion/style properties, and that allowlistVersion in registry.manifest.json equals this version.",
        "nodeProperties": ["section", "variant", "retrievalEligible", "content", "motion", "style"],
        "motionProperties": ["pattern", "trigger", "reducedMotionFallback", "durationToken", "easingToken"],
        "styleSlots": ["surface", "text", "accent", "paddingBlock", "gap", "radius", "headingFont", "bodyFont"],
        "primitives": sorted(S.PRIMITIVES),
        "components": sorted(S.COMPONENTS),
        "sections": [{"id": sid, "variants": c["variants"], "retrievalEligible": c["retrievalEligible"],
                      "settableContentFields": sorted(c["content"]["fields"]), "allowedMotion": c["motion"]["allowedPatterns"],
                      "generatedAssetRoles": c["generatedAssetRoles"]} for sid, c in sorted(contracts.items())],
    })

    # ---------- templates + routes
    templates = {}
    for tid, t in S.TEMPLATES.items():
        nodes = []
        for n in t["nodes"]:
            nn = {"slot": n["slot"], "sections": n["sections"], "required": n["required"], "repeatable": n.get("repeatable", False)}
            if n.get("repeatable"):
                nn["minCount"], nn["maxCount"] = n["minCount"], n["maxCount"]
            if n.get("variants"):
                nn["variants"] = n["variants"]
            nodes.append(nn)
        templates[tid] = {"id": tid, "title": t["title"], "purpose": t["purpose"], "nodes": nodes, "overlays": t["overlays"],
                          "noHero": t.get("noHero", False), "routes": t["routes"]}
    title_words = max(source_dom.words(source_dom.find_first(classified[r][1], "title").text()) for r in S.ROUTES)
    desc_words = max(source_dom.words(next((n.attrs.get("content", "") for n in classified[r][1].iter() if n.tag == "meta" and n.attrs.get("name") == "description"), ""))
                     for r in S.ROUTES)
    wjson("templates/templates.json", {
        "version": REPO_VERSION,
        "note": "One template per page purpose. Nodes are explicit slots (sections allowed in the slot, required, repeatable with min/max counts, allowed variants). The real classifier (extraction/classify_routes.py) checks that every route matches exactly its assigned template.",
        "metaBudgets": {"title": {"maxWords": title_words}, "description": {"maxWords": desc_words},
                        "evidence": "max words of <title> / meta[name=description] over all 12 routes"},
        "templates": templates,
    })
    routes = []
    for tid, t in S.TEMPLATES.items():
        for r in t["routes"]:
            seq = classified[r][0]
            routes.append({"route": r, "template": tid, "classifiedSequence": [f'{s["section"]}[{s["variant"]}]' for s in seq]})
    routes.sort(key=lambda x: S.ROUTES.index(x["route"]))
    wjson("templates/routes.json", {"version": REPO_VERSION, "note": "Every route the source serves, mapped exactly once. classifiedSequence is the classifier output at build time; classify_routes.py --check re-derives it.", "routes": routes})

    # ---------- tokens
    token_files = build_tokens(src, mv)
    for rel, data in token_files.items():
        wjson(rel, data)
    catalog = flatten_catalog(token_files)
    wjson("tokens/llm/token-catalog.json", {"version": TOKENS_VERSION, "derivedFrom": sorted(k for k in token_files if "/themes/" not in k),
                                            "note": "Generated by extraction/build_repo.py from the token files; verify_all re-derives it and fails on any difference.",
                                            "count": len(catalog), "tokens": catalog})
    wjson("tokens/00-foundation/motion-patterns.json", {
        "version": TOKENS_VERSION,
        "note": "Closed set of motion patterns observed in the source; each pins its reduced-motion fallback (also pinned in schema/semantic_validate.py MOTION_FALLBACK). Global rule: every animation/transition collapses to ~0ms under prefers-reduced-motion.",
        "globalReducedMotion": [src.cite(r, n) for r, n in S.GLOBAL_REDUCED_MOTION_CITES],
        "patterns": {k: {"reducedMotionFallback": v[0], "trigger": S.PATTERN_TRIGGER[k], "description": v[2], "cites": [src.cite(r, n) for r, n in v[1]]}
                     for k, v in S.MOTION_PATTERNS.items()},
    })

    # ---------- asset roles
    roles = {}
    for group in (S.ASSET_ROLES, S.LINK_ROLES, S.COPY_ROLES):
        for rid, r in group.items():
            e = {"availability": r["availability"], "generationPolicy": r["generationPolicy"], "description": r["description"],
                 "appliesTo": "asset" if group is S.ASSET_ROLES else ("link" if group is S.LINK_ROLES else "copy"),
                 "generationSafeSubstitutes": r["subs"]}
            if group is S.ASSET_ROLES:
                e["pathPatterns"] = r["pathPatterns"]
                e["evidence"] = [src.cite(f, n) for f, n in r["evidence"]]
            roles[rid] = e
    wjson("assets/asset-roles.json", {
        "version": REPO_VERSION,
        "licensing": "The source is a real, living person's portfolio showing real employer/client product work. Generated pages must never reproduce the owner's name, wordmark, photographs, contact details or URLs, nor the employer's or clients' product screens, videos, product names or copy. Generators must not fabricate look-alikes of any of these either (blocked-for-generation). Use the generation-safe substitutes.",
        "availabilityEnum": ["reference-only", "generation-safe", "blocked-for-generation"],
        "placeholderSources": {"asset": "^(placeholder|generated|user-supplied)://", "url": "reserved domains only: *.example, *.invalid, example.com, example.org, example.net"},
        "notApplicable": {"rating.placeholder": "The source has no ratings, reviews or testimonials, so no rating role or rating field exists."},
        "roles": roles,
    })

    # ---------- schema
    wjson("schema/pagespec.schema.json", build_pagespec_schema(contracts, catalog))
    wjson("schema/section-contract.schema.json", SECTION_CONTRACT_SCHEMA)

    # ---------- measured values
    bp_hist = {}
    for p in glob.glob(os.path.join(root, "css", "*.css")):
        for m in re.findall(r"@media\s*([^{]*)\{", open(p, encoding="utf-8").read()):
            k = " ".join(m.split())
            bp_hist[k] = bp_hist.get(k, 0) + 1
    mv["breakpointHistogram"] = dict(sorted(bp_hist.items(), key=lambda kv: -kv[1])[:20])
    mv["sourceSite"] = {
        "location": "sibling of design-repo/ (the folder that contains this design-repo); citations below are relative to it",
        "stack": "hand-written static HTML + plain CSS + vanilla JS, no build step, no package.json",
        "files": {"html": len(glob.glob(os.path.join(root, "*.html"))), "css": len(glob.glob(os.path.join(root, "css", "*.css"))),
                  "js": len(glob.glob(os.path.join(root, "js", "*.js"))),
                  "cssLines": sum(len(open(p, encoding="utf-8").read().split("\n")) - 1 for p in glob.glob(os.path.join(root, "css", "*.css"))),
                  "jsLines": sum(len(open(p, encoding="utf-8").read().split("\n")) - 1 for p in glob.glob(os.path.join(root, "js", "*.js")))},
        "routes": S.ROUTES,
        "mirrorOf": "a live personal portfolio; the local copy self-hosts its two web fonts (Google Fonts @imports re-pointed to assets/fonts/*.css) and adds a local static server (serve.mjs, not part of the original).",
    }
    mv["copyBudgets"] = {sid: {k: strip_evidence(v) for k, v in b.items()} for sid, b in budgets.items()}
    mv["citations"] = collect_citations(src)
    wjson("extraction/measured-values.json", mv)

    # ---------- reference examples
    for old in glob.glob(os.path.join(REPO, "schema", "examples", "reference.*.json")):
        os.remove(old)
    for tid, route in S.REFERENCE_ROUTES.items():
        ex = reference_example(src, classified, contracts, tid, route)
        wjson(f"schema/examples/reference.{tid.split('.', 1)[1]}.json", ex)
    print("build_repo: sections=%d templates=%d tokens=%d routes=%d" % (len(contracts), len(templates), len(catalog), len(routes)))
    import update_manifest
    update_manifest.main([])


def strip_evidence(b):
    out = {k: v for k, v in b.items() if k in ("maxWords", "maxItems")}
    if "item" in b:
        out["item"] = {k: strip_evidence(v) for k, v in b["item"].items()}
    return out


def merge_budget(f, b):
    out = {"type": f["type"], "required": bool(f.get("required"))}
    if f.get("requiredForVariants"):
        out["requiredForVariants"] = f["requiredForVariants"]
    for k in ("maxWords", "maxItems"):
        if k in b:
            out[k] = b[k]
    if f.get("joinMatches"):
        out["joinMatches"] = True
    if "evidence" in b:
        out["evidence"] = b["evidence"]
    if f.get("item"):
        out["item"] = {k: merge_budget(v, b.get("item", {}).get(k, {})) for k, v in f["item"].items()}
    return out


def collect_citations(src):
    """Headline facts with path:line citations into the sibling site (verify_all re-checks each needle)."""
    facts = [
        ("Night is the default theme (inline head script)", "index.html", "sessionStorage.getItem('site-theme')!=='day'"),
        ("Day/Night switch is injected into the header by script", "js/theme.js", "btn.className = 'theme-toggle';"),
        ("Theme switch crossfade class removed after 500ms", "js/theme.js", "setTimeout(() => root.classList.remove('theme-anim'), 500);"),
        ("Desktop hint shows only below 980px", "js/main.js", "if (!window.matchMedia('(max-width: 979px)').matches) return;"),
        ("Desktop hint appears 500ms after load", "js/main.js", "setTimeout(maybeShow, 500);"),
        ("Desktop hint auto-dismisses after 10s", "js/main.js", "autoDismissTimer = setTimeout(() => dismiss(false), 10000);"),
        ("Global reduced-motion rule", "css/styles.css", "animation-duration: 0.001ms !important;"),
        ("Inter self-hosted (font import re-pointed)", "css/styles.css", "@import url('../assets/fonts/inter.css');"),
        ("Outfit self-hosted (font import re-pointed)", "css/dream-theme.css", "@import url("),
        ("Display family is Outfit", "css/dream-theme.css", "--font-display: 'Outfit', 'Inter', system-ui, sans-serif;"),
        ("Locked projects are gated client-side by a password dialog (secret intentionally not recorded)", "js/lock.js", "function openModal(href, target, title) {"),
        ("Reveal observer threshold 0.12", "js/offline-consultation.js", "}, { threshold: 0.12 });"),
        ("Scroll console tracks the step in the middle band", "js/visit-clinic-v3.js", "rootMargin: '-45% 0px -45% 0px'"),
        ("Story page loads only its own stylesheet", "offline-doctor-consultation.html", '<link rel="stylesheet" href="css/oc-story.css?v=15">'),
        ("Story page defaults to night, day via attribute", "offline-doctor-consultation.html", "if (sessionStorage.getItem('site-theme') === 'day') document.documentElement.dataset.theme = 'day';"),
        ("Home project box renders from a data file", "js/data.js", "const PROJECTS = ["),
    ]
    return [{"claim": c, "cite": src.cite(f, n), "needle": n} for c, f, n in facts]


if __name__ == "__main__":
    main()
