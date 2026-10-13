/* TerraVisa kartı: etkileşimli 3D glob (d3-geo, canvas) */
(function () {
  if (window.__tideGlobe) return;
  window.__tideGlobe = 1;
  var hosts = document.querySelectorAll('[data-globe]');
  if (!hosts.length) return;
  var base = (document.currentScript && document.currentScript.src || '').replace(/globe\.js.*$/, '');
  var lang = document.documentElement.lang === 'en' ? 'en' : 'tr';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function load(src) {
    return new Promise(function (ok, fail) {
      var s = document.createElement('script');
      s.src = base + src; s.onload = ok; s.onerror = fail;
      document.head.appendChild(s);
    });
  }

  load('vendor/d3-array.min.js')
    .then(function () { return load('vendor/d3-geo.min.js'); })
    .then(function () { return load('vendor/topojson-client.min.js'); })
    .then(function () { return fetch(base + 'vendor/world-110m.json'); })
    .then(function (r) { return r.json(); })
    .then(function (topo) { for (var i = 0; i < hosts.length; i++) start(topo, hosts[i]); })
    .catch(function () { /* poster görseli yerinde kalır */ });

  function start(topo, host) {
    var mini = host.getAttribute('data-globe') === 'mini';
    var d3 = window.d3, topojson = window.topojson;
    var countries = topojson.feature(topo, topo.objects.countries).features;
    var borders = topojson.mesh(topo, topo.objects.countries, function (a, b) { return a !== b; });
    var graticule = d3.geoGraticule10();
    var sphere = { type: 'Sphere' };
    var ADANA = [35.32, 37.0];

    var names = null;
    try { names = new Intl.DisplayNames([lang], { type: 'region' }); } catch (e) {}
    var special = {
      'N. Cyprus': { tr: 'Kuzey Kıbrıs', en: 'Northern Cyprus' },
      'Somaliland': { tr: 'Somaliland', en: 'Somaliland' }
    };
    function nameOf(f) {
      var p = f.properties;
      if (special[p.n]) return special[p.n][lang];
      if (names && p.a2) { try { return names.of(p.a2); } catch (e) {} }
      return p.n;
    }

    var canvas = document.createElement('canvas');
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', lang === 'en'
      ? 'Interactive 3D globe. Drag to rotate, hover a country to see its name.'
      : 'Etkileşimli 3D dünya globu. Çevirmek için sürükle, adını görmek için bir ülkenin üzerine gel.');
    var tip = host.querySelector('.globe-tip');
    if (mini) { canvas.setAttribute('aria-hidden', 'true'); canvas.removeAttribute('role'); canvas.removeAttribute('aria-label'); }
    host.insertBefore(canvas, tip || null);
    var ctx = canvas.getContext('2d');

    var proj = d3.geoOrthographic().clipAngle(90).precision(0.4);
    var path = d3.geoPath(proj, ctx);
    var rot = [-30, -32, 0];
    var size = 0, dpr = 1;

    function resize() {
      var w = host.clientWidth;
      if (!w) return;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      size = w;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(w * dpr);
      proj.translate([w / 2, w / 2]).scale(w / 2 - (mini ? 2 : 6));
      draw();
    }

    var hover = null;

    function draw() {
      if (!size) return;
      var r = proj.scale(), c = size / 2;
      proj.rotate(rot);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, size, size);

      // atmosfer
      var atm = ctx.createRadialGradient(c, c, r * 0.96, c, c, r * 1.06);
      atm.addColorStop(0, 'rgba(140,205,240,.55)');
      atm.addColorStop(1, 'rgba(140,205,240,0)');
      ctx.fillStyle = atm;
      ctx.beginPath(); ctx.arc(c, c, r * 1.06, 0, 2 * Math.PI); ctx.fill();

      // okyanus
      var sea = ctx.createRadialGradient(c - r * 0.35, c - r * 0.4, r * 0.1, c, c, r);
      sea.addColorStop(0, '#bfe7f7');
      sea.addColorStop(0.55, '#79c3e6');
      sea.addColorStop(1, '#3d93c4');
      ctx.beginPath(); path(sphere); ctx.fillStyle = sea; ctx.fill();

      ctx.beginPath(); path(graticule);
      ctx.strokeStyle = 'rgba(255,255,255,.28)'; ctx.lineWidth = 0.6; ctx.stroke();

      // kara
      ctx.beginPath();
      for (var i = 0; i < countries.length; i++) path(countries[i]);
      ctx.fillStyle = '#fbf5ea'; ctx.fill();

      if (hover) {
        ctx.beginPath(); path(hover);
        ctx.fillStyle = '#ffcfa6'; ctx.fill();
      }

      ctx.beginPath(); path(borders);
      ctx.strokeStyle = 'rgba(150,128,98,.55)'; ctx.lineWidth = mini ? 0.35 : 0.5; ctx.stroke();

      // Adana işareti (görünür yüzdeyse)
      if (!mini && d3.geoDistance(ADANA, [-rot[0], -rot[1]]) < Math.PI / 2 - 0.05) {
        var p = proj(ADANA);
        ctx.beginPath(); ctx.arc(p[0], p[1], 5.5, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(58,159,160,.25)'; ctx.fill();
        ctx.beginPath(); ctx.arc(p[0], p[1], 3, 0, 2 * Math.PI);
        ctx.fillStyle = '#2f8f91'; ctx.fill();
        ctx.lineWidth = 1.2; ctx.strokeStyle = '#fff'; ctx.stroke();
      }

      // gölge ve parlama: küreye hacim verir
      var shade = ctx.createRadialGradient(c - r * 0.45, c - r * 0.5, r * 0.2, c, c, r * 1.02);
      shade.addColorStop(0, 'rgba(255,255,255,0)');
      shade.addColorStop(0.7, 'rgba(20,60,100,.06)');
      shade.addColorStop(1, 'rgba(15,45,85,.38)');
      ctx.beginPath(); path(sphere); ctx.fillStyle = shade; ctx.fill();

      var spec = ctx.createRadialGradient(c - r * 0.42, c - r * 0.48, 0, c - r * 0.42, c - r * 0.48, r * 0.55);
      spec.addColorStop(0, 'rgba(255,255,255,.42)');
      spec.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.beginPath(); path(sphere); ctx.fillStyle = spec; ctx.fill();

      ctx.beginPath(); path(sphere);
      ctx.strokeStyle = 'rgba(255,255,255,.55)'; ctx.lineWidth = 1; ctx.stroke();
    }

    // ---- hareket döngüsü
    var visible = false, dragging = false, vx = 0, vy = 0, lastT = 0, idleUntil = 0, raf = 0;
    var SPIN = mini ? 10 : 7; // derece / saniye

    function tick(t) {
      raf = 0;
      var dt = lastT ? Math.min((t - lastT) / 1000, 0.05) : 0;
      lastT = t;
      var moving = false;
      if (!dragging) {
        if (Math.abs(vx) > 0.01 || Math.abs(vy) > 0.01) {
          rot[0] += vx * dt * 60; rot[1] = clampLat(rot[1] - vy * dt * 60);
          vx *= Math.pow(0.9, dt * 60); vy *= Math.pow(0.9, dt * 60);
          moving = true;
        } else if (!reduce && t > idleUntil) {
          rot[0] += SPIN * dt; moving = true;
        }
      }
      if (moving) draw();
      if (visible && !document.hidden && (moving || !reduce)) raf = requestAnimationFrame(tick);
      else lastT = 0;
    }
    function kick() { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(tick); }
    function clampLat(v) { return Math.max(-70, Math.min(70, v)); }

    // ---- sürükleme
    var px = 0, py = 0;
    if (!mini) {
    canvas.addEventListener('pointerdown', function (e) {
      dragging = true; px = e.clientX; py = e.clientY; vx = vy = 0;
      canvas.setPointerCapture(e.pointerId);
      host.classList.add('is-grabbing', 'was-used');
    });
    canvas.addEventListener('pointermove', function (e) {
      if (dragging) {
        var k = 180 / size;
        var dx = (e.clientX - px) * k, dy = (e.clientY - py) * k;
        px = e.clientX; py = e.clientY;
        rot[0] += dx; rot[1] = clampLat(rot[1] - dy);
        vx = dx; vy = dy;
        hideTip(); draw();
        return;
      }
      pick(e);
    });
    function endDrag() {
      if (!dragging) return;
      dragging = false; host.classList.remove('is-grabbing');
      idleUntil = performance.now() + 2200; kick();
    }
    canvas.addEventListener('pointerup', function (e) {
      var tap = Math.abs(vx) < 0.4 && Math.abs(vy) < 0.4;
      endDrag();
      if (tap) pick(e, true);
    });
    canvas.addEventListener('pointercancel', endDrag);
    canvas.addEventListener('pointerleave', function () { if (!dragging) { hover = null; hideTip(); draw(); } });

    // ---- ülke seçimi
    function pick(e, sticky) {
      var b = canvas.getBoundingClientRect();
      var x = e.clientX - b.left, y = e.clientY - b.top;
      var c = size / 2, r = proj.scale();
      var found = null;
      if ((x - c) * (x - c) + (y - c) * (y - c) < r * r) {
        var ll = proj.invert([x, y]);
        if (ll) for (var i = 0; i < countries.length; i++) {
          if (d3.geoContains(countries[i], ll)) { found = countries[i]; break; }
        }
      }
      if (found !== hover) { hover = found; draw(); }
      if (found) {
        tip.textContent = nameOf(found);
        tip.style.left = x + 'px'; tip.style.top = y + 'px';
        tip.hidden = false;
        idleUntil = performance.now() + (sticky ? 3500 : 1200);
      } else hideTip();
    }
    }
    function hideTip() { if (tip) tip.hidden = true; }

    // ---- görünürlük
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (en) {
        visible = en[0].isIntersecting;
        if (visible) kick();
      }, { threshold: 0.05 }).observe(host);
    } else { visible = true; }
    document.addEventListener('visibilitychange', kick);
    if ('ResizeObserver' in window) new ResizeObserver(resize).observe(host);
    else window.addEventListener('resize', resize);

    resize();
    host.classList.add('is-live');
    kick();
  }
})();
