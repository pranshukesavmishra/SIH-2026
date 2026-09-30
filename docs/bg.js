/* Page background: a very dim grid of stars that drifts slowly. Near the cursor the
   stars part gently and faint lines join them, like a small constellation.
   Kept deliberately quiet so it never competes with the text. Dark pages only. */
(function () {
  if (!document.body || document.body.classList.contains('light')) return;
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cv = document.createElement('canvas');
  cv.id = 'bgStars'; cv.setAttribute('aria-hidden', 'true');
  document.body.prepend(cv);
  const x = cv.getContext('2d');
  const SP = 46;                                   // grid spacing (px)
  let W = 0, H = 0, dpr = 1, cols = 0, rows = 0, stars = [];
  const mouse = { x: -9999, y: -9999, sx: -9999, sy: -9999 };
  let s = 3; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;

  const build = () => {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = innerWidth; H = innerHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    cols = Math.ceil(W / SP) + 2; rows = Math.ceil(H / SP) + 2;
    s = 3; stars = [];
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      stars.push({ i, j, jx: (rnd() - .5) * SP * .5, jy: (rnd() - .5) * SP * .5, b: .25 + rnd() * .75, ph: rnd() * 6.28, big: rnd() > .965, ox: 0, oy: 0 });
    }
  };
  build();
  addEventListener('resize', build);
  addEventListener('pointermove', e => { mouse.x = e.clientX; mouse.y = e.clientY; if (mouse.sx < -999) { mouse.sx = mouse.x; mouse.sy = mouse.y; } }, { passive: true });
  document.addEventListener('pointerleave', () => { mouse.x = mouse.y = -9999; });

  const R = 170;                                   // cursor influence radius
  let last = 0, t0 = performance.now();
  const draw = now => {
    if (!still) requestAnimationFrame(draw);
    if (document.hidden || now - last < 32) return;    // ~30 fps is plenty for this
    last = now;
    const t = (now - t0) / 1000;
    mouse.sx += (mouse.x - mouse.sx) * .12; mouse.sy += (mouse.y - mouse.sy) * .12;
    // the whole field drifts slowly down and to the left
    const offX = -(t * 5) % SP, offY = (t * 8) % SP;
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    x.clearRect(0, 0, W, H);
    const pos = new Float32Array(stars.length * 2), near = [];
    for (let k = 0; k < stars.length; k++) {
      const st = stars[k];
      let px = st.i * SP + st.jx + offX - SP, py = st.j * SP + st.jy + offY - SP;
      const dx = px - mouse.sx, dy = py - mouse.sy, d = Math.hypot(dx, dy);
      let tx = 0, ty = 0;
      if (d < R && d > 0.1) { const f = (1 - d / R) ** 2 * 26; tx = dx / d * f; ty = dy / d * f; near.push(k); }
      st.ox += (tx - st.ox) * .1; st.oy += (ty - st.oy) * .1;
      px += st.ox; py += st.oy;
      pos[k * 2] = px; pos[k * 2 + 1] = py;
      const tw = .65 + .35 * Math.sin(t * 1.1 + st.ph);
      const glow = d < R ? (1 - d / R) : 0;
      const a = (0.13 + 0.2 * st.b) * tw + glow * 0.3;
      x.fillStyle = glow > 0.05 ? `rgba(150,220,255,${a})` : `rgba(210,220,240,${a})`;
      const r = st.big ? 1.25 : 0.75;
      x.beginPath(); x.arc(px, py, r + glow * 0.6, 0, 6.2832); x.fill();
    }
    // faint constellation lines between neighbouring stars near the cursor
    if (near.length) {
      x.lineWidth = 0.6;
      for (const k of near) {
        const px = pos[k * 2], py = pos[k * 2 + 1];
        const f = 1 - Math.hypot(px - mouse.sx, py - mouse.sy) / R;
        if (f <= 0) continue;
        for (const n of [k + 1, k + cols, k + cols + 1]) {
          if (n >= stars.length) continue;
          const qx = pos[n * 2], qy = pos[n * 2 + 1];
          if (Math.abs(qx - px) > SP * 1.8) continue;
          x.strokeStyle = `rgba(120,200,240,${0.14 * f})`;
          x.beginPath(); x.moveTo(px, py); x.lineTo(qx, qy); x.stroke();
        }
      }
    }
  };
  requestAnimationFrame(draw);
})();
