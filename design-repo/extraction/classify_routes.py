#!/usr/bin/env python3
"""Real route classifier: derives each route's section sequence from the sibling site's DOM.

    python3 extraction/classify_routes.py            # print every route's sequence + template matches
    python3 extraction/classify_routes.py --json     # machine output
    python3 extraction/classify_routes.py --check    # exit 1 unless every route matches exactly its
                                                     # assigned template (templates/routes.json) and
                                                     # the recorded sequence in templates/routes.json

The sibling site is found at <design-repo>/.. (or $SOURCE_SITE_DIR). When it is absent the
script says so and exits 0 with --check (graceful degradation for a design-repo-only copy).
Template matching uses schema/semantic_validate.py's own matcher, so the classifier and the
validator cannot disagree about what a template allows.
"""
import json
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "schema"))

import source_dom  # noqa: E402


def source_root():
    env = os.environ.get("SOURCE_SITE_DIR")
    cand = env if env else os.path.dirname(REPO)
    return cand if os.path.isfile(os.path.join(cand, "index.html")) else None


def load_rules():
    with open(os.path.join(HERE, "classifier-rules.json")) as f:
        return json.load(f)["rules"]


def _contains(node, pred):
    return any(pred(d) for d in node.iter())


def _rule_matches(node, m):
    if m.get("tag") and node.tag != m["tag"]:
        return False
    cls = node.classes
    if "class" in m and not all(c in cls for c in m["class"]):
        return False
    if "classExact" in m and sorted(cls) != sorted(m["classExact"]):
        return False
    if "id" in m and node.attrs.get("id") != m["id"]:
        return False
    for k, v in (m.get("attr") or {}).items():
        if node.attrs.get(k) != v:
            return False
    if "containsTag" in m and not _contains(node, lambda d: d.tag == m["containsTag"]):
        return False
    if "containsClass" in m and not _contains(node, lambda d: m["containsClass"] in d.classes):
        return False
    return True


def classify_node(node, rules):
    for r in rules:
        if _rule_matches(node, r["match"]):
            variant = r.get("variant")
            for cls, var in r.get("variantByClass", []):
                if cls in node.classes:
                    variant = var
                    break
            for attr, table in (r.get("variantByAttr") or {}).items():
                variant = table.get(node.attrs.get(attr), variant)
            return r["section"], variant or r.get("defaultVariant")
    return None, None


def parse_route(root, route):
    with open(os.path.join(root, route), encoding="utf-8") as f:
        return source_dom.parse(f.read())


def classify(root, route, rules=None):
    rules = rules or load_rules()
    dom = parse_route(root, route)
    out = []
    for b in source_dom.blocks(dom):
        sec, var = classify_node(b, rules)
        out.append({
            "section": sec, "variant": var, "tag": b.tag, "classes": b.classes,
            "id": b.attrs.get("id"), "line": b.line, "endLine": b.end_line,
        })
    return out, dom


def main(argv):
    root = source_root()
    as_json, check = "--json" in argv, "--check" in argv
    if root is None:
        print("WARN classify_routes: sibling site not present; classification skipped")
        return 0
    import semantic_validate as sv  # noqa: E402
    templates = sv.load_templates()
    with open(os.path.join(REPO, "templates", "routes.json")) as f:
        routes = json.load(f)["routes"]
    report, errors = {}, []
    for entry in routes:
        route = entry["route"]
        seq, _ = classify(root, route)
        unclassified = [s for s in seq if s["section"] is None]
        ids = [s["section"] for s in seq]
        nodes = [{"section": s["section"], "variant": s["variant"]} for s in seq]
        matches = [tid for tid, t in templates.items() if not unclassified and not sv.match_template(nodes, t)]
        report[route] = {"sequence": [f'{s["section"]}[{s["variant"]}]' for s in seq], "matches": matches}
        if unclassified:
            errors.append(f"{route}: unclassified source blocks {[(u['tag'], u['classes'], u['line']) for u in unclassified]}")
        if matches != [entry["template"]]:
            errors.append(f"{route}: classifier matches {matches}, routes.json assigns {entry['template']}")
        recorded = entry.get("classifiedSequence")
        if recorded is not None and recorded != report[route]["sequence"]:
            errors.append(f"{route}: classified sequence drifted from templates/routes.json classifiedSequence")
    if as_json:
        print(json.dumps(report, indent=1))
    else:
        for r, v in report.items():
            print(f"{r}  -> {v['matches']}")
            print("    " + " > ".join(v["sequence"]))
    if check:
        for e in errors:
            print("FAIL", e)
        print(f"classify_routes --check: {len(routes)} routes, {len(errors)} error(s)")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
