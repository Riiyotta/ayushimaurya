# Design-repo: personal product-design portfolio

An AI-ready design system extracted from a static personal portfolio (12 pages: home, project
index, resume, NDA notice and 8 case studies). A generator composes **PageSpecs** from this
repo's templates, section contracts and tokens; `schema/semantic_validate.py` decides whether a
PageSpec is acceptable.

**Status:** `design-review-pending`, `productionApproved: false`. Category `portfolio`, bound to
the generic `n0-design-constraints-common` 0.1.0 policy with a local extension
(`policy/design-policy.json`); approval `defined-pending-architecture-review`, no architecture
decision recorded. Nothing here has been signed off by a person.

**Sensitivity.** The source is a real, living person's portfolio showing real employer and
client product work. `mode: "generated"` PageSpecs may not contain the owner's name, contact
details, URLs, wordmark or photographs, the employer's or clients' names, product names, screens,
videos or copy (rules `GENERATED_MODE_*`, patterns harvested into `policy/source-brand.json`;
copy is stored only as fingerprints). The locked-project password of the source is never
recorded: `utility.lock-modal` describes the gate mechanism only, and `verify_all` checks that the
secret (read at runtime from the source) appears in no repo file.

## Counts

<!-- counts:start (written by extraction/update_manifest.py from disk; verify_all checks it) -->

| count | what |
|---:|---|
| 178 | tokens in the LLM catalog |
| 15 | token files (foundation, semantic, component, layout, themes) |
| 11 | primitives |
| 8 | components |
| 29 | section contracts |
| 6 | of which runtime UI (retrievalEligible: false) |
| 6 | templates |
| 12 | routes (each mapped exactly once) |
| 19 | asset/link/copy roles |
| 14 | motion patterns |
| 10 | compatibility rules |
| 12 | example PageSpecs |
| 6 | of which reference |
| 6 | of which generated |
| 98 | adversarial cases (mutations + controls) |
| 31 | drift cases |

<!-- counts:end -->

## Layout

```
registry.manifest.json      status, versions, counts (recomputed), entry points, policy binding + contentHash
tokens/00-foundation/       color (theme-bound palette), typography, spacing, radius, motion, breakpoint, elevation, motion-patterns
tokens/10-semantic/         semantic colour roles -> palette references per theme
tokens/20-component/        cta sizing, story-page scope, case-study scope (per theme)
tokens/30-layout/           container, measure, nav height, story wrap
tokens/themes/              night.json (default), day.json
tokens/llm/                 token-catalog.json (generated), token-policy.json, component-allowlist.json (generated)
primitives/ components/     11 primitives, 8 components, each cited at a real source line
sections/                   29 section contracts: source{} provenance + semantic{} taxonomy, budgets, motion, responsive
templates/                  templates.json (6 templates, slot patterns), routes.json (12 routes + classifier sequences)
compatibility/graph.json    10 rhythm/position rules (error|warn), each implemented in the validator
assets/asset-roles.json     19 closed roles with three-way availability (pinned in code), substitutes, licensing
policy/                     design-policy.json (category, rules, approval), source-brand.json (harvested patterns)
schema/                     pagespec.schema.json, section-contract.schema.json, semantic_validate.py, examples/, tests/
extraction/                 measured-values.json, classifier, builder, harvester, wrapper gate, verify_all, prove_drift
```

## How it was built (evidence, not guesses)

* **Measured** with `extraction/measure_sections.mjs` (headless Chromium, any Playwright install via
  `PLAYWRIGHT_MODULE`; site served over HTTP via `SITE_BASE_URL`): in-flow block heights per route at
  1440x900 (plus page heights at 768 and 390), computed-style histograms for both themes, and the
  resolved custom properties of `:root`, the case-study scope and the about-me scope, per theme.
  Results live in `extraction/measured-values.json` (numbers only, no copy).
* **Classified** with `extraction/classify_routes.py`, which parses every page and maps each in-flow
  block (`header`, `footer`, outermost `section`/`nav` in `main`; wrapper sections are descended
  into) through `extraction/classifier-rules.json`. Its block lists match the browser measurement
  one-for-one on all 12 routes.
* **Built** with `extraction/build_repo.py` from `extraction/build_spec.py`: every content field has an
  evidence selector; `maxWords` / `maxItems` are the maxima measured across every real instance of
  that section (verify_all re-derives them). Citations are found by needle in the real files, never
  typed as line numbers. Reference examples are extracted from the real DOM.
* **Harvested** with `extraction/harvest_source_patterns.py`: person / brand / product / URL patterns and
  sha256 fingerprints of every source text segment and 6-word shingle.

## Templates and routes (classifier output)

