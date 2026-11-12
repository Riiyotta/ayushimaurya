# Changelog

## 1.0.0 (initial build)

Built from scratch (skill Situation A) against the local mirror of the portfolio site (12 static
pages). No pre-existing extraction groundwork (IA, specs, QA files) was present.

Counts (recomputed from disk by `extraction/update_manifest.py`; `verify_all` checks this block):

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

### Built
- Measurement tool, real-DOM classifier, evidence-driven builder, source-pattern harvester.
- 29 section contracts with closed `source{}` / `semantic{}` objects, measured word/item budgets,
  closed motion with pinned reduced-motion fallbacks, structured responsive rules cited at `@media` blocks.
- 6 templates (slot patterns, disjoint), 12 routes each mapped exactly once.
- Token files from resolved custom properties per theme (Night default, Day alternate), LLM token
  catalog + policy, component allowlist.
- Asset/link/copy roles with three-way availability pinned in `verify_all.py` and `semantic_validate.py`.
- Wrapper gate (thresholds pinned in code) on heights measured at 1440px for every route; one
  reviewed whitelist entry (agent attestation, pending human review).
- 6 reference examples (extracted from the real DOM) and 6 generated examples (fictional owner,
  original copy, placeholder assets, reserved-domain URLs).
- Adversarial suite (mutations + controls incl. one synthesized control per template) and
  `prove_drift.py`.

### Corrections made while building (evidence beat the first draft)
- The source has 22 stylesheets (10,852 lines) and 15 scripts (3,847 lines). An earlier
  briefing said 34 stylesheets and about 11.5k lines.
- Page heights after a full scroll pass (lazy media loaded) differ from an earlier capture for two
  routes: hybrid-diagnostic 10944px (was 9680), visit-clinic 31750px (was 31097). The new values are recorded.
- The skills strip also uses case-study videos, and the diary also uses cloud art. The validator
  rejected the first reference examples, and both roles were added to those contracts.
- The scroll-driven narratives have no heading of their own, so the field was removed rather than invented.
- The owner's phone number was dropped from the reference resume example; only a generic pattern
  is kept for the leakage rule.

### Not done (and why)
- Fresh `git clone` verification (R14): the source is not under version control.
- Live-vs-clone parity (R12): there is no separate clone; not measured.
- IR (R13): none exists; none generated.
