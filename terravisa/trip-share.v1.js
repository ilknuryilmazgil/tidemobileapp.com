// Paylaşılan Seyahat Planı istemci kodu (TripSharePage.astro).
// Güvenlik: plan verisi yalnızca textContent / createElement ile yazılır; innerHTML'e hiçbir veri girmez.
// Bağlantı anahtarı adresin # bölümündedir ve yalnızca Cloud Function çağrısının gövdesinde gönderilir.
const cfg = JSON.parse(document.getElementById('tp-cfg').textContent);
const T = cfg.T;
const $ = (id) => document.getElementById(id);
const ID_KEY = /^([A-Za-z0-9_-]{22})\.([A-Za-z0-9_-]{43})$/;
const SESSION_RE = /^[A-Za-z0-9_-]{43}$/;
const COUNTRY_RE = /^[A-Z]{2}$/;
const CITY_RE = /^[a-z0-9-]{1,40}$/;

if (window.top !== window.self) document.documentElement.hidden = true; // başka sitede çerçeve içinde gösterilmez

const m = location.hash.slice(1).match(ID_KEY);
const link = m ? { id: m[1], key: m[2] } : null;
const SKEY = link ? 'tv.trip.' + link.id : '';
const getSession = () => { try { const s = sessionStorage.getItem(SKEY); return s && SESSION_RE.test(s) ? s : ''; } catch { return ''; } };
const setSession = (s) => { try { sessionStorage.setItem(SKEY, s); } catch {} };

