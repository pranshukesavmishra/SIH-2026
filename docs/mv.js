/* Mission viewer: chapter rail, synced KPIs and custom transport for the 3D simulation.
   Loads (720p on phones) when reached and plays muted while at least half visible. */
(function () {
  const mv = document.getElementById('mv'), v = document.getElementById('filmVideo');
  if (!mv || !v) return;
  const $ = id => document.getElementById(id);
  const chBtns = [...document.querySelectorAll('#mvCh button')], times = chBtns.map(b => +b.dataset.t);
  const kpis = [...document.querySelectorAll('#mvKpi div')], track = $('mvTrack'), fill = $('mvFill'), tc = $('mvTc'), stage = $('mvStage');
  const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const load = () => { if (!v.getAttribute('src')) v.src = window.innerWidth <= 800 ? 'media/ZeroDrift_ISRO_Simulation_720p.mp4' : 'media/ZeroDrift_ISRO_Simulation_1080p.mp4'; };
  const dur = () => v.duration || 100;
  let cur = -1;
  const update = () => {
    const t = v.currentTime || 0, d = dur();
    fill.style.width = (100 * t / d) + '%'; track.setAttribute('aria-valuenow', Math.round(100 * t / d));
    const m = Math.floor(t / 60), sec = (t % 60).toFixed(1).padStart(4, '0');
    tc.textContent = 'T+' + String(m).padStart(2, '0') + ':' + sec;
    let k = 0; times.forEach((x, i) => { if (t >= x) k = i; });
    if (k !== cur) {
      cur = k;
      chBtns.forEach((b, i) => { b.classList.toggle('on', i === k); b.classList.toggle('done', i < k); });
      stage.querySelector('em').textContent = String(k).padStart(2, '0');
      stage.querySelector('span').innerHTML = chBtns[k].querySelector('span').innerHTML;
      kpis.forEach(el => el.classList.toggle('hot', +el.dataset.ch === k || (k === 7)));
      const on = chBtns[k]; if (on && on.parentNode.parentNode.scrollWidth > on.parentNode.parentNode.clientWidth) on.parentNode.parentNode.scrollTo({ left: on.parentNode.offsetLeft - 12, behavior: 'smooth' });
    }
  };
  const play = () => { load(); mv.classList.add('started'); v.play().catch(() => {}); };
  const seek = t => { load(); const go = () => { v.currentTime = t; update(); }; v.readyState ? go() : v.addEventListener('loadedmetadata', go, { once: true }); };
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
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((es, o) => { if (es.some(e => e.isIntersecting)) { load(); o.disconnect(); } }, { rootMargin: '300px 0px' }).observe(mv);
    new IntersectionObserver(es => es.forEach(e => {
      if (e.intersectionRatio >= 0.5) { if (!still && !mv.dataset.auto) { mv.dataset.auto = '1'; play(); } }
      else if (!v.paused) v.pause();
    }), { threshold: [0, 0.5] }).observe(mv);
  }
})();
