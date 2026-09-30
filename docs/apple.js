/* ZeroDrift site behaviour: reveal on scroll, lazy in-view videos, highlights carousel, card rails. */
(function () {
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const io = (cb, opt) => ('IntersectionObserver' in window) ? new IntersectionObserver(cb, opt) : null;

  // 1. Reveal
  const rv = document.querySelectorAll('.rv');
  const ro = io(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); ro.unobserve(e.target); } }), { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  rv.forEach(el => ro ? ro.observe(el) : el.classList.add('in'));

  // 2. Lazy videos: <video data-src> loads near the viewport; data-auto plays muted while visible.
  const pick = v => (window.innerWidth <= 800 && v.dataset.srcSm) ? v.dataset.srcSm : v.dataset.src;
  const load = v => { if (!v.getAttribute('src') && v.dataset.src) v.src = pick(v); };
  const near = io(es => es.forEach(e => { if (e.isIntersecting) { load(e.target); near.unobserve(e.target); } }), { rootMargin: '600px 0px' });
  const vis = io(es => es.forEach(e => {
    const v = e.target;
    if (e.intersectionRatio >= 0.5) { if (!still && v.dataset.auto !== undefined && !v.closest('.hl')) { load(v); v.muted = true; v.play().catch(() => {}); } }
    else if (!v.paused) v.pause();
  }), { threshold: [0, 0.5] });
  document.querySelectorAll('video[data-src]').forEach(v => { near ? near.observe(v) : load(v); if (vis) vis.observe(v); });

  // 3. Highlights carousel
  document.querySelectorAll('.hl').forEach(hl => {
    const track = hl.querySelector('.hl-track'), cards = [...hl.querySelectorAll('.hl-card')];
    const dots = hl.querySelector('.hl-dots'), pp = hl.querySelector('.hl-pp');
    const DUR = +(hl.dataset.dur || 7);
    let cur = -1, timer = null, inView = false;
    cards.forEach((c, i) => { const b = document.createElement('button'); b.type = 'button'; b.setAttribute('aria-label', 'Slide ' + (i + 1)); b.innerHTML = '<i></i>'; b.onclick = () => go(i, true); dots.appendChild(b); });
    const btns = [...dots.children];
    const setActive = i => {
      if (i === cur) return; cur = i;
      btns.forEach((b, k) => { b.classList.toggle('on', k === i); const f = b.querySelector('i'); f.style.animation = 'none'; void f.offsetWidth; f.style.animation = ''; });
      hl.style.setProperty('--dur', DUR + 's');
      cards.forEach((c, k) => { const v = c.querySelector('video'); if (!v) return; if (k === i && inView) { load(v); v.muted = true; v.currentTime = 0; v.play().catch(() => {}); } else if (!v.paused) v.pause(); });
      schedule();
    };
    const go = (i, user) => { i = (i + cards.length) % cards.length; track.scrollTo({ left: cards[i].offsetLeft - track.offsetLeft - (parseFloat(getComputedStyle(track).paddingLeft) || 0), behavior: still ? 'auto' : 'smooth' }); setActive(i); if (user) schedule(); };
    const schedule = () => { clearTimeout(timer); if (!hl.classList.contains('paused') && inView) timer = setTimeout(() => go(cur + 1), DUR * 1000); };
    let st; track.addEventListener('scroll', () => { clearTimeout(st); st = setTimeout(() => {
      const x = track.scrollLeft; let best = 0, bd = 1e9; cards.forEach((c, k) => { const d = Math.abs(c.offsetLeft - track.offsetLeft - (parseFloat(getComputedStyle(track).paddingLeft) || 0) - x); if (d < bd) { bd = d; best = k; } }); setActive(best); }, 90); }, { passive: true });
    pp.onclick = () => { hl.classList.toggle('paused'); const v = cards[cur] && cards[cur].querySelector('video'); if (hl.classList.contains('paused')) { clearTimeout(timer); if (v) v.pause(); } else { if (v) v.play().catch(() => {}); schedule(); } };
    const o = io(es => es.forEach(e => { inView = e.intersectionRatio >= 0.35; if (inView) { if (cur < 0) setActive(0); else { const v = cards[cur].querySelector('video'); if (v && !hl.classList.contains('paused')) { load(v); v.play().catch(() => {}); } schedule(); } } else { clearTimeout(timer); cards.forEach(c => { const v = c.querySelector('video'); if (v && !v.paused) v.pause(); }); } }), { threshold: [0, 0.35] });
    if (still) hl.classList.add('paused');
    o ? o.observe(hl) : setActive(0);
  });

  // 4. Card rails: arrow buttons
  document.querySelectorAll('[data-rail]').forEach(ctl => {
    const rail = document.getElementById(ctl.dataset.rail); if (!rail) return;
    const step = () => (rail.querySelector('.rc') || rail).getBoundingClientRect().width + 20;
    ctl.querySelector('.prev').onclick = () => rail.scrollBy({ left: -step(), behavior: 'smooth' });
    ctl.querySelector('.next').onclick = () => rail.scrollBy({ left: step(), behavior: 'smooth' });
  });

  // 5. YouTube: load the player only when asked
  document.querySelectorAll('[data-yt]').forEach(btn => btn.addEventListener('click', () => {
    const f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + btn.dataset.yt + '?autoplay=1&rel=0&modestbranding=1';
    f.title = btn.getAttribute('aria-label') || 'Video'; f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen = true;
    btn.parentNode.replaceChildren(f);
  }));
})();

