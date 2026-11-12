#!/usr/bin/env node
// Re-measure tool for the design-repo (optional; verify_all does not need a browser).
//
//   SITE_BASE_URL=http://127.0.0.1:8090/ node extraction/measure_sections.mjs heights > out.json
//   SITE_BASE_URL=http://127.0.0.1:8090/ node extraction/measure_sections.mjs styles  > styles.json
//   SITE_BASE_URL=http://127.0.0.1:8090/ node extraction/measure_sections.mjs scoped  > scoped.json
//
// Playwright is resolved from the PLAYWRIGHT_MODULE env var (a directory that contains
// node_modules/playwright, or the package path itself) or from a normal `import('playwright')`.
// No machine path is stored in this repo. The site must be served over HTTP (any static server).
//
// "heights": for every route and viewport, the in-flow semantic blocks (header, footer and
// the outermost <section>/<nav> elements inside <main>; a <section> that itself contains
// <section>s is a wrapper and is descended into), with document top and height in CSS px.
// Overlays (role=dialog, [hidden], position fixed) are skipped: they take no page height.
// The block-selection rule is identical to extraction/classify_routes.py, so the measured
// list and the classifier's sequence can be joined index by index.
//
// "styles": computed-style histograms (colour, background, font family/size/weight, radius)
// over visible elements, plus the resolved :root custom properties, for both themes.

import { createRequire } from 'module';

const ROUTES = [
  'index.html', 'projects.html', 'resume.html', 'nda.html', 'claim-approval.html',
  'family-ahc.html', 'hybrid-diagnostic.html', 'offline-doctor-consultation.html',
  'virtual-wardrobe.html', 'visit-clinic-gift-cards.html', 'visit-clinic.html', 'wallet-ui.html',
];
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'mobile', width: 390, height: 844 },
];

async function loadPlaywright() {
  const hint = process.env.PLAYWRIGHT_MODULE;
  if (hint) {
    try { return createRequire(hint.endsWith('/') ? hint : hint + '/')('playwright'); } catch (e) { /* fall through */ }
    return await import(hint);
  }
  return await import('playwright');
}

const BLOCKS_FN = () => {
  const main = document.querySelector('main');
  const out = [];
  const isOverlay = (el) => {
    const cs = getComputedStyle(el);
    return el.hidden || el.getAttribute('role') === 'dialog' || cs.position === 'fixed' || cs.display === 'none';
  };
  const describe = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      tag: el.tagName.toLowerCase(),
      id: el.id || null,
      classes: [...el.classList],
      top: Math.round(r.top + window.scrollY),
      height: Math.round(r.height),
      position: cs.position,
    };
  };
  const header = document.querySelector('body > header');
  if (header) out.push(describe(header));
  const walk = (node) => {
    for (const el of node.children) {
      const tag = el.tagName.toLowerCase();
      if (isOverlay(el)) continue;
      if (tag === 'section') {
        if (el.querySelector('section')) { walk(el); continue; }
        out.push(describe(el));
      } else if (tag === 'nav') {
        out.push(describe(el));
      } else {
        walk(el);
      }
    }
  };
  if (main) walk(main);
  const footer = document.querySelector('body > footer');
  if (footer) out.push(describe(footer));
  return { scrollHeight: document.documentElement.scrollHeight, blocks: out };
};

