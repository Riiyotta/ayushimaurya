# https://ayushimaurya.vercel.app (personal product-design portfolio)

Source: https://ayushimaurya.vercel.app (personal product-design portfolio) · Local static mirror at this folder, served by serve.mjs; byte-identical HTML to the live site except self-hosted Google Fonts.
Status: **measured-from-mirror** · production approved: **false**
12 routes · 9 templates · 54 unique sections

> Generated from `ia.json` by `build.mjs`. Edit the JSON, not this file.

## Shape of the site

The largest 3 templates (Case study — short (cover + one chapter), Case study — long-form with scroll console, Home) account for 6 of 12 routes (50%). The remaining 6 routes span 6 templates.

| template | routes | share |
|---|---:|---:|
| Case study — short (cover + one chapter) | 3 | 25% |
| Case study — long-form with scroll console | 2 | 17% |
| Home | 1 | 8% |
| Work index | 1 | 8% |
| Resume | 1 | 8% |
| NDA notice | 1 | 8% |
| Case study — chaptered | 1 | 8% |
| Case study — scrollytelling | 1 | 8% |
| Case study — screen gallery | 1 | 8% |

## Page chrome

**11 routes carry chrome = `site`** — Home, Work index, Resume, NDA notice, Case study — short (cover + one chapter), Case study — chaptered, Case study — long-form with scroll console, Case study — screen gallery.

**1 routes carry chrome = `story`** — Case study — scrollytelling.

## Sections by reuse

How widely a section is shared determines whether it belongs in a shared
component library or stays local to its page.

