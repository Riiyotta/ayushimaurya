/* More Work grid: each card tilts gently toward the pointer and a soft light follows it.
   Mouse / pen only; skipped when the visitor prefers reduced motion. */
(function () {
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.mw-item').forEach((card) => {
    let raf = 0;
    card.addEventListener('pointermove', (e) => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width;
      const y = (e.clientY - r.top) / r.height;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        card.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
        card.style.setProperty('--my', (y * 100).toFixed(1) + '%');
        if (fine && !reduced) {
          card.style.setProperty('--ry', ((x - 0.5) * 6).toFixed(2) + 'deg');
          card.style.setProperty('--rx', ((0.5 - y) * 6).toFixed(2) + 'deg');
        }
      });
    });
    card.addEventListener('pointerleave', () => {
      cancelAnimationFrame(raf);
      card.style.setProperty('--rx', '0deg');
      card.style.setProperty('--ry', '0deg');
    });
  });
})();

/* walkthrough videos: play while the card is on screen (and not for reduced motion).
   Phones in Low Power Mode refuse autoplay, so the first touch on the page retries the ones in view. */
(function () {
  const vids = [...document.querySelectorAll('.mw-vid')];
  if (!vids.length || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const inView = new Set();
  const play = (v) => { v.preload = 'auto'; const p = v.play(); if (p && p.catch) p.catch(() => {}); };
  if (!('IntersectionObserver' in window)) { vids.forEach(play); return; }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { inView.add(e.target); play(e.target); } else { inView.delete(e.target); e.target.pause(); }
    });
  }, { threshold: 0.25 });
  vids.forEach((v) => io.observe(v));
  const retry = () => inView.forEach((v) => { if (v.paused) play(v); });
  ['touchstart', 'touchend', 'click'].forEach((t) => document.addEventListener(t, retry, { passive: true }));
})();
