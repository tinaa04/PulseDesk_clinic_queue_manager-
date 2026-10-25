// Small progressive-enhancement helpers; authoritative state remains in Flask/SQLite.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type="submit"],button:not([type])');
    if (btn && !form.action.includes('/visit/')) { btn.dataset.originalText = btn.textContent; btn.textContent = 'Working…'; }
  }));
  document.querySelectorAll('[data-confirm]').forEach(el => el.addEventListener('click', e => {
    if (!confirm(el.dataset.confirm)) e.preventDefault();
  }));
});