| section | category | templates | routes | implementation | scope |
|---|---|---:|---:|---|---|
| `chrome.skip-link` | CHROME | 9 | 12 | `a.skip-link (a.skip on the story template)` | All 12 routes. |
| `chrome.site-header` | CHROME | 8 | 11 | `header.site-header · js/theme.js (Day/Night toggle), js/main.js (menu)` | 11 routes: every template except the scrollytelling case study. |
| `chrome.mobile-menu` | CHROME | 8 | 11 | `div#mobile-menu.mobile-menu` | 11 routes, paired with chrome.site-header. |
| `chrome.site-footer` | CHROME | 8 | 11 | `footer.site-footer.container` | 11 routes, paired with chrome.site-header. |
| `case.chapter` | CASE | 2 | 4 | `section.cs2-ch (.tint variant)` | 4 routes: one chapter on each short case study, seven on the chaptered one. |
| `cta.case-end` | CTA | 2 | 4 | `section.cs2-end` | 4 routes: the short and chaptered case studies. |
| `overlay.image-lightbox` | OVERLAY | 3 | 3 | `div#cs2-lightbox / dialog#vx-lightbox / div.zoom` | 3 routes: the chaptered, gallery and scrollytelling case studies. |
| `case.chapter-nav` | CASE | 2 | 3 | `nav.cs2-nav / nav.v3-nav[data-chapter-nav]` | 3 routes: the chaptered and long-form case studies. |
| `hero.case-cover-short` | HERO | 1 | 3 | `section.cs2-hero.short` | 3 routes: the short case studies. |
| `overlay.lock-modal` | OVERLAY | 2 | 2 | `div#lock-modal.lock-modal · js/lock.js` | 2 routes: home and the work index. |
| `cta.page-nav-footer` | CTA | 2 | 2 | `div.cs-nav-footer` | 2 routes: the work index and the gallery case study. |
| `hero.case-cover-longform` | HERO | 1 | 2 | `section.v3-hero.v3-wrap#top` | 2 routes: the long-form case studies. |
| `case.tldr` | CASE | 1 | 2 | `section.v3-tldr#summary` | 2 routes: the long-form case studies. |
| `case.longform-chapter` | CASE | 1 | 2 | `main > div#<chapter> > section.v3-section (.v3-wrap/.v3-tint/.v3-dark)` | 2 routes: the long-form case studies (six chapter groups each). |
| `case.scroll-console` | CASE | 1 | 2 | `section.v3-console-section[data-console] · js/visit-clinic-v3.js, js/family-ahc.js` | 2 routes: the long-form case studies, inside one chapter group. |
| `cta.longform-final` | CTA | 1 | 2 | `section.v3-final` | 2 routes: the long-form case studies. |
| `chrome.story-bar` | CHROME | 1 | 1 | `header.bar + div.bar-progress · js/oc-story.js` | 1 route: the scrollytelling case study. |
| `chrome.story-footer` | CHROME | 1 | 1 | `footer.foot` | 1 route: the scrollytelling case study. |
| `overlay.project-box-overlay` | OVERLAY | 1 | 1 | `div#pbox-overlay.pbx-overlay · js/home-box.js` | 1 route: home. |
| `overlay.desktop-hint` | OVERLAY | 1 | 1 | `js/main.js (creates div.desktop-hint)` | 1 route: home. |
| `overlay.booth-viewer` | OVERLAY | 1 | 1 | `div#lw-booth-view.lw-booth-view · js/little-world.js` | 1 route: home. |
| `overlay.dreams-modal` | OVERLAY | 1 | 1 | `div#dreams.lw-dreams.lw-dreams-modal · js/little-world.js` | 1 route: home. |
| `hero.home-intro` | HERO | 1 | 1 | `section.hero.container · js/hero.js` | 1 route: home. |
| `hero.work-index-head` | HERO | 1 | 1 | `section.mw-head` | 1 route: the work index. |
| `hero.resume-head` | HERO | 1 | 1 | `resume.html > first section.section.container` | 1 route: the resume. |
| `hero.nda-heading` | HERO | 1 | 1 | `section.nda > a.cs-back, h1.nda-title, div.nda-body` | 1 route: the NDA notice. |
| `hero.case-cover-chaptered` | HERO | 1 | 1 | `section.cs2-hero` | 1 route: the chaptered case study. |
| `hero.story-cover` | HERO | 1 | 1 | `section.hero (offline-doctor-consultation.html)` | 1 route: the scrollytelling case study. |
| `hero.campaign-cover` | HERO | 1 | 1 | `section.vx-hero` | 1 route: the gallery case study. |
| `work.home-work-head` | WORK | 1 | 1 | `#work > div.pbx-head + div#filter-bar` | 1 route: home. |
| `work.project-box` | WORK | 1 | 1 | `div#pbox.pbx + div.pbx-dots + div.pbx-more + div#pbox-index · js/home-box.js, js/data.js` | 1 route: home. |
| `work.ai-playground` | WORK | 1 | 1 | `section#ai.ai` | 1 route: home. |
| `work.project-card-stack` | WORK | 1 | 1 | `section.mw-stack > a.mw-card` | 1 route: the work index. |
| `about.skills-list` | ABOUT | 1 | 1 | `section#skills.sk · js/skills.js` | 1 route: home. |
| `about.little-world-intro` | ABOUT | 1 | 1 | `section#lw-intro.lw-hero · js/little-world.js` | 1 route: home. |
| `about.diary` | ABOUT | 1 | 1 | `section#lw-diary.dy-stage · js/diary.js` | 1 route: home. |
| `about.to-be-continued` | ABOUT | 1 | 1 | `section#lw-ch5.lw-end` | 1 route: home. |
| `about.resume-summary` | ABOUT | 1 | 1 | `section.cs-section[aria-labelledby=summary-heading]` | 1 route: the resume. |
| `about.resume-experience` | ABOUT | 1 | 1 | `section.cs-section[aria-labelledby=experience-heading]` | 1 route: the resume. |
| `about.resume-skills` | ABOUT | 1 | 1 | `section.cs-section[aria-labelledby=skills-heading]` | 1 route: the resume. |
| `about.resume-education` | ABOUT | 1 | 1 | `section.cs-section[aria-labelledby=education-heading]` | 1 route: the resume. |
| `about.resume-certifications` | ABOUT | 1 | 1 | `section.cs-section[aria-labelledby=certifications-heading]` | 1 route: the resume. |
| `case.nda-redacted-art` | CASE | 1 | 1 | `section.nda > figure.nda-art` | 1 route: the NDA notice. |
| `case.story-panels` | CASE | 1 | 1 | `section.story[data-story] + p.story-end · js/oc-story.js` | 1 route: the scrollytelling case study. |
| `case.project-file` | CASE | 1 | 1 | `section.file.wrap` | 1 route: the scrollytelling case study. |
| `case.story-section` | CASE | 1 | 1 | `section.sec` | 1 route: the scrollytelling case study (seven instances). |
| `case.network-fork` | CASE | 1 | 1 | `section.fork[data-fork] + div.after-fork · js/oc-story.js` | 1 route: the scrollytelling case study. |
| `case.decision-cards` | CASE | 1 | 1 | `section.sec#decisions > article.ds` | 1 route: the scrollytelling case study. |
| `case.campaign-brief` | CASE | 1 | 1 | `section.vx-brief` | 1 route: the gallery case study. |
| `case.screen-gallery` | CASE | 1 | 1 | `visit-clinic-gift-cards.html > main > section:nth-child(3)` | 1 route: the gallery case study. |
| `cta.nda-walkthrough-ask` | CTA | 1 | 1 | `section.nda > div.nda-ask + div.nda-cta` | 1 route: the NDA notice. |
| `cta.story-end` | CTA | 1 | 1 | `section.end.wrap` | 1 route: the scrollytelling case study. |
| `cta.closing-line` | CTA | 1 | 1 | `section.oc-closing > p.oc-closing-line` | 1 route: the work index. |
| `cta.resume-cta` | CTA | 1 | 1 | `resume.html > last section.section.container` | 1 route: the resume. |

