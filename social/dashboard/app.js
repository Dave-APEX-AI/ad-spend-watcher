/* CaillteAI dashboard — render, animate, drill in. Self-contained, no backend. */

function sparkline(points, w = 96, h = 34) {
  const max = Math.max(...points), min = Math.min(...points);
  const span = (max - min) || 1;
  const step = w / (points.length - 1);
  const pts = points.map((p, i) => [i * step, h - ((p - min) / span) * (h - 4) - 2]);
  const d = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
  const area = d + ` L ${w} ${h} L 0 ${h} Z`;
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" fill="none">
    <path d="${area}" fill="rgba(15,185,126,.10)"/>
    <path d="${d}" stroke="var(--accent)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="${pts[pts.length-1][0].toFixed(1)}" cy="${pts[pts.length-1][1].toFixed(1)}" r="3.2" fill="var(--accent)"/>
  </svg>`;
}

function fmt(n, decimals) {
  if (decimals) return n.toFixed(decimals);
  return Math.round(n).toLocaleString('en-GB');
}

function countUp(el, target, decimals, suffix) {
  const dur = 1100, t0 = performance.now();
  function tick(t) {
    const p = Math.min(1, (t - t0) / dur);
    const e = 1 - Math.pow(1 - p, 3);
    el.firstChild.nodeValue = fmt(target * e, decimals);
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* stats */
const statsEl = document.getElementById('stats');
STATS.forEach(s => {
  const card = document.createElement('div');
  card.className = 'stat';
  card.dataset.key = s.key;
  card.innerHTML = `
    <div class="ico">${s.icon}</div>
    <div class="label">${s.label}</div>
    <div class="value"><span class="num">0</span>${s.suffix ? `<small>${s.suffix}</small>` : ''}</div>
    <div class="delta ${s.flat ? 'flat' : ''}">${s.flat ? '◦' : '▲'} ${s.delta}</div>
    ${sparkline(s.spark)}`;
  statsEl.appendChild(card);
  const num = card.querySelector('.num');
  num.textContent = '0';
  countUp(num, s.value, s.decimals, s.suffix);
  card.addEventListener('click', () => openAgentByStat(s.key));
});

/* agents */
const agentsEl = document.getElementById('agents');
AGENTS.forEach(a => {
  const card = document.createElement('div');
  card.className = 'agent';
  card.dataset.key = a.key;
  card.innerHTML = `
    <span class="status"><span class="d"></span>working</span>
    <div class="viz">${a.viz}</div>
    <div class="a-name">${a.name}</div>
    <div class="a-role">${a.role}</div>
    <div class="a-metrics">${a.metrics.map(m => `<div class="a-row"><span class="k">${m[0]}</span><span class="v">${m[1]}</span></div>`).join('')}</div>
    <div class="open">Open ${a.name} →</div>`;
  agentsEl.appendChild(card);
  card.addEventListener('click', () => openModal(a));
});

/* planner calendar animation */
(function () {
  const cal = document.getElementById('calviz');
  if (!cal) return;
  for (let i = 0; i < 21; i++) {
    const c = document.createElement('i');
    if ([1,2,4,5,7,9,10,12,14,15,17,19,20].includes(i)) {
      c.className = 'on';
      c.style.animationDelay = (i * 0.06) + 's';
    }
    cal.appendChild(c);
  }
  document.querySelectorAll('.bars i').forEach((b, i) => b.style.height = (16 + i * 8) + 'px');
})();

/* modal */
const overlay = document.getElementById('overlay');
const modalBody = document.getElementById('modalBody');
function openModal(a) {
  const m = a.modal;
  modalBody.innerHTML = `
    <div class="m-eyebrow">${m.eyebrow}</div>
    <h3>${m.title}</h3>
    <div class="m-sub">${m.sub}</div>
    <div class="m-kpis">${m.kpis.map(k => `<div class="m-kpi"><div class="v">${k[0]}</div><div class="k">${k[1]}</div></div>`).join('')}</div>
    <div class="m-list">${m.items.map(it => `<div class="m-item"><span class="tag">${it[0]}</span><span class="txt">${it[1]}</span><span class="meta">${it[2]}</span></div>`).join('')}</div>`;
  overlay.classList.add('show');
}
function openAgentByStat(statKey) {
  const map = { followers:'dm', views:'analyst', top:'analyst', eng:'analyst' };
  const a = AGENTS.find(x => x.key === (map[statKey] || 'analyst'));
  if (a) openModal(a);
}
document.getElementById('modalClose').addEventListener('click', () => overlay.classList.remove('show'));
overlay.addEventListener('click', e => { if (e.target === overlay) overlay.classList.remove('show'); });

/* updated time */
document.getElementById('updated').textContent = 'updated ' + new Date().toLocaleString('en-GB', { hour: '2-digit', minute: '2-digit' });

/* allow ?open=analyst to auto-open a modal (used for screenshots) */
const q = new URLSearchParams(location.search).get('open');
if (q) { const a = AGENTS.find(x => x.key === q); if (a) openModal(a); }
