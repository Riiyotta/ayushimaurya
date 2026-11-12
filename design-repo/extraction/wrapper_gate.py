#!/usr/bin/env python3
"""Whole-page-wrapper quality gate (BASELINE R9). Called from extraction/verify_all.py.

    python3 extraction/wrapper_gate.py

Reads measured section heights (extraction/measured-values.json#sectionHeights, measured at
1440px by extraction/measure_sections.mjs), the route table, the section contracts and the
reviewed whitelist (extraction/wrapper-whitelist.json). Thresholds are pinned here, not in JSON.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VIEWPORT_WIDTH = 1440
HERO_WARN_PX = 1800
HERO_FAIL_PX = 3000
SHARE_WARN = 0.50
SHARE_FAIL = 0.60
MIN_INFLOW_SECTIONS = 3
NO_HEIGHT_POSITIONS = {"fixed", "sticky"}     # take no page height for the share rule
AGENT_ATTESTATION = "agent attestation, not a human sign-off"


def _load(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return json.load(f)


def run(root=REPO):
    errors, warnings = [], []
    mv = _load(root, "extraction/measured-values.json")
    routes = _load(root, "templates/routes.json")["routes"]
    wl = _load(root, "extraction/wrapper-whitelist.json")["entries"]
    cats = {}
    for fn in os.listdir(os.path.join(root, "sections")):
        if fn.endswith(".json"):
            c = _load(root, "sections/" + fn)
            cats[c["id"]] = c["semantic"]["category"]
    sh = mv.get("sectionHeights")
    if not sh:
        return ["MISSING_MEASUREMENT: extraction/measured-values.json has no sectionHeights"], warnings
    if sh.get("viewport", {}).get("width") != VIEWPORT_WIDTH:
        errors.append(f"WRONG_VIEWPORT: sectionHeights measured at {sh.get('viewport')}, gate requires width {VIEWPORT_WIDTH}")
    hits = {}
    for r in routes:
        route = r["route"]
        m = sh.get("routes", {}).get(route)
        if not m:
            errors.append(f"MISSING_MEASUREMENT: {route} has no measured section heights")
            continue
        blocks = m.get("blocks", [])
        measured_seq = [f'{b.get("section")}[{b.get("variant")}]' for b in blocks]
        if r.get("classifiedSequence") and measured_seq != r["classifiedSequence"]:
            errors.append(f"MEASUREMENT_STALE: {route} measured sequence differs from its classified sequence; re-measure")
        page = m.get("pageHeightPx")
        if not isinstance(page, int) or page <= 0:
            errors.append(f"MISSING_MEASUREMENT: {route} has no pageHeightPx")
            continue
        inflow = [b for b in blocks if cats.get(b.get("section")) != "SHELL" and b.get("position") not in NO_HEIGHT_POSITIONS]
        for b in blocks:
            if not isinstance(b.get("heightPx"), int):
                errors.append(f"MISSING_MEASUREMENT: {route} block {b.get('index')} ({b.get('section')}) has no heightPx")
                continue
            key = (route, b["section"], b["index"])
            h = b["heightPx"]
            if cats.get(b.get("section")) == "HERO":
                if h > HERO_FAIL_PX:
                    hits[key] = ("HERO_FAIL", h, f"HERO {b['section']} is {h}px > {HERO_FAIL_PX}px")
                elif h > HERO_WARN_PX:
                    warnings.append(f"HERO_TALL: {route} {b['section']} is {h}px > {HERO_WARN_PX}px")
            if b in inflow and len(inflow) >= MIN_INFLOW_SECTIONS:
                share = h / page
                if share > SHARE_FAIL:
                    hits[key] = ("SHARE_FAIL", h, f"{b['section']} holds {share:.1%} of {route} ({h}/{page}px) > {SHARE_FAIL:.0%}")
                elif share > SHARE_WARN:
                    warnings.append(f"SHARE_HIGH: {route} {b['section']} holds {share:.1%} of the page")
    used = set()
    for e in wl:
        key = (e.get("route"), e.get("section"), e.get("index"))
        tag = f"whitelist {key}"
        if not e.get("reviewedBy"):
            errors.append(f"WHITELIST_INVALID: {tag} has no reviewedBy")
        elif re.search(r"agent|claude|assistant|automated", e["reviewedBy"], re.I) and AGENT_ATTESTATION not in e["reviewedBy"]:
            errors.append(f"WHITELIST_INVALID: {tag} reviewedBy is an agent but does not say '{AGENT_ATTESTATION}'")
        if len(e.get("justification", "")) < 30:
            errors.append(f"WHITELIST_INVALID: {tag} justification shorter than 30 characters")
        if key not in hits:
            errors.append(f"WHITELIST_STALE: {tag} no longer matches a gate hit (remove it)")
            continue
        rule, h, msg = hits[key]
        if not isinstance(e.get("maxHeightPx"), int):
            errors.append(f"WHITELIST_INVALID: {tag} has no integer maxHeightPx")
        elif h > e["maxHeightPx"]:
            errors.append(f"WHITELIST_OVER_CAP: {tag} measured {h}px exceeds maxHeightPx {e['maxHeightPx']}")
        elif h == e["maxHeightPx"]:
            errors.append(f"WHITELIST_INVALID: {tag} maxHeightPx must be above the measured {h}px")
        if e.get("measuredHeightPx") != h:
            errors.append(f"WHITELIST_STALE: {tag} records {e.get('measuredHeightPx')}px, measured now {h}px")
        used.add(key)
        warnings.append(f"WHITELISTED ({rule}): {msg} [{e['reviewedBy']}]")
    for key, (rule, h, msg) in hits.items():
        if key not in used:
            errors.append(f"{rule}: {msg} and it is not whitelisted")
    return errors, warnings


def main():
    errors, warnings = run()
    for w in warnings:
        print("  WARN ", w)
    for e in errors:
        print("  FAIL ", e)
    print(f"wrapper_gate: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