**10 shared sections** appear in more than one template and belong in a component library.

**44 single-use sections** appear in exactly one template. Building these
as "reusable" components up front would be speculative — keep them page-local
until a second caller actually appears.

## Templates

### Home — `template.home`

1 route · `/index.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.home-intro` | page-local |
| 5 | WORK | `work.home-work-head` | page-local |
| 6 | WORK | `work.project-box` | page-local |
| 7 | WORK | `work.ai-playground` | page-local |
| 8 | ABOUT | `about.skills-list` | page-local |
| 9 | ABOUT | `about.little-world-intro` | page-local |
| 10 | ABOUT | `about.diary` | page-local |
| 11 | ABOUT | `about.to-be-continued` | page-local |
| 12 | CHROME | `chrome.site-footer` | shared ×8 |
| 13 | OVERLAY | `overlay.project-box-overlay` | page-local |
| 14 | OVERLAY | `overlay.lock-modal` | shared ×2 |
| 15 | OVERLAY | `overlay.booth-viewer` | page-local |
| 16 | OVERLAY | `overlay.dreams-modal` | page-local |
| 17 | OVERLAY | `overlay.desktop-hint` | page-local |

### Work index — `template.work-index`

1 route · `/projects.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.work-index-head` | page-local |
| 5 | WORK | `work.project-card-stack` | page-local |
| 6 | CTA | `cta.closing-line` | page-local |
| 7 | CTA | `cta.page-nav-footer` | shared ×2 |
| 8 | OVERLAY | `overlay.lock-modal` | shared ×2 |
| 9 | CHROME | `chrome.site-footer` | shared ×8 |

### Resume — `template.resume`

1 route · `/resume.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.resume-head` | page-local |
| 5 | ABOUT | `about.resume-summary` | page-local |
| 6 | ABOUT | `about.resume-experience` | page-local |
| 7 | ABOUT | `about.resume-skills` | page-local |
| 8 | ABOUT | `about.resume-education` | page-local |
| 9 | ABOUT | `about.resume-certifications` | page-local |
| 10 | CTA | `cta.resume-cta` | page-local |
| 11 | CHROME | `chrome.site-footer` | shared ×8 |

### NDA notice — `template.nda-notice`

1 route · `/nda.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.nda-heading` | page-local |
| 5 | CASE | `case.nda-redacted-art` | page-local |
| 6 | CTA | `cta.nda-walkthrough-ask` | page-local |
| 7 | CHROME | `chrome.site-footer` | shared ×8 |

### Case study — short (cover + one chapter) — `template.case-study-short`