class NetError extends Error {}
class RateError extends Error {}
async function call(name, data) {
  let r;
  try {
    r = await fetch(`${cfg.fn}/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ data }), credentials: 'omit', referrerPolicy: 'no-referrer', cache: 'no-store' });
  } catch { throw new NetError(); }
  const j = await r.json().catch(() => null);
  if (j && j.error && j.error.status === 'RESOURCE_EXHAUSTED') throw new RateError();
  if (!r.ok || !j || typeof j.result !== 'object' || j.result === null) throw new NetError();
  return j.result;
}

/* ── Biçimlendirme ── */
const locale = cfg.lang === 'tr' ? 'tr-TR' : 'en-GB';
const okDate = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s);
const dt = (s) => new Date(s + 'T00:00:00Z');
const fmt = (s, o) => okDate(s) ? new Intl.DateTimeFormat(locale, { timeZone: 'UTC', ...o }).format(dt(s)) : '';
const dayMonth = (s) => fmt(s, { day: 'numeric', month: 'long' });
function range(a, b) {
  if (!okDate(a) || !okDate(b)) return '';
  const y = (s) => s.slice(0, 4), mo = (s) => s.slice(0, 7);
  if (a === b) return fmt(a, { day: 'numeric', month: 'long', year: 'numeric' });
  if (mo(a) === mo(b)) return `${fmt(a, { day: 'numeric' })} – ${fmt(b, { day: 'numeric', month: 'long', year: 'numeric' })}`;
  if (y(a) === y(b)) return `${dayMonth(a)} – ${fmt(b, { day: 'numeric', month: 'long', year: 'numeric' })}`;
  return `${fmt(a, { day: 'numeric', month: 'long', year: 'numeric' })} – ${fmt(b, { day: 'numeric', month: 'long', year: 'numeric' })}`;
}
const diffDays = (a, b) => Math.round((dt(b) - dt(a)) / 86400000);
const stamp = (ms) => Number.isFinite(ms) ? new Intl.DateTimeFormat(locale, { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(ms)) : '';
const tpl = (s, v) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ''));
const str = (v, max = 200) => (typeof v === 'string' ? v : '').slice(0, max);
const nightsText = (n) => (n === 1 ? T.nightsOne : tpl(T.nights, { n }));
const daysText = (n) => (n === 1 ? T.dayOne : tpl(T.daysN, { n }));

/* ── DOM yardımcıları ── */
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
const icon = (name) => $('ic-' + name).content.firstElementChild.cloneNode(true);
const setImg = (img, src) => { if (typeof src === 'string' && src.startsWith('/')) img.src = src; };
const countryImg = (c, kind) => (COUNTRY_RE.test(c) && cfg.img.country[c] ? cfg.img.country[c][kind] : kind === 'hero' ? cfg.img.genericHero : cfg.img.genericCard);
const cityImg = (id, c) => (CITY_RE.test(id) && Object.prototype.hasOwnProperty.call(cfg.img.city, id) ? cfg.img.city[id] : countryImg(c, 'card'));

/* ── Durum ekranları ── */
function showStatus(state, data) {
  const st = T.st[state];
  $('tp-loading').hidden = true; $('tp-plan').hidden = true; $('tp-status').hidden = false;
  document.title = `${st.t} · TerraVisa`;
  $('st-title').textContent = st.t; $('st-text').textContent = st.s;
  const ic = $('st-icon');
  ic.classList.toggle('red', state === 'revoked' || state === 'invalid');
  ic.querySelectorAll('[data-i]').forEach((s) => s.classList.toggle('on', s.dataset.i === state));
  // Yalnızca "empty" durumunda ziyaretçi yetkilidir; plan bilgisi ve ülke fotoğrafı yalnızca orada gösterilir.
  const plan = state === 'empty' && data && data.plan ? data.plan : null;
  setImg($('st-bg'), plan ? countryImg(plan.country, 'hero') : cfg.img.genericHero);
  const card = $('st-card');
  card.hidden = !['invite', 'revoked', 'expired', 'empty'].includes(state);
  if (!card.hidden) {
    setImg($('st-card-img'), plan ? countryImg(plan.country, 'card') : cfg.img.genericCard);
    $('st-card-title').textContent = plan ? str(plan.title, 80) : st.card;
    const dates = $('st-card-dates'), cities = $('st-card-cities');
    dates.hidden = cities.hidden = !plan;
    if (plan) {
      dates.querySelector('span').textContent = `${range(plan.startDate, plan.endDate)} (${daysText(diffDays(plan.startDate, plan.endDate) + 1)})`;
      cities.querySelector('span').textContent = (Array.isArray(plan.cities) ? plan.cities : []).map((c) => str(c && c.name, 60)).filter(Boolean).join(', ');
    }
    const badge = $('st-badge');
    badge.textContent = st.badge; badge.classList.toggle('amber', state === 'empty' || state === 'invite');
    $('st-badge-s').textContent = st.badgeS || '';
  }
  $('st-tips').hidden = state !== 'offline';
  $('st-invite').hidden = state !== 'invite';
  const btn = $('st-primary');
  btn.hidden = !st.btn; btn.disabled = false;
  if (st.btn) {
    $('st-primary-t').textContent = st.btn;
    $('st-primary-ic').replaceChildren(icon(state === 'offline' ? 'refresh' : 'send'));
    btn.onclick = state === 'offline' ? () => location.reload() : notifyOwner;
  }
  say('');
}
function say(msg, err) { const s = $('st-msg'); s.textContent = msg; s.classList.toggle('err', !!err); }

async function notifyOwner() {
  const btn = $('st-primary');
  btn.disabled = true;
  try { await call('tripShareNotifyOwner', { id: link.id, key: link.key }); say(T.notified); }
  catch (e) { btn.disabled = false; say(e instanceof RateError ? T.rate : T.st.offline.s, true); }
}

/* ── Özel davet doğrulaması ── */
function setupInvite() {
  const fe = $('f-email'), fc = $('f-code'), email = $('i-email'), code = $('i-code');
  const busy = (f, on) => { const b = f.querySelector('button[type=submit]'); b.disabled = on; b.querySelector('span').textContent = on ? T.busy : (f === fe ? T.sendCode : T.verify); };
  fe.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const v = email.value.trim().toLowerCase();
    if (!/^[^\s@<>"']+@[^\s@<>"']+\.[^\s@<>"']{2,}$/.test(v) || v.length > 160) { say(T.badEmail, true); email.focus(); return; }
    busy(fe, true); say('');
    try { await call('tripShareSendCode', { id: link.id, key: link.key, email: v, lang: cfg.lang }); fe.hidden = true; fc.hidden = false; code.focus(); }
    catch (e) { say(e instanceof RateError ? T.rate : T.st.offline.s, true); }
    finally { busy(fe, false); }
  });
  fc.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const c = code.value.replace(/\D/g, '');
    if (c.length !== 6) { say(T.badCode, true); code.focus(); return; }
    busy(fc, true); say('');
    try {
      const r = await call('tripShareVerifyCode', { id: link.id, key: link.key, email: email.value.trim().toLowerCase(), code: c });
      if (r.ok === true && SESSION_RE.test(String(r.session))) { setSession(r.session); code.value = ''; await load(); return; }
      say(T.badCode, true);
    } catch (e) { say(e instanceof RateError ? T.rate : T.st.offline.s, true); }
    finally { busy(fc, false); }
  });
  $('i-other').addEventListener('click', () => { fc.hidden = true; fe.hidden = false; code.value = ''; say(''); email.focus(); });
}

/* ── Plan görünümü ── */
function showPlan(data) {
  const p = data.plan;
  const days = Array.isArray(p.days) ? p.days : [];
  const cities = (Array.isArray(p.cities) ? p.cities : []).filter((c) => c && typeof c.name === 'string');
  $('tp-loading').hidden = true; $('tp-status').hidden = true; $('tp-plan').hidden = false;
  const title = str(p.title, 80);
  document.title = `${title} · TerraVisa`;
  setImg($('p-hero'), countryImg(p.country, 'hero'));
  $('p-title').textContent = title;
  const owner = str(data.ownerName, 40);
  $('p-by').textContent = owner ? tpl(T.by, { name: owner }) : T.byAnon;
  $('p-dates').textContent = range(p.startDate, p.endDate);
  const nDays = days.length;
  $('p-nights').textContent = nightsText(Math.max(0, diffDays(p.startDate, p.endDate)));
  const cityNames = cities.map((c) => str(c.name, 60));
  $('p-cities').textContent = cityNames.join(', ');
  $('p-summary').textContent = tpl(T.summary, { cities: cityNames.join(', '), days: nDays });
  const stopCount = days.reduce((n, d) => n + (Array.isArray(d.stops) ? d.stops.length : 0), 0);
  $('s-city').textContent = String(cities.length); $('s-stop').textContent = String(stopCount); $('s-day').textContent = String(nDays);

  // Şehir kartları: ardışık günler aynı şehirde gruplanır.
  const groups = [];
  for (const d of days) {
    const name = str(d.city, 60) || cityNames[0] || '';
    const last = groups[groups.length - 1];
    if (last && last.name === name) { last.end = d.date; last.n++; } else groups.push({ name, start: d.date, end: d.date, n: 1 });
  }
  $('p-route').replaceChildren(...groups.map((g, i) => {
    const li = el('li');
    const c = cities.find((x) => x.name === g.name);
    const img = el('img'); img.alt = ''; img.loading = 'lazy'; img.width = 360; img.height = 150; setImg(img, cityImg(c ? str(c.id, 40) : '', p.country));
    const body = el('div', 'cb');
    const dRow = el('p', 'm'); dRow.append(icon('calendar'), el('span', '', range(g.start, g.end)));
    const nRow = el('p', 'm'); nRow.append(icon('clock'), el('span', '', daysText(g.n)));
    body.append(el('h3', '', g.name), dRow, nRow);
    li.append(img, el('span', 'num', String(i + 1)), body);
    return li;
  }));

  const notes = [];
  $('p-days').replaceChildren(...days.map((d, i) => {
    const li = el('li');
    const head = el('div', 'dh'); head.append(el('strong', '', tpl(T.day, { n: i + 1 })), el('span', '', `${fmt(d.date, { day: 'numeric', month: 'long', weekday: 'long' })}${d.city ? ' · ' + str(d.city, 60) : ''}`));
    li.append(head);
    const stops = Array.isArray(d.stops) ? d.stops : [];
    if (!stops.length) { li.append(el('p', 'free', T.free)); return li; }
    const ol = el('ol', 'stops');
    for (const s of stops) {
      const hasTime = /^\d{2}:\d{2}$/.test(s.start) && /^\d{2}:\d{2}$/.test(s.end);
      const row = el('li', 'stop' + (hasTime ? '' : ' nt'));
      if (hasTime) row.append(el('span', 'time', `${s.start}–${s.end}`));
      const box = el('div');
      box.append(el('p', 'sn', str(s.name, 80)));
      const sub = [str(s.kind, 40), str(s.area, 80)].filter(Boolean).join(' · ');
      if (sub) box.append(el('p', 'sa', sub));
      const note = str(s.note, 300);
      if (note) { box.append(el('p', 'snote', note)); notes.push({ day: i + 1, date: d.date, stop: str(s.name, 80), note }); }
      row.append(box); ol.append(row);
    }
    li.append(ol);
    return li;
  }));
  $('p-times').hidden = !p.includeTimes;

  $('p-legs').replaceChildren(...days.map((d, i) => {
    const li = el('li');
    const head = el('div', 'dh'); head.append(el('strong', '', tpl(T.day, { n: i + 1 })), el('span', '', `${dayMonth(d.date)}${d.city ? ' · ' + str(d.city, 60) : ''}`));
    li.append(head);
    const stops = Array.isArray(d.stops) ? d.stops : [];
    if (!stops.length) { li.append(el('p', 'free', T.routeEmpty)); return li; }
    const ol = el('ol', 'stops');
    stops.forEach((s, j) => {
      if (j > 0 && Object.prototype.hasOwnProperty.call(T.modes, s.mode)) { const leg = el('li', 'leg'); leg.append(icon(s.mode === 'walk' ? 'walk' : 'route'), el('span', '', T.modes[s.mode])); ol.append(leg); }
      const row = el('li', 'stop nt'); const box = el('div'); box.append(el('p', 'sn', `${j + 1}. ${str(s.name, 80)}`));
      if (s.area) box.append(el('p', 'sa', str(s.area, 80)));
      row.append(box); ol.append(row);
    });
    li.append(ol);
    return li;
  }));

  $('t-notes').hidden = !notes.length;
  $('p-notes').replaceChildren(...notes.map((n) => { const li = el('li'); li.append(el('strong', '', n.stop), el('small', '', `${tpl(T.day, { n: n.day })} · ${dayMonth(n.date)}`), el('p', '', n.note)); return li; }));

  $('d-owner-row').hidden = !owner; $('d-owner').textContent = owner;
  $('d-until').textContent = tpl(T.untilFmt, { date: stamp(data.expiresAt) });
  $('d-updated').textContent = stamp(data.updatedAt);
}

/* ── Sekmeler (WAI-ARIA tabs) ── */
const tabs = ['overview', 'days', 'route', 'notes'];
function select(name, focus) {
  for (const t of tabs) {
    const b = $('t-' + t), on = t === name;
    b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; $('v-' + t).hidden = !on;
    if (on && focus) b.focus();
  }
}
tabs.forEach((t) => {
  const b = $('t-' + t);
  b.addEventListener('click', () => select(t));
  b.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const vis = tabs.filter((x) => !$('t-' + x).hidden);
    const i = vis.indexOf(t) + (e.key === 'ArrowRight' ? 1 : -1);
    select(vis[(i + vis.length) % vis.length], true);
  });
});

/* ── Yükleme ── */
async function load() {
  if (!link) { showStatus('invalid'); return; }
  let r;
  try { r = await call('tripShareView', { id: link.id, key: link.key, session: getSession() || undefined }); }
  catch { showStatus('offline'); return; }
  const state = r && r.state;
  if (state === 'active' && r.plan && typeof r.plan === 'object') { showPlan(r); select('overview'); return; }
  if (['empty', 'invite', 'expired', 'revoked', 'invalid'].includes(state)) { showStatus(state, r); return; }
  showStatus('offline');
}
// "Uygulamada Aç" (Android ve iOS): uygulama yüklüyse plan uygulamada açılır. Android'de yüklü değilse bu sayfada kalınır.
if (link) {
  const ua = navigator.userAgent;
  const ios = /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
  const a = $('tp-app');
  if (/Android/i.test(ua)) {
    const back = encodeURIComponent(location.href);
    a.href = `intent://trip/${link.id}.${link.key}#Intent;scheme=terravisa;package=com.tidemobile.terravisa.yeni;S.browser_fallback_url=${back};end`;
    a.hidden = false;
  } else if (ios) {
    a.href = `terravisa://trip/${link.id}.${link.key}`;
    a.hidden = false;
  }
}
setupInvite();
window.addEventListener('hashchange', () => location.reload());
load();
