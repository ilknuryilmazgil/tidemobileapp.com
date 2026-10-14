(function () {
  // okuma ilerlemesi
  var bar = document.getElementById('readProgress');
  var art = document.querySelector('.prose');
  if (bar && art) {
    var tick = function () {
      var r = art.getBoundingClientRect();
      var total = r.height - window.innerHeight * 0.6;
      var p = Math.min(1, Math.max(0, -r.top / (total > 0 ? total : 1)));
      bar.style.transform = 'scaleX(' + p + ')';
    };
    window.addEventListener('scroll', tick, { passive: true });
    window.addEventListener('resize', tick);
    tick();
  }

  // içindekiler: görünen bölümü vurgula
  var links = document.querySelectorAll('.toc a');
  if (links.length && 'IntersectionObserver' in window) {
    var map = {};
    links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (a) { a.classList.remove('is-active'); });
        var a = map[en.target.id];
        if (a) a.classList.add('is-active');
      });
    }, { rootMargin: '-20% 0px -70% 0px' });
    Object.keys(map).forEach(function (id) {
      var h = document.getElementById(id);
      if (h) io.observe(h);
    });
  }

  // blog kategori süzgeci
  var grid = document.getElementById('postGrid');
  var btns = document.querySelectorAll('.filters button');
  if (grid && btns.length) {
    btns.forEach(function (b) {
      b.addEventListener('click', function () {
        var f = b.getAttribute('data-filter');
        btns.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        grid.querySelectorAll('.post').forEach(function (card) {
          card.hidden = f !== 'all' && card.getAttribute('data-cat') !== f;
        });
      });
    });
  }
})();
