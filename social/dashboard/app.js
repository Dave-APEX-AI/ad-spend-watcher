/* CaillteAI dashboard — fetch live data.json (fallback to embedded), then render + drill in. */

function sparkline(points, w = 96, h = 34) {
  const max = Math.max(...points), min = Math.min(...points);
  const span = (max - min) || 1, step = w / (points.length - 1);
  const pts = points.map((p, i) => [i * step, h - ((p - min) / span) * (h - 4) - 2]);
  const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" fill="none">
    <path d="${d} L ${w} ${h} L 0 ${h} Z" fill="rgba(15,185,126,.10)"/>
    <path d="${d}" stroke="var(--accent)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${pts[pts.length-1][0].toFixed(1)}" cy="${pts[pts.length-1][1].toFixed(1)}" r="3.2" fill="var(--accent)"/></svg>`;
}
const fmt = (n, d) => d ? Number(n).toFixed(d) : Math.round(n).toLocaleString('en-GB');
function countUp(el, target, decimals) {
  if (new URLSearchParams(location.search).get('still')) { el.firstChild.nodeValue = fmt(target, decimals); return; }
  const dur = 1100, t0 = performance.now();
  (function tick(t) {
    const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
    el.firstChild.nodeValue = fmt(target * e, decimals);
    if (p < 1) requestAnimationFrame(tick);
  })(t0);
}

/* merge live data.json over the embedded defaults */
function applyLive(d) {
  if (!d) return;
  const S = Object.fromEntries(STATS.map(s => [s.key, s]));
  const A = Object.fromEntries(AGENTS.map(a => [a.key, a]));
  if (d.stats) {
    if (d.stats.followers != null) { S.followers.value = d.stats.followers; S.followers.note = ''; S.followers.delta = 'live'; }
    if (d.stats.views != null) S.views.value = d.stats.views;
    if (d.stats.topViews != null) { S.top.value = d.stats.topViews; if (d.stats.topLabel) S.top.delta = d.stats.topLabel; }
    if (d.stats.engagement != null) S.eng.value = d.stats.engagement;
  }
  if (d.analyst) {
    const an = d.analyst;
    A.analyst.metrics = [['Posts tracked', an.postsTracked], ['Top format', an.topFormat], ['Best post', an.best]];
    A.analyst.modal.kpis = [[String(an.postsTracked), 'Posts tracked'], [String(an.best), 'Top views'], [an.topFormat, 'Best format']];
    A.analyst.modal.items = [...(an.top || []), ['insight', an.insight1, 'reels win'], ['insight', an.insight2, 'focus']];
  }
  if (d.planner) {
    A.planner.metrics = [['Queued', d.planner.queued], ['Days buffered', d.planner.days], ['Cadence', '2/day']];
    A.planner.modal.kpis = [[String(d.planner.queued), 'Posts queued'], [d.planner.days + ' days', 'Buffered'], ['2/day', 'Cadence']];
  }
  if (d.updated) document.getElementById('updated').textContent = 'updated ' + d.updated;
}

function renderStats() {
  const el = document.getElementById('stats'); el.innerHTML = '';
  STATS.forEach(s => {
    const card = document.createElement('div');
    card.className = 'stat'; card.dataset.key = s.key;
    card.innerHTML = `<div class="ico">${s.icon}</div>
      <div class="label">${s.label}</div>
      <div class="value"><span class="num">0</span>${s.suffix ? `<small>${s.suffix}</small>` : ''}</div>
      <div class="delta ${s.flat ? 'flat' : ''}">${s.flat ? '◦' : '▲'} ${s.delta}</div>
      ${sparkline(s.spark)}`;
    el.appendChild(card);
    countUp(card.querySelector('.num'), s.value, s.decimals);
    card.addEventListener('click', () => openAgentByStat(s.key));
  });
}

function renderAgents() {
  const el = document.getElementById('agents'); el.innerHTML = '';
  AGENTS.forEach(a => {
    const card = document.createElement('div');
    card.className = 'agent'; card.dataset.key = a.key;
    card.innerHTML = `<span class="status"><span class="d"></span>working</span>
      <div class="viz">${a.viz}</div>
      <div class="a-name">${a.name}</div><div class="a-role">${a.role}</div>
      <div class="a-metrics">${a.metrics.map(m => `<div class="a-row"><span class="k">${m[0]}</span><span class="v">${m[1]}</span></div>`).join('')}</div>
      <div class="open">Open ${a.name} →</div>`;
    el.appendChild(card);
    card.addEventListener('click', () => openModal(a));
  });
  const cal = document.getElementById('calviz');
  if (cal) for (let i = 0; i < 21; i++) {
    const c = document.createElement('i');
    if ([1,2,4,5,7,9,10,12,14,15,17,19,20].includes(i)) { c.className = 'on'; c.style.animationDelay = (i * 0.06) + 's'; }
    cal.appendChild(c);
  }
  document.querySelectorAll('.bars i').forEach((b, i) => b.style.height = (16 + i * 8) + 'px');
}

const overlay = document.getElementById('overlay'), modalBody = document.getElementById('modalBody');
function openModal(a) {
  const m = a.modal;
  modalBody.innerHTML = `<div class="m-eyebrow">${m.eyebrow}</div><h3>${m.title}</h3>
    <div class="m-sub">${m.sub}</div>
    <div class="m-kpis">${m.kpis.map(k => `<div class="m-kpi"><div class="v">${k[0]}</div><div class="k">${k[1]}</div></div>`).join('')}</div>
    <div class="m-list">${m.items.map(it => `<div class="m-item"><span class="tag">${it[0]}</span><span class="txt">${it[1]}</span><span class="meta">${it[2]}</span></div>`).join('')}</div>`;
  overlay.classList.add('show');
}
function openAgentByStat(k) {
  const map = { followers: 'dm', views: 'analyst', top: 'analyst', eng: 'analyst' };
  const a = AGENTS.find(x => x.key === (map[k] || 'analyst')); if (a) openModal(a);
}
document.getElementById('modalClose').addEventListener('click', () => overlay.classList.remove('show'));
overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('show'); });

async function init() {
  try {
    const r = await fetch('data.json', { cache: 'no-store' });
    if (r.ok) applyLive(await r.json());
  } catch (e) { /* fall back to embedded data */ }
  if (!document.getElementById('updated').textContent.startsWith('updated 2'))
    document.getElementById('updated').textContent = 'updated ' + new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  renderStats(); renderAgents();
  const q = new URLSearchParams(location.search).get('open');
  if (q) { const a = AGENTS.find(x => x.key === q); if (a) openModal(a); }
}
init();
