/* Hero: interactive alignment field.
   A grid of randomly-angled tick marks. Ticks near the pointer rotate into
   alignment and darken — chaos resolving into order as you move through it. */
(function () {
  var canvas = document.querySelector('[data-hero-field]');
  if (!canvas) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var ctx = canvas.getContext('2d');
  var ticks = [];
  var w = 0, h = 0, dpr = 1;
  var pointer = { x: -9999, y: -9999, active: false };
  var RADIUS = 190;
  var raf = null;

  function build() {
    var rect = canvas.getBoundingClientRect();
    w = rect.width; h = rect.height;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var step = w < 700 ? 34 : 44;
    var cols = Math.ceil(w / step);
    var rows = Math.ceil(h / step);
    var offX = (w - (cols - 1) * step) / 2;
    var offY = (h - (rows - 1) * step) / 2;

    ticks = [];
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) {
        var base = Math.random() * Math.PI;
        ticks.push({
          x: offX + c * step,
          y: offY + r * step,
          base: base,
          a: base,
          e: 0
        });
      }
    }
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);
    ctx.lineCap = 'round';
    for (var i = 0; i < ticks.length; i++) {
      var t = ticks[i];
      var target = 0, energy = 0;
      if (pointer.active) {
        var dx = pointer.x - t.x, dy = pointer.y - t.y;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (d < RADIUS) {
          energy = 1 - d / RADIUS;
          energy = energy * energy;
        }
      }
      // aligned angle when energised, own angle at rest
      var aim = t.base + (0 - normalize(t.base)) * energy;
      t.a += (aim - t.a) * 0.12;
      t.e += (energy - t.e) * 0.12;

      var len = 9 + t.e * 9;
      var alpha = 0.14 + t.e * 0.72;
      ctx.strokeStyle = (night() ? 'rgba(236,230,246,' : 'rgba(58,46,57,') + alpha.toFixed(3) + ')';
      ctx.lineWidth = 1 + t.e * 0.6;
      ctx.beginPath();
      ctx.moveTo(t.x - Math.cos(t.a) * len / 2, t.y - Math.sin(t.a) * len / 2);
      ctx.lineTo(t.x + Math.cos(t.a) * len / 2, t.y + Math.sin(t.a) * len / 2);
      ctx.stroke();
    }
    raf = requestAnimationFrame(draw);
  }

  // ticks are drawn light on the Night theme
  function night() { return document.documentElement.dataset.theme === 'night'; }

  // how far `base` sits from horizontal, signed, so easing pulls the short way
  function normalize(base) {
    var a = base % Math.PI;
    return a > Math.PI / 2 ? a - Math.PI : a;
  }

  function move(e) {
    var rect = canvas.getBoundingClientRect();
    pointer.x = e.clientX - rect.left;
    pointer.y = e.clientY - rect.top;
    pointer.active = true;
  }

  function leave() { pointer.active = false; }

  function start() {
    build();
    if (raf) cancelAnimationFrame(raf);
    if (reduce.matches) {
      pointer.active = false;
      ctx.clearRect(0, 0, w, h);
      ctx.lineCap = 'round';
      for (var i = 0; i < ticks.length; i++) {
        var t = ticks[i];
        ctx.strokeStyle = night() ? 'rgba(236, 230, 246, 0.14)' : 'rgba(56, 52, 48, 0.14)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(t.x - Math.cos(t.base) * 4.5, t.y - Math.sin(t.base) * 4.5);
        ctx.lineTo(t.x + Math.cos(t.base) * 4.5, t.y + Math.sin(t.base) * 4.5);
        ctx.stroke();
      }
      return;
    }
    raf = requestAnimationFrame(draw);
  }

  var hero = canvas.closest('.hero') || document.body;
  hero.addEventListener('pointermove', move);
  hero.addEventListener('pointerleave', leave);
  hero.addEventListener('pointerdown', move);
  // touch has no hover: a lifted finger should settle the field just like a
  // mouse leaving, even if the browser doesn't also fire pointerleave for it
  hero.addEventListener('pointerup', leave);
  hero.addEventListener('pointercancel', leave);

  var t0;
  window.addEventListener('resize', function () {
    clearTimeout(t0);
    t0 = setTimeout(start, 180);
  });
  reduce.addEventListener('change', start);
  window.addEventListener('site-theme', start);

  start();

  // staggered entrance for the hero copy
  document.documentElement.setAttribute('data-hero-ready', 'true');
})();

