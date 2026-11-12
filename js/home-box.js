/**
 * Homepage "box of work". Builds one card per project from data.js, opens the
 * box when it scrolls into view, filters by category (non-matching cards sink
 * into the box) and expands a card into a full project view with a FLIP
 * transition. Locked projects hand off to lock.js through data-locked links.
 */
(function () {
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const box = document.getElementById('pbox');
  if (!box || typeof PROJECTS === 'undefined') return;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const HIDDEN = ['add-patient-previous-checkup', 'lab-test-booking-revamp', 'visit-clinic-gift-cards'];

  // what each card leads with — only facts that already appear on the site
  // what each card leads with — only facts that already appear on the site.
  // t = the card's archive-tab colour (restrained palette), shot = a real screen from the project.
  const LOOK = {
    'hybrid-test-booking': { g: '#f7f3ec', t: '#c9b8f0', c: '#c9b8f0', area: 'Diagnostics', short: 'Hybrid booking', k: 'Outcome', big: '1 cart', small: 'pathology + radiology, booked together', shot: 'assets/case-studies/hybrid/h01-phone-poster.jpg' },
    'visit-clinic-digital-experience': { g: '#f7f3ec', t: '#f2b6c8', c: '#f2b6c8', area: 'Clinic', short: 'Digital clinic', k: 'Impact', big: '~100', small: 'app bookings in one day', shot: 'assets/thumbs/visit-clinic.webp' },
    'visit-clinic-gift-cards': { g: '#f7f3ec', t: '#f6d980', c: '#f6d980', area: 'Referrals', short: 'Gift cards', k: 'Referral offer', big: '₹500', small: 'give ₹500, get ₹500', shot: 'assets/thumbs/gift-cards.webp' },
    'family-ahc': { g: '#f7f3ec', t: '#f6d980', c: '#f6d980', area: 'Family upsell', short: 'Family checkups', k: 'Adoption', big: '32.6%', small: 'of order-timeline visitors used it', shot: 'assets/case-studies/family/f5-members-selected.webp' },
    'offline-consultation-booking': { g: '#f7f3ec', t: '#f2b6c8', c: '#f2b6c8', area: 'Consultations', short: 'Offline consults', k: 'Outcome', big: '↑ Retention', small: 'higher user satisfaction and retention', shot: 'assets/thumbs/selfbook.webp' },
    'claim-approval': { g: '#f7f3ec', t: '#c9b8f0', c: '#c9b8f0', cardTitle: 'Claim Approval Dashboard', area: 'Claims · AI', short: 'Claims AI', k: 'Impact', big: '−87%', small: 'claim review time, 30 → 4 min', shot: 'assets/case-studies/claims/claims-thumb.webp' },
  };
  const FALLBACK = { g: '#f7f3ec', t: '#3a3634', c: '#3a3634', area: '', k: 'Impact', big: '→', small: '', shot: '' };
  const RZ = ['-2.5deg', '-1deg', '0.5deg', '-1deg', '1.5deg', '-2deg', '2deg'];
  const ZF = [0.06, -0.08, 0.02, -0.1, 0.05, -0.04, 0.03];   // depth inside the box, as a share of its depth

  const list = PROJECTS.filter((p) => !HIDDEN.includes(p.slug)).sort((a, b) => a.priority - b.priority);
  const cats = [{ slug: 'everything', label: 'Everything' }, ...(typeof CATEGORIES !== 'undefined' ? CATEGORIES : [])];
  const labelFor = (slug) => (cats.find((c) => c.slug === slug) || {}).label || slug;
  const look = (p) => Object.assign({}, FALLBACK, LOOK[p.slug] || {});
  const esc = (s) => String(s || '').replace(/[&<>"]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]));

  function hrefFor(p) {
    const internal = p.nda || p.pageUrl;
    const href = p.nda ? `nda.html?project=${p.slug}` : (p.pageUrl || p.framerUrl || (typeof FRAMER_URL !== 'undefined' ? FRAMER_URL : 'projects.html'));
    return { href, external: !internal };
  }

  // ---------- render cards + index ----------
  const cardsEl = box.querySelector('.pbx-cards');
  const indexEl = document.getElementById('pbox-index');
  cardsEl.innerHTML = list.map((p, i) => {
    const l = look(p);
    return `
      <button class="pbx-card" type="button" data-i="${i}" style="--g:${l.g};--c:${l.c};--t:${l.t};--rz:${RZ[i % RZ.length]};--x:calc(var(--bw) * ${((i - (list.length - 1) / 2) * 0.192).toFixed(3)});--z:calc(var(--bd) * ${ZF[i % ZF.length]});--i:${i}"
        aria-label="${esc(p.title)}${p.locked ? ' (locked)' : ''}. ${esc(l.k)}: ${esc(l.big)}, ${esc(l.small)}. Open project">
        <span class="pbx-card-in">
          <span class="pbx-card-top"><b class="pbx-card-no">${String(i + 1).padStart(2, '0')}</b><span class="pbx-card-area">${esc(l.area)}</span>${p.locked ? '<span class="pbx-card-lock" aria-hidden="true">🔒</span>' : ''}</span>
          <span class="pbx-card-title">${esc(l.cardTitle || p.title)}</span>
          <span class="pbx-card-short" aria-hidden="true">${esc(l.short || p.title)}</span>
          <span class="pbx-card-impact">
            <em class="pbx-card-k">${esc(l.k)}</em>
            <span class="pbx-card-big">${esc(l.big)}</span>
            <span class="pbx-card-small">${esc(l.small)}</span>
          </span>
          ${l.shot ? `<span class="pbx-card-shot" aria-hidden="true"><img src="${esc(l.shot)}" alt="" decoding="async"></span>` : ''}
        </span>
      </button>`;
  }).join('');
  if (indexEl) {
    indexEl.innerHTML = list.map((p, i) => `
      <button type="button" data-i="${i}" style="--c:${look(p).c}">
        <i>${String(i + 1).padStart(2, '0')}</i>
        <span><b>${esc(p.title)}</b><span class="pbx-index-stat"><strong>${esc(look(p).big)}</strong> ${esc(look(p).small)}</span><span>${esc(look(p).area)}${p.locked ? ' · 🔒 locked' : ''}</span></span>
      </button>`).join('');
  }
  const cards = [...cardsEl.querySelectorAll('.pbx-card')];

  // ---------- sound: tiny paper sounds made with Web Audio (no files) ----------
  // Browsers only allow audio after the visitor clicks or taps, so the context
  // starts on the first gesture. Always on.
  const sfx = (() => {
    const AC = window.AudioContext || window.webkitAudioContext;
    let ctx = null; let noise = null; let last = 0;
    const on = true; // sound is always on
    function wake() {
      if (!AC) return;
      if (!ctx) {
        ctx = new AC();
        noise = ctx.createBuffer(1, ctx.sampleRate * 0.6, ctx.sampleRate);
        const d = noise.getChannelData(0);
        for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      }
      if (ctx.state === 'suspended') ctx.resume();
    }
    ['pointerdown', 'keydown', 'touchstart'].forEach((ev) => window.addEventListener(ev, wake, { passive: true }));
    const ready = () => on && ctx && ctx.state === 'running';
    // a filtered burst of noise: paper rustle / slide
    function rustle({ dur = 0.06, vol = 0.05, f1 = 3000, f2 = f1, q = 0.9, delay = 0 }) {
      const t = ctx.currentTime + delay;
      const src = ctx.createBufferSource(); src.buffer = noise;
      const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = q;
      bp.frequency.setValueAtTime(f1, t); bp.frequency.exponentialRampToValueAtTime(f2, t + dur);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + Math.min(0.012, dur / 3));
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(bp).connect(g).connect(ctx.destination);
      src.start(t, Math.random() * 0.3); src.stop(t + dur + 0.02);
    }
    // a soft rounded tone: the "pop" when a card lands
    function tone({ f1 = 520, f2 = f1, dur = 0.14, vol = 0.06, type = 'sine', delay = 0 }) {
      const t = ctx.currentTime + delay;
      const o = ctx.createOscillator(); o.type = type;
      o.frequency.setValueAtTime(f1, t); o.frequency.exponentialRampToValueAtTime(f2, t + dur);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g).connect(ctx.destination); o.start(t); o.stop(t + dur + 0.02);
    }
    // a whoosh: airy noise through a sweeping filter that swells in the middle, like something flying past
    function whoosh({ dur = 0.5, vol = 0.16, f1 = 300, f2 = 2400, peak = 0.45 }) {
      const t = ctx.currentTime;
      const src = ctx.createBufferSource(); src.buffer = noise; src.playbackRate.value = 0.9;
      const bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 1.4;
      bp.frequency.setValueAtTime(f1, t); bp.frequency.exponentialRampToValueAtTime(f2, t + dur);
      const lp = ctx.createBiquadFilter(); lp.type = 'lowpass';
      lp.frequency.setValueAtTime(Math.min(f1, f2) * 2, t); lp.frequency.exponentialRampToValueAtTime(Math.max(f1, f2) * 2.5, t + dur * peak);
      lp.frequency.exponentialRampToValueAtTime(Math.min(f1, f2) * 2, t + dur);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(vol, t + dur * peak);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(bp).connect(lp).connect(g).connect(ctx.destination);
      src.start(t, Math.random() * 0.05); src.stop(t + dur + 0.02);
    }
    const play = {
      hover() { const n = performance.now(); if (n - last < 70) return; last = n; rustle({ dur: 0.045, vol: 0.035, f1: 4200, f2: 2600, q: 1.2 }); },
      open() { whoosh({ dur: 0.55, vol: 0.18, f1: 260, f2: 2600, peak: 0.5 }); },     // whoosh out, rising
      close() { whoosh({ dur: 0.5, vol: 0.15, f1: 2400, f2: 240, peak: 0.45 }); },    // whoosh back, falling
      swipe() { rustle({ dur: 0.16, vol: 0.05, f1: 1400, f2: 3000, q: 0.8 }); },
      sink() { rustle({ dur: 0.2, vol: 0.045, f1: 2400, f2: 700, q: 0.8 }); },
      lid() { rustle({ dur: 0.4, vol: 0.05, f1: 600, f2: 1800, q: 0.6 }); tone({ f1: 140, f2: 90, dur: 0.22, vol: 0.08, delay: 0.32 }); },
    };
    return {
      play(name) { if (ready() && play[name]) play[name](); },
      wake,
    };
  })();
  cards.forEach((c) => {
    c.addEventListener('pointerenter', (e) => { if (e.pointerType === 'mouse') sfx.play('hover'); });
    c.addEventListener('focus', () => sfx.play('hover'));
  });

  // ---------- phones: a swipeable row — one big card in front, its neighbours peeking ----------
  const mob = window.matchMedia('(max-width: 640px)');
  // start on the 2nd card so a neighbour peeks out on both sides (3 cards in view)
  let pick = Math.min(1, list.length - 1);
  const dotsEl = document.createElement('div');
  dotsEl.className = 'pbx-dots';
  dotsEl.setAttribute('aria-hidden', 'true');
  dotsEl.innerHTML = list.map((p, i) => `<button type="button" tabindex="-1" data-i="${i}" style="--c:${look(p).c}"></button>`).join('');
  box.after(dotsEl);
  function layoutRow() {
    cards.forEach((c, i) => {
      const m = i - pick;
      c.style.setProperty('--m', m);
      c.style.setProperty('--ma', Math.abs(m));
      c.classList.toggle('is-front', m === 0);
      c.classList.toggle('is-far', Math.abs(m) > 1);
    });
    [...dotsEl.children].forEach((d, i) => d.classList.toggle('on', i === pick));
  }
  function pickCard(i) {
    const was = pick;
    pick = Math.max(0, Math.min(cards.length - 1, i));
    if (pick !== was) sfx.play('swipe');
    layoutRow();
  }
  layoutRow();
  dotsEl.addEventListener('click', (e) => { const d = e.target.closest('button'); if (d) pickCard(+d.dataset.i); });
  let tx = null; let ty = 0;
  box.addEventListener('touchstart', (e) => { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
  box.addEventListener('touchend', (e) => {
    if (tx === null || !mob.matches) return;
    const dx = e.changedTouches[0].clientX - tx;
    const dy = e.changedTouches[0].clientY - ty;
    tx = null;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.3) pickCard(pick + (dx < 0 ? 1 : -1));
  });

  // ---------- open the box each time it scrolls into view ----------
  // It opens once ~40% of it is on screen, and quietly closes again after it
  // has left the screen completely, so the opening plays on every visit.
  let settleT = 0;
  function openBox() {
    if (box.classList.contains('is-open')) return;
    box.classList.add('is-open');
    sfx.play('lid');
    clearTimeout(settleT);
    settleT = setTimeout(() => box.classList.add('settled'), 1100);
  }
  function closeBox() {
    if (openIndex !== -1) return; // a project is open on top (the observer only fires after setup)
    clearTimeout(settleT);
    box.classList.remove('is-open', 'settled');
  }
  if (reduced || !('IntersectionObserver' in window)) openBox();
  else {
    // starts just before the box reaches the screen, so the cards are already up when you get there
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => {
        if (e.isIntersecting) openBox();
        else closeBox();
      });
    }, { threshold: 0, rootMargin: '0px 0px 25% 0px' });
    io.observe(box);
  }

  // ---------- the whole box turns gently toward the cursor ----------
  if (fine && !reduced) {
    let raf = 0;
    box.addEventListener('pointermove', (e) => {
      const r = box.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        box.style.setProperty('--ry', (-6 + x * 14).toFixed(2) + 'deg');
        box.style.setProperty('--rx', (-21 - y * 6).toFixed(2) + 'deg');
      });
    });
    box.addEventListener('pointerleave', () => { box.style.removeProperty('--ry'); box.style.removeProperty('--rx'); });
  }

  // ---------- filters: non-matching cards sink into the box ----------
  const filterBar = document.getElementById('filter-bar');
  const diag = document.getElementById('diagnosis-label');
  let active = 'everything';
  if (filterBar) {
    cats.forEach((c) => {
      const b = document.createElement('button');
      b.className = 'filter-chip';
      b.type = 'button';
      b.textContent = c.label;
      b.setAttribute('aria-pressed', String(c.slug === active));
      b.addEventListener('click', () => { if (active !== c.slug) { active = c.slug; applyFilter(); sfx.play(active === 'everything' ? 'swipe' : 'sink'); } });
      filterBar.appendChild(b);
    });
  }
  function applyFilter() {
    if (filterBar) [...filterBar.children].forEach((b, i) => b.setAttribute('aria-pressed', String(cats[i].slug === active)));
    if (diag) diag.textContent = active === 'everything' ? 'All work' : `Showing: ${labelFor(active)}`;
    list.forEach((p, i) => {
      const out = active !== 'everything' && !p.categories.includes(active);
      cards[i].classList.toggle('is-out', out);
      // a shrunk card stays tappable: tapping it lifts it and switches to its category
      cards[i].setAttribute('aria-label', out
        ? `${p.title}: show ${labelFor(p.categories[0])} projects`
        : `${p.title}${p.locked ? ' (locked)' : ''}. Open project`);
      const ib = indexEl && indexEl.children[i];
      if (ib) ib.classList.toggle('is-out', out);
    });
    // phones: if the front card was filtered out, bring the first matching one forward
    if (typeof pickCard === 'function' && cards[pick] && cards[pick].classList.contains('is-out')) {
      const first = cards.findIndex((c) => !c.classList.contains('is-out'));
      if (first >= 0) pickCard(first);
    }
  }

  // ---------- expanded project view (FLIP) ----------
  const overlay = document.getElementById('pbox-overlay');
  const sheet = overlay.querySelector('.pbx-sheet');
  const body = overlay.querySelector('.pbx-sheet-body');
  const closeBtn = overlay.querySelector('.pbx-close');
  let openIndex = -1;
  let lastFocus = null;
  const EASE = 'cubic-bezier(0.2, 0.85, 0.2, 1)';

  function targetRect() {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    if (vw <= 640) return { left: 0, top: 0, width: vw, height: vh, radius: 0 };
    const w = Math.min(1080, vw * 0.92);
    const h = Math.min(680, vh * 0.88);
    return { left: (vw - w) / 2, top: (vh - h) / 2, width: w, height: h, radius: 24 };
  }
  function place(r) {
    sheet.style.left = r.left + 'px';
    sheet.style.top = r.top + 'px';
    sheet.style.width = r.width + 'px';
    sheet.style.height = r.height + 'px';
    sheet.style.borderRadius = r.radius + 'px';
  }

  function detailHTML(p, i) {
    const l = look(p);
    const { href, external } = hrefFor(p);
    // same preview as the pre-box homepage, kept straight:
    // walkthrough video (was a GIF) > cycling screenshots > one scrollable screen > locked note
    const visual = p.previewVideo
      ? `<div class="pbx-d-frame is-video${p.previewPhone ? ' is-phone' : ''}${p.previewWide ? ' is-wide' : ''}"><video autoplay muted loop playsinline preload="metadata"${p.previewPoster ? ` poster="${esc(p.previewPoster)}"` : ''} aria-label="${esc(p.title)} walkthrough"><source src="${esc(p.previewVideo)}" type="video/mp4"></video></div>`
      : p.previewImages
      ? `<div class="pbx-d-frame"><div class="pbx-cycle">${p.previewImages.map((src, j) => `<img src="${esc(src)}" alt="${esc(p.title)}, app screen ${j + 1}" data-on="${j === 0}">`).join('')}</div></div>`
      : p.previewImage
      ? `<div class="pbx-d-frame is-scroll" tabindex="0" aria-label="${esc(p.title)} screen, scrollable"><img src="${esc(p.previewImage)}" alt="${esc(p.title)}, app screen"></div>`
      : p.locked
      ? `<div class="pbx-d-frame is-note"><p class="pbx-note-eyes" aria-hidden="true">🔒</p><p class="pbx-note-title">This project is locked.</p><p class="pbx-note-body">Use "Unlock to view in detail" and enter the password to see it.</p></div>`
      : `<div class="pbx-d-art" aria-hidden="true">${esc(l.big)}</div>`;
    const rows = p.summary ? `
      <dl class="pbx-d-rows">
        <div><dt>Problem</dt><dd>${esc(p.summary.problem)}</dd></div>
        <div><dt>Solution</dt><dd>${esc(p.summary.solution)}</dd></div>
        <div><dt>Impact</dt><dd>${esc(p.summary.impact)}</dd></div>
      </dl>` : '';
    const lockAttrs = p.locked ? ` data-locked="true" data-slug="${esc(p.slug)}"` : '';
    const target = external ? ' target="_blank" rel="noopener"' : '';
    const ctaText = p.locked ? 'Unlock to view in detail 🔒' : (external ? 'View in detail ↗' : 'View in detail');
    return `
      <div>
        <p class="pbx-d-kicker">${String(i + 1).padStart(2, '0')} · ${esc(l.area)}</p>
        <h2 class="pbx-d-title" id="pbox-title">${esc(p.title)}</h2>
        <p class="pbx-d-one">${esc(p.oneLiner)}</p>
        <div class="pbx-d-stat"><em>${esc(l.k)}</em><b>${esc(l.big)}</b><span>${esc(l.small)}</span></div>
        ${rows}
        <div class="pbx-d-tags">${p.categories.map((c) => `<span>${esc(labelFor(c))}</span>`).join('')}</div>
        <a class="pbx-d-cta" href="${esc(href)}"${target}${lockAttrs}><span class="project-title visually-hidden">${esc(p.title)}</span>${ctaText} <span class="arrow" aria-hidden="true">→</span></a>
      </div>
      <div class="pbx-d-visual">${visual}</div>`;
  }

  function open(i) {
    if (openIndex !== -1) return;
    const p = list[i];
    const card = cards[i];
    openIndex = i;
    lastFocus = document.activeElement;
    sheet.style.setProperty('--g', look(p).g);
    sheet.style.setProperty('--t', look(p).t);
    body.innerHTML = detailHTML(p, i);
    overlay.hidden = false;
    document.documentElement.style.overflow = 'hidden';

    const from = card.getBoundingClientRect();
    const to = targetRect();
    card.classList.add('is-flying');
    place(to);
    requestAnimationFrame(() => overlay.classList.add('is-open'));
    if (reduced) {
      sheet.classList.add('show');
    } else {
      sheet.animate([
        { left: from.left + 'px', top: from.top + 'px', width: from.width + 'px', height: from.height + 'px', borderRadius: '12px' },
        { left: to.left + 'px', top: to.top + 'px', width: to.width + 'px', height: to.height + 'px', borderRadius: to.radius + 'px' },
      ], { duration: 650, easing: EASE });
      setTimeout(() => sheet.classList.add('show'), 260);
    }
    closeBtn.focus({ preventScroll: true });
    sfx.play('open');
    startCycle();
  }

  let cycleTimer = null;
  function startCycle() {
    clearInterval(cycleTimer);
    const frames = [...body.querySelectorAll('.pbx-cycle img')];
    if (frames.length < 2 || reduced) return;
    let k = 0;
    cycleTimer = setInterval(() => {
      frames[k].dataset.on = 'false';
      k = (k + 1) % frames.length;
      frames[k].dataset.on = 'true';
    }, 2600);
  }

  function close() {
    if (openIndex === -1) return;
    const card = cards[openIndex];
    const from = sheet.getBoundingClientRect();
    const to = card.getBoundingClientRect();
    clearInterval(cycleTimer);
    sfx.play('close');
    sheet.classList.remove('show');
    overlay.classList.remove('is-open');
    const done = () => {
      overlay.hidden = true;
      card.classList.remove('is-flying');
      document.documentElement.style.overflow = '';
      body.innerHTML = '';
      openIndex = -1;
      if (lastFocus) lastFocus.focus({ preventScroll: true });
    };
    if (reduced) { done(); return; }
    const anim = sheet.animate([
      { left: from.left + 'px', top: from.top + 'px', width: from.width + 'px', height: from.height + 'px', borderRadius: getComputedStyle(sheet).borderRadius },
      { left: to.left + 'px', top: to.top + 'px', width: to.width + 'px', height: to.height + 'px', borderRadius: '12px' },
    ], { duration: 520, easing: EASE, delay: 120, fill: 'forwards' });
    // finish exactly once, even if the browser never reports the animation ending
    let ended = false;
    const end = () => { if (ended) return; ended = true; anim.cancel(); done(); };
    anim.onfinish = end;
    setTimeout(end, 900);
  }

  cards.forEach((c, i) => c.addEventListener('click', () => {
    // phones: a side card comes to the front first; tapping the front card opens it
    if (mob.matches && i !== pick) { pickCard(i); return; }
    if (c.classList.contains('is-out')) {
      // rise it up and update the filter to this project's category
      active = list[i].categories[0];
      applyFilter();
      sfx.play('swipe');
      c.classList.add('just-picked');
      setTimeout(() => c.classList.remove('just-picked'), 700);
      return;
    }
    open(i);
  }));
  if (indexEl) [...indexEl.children].forEach((b) => b.addEventListener('click', () => {
    const i = +b.dataset.i;
    if (mob.matches) pickCard(i);
    // bring the box into view first so the card has somewhere to fly from
    const r = box.getBoundingClientRect();
    if (r.bottom < 80 || r.top > window.innerHeight - 80) {
      box.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'center' });
      setTimeout(() => open(i), reduced ? 0 : 600);
    } else open(i);
  }));
  closeBtn.addEventListener('click', close);
  overlay.querySelector('.pbx-backdrop').addEventListener('click', close);
  document.addEventListener('keydown', (e) => {
    if (openIndex === -1) return;
    const lockOpen = document.querySelector('[data-lock-modal]:not([hidden])');
    if (e.key === 'Escape' && !lockOpen) close();
    if (e.key === 'Tab' && !lockOpen) { // keep focus inside the sheet
      const f = [...sheet.querySelectorAll('a[href], button')].filter((el) => !el.hidden);
      if (!f.length) return;
      const first = f[0];
      const last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  window.addEventListener('resize', () => { if (openIndex !== -1) place(targetRect()); });

  applyFilter();
})();
