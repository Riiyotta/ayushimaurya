"""Minimal, dependency-free DOM for the sibling static site's HTML (standard library only).

Used by extraction/classify_routes.py (section sequence per route) and
extraction/build_repo.py (copy budgets, citations). The block-selection rule mirrors
extraction/measure_sections.mjs exactly:

  * the <header> and <footer> that are direct children of <body>;
  * inside <main>: every outermost <section> or <nav>; a <section> that contains another
    <section> is a wrapper and is descended into;
  * overlays are skipped: [hidden], role="dialog", <dialog>, <template>, <script>.

Selector support (enough for the evidence selectors in sections/*.json):
  tag, .class, tag.class.class, #id, [attr], [attr=value], descendant (space) and child (>)
  combinators, comma lists, ":self" and "<simple-selector>:self" (the scope element itself when it matches).
"""
from html.parser import HTMLParser
import re

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TEXT = {"script", "style", "svg", "template"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "line", "end_line", "text_parts")

    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.parent, self.line = tag, attrs, parent, line
        self.children, self.text_parts, self.end_line = [], [], line

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def text(self):
        if self.tag in SKIP_TEXT:
            return ""
        out = []
        for part in self.text_parts:
            out.append(part if isinstance(part, str) else part.text())
        txt = " ".join(" ".join(out).split())
        return re.sub(r"\(\s+", "(", re.sub(r"\s+([,.;:!?)’])", r"\1", txt))

    def iter(self):
        for c in self.children:
            yield c
            yield from c.iter()


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None, 1)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        parent = self.stack[-1]
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, parent, self.getpos()[0])
        parent.children.append(node)
        parent.text_parts.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        parent = self.stack[-1]
        node = Node(tag, {k: (v if v is not None else "") for k, v in attrs}, parent, self.getpos()[0])
        parent.children.append(node)
        parent.text_parts.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                for n in self.stack[i:]:
                    n.end_line = self.getpos()[0]
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].text_parts.append(data)


def parse(html_text):
    b = _Builder()
    b.feed(html_text)
    b.close()
    return b.root


def _is_overlay(n):
    return ("hidden" in n.attrs or n.attrs.get("role") == "dialog" or n.tag in ("dialog", "template", "script"))


def find_first(root, tag):
    for n in root.iter():
        if n.tag == tag:
            return n
    return None


def blocks(root):
    """In-flow semantic blocks in document order (see module docstring)."""
    body = find_first(root, "body")
    out = []
    if body is None:
        return out
    header = next((c for c in body.children if c.tag == "header"), None)
    footer = next((c for c in body.children if c.tag == "footer"), None)
    main = find_first(body, "main")
    if header is not None:
        out.append(header)

    def contains_section(n):
        return any(d.tag == "section" for d in n.iter())

    def walk(n):
        for c in n.children:
            if _is_overlay(c):
                continue
            if c.tag == "section":
                if contains_section(c):
                    walk(c)
                else:
                    out.append(c)
            elif c.tag == "nav":
                out.append(c)
            else:
                walk(c)

    if main is not None:
        walk(main)
    if footer is not None:
        out.append(footer)
    return out


_SIMPLE = re.compile(r"^(?P<tag>[a-z0-9]+)?(?P<rest>(?:[.#][A-Za-z0-9_-]+|\[[A-Za-z0-9_-]+(?:=[^\]]*)?\])*)$")


def _match_simple(n, simple):
    m = _SIMPLE.match(simple)
    if not m:
        raise ValueError("unsupported selector part: %r" % simple)
    if m.group("tag") and n.tag != m.group("tag"):
        return False
    for tok in re.findall(r"[.#][A-Za-z0-9_-]+|\[[^\]]+\]", m.group("rest")):
        if tok[0] == "." and tok[1:] not in n.classes:
            return False
        if tok[0] == "#" and n.attrs.get("id") != tok[1:]:
            return False
        if tok[0] == "[":
            name, _, val = tok[1:-1].partition("=")
            if name not in n.attrs or (val and n.attrs.get(name) != val.strip("\"'")):
                return False
    return True


def _matches_chain(n, parts, scope):
    """parts: alternating simple selectors and combinators (' ' or '>'), rightmost last."""
    if not _match_simple(n, parts[-1]):
        return False
    i, cur = len(parts) - 2, n
    while i >= 0:
        comb, sel = parts[i], parts[i - 1]
        if comb == ">":
            cur = cur.parent
            if cur is None or cur is scope.parent or not _match_simple(cur, sel):
                return False
        else:
            cur = cur.parent
            while cur is not None and cur is not scope.parent and not _match_simple(cur, sel):
                cur = cur.parent
            if cur is None or cur is scope.parent:
                return False
        i -= 2
    return True


def select(scope, selector):
    """Matching descendants of scope in document order. ':self' / 'tag:self' return [scope]."""
    results = []
    for group in [g.strip() for g in selector.split(",") if g.strip()]:
        if group.endswith(":self"):
            t = group[: -len(":self")]
            if not t or _match_simple(scope, t):
                results.append(scope)
            continue
        toks = group.replace(">", " > ").split()
        parts = []
        for t in toks:
            if t == ">":
                parts.append(">")
            else:
                if parts and parts[-1] != ">":
                    parts.append(" ")
                parts.append(t)
        for n in scope.iter():
            if n not in results and _matches_chain(n, parts, scope):
                results.append(n)
    order = {id(n): i for i, n in enumerate([scope] + list(scope.iter()))}
    return sorted(results, key=lambda n: order.get(id(n), 0))


def words(text):
    return len([w for w in re.split(r"\s+", text.strip()) if re.search(r"[A-Za-z0-9₹%→←↗]", w)])