| template | routes | real section sequences |
|---|---|---|
| `template.home` | index.html | header, home.hero, work-showcase, featured-project, skills-index, about.intro, about.diary, about.closing, footer |
| `template.project-index` | projects.html | header, index.page-header, index.project-grid, conversion.closing[link-row], footer |
| `template.resume` | resume.html | header, resume.header, resume.entry-group x5 (summary, experience, skills, education, certifications), conversion.closing[cta-band], footer |
| `template.notice` | nda.html | header, notice.protected-work, footer (no hero) |
| `template.case-study-brief` | claim-approval, virtual-wardrobe, wallet-ui, visit-clinic-gift-cards | header, casestudy.hero[stage or cover], (summary[brief-grid]), 1-2 of chapter / screen-gallery, closing, footer |
| `template.case-study-chaptered` | hybrid-diagnostic, visit-clinic, family-ahc, offline-doctor-consultation | header, casestudy.hero[split-media, journey or poster], prelude (summary / storyboard), (chapter-nav), 3+ of chapter / problem-statement / decision / scroll-narrative, closing, footer |

`templates/routes.json` records each route's full classified sequence; `classify_routes.py --check`
re-derives it and requires every route to match **exactly** its own template (the brief and
chaptered templates are disjoint: 1-2 body sections vs 3+).

### Judgement calls

* **Case studies are one family, two templates.** Three different implementations (the `cs2` layout,
  the `v3` layout and the self-contained story page with its own stylesheet) serve one purpose and
  normalise to the same section types. The classifier shows two shapes: brief/gated studies with
  1-2 content sections (5-6 blocks per page), and long-form studies with 7-20 chapter-level
  sections. Grouping by purpose and depth instead of by wrapper class gives two disjoint templates.
* **Long-form studies are decomposed** into hero / summary / chapter-nav / chapter (plain, tint,
  dark) / problem-statement / decision (single or list) / scroll-narrative (console, panels,
  stepper) / closing. No section holds a whole case study (largest share: the console narrative,
  24.4% of family-ahc; the decisions list, 29.5% of the story page).
* **HERO = page opener only:** home.hero, index.page-header, resume.header, casestudy.hero. The NDA
  page is one compact notice (no hero; 1 in-flow section, so the share rule does not apply).
* **The about-me band** (`section.lw`) is a wrapper around three sections and is descended into, so it is not a section itself.
* **Runtime UI** (mobile menu, password dialog, timed desktop hint, lightboxes and project sheet,
  dreams overlay, reading-progress bar) are overlay-only contracts with `retrievalEligible: false`.
* **Whitelist (R9):** `projects.html` / `index.project-grid` holds 62.4% of the page (2690 of 4313px
  at 1440px). It is one uniform card grid that is already separated from the header and the closing;
  whitelisted with `maxHeightPx` 2900 by an agent attestation (not a human sign-off), status
  pending human review. No HERO exceeds 1800px (tallest: 1407px, wallet-ui).
* **No ratings/reviews** exist in the source, so no rating role or rating rule exists (documented in
  `assets/asset-roles.json#notApplicable`).
* **Theme:** Night is the default (inline head script); Day is the alternate. Palette tokens are
  theme-bound (`palette.night.*`, `palette.day.*`); semantic `color.*` tokens resolve per theme.
* **Fonts:** exactly two families are rendered (Outfit display, Inter text), matching the measured
  histogram; the script-style signature is an image (`brand.wordmark-logo`, blocked for generation).

## Verify

```bash
python3 extraction/verify_all.py                  # all cross-file checks (degrades to WARN without the sibling site)
python3 schema/semantic_validate.py schema/examples/*.json
python3 schema/tests/adversarial_test.py           # every mutation rejected, every control passes
python3 extraction/prove_drift.py                  # every injected drift makes verify_all fail
python3 extraction/wrapper_gate.py
python3 extraction/classify_routes.py --check      # needs the sibling site
```

Requirements: Python 3.9+ and `jsonschema` (`pip install jsonschema`). Re-measuring needs Node 18+
and Playwright with Chromium (`SITE_BASE_URL=http://127.0.0.1:8090/ PLAYWRIGHT_MODULE=<dir> node
extraction/measure_sections.mjs heights`). After any source change: re-measure, run
`python3 extraction/build_repo.py --heights ... --styles ... --scoped ...`, then
`python3 extraction/harvest_source_patterns.py`, then the checks above (BASELINE R16).

### Version fields

`allowlistVersion` and `pageSpecVersion` are machine-checked by `verify_all`; `repositoryVersion`
is documentation-only.

## Known limits (stated plainly)

* **Fresh-clone verification (R14) was not run:** the source project is not under version control,
  so there is no commit to clone. The design-repo-alone run in an empty temp directory was done
  instead. `.gitignore` is provided for when it is committed.
* **Parity (R12) was not measured:** there is no separate clone or rebuild to compare with the live
  site. The evidence source is the local mirror itself, and no live-site capture was taken.
* **No IR** exists and none was generated (R13).
* `sectionHeights` are measured at 1440px only (as the gate requires). Page heights at 768 and 390
  are recorded, and responsive behaviour is captured per section from the real `@media` rules.
* The project-box cards on the home page are rendered by script from a data file. Their budgets come
  from that file (`js/data.js`), not from DOM measurement.
