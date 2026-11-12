/* The diary: "Know more about me" chapters live on the pages of one big book.
   Closed → tap the cover → it swings open onto chapter 01. Index tabs, the
   arrows, arrow keys, swipes and tapping a page (right = next, left = back)
   turn the pages; ✕ / Close / Esc shut it, and it always reopens on 01.
   Two-page spreads on wide screens, one chapter at a time on tablets. On
   phones, opening it lifts the real two-page diary into a full-screen modal,
   turned to landscape (rotated 90° while the phone is held upright). */
(function () {
  const book = document.getElementById('dy-book');
  if (!book) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const single = window.matchMedia('(max-width: 1023px)');
  const phone = window.matchMedia('(max-width: 767px)');
  // phones (upright or sideways) open the diary in the landscape modal
  const modalQ = window.matchMedia('(max-width: 767px), (max-height: 520px) and (max-width: 1023px)');
  const stage = document.getElementById('lw-diary');
  let modal = false;   // the diary is showing in the full-screen modal
  let rotated = false; // ...and turned 90° because the phone is upright
  let holder = null;   // keeps the page from jumping while the diary is lifted out
  const isSingle = () => single.matches && !modal;
  const isPhone = () => phone.matches && !modal;
  const cover = document.getElementById('dy-cover');
  const spreads = [...book.querySelectorAll('.dy-spread')];
  const tabs = [...book.querySelectorAll('.dy-tab')];
  const prev = document.getElementById('dy-prev');
  const next = document.getElementById('dy-next');
  const where = document.getElementById('dy-where');
  const EASE_IN = 'cubic-bezier(0.5, 0, 0.75, 0.2)';
  const EASE_OUT = 'cubic-bezier(0.25, 0.8, 0.5, 1)';
  let cur = 0;
  let isOpen = false;
  let busy = false;
  let side = 0; // phones: 0 = left page of the chapter, 1 = right page
  const LEAVES = spreads.length * 2;

  // WAAPI with a timer fallback (background tabs can throttle onfinish)
  function play(el, frames, ms, easing) {
    return new Promise((resolve) => {
      if (reduced || !el.animate) { resolve(); return; }
      const a = el.animate(frames, { duration: ms, easing, fill: 'forwards' });
      let done = false;
      const end = () => { if (done) return; done = true; resolve(a); };
      a.onfinish = end;
      setTimeout(end, ms + 150);
    });
  }
  const clear = (...els) => els.forEach((el) => { if (!el) return; el.getAnimations().forEach((a) => a.cancel()); el.style.transform = ''; });
  const page = (sp, side) => sp.querySelector('.dy-page.' + side);

  // chapter 02's path: a hand-drawn, wandering line through the milestone icons
  // each hop has its own hand-drawn swoop: [cp1 x-offset, cp1 share of the drop, cp2 x-offset, cp2 share back up]
  // (the third hop curls into a little loop)
  const SWOOPS = [[40, 0.95, -110, 0.05], [90, 0.75, 120, 0.55], [-60, 1.45, -150, -0.45], [130, 0.45, 70, 0.95], [-30, 1.05, -120, 0.1]];
  function drawPath(ol) {
    if (!ol || !ol.offsetHeight) return;
    const pts = [...ol.querySelectorAll('.dy-path-ico')].map((ic) => {
      const li = ic.parentElement;
      return [li.offsetLeft + ic.offsetLeft + ic.offsetWidth / 2, li.offsetTop + ic.offsetTop + ic.offsetHeight / 2];
    });
    const k1 = ol.offsetWidth / 520; // swoops scale with the page width
    let d = `M${pts[0][0]} ${pts[0][1]}`;
    for (let k = 1; k < pts.length; k++) {
      const [x0, y0] = pts[k - 1];
      const [x1, y1] = pts[k];
      const [ax, ay, bx, by] = SWOOPS[(k - 1) % SWOOPS.length];
      const dy = y1 - y0;
      d += ` C${(x0 + ax * k1).toFixed(1)} ${(y0 + dy * ay).toFixed(1)}, ${(x1 + bx * k1).toFixed(1)} ${(y1 - dy * by).toFixed(1)}, ${x1.toFixed(1)} ${y1.toFixed(1)}`;
    }
    let svg = ol.querySelector('.dy-path-line');
    if (!svg) {
      svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('class', 'dy-path-line');
      svg.setAttribute('aria-hidden', 'true');
      svg.innerHTML = '<path/>';
      ol.prepend(svg);
    }
    svg.setAttribute('width', ol.offsetWidth);
    svg.setAttribute('height', ol.offsetHeight);
    svg.firstChild.setAttribute('d', d);
  }
  const drawPaths = () => book.querySelectorAll('.dy-path').forEach(drawPath);

  function refresh(sp) {
    sp.querySelectorAll('.lw-anno').forEach((a) => a.classList.add('in'));
    sp.querySelectorAll('.dy-path').forEach(drawPath);
    // on phones the receipt waits until its own page (the right one) is showing
    if (isPhone() && sp.id === 'lw-ch4' && side === 0) return;
    document.dispatchEvent(new CustomEvent('lw:page', { detail: { id: sp.id } }));
  }

  function paint() {
    spreads.forEach((sp, i) => {
      sp.classList.toggle('is-on', i === cur);
      sp.classList.toggle('show-r', i === cur && side === 1);
      sp.toggleAttribute('inert', !isOpen || i !== cur);
    });
    tabs.forEach((t, i) => {
      if (i === cur && isOpen) t.setAttribute('aria-current', 'page'); else t.removeAttribute('aria-current');
    });
    const sp = spreads[cur];
    where.innerHTML = `<b>${sp.dataset.ch}</b> / ${String(spreads.length).padStart(2, '0')} · ${sp.dataset.title.toLowerCase()}`;
    // on the last page, "next" closes the diary
    const atEnd = isPhone() ? cur * 2 + side === LEAVES - 1 : cur === spreads.length - 1;
    prev.disabled = isPhone() ? cur * 2 + side === 0 : cur === 0;
    next.setAttribute('aria-label', atEnd ? 'Close the diary' : 'Next page');
    next.classList.toggle('is-end', atEnd);
  }

  function keepInView() {
    const r = book.getBoundingClientRect();
    if (r.top < 100 || r.top > window.innerHeight * 0.5) {
      window.scrollTo({ top: r.top + window.scrollY - 124, behavior: reduced ? 'auto' : 'smooth' });
    }
  }

  // ---------- the landscape modal (phones) ----------
  function fitModal() {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    rotated = vh > vw;
    const W = rotated ? vh : vw;  // the screen, measured along the book
    const H = rotated ? vw : vh;
    book.style.setProperty('--dy-rot', rotated ? '90deg' : '0deg');
    book.style.marginBottom = '';
    const z = Math.min((W - 40) / (book.offsetWidth + 50), (H - 24) / book.offsetHeight);
    book.style.setProperty('--dy-z', z.toFixed(3));
  }
  function enterModal() {
    holder = document.createElement('div');
    holder.style.height = stage.offsetHeight + 'px';
    stage.after(holder);
    modal = true;
    stage.classList.add('is-modal');
    document.documentElement.style.overflow = 'hidden';
    fit();
    drawPaths();
  }
  function exitModal() {
    modal = false;
    stage.classList.remove('is-modal');
    book.style.removeProperty('--dy-rot');
    if (holder) { holder.remove(); holder = null; }
    document.documentElement.style.overflow = '';
    fit();
    drawPaths();
    const r = book.getBoundingClientRect();
    window.scrollTo({ top: r.top + window.scrollY - 140, behavior: 'auto' });
  }
  // two frames (with a timer fallback: hidden tabs pause animation frames)
  const nextFrame = () => new Promise((r) => { requestAnimationFrame(() => requestAnimationFrame(r)); setTimeout(r, 80); });

  // ---------- sound: a paper page-turn, made with Web Audio (no files) ----------
  // Browsers only allow audio after a click or tap, so it starts on the first gesture.
  const turnSfx = (() => {
    const AC = window.AudioContext || window.webkitAudioContext;
    let ctx = null; let noise = null;
    const wake = () => {
      if (!AC) return;
      if (!ctx) {
        ctx = new AC();
        noise = ctx.createBuffer(1, ctx.sampleRate * 0.8, ctx.sampleRate);
        const d = noise.getChannelData(0);
        for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      }
      if (ctx.state === 'suspended') ctx.resume();
    };
    ['pointerdown', 'keydown', 'touchstart'].forEach((ev) => window.addEventListener(ev, wake, { passive: true }));
    // filtered noise with a quick rise and a soft fall
    const burst = ({ at = 0, dur, vol, type = 'bandpass', f1, f2, q = 0.8 }) => {
      const t = ctx.currentTime + at;
      const src = ctx.createBufferSource(); src.buffer = noise;
      const f = ctx.createBiquadFilter(); f.type = type; f.Q.value = q;
      f.frequency.setValueAtTime(f1, t); f.frequency.exponentialRampToValueAtTime(f2, t + dur);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(vol, t + dur * 0.3);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(f).connect(g).connect(ctx.destination);
      src.start(t, Math.random() * 0.4); src.stop(t + dur + 0.02);
    };
    // play now, or as soon as the first click has unlocked audio
    const withCtx = (fn) => {
      wake();
      if (!ctx) return;
      if (ctx.state === 'running') fn();
      else ctx.resume().then(() => { if (ctx.state === 'running') fn(); }).catch(() => {});
    };
    return {
      page() {   // the page lifts (airy swish), then lands (soft flap)
        withCtx(() => {
          burst({ dur: 0.26, vol: 0.09, f1: 1400, f2: 4200, q: 0.7 });
          burst({ at: 0.2, dur: 0.12, vol: 0.12, type: 'lowpass', f1: 1600, f2: 500, q: 0.5 });
        });
      },
      cover() {  // the board swings: a deeper swish and a heavier landing
        withCtx(() => {
          burst({ dur: 0.34, vol: 0.08, f1: 700, f2: 2400, q: 0.6 });
          burst({ at: 0.3, dur: 0.16, vol: 0.16, type: 'lowpass', f1: 900, f2: 220, q: 0.5 });
        });
      },
    };
  })();

  async function open() {
    if (isOpen || busy) return;
    busy = true;
    turnSfx.cover();
    if (!modal && modalQ.matches) {
      enterModal();
      await play(stage, [{ opacity: 0 }, { opacity: 1 }], 260, EASE_OUT);
      stage.getAnimations().forEach((a) => a.cancel());
      await nextFrame();
    }
    const sp = spreads[cur];
    if (isSingle()) {
      await play(cover, [{ transform: 'rotateY(0deg)' }, { transform: 'rotateY(-90deg)', opacity: 0.6 }], 520, EASE_IN);
      book.classList.remove('is-closed');
      book.classList.add('is-open');
      clear(cover);
      isOpen = true;
      paint();
      drawPaths();
      await play(sp, [{ opacity: 0, transform: 'translateY(14px)' }, { opacity: 1, transform: 'none' }], 420, EASE_OUT);
      clear(sp);
    } else {
      const left = page(sp, 'l');
      left.style.transform = 'rotateY(90deg)';
      book.classList.remove('is-closed');
      book.classList.add('is-opening');
      await play(cover, [{ transform: 'rotateY(0deg)' }, { transform: 'rotateY(-90deg)', filter: 'brightness(0.8)' }], 560, EASE_IN);
      book.classList.add('is-open');
      isOpen = true;
      paint();
      await play(left, [{ transform: 'rotateY(90deg)', filter: 'brightness(0.8)' }, { transform: 'rotateY(0deg)', filter: 'brightness(1)' }], 560, EASE_OUT);
      clear(left, cover);
      book.classList.remove('is-opening');
    }
    refresh(sp);
    busy = false;
  }

  // closing: the page folds back, the cover swings shut over it
  async function close() {
    if (!isOpen || busy) return;
    busy = true;
    isOpen = false;
    turnSfx.cover();
    const sp = spreads[cur];
    if (isSingle()) {
      await play(sp, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(14px)' }], 300, EASE_IN);
      clear(sp);
      book.classList.remove('is-open');
      book.classList.add('is-closed');
      paint();
      keepInView();
      await play(cover, [{ transform: 'rotateY(-90deg)', opacity: 0.6 }, { transform: 'rotateY(0deg)', opacity: 1 }], 520, EASE_OUT);
      clear(cover);
    } else {
      const left = page(sp, 'l');
      await play(left, [{ transform: 'rotateY(0deg)', filter: 'brightness(1)' }, { transform: 'rotateY(90deg)', filter: 'brightness(0.8)' }], 480, EASE_IN);
      left.style.transform = 'rotateY(90deg)';
      cover.style.transform = 'rotateY(-90deg)';
      book.classList.remove('is-open');
      book.classList.add('is-closing');
      await play(cover, [{ transform: 'rotateY(-90deg)', filter: 'brightness(0.8)' }, { transform: 'rotateY(0deg)', filter: 'brightness(1)' }], 600, EASE_OUT);
      book.classList.add('is-closed');
      book.classList.remove('is-closing');
      paint();
      clear(left, cover);
    }
    // every reopening starts again from chapter 01
    cur = 0;
    side = 0;
    paint();
    book.querySelector('.dy-hint').textContent = 'open it again whenever you like ✿';
    if (modal) {
      await play(stage, [{ opacity: 1 }, { opacity: 0 }], 240, EASE_IN);
      exitModal();
      stage.getAnimations().forEach((a) => a.cancel());
    }
    cover.querySelector('.dy-cover-open').focus({ preventScroll: true });
    busy = false;
  }

  // phones: turn to any page (leaf 0–9) — the old page lifts away, the new one settles in
  async function turnTo(leaf) {
    const from = cur * 2 + side;
    if (busy || leaf === from || leaf < 0 || leaf >= LEAVES) return;
    busy = true;
    turnSfx.page();
    const fwd = leaf > from;
    const out = page(spreads[cur], side ? 'r' : 'l');
    if (fwd) await play(out, [{ transform: 'rotateY(0deg)', opacity: 1 }, { transform: 'rotateY(-75deg)', opacity: 0.3 }], 340, EASE_IN);
    else await play(out, [{ opacity: 1, transform: 'none' }, { opacity: 0.3, transform: 'translateX(24px)' }], 220, EASE_IN);
    clear(out);
    cur = Math.floor(leaf / 2);
    side = leaf % 2;
    paint();
    const inn = page(spreads[cur], side ? 'r' : 'l');
    inn.scrollTop = 0;
    inn.querySelectorAll('.dy-path').forEach(drawPath);
    if (fwd) await play(inn, [{ opacity: 0.5, transform: 'translateX(22px)' }, { opacity: 1, transform: 'none' }], 300, EASE_OUT);
    else await play(inn, [{ transform: 'rotateY(-75deg)', opacity: 0.3 }, { transform: 'rotateY(0deg)', opacity: 1 }], 380, EASE_OUT);
    clear(inn);
    refresh(spreads[cur]);
    busy = false;
  }
  // one step forward / back, whatever the layout; past the last page the diary closes
  const step = (d) => {
    const atEnd = isPhone() ? cur * 2 + side === LEAVES - 1 : cur === spreads.length - 1;
    if (d > 0 && atEnd) return close();
    return isPhone() ? turnTo(cur * 2 + side + d) : go(cur + d);
  };

  async function go(to) {
    if (!isOpen && !busy && to >= 0 && to < spreads.length) { cur = to; side = 0; await open(); return; }
    if (isPhone()) { await turnTo(to * 2); return; }
    if (busy || to === cur || to < 0 || to >= spreads.length) return;
    busy = true;
    turnSfx.page();
    const from = spreads[cur];
    const target = spreads[to];
    const fwd = to > cur;
    if (isSingle()) {
      // one page: the current page lifts away, the next one settles in
      if (fwd) {
        await play(from, [{ transform: 'rotateY(0deg)', opacity: 1 }, { transform: 'rotateY(-80deg)', opacity: 0 }], 380, EASE_IN);
      } else {
        await play(from, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateX(30px)' }], 260, EASE_IN);
      }
      clear(from);
      cur = to;
      paint();
      keepInView();
      if (fwd) await play(target, [{ opacity: 0.5, transform: 'translateX(22px)' }, { opacity: 1, transform: 'none' }], 320, EASE_OUT);
      else await play(target, [{ transform: 'rotateY(-80deg)', opacity: 0 }, { transform: 'rotateY(0deg)', opacity: 1 }], 420, EASE_OUT);
      clear(target);
    } else {
      // two pages: the turning page swings over the spine, the next spread is waiting underneath
      const lift = page(from, fwd ? 'r' : 'l');
      const land = page(target, fwd ? 'l' : 'r');
      const out = fwd ? 'rotateY(-90deg)' : 'rotateY(90deg)';
      const inn = fwd ? 'rotateY(90deg)' : 'rotateY(-90deg)';
      land.style.transform = inn;
      target.classList.add('is-under');
      await play(lift, [{ transform: 'rotateY(0deg)', filter: 'brightness(1)' }, { transform: out, filter: 'brightness(0.78)' }], 420, EASE_IN);
      lift.style.transform = out;
      target.classList.add('is-top');
      await play(land, [{ transform: inn, filter: 'brightness(0.78)' }, { transform: 'rotateY(0deg)', filter: 'brightness(1)' }], 460, EASE_OUT);
      cur = to;
      paint();
      target.classList.remove('is-under', 'is-top');
      clear(lift, land);
    }
    refresh(target);
    busy = false;
  }

  // the whole cover opens it on bigger screens; on phones only the "Open my diary" button does
  cover.addEventListener('click', (e) => {
    if (isPhone() && !e.target.closest('.dy-cover-open')) return;
    open();
  });
  book.querySelectorAll('[data-dy-close]').forEach((b) => b.addEventListener('click', close));
  tabs.forEach((t) => t.addEventListener('click', () => go(+t.dataset.go)));
  prev.addEventListener('click', () => step(-1));
  next.addEventListener('click', () => step(1));

  // arrow keys turn pages while the diary is on screen (and no popup is open)
  document.addEventListener('keydown', (e) => {
    if (!isOpen || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight' && e.key !== 'Escape')) return;
    if (e.target && e.target.closest && e.target.closest('input, textarea, .lw-polaroid, [role="dialog"]')) return;
    if (document.querySelector('.lw-dreams-modal:not([hidden]), .lw-booth-view:not([hidden])')) return;
    const r = book.getBoundingClientRect();
    if (r.bottom < window.innerHeight * 0.3 || r.top > window.innerHeight * 0.7) return;
    if (e.key === 'Escape') close();
    else step(e.key === 'ArrowRight' ? 1 : -1);
  });

  // swipe between chapters (but never while dragging a polaroid)
  let sx = null; let sy = 0;
  const area = document.getElementById('dy-spreads');
  area.addEventListener('touchstart', (e) => {
    sx = e.target.closest('.lw-polaroid, .lw-shelf') ? null : e.touches[0].clientX;
    sy = e.touches[0].clientY;
  }, { passive: true });
  area.addEventListener('touchend', (e) => {
    if (sx === null) return;
    let dx = e.changedTouches[0].clientX - sx;
    let dy = e.changedTouches[0].clientY - sy;
    sx = null;
    if (modal && rotated) [dx, dy] = [dy, -dx]; // the book is turned 90°: its x runs down the screen
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.6) step(dx < 0 ? 1 : -1);
  });

  // tap a page: the right side turns forward, the left side turns back
  // (taps on photos, buttons, links and the shelf keep doing their own thing)
  area.addEventListener('click', (e) => {
    if (!isOpen || busy) return;
    if (e.target.closest('a, button, input, textarea, .lw-polaroid, .lw-shelf, .lw-ticket-big, .lw-door-zone, .lw-receipt')) return;
    const sel = window.getSelection();
    if (sel && String(sel).length) return;
    const r = area.getBoundingClientRect();
    // turned 90°, the left page sits on top and the right page below
    const fwd = modal && rotated ? e.clientY > r.top + r.height / 2 : e.clientX > r.left + r.width / 2;
    step(fwd ? 1 : -1);
  });

  // fit the whole book (and its nav) on one screen below the sticky header
  function fit() {
    if (modal) { fitModal(); return; }
    let z = 1;
    if (!isSingle()) {
      const head = document.querySelector('.site-header');
      const top = head ? head.getBoundingClientRect().height : 72;
      z = Math.min(1, Math.max(0.55, (window.innerHeight - top - 36) / book.offsetHeight));
    }
    book.style.setProperty('--dy-z', z.toFixed(3));
    book.style.marginBottom = z < 1 ? `${(-(1 - z) * book.offsetHeight).toFixed(1)}px` : '';
  }
  fit();
  drawPaths();
  window.addEventListener('resize', () => { fit(); drawPaths(); });
  window.addEventListener('load', () => { fit(); drawPaths(); });

  paint();
  window.lwDiary = {
    open, close, go,
    zoom: () => parseFloat(book.style.getPropertyValue('--dy-z')) || 1,
    rot: () => (modal && rotated ? 90 : 0),
  };
})();