/* Hero name: per-letter pointer reactivity.
   Letters closest to the cursor lift and gain weight, then settle back. */
(function () {
  var name = document.querySelector('.hero-name');
  if (!name) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var source = name.textContent;
  name.setAttribute('aria-label', source);
  name.textContent = '';

  var chars = [];
  source.split('').forEach(function (ch) {
    var span = document.createElement('span');
    span.className = 'hero-char';
    span.setAttribute('aria-hidden', 'true');
    if (ch === ' ') {
      span.innerHTML = '&nbsp;';
      span.style.setProperty('--space', '1');
    } else {
      span.textContent = ch;
      span.setAttribute('data-ch', ch);
    }
    name.appendChild(span);
    chars.push(span);
  });

  var QUALITIES = [
    'Asks why before how',
    'Yes to honest feedback',
    'Understands the whole system',
    'Simplifies complex flows',
    'Hears users out',
    'Iterates until it works',
    'Makes hard things clear',
    'Always learning',
    'Unpacks messy problems',
    'Respects real constraints',
    'Yes to simple solutions',
    'Attention to detail'
  ];
  var bubble = document.querySelector('[data-hero-bubble]');
  var bubbleText = document.querySelector('[data-hero-bubble-text]');
  var FILLS = ['#f7c6d4', '#ffe7a3', '#d9cdf7', '#fbd6bd', '#f2d4ee', '#e6dcfa'];
  var qIndex = 0;
  chars.forEach(function (el) {
    if (el.style.getPropertyValue('--space') === '1') return;
    el.setAttribute('data-quality', QUALITIES[qIndex % QUALITIES.length]);
    qIndex++;
  });
  var shown = null;

  var boxes = [];
  var RADIUS = 150;
  var pointer = { x: -9999, y: -9999, active: false };
  var raf = null;

  function measure() {
    boxes = chars.map(function (el) {
      var r = el.getBoundingClientRect();
      return { el: el, x: r.left + r.width / 2, y: r.top + r.height / 2, e: 0 };
    });
  }

  function tick() {
    var moving = false;
    for (var i = 0; i < boxes.length; i++) {
      var b = boxes[i];
      var target = 0;
      if (pointer.active) {
        var dx = pointer.x - b.x, dy = pointer.y - b.y;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (d < RADIUS) {
          target = 1 - d / RADIUS;
          target = target * target;
        }
      }
      b.e += (target - b.e) * 0.4;
      if (b.e > 0.002) moving = true;
      b.el.style.transform = 'translateY(' + (-b.e * 14).toFixed(2) + 'px) scale(' + (1 + b.e * 0.06).toFixed(3) + ')';
    }

    if (bubble && bubbleText) {
      var top = null, best = 0, anchor = null, anchorBox = null;
      for (var j = 0; j < boxes.length; j++) {
        var q = boxes[j].el.getAttribute('data-quality');
        if (q && boxes[j].e > best) { best = boxes[j].e; top = q; anchor = boxes[j].el; anchorBox = boxes[j]; }
      }
      if (best > 0.32 && top && anchor) {
        if (top !== shown) {
          var glyph = anchor.getAttribute('data-ch') || '';
          bubbleText.innerHTML = '<b>' + glyph + '</b>' + top.slice(1);
          bubble.style.setProperty('--fill', FILLS[boxes.indexOf(anchorBox) % FILLS.length]);
          shown = top;
        }
        var r = anchor.getBoundingClientRect();
        var letterCx = r.left + r.width / 2;
        var bw = bubbleText.offsetWidth || 0;
        void anchorBox;
        var pad = 12;
        var minCx = bw / 2 + pad;
        var maxCx = window.innerWidth - bw / 2 - pad;
        var cx = maxCx < minCx ? window.innerWidth / 2 : Math.min(Math.max(letterCx, minCx), maxCx);
        bubble.style.left = Math.round(cx) + 'px';
        bubble.style.top = Math.round(r.top + r.height * 0.28) + 'px';
        var tail = Math.max(-bw / 2 + 14, Math.min(bw / 2 - 14, letterCx - cx));
        bubble.style.setProperty('--tail-x', Math.round(tail) + 'px');
        bubble.setAttribute('data-visible', 'true');
      } else if (shown !== null) {
        bubble.setAttribute('data-visible', 'false');
        shown = null;
      }
    }
    raf = moving || pointer.active ? requestAnimationFrame(tick) : null;
  }

  function wake() { if (!raf) raf = requestAnimationFrame(tick); }

  var hero = name.closest('.hero') || document.body;
  hero.addEventListener('pointermove', function (e) {
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    pointer.active = true;
    wake();
  });
  var settle = function () {
    pointer.active = false;
    wake();
  };
  hero.addEventListener('pointerleave', settle);
  // touch has no hover: settle the letters on lift too, not just on leave
  hero.addEventListener('pointerup', settle);
  hero.addEventListener('pointercancel', settle);

  var t;
  window.addEventListener('resize', function () {
    clearTimeout(t);
    t = setTimeout(measure, 180);
  });
  window.addEventListener('scroll', measure, { passive: true });

  measure();
  setTimeout(measure, 900); // after the entrance animation settles
})();

