/* Family health checkups case study: the interactive illustrations.
   (The hero journey, chapter nav, console and reveals come from visit-clinic-v3.js.) */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const inView = (el, cb, opts) => {
    if (!('IntersectionObserver' in window)) { cb(true); return; }
    new IntersectionObserver((es) => es.forEach((e) => cb(e.isIntersecting)), opts || { threshold: 0.35 }).observe(el);
  };

  /* ---------- decision: during booking vs after booking ---------- */
  const cmp = document.querySelector('[data-fa-compare]');
  if (cmp) {
    const btns = cmp.querySelectorAll('[data-fa-set]');
    const cap = cmp.querySelector('[data-fa-caption]');
    const caps = {
      idea: 'The first idea: every lab shows covered and paid prices together, so picking a lab means comparing family prices too.',
      shipped: 'Shipped: the user only picks a lab for their own checkup. The family offer comes later, on the order timeline.',
    };
    let touched = false;
    const set = (mode) => {
      cmp.dataset.mode = mode;
      btns.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.faSet === mode)));
      if (cap) cap.textContent = caps[mode];
    };
    btns.forEach((b) => b.addEventListener('click', () => { touched = true; set(b.dataset.faSet); }));
    let shown = false;
    inView(cmp, (on) => {
      if (!on || shown) return;
      shown = true;
      setTimeout(() => { if (!touched) set('shipped'); }, reduce ? 0 : 2200);
    });
  }

  /* ---------- family picker: tap members, the tier, price and saving follow ----------
     Prices from the shipped screens: +1 ₹4,000 · +2 ₹6,800 · +3 ₹9,600 (₹4,000 each at full price). */
  const picker = document.querySelector('[data-fa-picker]');
  if (picker) {
    const members = Array.from(picker.querySelectorAll('button.fa-member'));
    const tiers = Array.from(picker.querySelectorAll('[data-tier]'));
    const cta = picker.querySelector('[data-fa-cta]');
    const countEl = picker.querySelector('[data-fa-count]');
    const saveEl = picker.querySelector('[data-fa-save]');
    const TOTAL = [0, 4000, 6800, 9600];
    const inr = (v) => '₹' + v.toLocaleString('en-IN');
    const paint = () => {
      const n = members.filter((m) => m.getAttribute('aria-pressed') === 'true').length;
      tiers.forEach((t) => t.classList.toggle('on', Number(t.dataset.tier) === n));
      const saving = n * 4000 - TOTAL[n];
      // same wording as the shipped sheet
      countEl.textContent = n ? `${n} member${n > 1 ? 's' : ''} selected` : 'Add family member to this visit';
      saveEl.textContent = saving > 0 ? `🎉 You are saving ₹${saving}` : 'Family pricing';
      saveEl.classList.toggle('on', saving > 0);
      cta.textContent = 'Continue';
      cta.classList.toggle('off', !n);
    };
    let touched = false;
    members.forEach((m) => m.addEventListener('click', () => {
      touched = true;
      m.setAttribute('aria-pressed', String(m.getAttribute('aria-pressed') !== 'true'));
      paint();
    }));
    paint();
    // a short demo the first time it comes into view: pick two members
    let played = false;
    inView(picker, (on) => {
      if (!on || played || reduce) return;
      played = true;
      [0, 1].forEach((k, i) => setTimeout(() => {
        if (touched) return;
        members[k].setAttribute('aria-pressed', 'true');
        paint();
      }, 900 + i * 1000));
    }, { threshold: 0.3 });
  }

  /* ---------- results: count up, grow the funnel, fill the ring ---------- */
  const countUp = (el) => {
    const end = Number(el.dataset.count);
    const dec = Number(el.dataset.dec || 0);
    const fmt = (v) => (dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-IN'));
    if (reduce) { el.textContent = fmt(end); return; }
    const t0 = performance.now();
    const step = (now) => {
      const k = Math.min(1, (now - t0) / 1400);
      el.textContent = fmt(end * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(step);
    };
    el.textContent = fmt(0);
    requestAnimationFrame(step);
  };
  document.querySelectorAll('[data-fa-funnel], [data-fa-ring]').forEach((box) => {
    let done = false;
    inView(box, (on) => {
      if (!on || done) return;
      done = true;
      box.classList.add('in');
      box.querySelectorAll('[data-count]').forEach(countUp);
    }, { threshold: 0.4 });
  });
})();

/* tall screens: scroll slowly inside the phone frame, top to bottom and back.
   Runs only while on screen, pauses on hover; reduced motion lets people scroll by hand. */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SPEED = 28; // px per second
  document.querySelectorAll('img[data-autoscroll]').forEach((img) => {
    const box = document.createElement('div');
    box.className = 'fa-scroller';
    img.parentNode.insertBefore(box, img);
    box.appendChild(img);
    const measure = () => {
      const dist = img.getBoundingClientRect().height - box.getBoundingClientRect().height;
      if (dist <= 4) { box.classList.remove('is-running'); return; }
      box.style.setProperty('--dist', `${Math.round(dist)}px`);
      box.style.setProperty('--dur', `${Math.max(8, dist / SPEED / 0.84).toFixed(1)}s`);
      if (!reduce) box.classList.add('is-running');
    };
    if (img.complete && img.naturalWidth) measure(); else img.addEventListener('load', measure, { once: true });
    window.addEventListener('resize', measure);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver((es) => es.forEach((e) => box.classList.toggle('is-paused', !e.isIntersecting)), { threshold: 0.1 }).observe(box);
    }
  });
})();