3 routes · `/claim-approval.html`, `/virtual-wardrobe.html`, `/wallet-ui.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.case-cover-short` | page-local |
| 5 | CASE | `case.chapter` | shared ×2 |
| 6 | CTA | `cta.case-end` | shared ×2 |
| 7 | CHROME | `chrome.site-footer` | shared ×8 |

### Case study — chaptered — `template.case-study-chaptered`

1 route · `/hybrid-diagnostic.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.case-cover-chaptered` | page-local |
| 5 | CASE | `case.chapter-nav` | shared ×2 |
| 6 | CASE | `case.chapter` | shared ×2 |
| 7 | CTA | `cta.case-end` | shared ×2 |
| 8 | OVERLAY | `overlay.image-lightbox` | shared ×3 |
| 9 | CHROME | `chrome.site-footer` | shared ×8 |

### Case study — long-form with scroll console — `template.case-study-longform`

2 routes · `/visit-clinic.html`, `/family-ahc.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.case-cover-longform` | page-local |
| 5 | CASE | `case.tldr` | page-local |
| 6 | CASE | `case.chapter-nav` | shared ×2 |
| 7 | CASE | `case.longform-chapter` | page-local |
| 8 | CASE | `case.scroll-console` | page-local |
| 9 | CTA | `cta.longform-final` | page-local |
| 10 | CHROME | `chrome.site-footer` | shared ×8 |

### Case study — scrollytelling — `template.case-study-scrollytelling`

1 route · `/offline-doctor-consultation.html` · chrome: **story**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.story-bar` | page-local |
| 3 | HERO | `hero.story-cover` | page-local |
| 4 | CASE | `case.story-panels` | page-local |
| 5 | CASE | `case.project-file` | page-local |
| 6 | CASE | `case.story-section` | page-local |
| 7 | CASE | `case.network-fork` | page-local |
| 8 | CASE | `case.decision-cards` | page-local |
| 9 | CTA | `cta.story-end` | page-local |
| 10 | OVERLAY | `overlay.image-lightbox` | shared ×3 |
| 11 | CHROME | `chrome.story-footer` | page-local |

### Case study — screen gallery — `template.case-study-gallery`

1 route · `/visit-clinic-gift-cards.html` · chrome: **site**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.skip-link` | shared ×9 |
| 2 | CHROME | `chrome.site-header` | shared ×8 |
| 3 | CHROME | `chrome.mobile-menu` | shared ×8 |
| 4 | HERO | `hero.campaign-cover` | page-local |
| 5 | CASE | `case.campaign-brief` | page-local |
| 6 | CASE | `case.screen-gallery` | page-local |
| 7 | CTA | `cta.page-nav-footer` | shared ×2 |
| 8 | OVERLAY | `overlay.image-lightbox` | shared ×3 |
| 9 | CHROME | `chrome.site-footer` | shared ×8 |

## Section reference

### CHROME

_Page furniture that frames content: skip link, header/bar, mobile menu, footer._

**`chrome.skip-link`** — Visually hidden 'Skip to content' anchor to #main, revealed on keyboard focus.

· All 12 routes. · appears on 12 routes · implemented by `a.skip-link (a.skip on the story template)`

**`chrome.site-header`** — Top header: script-signature logo image linking home, 'My work' and 'Resume' links, a Day/Night theme toggle pill, and a 'Menu' button below the mobile breakpoint.

· 11 routes: every template except the scrollytelling case study. · appears on 11 routes · implemented by `header.site-header · js/theme.js (Day/Night toggle), js/main.js (menu)`

**`chrome.mobile-menu`** — Fixed, hidden-by-default full-screen navigation panel opened by the header's Menu button on narrow viewports.

· 11 routes, paired with chrome.site-header. · appears on 11 routes · implemented by `div#mobile-menu.mobile-menu`

**`chrome.site-footer`** — Dark footer: name and role, the 'Let's work together' line, Email / LinkedIn / Resume links, a 'More work' link, and a copyright line.

· 11 routes, paired with chrome.site-header. · appears on 11 routes · implemented by `footer.site-footer.container`