/* Hero collage: a painterly brush stroke wipes the white away as you move.
   A mask canvas accumulates bristly stamps along the pointer path and slowly
   fades, so the reveal reads as wet paint drying rather than a spotlight. */
(function () {
  var canvas = document.querySelector('[data-hero-photo]');
  if (!canvas) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var ctx = canvas.getContext('2d');
  var mask = document.createElement('canvas');
  var mctx = mask.getContext('2d');
  var img = new Image();
  var ready = false;
  var w = 0, h = 0, dpr = 1;
  var hero = canvas.closest('.hero') || document.body;
  var last = null;
  var queue = [];
  var raf = null;
  var painted = false;

  // per-stamp bristle offsets, fixed so the brush keeps a consistent shape
  var BRISTLES = [];
  for (var i = 0; i < 9; i++) {
    BRISTLES.push({
      o: (i - 4) / 4,
      r: 38 + Math.random() * 34,
      a: 0.5 + Math.random() * 0.5
    });
  }

  img.onload = function () { ready = true; resize(); wake(); };
  img.src = 'assets/hero-collage.png';

  function resize() {
    var rect = canvas.getBoundingClientRect();
    w = rect.width; h = rect.height;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = mask.width = Math.round(w * dpr);
    canvas.height = mask.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    mctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    mctx.clearRect(0, 0, w, h);
  }

  function stamp(x, y, nx, ny, speed) {
    // brush is perpendicular to travel; wobble gives it a hand-made edge
    var px = -ny, py = nx;
    var scale = 0.75 + Math.min(speed / 26, 1) * 0.6;
    for (var i = 0; i < BRISTLES.length; i++) {
      var b = BRISTLES[i];
      var off = b.o * 66 * scale;
      var jx = x + px * off + (Math.random() - 0.5) * 7;
      var jy = y + py * off + (Math.random() - 0.5) * 7;
      var r = b.r * scale * (0.85 + Math.random() * 0.3);
      var g = mctx.createRadialGradient(jx, jy, 0, jx, jy, r);
      var edge = 1 - Math.abs(b.o) * 0.55;
      g.addColorStop(0, 'rgba(0,0,0,' + (b.a * edge).toFixed(3) + ')');
      g.addColorStop(0.6, 'rgba(0,0,0,' + (b.a * edge * 0.45).toFixed(3) + ')');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      mctx.fillStyle = g;
      mctx.beginPath();
      mctx.arc(jx, jy, r, 0, Math.PI * 2);
      mctx.fill();
    }
    // dry-brush speckle trailing off the stroke
    for (var k = 0; k < 5; k++) {
      var sr = 2 + Math.random() * 7;
      var sx = x + px * (Math.random() - 0.5) * 130 + nx * (Math.random() - 0.5) * 40;
      var sy = y + py * (Math.random() - 0.5) * 130 + ny * (Math.random() - 0.5) * 40;
      mctx.fillStyle = 'rgba(0,0,0,' + (0.12 + Math.random() * 0.25).toFixed(3) + ')';
      mctx.beginPath();
      mctx.arc(sx, sy, sr, 0, Math.PI * 2);
      mctx.fill();
    }
  }

  var idle = 0;
  var inside = false;

  function frame() {
    var paintedThisFrame = false;
    // lay down everything queued since the last frame
    while (queue.length) {
      var p = queue.shift();
      if (last) {
        var dx = p.x - last.x, dy = p.y - last.y;
        var d = Math.sqrt(dx * dx + dy * dy) || 1;
        var nx = dx / d, ny = dy / d;
        var step = 9;
        for (var t = 0; t < d; t += step) {
          stamp(last.x + nx * t, last.y + ny * t, nx, ny, d);
          painted = true;
          paintedThisFrame = true;
        }
      }
      last = p;
    }

    idle = paintedThisFrame ? 0 : idle + 1;

    // dry-out: gentle while painting, decisive once the cursor stops or leaves
    var fade = paintedThisFrame ? 0.028 : 0.05;
    mctx.save();
    mctx.globalCompositeOperation = 'destination-out';
    mctx.fillStyle = 'rgba(0,0,0,' + fade + ')';
    mctx.fillRect(0, 0, w, h);
    mctx.restore();

    // a long idle inside the hero also dissolves, so paint never sits forever
    if (painted && !dissolving && inside && idle > 220) dissolve();

    ctx.clearRect(0, 0, w, h);
    if (ready && painted) {
      var ir = img.width / img.height;
      var cr = w / h;
      var dw, dh, dx2, dy2;
      if (ir > cr) { dh = h; dw = h * ir; } else { dw = w; dh = w / ir; }
      dx2 = (w - dw) / 2;
      dy2 = (h - dh) * 0.28;
      ctx.globalAlpha = 0.94;
      ctx.drawImage(img, dx2, dy2, dw, dh);
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'destination-in';
      ctx.drawImage(mask, 0, 0, w, h);
      ctx.globalCompositeOperation = 'source-over';
    }
    if (!dissolving && ++sampleTick % 10 === 0) sampleText();
    if (!painted && !inside && !dissolving) { raf = null; return; }
    raf = requestAnimationFrame(frame);
  }

  function wake() { if (!raf) raf = requestAnimationFrame(frame); }

  var dissolving = false;
  var dissolveTimer = null;

  function dissolve() {
    if (dissolving || !painted) return;
    dissolving = true;
    canvas.style.transition = 'opacity 620ms cubic-bezier(0.4, 0, 1, 1)';
    canvas.style.opacity = '0';
    for (var q = 0; q < texts.length; q++) texts[q].setAttribute('data-on-art', 'false');
    clearTimeout(dissolveTimer);
    dissolveTimer = setTimeout(function () {
      mctx.clearRect(0, 0, w, h);
      painted = false;
      last = null;
      dissolving = false;
      canvas.style.transition = 'none';
      canvas.style.opacity = '1';
    }, 660);
  }

  function undissolve() {
    clearTimeout(dissolveTimer);
    if (!dissolving) return;
    dissolving = false;
    mctx.clearRect(0, 0, w, h);
    painted = false;
    canvas.style.transition = 'none';
    canvas.style.opacity = '1';
  }

  var lift = function () {
    inside = false;
    last = null;
    dissolve();
    wake();
  };
  hero.addEventListener('pointerleave', lift);
  // touch has no hover: a lifted finger should dry the paint like a mouse
  // leaving, not linger as if still pointing at the last spot
  hero.addEventListener('pointerup', lift);
  hero.addEventListener('pointercancel', lift);

  hero.addEventListener('pointermove', function (ev) {
    inside = true;
    undissolve();
    var rect = canvas.getBoundingClientRect();
    queue.push({ x: ev.clientX - rect.left, y: ev.clientY - rect.top });
    if (queue.length > 24) queue.shift();
    wake();
  });

  var rt;
  window.addEventListener('resize', function () {
    clearTimeout(rt);
    rt = setTimeout(resize, 180);
  });

  // ---- text inversion: sample the painted mask beneath each text run ----
  var texts = [];
  (function collectTexts() {
    var chars = document.querySelectorAll('.hero-name .hero-char');
    for (var i = 0; i < chars.length; i++) texts.push(chars[i]);

    ['.hero-role', '.hero-statement', '.hero-support', '.hero-cta .btn-diagnose'].forEach(function (sel) {
      var el = document.querySelector(sel);
      if (!el) return;
      splitWords(el);
      var words = el.querySelectorAll('.hero-word');
      for (var k = 0; k < words.length; k++) texts.push(words[k]);
    });
  })();

  // wrap every word in its own span so inversion can follow the brush edge
  function splitWords(root) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    var nodes = [], n;
    while ((n = walker.nextNode())) if (n.nodeValue.trim()) nodes.push(n);
    nodes.forEach(function (node) {
      var frag = document.createDocumentFragment();
      node.nodeValue.split(/(\s+)/).forEach(function (part) {
        if (!part) return;
        if (/^\s+$/.test(part)) {
          frag.appendChild(document.createTextNode(part));
        } else {
          var s = document.createElement('span');
          s.className = 'hero-word';
          s.textContent = part;
          frag.appendChild(s);
        }
      });
      node.parentNode.replaceChild(frag, node);
    });
  }

  var sampleTick = 0;
  function sampleText() {
    if (!texts.length) return;
    var hrect = canvas.getBoundingClientRect();
    for (var i = 0; i < texts.length; i++) {
      var el = texts[i];
      var r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      var x0 = r.left - hrect.left, y0 = r.top - hrect.top;
      var cols = Math.max(2, Math.min(4, Math.round(r.width / 22)));
      var hit = 0, total = 0;
      for (var c = 0; c < cols; c++) {
        for (var rw = 0; rw < 2; rw++) {
          var sx = Math.round((x0 + (c + 0.5) * (r.width / cols)) * dpr);
          var sy = Math.round((y0 + (rw + 0.5) * (r.height / 2)) * dpr);
          if (sx < 0 || sy < 0 || sx >= mask.width || sy >= mask.height) continue;
          total++;
          try {
            if (mctx.getImageData(sx, sy, 1, 1).data[3] > 60) hit++;
          } catch (err) { return; }
        }
      }
      var on = total > 0 && hit / total > 0.3;
      if ((el.getAttribute('data-on-art') === 'true') !== on) {
        el.setAttribute('data-on-art', on ? 'true' : 'false');
      }
    }
  }

  resize();
  wake();
})();

