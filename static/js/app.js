// static/js/app.js - minimal client behavior for forms and UI feedback
document.addEventListener('DOMContentLoaded', function () {
  // simple submit button feedback
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function (e) {
      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        btn.disabled = true;
        const original = btn.textContent;
        btn.textContent = 'Working...';
        // re-enable after 3s if no navigation (safety)
        setTimeout(() => { btn.disabled = false; btn.textContent = original; }, 3000);
      }
    });
  });

  // optional: enable copy-to-clipboard for elements with data-copy
  document.body.addEventListener('click', function (e) {
    const t = e.target;
    if (t && t.matches('[data-copy]')) {
      const text = t.getAttribute('data-copy');
      if (!text) return;
      navigator.clipboard?.writeText(text).then(() => {
        const prev = t.textContent;
        t.textContent = 'Copied';
        setTimeout(() => t.textContent = prev, 1200);
      }).catch(() => {
        // fallback: briefly flash
        t.style.opacity = '0.6';
        setTimeout(() => t.style.opacity = '', 600);
      });
    }
  });
});