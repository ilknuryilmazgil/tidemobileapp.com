/* Tide Mobile çerez onayı
 * Google Analytics yalnızca ziyaretçi "Kabul et" dedikten sonra yüklenir (KVKK Çerez Rehberi, GDPR).
 * Varsayılan: tüm çerezler reddedilmiş. Tercih 12 ay saklanır, sonra yeniden sorulur.
 * Sayfada [data-cerez-tercih] olan bir bağlantı tıklanınca panel yeniden açılır.
 */
(function () {
  'use strict';

  var GA_ID = 'G-KWZ9E0MQ41';
  var KEY = 'tm-cerez';
  var MAX_AGE = 365 * 24 * 60 * 60 * 1000;
  var en = (document.documentElement.lang || '').toLowerCase().indexOf('en') === 0;
  var POLICY = 'gizlilik.html#3-cerezler-ve-benzeri-teknolojiler';

  var TXT = en ? {
    label: 'Cookie preferences',
    title: 'Cookies',
    body: 'We would like to use Google Analytics cookies to understand how the site is used. They are only set if you accept. Strictly necessary features work either way.',
    more: 'Cookie details (TR)',
    accept: 'Accept',
    reject: 'Reject'
  } : {
    label: 'Çerez tercihleri',
    title: 'Çerezler',
    body: 'Sitenin nasıl kullanıldığını anlamak için Google Analytics çerezlerini kullanmak istiyoruz. Bu çerezler yalnızca kabul edersen yerleştirilir. Site her iki durumda da çalışır.',
    more: 'Çerez ayrıntıları',
    accept: 'Kabul et',
    reject: 'Reddet'
  };

  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== 'function') {
    window.gtag = function () { window.dataLayer.push(arguments); };
  }

  var memory = null; // localStorage kapalıysa tercih bu sayfa boyunca burada tutulur
  var gaLoaded = false;
  var panel = null;

  function read() {
    try {
      var raw = window.localStorage.getItem(KEY);
      if (!raw) return memory;
      var d = JSON.parse(raw);
      if (!d || (d.a !== 0 && d.a !== 1) || typeof d.t !== 'number') return memory;
      if (Date.now() - d.t > MAX_AGE) return null;
      return d.a === 1;
    } catch (e) {
      return memory;
    }
  }

  function save(granted) {
    memory = granted;
    try {
      window.localStorage.setItem(KEY, JSON.stringify({ a: granted ? 1 : 0, t: Date.now(), v: 1 }));
    } catch (e) { /* özel pencere vb. */ }
  }

  function loadGA() {
    if (gaLoaded) return;
    gaLoaded = true;
    window.gtag('consent', 'update', { analytics_storage: 'granted' });
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { allow_google_signals: false, allow_ad_personalization_signals: false });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
  }

  function clearGACookies() {
    var host = location.hostname;
    var domains = ['', host, '.' + host];
    var parts = host.split('.');
    if (parts.length > 2) domains.push('.' + parts.slice(-2).join('.'));
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (name === '_ga' || name.indexOf('_ga_') === 0 || name === '_gid' || name === '_gat') {
        domains.forEach(function (d) {
          document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + (d ? '; domain=' + d : '');
        });
      }
    });
  }

  function apply(granted) {
    if (granted) {
      loadGA();
    } else {
      window.gtag('consent', 'update', { analytics_storage: 'denied' });
      clearGACookies();
    }
  }

  var CSS =
    '.cerez{position:fixed;z-index:70;left:max(16px,env(safe-area-inset-left));bottom:max(16px,env(safe-area-inset-bottom));' +
    'width:min(380px,calc(100vw - 32px));box-sizing:border-box;padding:20px 20px 18px;border-radius:18px;' +
    'background:#fbf6ec;color:#143a4f;box-shadow:0 0 0 1px rgba(28,71,95,.13),0 24px 48px -24px rgba(16,48,63,.45),0 2px 6px -3px rgba(16,48,63,.15);' +
    'font-family:"Switzer",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:.9rem;line-height:1.5;' +
    'opacity:0;transform:translateY(12px);transition:opacity .35s ease,transform .35s ease}' +
    '.cerez.is-in{opacity:1;transform:none}' +
    '.cerez h2{margin:0 0 6px;font-family:"General Sans",ui-sans-serif,system-ui,sans-serif;font-size:1.02rem;font-weight:600;color:#1c475f;letter-spacing:0}' +
    '.cerez p{margin:0 0 14px;color:#2b5468}' +
    '.cerez p a{color:#24797f;text-decoration:underline;text-underline-offset:2px}' +
    '.cerez-btns{display:grid;grid-template-columns:1fr 1fr;gap:10px}' +
    '.cerez-btns button{appearance:none;margin:0;min-height:44px;padding:0 14px;border-radius:999px;cursor:pointer;' +
    'font:500 .9rem/1 "General Sans",ui-sans-serif,system-ui,sans-serif;border:1.5px solid #1c475f;transition:background-color .2s,color .2s}' +
    '.cerez-red{background:transparent;color:#1c475f}' +
    '.cerez-red:hover{background:rgba(28,71,95,.07)}' +
    '.cerez-kabul{background:#1c475f;color:#fbf6ec}' +
    '.cerez-kabul:hover{background:#10303f;border-color:#10303f}' +
    '.cerez button:focus-visible,.cerez a:focus-visible{outline:2px solid #329aa1;outline-offset:2px}' +
    '@media (prefers-reduced-motion:reduce){.cerez{transition:none}}' +
    '@media print{.cerez{display:none}}';

  function injectCSS() {
    if (document.getElementById('cerez-css')) return;
    var st = document.createElement('style');
    st.id = 'cerez-css';
    st.textContent = CSS;
    document.head.appendChild(st);
  }

  function close() {
    if (!panel) return;
    var p = panel;
    panel = null;
    p.classList.remove('is-in');
    setTimeout(function () { if (p.parentNode) p.parentNode.removeChild(p); }, 360);
  }

  function choose(granted) {
    var was = read();
    save(granted);
    apply(granted);
    close();
    // Daha önce kabul edilmiş ve şimdi geri alınmışsa yüklü GA kodunu tamamen durdurmak için sayfayı yenile
    if (was === true && !granted && gaLoaded) location.reload();
  }

  function open(focus) {
    if (panel) return;
    injectCSS();
    panel = document.createElement('section');
    panel.className = 'cerez';
    panel.setAttribute('role', 'region');
    panel.setAttribute('aria-label', TXT.label);
    panel.innerHTML =
      '<h2>' + TXT.title + '</h2>' +
      '<p>' + TXT.body + ' <a href="' + POLICY + '">' + TXT.more + '</a></p>' +
      '<div class="cerez-btns">' +
      '<button type="button" class="cerez-red">' + TXT.reject + '</button>' +
      '<button type="button" class="cerez-kabul">' + TXT.accept + '</button>' +
      '</div>';
    panel.querySelector('.cerez-red').addEventListener('click', function () { choose(false); });
    panel.querySelector('.cerez-kabul').addEventListener('click', function () { choose(true); });
    document.body.appendChild(panel);
    var p = panel;
    requestAnimationFrame(function () { requestAnimationFrame(function () { p.classList.add('is-in'); }); });
    if (focus) p.querySelector('.cerez-red').focus();
  }

  function init() {
    var state = read();
    if (state === true) apply(true);
    else if (state === null) open(false);

    document.addEventListener('click', function (e) {
      var t = e.target && e.target.closest ? e.target.closest('[data-cerez-tercih]') : null;
      if (!t) return;
      e.preventDefault();
      open(true);
    });
  }

  window.tmCerezTercih = function () { open(true); };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
