// ---------- CSRF ----------
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? m.pop() : '';
}
const CSRF = getCookie('csrftoken');

function trackEvent(name, props = {}) {
  if (typeof window.plausible === 'function') {
    window.plausible(name, { props });
  }
}

// ---------- Modal ----------
function initModals() {
  const dlg  = document.getElementById('app-modal');
  const body = document.getElementById('modal-body');
  if (!dlg || !body) return;

  // Open any link with data-modal-open
  document.addEventListener('click', async (e) => {
    const trigger = e.target.closest('[data-modal-open]');
    if (!trigger) return;

    e.preventDefault();

    const href = trigger.getAttribute('href');
    const url  = new URL(href, window.location.origin);
    url.searchParams.set('partial','1');

    const res  = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' }});
    const html = await res.text();

    body.innerHTML = html;
    dlg.showModal();

    // Ensure form posts to canonical endpoint (without ?partial)
    const form = body.querySelector('form');
    if (form) {
      const actionUrl = new URL(href, window.location.origin);
      actionUrl.searchParams.delete('partial');
      form.setAttribute('action', actionUrl.toString());
      if (!form.getAttribute('method')) form.setAttribute('method', 'POST');
      wireModalForm(body, dlg);
    }

    // Also wire any [data-modal-close] in the freshly inserted content
    body.addEventListener('click', onScopedCloseClick, { once: true });
  });

  // ESC closes
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') dlg.close();
  });
}

function onScopedCloseClick(e) {
  const btn = e.target.closest('[data-modal-close]');
  if (!btn) return;
  const dlg = document.getElementById('app-modal');
  if (dlg && typeof dlg.close === 'function') dlg.close();
}

function enhanceModalForms(scope, dlg) {
  // Optional: live color preview for column rename/create
  const colorInput = scope.querySelector('input[type="color"][name$="color"]');
  if (!colorInput) return;

  const previewNode =
    scope.querySelector('.column-head') ||
    document.querySelector('.column-head') ||
    dlg;

  const apply = (val) => val && previewNode.style.setProperty('--col-color', val);
  apply(colorInput.value);
  colorInput.addEventListener('input', (e) => apply(e.target.value));
}

function wireModalForm(scope, dlg) {
  const form = scope.querySelector('form');
  if (!form) return;

  // Make sure any Cancel button won't submit the form
  scope.querySelectorAll('[data-modal-close]').forEach((b) => {
    if (!b.getAttribute('type')) b.setAttribute('type', 'button');
  });

  enhanceModalForms(scope, dlg);

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();

    try {
      const res = await fetch(form.action || window.location.href, {
        method: (form.method || 'POST').toUpperCase(),
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': CSRF,
        },
        body: new FormData(form),
      });

      // Success via 204 or redirect
      if (res.status === 204 || res.redirected) {
        dlg.close();
        window.location.reload();
        return;
      }

      const html = await res.text();

      // Validation error: re-render form inside modal and re-wire
      if (res.status === 200 && html.includes('<form')) {
        scope.innerHTML = html;

        // keep cancel buttons as non-submit
        scope.querySelectorAll('[data-modal-close]').forEach((b) => {
          if (!b.getAttribute('type')) b.setAttribute('type', 'button');
        });

        wireModalForm(scope, dlg);
        return;
      }

      // Fallback: close and reload
      dlg.close();
      window.location.reload();
    } catch (err) {
      console.error('[modal] submit failed:', err);
    }
  }, { once: true });
}

// ---------- Drag & Drop ----------
let draggedEl = null;

function ensurePlaceholder(listEl) {
  const cards = listEl.querySelectorAll('.task-card');
  const empty = listEl.querySelector('.empty');
  if (cards.length && empty) empty.remove();
  if (!cards.length && !empty) {
    const li = document.createElement('li');
    li.className = 'empty';
    li.style.cssText = 'padding:8px 10px; opacity:.7;';
    li.innerHTML = '<em>No tasks</em>';
    listEl.appendChild(li);
  }
}

function initDnD() {
  document.addEventListener('dragstart', (e) => {
    const card = e.target.closest('.task-card[draggable="true"]');
    if (!card) return;
    draggedEl = card;
    card.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', card.dataset.taskId || '');
  });

  document.addEventListener('dragend', () => {
    if (draggedEl) draggedEl.classList.remove('dragging');
    draggedEl = null;
  });

  document.addEventListener('dragover', (e) => {
    const zone = e.target.closest('.dropzone');
    if (!zone) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    zone.classList.add('drop-hover');
  });

  document.addEventListener('dragleave', (e) => {
    const zone = e.target.closest('.dropzone');
    if (zone) zone.classList.remove('drop-hover');
  });

  document.addEventListener('drop', async (e) => {
    const zone = e.target.closest('.dropzone');
    if (!zone) return;
    e.preventDefault();
    zone.classList.remove('drop-hover');
    if (!draggedEl) return;

    const taskId = draggedEl.dataset.taskId;
    const columnId = zone.dataset.columnId;
    if (!taskId || !columnId) return;

    const fromList = draggedEl.parentElement;
    zone.appendChild(draggedEl);
    ensurePlaceholder(fromList);
    ensurePlaceholder(zone);

    try {
      const resp = await fetch(`/tasks/${taskId}/move/${columnId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': CSRF,
          'X-Requested-With': 'XMLHttpRequest',
        },
      });
      if (!resp.ok) throw new Error('Move failed');
      trackEvent('task-moved', { column: columnId });
    } catch (err) {
      fromList.appendChild(draggedEl);
      ensurePlaceholder(fromList);
      ensurePlaceholder(zone);
      console.error(err);
      alert('Could not move task. Please try again.');
    }
  });
}

// ---------- Hotkeys (single handler) ----------
document.addEventListener('keydown', (e) => {
  if (e.target && /input|textarea|select|button/i.test(e.target.tagName)) return;
  const k = (e.key || '').toLowerCase();
  if (k !== 'c' && k !== 'n') return;

  const el =
    document.getElementById(k === 'c' ? 'link-add-column' : 'link-add-task') ||
    document.querySelector(`[data-hotkey="${k}"]`);

  if (el) {
    e.preventDefault();
    el.click();
  }
});

// ---------- Filters: auto-apply on change ----------
document.addEventListener('DOMContentLoaded', () => {
  const f = document.querySelector('form.filters');
  if (f) f.addEventListener('change', () => f.submit());
});

// ---------- Boot ----------
document.addEventListener('DOMContentLoaded', () => {
  initModals();
  initDnD();
});

window.trackEvent = trackEvent;
