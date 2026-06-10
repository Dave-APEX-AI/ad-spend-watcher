// caillte-leads — Cloudflare Worker capturing missed-call audit leads.
//
// Storage model: single KV key `leads_v1` holding an append-only array of
//   { name, email, phone, result:{job,miss,days,conv,lostYear,lostMonth},
//     trade, utm_source, utm_medium, utm_campaign, page, ts }
//
// Endpoints
//   POST /lead          -> body {lead}            -> { ok, count }
//   GET  /leads?token=  -> CSV export (admin)     -> text/csv
//   OPTIONS *           -> CORS preflight
//
// Security: Origin allowlist for POST, strict validation + caps, admin token
// (env.ADMIN_TOKEN secret) for export. Mirrors worker/asw-status threat model.

const ALLOWED_ORIGINS = [
  'https://www.caillteai.com',
  'https://caillteai.com',
  'https://dave-apex-ai.github.io',
  'http://localhost:8080',
  'http://127.0.0.1:8080',
  'null' // file:// during local tests
];

const LEADS_KEY = 'leads_v1';
const MAX_LEADS = 50000;       // hard cap on stored array
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PHONE_RE = /^[+0-9()\-\s]{6,24}$/;

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
    status, headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) }
  });
}
const clean = (v, max) => (typeof v === 'string' ? v.slice(0, max) : '');
function num(v) { const n = Number(v); return Number.isFinite(n) ? n : 0; }

function validResult(r) {
  return r && typeof r === 'object';
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    // ── Capture a lead ──────────────────────────────────────────────────
    if (request.method === 'POST' && url.pathname === '/lead') {
      if (!ALLOWED_ORIGINS.includes(origin)) {
        return json({ error: 'origin not allowed' }, 403, origin);
      }
      let body;
      try { body = await request.json(); }
      catch (e) { return json({ error: 'invalid json' }, 400, origin); }

      const email = clean(body.email, 254).trim();
      const phone = clean(body.phone, 24).trim();
      if (!email && !phone) {
        return json({ error: 'email or phone required' }, 400, origin);
      }
      if (email && !EMAIL_RE.test(email)) return json({ error: 'invalid email' }, 400, origin);
      if (phone && !PHONE_RE.test(phone)) return json({ error: 'invalid phone' }, 400, origin);

      const r = validResult(body.result) ? body.result : {};
      const lead = {
        name: clean(body.name, 120).trim(),
        email, phone,
        result: {
          job: num(r.job), miss: num(r.miss), days: num(r.days), conv: num(r.conv),
          lostYear: num(r.lostYear), lostMonth: num(r.lostMonth)
        },
        trade: clean(body.trade, 40),
        utm_source: clean(body.utm_source, 60),
        utm_medium: clean(body.utm_medium, 60),
        utm_campaign: clean(body.utm_campaign, 80),
        page: clean(body.page, 300),
        ts: Date.now()
      };

      const raw = await env.LEADS_KV.get(LEADS_KEY);
      const leads = raw ? JSON.parse(raw) : [];
      if (leads.length >= MAX_LEADS) leads.shift();
      leads.push(lead);
      await env.LEADS_KV.put(LEADS_KEY, JSON.stringify(leads));

      return json({ ok: true, count: leads.length }, 200, origin);
    }

    // ── Admin CSV export ────────────────────────────────────────────────
    if (request.method === 'GET' && url.pathname === '/leads') {
      const token = url.searchParams.get('token') || '';
      if (!env.ADMIN_TOKEN || token !== env.ADMIN_TOKEN) {
        return json({ error: 'unauthorized' }, 401, origin);
      }
      const raw = await env.LEADS_KV.get(LEADS_KEY);
      const leads = raw ? JSON.parse(raw) : [];
      const cols = ['ts','name','email','phone','trade','lostYear','lostMonth',
                    'job','miss','days','conv','utm_source','utm_medium','utm_campaign','page'];
      const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
      const rows = leads.map(l => [
        new Date(l.ts).toISOString(), l.name, l.email, l.phone, l.trade,
        l.result?.lostYear, l.result?.lostMonth, l.result?.job, l.result?.miss,
        l.result?.days, l.result?.conv, l.utm_source, l.utm_medium, l.utm_campaign, l.page
      ].map(esc).join(','));
      const csv = [cols.join(','), ...rows].join('\n');
      return new Response(csv, {
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="caillte-leads.csv"'
        }
      });
    }

    return json({ error: 'not found' }, 404, origin);
  }
};
