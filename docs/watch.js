/* Home · "Watch it decide": what the camera sees, simulated live.
   A 4.0 x 2.5 degree camera view. Two red lights: the beacon blinks at 4 Hz,
   the decoy glows steadily. The tracker scores each light's blink; a steady
   light scores zero however bright it is. Once the beacon is confirmed a
   type-2 loop steers the aim onto it while the platform drifts (a ramp).
   Cover the beacon and the aim coasts on the last measured motion; it never
   jumps to the decoy. Pixel figures are for this simulation only. */
(function () {
  const cv = document.getElementById('wdCanvas');
  if (!cv) return;
  const $ = id => document.getElementById(id);
  const g = cv.getContext('2d');
  const FOVW = 4.0, FOVH = 2.5, PXDEG = 160, STEP = 1 / 60, RESTART = 40;
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const S = {};
  const stars = Array.from({ length: 140 }, () => ({ az: (Math.random() - 0.5) * 40, el: (Math.random() - 0.5) * 20, a: 0.15 + Math.random() * 0.5, r: Math.random() < 0.12 ? 1.4 : 0.8 }));

  function reset() {
    Object.assign(S, { t: 0, boreAz: -1.6, boreEl: 0.7, tgtAz: 0, tgtEl: 0, i1: 0, i2: 0, i1e: 0,
      state: 'SEARCH', acqAt: null, score: 0, err: NaN, hist: [], scanDir: 1, scanC: -1.6, acc: [], covered: false });
    setCover(false);
  }

  const DESC = {
    SEARCH: 'Scanning the sky. No light has been tested yet.',
    ACQUIRE: 'Two lights in view. Scoring each one’s blink: identity is the 4 Hz rhythm, not brightness.',
    TRACK: 'Beacon confirmed. Closing the aim error while the platform drifts.',
    LOCK: 'Aim on the beacon. The loop holds it through the drift.',
    PREDICT: 'Beacon covered. Coasting on its last measured motion. The decoy is still ignored.',
  };
  const TONE = { SEARCH: '', ACQUIRE: 'warn', TRACK: 'acc', LOCK: 'ok', PREDICT: 'warn' };

  function step(dt) {
    S.t += dt;
    S.tgtAz += 0.50 * dt + 0.10 * Math.sin(S.t * 0.7) * dt;        // platform drift (a ramp) + weave
    S.tgtEl += 0.14 * dt + 0.08 * Math.cos(S.t * 0.9) * dt;
    const dAz = S.tgtAz - S.boreAz, dEl = S.tgtEl - S.boreEl;
    const inFrame = Math.abs(dAz) < FOVW / 2 && Math.abs(dEl) < FOVH / 2;
    const seen = inFrame && !S.covered;

    // blink score over a 1.5 s window: a steady light scores 0
    S.acc.push(seen ? (Math.sin(2 * Math.PI * 4 * S.t) > 0 ? 1 : 0) : 0.5);
    if (S.acc.length > 90) S.acc.shift();
    const mean = S.acc.reduce((a, b) => a + b, 0) / S.acc.length;
    S.score = seen && S.acc.length > 30 ? 1 - Math.abs(2 * mean - 1) : 0;

    if (S.state === 'SEARCH') {
      S.boreAz += S.scanDir * 1.6 * dt;
      if (Math.abs(S.boreAz - S.scanC) > 2.2) { S.scanDir *= -1; S.boreEl -= 0.3 * Math.sign(S.boreEl - S.tgtEl || 1); }
      if (seen) S.state = 'ACQUIRE';
    } else if (S.state === 'ACQUIRE') {
      if (!seen) { S.state = 'SEARCH'; S.scanC = S.boreAz; }
      else if (S.score > 0.7) { S.state = 'TRACK'; if (S.acqAt === null) S.acqAt = S.t; }
    } else if (S.state === 'PREDICT') {
      S.boreAz += (2.2 * S.i1 + 0.35 * S.i2) * dt;                   // keep the last measured rate
      S.boreEl += 2.2 * S.i1e * dt;
      if (!S.covered) { S.state = inFrame ? 'ACQUIRE' : 'SEARCH'; S.acc = []; S.scanC = S.boreAz; }
    }
    if (S.state === 'TRACK' || S.state === 'LOCK') {
      if (S.covered) S.state = 'PREDICT';
      else {
        const kp = 3.0, ki = 2.2, kii = 0.35, leak = Math.exp(-dt / 1.8);
        S.i1 += dAz * dt; S.i2 = S.i2 * leak + S.i1 * dt;
        S.boreAz += (kp * dAz + ki * S.i1 + kii * S.i2) * dt;
        S.i1e += dEl * dt;
        S.boreEl += (kp * dEl + ki * S.i1e) * dt;
        S.err = Math.hypot(S.tgtAz - S.boreAz, S.tgtEl - S.boreEl) * PXDEG;
        S.state = S.err < 12 ? 'LOCK' : 'TRACK';
      }
    }
    if (S.state !== 'TRACK' && S.state !== 'LOCK') S.err = inFrame ? Math.hypot(S.tgtAz - S.boreAz, S.tgtEl - S.boreEl) * PXDEG : NaN;
    S.hist.push({ t: S.t, e: S.err });
    while (S.hist.length && S.t - S.hist[0].t > 12) S.hist.shift();
  }

  function blob(x, y, r, col, a) {
    const q = g.createRadialGradient(x, y, 0, x, y, r);
    q.addColorStop(0, `rgba(${col},${a})`); q.addColorStop(0.35, `rgba(${col},${a * 0.5})`); q.addColorStop(1, `rgba(${col},0)`);
    g.fillStyle = q; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
  }
  function corners(x, y, h, col, w) {
    const k = h * 0.42; g.strokeStyle = col; g.lineWidth = w;
    g.beginPath();
    [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(([sx, sy]) => {
      g.moveTo(x + sx * h, y + sy * (h - k)); g.lineTo(x + sx * h, y + sy * h); g.lineTo(x + sx * (h - k), y + sy * h);
    });
    g.stroke();
  }

  let W = 0, H = 0, dpr = 1;
  function size() {
    const r = cv.getBoundingClientRect(); dpr = Math.min(2, devicePixelRatio || 1);
    W = Math.max(1, r.width); H = Math.max(1, r.height);
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
  }
  addEventListener('resize', size); size();

  function draw() {
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.fillStyle = '#02060d'; g.fillRect(0, 0, W, H);
    const top = 56, bot = W < 560 ? 80 : 66, side = 20, sc = Math.min((W - side * 2) / FOVW, (H - top - bot) / FOVH);
    const fw = FOVW * sc, fh = FOVH * sc, cx = W / 2, cy = top + (H - top - bot) / 2, fx = cx - fw / 2, fy = cy - fh / 2;
    const P = d => d * sc, mono = Math.max(10, Math.min(12, W / 70)) + 'px ui-monospace,SFMono-Regular,Menlo,monospace';

    g.save(); g.beginPath(); g.rect(fx, fy, fw, fh); g.clip();
    g.fillStyle = '#02060d'; g.fillRect(fx, fy, fw, fh);
    for (const s of stars) {                                        // the sky moves as the aim moves
      const x = cx + P(s.az - S.boreAz * 0.35), y = cy - P(s.el - S.boreEl * 0.35);
      g.fillStyle = `rgba(210,225,255,${s.a})`; g.fillRect(x, y, s.r, s.r);
    }
    g.fillStyle = 'rgba(255,255,255,.35)';                          // sensor noise
    for (let i = 0; i < 90; i++) g.fillRect(fx + Math.random() * fw | 0, fy + Math.random() * fh | 0, 1, 1);
    g.strokeStyle = 'rgba(79,199,234,.08)'; g.lineWidth = 1;        // 0.5 degree grid
    g.beginPath();
    for (let a = -2; a <= 2; a += 0.5) { g.moveTo(cx + P(a), fy); g.lineTo(cx + P(a), fy + fh); }
    for (let e = -1; e <= 1; e += 0.5) { g.moveTo(fx, cy + P(e)); g.lineTo(fx + fw, cy + P(e)); }
    g.stroke();
    g.strokeStyle = '#3a5a80'; g.lineWidth = 1.2;                   // boresight
    g.beginPath(); g.moveTo(cx - 18, cy); g.lineTo(cx - 6, cy); g.moveTo(cx + 6, cy); g.lineTo(cx + 18, cy);
    g.moveTo(cx, cy - 18); g.lineTo(cx, cy - 6); g.moveTo(cx, cy + 6); g.lineTo(cx, cy + 18); g.stroke();

    const bx = cx + P(S.tgtAz - S.boreAz), by = cy - P(S.tgtEl - S.boreEl);
    const narrow = W < 560, dx = bx + P(narrow ? -1.1 : 0.9), dy = by + P(narrow ? 0.3 : 0.55);
    const on = Math.sin(2 * Math.PI * 4 * S.t) > 0;
    const R = Math.max(14, sc * 0.13);
    blob(dx, dy, R * 1.2, '240,95,85', 0.85);                       // decoy: steady
    if (on && !S.covered) blob(bx, by, R, '255,60,60', 0.98);       // beacon: 4 Hz
    if (S.covered) {                                                // the card over the beacon
      g.fillStyle = 'rgba(40,44,52,.92)'; g.strokeStyle = 'rgba(255,200,90,.6)'; g.lineWidth = 1;
      g.beginPath(); g.roundRect(bx - R * 1.1, by - R * 1.1, R * 2.2, R * 2.2, 4); g.fill(); g.stroke();
    }
    g.font = mono;
    g.fillStyle = '#5f7288'; g.fillText(narrow ? 'decoy · steady' : 'decoy · steady · never blinks', dx - R * 1.35, dy + R * 1.35 + 15);

    const trk = S.state === 'TRACK' || S.state === 'LOCK';
    if (S.state !== 'SEARCH') {
      const h = R * 1.5;
      if (S.state === 'PREDICT') { g.setLineDash([4, 4]); corners(bx, by, h, '#FFC85A', 1.4); g.setLineDash([]); g.fillStyle = '#FFC85A'; g.fillText('beacon dark · predicting', bx - h, by - h - 8); }
      else {
        corners(bx, by, h, trk ? '#3BD68C' : '#FFC24D', 1.6);
        g.fillStyle = trk ? '#3BD68C' : '#FFC24D';
        g.fillText(trk ? 'beacon · 4 Hz · locked' : `candidate · blink score ${(S.score * 100) | 0}%`, bx - h, by - h - 8);
      }
      const d = R * 1.35;
      g.strokeStyle = '#FF5555'; g.lineWidth = 1.2; g.setLineDash([3, 3]); g.strokeRect(dx - d, dy - d, d * 2, d * 2); g.setLineDash([]);
      g.fillStyle = '#FF5555'; g.fillText(narrow ? 'rejected' : 'rejected · no blink', dx - d, dy - d - 7);
    }
    if (trk || S.state === 'PREDICT') {
      if (Math.sin(2 * Math.PI * 7 * S.t) > 0) blob(cx, cy, 8, '255,120,120', 0.95);   // our laser return
      g.strokeStyle = 'rgba(79,199,234,.55)'; g.lineWidth = 1; g.beginPath(); g.moveTo(cx, cy); g.lineTo(bx, by); g.stroke();
    }
    g.restore();
    g.strokeStyle = '#243a55'; g.lineWidth = 1; g.strokeRect(fx + .5, fy + .5, fw - 1, fh - 1);
    g.font = mono; g.fillStyle = '#5f7288'; g.textAlign = 'right';
    g.fillText(W > 560 ? `field of view ${FOVW.toFixed(1)}° × ${FOVH.toFixed(1)}°  ·  aim az ${S.boreAz.toFixed(2)}°  el ${S.boreEl.toFixed(2)}°` : `az ${S.boreAz.toFixed(2)}°  el ${S.boreEl.toFixed(2)}°`, W - 20, 31);
    g.textAlign = 'left';
  }

  const plot = $('wdPlot'), pg = plot.getContext('2d');
  function ui() {
    const st = $('wdState');
    st.textContent = S.state; st.dataset.tone = TONE[S.state];
    $('wdDesc').textContent = DESC[S.state];
    $('wdT').textContent = S.t.toFixed(1) + ' s';
    $('wdErr').textContent = Number.isFinite(S.err) ? S.err.toFixed(1) + ' px' : 'not in view';
    $('wdScore').textContent = S.score.toFixed(2);
    $('wdAcq').textContent = S.acqAt !== null ? S.acqAt.toFixed(2) + ' s' : '—';
    const pill = $('wdPill'); pill.dataset.s = S.state; pill.lastChild.textContent = S.state === 'PREDICT' ? 'PREDICTING' : S.state;

    const r = plot.getBoundingClientRect(), pw = Math.max(1, r.width), ph = Math.max(1, r.height);
    if (plot.width !== Math.round(pw * dpr)) { plot.width = Math.round(pw * dpr); plot.height = Math.round(ph * dpr); }
    pg.setTransform(dpr, 0, 0, dpr, 0, 0); pg.clearRect(0, 0, pw, ph);
    const vals = S.hist.filter(h => Number.isFinite(h.e)).map(h => h.e), max = Math.max(40, ...vals);
    const yL = ph - 12 / max * ph;
    pg.strokeStyle = 'rgba(255,255,255,.1)'; pg.setLineDash([3, 3]); pg.beginPath(); pg.moveTo(0, yL); pg.lineTo(pw, yL); pg.stroke(); pg.setLineDash([]);
    pg.fillStyle = '#86868b'; pg.font = '10px ui-monospace,monospace'; pg.textAlign = 'right'; pg.fillText('lock · 12 px', pw - 2, Math.max(10, yL - 4)); pg.textAlign = 'left';
    if (S.hist.length > 1) {
      pg.strokeStyle = '#3BD68C'; pg.lineWidth = 1.6; pg.beginPath(); let go = false;
      S.hist.forEach(h => { if (!Number.isFinite(h.e)) { go = false; return; }
        const x = (h.t - S.hist[0].t) / 12 * pw, y = ph - Math.min(1, h.e / max) * (ph - 4);
        go ? pg.lineTo(x, y) : (pg.moveTo(x, y), go = true); });
      pg.stroke();
    }
  }

  function setCover(c) {
    S.covered = c;
    const b = $('wdCover'); if (b) { b.classList.toggle('on', c); b.lastChild.textContent = c ? 'Uncover the beacon' : 'Cover the beacon'; }
  }
  $('wdCover').addEventListener('click', () => setCover(!S.covered));
  $('wdReset').addEventListener('click', reset);

  let vis = false, last = 0, acc = 0;
  if ('IntersectionObserver' in window) new IntersectionObserver(es => { vis = es.some(e => e.isIntersecting); }, { threshold: 0.05 }).observe(cv);
  else vis = true;
  reset();
  if (still) { for (let i = 0; i < 360; i++) step(STEP); }
  function frame(now) {
    requestAnimationFrame(frame);
    if (!vis || document.hidden) { last = now; return; }
    if (!still) {
      acc += Math.min(0.1, (now - (last || now)) / 1000);
      while (acc >= STEP) { step(STEP); acc -= STEP; }
      if (S.t > RESTART && !S.covered) reset();
    }
    last = now;
    draw(); ui();
  }
  requestAnimationFrame(frame);
})();
