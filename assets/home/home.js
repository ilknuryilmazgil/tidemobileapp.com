(function () {
  var nav = document.getElementById('nav');
  var onScroll = function () { nav.classList.toggle('is-solid', window.scrollY > 12); };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  var toggle = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  var setMenu = function (open) {
    links.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) nav.classList.add('is-solid'); else onScroll();
  };
  toggle.addEventListener('click', function () { setMenu(!links.classList.contains('is-open')); });
  links.addEventListener('click', function (e) { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });

  var items = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add('is-in'); });
  }

  // Globlar: sayfa yüklendikten sonra, tarayıcı boşta iken (ilk açılış hızını etkilemez)
  if (document.querySelector('[data-globe]')) {
    var addGlobe = function () {
      if (addGlobe.done) return; addGlobe.done = 1;
      var s = document.createElement('script');
      s.src = 'assets/home/globe.js?v=2'; s.async = true;
      document.body.appendChild(s);
    };
    var idle = window.requestIdleCallback || function (f) { return setTimeout(f, 600); };
    if (document.readyState === 'complete') idle(addGlobe);
    else window.addEventListener('load', function () { idle(addGlobe); });
  }

  var form = document.getElementById('contactForm');
  var status = document.getElementById('formStatus');
  if (form && window.fetch) {
    var en = document.documentElement.lang === 'en';
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      btn.disabled = true;
      status.className = 'form-status';
      status.textContent = en ? 'Sending...' : 'Gönderiliyor...';
      fetch(form.action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          form.reset();
          status.textContent = en ? 'Thank you, your message has reached us.' : 'Teşekkürler, mesajın bize ulaştı.';
        })
        .catch(function () {
          status.className = 'form-status err';
          status.textContent = en ? 'Could not send. Please email tidemobile.contact@gmail.com.' : 'Gönderilemedi. Lütfen tidemobile.contact@gmail.com adresine yaz.';
        })
        .then(function () { btn.disabled = false; });
    });
  }
})();
