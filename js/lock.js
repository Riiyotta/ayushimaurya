/**
 * Password gate for locked project rows on the homepage.
 * Client-side only — good enough to keep a casual visitor out, not real
 * security (anyone can read this file). Change PASSWORD below to your own.
 */
(function () {
  // CHANGE ME — the password that unlocks a "locked" project.
  const PASSWORD = 'visithealth2024';

  const modal = document.querySelector('[data-lock-modal]');
  if (!modal) return;

  const form = modal.querySelector('[data-lock-form]');
  const input = modal.querySelector('[data-lock-input]');
  const error = modal.querySelector('[data-lock-error]');
  const body = modal.querySelector('[data-lock-body]');
  let pendingHref = null;
  let pendingTarget = null;
  let lastFocused = null;

  function openModal(href, target, title) {
    pendingHref = href;
    pendingTarget = target;
    if (body) {
      body.textContent = title
        ? `"${title}" is locked. Enter the password to view it.`
        : 'Enter the password to view this case study.';
    }
    lastFocused = document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    error.hidden = true;
    input.value = '';
    input.removeAttribute('data-invalid');
    // wait a frame so the panel is laid out before focusing (avoids scroll jump)
    requestAnimationFrame(() => input.focus());
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
    pendingHref = null;
    pendingTarget = null;
    if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
  }

  // every locked row is caught here, even ones rendered after this script runs
  document.addEventListener('click', (e) => {
    const link = e.target.closest('[data-locked="true"]');
    if (!link) return;
    e.preventDefault();
    openModal(link.getAttribute('href'), link.getAttribute('target'), link.querySelector('.project-title')?.textContent);
  });

  modal.querySelectorAll('[data-lock-close]').forEach((el) => {
    el.addEventListener('click', closeModal);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (input.value === PASSWORD) {
      const href = pendingHref;
      const target = pendingTarget;
      closeModal();
      if (!href) return;
      if (target === '_blank') window.open(href, '_blank', 'noopener');
      else window.location.href = href;
      return;
    }
    error.hidden = false;
    input.setAttribute('data-invalid', 'true');
    input.value = '';
    input.focus();
    // retrigger the shake on repeated wrong attempts
    input.addEventListener('animationend', () => input.removeAttribute('data-invalid'), { once: true });
  });
})();