const STYLES_FN = (propNames) => {
  const hist = { color: {}, backgroundColor: {}, fontFamily: {}, fontSize: {}, fontWeight: {}, borderRadius: {} };
  const bump = (k, v) => { if (!v) return; hist[k][v] = (hist[k][v] || 0) + 1; };
  for (const el of document.body.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (hasText) {
      bump('color', cs.color); bump('fontFamily', cs.fontFamily.split(',')[0].replace(/["']/g, '').trim());
      bump('fontSize', cs.fontSize); bump('fontWeight', cs.fontWeight);
    }
    if (cs.backgroundColor !== 'rgba(0, 0, 0, 0)') bump('backgroundColor', cs.backgroundColor);
    if (cs.borderTopLeftRadius !== '0px') bump('borderRadius', cs.borderTopLeftRadius);
  }
  const rootCs = getComputedStyle(document.documentElement);
  const vars = {};
  for (const n of propNames) { const v = rootCs.getPropertyValue(n).trim(); if (v) vars[n] = v; }
  return { hist, vars, dataTheme: document.documentElement.dataset.theme || null };
};

async function settle(page) {
  await page.evaluate(async () => {
    await document.fonts.ready;
    const step = Math.max(400, Math.floor(window.innerHeight * 0.8));
    for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 60));
    }
    window.scrollTo(0, 0);
    await new Promise((r) => setTimeout(r, 300));
  });
}

async function main() {
  const mode = process.argv[2] || 'heights';
  const base = process.env.SITE_BASE_URL;
  if (!base) { console.error('set SITE_BASE_URL (e.g. http://127.0.0.1:8090/)'); process.exit(2); }
  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {});
  const result = { tool: 'extraction/measure_sections.mjs', mode, measuredAt: new Date().toISOString(), routes: {} };
  try {
    if (mode === 'heights') {
      for (const vp of VIEWPORTS) {
        for (const route of ROUTES) {
          const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
          const page = await ctx.newPage();
          await page.goto(base + route, { waitUntil: 'load' });
          await settle(page);
          const m = await page.evaluate(BLOCKS_FN);
          (result.routes[route] ||= {})[String(vp.width)] = m;
          await ctx.close();
        }
      }
    } else if (mode === 'styles') {
      const propNames = JSON.parse(process.env.CUSTOM_PROPS || '[]');
      for (const theme of ['night', 'day']) {
        for (const route of ROUTES) {
          const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
          if (theme === 'day') await ctx.addInitScript(() => { try { sessionStorage.setItem('site-theme', 'day'); } catch (e) {} });
          const page = await ctx.newPage();
          await page.goto(base + route, { waitUntil: 'load' });
          await settle(page);
          (result.routes[route] ||= {})[theme] = await page.evaluate(STYLES_FN, propNames);
          await ctx.close();
        }
      }
    } else if (mode === 'scoped') {
      // custom properties declared on a scope element rather than :root (case-study v3 scope,
      // little-world scope), resolved in both themes
      const SCOPES = [
        ['visit-clinic.html', 'main.v3', ['--acc', '--acc-2', '--acc-tint', '--ink', '--muted', '--line', '--line-2', '--paper', '--tint', '--mono']],
        ['index.html', 'section.lw', ['--cream', '--paper', '--ink', '--ink-soft', '--pink', '--pink-deep', '--pink-soft', '--blue', '--sky',
          '--blue-soft', '--butter', '--butter-soft', '--lav', '--lav-deep', '--lav-soft', '--mint', '--mint-soft', '--line', '--display',
          '--hand', '--spring', '--soft']],
      ];
      for (const theme of ['night', 'day']) {
        for (const [route, sel, props] of SCOPES) {
          const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
          if (theme === 'day') await ctx.addInitScript(() => { try { sessionStorage.setItem('site-theme', 'day'); } catch (e) {} });
          const page = await ctx.newPage();
          await page.goto(base + route, { waitUntil: 'load' });
          const vars = await page.evaluate(([s, ps]) => {
            const cs = getComputedStyle(document.querySelector(s)); const o = {};
            for (const n of ps) o[n] = cs.getPropertyValue(n).trim();
            return o;
          }, [sel, props]);
          ((result.scopes ||= {})[sel] ||= { route })[theme] = vars;
          await ctx.close();
        }
      }
    } else {
      console.error('mode must be heights|styles|scoped'); process.exit(2);
    }
  } finally {
    await browser.close();
  }
  process.stdout.write(JSON.stringify(result, null, 1));
}

main().catch((e) => { console.error(e); process.exit(1); });
