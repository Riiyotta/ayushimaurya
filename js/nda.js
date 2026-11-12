/* NDA page: names the requested project and personalises the mail subject. */
(function () {
  const slug = new URLSearchParams(window.location.search).get('project');
  if (!slug || typeof PROJECTS === 'undefined') return;

  const project = PROJECTS.find((p) => p.slug === slug);
  if (!project) return;

  const label = document.querySelector('[data-nda-project]');
  if (label) {
    label.textContent = project.title;
    label.hidden = false;
  }

  const mail = document.querySelector('[data-nda-mail]');
  if (mail) {
    mail.href = 'mailto:ayushimaurya108@gmail.com?subject='
      + encodeURIComponent('Private walkthrough — ' + project.title);
  }

  document.title = project.title + ' — under NDA — Ayushi Maurya';
})();

/* The redacted sheet: a soft lens follows the pointer, thinning the ink bars
   just enough to suggest a document without ever making it legible. */
(function () {
  const art = document.querySelector('[data-nda-art]');
  if (!art) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const sheet = art.querySelector('.nda-art-sheet');
  const target = { x: 0, y: 0, r: 0 };
  const cur = { x: 0, y: 0, r: 0 };
  const R = 130;
  let raf = null;

  function tick() {
    cur.x += (target.x - cur.x) * 0.2;
    cur.y += (target.y - cur.y) * 0.2;
    cur.r += (target.r - cur.r) * 0.14;
    const live = document.querySelector('.nda-art-sheet');
    if (live) {
      live.style.setProperty('--px', cur.x.toFixed(1) + 'px');
      live.style.setProperty('--py', cur.y.toFixed(1) + 'px');
      live.style.setProperty('--lens', cur.r.toFixed(1) + 'px');
    }
    const moving = Math.abs(target.r - cur.r) > 0.4
      || Math.abs(target.x - cur.x) > 0.4
      || Math.abs(target.y - cur.y) > 0.4;
    raf = moving ? requestAnimationFrame(tick) : null;
  }
  function wake() { if (!raf) raf = requestAnimationFrame(tick); }

  // delegated from document so the handler survives a host re-render
  document.addEventListener('pointermove', (e) => {
    const live = document.querySelector('.nda-art-sheet');
    if (!live) return;
    const rect = live.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    if (x < 0 || y < 0 || x > rect.width || y > rect.height) { target.r = 0; wake(); return; }
    if (target.r === 0) { cur.x = x; cur.y = y; }
    target.x = x;
    target.y = y;
    target.r = R;
    wake();
  }, true);
})();