/* MK1 / MK2 views: PHOTO · VIDEO · 3D tabs (a missing file shows the "coming soon" panel).
   data-cycle="video,3d,photo" plays the tabs in turn while the card is on screen:
   the video runs to its end, 3D shows for 10 s, the photo for 5 s, then round again.
   Clicking a tab stops the cycle on that card. */
document.querySelectorAll('.rig-view').forEach(view => {
  const tabs = view.querySelectorAll('.rig-tabs button');
  const empty = view.querySelector('.rig-empty');
  const media = { photo: view.querySelector('img.rig-media'), video: view.querySelector('video.rig-media') };
  const missing = {};
  let cur = null, inView = false;
  const order = (view.dataset.cycle || '').split(',').filter(Boolean);
  let auto = order.length > 1 && !matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DWELL = { '3d': 10, photo: 5 };
  let held = 0;
  const playVideo = () => { const v = media.video; if (v && cur === 'video' && inView && !missing.video) { v.muted = true; v.play().catch(() => {}); } };
  const show = kind => {
    cur = kind; held = 0;
    tabs.forEach(t => t.classList.toggle('on', t.dataset.view === kind));
    view.classList.toggle('flat', kind !== '3d');
    Object.entries(media).forEach(([k, el]) => {
      if (!el) return;
      const on = k === kind && !missing[k];
      el.classList.toggle('show', on);
      if (k === 'video' && !on) el.pause();
    });
    playVideo();
    const gone = kind !== '3d' && (missing[kind] || !media[kind] || !media[kind].dataset.src);
    if (empty) empty.classList.toggle('show', !!gone);
  };
  const open = k => { const el = media[k]; if (el && el.dataset.src && !el.getAttribute('src')) el.setAttribute('src', el.dataset.src); show(k); };
  const next = () => {
    let k = order[(order.indexOf(cur) + 1) % order.length];
    if (missing[k]) k = order[(order.indexOf(k) + 1) % order.length];
    if (k === 'video' && media.video) try { media.video.currentTime = 0; } catch (e) {}
    open(k);
  };
  Object.entries(media).forEach(([k, el]) => {
    if (!el) return;
    el.addEventListener('error', () => { missing[k] = true; if (cur === k) { if (auto) next(); else show(k); } });
  });
  if (media.video) media.video.addEventListener('ended', () => { if (auto && cur === 'video') next(); else if (cur === 'video') { media.video.currentTime = 0; playVideo(); } });
  tabs.forEach(t => t.addEventListener('click', () => { auto = false; open(t.dataset.view); }));
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(es => es.forEach(e => {
      inView = e.intersectionRatio >= 0.35;
      if (inView) { if (cur === 'video') open('video'); }
      else if (media.video) media.video.pause();
    }), { threshold: [0, 0.35] }).observe(view);
  } else inView = true;
  let tick = performance.now();
  if (auto) setInterval(() => {
    const now = performance.now(), dt = Math.min(1, (now - tick) / 1000); tick = now;
    if (!inView || document.hidden || !DWELL[cur]) return;
    held += dt; if (held >= DWELL[cur]) next();
  }, 250);
  const first = view.dataset.default || '3d';
  if (first === '3d') cur = '3d';
  else if (first === 'video') show('video');   // the file loads when the card comes on screen
  else open(first);
});

/* Software screen recording: loads near the section, plays muted while at least
   half is on screen, 720p on phones. */
(function () {
  const v = document.getElementById('swVideo');
  if (!v || !('IntersectionObserver' in window)) return;
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const load = () => { if (!v.getAttribute('src')) v.src = window.innerWidth <= 800 && v.dataset.srcSm ? v.dataset.srcSm : v.dataset.src; };
  new IntersectionObserver((es, o) => { if (es.some(e => e.isIntersecting)) { load(); o.disconnect(); } }, { rootMargin: '300px 0px' }).observe(v);
  new IntersectionObserver(es => es.forEach(e => {
    if (e.intersectionRatio >= 0.5) { load(); if (!still) v.play().catch(() => {}); }
    else if (!v.paused) v.pause();
  }), { threshold: [0, 0.5] }).observe(v);
  const fs = document.getElementById('swFull');
  if (fs) fs.addEventListener('click', () => {
    load();
    if (v.requestFullscreen) v.requestFullscreen().catch(() => {}); else if (v.webkitEnterFullscreen) v.webkitEnterFullscreen();
    v.play().catch(() => {});
  });
})();

/* Product nav: highlight the section in view. */
(function () {
  const links = [...document.querySelectorAll('.pn-l a[href^="#"]')];
  if (!links.length || !('IntersectionObserver' in window)) return;
  const map = new Map(links.map(a => [a.getAttribute('href').slice(1), a]));
  const io = new IntersectionObserver(es => es.forEach(e => {
    const a = map.get(e.target.id); if (!a) return;
    if (e.isIntersecting) { links.forEach(l => l.classList.remove('on')); a.classList.add('on'); }
  }), { rootMargin: '-45% 0px -50% 0px' });
  map.forEach((a, id) => { const el = document.getElementById(id); if (el) io.observe(el); });
})();
