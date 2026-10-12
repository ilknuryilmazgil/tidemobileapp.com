(function () {
  var root = (document.currentScript && document.currentScript.src || '').replace(/assets\/site\.js.*$/, '');
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  // duyuru şeridi
  var ann = $('#announce');
  if (ann && store('modi_announce_closed') === '1') ann.hidden = true;
  $$('[data-close-announce]').forEach(function (b) { b.addEventListener('click', function () { ann.hidden = true; store('modi_announce_closed', '1'); }); });

  // mobil menü
  var drawer = $('#drawer');
  function setDrawer(open) { if (!drawer) return; drawer.classList.toggle('open', open); drawer.setAttribute('aria-hidden', open ? 'false' : 'true'); document.body.style.overflow = open ? 'hidden' : ''; }
  $$('[data-open-menu]').forEach(function (b) { b.addEventListener('click', function () { setDrawer(true); }); });
  $$('[data-close-menu]').forEach(function (b) { b.addEventListener('click', function () { setDrawer(false); }); });
  if (drawer) drawer.addEventListener('click', function (e) { if (e.target === drawer || e.target.closest('nav a')) setDrawer(false); });

  // arama
  var layer = $('#searchLayer'), input = $('#searchInput'), out = $('#searchResults'), index = null;
  function norm(s) { return (s || '').toLocaleLowerCase('tr').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ı/g, 'i'); }
  function render(q) {
    if (!out) return;
    var n = norm(q).trim();
    var list = (index || []).filter(function (x) { return !n || norm(x.t + ' ' + x.d).indexOf(n) > -1; }).slice(0, 12);
    out.innerHTML = '';
    if (!list.length) { out.innerHTML = '<p style="padding:10px;font-size:.88rem">Sonuç bulunamadı. Farklı bir kelime dene.</p>'; return; }
    list.forEach(function (x) { var a = document.createElement('a'); a.href = root + x.u; var b = document.createElement('b'); b.textContent = x.t; var s = document.createElement('small'); s.textContent = x.d; a.appendChild(b); a.appendChild(s); out.appendChild(a); });
  }
  function setSearch(open) {
    if (!layer) return;
    layer.classList.toggle('open', open); layer.setAttribute('aria-hidden', open ? 'false' : 'true');
    if (open) {
      if (!index) fetch(root + 'assets/search.json').then(function (r) { return r.json(); }).then(function (d) { index = d; render(input.value); }).catch(function () { index = []; });
      setTimeout(function () { input && input.focus(); }, 30);
    }
  }
  $$('[data-open-search]').forEach(function (b) { b.addEventListener('click', function () { setSearch(true); }); });
  $$('[data-close-search]').forEach(function (b) { b.addEventListener('click', function (e) { e.preventDefault(); setSearch(false); }); });
  if (layer) layer.addEventListener('click', function (e) { if (e.target === layer) setSearch(false); });
  if (input) input.addEventListener('input', function () { render(input.value); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { setSearch(false); setDrawer(false); } if (e.key === '/' && !/input|textarea|select/i.test(document.activeElement.tagName)) { e.preventDefault(); setSearch(true); } });

  // yolculuk filtreleri
  var jgrid = $('#journeys');
  if (jgrid) {
    var theme = 'all', days = 'all';
    var apply = function () {
      var shown = 0;
      $$('.jcard', jgrid).forEach(function (c) { var ok = (theme === 'all' || c.dataset.theme === theme) && (days === 'all' || c.dataset.days === days); c.hidden = !ok; if (ok) shown++; });
      var cnt = $('#jcount'); if (cnt) cnt.textContent = shown + ' yolculuk';
      $$('.theme').forEach(function (t) { t.classList.toggle('active', t.dataset.theme === theme); });
      $$('.filter-bar .chip').forEach(function (ch) { ch.classList.toggle('on', ch.dataset.days === days); });
    };
    $$('.theme').forEach(function (t) { t.addEventListener('click', function () { theme = theme === t.dataset.theme ? 'all' : t.dataset.theme; apply(); jgrid.scrollIntoView({ behavior: 'smooth', block: 'start' }); }); });
    $$('.filter-bar .chip').forEach(function (ch) { ch.addEventListener('click', function () { days = ch.dataset.days; apply(); }); });
    if (location.hash) { var target = document.getElementById(location.hash.slice(1)); if (target && target.classList.contains('jcard')) { target.style.boxShadow = '0 0 0 3px var(--orange-soft)'; target.style.borderColor = 'var(--orange-line)'; } }
  }

  // test / araç filtresi
  var tools = $('#tools');
  if (tools) $$('[data-kind]').forEach(function (ch) {
    if (!ch.classList.contains('chip')) return;
    ch.addEventListener('click', function () {
      var k = ch.dataset.kind;
      $$('.chip[data-kind]').forEach(function (x) { x.classList.toggle('on', x === ch); });
      $$('.tcard', tools).forEach(function (c) { c.hidden = !(k === 'all' || c.dataset.kind === k); });
    });
  });

  // yazı filtresi
  var agrid = $('#artgrid');
  if (agrid) $$('[data-filter]').forEach(function (ch) {
    ch.addEventListener('click', function () {
      var f = ch.dataset.filter;
      $$('[data-filter]').forEach(function (x) { x.classList.toggle('on', x === ch); });
      $$('.acard', agrid).forEach(function (c) { c.hidden = !(f === 'all' || (' ' + c.dataset.tags + ' ').indexOf(' ' + f + ' ') > -1); });
    });
  });

  // SSS: yan menü vurgusu
  var sideLinks = $$('.side-link[href^="#"]');
  if (sideLinks.length && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) sideLinks.forEach(function (l) { l.classList.toggle('on', l.getAttribute('href') === '#' + e.target.id); }); }); }, { rootMargin: '-30% 0px -60% 0px' });
    sideLinks.forEach(function (l) { var t = document.getElementById(l.getAttribute('href').slice(1)); if (t) io.observe(t); });
  }

  // iletişim formu: e-posta uygulamasında hazır mesaj açar
  var form = $('#contactForm');
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    var msg = $('#formMsg'), f = form.elements;
    if (!f.ad.value.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.mail.value) || !f.konu.value || !f.mesaj.value.trim()) { msg.style.color = 'var(--orange)'; msg.textContent = 'Lütfen yıldızlı alanların hepsini doldur.'; return; }
    if (!$('#f-kvkk').checked) { msg.style.color = 'var(--orange)'; msg.textContent = 'Devam etmek için KVKK Aydınlatma Metni onayını işaretle.'; return; }
    var body = 'Ad: ' + f.ad.value + '\nE-posta: ' + f.mail.value + '\nCihaz: ' + f.cihaz.value + '\n\n' + f.mesaj.value;
    window.location.href = 'mailto:tidemobile.contact@gmail.com?subject=' + encodeURIComponent('[Modi] ' + f.konu.value) + '&body=' + encodeURIComponent(body);
    msg.style.color = 'var(--green)'; msg.textContent = 'Mesajın e-posta uygulamanda hazırlandı. Göndermeyi unutma!';
  });


  // "Uygulamada başla": cihaza göre mağaza, bilgisayarda seçim penceresi
  var modal = $('#appModal');
  var ua = navigator.userAgent || '';
  var isIOS = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var isAndroid = /Android/i.test(ua);
  function storeUrl(kind) { var a = $('.store[data-store="' + kind + '"]'); return a ? a.href : null; }
  function setModal(open) { if (!modal) return; modal.hidden = !open; document.body.style.overflow = open ? 'hidden' : ''; }
  $$('[data-app]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var url = isIOS ? storeUrl('ios') : isAndroid ? storeUrl('android') : null;
      e.preventDefault();
      if (url) window.open(url, '_blank', 'noopener'); else setModal(true);
    });
  });
  $$('[data-close-app]').forEach(function (b) { b.addEventListener('click', function () { setModal(false); }); });
  if (modal) modal.addEventListener('click', function (e) { if (e.target === modal) setModal(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setModal(false); });

  // görünürken yumuşak giriş
  var fades = $$('.fade');
  if ('IntersectionObserver' in window) {
    var fo = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); fo.unobserve(e.target); } }); }, { rootMargin: '0px 0px -8% 0px' });
    fades.forEach(function (el) { fo.observe(el); });
  } else fades.forEach(function (el) { el.classList.add('in'); });
})();