**`chrome.story-bar`** — Fixed top bar specific to the scrollytelling case study, with its own theme toggle and a thin reading-progress line above it.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `header.bar + div.bar-progress · js/oc-story.js`

**`chrome.story-footer`** — Minimal one-line footer (year only) closing the scrollytelling case study.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `footer.foot`

### OVERLAY

_Hidden-by-default runtime UI opened by a click or timer: modals, lightboxes, viewers, hints._

**`overlay.lock-modal`** — 'This project is locked' password dialog shown when a locked project row or card is clicked; client-side gate only.

· 2 routes: home and the work index. · appears on 2 routes · implemented by `div#lock-modal.lock-modal · js/lock.js`

**`overlay.project-box-overlay`** — Fixed overlay that expands a project from the home project box into a larger view.

· 1 route: home. · appears on 1 routes · implemented by `div#pbox-overlay.pbx-overlay · js/home-box.js`

**`overlay.desktop-hint`** — Mobile-only dialog ('Drag through my name… open it on desktop'), mounted 500ms after load at widths up to 979px, auto-dismissed after 10s, suppressed for the session once closed.

· 1 route: home. · appears on 1 routes · implemented by `js/main.js (creates div.desktop-hint)`

**`overlay.booth-viewer`** — Photo viewer with previous/next/close controls for the photo-booth strip in the personal-story intro.

· 1 route: home. · appears on 1 routes · implemented by `div#lw-booth-view.lw-booth-view · js/little-world.js`

**`overlay.dreams-modal`** — 'What I'm working towards' modal over a cloud backdrop, opened by the 'A peek into my dreams' button.

· 1 route: home. · appears on 1 routes · implemented by `div#dreams.lw-dreams.lw-dreams-modal · js/little-world.js`

**`overlay.image-lightbox`** — Click-to-enlarge viewer for case-study screenshots; three implementations of the same behaviour.

· 3 routes: the chaptered, gallery and scrollytelling case studies. · appears on 3 routes · implemented by `div#cs2-lightbox / dialog#vx-lightbox / div.zoom`

### HERO

_The page-opening block: title, positioning line and (on case studies) cover media._

**`hero.home-intro`** — Home opener: very large display-type name, role line, a three-line positioning statement, a one-line sub, and a 'See my work' arrow link, over a randomised field of short dashes.

· 1 route: home. · appears on 1 routes · implemented by `section.hero.container · js/hero.js`

**`hero.work-index-head`** — Work-index opener: the 'Everything I've worked on.' heading with an intro line.

· 1 route: the work index. · appears on 1 routes · implemented by `section.mw-head`

**`hero.resume-head`** — Resume opener: 'Resume' kicker, name, role, and a contact list (email, phone, LinkedIn).

· 1 route: the resume. · appears on 1 routes · implemented by `resume.html > first section.section.container`

**`hero.nda-heading`** — NDA notice opener: 'All work' back link, 'This one is under NDA' title and a short explanation of why the project can't be shown.

· 1 route: the NDA notice. · appears on 1 routes · implemented by `section.nda > a.cs-back, h1.nda-title, div.nda-body`

**`hero.case-cover-short`** — Short case-study cover: kicker, title, dek, a meta list and a looping video in a framed stage panel (optional action buttons), leading straight into a single chapter.

· 3 routes: the short case studies. · appears on 3 routes · implemented by `section.cs2-hero.short`

**`hero.case-cover-chaptered`** — Chaptered case-study cover: kicker, title, dek, a meta list and a looping video in a side media panel, leading into a chapter navigation and seven chapters.

· 1 route: the chaptered case study. · appears on 1 routes · implemented by `section.cs2-hero`

**`hero.case-cover-longform`** — Long-form case-study cover: one-sentence product framing as the title, meta and hero visual.

· 2 routes: the long-form case studies. · appears on 2 routes · implemented by `section.v3-hero.v3-wrap#top`

**`hero.story-cover`** — Full-viewport scrollytelling opener ('The Doctor Finder') that hands off directly to the story panels.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `section.hero (offline-doctor-consultation.html)`