/* Typewriter ticks: a short mechanical click as the cursor crosses each letter
   of the name. Muted until the visitor's first interaction (autoplay policy). */
(function () {
  var chars = document.querySelectorAll('.hero-name .hero-char');
  if (!chars.length) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;

  var ctx = null;
  var lastAt = -1;

  // only real activation gestures unlock audio — pointermove does not count,
  // and the listeners stay attached so a later gesture can still resume
  function arm() {
    try {
      if (!ctx) ctx = new AC();
      if (ctx.state !== 'running') ctx.resume();
    } catch (e) { ctx = null; }
  }
  // touchend/pointerup are included too — some mobile browsers only treat a
  // completed tap as a real activation gesture, not the initial touchstart
  ['pointerdown', 'pointerup', 'touchstart', 'touchend', 'keydown', 'wheel', 'scroll'].forEach(function (ev) {
    window.addEventListener(ev, arm, { passive: true });
  });
  // create the context eagerly and keep nudging it, so the very first hover
  // after any qualifying gesture already has a running context
  arm();

  // Typewriter strike: the sharp slap of the typebar on the platen, a metallic
  // ring from the linkage, and a low wooden thud from the carriage.
  function tick(bright) {
    if (!ctx) return;
    // on mobile the unlocking gesture and the first tick are the same touch
    // drag, so resume() is still pending here — schedule the sound anyway
    // instead of dropping it, since it plays as soon as the context wakes up
    if (ctx.state !== 'running') ctx.resume();
    var now = ctx.currentTime;
    if (now - lastAt < 0.03) return; // don't machine-gun on fast sweeps
    lastAt = now;

    var out = ctx.createGain();
    out.gain.value = bright ? 0.46 : 0.37;
    out.connect(ctx.destination);

    function noise(seconds, curve) {
      var len = Math.max(1, Math.floor(ctx.sampleRate * seconds));
      var buf = ctx.createBuffer(1, len, ctx.sampleRate);
      var d = buf.getChannelData(0);
      for (var i = 0; i < len; i++) {
        d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, curve);
      }
      var src = ctx.createBufferSource();
      src.buffer = buf;
      return src;
    }

    // 1. the slap — bright, very short, this is the character of a typewriter
    var slap = noise(0.014, 2.5);
    var slapBp = ctx.createBiquadFilter();
    slapBp.type = 'bandpass';
    slapBp.frequency.value = bright ? 2900 : 2400;
    slapBp.Q.value = 0.9;
    var slapG = ctx.createGain();
    slapG.gain.setValueAtTime(0.0001, now);
    slapG.gain.exponentialRampToValueAtTime(bright ? 0.34 : 0.27, now + 0.0015);
    slapG.gain.exponentialRampToValueAtTime(0.0001, now + 0.022);
    slap.connect(slapBp).connect(slapG).connect(out);

    // 2. metallic ring — two detuned partials, short and inharmonic
    [bright ? 1950 : 1700, bright ? 2980 : 2560].forEach(function (f, i) {
      var ring = ctx.createOscillator();
      ring.type = 'triangle';
      ring.frequency.value = f;
      var rg = ctx.createGain();
      rg.gain.setValueAtTime(0.0001, now);
      rg.gain.exponentialRampToValueAtTime(i === 0 ? 0.03 : 0.016, now + 0.004);
      rg.gain.exponentialRampToValueAtTime(0.0001, now + 0.055);
      ring.connect(rg).connect(out);
      ring.start(now);
      ring.stop(now + 0.07);
    });

    // 3. platen thud — low body so the strike lands on something solid
    var thud = ctx.createOscillator();
    thud.type = 'triangle';
    thud.frequency.setValueAtTime(230, now);
    thud.frequency.exponentialRampToValueAtTime(120, now + 0.04);
    var thudG = ctx.createGain();
    thudG.gain.setValueAtTime(0.0001, now);
    thudG.gain.exponentialRampToValueAtTime(0.14, now + 0.003);
    thudG.gain.exponentialRampToValueAtTime(0.0001, now + 0.06);
    thud.connect(thudG).connect(out);

    slap.start(now);
    thud.start(now);
    thud.stop(now + 0.08);
  }

  // "tik tac tac tac": first letter of each word is the bright tik
  var bright = [];
  var startWord = true;
  for (var i = 0; i < chars.length; i++) {
    var isSpace = !chars[i].getAttribute('data-ch');
    bright.push(!isSpace && startWord);
    startWord = isSpace;
  }

  var hint = null;
  function showHint() {
    if (hint || !ctx || ctx.state === 'running') return;
    var name = document.querySelector('.hero-name');
    if (!name) return;
    if (getComputedStyle(name).position === 'static') name.style.position = 'relative';
    hint = document.createElement('span');
    hint.className = 'hero-sound-hint';
    hint.textContent = 'click for sound';
    name.appendChild(hint);
  }
  function clearHint() {
    if (!hint) return;
    hint.setAttribute('data-gone', 'true');
    var el = hint;
    hint = null;
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 400);
  }
  window.addEventListener('pointerdown', clearHint);
  window.addEventListener('keydown', clearHint);

  var current = -1;
  document.addEventListener('pointermove', function (e) {
    var hit = -1;
    var live = document.querySelectorAll('.hero-name .hero-char');
    for (var j = 0; j < live.length; j++) {
      if (live[j].style.getPropertyValue('--space') === '1') continue;
      var r = live[j].getBoundingClientRect();
      // generous vertical band so ticks fire along the whole word
      if (e.clientX >= r.left && e.clientX <= r.right
        && e.clientY >= r.top - 10 && e.clientY <= r.bottom + 10) { hit = j; break; }
    }
    if (hit !== current) {
      if (hit !== -1) {
        if (ctx && ctx.state !== 'running') { ctx.resume(); showHint(); }
        tick(bright[hit]);
      }
      current = hit;
    }
  }, { passive: true });
})();
