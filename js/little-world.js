/* "A little world called Ayushi" — interactions.
   Reveals, progressive annotations, cursor-reactive stickers, the plot-twist
   path, the shelf of notes, the receipt printer, the door, chapter progress
   and a few easter eggs. Everything degrades to a readable static page. */
(function () {
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  const root = document.querySelector('.lw');
  if (!root) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const $ = (id) => document.getElementById(id);

  // ---------- replaceable photos: show the pastel placeholder until an image exists
  root.querySelectorAll('.lw-photo img').forEach((img) => {
    const mark = () => img.closest('.lw-photo').classList.add('is-empty');
    if (img.complete && img.naturalWidth === 0) mark();
    img.addEventListener('error', mark);
  });

  // ---------- reveals + progressive annotations
  // things inside the diary appear when their page is turned to (see diary.js)
  const revealables = [...root.querySelectorAll('.lw-r, .lw-anno')].filter((el) => !el.closest('.dy-book'));
  const onReveal = new Map(); // element -> callback when first shown
  function show(el) {
    if (el.classList.contains('in')) return;
    el.classList.add('in');
    const cb = onReveal.get(el);
    if (cb) cb();
  }
  if (reduced || !('IntersectionObserver' in window)) {
    revealables.forEach(show);
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.18, rootMargin: '0px 0px -6% 0px' });
    revealables.forEach((el) => io.observe(el));
    // safety net for background tabs
    const sweep = () => revealables.forEach((el) => { if (el.getBoundingClientRect().top < window.innerHeight * 0.95) show(el); });
    setTimeout(sweep, 1400);
    window.addEventListener('scroll', sweep, { passive: true });
  }

  // ---------- invitation: glide down to the diary and open it
  const invite = $('lw-invite');
  if (invite) invite.addEventListener('click', () => {
    invite.classList.add('open');
    const t = $('dy-book');
    const head = document.querySelector('.site-header');
    const y = t.getBoundingClientRect().top + window.scrollY - (head ? head.offsetHeight : 72) - 18;
    window.scrollTo({ top: y, behavior: reduced ? 'auto' : 'smooth' });
    setTimeout(() => { if (window.lwDiary) window.lwDiary.open(); }, reduced ? 0 : 650);
  });

  // ---------- stickers respond to the cursor (each has its own depth)
  function cursorReact(zone) {
    if (!zone || !fine || reduced) return;
    const items = zone.querySelectorAll('.lw-cur');
    zone.addEventListener('pointermove', (e) => {
      const r = zone.getBoundingClientRect();
      const nx = (e.clientX - r.left) / r.width - 0.5;
      const ny = (e.clientY - r.top) / r.height - 0.5;
      items.forEach((it) => {
        const d = parseFloat(it.dataset.depth || '1');
        it.style.setProperty('--px', (nx * 22 * d).toFixed(1) + 'px');
        it.style.setProperty('--py', (ny * 18 * d).toFixed(1) + 'px');
        it.style.setProperty('--pr', (nx * 12 * d).toFixed(1) + 'deg');
      });
    });
    zone.addEventListener('pointerleave', () => items.forEach((it) => {
      it.style.removeProperty('--px'); it.style.removeProperty('--py'); it.style.removeProperty('--pr');
    }));
  }
  // (the chapter 01 stickers stay still: no cursor-follow there)

  // ---------- 02: the path draws itself as you scroll through it
  const path = $('lw-path');
  const draw = path && path.querySelector('.draw');
  const stones = path ? [...path.querySelectorAll('.lw-ms')] : [];
  let len = 0;
  if (draw) {
    len = draw.getTotalLength();
    draw.style.strokeDasharray = len;
    draw.style.strokeDashoffset = reduced ? 0 : len;
    if (reduced) stones.forEach((s) => s.classList.add('on'));
  }
  function drawPath() {
    if (!draw || reduced) return;
    const r = path.getBoundingClientRect();
    const vh = window.innerHeight;
    const p = Math.min(1, Math.max(0, (vh * 0.85 - r.top) / (r.height + vh * 0.25)));
    draw.style.strokeDashoffset = (len * (1 - p)).toFixed(1);
    stones.forEach((s) => s.classList.toggle('on', p >= parseFloat(s.dataset.at)));
  }

  // ---------- 03: the shelf of little notes
  const NOTES = {
    paint: ['Painting', 'I love painting, especially playing with colours.'],
    craft: ['Crafts', 'I enjoy making things by hand with paper, glue and thread.'],
    music: ['Music', 'Music has been part of my life since my singing and dancing days.'],
    nature: ['Nature', 'Being out in nature makes me feel calm.'],
    beauty: ['Fashion & beauty', "I'm interested in both fashion and beauty. I enjoy finding a style that feels like me and noticing small details."],
    calm: ['Peaceful moments', 'I love a quiet, peaceful moment.'],
    people: ['People', "I'm curious about human behaviour and why people do what they do."],
    problems: ['Real problems', 'I love understanding a real problem properly and then making something useful to solve it.'],
  };
  const shelf = $('lw-shelf');
  const seen = new Set();
  const hearts = $('lw-hearts');
  if (hearts) hearts.innerHTML = Array.from({ length: 8 }, () => '<i><svg viewBox="0 0 24 24"><use href="#s-heart" fill="currentColor"/></svg></i>').join('');
  if (shelf) {
    const buttons = [...shelf.querySelectorAll('.lw-obj')];
    buttons.forEach((b) => b.addEventListener('click', () => {
      const [title, text] = NOTES[b.dataset.k];
      buttons.forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      b.classList.add('seen');
      const before = seen.size;
      seen.add(b.dataset.k);
      const inner = $('lw-note-inner');
      inner.innerHTML = `<p class="lw-diary-date">Note ${String([...Object.keys(NOTES)].indexOf(b.dataset.k) + 1).padStart(2, '0')} · ${title}</p><p class="lw-diary-title">${title}</p><p class="lw-diary-text">${text}</p>`;
      inner.style.animation = 'none'; void inner.offsetWidth; inner.style.animation = '';
      hearts.querySelectorAll('i').forEach((h, i) => h.classList.toggle('on', i < seen.size));
      $('lw-count-text').textContent = `${seen.size} of 8 notes opened`;
      if (seen.size === 8 && before === 7) {
        $('lw-allfound').hidden = false;
        burst(b, 14);
      }
      // on small screens, bring the note into view
      if (window.innerWidth <= 960) $('lw-note').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'nearest' });
    }));
  }

  // ---------- 04: the receipt prints the first time its diary page is opened
  const receipt = $('lw-receipt');
  if (receipt) {
    const print = () => { receipt.classList.remove('printed'); void receipt.offsetWidth; requestAnimationFrame(() => receipt.classList.add('printed')); };
    let printedOnce = false;
    if (reduced) receipt.classList.add('printed');
    else document.addEventListener('lw:page', (e) => {
      if (e.detail.id === 'lw-ch4' && !printedOnce) { printedOnce = true; print(); }
    });
    $('lw-reprint').addEventListener('click', () => (reduced ? null : print()));
  }

  // ---------- 05: the door (hover opens on desktop, tap toggles everywhere)
  const door = $('lw-door');
  if (door) door.addEventListener('click', () => {
    // every tap opens the door to the starry night (the dreams overlay follows)
    const wasOpen = door.classList.contains('open');
    door.classList.add('open');
    if (!wasOpen) burst(door, 10, 'sparkle');
  });

  // ---------- easter eggs
  function burst(el, n, kind) {
    if (reduced) return;
    const r = el.getBoundingClientRect();
    for (let i = 0; i < n; i++) {
      const s = document.createElement('span');
      s.className = 'lw-pop';
      const a = Math.random() * Math.PI * 2;
      const d = 40 + Math.random() * 70;
      s.style.left = (r.left + r.width / 2 - 8) + 'px';
      s.style.top = (r.top + r.height / 2 - 8) + 'px';
      s.style.setProperty('--dx', Math.cos(a) * d + 'px');
      s.style.setProperty('--dy', Math.sin(a) * d + 'px');
      s.style.color = ['#e7839f', '#9d86dc', '#a993e6', '#e8c45c', '#7fcca8'][i % 5];
      s.innerHTML = `<svg viewBox="0 0 24 24"><use href="#s-${kind || 'heart'}" fill="currentColor"/></svg>`;
      document.body.appendChild(s);
      setTimeout(() => s.remove(), 950);
    }
  }
  document.querySelectorAll('.lw-heart-btn').forEach((b) => b.addEventListener('click', () => burst(b, 10)));

  const moon = $('lw-moon');
  const hero = document.querySelector('.lw-hero');
  if (moon && hero) moon.addEventListener('click', () => {
    if (reduced) return;
    const s = document.createElement('span');
    s.className = 'lw-shooting';
    s.style.left = (5 + Math.random() * 30) + '%';
    s.style.top = (4 + Math.random() * 20) + '%';
    hero.appendChild(s);
    setTimeout(() => s.remove(), 1300);
  });

  // type "ayushi" anywhere: cherry blossoms fall
  let typed = '';
  document.addEventListener('keydown', (e) => {
    if ((e.target && e.target.closest && e.target.closest('input, textarea')) || !e.key || e.key.length !== 1) return;
    typed = (typed + e.key.toLowerCase()).slice(-6);
    if (typed === 'ayushi') petals();
  });
  function petals() {
    if (reduced) return;
    const cols = ['#f7b6c8', '#fbd5e1', '#e7839f', '#ffe1ea'];
    for (let i = 0; i < 36; i++) {
      const p = document.createElement('span');
      p.className = 'lw-petal';
      p.style.setProperty('--x', Math.random() * 100 + 'vw');
      p.style.setProperty('--s', 10 + Math.random() * 14 + 'px');
      p.style.setProperty('--t', 4 + Math.random() * 4 + 's');
      p.style.setProperty('--dx', (Math.random() - 0.5) * 240 + 'px');
      p.style.setProperty('--rot', (Math.random() * 720 - 360) + 'deg');
      p.style.setProperty('--c', cols[i % cols.length]);
      p.style.animationDelay = Math.random() * 2 + 's';
      p.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 2c4 4 6 8 6 12a6 6 0 0 1-12 0c0-4 2-8 6-12z" fill="currentColor"/></svg>';
      document.body.appendChild(p);
      setTimeout(() => p.remove(), 10000);
    }
  }

  // ---------- chapter progress (binder tabs on desktop, dots on mobile)
  const chapters = [...root.querySelectorAll('[data-ch]')];
  const tabs = [...document.querySelectorAll('.lw-tab')];
  const tabsWrap = $('lw-tabs');
  const mprog = $('lw-mprog');
  const dots = mprog ? [...mprog.querySelectorAll('i')] : [];
  function progress() {
    if (!tabsWrap) return;
    const mid = window.innerHeight * 0.45;
    let cur = -1;
    chapters.forEach((c, i) => { if (c.getBoundingClientRect().top < mid) cur = i; });
    const endEl = document.querySelector('.site-footer');
    const pastEnd = endEl && endEl.getBoundingClientRect().top < window.innerHeight * 0.6;
    const visible = cur >= 0 && !pastEnd;
    tabsWrap.classList.toggle('show', visible);
    if (mprog) mprog.classList.toggle('show', visible);
    tabs.forEach((t, i) => {
      if (i === cur) t.setAttribute('aria-current', 'step'); else t.removeAttribute('aria-current');
      t.classList.toggle('done', i < cur);
    });
    dots.forEach((d, i) => d.classList.toggle('on', i <= cur));
    if (mprog && cur >= 0) {
      const sp = mprog.querySelector('span');
      sp.textContent = chapters[cur].dataset.title.toLowerCase();
      sp.dataset.num = `${chapters[cur].dataset.ch} / 05`;
    }
  }
  tabs.forEach((t) => t.addEventListener('click', (e) => {
    const target = document.querySelector(t.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 60, behavior: reduced ? 'auto' : 'smooth' });
  }));

  // ---------- gentle scroll parallax for layers marked with data-depth
  const layers = [...root.querySelectorAll('.lw-hero [data-depth]')];
  const heroEl = root.querySelector('.lw-hero');
  function parallax() {
    if (reduced || !heroEl) return;
    const r = heroEl.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) return;
    const y = Math.max(0, -r.top);
    layers.forEach((l) => { l.style.transform = `translateY(${(y * parseFloat(l.dataset.depth)).toFixed(1)}px)`; });
  }

  // ---------- A peek into my dreams: stars → constellation ----------
  const DREAMS = [
    ['My dream house', 'One day, I want to buy my dream house and make it my own.'],
    ['My own brand', 'I want to start my own brand someday.'],
    ['A design leader', 'I want to become a design leader in a good company.'],
    ['The right decisions', 'I want to be strong enough to take the right decisions for my life.'],
    ['A good human', 'I want to be a good human, someone who can inspire people and is admirable.'],
    ['More to come', 'I have more dreams that I am still figuring out. This star is for them.'],
  ];
  let resetSky = null;
  const sky = $('lw-sky');
  if (sky) {
    const stars = [...sky.querySelectorAll('.lw-dstar')];
    const lines = [...sky.querySelectorAll('line[data-a]')];
    lines.forEach((l) => {
      const len = Math.hypot(l.x2.baseVal.value - l.x1.baseVal.value, l.y2.baseVal.value - l.y1.baseVal.value);
      l.style.setProperty('--len', len.toFixed(1));
    });
    // dreams unlock one at a time: only the next star glows and can be tapped
    const seenD = new Set();
    let step = 0;
    function paintSteps() {
      stars.forEach((x, k) => {
        const isNext = k === step;
        const locked = k > step;
        x.classList.toggle('is-next', isNext);
        x.classList.toggle('is-locked', locked);
        x.disabled = locked;
        x.setAttribute('aria-label', locked ? `Dream ${k + 1}, locked` : (isNext ? `Dream ${k + 1}, tap to reveal` : `Dream ${k + 1}: ${DREAMS[k][0]}`));
      });
    }
    paintSteps();
    // every visit starts fresh: nothing revealed, only the first star waiting
    const introHTML = $('lw-dream-inner').innerHTML;
    const introCount = $('lw-dream-count').textContent;
    resetSky = () => {
      seenD.clear();
      step = 0;
      stars.forEach((x) => { x.classList.remove('seen'); x.setAttribute('aria-pressed', 'false'); });
      lines.forEach((l) => l.classList.remove('on'));
      sky.classList.remove('done');
      $('lw-dream-inner').innerHTML = introHTML;
      $('lw-dream-count').textContent = introCount;
      paintSteps();
    };
    stars.forEach((st) => st.addEventListener('click', () => {
      const i = +st.dataset.i;
      if (i > step) return;
      stars.forEach((x) => x.setAttribute('aria-pressed', String(x === st)));
      st.classList.add('seen');
      seenD.add(i);
      if (i === step) { step = Math.min(step + 1, stars.length); paintSteps(); }
      const [t, txt] = DREAMS[i];
      const inner = $('lw-dream-inner');
      inner.innerHTML = `<p class="lw-dream-num">Dream ${String(i + 1).padStart(2, '0')}</p><p class="lw-dream-title">${t}</p><p class="lw-dream-text">${txt}</p>`;
      inner.style.animation = 'none'; void inner.offsetWidth; inner.style.animation = '';
      lines.forEach((l) => l.classList.toggle('on', seenD.has(+l.dataset.a) && seenD.has(+l.dataset.b)));
      const core = [0, 1, 2, 3, 4].every((k) => seenD.has(k));
      const was = sky.classList.contains('done');
      sky.classList.toggle('done', core);
      const n = [0, 1, 2, 3, 4].filter((k) => seenD.has(k)).length;
      $('lw-dream-count').textContent = core ? 'all 5 dreams revealed ✦' : `${n} of 5 dreams revealed · tap the next glowing star`;
      if (core && !was) burst(st, 12, 'sparkle');
      if (window.innerWidth <= 900) $('lw-dream-card').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'nearest' });
    }));
  }

  // ---------- "me, in three moods": photo strip viewer ----------
  const view = $('lw-booth-view');
  const frames = [...document.querySelectorAll('.lw-booth-frame')];
  if (view && frames.length) {
    const img = view.querySelector('.lw-bv-photo img');
    const mood = view.querySelector('.lw-bv-mood');
    const count = view.querySelector('.lw-bv-count');
    let idx = 0;
    let lastFocus = null;
    function showPhoto(i, swap) {
      idx = (i + frames.length) % frames.length;
      const f = frames[idx];
      const src = f.querySelector('img');
      img.src = src.getAttribute('src');
      img.alt = src.alt;
      mood.textContent = f.dataset.mood;
      count.textContent = `${idx + 1} / ${frames.length}`;
      view.setAttribute('aria-label', `Photo ${idx + 1} of ${frames.length}: ${f.dataset.mood}`);
      if (swap && !reduced) { view.classList.remove('swap'); void view.offsetWidth; view.classList.add('swap'); }
    }
    function openView(i) {
      lastFocus = document.activeElement;
      showPhoto(i, false);
      view.hidden = false;
      document.documentElement.style.overflow = 'hidden';
      if (!reduced) { view.classList.remove('flash'); void view.offsetWidth; view.classList.add('flash'); }
      view.querySelector('.lw-bv-close').focus({ preventScroll: true });
    }
    function closeView() {
      view.hidden = true;
      view.classList.remove('flash', 'swap');
      document.documentElement.style.overflow = '';
      if (lastFocus) lastFocus.focus({ preventScroll: true });
    }
    frames.forEach((f, i) => f.addEventListener('click', () => openView(i)));
    view.querySelector('.lw-bv-prev').addEventListener('click', () => showPhoto(idx - 1, true));
    view.querySelector('.lw-bv-next').addEventListener('click', () => showPhoto(idx + 1, true));
    view.querySelectorAll('[data-bv-close]').forEach((b) => b.addEventListener('click', closeView));
    document.addEventListener('keydown', (e) => {
      if (view.hidden) return;
      if (e.key === 'Escape') closeView();
      else if (e.key === 'ArrowRight') showPhoto(idx + 1, true);
      else if (e.key === 'ArrowLeft') showPhoto(idx - 1, true);
      else if (e.key === 'Tab') { // keep focus inside the viewer
        const btns = [...view.querySelectorAll('button')];
        const first = btns[0]; const last = btns[btns.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    // swipe between photos on touch
    let tx = null;
    view.addEventListener('touchstart', (e) => { tx = e.touches[0].clientX; }, { passive: true });
    view.addEventListener('touchend', (e) => {
      if (tx === null) return;
      const d = e.changedTouches[0].clientX - tx;
      if (Math.abs(d) > 40) showPhoto(idx + (d < 0 ? 1 : -1), true);
      tx = null;
    });
  }

  // ---------- chapter 01: movable polaroids ----------
  const crafts = $('lw-collage1');
  if (crafts) {
    const pics = [...crafts.querySelectorAll('.lw-polaroid')];
    const tidy = $('lw-tidy');
    let top = 10;
    const getD = (el, k) => parseFloat(el.style.getPropertyValue(k)) || 0;
    // keep the photo's centre inside the scrapbook page
    // the diary may be scaled (and on phones turned 90°): convert screen px to page px
    const zoom = () => (window.lwDiary ? window.lwDiary.zoom() : 1);
    const rot = () => (window.lwDiary && window.lwDiary.rot ? window.lwDiary.rot() : 0);
    // keep the photo's centre inside the scrapbook page (layout box, so transforms don't matter)
    function clampMove(el, dx, dy) {
      const w = el.offsetWidth;
      const h = el.offsetHeight;
      dx = Math.min(Math.max(dx, -(el.offsetLeft + w / 2)), crafts.offsetWidth - el.offsetLeft - w / 2);
      dy = Math.min(Math.max(dy, -(el.offsetTop + h / 2)), crafts.offsetHeight - el.offsetTop - h / 2);
      return [dx, dy];
    }
    function setPos(el, dx, dy) {
      el.style.setProperty('--dx', dx.toFixed(1) + 'px');
      el.style.setProperty('--dy', dy.toFixed(1) + 'px');
      if (tidy) tidy.hidden = false;
    }
    function raise(el) { top += 1; el.style.setProperty('--zi', top); }
    pics.forEach((el) => {
      let sx = 0; let sy = 0; let ox = 0; let oy = 0; let dragging = false;
      el.addEventListener('pointerdown', (e) => {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        dragging = true;
        sx = e.clientX; sy = e.clientY; ox = getD(el, '--dx'); oy = getD(el, '--dy');
        try { el.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events */ }
        el.classList.add('is-drag');
        raise(el);
        e.preventDefault();
      });
      el.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        const z = zoom();
        let mx = (e.clientX - sx) / z;
        let my = (e.clientY - sy) / z;
        if (rot()) [mx, my] = [my, -mx];
        const [dx, dy] = clampMove(el, ox + mx, oy + my);
        setPos(el, dx, dy);
      });
      const end = () => { dragging = false; el.classList.remove('is-drag'); };
      el.addEventListener('pointerup', end);
      el.addEventListener('pointercancel', end);
      // keyboard: arrows nudge the focused photo (shift = bigger steps)
      el.addEventListener('keydown', (e) => {
        const step = e.shiftKey ? 40 : 12;
        const map = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
        if (!map[e.key]) return;
        e.preventDefault();
        raise(el);
        const [dx, dy] = clampMove(el, getD(el, '--dx') + map[e.key][0], getD(el, '--dy') + map[e.key][1]);
        setPos(el, dx, dy);
      });
    });
    if (tidy) tidy.addEventListener('click', () => {
      pics.forEach((el) => { el.style.removeProperty('--dx'); el.style.removeProperty('--dy'); el.style.removeProperty('--zi'); });
      tidy.hidden = true;
    });
  }

  // ---------- "A peek into my dreams": full-screen overlay ----------
  const dreams = $('dreams');
  const openBtn = $('lw-open-dreams');
  if (dreams && openBtn) {
    let lastF = null;
    function openDreams(e, from) {
      if (e) e.preventDefault();
      lastF = document.activeElement;
      const r = (from || openBtn).getBoundingClientRect();
      // the sky blooms from the button; keep that point on screen
      const cx = Math.min(Math.max(r.left + r.width / 2, 0), window.innerWidth);
      const cy = Math.min(Math.max(r.top + r.height / 2, 0), window.innerHeight);
      dreams.style.setProperty('--ox', cx + 'px');
      dreams.style.setProperty('--oy', cy + 'px');
      if (resetSky) resetSky();
      dreams.hidden = false;
      document.documentElement.style.overflow = 'hidden';
      dreams.querySelector('.lw-dreams-scroll').scrollTop = 0;
      requestAnimationFrame(() => requestAnimationFrame(() => dreams.classList.add('is-open')));
      $('lw-close-dreams').focus({ preventScroll: true });
      startShooting();
    }
    // a shooting star every few seconds while the night sky is open
    let shootTimer = null;
    function shoot() {
      if (dreams.hidden || document.hidden) return;
      const st = document.createElement('span');
      st.className = 'lw-shooting';
      st.style.left = (Math.random() * 45) + '%';
      st.style.top = (Math.random() * 35) + '%';
      dreams.appendChild(st);
      setTimeout(() => st.remove(), 1300);
    }
    function startShooting() {
      if (reduced) return;
      clearInterval(shootTimer);
      setTimeout(shoot, 900);
      shootTimer = setInterval(shoot, 3800);
    }
    function closeDreams() {
      if (dreams.hidden) return;
      dreams.classList.remove('is-open');
      clearInterval(shootTimer);
      const done = () => {
        dreams.hidden = true;
        document.documentElement.style.overflow = '';
        if (lastF) lastF.focus({ preventScroll: true });
      };
      if (reduced) done(); else setTimeout(done, 800);
    }
    openBtn.addEventListener('click', (e) => openDreams(e));
    // opening the door shows the night sky inside, then the dreams bloom out of it
    const doorEl = $('lw-door');
    if (doorEl) doorEl.addEventListener('click', () => {
      openDreams(null, doorEl);   // straight into the starry night
    });
    $('lw-close-dreams').addEventListener('click', closeDreams);
    dreams.querySelectorAll('[data-dreams-close]').forEach((b) => b.addEventListener('click', closeDreams));
    document.addEventListener('keydown', (e) => {
      if (dreams.hidden) return;
      if (e.key === 'Escape') closeDreams();
      if (e.key === 'Tab') {
        const f = [...dreams.querySelectorAll('button, a[href]')];
        const first = f[0]; const last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }

  // ---------- dreams section: cloud bank parallax (each layer at its own speed) ----------
  const bank = document.querySelector('.lw-cloudbank');
  const bankLayers = bank ? [...bank.querySelectorAll('img')] : [];
  function cloudParallax() {
    if (!bank || reduced) return;
    const r = bank.parentElement.getBoundingClientRect();
    if (r.bottom < 0 || r.top > window.innerHeight) return;
    // 0 when the section enters from below, 1 when it leaves at the top
    const p = Math.min(1, Math.max(0, (window.innerHeight - r.top) / (window.innerHeight + r.height)));
    bankLayers.forEach((img) => {
      const sp = parseFloat(img.dataset.speed || '0.2');
      img.style.setProperty('--py', ((1 - p) * sp * 260).toFixed(1) + 'px');
    });
  }

  let ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { drawPath(); progress(); parallax(); cloudParallax(); ticking = false; });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  drawPath(); progress(); cloudParallax();
})();
