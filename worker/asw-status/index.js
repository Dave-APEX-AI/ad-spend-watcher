// asw-status — Cloudflare Worker backing the VA dashboard CRM sync.
//
// Storage model: single KV key `state_v1` holding
//   { [companyId]: { status, notes, updatedAt } }
// Concurrency: last-write-wins per companyId. Fine at this volume (2 users / 55 companies).
//
// Endpoints
//   GET  /            -> { state, ts }
//   POST /            -> body { companyId, status?, notes? } -> { ok, companyId, entry }
//   OPTIONS /         -> CORS preflight
//
// Security: Origin allowlist + strict body validation. See CLAUDE.md for threat model.

const ALLOWED_ORIGINS = [
  'https://dave-apex-ai.github.io',
  'http://localhost:8080',
  'http://127.0.0.1:8080',
  'null' // file:// during local tests
];

const VALID_STATUSES = new Set([
  'not_contacted', 'contacted', 'replied', 'booked', 'passed'
]);

const STATE_KEY = 'state_v1';
const MAX_NOTES_LEN = 2000;
const COMPANY_ID_RE = /^[a-zA-Z0-9_\-:.]{1,64}$/;

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin'
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) }
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method === 'GET' && url.pathname === '/') {
      const raw = await env.STATUS_KV.get(STATE_KEY);
      const state = raw ? JSON.parse(raw) : {};
      return json({ state, ts: Date.now() }, 200, origin);
    }

    if (request.method === 'POST' && url.pathname === '/') {
      if (!ALLOWED_ORIGINS.includes(origin)) {
        return json({ error: 'origin not allowed' }, 403, origin);
      }

      let body;
      try { body = await request.json(); }
      catch (e) { return json({ error: 'invalid json' }, 400, origin); }

      const { companyId, status, notes } = body || {};

      if (!companyId || typeof companyId !== 'string' || !COMPANY_ID_RE.test(companyId)) {
        return json({ error: 'invalid companyId' }, 400, origin);
      }
      if (status !== undefined && !VALID_STATUSES.has(status)) {
        return json({ error: 'invalid status' }, 400, origin);
      }
      if (notes !== undefined && (typeof notes !== 'string' || notes.length > MAX_NOTES_LEN)) {
        return json({ error: 'invalid notes' }, 400, origin);
      }

      const raw = await env.STATUS_KV.get(STATE_KEY);
      const state = raw ? JSON.parse(raw) : {};
      const prev = state[companyId] || {};
      state[companyId] = {
        status: status ?? prev.status ?? 'not_contacted',
        notes: notes ?? prev.notes ?? '',
        updatedAt: Date.now()
      };
      await env.STATUS_KV.put(STATE_KEY, JSON.stringify(state));

      return json({ ok: true, companyId, entry: state[companyId] }, 200, origin);
    }

    return json({ error: 'not found' }, 404, origin);
  }
};
