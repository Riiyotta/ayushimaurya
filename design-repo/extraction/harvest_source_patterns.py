#!/usr/bin/env python3
"""Harvest the source's identity patterns and copy fingerprints into policy/source-brand.json.

    python3 extraction/harvest_source_patterns.py            # write policy/source-brand.json
    python3 extraction/harvest_source_patterns.py --check    # exit 1 if the committed file differs

Everything is derived from the real sibling site, never typed in by hand:
  person   name tokens of the footer owner name (index.html .footer-name) and every "Dr. First Last"
           found in the pages
  contact  a generic 10-digit mobile-number pattern, only if such a number appears on the resume
           (the number itself is NOT stored)
  brand    employer names (resume .decision-row-value "Employer — description" entries)
  product  case-study names (page <title> before " — ", split on " · ", for routes assigned to a
           case-study template), the featured side project title, data-file codenames
  url      every external host linked from the pages (font/W3C infrastructure excluded)
  copy     sha256 fingerprints (12 hex) of every normalized text segment of 3+ words and of every
           6-word shingle; CTA fingerprints of link/button labels of 3+ words. The copy itself is
           not stored, so the repo does not carry the source's text.
Normalization and fingerprinting are imported from schema/semantic_validate.py (one implementation).
"""
import glob
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "schema"))
import classify_routes  # noqa: E402
import source_dom  # noqa: E402
from semantic_validate import fp, normalize  # noqa: E402

TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "p", "li", "a", "button", "figcaption", "dt", "dd", "span", "small", "b", "strong",
             "em", "label", "title", "blockquote", "td", "th", "div", "h6", "summary", "q", "mark", "i"}
SHINGLE = 6
INFRA_HOSTS = re.compile(r"(^|\.)(w3\.org|googleapis\.com|gstatic\.com)$")


def words_pattern(text):
    toks = [re.escape(t) for t in normalize(text).split()]
    return r"\b" + r"\W+".join(toks) + r"\b"


