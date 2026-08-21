/* GourmetPOS ERP - Cliente API Global */

const API_BASE = window.location.origin + '/api';

const API = {
  async get(path) {
    const token = localStorage.getItem('gourmetpos_cliente_token');
    const r = await fetch(API_BASE + path, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined);
    if (!r.ok) throw new Error(`Error ${r.status}: ${r.statusText}`);
    return r.json();
  },

  async post(path, body = {}) {
    const token = localStorage.getItem('gourmetpos_cliente_token') || localStorage.getItem('gourmetpos_registro_token');
    const r = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || `Error ${r.status}`);
    }
    return r.json();
  },

  async put(path, body = {}) {
    const r = await fetch(API_BASE + path, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || `Error ${r.status}`);
    }
    return r.json();
  },

  async delete(path) {
    const r = await fetch(API_BASE + path, { method: 'DELETE' });
    if (!r.ok) throw new Error(`Error ${r.status}`);
    return r.json();
  },
};

/* ── TOAST NOTIFICATIONS ── */
function toast(msg, tipo = 'info', duracion = 3000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  t.className = `toast ${tipo}`;
  t.innerHTML = `<span>${icons[tipo] || ''}</span><span>${msg}</span>`;
  container.appendChild(t);
  setTimeout(() => t.remove(), duracion);
}

/* ── FORMATO ── */
const fmt = (n, sym = '$') => `${sym} ${Math.round(+n || 0).toLocaleString('es-CO')}`;
const fmtFecha = (iso) => new Date(iso).toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' });

/* ── BADGES ── */
const BADGE = {
  libre:        '<span class="badge badge-libre">Libre</span>',
  ocupada:      '<span class="badge badge-ocupada">Ocupada</span>',
  cuenta:       '<span class="badge badge-cuenta">Cuenta</span>',
  pendiente:    '<span class="badge badge-pendiente">Pendiente</span>',
  en_preparacion: '<span class="badge badge-preparacion">Preparando</span>',
  listo:        '<span class="badge badge-listo">Listo</span>',
  entregado:    '<span class="badge badge-entregado">Entregado</span>',
  cancelado:    '<span class="badge badge-entregado">Cancelado</span>',
};

/* ── MODAL HELPER ── */
function showModal(id) {
  document.getElementById(id)?.classList.add('show');
}
function hideModal(id) {
  document.getElementById(id)?.classList.remove('show');
}

/* ── WEBSOCKET LIVE UPDATES ── */
function connectWS(onMessage) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); } catch {}
  };
  ws.onclose = () => setTimeout(() => connectWS(onMessage), 3000);
  return ws;
}

/* ── SIDEBAR ACTIVE LINK ── */
document.addEventListener('DOMContentLoaded', () => {
  const page = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar-nav a').forEach(a => {
    if (a.getAttribute('href') === page) a.classList.add('active');
  });
});

// Expose common helpers to global scope for legacy pages
window.API = API;
window.fmt = fmt;
window.fmtFecha = fmtFecha;
window.toast = toast;
window.BADGE = BADGE;
window.showModal = showModal;
window.hideModal = hideModal;
window.connectWS = connectWS;
