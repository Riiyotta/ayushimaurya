# Ayushi Maurya portfolio — local mirror + information architecture

This folder is a static mirror of https://ayushimaurya.vercel.app (12 HTML pages, CSS, JS and assets) plus an
information architecture (IA) describing its pages and sections.

## Files

| file | edit? | what it is |
|---|---|---|
| `ia.json` | **hand-edit this** | Source of truth: categories, every section defined once, 9 templates with their ordered section ids and routes. |
| `IA.md` | generated — don't edit | Readable IA: site shape, chrome split, sections by reuse, per-template tables, section reference. |
| `matrix.csv` | generated — don't edit | Section × template matrix for a spreadsheet. |
| `validate.mjs` / `build.mjs` | copied as-is | Generic IA validator and generator, driven only by `ia.json`. |
| `serve.mjs` | — | Local static server with HTTP Range support (needed for the videos). |
| `design-repo/` | — | Separate design-repo build (tokens, contracts, validators); see its own README. |

## Run

```bash
node serve.mjs 8090                  # site at http://127.0.0.1:8090/index.html
node validate.mjs && node build.mjs  # after any edit to ia.json
```

## What the data shows

- **Case studies are most of the site, and every one is close to bespoke.** 8 of the 12 routes are case studies, spread
  across 5 templates with 5 different cover sections. Only the 3 short case studies share one template.
  7 of the 9 templates serve a single route.
- **Only 10 of the 54 sections are shared; 44 are page-local.** The shared ones are the 4 chrome pieces (skip link,
  header, mobile menu, footer), the image lightbox, the lock modal, the two-link page pager, and three chapter
  pieces (chapter, chapter nav, chapter-style "Get in touch" close).
- **Some sections are shared in purpose but not in code.** The image lightbox has three separate implementations
  (`#cs2-lightbox`, `dialog#vx-lightbox`, `.zoom`), and the chapter nav has two (`nav.cs2-nav`, `nav.v3-nav`). They
  are the clearest candidates to consolidate into one component.
- **One route uses its own page chrome.** The scrollytelling case study (`offline-doctor-consultation.html`) has its
  own fixed bar with a reading-progress line and a one-line footer. The other 11 routes share the site header and footer.

The home page also carries five hidden overlays (project box, lock modal, photo-booth viewer, dreams modal, and a
mobile-only "open on desktop" hint). They are listed in `ia.json` under `OVERLAY` so they are not mistaken for
in-flow content.

How the IA was measured: section order comes from the rendered DOM of each page at 1440×900 in headless Chromium,
taken from the direct children of `<body>` and `<main>`, and one level deeper for large wrappers. Descriptions
were checked against the HTML source.