def harvest(root):
    routes = json.load(open(os.path.join(REPO, "templates", "routes.json")))["routes"]
    doms = {r["route"]: classify_routes.parse_route(root, r["route"]) for r in routes}
    ev = {}

    def cite(rel, needle):
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if needle in line:
                    return f"{rel}:{i}"
        raise SystemExit(f"needle not found {rel}: {needle!r}")

    # person
    owner = source_dom.select(doms["index.html"], ".footer-name")[0].text()
    person = []
    for tok in owner.split():
        if len(tok) >= 4:
            person.append(re.escape(tok.lower()))
            ev[re.escape(tok.lower())] = cite("index.html", 'class="footer-name"')
    docs = set()
    for r, d in doms.items():
        for n in d.iter():
            for v in [n.attrs.get("alt", ""), n.attrs.get("aria-label", "")] + [p for p in n.text_parts if isinstance(p, str)]:
                for m in re.finditer(r"Dr\.\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)", v):
                    docs.add((m.group(1), m.group(2), r))
    for a, b, r in sorted(docs):
        pat = re.escape(a.lower()) + r"\s+" + re.escape(b.lower())
        person.append(pat)
        ev[pat] = cite(r, f"Dr. {a} {b}")

    # contact (pattern only, never the value)
    contact = []
    resume_text = doms["resume.html"].text() if "resume.html" in doms else ""
    if re.search(r"(?<!\d)[6-9]\d{9}(?!\d)", resume_text):
        contact.append(r"(?<!\d)[6-9]\d{9}(?!\d)")
        ev[contact[-1]] = "resume.html (a 10-digit mobile number in the contact grid; value deliberately not stored)"

    # brand: employers
    brand = []
    for n in source_dom.select(doms["resume.html"], ".decision-row-value"):
        t = n.text()
        if " — " in t:
            emp = t.split(" — ")[0].strip()
            pat = words_pattern(emp)
            if pat not in brand:
                brand.append(pat)
                ev[pat] = cite("resume.html", emp.replace("&", "&amp;") if "&" in emp else emp)

    # product names
    product = []
    case_routes = [r["route"] for r in routes if r["template"].startswith("template.case-study")]
    for r in case_routes:
        title = source_dom.find_first(doms[r], "title").text()
        left = title.split(" — ")[0]
        for part in left.split(" · "):
            part = re.sub(r"\s+Case Study$", "", part).strip()
            pat = words_pattern(part)
            if pat not in product:
                product.append(pat)
                ev[pat] = cite(r, "<title>")
    for n in source_dom.select(doms["index.html"], ".ai-body h3"):
        pat = words_pattern(n.text())
        product.append(pat)
        ev[pat] = cite("index.html", n.text())
    data_js = open(os.path.join(root, "js", "data.js"), encoding="utf-8").read()
    for m in re.finditer(r"codename:\s*'([^']+)'", data_js):
        pat = words_pattern(m.group(1))
        product.append(pat)
        ev[pat] = cite("js/data.js", m.group(0))

    # url hosts
    url = []
    for r, d in doms.items():
        for n in d.iter():
            href = n.attrs.get("href", "") if n.tag == "a" else ""
            m = re.match(r"^https?://([^/]+)", href)
            if not m:
                continue
            host = m.group(1).lower()
            host = host[4:] if host.startswith("www.") else host
            if INFRA_HOSTS.search(host):
                continue
            pat = re.escape(host)
            if pat not in url:
                url.append(pat)
                ev[pat] = cite(r, m.group(0))

    # copy fingerprints
    segments = []
    for r, d in doms.items():
        for n in d.iter():
            if n.tag in TEXT_TAGS:
                segments.append(n.text())
            for a in ("alt", "aria-label", "content", "title", "data-proj", "data-name", "data-cap", "data-mood", "placeholder"):
                if n.attrs.get(a):
                    segments.append(n.attrs[a])
    for js in sorted(glob.glob(os.path.join(root, "js", "*.js"))):
        txt = open(js, encoding="utf-8").read()
        for m in re.finditer(r"'((?:[^'\\\n]|\\.){12,})'|\"((?:[^\"\\\n]|\\.){12,})\"|`([^`]{12,})`", txt):
            s = m.group(1) or m.group(2) or m.group(3) or ""
            s = re.sub(r"<[^>]+>", " ", s)
            if " " in s and not s.startswith("[ADD"):
                segments.append(s.replace("\\'", "'"))
    full, shingles = set(), set()
    for s in segments:
        ws = normalize(s).split()
        if len(ws) >= 3:
            full.add(fp(" ".join(ws)))
        for j in range(len(ws) - SHINGLE + 1):
            shingles.add(fp(" ".join(ws[j:j + SHINGLE])))
    cta = set()
    for r, d in doms.items():
        for n in d.iter():
            if n.tag in ("a", "button"):
                ws = normalize(n.text()).split()
                if len(ws) >= 3:
                    cta.add(fp(" ".join(ws)))
    return {
        "version": "1.0.0",
        "note": "Generated by extraction/harvest_source_patterns.py from the real source; do not edit by hand. Regexes are case-insensitive. Copy is stored only as fingerprints.",
        "sourceBrand": {
            "patterns": {"person": person, "contact": contact, "brand": brand, "product": product, "url": url},
            "evidence": ev,
            "copyFingerprints": {"algorithm": "sha256(normalize(text)) first 12 hex; normalize = schema/semantic_validate.py normalize()",
                                 "shingleSize": SHINGLE, "segmentsScanned": len(segments),
                                 "fullSegments": sorted(full), "shingles": sorted(shingles)},
            "ctaFingerprints": {"minWords": 3, "labels": sorted(cta)},
        },
    }


def main(argv):
    root = classify_routes.source_root()
    if root is None:
        print("WARN harvest_source_patterns: sibling site not present; skipped")
        return 0
    data = harvest(root)
    path = os.path.join(REPO, "policy", "source-brand.json")
    if "--check" in argv:
        cur = json.load(open(path, encoding="utf-8"))
        if cur != data:
            print("FAIL policy/source-brand.json differs from a fresh harvest of the source")
            return 1
        print("PASS policy/source-brand.json matches a fresh harvest")
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    p = data["sourceBrand"]
    print("harvested: person=%d contact=%d brand=%d product=%d url=%d fullSegments=%d shingles=%d cta=%d" % (
        len(p["patterns"]["person"]), len(p["patterns"]["contact"]), len(p["patterns"]["brand"]), len(p["patterns"]["product"]),
        len(p["patterns"]["url"]), len(p["copyFingerprints"]["fullSegments"]), len(p["copyFingerprints"]["shingles"]), len(p["ctaFingerprints"]["labels"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
