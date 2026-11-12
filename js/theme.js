/* Day / Night switch for every page. The choice is shared across the site
   (sessionStorage 'site-theme', so every new visit opens in Night); the inline snippet in each <head> applies it before paint. */
(function () {
  const root = document.documentElement;
  const nav = document.querySelector('.site-header .nav');
  if (!nav) return;

  const SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  const MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';

  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'theme-toggle';
  const paint = () => {
    const night = root.dataset.theme === 'night';
    btn.innerHTML = `${night ? SUN : MOON}<span>${night ? 'Day' : 'Night'}</span>`;
    btn.setAttribute('aria-label', night ? 'Switch to day theme' : 'Switch to night theme');
  };
  btn.addEventListener('click', () => {
    root.classList.add('theme-anim');
    if (root.dataset.theme === 'night') delete root.dataset.theme; else root.dataset.theme = 'night';
    try { sessionStorage.setItem('site-theme', root.dataset.theme === 'night' ? 'night' : 'day'); } catch (e) {}
    paint();
    window.dispatchEvent(new Event('site-theme'));
    setTimeout(() => root.classList.remove('theme-anim'), 500);
  });
  paint();
  const menuBtn = nav.querySelector('.nav-menu-btn');
  nav.insertBefore(btn, menuBtn || null);
})();
