/**
 * Shared behavior: mobile nav toggle. Included on every page.
 */
(function () {
  const menuBtn = document.querySelector('[data-menu-toggle]');
  const mobileMenu = document.querySelector('[data-mobile-menu]');
  if (!menuBtn || !mobileMenu) return;

  function closeMenu() {
    menuBtn.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('data-open', 'false');
    document.body.style.overflow = '';
  }

  function openMenu() {
    menuBtn.setAttribute('aria-expanded', 'true');
    mobileMenu.setAttribute('data-open', 'true');
    document.body.style.overflow = 'hidden';
  }

  menuBtn.addEventListener('click', () => {
    const isOpen = menuBtn.getAttribute('aria-expanded') === 'true';
    isOpen ? closeMenu() : openMenu();
  });

  mobileMenu.querySelectorAll('a').forEach((a) => a.addEventListener('click', closeMenu));

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menuBtn.getAttribute('aria-expanded') === 'true') {
      closeMenu();
      menuBtn.focus();
    }
  });
})();

/**
 * Dismissible overlay, mobile only: nudges visitors toward desktop for a
 * good experience. An overlay rather than a toast so it can't be scrolled
 * past unnoticed. Dismissing it only holds for this browser session — close
 * the site and open it again and it shows once more.
 */
(function () {
  // home page only — the name-drag effect it points to lives there, so no
  // other page (case studies, resume, more work) shows this prompt
  if (!document.getElementById('home-project-list') && !document.getElementById('pbox')) return;

  const DISMISS_KEY = 'desktop-hint-dismissed';

  let dismissed = false;
  try { dismissed = sessionStorage.getItem(DISMISS_KEY) === '1'; } catch (e) { dismissed = false; }
  if (dismissed) return;

  // checked at display time, not at parse time, so a viewport that only
  // settles after load (e.g. orientation change, a late resize) still counts
  function maybeShow() {
    if (!window.matchMedia('(max-width: 979px)').matches) return;
    if (document.querySelector('.desktop-hint')) return;

    const hint = document.createElement('div');
    hint.className = 'desktop-hint';
    hint.setAttribute('role', 'dialog');
    hint.setAttribute('aria-modal', 'true');
    hint.innerHTML = `
      <div class="desktop-hint-backdrop"></div>
      <div class="desktop-hint-panel">
        <button class="desktop-hint-close" type="button" aria-label="Dismiss">×</button>
        <p class="desktop-hint-icon" aria-hidden="true">👀</p>
        <p class="desktop-hint-text">Drag through my name, learn about me. Open it on desktop tho, way better fr.</p>
      </div>
    `;
    document.body.appendChild(hint);
    hint.setAttribute('data-mounted', 'true');
    document.body.style.overflow = 'hidden';

    let autoDismissTimer = null;

    // persist: true only when the reader explicitly closed it — an auto
    // timeout just hides this showing, it isn't "never show me this again".
    // Either way it's sessionStorage, not localStorage: closing the site
    // and opening it again (a new session) shows it once more.
    function dismiss(persist) {
      clearTimeout(autoDismissTimer);
      hint.setAttribute('data-visible', 'false');
      document.body.style.overflow = '';
      if (persist) {
        try { sessionStorage.setItem(DISMISS_KEY, '1'); } catch (e) { /* private mode, etc. */ }
      }
      setTimeout(() => hint.remove(), 300);
    }

    hint.querySelector('.desktop-hint-close').addEventListener('click', () => dismiss(true));
    hint.querySelector('.desktop-hint-backdrop').addEventListener('click', () => dismiss(true));
    requestAnimationFrame(() => hint.setAttribute('data-visible', 'true'));
    autoDismissTimer = setTimeout(() => dismiss(false), 10000);
  }

  setTimeout(maybeShow, 500);
})();
