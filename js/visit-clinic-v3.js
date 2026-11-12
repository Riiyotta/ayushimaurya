/**
 * Visit Clinic case study v3: the "one visit" story.
 * Every interaction here explains the product (visit states, the check-in
 * rule, queues underneath one visit). Motion stops for reduced-motion users.
 */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const inView = (el, cb, opts) => {
    if (!('IntersectionObserver' in window)) { cb(true); return; }
    new IntersectionObserver((entries) => entries.forEach((e) => cb(e.isIntersecting, e)), opts || { threshold: 0.35 }).observe(el);
  };

  /* ---------- hero: one visit moving through its states ---------- */
  const hero = document.querySelector('[data-hero-journey]');
  if (hero) {
    const steps = Array.from(hero.querySelectorAll('.v3-hj-track li'));
    const cap = hero.querySelector('[data-hj-caption]');
    let i = 0;
    let timer = null;
    const paint = () => {
      steps.forEach((s, k) => {
        s.classList.toggle('done', k < i);
        s.classList.toggle('now', k === i);
      });
      if (cap) cap.textContent = steps[i].dataset.cap;
    };
    paint();
    if (reduce) { i = steps.length - 1; paint(); }
    else {
      inView(hero, (on) => {
        if (on && !timer) timer = setInterval(() => { i = (i + 1) % steps.length; paint(); }, 1700);
        if (!on && timer) { clearInterval(timer); timer = null; }
      }, { threshold: 0.2 });
    }
  }

  /* ---------- bet 01: home check-in vs the 100 m rule ---------- */
  const radius = document.querySelector('[data-radius]');
  if (radius) {
    const btns = radius.querySelectorAll('[data-radius-set]');
    const caption = radius.querySelector('[data-radius-caption]');
    const copy = {
      idea: "The idea: anyone can join the queue from anywhere. The clinic can't tell who is really on the way.",
      final: 'What we shipped: check-in only opens within 100 m of the clinic, so everyone in the queue is actually nearby.'
    };
    let touched = false;
    const set = (mode) => {
      radius.classList.toggle('is-final', mode === 'final');
      btns.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.radiusSet === mode)));
      if (caption) caption.textContent = copy[mode];
    };
    btns.forEach((b) => b.addEventListener('click', () => { touched = true; set(b.dataset.radiusSet); }));
    // play the idea -> shipped transition once, the first time it's seen
    let played = false;
    inView(radius, (on) => {
      if (on && !played && !touched) {
        played = true;
        setTimeout(() => { if (!touched) set('final'); }, reduce ? 0 : 1800);
      }
    }, { threshold: 0.5 });
  }

  /* ---------- bet 02: patient view vs system view ---------- */
  const views = document.querySelector('[data-views]');
  if (views) {
    const btns = views.querySelectorAll('[data-view-set]');
    const panes = views.querySelectorAll('[data-view]');
    const lanesWrap = views.querySelector('[data-lanes]');
    const lanes = Array.from(views.querySelectorAll('.v3-lane'));
    const me = views.querySelector('[data-me]');
    let lane = 1;
    let timer = null;
    let visible = false;

    const place = () => {
      const l = lanes[lane];
      const tokens = l.querySelector('.v3-tokens');
      const last = tokens.lastElementChild;
      const base = lanesWrap.getBoundingClientRect();
      const ref = (last || tokens).getBoundingClientRect();
      const x = (last ? ref.right + 6 : ref.left) - base.left;
      const y = ref.top - base.top + ref.height / 2 - me.offsetHeight / 2;
      me.style.transform = `translate(${x}px, ${y}px)`;
      lanes.forEach((ln, k) => ln.classList.toggle('is-active', k === lane));
    };
    const stop = () => { clearInterval(timer); timer = null; };
    const start = () => {
      if (reduce || timer || !visible) return;
      timer = setInterval(() => { lane = (lane + 1) % lanes.length; place(); }, 1600);
    };
    const set = (mode) => {
      btns.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.viewSet === mode)));
      panes.forEach((p) => { p.hidden = p.dataset.view !== mode; });
      if (mode === 'system') { requestAnimationFrame(place); start(); } else stop();
    };
    btns.forEach((b) => b.addEventListener('click', () => set(b.dataset.viewSet)));
    window.addEventListener('resize', () => { if (!views.querySelector('[data-view="system"]').hidden) place(); });
    inView(views, (on) => {
      visible = on;
      if (!on) stop();
      else if (!views.querySelector('[data-view="system"]').hidden) { place(); start(); }
    }, { threshold: 0.3 });
    // system view is the default: park T-8 in its first queue straight away
    if (!views.querySelector('[data-view="system"]').hidden) {
      requestAnimationFrame(place);
      window.addEventListener('load', place);
    }
  }

  /* ---------- follow the visit: console tracks the step in view ---------- */
  const consoleWrap = document.querySelector('[data-console]');
  if (consoleWrap) {
    const items = Array.from(consoleWrap.querySelectorAll('.v3-console-list li'));
    const steps = Array.from(consoleWrap.querySelectorAll('.v3-step'));
    const paint = (n) => {
      items.forEach((it, k) => { it.classList.toggle('done', k < n); it.classList.toggle('now', k === n); });
      steps.forEach((s, k) => s.classList.toggle('is-current', k === n));
    };
    paint(0);
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) paint(Number(e.target.dataset.step)); });
      }, { rootMargin: '-45% 0px -45% 0px', threshold: 0 });
      steps.forEach((s) => io.observe(s));
    }
  }

  /* ---------- peek under the screen ---------- */
  document.querySelectorAll('[data-peek]').forEach((card) => {
    const btn = card.querySelector('.v3-flip');
    const front = card.querySelector('.front');
    const back = card.querySelector('.back');
    btn.addEventListener('click', () => {
      const on = btn.getAttribute('aria-pressed') !== 'true';
      btn.setAttribute('aria-pressed', String(on));
      btn.textContent = on ? 'What the patient sees' : "What's underneath";
      front.hidden = on;
      back.hidden = !on;
    });
  });

  /* ---------- after launch: the loop keeps going ---------- */
  const loop = document.querySelector('[data-loop]');
  if (loop) {
    const nodes = Array.from(loop.querySelectorAll('li'));
    let k = 0;
    let t = null;
    const tick = () => { nodes.forEach((n, j) => n.classList.toggle('is-on', j === k)); k = (k + 1) % nodes.length; };
    tick();
    if (!reduce) inView(loop, (on) => {
      if (on && !t) t = setInterval(tick, 1100);
      if (!on && t) { clearInterval(t); t = null; }
    });
  }


  /* ---------- illustration: one patient walking the clinic floor ---------- */
  const floor = document.querySelector('[data-floor]');
  if (floor) {
    const pts = [[30, 352], [150, 356], [170, 200], [390, 146], [580, 146], [390, 290], [580, 290], [780, 290], [780, 392]];
    const copy = [
      ['Arriving', 'Leave in 30 minutes to arrive on time'],
      ['Checked in', 'Token T-8 · via app, kiosk or front desk'],
      ['Waiting', '3 ahead of you · about 10 min'],
      ['Vitals', 'Your turn is coming up · Vitals, Room 4'],
      ['Consult', "It's your turn now · Room 4"],
      ['Testing', 'Give your blood sample · Room 1'],
      ['Testing', 'Wait for your chest X-ray · Room 8'],
      ['Collecting', 'Collect at the pharmacy counter'],
      ['Going home', 'Reports on the way · follow-up in 3 days']
    ];
    const me = floor.querySelector('[data-me]');
    const rooms = Array.from(floor.querySelectorAll('.fp-room'));
    const all = floor.querySelector('.fp-path-all');
    const done = floor.querySelector('.fp-path-done');
    const phone = floor.querySelector('.v3-floor-phone');
    const stateEl = floor.querySelector('[data-fp-state]');
    const msgEl = floor.querySelector('[data-fp-msg]');
    const bars = Array.from(floor.querySelectorAll('[data-fp-bar] li'));
    const str = (arr) => arr.map((p) => p.join(',')).join(' ');
    all.setAttribute('points', str(pts));
    let i = 0;
    let t = null;
    const paint = () => {
      const [x, y] = pts[i];
      me.style.transform = `translate(${x}px, ${y}px)`;
      done.setAttribute('points', str(pts.slice(0, i + 1)));
      rooms.forEach((r) => {
        const k = Number(r.dataset.room);
        r.classList.toggle('on', k === i);
        r.classList.toggle('done', k < i);
      });
      bars.forEach((b, k) => b.classList.toggle('on', k <= i));
      phone.classList.add('swap');
      setTimeout(() => { stateEl.textContent = copy[i][0]; msgEl.textContent = copy[i][1]; phone.classList.remove('swap'); }, reduce ? 0 : 220);
    };
    if (reduce) { i = 2; paint(); }
    else {
      paint();
      inView(floor, (on) => {
        if (on && !t) t = setInterval(() => { i = (i + 1) % pts.length; paint(); }, 2000);
        if (!on && t) { clearInterval(t); t = null; }
      }, { threshold: 0.3 });
    }
  }

  /* ---------- phones: the vertical journey lights up step by step ---------- */
  const physical = document.querySelector('.v3-physical');
  if (physical && !reduce) {
    const steps = Array.from(physical.querySelectorAll('li'));
    let k = 0;
    let t = null;
    const paint = () => steps.forEach((li, j) => { li.classList.toggle('done', j < k); li.classList.toggle('now', j === k); });
    inView(physical, (on) => {
      const mobile = window.matchMedia('(max-width: 979px)').matches;
      if (on && mobile && !t) { paint(); t = setInterval(() => { k = (k + 1) % steps.length; paint(); }, 900); }
      if ((!on || !mobile) && t) { clearInterval(t); t = null; }
    }, { threshold: 0.3 });
  }

  /* ---------- scroll reveals, staggered inside lists ---------- */
  if (!reduce && 'IntersectionObserver' in window) {
    const groups = [
      ['.v3-pain-list', 'li'], ['.v3-evo', 'li'], ['.v3-trade', ':scope > div'], ['.v3-nums', ':scope > div'],
      ['.v3-knew', 'li'], ['.v3-ways-entries', '.v3-entry'], ['.v3-real', '.v3-real-row'],
      ['.v3-reflect-list', 'li'], ['.v3-challenges', 'li'], ['.v3-touchline', 'li'], ['.v3-after', '.v3-after-row'], ['.v3-gx-list', 'li'], ['.v3-tldr-grid', '.v3-tldr-cell'], ['.v3-layer-grid', '.v3-col'], ['.v3-next', 'li']
    ];
    const targets = [];
    groups.forEach(([parent, child]) => document.querySelectorAll(parent).forEach((p) => {
      p.querySelectorAll(child).forEach((el, k) => { el.style.setProperty('--d', `${Math.min(k, 8) * 0.08}s`); targets.push(el); });
    }));
    document.querySelectorAll('.v3 .v3-h2, .v3 .v3-display, .v3-problem-card, .v3-statement, .v3-takeaway, .v3-devs, .v3-radius, .v3-views, .v3-continue, .v3-kiosk, .v3-rank, .v3-entry-card, .v3-proto').forEach((el) => targets.push(el));
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });
    targets.forEach((el) => { el.classList.add('v3-rv'); io.observe(el); });
    // safety net: never leave content hidden if the observer is delayed
    const sweep = () => targets.forEach((el) => {
      if (!el.classList.contains('in') && el.getBoundingClientRect().top < window.innerHeight * 0.95) el.classList.add('in');
    });
    let queued = false;
    window.addEventListener('scroll', () => { if (queued) return; queued = true; setTimeout(() => { queued = false; sweep(); }, 250); }, { passive: true });
    setTimeout(sweep, 1200);
  }

  /* ---------- count the launch numbers up when they arrive ---------- */
  if (!reduce) {
    document.querySelectorAll('.v3-nums b, .v3-tldr-nums b').forEach((b) => {
      const m = b.textContent.match(/^(~?)(\d+)(%?)$/);
      if (!m) return;
      const [, pre, num, suf] = m;
      const end = Number(num);
      b.textContent = `${pre}0${suf}`;
      inView(b, (on) => {
        if (!on || b.dataset.counted) return;
        b.dataset.counted = '1';
        const t0 = performance.now();
        const step = (now) => {
          const k = Math.min(1, (now - t0) / 1200);
          const eased = 1 - Math.pow(1 - k, 3);
          b.textContent = `${pre}${Math.round(end * eased)}${suf}`;
          if (k < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      }, { threshold: 0.6 });
    });
  }

  /* ---------- prototype videos: play while on screen, pause when not ---------- */
  document.querySelectorAll('[data-proto]').forEach((fig) => {
    const video = fig.querySelector('video');
    const btn = fig.querySelector('.v3-proto-btn');
    let userPaused = false;
    const setBtn = (playing) => {
      btn.dataset.state = playing ? 'playing' : 'paused';
      btn.setAttribute('aria-label', playing ? 'Pause prototype' : 'Play prototype');
    };
    const play = () => { if (video.preload === 'none') video.preload = 'auto'; const p = video.play(); if (p && p.catch) p.catch(() => setBtn(false)); };
    video.addEventListener('play', () => setBtn(true));
    video.addEventListener('pause', () => setBtn(false));
    btn.addEventListener('click', () => {
      if (video.paused) { userPaused = false; play(); } else { userPaused = true; video.pause(); }
    });
    if (reduce) return; // reduced motion: poster + play button only, never autoplay
    inView(fig, (on) => {
      if (on && !userPaused) play();
      if (!on && !video.paused) video.pause();
    }, { threshold: 0.5 });
  });

  /* ---------- in-page links glide instead of jumping ---------- */
  const headerOffset = () => {
    const header = document.querySelector('.site-header');
    const nav = document.querySelector('[data-chapter-nav]');
    return (header ? header.offsetHeight : 72) + (nav ? nav.offsetHeight + 24 : 24);
  };
  const glideTo = (target) => {
    const end = target.getBoundingClientRect().top + window.scrollY - headerOffset();
    if (reduce || document.hidden) { window.scrollTo(0, end); return; }
    const start = window.scrollY;
    const dist = end - start;
    const dur = Math.min(1100, Math.max(450, Math.abs(dist) * 0.35));
    const t0 = performance.now();
    const ease = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
    const step = (now) => {
      const k = Math.min(1, (now - t0) / dur);
      window.scrollTo(0, start + dist * ease(k));
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };
  document.querySelectorAll('main.v3 a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href').slice(1);
      const target = id && document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      glideTo(target);
      if (history.replaceState) history.replaceState(null, '', `#${id}`);
    });
  });

  /* ---------- sticky chapter nav ---------- */
  const nav = document.querySelector('[data-chapter-nav]');
  if (nav && 'IntersectionObserver' in window) {
    const links = nav.querySelectorAll('[data-nav]');
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((a) => a.classList.toggle('is-active', a.dataset.nav === e.target.dataset.chapter));
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    document.querySelectorAll('[data-chapter]').forEach((c) => io.observe(c));
  }
})();