**`hero.campaign-cover`** — Gallery case-study cover built around the campaign offer line ('Give ₹500, Get ₹500.').

· 1 route: the gallery case study. · appears on 1 routes · implemented by `section.vx-hero`

### WORK

_Blocks that list or showcase projects._

**`work.home-work-head`** — Home work intro: 'All work' kicker, 'Problems I've worked on…' heading and a row of skill filter chips.

· 1 route: home. · appears on 1 routes · implemented by `#work > div.pbx-head + div#filter-bar`

**`work.project-box`** — Interactive 'healthcare work box' showcasing projects, with pagination dots, a 'View more work' link and a numbered project index list beneath.

· 1 route: home. · appears on 1 routes · implemented by `div#pbox.pbx + div.pbx-dots + div.pbx-more + div#pbox-index · js/home-box.js, js/data.js`

**`work.ai-playground`** — 'My AI playground' block: heading plus playable AI-built project cards (e.g. a maths Jenga game) with looping video previews.

· 1 route: home. · appears on 1 routes · implemented by `section#ai.ai`

**`work.project-card-stack`** — Vertical stack of 10 large numbered project cards (number · area tag, one-line outcome, thumbnail), revealed on scroll; some link to locked projects.

· 1 route: the work index. · appears on 1 routes · implemented by `section.mw-stack > a.mw-card`

### ABOUT

_Blocks about the person: skills, personal story, resume content._

**`about.skills-list`** — 'What I do' list of skill areas (0→1 product design, product strategy, AI product design, UX research…), each with a thumbnail or video preview.

· 1 route: home. · appears on 1 routes · implemented by `section#skills.sk · js/skills.js`

**`about.little-world-intro`** — 'A little world called Ayushi' personal-story opener with a photo-booth strip and craft photos, set on a torn-paper band.

· 1 route: home. · appears on 1 routes · implemented by `section#lw-intro.lw-hero · js/little-world.js`

**`about.diary`** — Paged diary of personal chapters, shown as book spreads with page turning, plus short 'love' notes.

· 1 route: home. · appears on 1 routes · implemented by `section#lw-diary.dy-stage · js/diary.js`

**`about.to-be-continued`** — Closing personal chapter ('chapter 05 · to be continued…') on a pastel cloud band, with the 'A peek into my dreams' button.

· 1 route: home. · appears on 1 routes · implemented by `section#lw-ch5.lw-end`

**`about.resume-summary`** — Resume 'Professional Summary' paragraph.

· 1 route: the resume. · appears on 1 routes · implemented by `section.cs-section[aria-labelledby=summary-heading]`

**`about.resume-experience`** — Resume 'Experience' list: roles with employer, dates and achievement bullets.

· 1 route: the resume. · appears on 1 routes · implemented by `section.cs-section[aria-labelledby=experience-heading]`

**`about.resume-skills`** — Resume 'Skills' groups.

· 1 route: the resume. · appears on 1 routes · implemented by `section.cs-section[aria-labelledby=skills-heading]`

**`about.resume-education`** — Resume 'Education' entry.

· 1 route: the resume. · appears on 1 routes · implemented by `section.cs-section[aria-labelledby=education-heading]`

**`about.resume-certifications`** — Resume 'Certifications / Programs' list.

· 1 route: the resume. · appears on 1 routes · implemented by `section.cs-section[aria-labelledby=certifications-heading]`

### CASE

_Case-study narrative blocks between the opener and the closing._

**`case.nda-redacted-art`** — Interactive redacted-page illustration that stays redacted as the cursor moves over it.

· 1 route: the NDA notice. · appears on 1 routes · implemented by `section.nda > figure.nda-art`

**`case.tldr`** — Summary panel directly under a long-form cover ('The short version' / 'My role').

· 2 routes: the long-form case studies. · appears on 2 routes · implemented by `section.v3-tldr#summary`

**`case.chapter-nav`** — Sticky in-page chapter navigation that tracks the chapter in view.

· 3 routes: the chaptered and long-form case studies. · appears on 3 routes · implemented by `nav.cs2-nav / nav.v3-nav[data-chapter-nav]`

