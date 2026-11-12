/* What I do: the hovered line splits at the word gap nearest the cursor and the project strip opens there.
   Moving along the line moves the split; the tile under the cursor lifts, and a pill names the project.
   While scrolling (desktop and phones) the line nearest the middle of the screen opens by itself, split near its middle;
   the images pop in one after another. */
(function () {
  const sec = document.getElementById('skills');
  if (!sec) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const touch = window.matchMedia('(max-width: 760px), (hover: none)');
  const lines = Array.from(sec.querySelectorAll('.sk-line'));
  const pill = sec.querySelector('.sk-pill');
  const pillT = sec.querySelector('.sk-pill-t');
  let open = null;
  let hovering = false;
  let lastPt = null;

  const words = (li) => Array.from(li.querySelectorAll('.sk-w'));
  // word-gap midpoints in the link's own (untransformed) coordinates
  const gaps = (li) => {
    const w = words(li);
    const out = [];
    for (let k = 1; k < w.length; k += 1) out.push((w[k - 1].offsetLeft + w[k - 1].offsetWidth + w[k].offsetLeft) / 2);
    return out;
  };
  const splitAt = (li, k) => {
    if (li.dataset.k === String(k)) return;
    li.dataset.k = k;
    const strip = li.querySelector('.sk-strip');
    const half = strip.querySelector('.sk-strip-in').offsetWidth / 2 + parseFloat(getComputedStyle(li.querySelector('.sk-link')).fontSize) * 0.1;
    words(li).forEach((w, i) => w.style.setProperty('--dx', `${i < k ? -half : half}px`));
    strip.style.setProperty('--sx', `${gaps(li)[k - 1]}px`);
  };
  // the word gap closest to the middle of the line, so any cropping is shared by both sides
  const midGap = (li) => {
    const g = gaps(li);
    const mid = li.querySelector('.sk-link').offsetWidth / 2;
    let k = 1;
    g.forEach((gx, i) => { if (Math.abs(gx - mid) < Math.abs(g[k - 1] - mid)) k = i + 1; });
    return k;
  };
  const unsplit = (li) => {
    delete li.dataset.k;
    words(li).forEach((w) => w.style.removeProperty('--dx'));
    li.classList.remove('is-live');
    const home = li.querySelector('.sk-link');
    if (home.dataset.home) home.href = home.dataset.home;
    home.removeAttribute('target');
    clearTimeout(li._live);
    li.querySelector('.sk-strip-in').style.removeProperty('--nx');
    li.querySelectorAll('.sk-tile').forEach((t) => {
      t.classList.remove('is-hot');
      ['--s', '--lift', '--rz'].forEach((v) => t.style.removeProperty(v));
    });
  };
  const playVideos = (li, on) => li.querySelectorAll('video').forEach((v) => {
    if (!on) { v.pause(); return; }
    if (v.preload !== 'auto') {
      v.preload = 'auto';
      if (v.dataset.start) v.addEventListener('loadedmetadata', () => { v.currentTime = v.duration * Number(v.dataset.start); }, { once: true });
      v.load();
    }
    v.play().catch(() => {});
  });

  const set = (li, byHover) => {
    if (li === open) { pill.classList.toggle('on', !!li && !!byHover && !touch.matches); return; }
    if (open) { unsplit(open); playVideos(open, false); }
    open = li;
    lines.forEach((l) => l.classList.toggle('is-open', l === li));
    sec.classList.toggle('has-open', !!li);
    if (li) {
      pillT.textContent = li.querySelector('.sk-link').dataset.proj;
      playVideos(li, true);
      clearTimeout(li._live);
      li._live = setTimeout(() => li.classList.add('is-live'), 650);
    }
    pill.classList.toggle('on', !!li && !!byHover && !touch.matches);
  };

  const track = (li, e) => {
    const link = li.querySelector('.sk-link');
    const x = e.clientX - link.getBoundingClientRect().left;
    const g = gaps(li);
    let k = Number(li.dataset.k) || 0;
    // while the cursor is over the open strip, keep the split where it is so the images don't run away
    const half = li.querySelector('.sk-strip-in').offsetWidth / 2;
    if (!(open === li && k && Math.abs(x - g[k - 1]) < half + 8)) {
      k = 1;
      g.forEach((gx, i) => { if (Math.abs(gx - x) < Math.abs(g[k - 1] - x)) k = i + 1; });
    }
    hovering = true;
    set(li, true);
    splitAt(li, k);
    // dock: the tile nearest the cursor grows and lifts, and every tile tilts toward the cursor
    const tiles = Array.from(li.querySelectorAll('.sk-tile'));
    const tw = tiles[0].offsetWidth;
    let near = null, nd = Infinity;
    tiles.forEach((t) => {
      const r = t.getBoundingClientRect();
      const dx = e.clientX - (r.left + r.width / 2);
      const dy = e.clientY - (r.top + r.height / 2);
      const pull = Math.max(0, 1 - Math.abs(dx) / (tw * 1.6));
      t.style.setProperty('--s', (1 + pull * 0.16).toFixed(3));
      t.style.setProperty('--lift', pull.toFixed(3));
      t.style.setProperty('--rz', `${Math.max(-6, Math.min(6, dx / tw * 4 + dy / tw * 1.5)).toFixed(1)}deg`);
      if (Math.abs(dx) < nd) { nd = Math.abs(dx); near = t; }
    });
    const hot = nd < tw * 0.6 ? near : null;
    tiles.forEach((t) => t.classList.toggle('is-hot', t === hot));
    // a tile from a different project names it in the pill, and a click goes there
    const name = (hot && hot.dataset.name) || link.dataset.proj;
    if (pillT.textContent !== name) pillT.textContent = name;
    link.href = (hot && hot.dataset.href) || link.dataset.home;
    if (/^https?:/.test(link.getAttribute('href'))) { link.target = '_blank'; link.rel = 'noopener'; } else link.removeAttribute('target');
  };

  lines.forEach((li) => {
    const a = li.querySelector('.sk-link');
    a.dataset.home = a.getAttribute('href');
    li.addEventListener('mousemove', (e) => { if (!touch.matches) track(li, e); });
    li.addEventListener('mouseleave', () => {
      if (touch.matches) return;
      hovering = false;
      if (open === li) { unsplit(li); set(null); }
      // back to the scroll-picked line unless the cursor went straight onto another one
      setTimeout(() => { if (!hovering) onScroll(); }, 150);
    });
    // the whole row is clickable, not just the words
    li.addEventListener('click', (e) => { if (!a.contains(e.target)) a.click(); });
    a.addEventListener('focus', () => {
      set(li);
      splitAt(li, midGap(li));
    });
    a.addEventListener('blur', () => { if (!touch.matches && open === li) { unsplit(li); set(null); } });
  });
  window.addEventListener('mousemove', (e) => { lastPt = { x: e.clientX, y: e.clientY }; }, { passive: true });
  document.addEventListener('mouseleave', () => { lastPt = null; hovering = false; });
  sec.addEventListener('mousemove', (e) => {
    pill.style.setProperty('--mx', `${e.clientX}px`);
    pill.style.setProperty('--my', `${e.clientY}px`);
  });
  window.addEventListener('resize', () => { if (open) { const k = open.dataset.k; delete open.dataset.k; if (k) splitAt(open, Number(k)); } });

  // scroll: gentle sideways drift, alternating per line; on phones also pick the middle line
  let ticking = false;
  function onScroll() {
    ticking = false;
    const r = sec.getBoundingClientRect();
    const vh = window.innerHeight;
    if (r.bottom < 0 || r.top > vh) { if (open && !hovering) { unsplit(open); set(null); } return; }
    if (!reduce) {
      const k = (vh / 2 - (r.top + r.height / 2)) / vh; // about -1..1 across the section
      lines.forEach((l, i) => l.style.setProperty('--px', `${(i % 2 ? -1 : 1) * k * 4}vw`));
    }
    // still hovering only if the pointer is really over a line after the scroll
    if (hovering) {
      const el = lastPt && document.elementFromPoint(lastPt.x, lastPt.y);
      if (el && el.closest('.sk-line')) return;
      hovering = false;
    }
    let best = null, d = Infinity;
    lines.forEach((l) => {
      const lr = l.querySelector('.sk-w').getBoundingClientRect();
      const dd = Math.abs(lr.top + lr.height / 2 - vh * 0.45);
      if (dd < d) { d = dd; best = l; }
    });
    const pick = d < vh * 0.3 ? best : null;
    set(pick, false);
    if (pick) splitAt(pick, midGap(pick));
  };
  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  touch.addEventListener?.('change', () => { if (open) unsplit(open); set(null); onScroll(); });
  onScroll();
})();

/* decode the tile images before the section arrives, so the first hover shows them straight away */
(function () {
  const sec = document.getElementById('skills');
  if (!sec || !('IntersectionObserver' in window)) return;
  const io = new IntersectionObserver((es) => {
    if (!es.some((e) => e.isIntersecting)) return;
    io.disconnect();
    sec.querySelectorAll('.sk-tile img').forEach((img) => { if (img.decode) img.decode().catch(() => {}); });
  }, { rootMargin: '800px 0px' });
  io.observe(sec);
})();

/* phones in Low Power Mode refuse autoplay: the first touch retries the videos that should be playing
   (the open skill line and the work box walkthrough) */
(function () {
  const retry = () => document.querySelectorAll('.sk-line.is-open video, #work video[autoplay]').forEach((v) => {
    const r = v.getBoundingClientRect();
    if (v.paused && r.bottom > 0 && r.top < window.innerHeight) { const p = v.play(); if (p && p.catch) p.catch(() => {}); }
  });
  ['touchstart', 'touchend', 'click'].forEach((t) => document.addEventListener(t, retry, { passive: true }));
})();
