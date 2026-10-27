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

  // iletişim formu: mesajı doğrudan Modi ekibine iletir
  var form = $('#contactForm');
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    var msg = $('#formMsg'), f = form.elements, btn = form.querySelector('button[type="submit"]');
    function say(t, ok) { msg.style.color = ok ? 'var(--green)' : 'var(--orange)'; msg.textContent = t; }
    if (!f.ad.value.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(f.mail.value.trim()) || !f.konu.value || f.mesaj.value.trim().length < 2) { say('Lütfen yıldızlı alanların hepsini doldur.'); return; }
    if (!$('#f-kvkk').checked) { say('Devam etmek için KVKK Aydınlatma Metni'ni okuduğunu işaretle.'); return; }
    btn.disabled = true; var label = btn.innerHTML; btn.textContent = 'Gönderiliyor...';
    fetch('https://europe-west1-modi-76f7c.cloudfunctions.net/iletisimFormu', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ad: f.ad.value, mail: f.mail.value, konu: f.konu.value, cihaz: f.cihaz.value, mesaj: f.mesaj.value, website: f.website ? f.website.value : '', kvkk: true })
    }).then(function (r) { return r.json().then(function (j) { return { s: r.status, j: j }; }); })
      .then(function (r) {
        if (r.j && r.j.ok) { form.reset(); say('Mesajın bize ulaştı, teşekkürler! En kısa sürede e-posta ile dönüş yapacağız. 🐱', true); }
        else if (r.s === 429) say('Kısa sürede çok fazla mesaj gönderildi. Biraz sonra tekrar dener misin?');
        else say('Mesaj gönderilemedi. Bilgileri kontrol edip tekrar dene ya da tidemobile.contact@gmail.com adresine yaz.');
      })
      .catch(function () { say('Bağlantı sorunu oluştu. Tekrar dene ya da tidemobile.contact@gmail.com adresine yaz.'); })
      .then(function () { btn.disabled = false; btn.innerHTML = label; });
  });

  // "Uygulamada başla": cihaza göre mağaza, bilgisayarda seçim penceresi
  var modal = $('#appModal');
  var ua = navigator.userAgent || '';
  var isIOS = /iPhone|iPad|iPod/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var isAndroid = /Android/i.test(ua);
  function storeUrl(kind) { var a = $('[data-store="' + kind + '"]'); return a ? a.href : null; }
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


  // "Modi nasıl çalışır?": video adımı ile kartlar senkron; görünürken oynar, kart tıklanınca o adıma atlar
  var hv = $('#howVideo');
  if (hv) {
    var STEP_SEC = 4, cards = $$('.step-card'), reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches, loaded = false;
    var mark = function (i) { cards.forEach(function (c, k) { c.classList.toggle('on', k === i); c.setAttribute('aria-selected', k === i ? 'true' : 'false'); }); };
    var load = function () { if (loaded) return; loaded = true; $$('source', hv).forEach(function (s) { s.src = s.dataset.src; }); hv.load(); };
    hv.addEventListener('timeupdate', function () { if (pending !== null) return; mark(Math.floor(hv.currentTime / STEP_SEC) % cards.length); });
    var pending = null;
    var apply = function () { if (pending === null || hv.readyState < 1) return; var t = pending; pending = null; try { hv.currentTime = t; } catch (e) {} };
    ['loadedmetadata', 'loadeddata', 'canplay', 'playing'].forEach(function (ev) { hv.addEventListener(ev, apply); });
    cards.forEach(function (c, k) { c.addEventListener('click', function () { mark(k); if (reduce) return; load(); pending = k * STEP_SEC + 0.05; apply(); var p = hv.play(); if (p && p.then) p.then(apply).catch(function () {}); }); });
    if (!reduce && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { load(); var p = hv.play(); if (p && p.catch) p.catch(function () {}); } else hv.pause(); }); }, { threshold: 0.35 }).observe(hv);
    }
  }

  // meditasyon önizlemesi: kısa kesit çalar, bitince "devamı uygulamada" kartı açılır
  $$('[data-preview]').forEach(function (box) {
    var au = $('audio', box), btn = $('.mprev-btn', box), bar = $('.mprev-bar', box), fill = $('.mprev-bar span', box), time = $('[data-time]', box);
    var end = box.parentNode.querySelector('.mprev-end'), label = time.textContent;
    var fmt = function (s) { s = Math.max(0, Math.ceil(s)); return Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); };
    var setPlaying = function (on) { box.classList.toggle('playing', on); btn.setAttribute('aria-pressed', on ? 'true' : 'false'); };
    btn.addEventListener('click', function () {
      if (au.paused) { var p = au.play(); if (p && p.catch) p.catch(function () { setPlaying(false); }); } else au.pause();
    });
    au.addEventListener('play', function () { setPlaying(true); });
    au.addEventListener('pause', function () { setPlaying(false); });
    au.addEventListener('timeupdate', function () {
      if (!au.duration) return;
      var pct = Math.min(100, au.currentTime / au.duration * 100);
      fill.style.width = pct + '%'; bar.setAttribute('aria-valuenow', Math.round(pct));
      time.textContent = fmt(au.duration - au.currentTime);
    });
    au.addEventListener('ended', function () { setPlaying(false); box.hidden = true; end.hidden = false; });
    $('.mprev-again', end).addEventListener('click', function () {
      end.hidden = true; box.hidden = false; au.currentTime = 0; fill.style.width = '0'; time.textContent = label; btn.focus(); au.play();
    });
  });

  // görünürken yumuşak giriş
  var fades = $$('.fade');
  if ('IntersectionObserver' in window) {
    var fo = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); fo.unobserve(e.target); } }); }, { rootMargin: '0px 0px -8% 0px' });
    fades.forEach(function (el) { fo.observe(el); });
  } else fades.forEach(function (el) { el.classList.add('in'); });
})();