**`case.chapter`** — Numbered chapter ('01 At a glance', '03 Root cause'…) with heading, prose and figures; repeats with alternating tinted backgrounds on the chaptered page.

· 4 routes: one chapter on each short case study, seven on the chaptered one. · appears on 4 routes · implemented by `section.cs2-ch (.tint variant)`

**`case.longform-chapter`** — Long-form chapter group (e.g. #idea, #bets, #system) made of several full-width bands in plain, tinted or dark variants: brief, problem, pains, bets, entry points, pricing tiers.

· 2 routes: the long-form case studies (six chapter groups each). · appears on 2 routes · implemented by `main > div#<chapter> > section.v3-section (.v3-wrap/.v3-tint/.v3-dark)`

**`case.scroll-console`** — Scroll-driven walkthrough: a sticky phone/console panel on one side updates as numbered steps ('01 · Booked', '01 · Offer') scroll past on the other.

· 2 routes: the long-form case studies, inside one chapter group. · appears on 2 routes · implemented by `section.v3-console-section[data-console] · js/visit-clinic-v3.js, js/family-ahc.js`

**`case.story-panels`** — Four-panel scrollytelling sequence ('Something's not right. Time to see a doctor.') ending in a one-line hand-off.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `section.story[data-story] + p.story-end · js/oc-story.js`

**`case.project-file`** — Project 'file card' summarising the redesign (area, role, timeline) before the narrative starts.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `section.file.wrap`

**`case.story-section`** — Standard narrative section on the scrollytelling page: a short headline ('Clients said it first.') with prose, figures or reveal cards; repeats.

· 1 route: the scrollytelling case study (seven instances). · appears on 1 routes · implemented by `section.sec`

**`case.network-fork`** — Scroll-stepped diagram with its own step nav showing how two banners split the doctor network, followed by a short summary block.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `section.fork[data-fork] + div.after-fork · js/oc-story.js`

**`case.decision-cards`** — 'Six calls that shaped the flow': a run of numbered decision cards, each with its own header, rationale and screens.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `section.sec#decisions > article.ds`

**`case.campaign-brief`** — 'The goal' brief strip under the gallery cover.

· 1 route: the gallery case study. · appears on 1 routes · implemented by `section.vx-brief`

**`case.screen-gallery`** — 'The three screens' gallery: section head plus numbered screen cards (01 · Share …) that open in the lightbox.

· 1 route: the gallery case study. · appears on 1 routes · implemented by `visit-clinic-gift-cards.html > main > section:nth-child(3)`

### CTA

_Closing blocks that ask the reader to get in touch or move to another page._

**`cta.nda-walkthrough-ask`** — 'Ask for a walkthrough' prompt with an 'Available on request' line closing the NDA notice.

· 1 route: the NDA notice. · appears on 1 routes · implemented by `section.nda > div.nda-ask + div.nda-cta`

**`cta.case-end`** — 'Get in touch' close for chapter-style case studies: invitation line plus a 'Next: <project> →' link.

· 4 routes: the short and chaptered case studies. · appears on 4 routes · implemented by `section.cs2-end`

**`cta.longform-final`** — Long-form close: a one-sentence takeaway, a short paragraph, then 'All work' and 'Talk about this project' links.

· 2 routes: the long-form case studies. · appears on 2 routes · implemented by `section.v3-final`

**`cta.story-end`** — Scrollytelling close ('That's the booking, sorted') with onward links.

· 1 route: the scrollytelling case study. · appears on 1 routes · implemented by `section.end.wrap`

**`cta.closing-line`** — Single centred line inviting the reader to get in touch.

· 1 route: the work index. · appears on 1 routes · implemented by `section.oc-closing > p.oc-closing-line`

**`cta.page-nav-footer`** — Two-link pager: '← Go to home' and a forward link (contact or the next case study).

· 2 routes: the work index and the gallery case study. · appears on 2 routes · implemented by `div.cs-nav-footer`

**`cta.resume-cta`** — Resume close: 'See the designs behind these projects.' with a link to the work.

· 1 route: the resume. · appears on 1 routes · implemented by `resume.html > last section.section.container`
