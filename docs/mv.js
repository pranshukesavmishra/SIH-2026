/* Simulation player inside the laptop frame: the lid opens when the section is reached
   and closes when it leaves; chapter chips, callout markings and transport follow the video. */
(function () {
  const mv = document.getElementById('mv'), v = document.getElementById('filmVideo');
  if (!mv || !v) return;
  const $ = id => document.getElementById(id);
  const chBtns = [...document.querySelectorAll('#mvCh button')], times = chBtns.map(b => +b.dataset.t);
  const kpis = [...document.querySelectorAll('#mvKpi [data-ch]')], track = $('mvTrack'), fill = $('mvFill'), tc = $('mvTc'), stage = $('mvStage');
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const load = () => { if (!v.getAttribute('src')) v.src = window.innerWidth <= 800 ? 'media/ZeroDrift_ISRO_Simulation_720p.mp4' : 'media/ZeroDrift_ISRO_Simulation_1080p.mp4'; };
  const dur = () => v.duration || 100;
  const mmss = t => String(Math.floor(t / 60)).padStart(2, '0') + ':' + String(Math.floor(t % 60)).padStart(2, '0');
  let cur = -1;
  const update = () => {
    const t = v.currentTime || 0, d = dur();
    fill.style.width = (100 * t / d) + '%'; track.setAttribute('aria-valuenow', Math.round(100 * t / d));
    tc.textContent = mmss(t);
    let k = 0; times.forEach((x, i) => { if (t >= x) k = i; });
    if (k !== cur) {
      cur = k;
      chBtns.forEach((b, i) => { b.classList.toggle('on', i === k); b.classList.toggle('done', i < k); });
      const ic = chBtns[k].querySelector('svg');
      stage.innerHTML = (ic ? ic.outerHTML : '') + '<span>' + chBtns[k].dataset.label + '</span>';
      kpis.forEach(el => el.classList.toggle('hot', el.dataset.ch.split(',').includes(String(k)) || k === chBtns.length - 1));
      const on = chBtns[k], list = on.closest('ol');
      if (list && list.scrollWidth > list.clientWidth) list.scrollTo({ left: on.parentNode.offsetLeft - 12, behavior: 'smooth' });
    }
  };
  const play = () => { load(); mv.classList.add('started'); v.play().catch(() => {}); };
  // Some simple servers (for example Python's http.server) cannot serve part of a file, so the
  // browser cannot jump inside the video. If a jump does not land, load the file whole and jump again.
  let whole = false;
  const canReach = t => { for (let i = 0; i < v.seekable.length; i++) if (v.seekable.start(i) <= t && v.seekable.end(i) >= t - 0.5) return true; return false; };
  const loadWhole = t => {
    if (whole) return; whole = true;
    const wasPlaying = !v.paused;
    fetch(v.currentSrc || v.src).then(r => r.blob()).then(b => {
      v.src = URL.createObjectURL(b);
      v.addEventListener('loadedmetadata', () => { v.currentTime = t; update(); if (wasPlaying || mv.classList.contains('started')) v.play().catch(() => {}); }, { once: true });
    }).catch(() => {});
  };
  const seek = t => {
    load();
    const go = () => {
      if (!whole && t > 1 && !canReach(t)) return loadWhole(t);
      v.currentTime = t; update();
      if (!whole && t > 1) setTimeout(() => { if (Math.abs(v.currentTime - t) > 3 && v.currentTime < t) loadWhole(t); }, 700);
    };
    v.readyState ? go() : v.addEventListener('loadedmetadata', go, { once: true });
  };
  v.addEventListener('timeupdate', update);
  v.addEventListener('play', () => mv.classList.add('playing'));
  v.addEventListener('pause', () => mv.classList.remove('playing'));
  v.addEventListener('volumechange', () => mv.classList.toggle('sound', !v.muted));
  v.addEventListener('click', () => v.paused ? play() : v.pause());
  $('mvBig').addEventListener('click', () => { v.muted = false; play(); });
  $('mvPlay').addEventListener('click', () => v.paused ? play() : v.pause());
  $('mvMute').addEventListener('click', () => { v.muted = !v.muted; });
  chBtns.forEach(b => b.addEventListener('click', () => { seek(+b.dataset.t); play(); }));
  const pick = e => { const r = track.getBoundingClientRect(); seek(Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * dur()); };
  track.addEventListener('click', pick);
  track.addEventListener('keydown', e => { if (e.key === 'ArrowRight') seek(Math.min(dur(), v.currentTime + 5)); if (e.key === 'ArrowLeft') seek(Math.max(0, v.currentTime - 5)); });
  $('mvFs').addEventListener('click', () => {
    const el = $('mvScreen');
    if (document.fullscreenElement) document.exitFullscreen();
    else if (el.requestFullscreen) el.requestFullscreen().catch(() => {});
    else if (v.webkitEnterFullscreen) v.webkitEnterFullscreen();
  });
  v.muted = true; update();
  if (still) mv.classList.add('open');
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((es, o) => { if (es.some(e => e.isIntersecting)) { load(); o.disconnect(); } }, { rootMargin: '400px 0px' }).observe(mv);
    let openT = null;
    new IntersectionObserver(es => es.forEach(e => {
      if (e.intersectionRatio >= 0.45) {
        mv.classList.add('open');
        clearTimeout(openT);
        if (!still && !mv.dataset.auto) openT = setTimeout(() => { mv.dataset.auto = '1'; play(); }, 1500);
      } else if (e.intersectionRatio < 0.12) {
        clearTimeout(openT); if (!still) mv.classList.remove('open'); if (!v.paused) v.pause();
      }
    }), { threshold: [0, 0.12, 0.45] }).observe(mv);
  } else { mv.classList.add('open'); }
})();
