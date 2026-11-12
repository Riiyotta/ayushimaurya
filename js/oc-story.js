/* Offline doctor consultation story: theme toggle, progress bar, reveals, the pinned storyboard
   and fork chapters, flip cards, draggable notes, tabs, rounds, before/after, the slot demo,
   path screens that open at the right spot, and the zoom preview. */
(function () {
  const root = document.documentElement;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  const year = $('[data-year]');
  if (year) year.textContent = new Date().getFullYear();

  // ---------- theme ----------
  const themeBtn = $('[data-theme-toggle]');
  const themeLabel = $('[data-theme-label]');
  const paintTheme = () => {
    const day = root.dataset.theme === 'day';
    themeLabel.textContent = day ? 'Night' : 'Day';
    themeBtn.setAttribute('aria-label', day ? 'Switch to night theme' : 'Switch to day theme');
  };
  paintTheme();
  themeBtn.addEventListener('click', () => {
    if (root.dataset.theme === 'day') delete root.dataset.theme; else root.dataset.theme = 'day';
    try { sessionStorage.setItem('site-theme', root.dataset.theme === 'day' ? 'day' : 'night'); } catch (e) {}
    paintTheme();
  });

  // ---------- reveals ----------
  const rvs = $$('.rv, [data-feed]');
  if (reduce || !('IntersectionObserver' in window)) rvs.forEach((el) => el.classList.add('in'));
  else {
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    }), { threshold: 0.15, rootMargin: '0px 0px -6% 0px' });
    rvs.forEach((el) => io.observe(el));
  }
  // headings that aren't inside a .rv still get their highlight once seen
  $$('.hl').forEach((h) => { if (!h.closest('.rv') && !h.closest('.hero')) h.classList.add('in'); });

  // ---------- pinned sections: progress 0..1 through a tall section ----------
  const progressOf = (sec) => {
    const r = sec.getBoundingClientRect();
    const span = sec.offsetHeight - window.innerHeight;
    return span > 0 ? Math.min(1, Math.max(0, -r.top / span)) : 0;
  };

  const story = $('[data-story]');
  const panels = story ? $$('.panel', story) : [];
  const caps = story ? $$('[data-cap]', story) : [];
  const shots = story ? $$('[data-sp]', story) : [];
  let storyIdx = -1;
  const paintStory = () => {
    if (!story) return;
    const i = Math.min(panels.length - 1, Math.floor(progressOf(story) * panels.length * 0.999));
    if (i === storyIdx) return;
    storyIdx = i;
    panels.forEach((p, k) => { p.classList.toggle('on', k === i); p.classList.toggle('done', k < i); });
    caps.forEach((c, k) => c.classList.toggle('on', k === i));
    shots.forEach((c, k) => c.classList.toggle('on', k === i));
  };

  const fork = $('[data-fork]');
  const dotsBox = fork && $('[data-dots]', fork);
  if (dotsBox) {
    // 100 dots; about a fifth also take Self-Book, scattered through the grid
    for (let i = 0; i < 100; i += 1) {
      const d = document.createElement('i');
      d.className = 'dot';
      if (i % 5 === Math.floor(i / 10) % 5) d.classList.add('sb');
      d.style.setProperty('--d', i);
      dotsBox.appendChild(d);
    }
  }
  const forkSteps = fork ? $$('.steps button', fork) : [];
  const forkMsgs = fork ? $$('[data-msg]', fork) : [];
  const count = fork && $('[data-count]', fork);
  const countLabel = fork && $('[data-count-label]', fork);
  const COUNTS = [['100', 'of 100 doctors in the network'], ['100', 'doctors, split by two banners'], ['~20', 'of 100 doctors visible'], ['~20', 'and no way to see the rest']];
  let forkIdx = -1;
  const paintFork = (force) => {
    if (!fork) return;
    const i = force != null ? force : Math.min(3, Math.floor(progressOf(fork) * 4 * 0.999));
    if (i === forkIdx) return;
    forkIdx = i;
    fork.dataset.step = i;
    forkSteps.forEach((b, k) => b.classList.toggle('on', k === i));
    forkMsgs.forEach((m, k) => m.classList.toggle('on', k === i));
    count.textContent = COUNTS[i][0];
    countLabel.textContent = COUNTS[i][1];
  };
  forkSteps.forEach((b, k) => b.addEventListener('click', () => {
    const top = fork.getBoundingClientRect().top + window.scrollY;
    const span = fork.offsetHeight - window.innerHeight;
    window.scrollTo({ top: top + span * ((k + 0.5) / 4), behavior: reduce ? 'auto' : 'smooth' });
  }));

  // ---------- progress bar + scroll loop ----------
  const bar = $('.bar-progress');
  let ticking = false;
  const onScroll = () => {
    ticking = false;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.setProperty('--prog', max > 0 ? (window.scrollY / max).toFixed(4) : 0);
    paintStory();
    paintFork();
  };
  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();

  // ---------- flip cards ----------
  $$('[data-flip]').forEach((b) => b.addEventListener('click', () => {
    const on = b.classList.toggle('is-flipped');
    b.setAttribute('aria-pressed', on);
  }));

  // ---------- draggable notes ----------
  const board = $('[data-board]');
  if (board) {
    let drag = null;
    let z = 10;
    board.addEventListener('pointerdown', (e) => {
      const n = e.target.closest('.note');
      if (!n) return;
      const br = board.getBoundingClientRect();
      const nr = n.getBoundingClientRect();
      drag = { n, dx: e.clientX - nr.left, dy: e.clientY - nr.top, br };
      n.classList.add('drag');
      n.style.zIndex = (z += 1);
      n.setPointerCapture(e.pointerId);
    });
    board.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const { n, dx, dy, br } = drag;
      const x = Math.min(br.width - n.offsetWidth, Math.max(0, e.clientX - br.left - dx));
      const y = Math.min(br.height - n.offsetHeight, Math.max(0, e.clientY - br.top - dy));
      n.style.setProperty('--x', `${x}px`);
      n.style.setProperty('--y', `${y}px`);
    });
    const end = () => { if (drag) { drag.n.classList.remove('drag'); drag = null; } };
    board.addEventListener('pointerup', end);
    board.addEventListener('pointercancel', end);
  }

  // ---------- tabs (How Might We tray, paths) ----------
  const placeScreens = (scope) => $$('.screen[data-pos]', scope).forEach((s) => {
    const go = () => { s.scrollTop = (s.scrollHeight - s.clientHeight) * Number(s.dataset.pos); };
    const img = $('img', s);
    if (img && !img.complete) { img.loading = 'eager'; img.addEventListener('load', go, { once: true }); } else go();
  });
  $$('[data-tabs]').forEach((list) => {
    const tabs = $$('[role="tab"]', list);
    const select = (t, focus) => {
      tabs.forEach((x) => {
        const on = x === t;
        x.setAttribute('aria-selected', on);
        x.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(x.getAttribute('aria-controls'));
        panel.hidden = !on;
        if (on) placeScreens(panel);
      });
      if (focus) t.focus();
    };
    tabs.forEach((t, i) => {
      t.addEventListener('click', () => select(t));
      t.addEventListener('keydown', (e) => {
        const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
        if (!d) return;
        e.preventDefault();
        select(tabs[(i + d + tabs.length) % tabs.length], true);
      });
    });
  });
  placeScreens(document);

  // key decision cards can open a path tab on the way down
  $$('[data-open-tab]').forEach((a) => a.addEventListener('click', () => {
    const t = document.getElementById(a.dataset.openTab);
    if (t) t.click();
  }));

  // ---------- top three: before / after toggles ----------
  $$('[data-ba-seg]').forEach((seg) => {
    const art = seg.parentElement;
    const screen = $('[data-ba-screen]', art);
    const imgs = $$('[data-ba-img]', art);
    const place = (img) => {
      const go = () => { screen.scrollTop = (screen.scrollHeight - screen.clientHeight) * Number(img.dataset.baPos || 0); };
      if (img.complete) go(); else { img.loading = 'eager'; img.addEventListener('load', go, { once: true }); }
    };
    $$('[data-ba]', seg).forEach((b) => b.addEventListener('click', () => {
      $$('[data-ba]', seg).forEach((x) => x.setAttribute('aria-pressed', x === b));
      imgs.forEach((im) => { im.hidden = im.dataset.baImg !== b.dataset.ba; });
      place(imgs.find((im) => !im.hidden));
    }));
    place(imgs[0]);
  });

  // ---------- rounds ----------
  const rlist = $('[data-rounds]');
  if (rlist) {
    const btns = $$('.rbtn', rlist);
    const stages = $$('[data-round]');
    btns.forEach((b) => b.addEventListener('click', () => {
      btns.forEach((x) => x.setAttribute('aria-selected', x === b));
      stages.forEach((s) => s.classList.toggle('on', s.dataset.round === b.dataset.r));
    }));
  }

  // ---------- before / after ----------
  const twImg = $('[data-tw-img]');
  $$('[data-tw]').forEach((b) => b.addEventListener('click', () => {
    const v = b.dataset.tw;
    $$('[data-tw]').forEach((x) => x.setAttribute('aria-pressed', x === b));
    $$('[data-tw-copy]').forEach((c) => { c.hidden = c.dataset.twCopy !== v; });
    twImg.style.opacity = 0;
    setTimeout(() => {
      twImg.src = twImg.dataset[v];
      twImg.alt = v === 'after' ? 'The new consultation home' : 'The old consultation home with two banners';
      twImg.closest('.screen').scrollTop = 0;
      twImg.style.opacity = 1;
    }, reduce ? 0 : 180);
  }));

  // ---------- try it: the shipped doctor's page, with tap zones ----------
  const demo = $('[data-demo]');
  if (demo) {
    const views = $$('[data-view]', demo);
    const pick = $('[data-pick]', demo);
    const ring = $('[data-ring]', demo);
    const hint = $('[data-hint]');
    const show = (v, auto) => {
      views.forEach((x) => { x.hidden = x.dataset.view !== v; });
      demo.scrollTo({ top: v === 'self' || auto ? 0 : demo.scrollTop, behavior: 'auto' });
      if (auto) {
        hint.textContent = v === 'self' ? 'Self Book tab · tap the screen to try it' : 'Via Visit tab · tap the screen to try it';
        return;
      }
      hint.textContent = v === 'self'
        ? 'Self Book: call the centre, Visit pays from your OPD wallet, cashless letter instantly. Tap Via Visit to go back.'
        : 'Tap the greyed-out slot.';
    };
    $$('[data-go]', demo).forEach((b) => b.addEventListener('click', () => show(b.dataset.go)));

    // until someone taps it, the page flips between its two tabs on its own
    let timer = null;
    let touched = false;
    const stop = () => { clearInterval(timer); timer = null; };
    const start = () => {
      if (touched || timer) return;
      show('visit', true);
      timer = setInterval(() => show(views.find((x) => !x.hidden).dataset.view === 'visit' ? 'self' : 'visit', true), 3500);
    };
    demo.addEventListener('pointerdown', () => {
      if (touched) return;
      touched = true;
      stop();
      show('visit');
    }, true);
    new IntersectionObserver(([e]) => (e.isIntersecting ? start() : stop()), { threshold: 0.4 }).observe(demo);
    const full = $('[data-full]', demo);
    full.addEventListener('click', () => {
      demo.classList.add('tapped');
      full.classList.remove('shake'); void full.offsetWidth; full.classList.add('shake');
      pick.classList.remove('on');
      ring.classList.remove('ping'); void ring.offsetWidth; ring.classList.add('ping');
      // bring the banner into view
      const target = ring.offsetTop - demo.clientHeight * 0.55;
      if (target > demo.scrollTop) demo.scrollTo({ top: target, behavior: reduce ? 'auto' : 'smooth' });
      hint.textContent = 'That slot is taken. See the banner? Tap "Try Self Book".';
    });
    $$('[data-slot]', demo).forEach((b) => b.addEventListener('click', () => {
      ['left', 'top', 'width', 'height'].forEach((k) => { pick.style[k] = b.style[k]; });
      pick.classList.add('on');
      hint.textContent = `${b.dataset.slot} picked. Scroll down and tap Consult Now, or tap the greyed slot.`;
    }));
    $('[data-consult]', demo).addEventListener('click', () => {
      hint.textContent = pick.classList.contains('on')
        ? 'Request sent. With Via Visit, our team confirms your slot in 4 to 6 hours.'
        : 'Pick a slot first.';
    });
  }

  // ---------- zoom ----------
  const box = $('[data-zoom-box]');
  if (box) {
    const img = $('[data-zoom-img]', box);
    const cap = $('[data-zoom-cap]', box);
    let last = null;
    const close = () => { box.hidden = true; document.body.style.overflow = ''; if (last) last.focus(); };
    $$('[data-zoom]').forEach((b) => b.addEventListener('click', () => {
      last = b;
      img.src = b.dataset.zoom;
      img.alt = b.dataset.cap;
      cap.textContent = `${b.dataset.cap} · scroll inside the screen`;
      box.hidden = false;
      document.body.style.overflow = 'hidden';
      img.closest('.screen').scrollTop = 0;
      $('[data-zoom-close]', box).focus();
    }));
    $('[data-zoom-close]', box).addEventListener('click', close);
    box.addEventListener('click', (e) => { if (e.target === box) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !box.hidden) close(); });
  }
})();
