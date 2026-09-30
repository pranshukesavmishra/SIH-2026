/* "Watch it decide": the real ZeroDrift tracker (tracker-core.js, the same code as the
   Live demo) running in the browser on a small synthetic sky. One light blinks at 4 Hz;
   the others are decoys: a steady lamp, a lit window, a 7 Hz blinker, a 2 Hz blinker
   and random glints. Everything drawn on top comes from the tracker's own state. */
(function () {
  const root = document.getElementById('decide');
  const view = document.getElementById('dzCanvas');
  if (!root || !view || !window.ZeroDriftTracker) return;

  const PW = 480, PH = 300;                               // what the engine "sees"
  const cam = document.createElement('canvas'); cam.width = PW; cam.height = PH;
  const cx = cam.getContext('2d', { willReadFrequently: true });
  const vx = view.getContext('2d');
  const $ = id => document.getElementById(id);
  const FOV_H = 60, FOV_V = FOV_H * PH / PW;

  let tracker, lights, simT = 0, covered = 0, glint = null, wrongLocks = 0, lockedFrames = 0, frames = 0;
  let extra = 0, onDecoy = 0;
  const DECOYS = [
    { kind: 'lamp', x: 54, y: 240, r: 9, col: [255, 196, 120], hz: 0 },
    { kind: 'window', x: 424, y: 46, w: 38, h: 26, col: [190, 215, 255], hz: 0 },
    { kind: 'blink', x: 424, y: 252, r: 4.5, col: [255, 90, 80], hz: 7 },
    { kind: 'blink', x: 92, y: 44, r: 4, col: [255, 225, 170], hz: 2 },
  ];
  const EXTRA = [
    { kind: 'lamp', x: 250, y: 276, r: 7, col: [255, 236, 200], hz: 0 },
    { kind: 'blink', x: 290, y: 28, r: 4, col: [160, 220, 255], hz: 5.5 },
    { kind: 'blink', x: 26, y: 150, r: 4, col: [255, 170, 90], hz: 3 },
    { kind: 'lamp', x: 454, y: 150, r: 6, col: [220, 240, 255], hz: 0 },
  ];

  const reset = () => {
    tracker = new window.ZeroDriftTracker({ targetHz: 4 });
    lights = DECOYS.map(d => Object.assign({ ph: Math.random() }, d));
    simT = 0; covered = 0; glint = null; wrongLocks = 0; lockedFrames = 0; frames = 0; extra = 0; onDecoy = 0;
    $('dzWrong').textContent = '0';
  };

  const beaconAt = t => ({
    x: PW / 2 + Math.sin(t * 0.55) * 124 + Math.sin(t * 1.3) * 14,    // the path keeps clear of the decoys
    y: PH / 2 + Math.sin(t * 0.83 + 1) * 62,
  });
  const lit = (hz, t, ph) => hz ? ((t * hz + ph) % 1) < 0.5 : true;

  /* ---- draw what the camera sees (engine input) ---- */
  const drawCam = t => {
    cx.fillStyle = '#000'; cx.fillRect(0, 0, PW, PH);
    // dim stars: below the engine's brightness floor
    cx.fillStyle = 'rgb(70,70,80)';
    for (let i = 0; i < 40; i++) cx.fillRect((i * 97) % PW, (i * 53 + 17) % PH, 1, 1);
    lights.forEach(L => {
      if (!lit(L.hz, t, L.ph)) return;
      if (L.kind === 'window') { cx.fillStyle = `rgb(${L.col})`; cx.fillRect(L.x - L.w / 2, L.y - L.h / 2, L.w, L.h); return; }
      blob(cx, L.x, L.y, L.r, L.col, 1);
    });
    const b = beaconAt(t);
    if (lit(4, t, 0) && t > covered) blob(cx, b.x, b.y, 4.2, [235, 255, 245], 1);
    if (glint && t < glint.until) blob(cx, glint.x, glint.y, 3.5, [255, 255, 255], 1);
    return b;
  };
  function blob(c, x, y, r, col, a) {
    const g = c.createRadialGradient(x, y, 0, x, y, r * 2.4);
    g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(0.35, `rgba(${col},${a})`); g.addColorStop(1, `rgba(${col},0)`);
    c.fillStyle = g; c.beginPath(); c.arc(x, y, r * 2.4, 0, 6.2832); c.fill();
  }

  /* ---- draw the view: the same scene, large, plus the engine's own readings ---- */
  let VW = 0, VH = 0, S = 1, dpr = 1;
  const size = () => {
    const r = view.getBoundingClientRect();
    dpr = Math.min(2, window.devicePixelRatio || 1);
    VW = r.width; VH = r.height; S = Math.min(VW / PW, VH / PH);
    view.width = Math.round(VW * dpr); view.height = Math.round(VH * dpr);
  };
  new ResizeObserver(size).observe(view); size();
  const ox = () => (VW - PW * S) / 2, oy = () => (VH - PH * S) / 2;
  const P = (x, y) => [ox() + x * S, oy() + y * S];

  let lockAt = 0, hadLock = false, lastOn = false;
  const pulses = [];
  const drawView = (t, frac, now) => {
    const b = beaconAt(t);
    vx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const bg = vx.createRadialGradient(VW * 0.5, VH * 0.35, 0, VW * 0.5, VH * 0.5, VW * 0.8);
    bg.addColorStop(0, '#0b1422'); bg.addColorStop(1, '#030507');
    vx.fillStyle = bg; vx.fillRect(0, 0, VW, VH);
    // faint grid + boresight
    vx.strokeStyle = 'rgba(79,199,234,.06)'; vx.lineWidth = 1;
    for (let i = 1; i < 8; i++) { const [x] = P(PW * i / 8, 0); vx.beginPath(); vx.moveTo(x, 0); vx.lineTo(x, VH); vx.stroke(); }
    for (let i = 1; i < 5; i++) { const [, y] = P(0, PH * i / 5); vx.beginPath(); vx.moveTo(0, y); vx.lineTo(VW, y); vx.stroke(); }
    const [bx0, by0] = P(PW / 2, PH / 2);
    vx.strokeStyle = 'rgba(245,245,247,.35)'; vx.lineWidth = 1.2;
    vx.beginPath(); vx.moveTo(bx0 - 14, by0); vx.lineTo(bx0 - 5, by0); vx.moveTo(bx0 + 5, by0); vx.lineTo(bx0 + 14, by0);
    vx.moveTo(bx0, by0 - 14); vx.lineTo(bx0, by0 - 5); vx.moveTo(bx0, by0 + 5); vx.lineTo(bx0, by0 + 14); vx.stroke();
    // stars
    for (let i = 0; i < 40; i++) { const [x, y] = P((i * 97) % PW, (i * 53 + 17) % PH); vx.fillStyle = `rgba(200,210,230,${0.3 + 0.25 * Math.sin(t * 1.3 + i)})`; vx.fillRect(x, y, 1.3, 1.3); }
    // lights
    lights.forEach(L => {
      const on = lit(L.hz, t, L.ph);
      const [x, y] = P(L.x, L.y);
      if (L.kind === 'window') {
        vx.fillStyle = on ? 'rgba(170,200,255,.9)' : 'rgba(170,200,255,.12)';
        vx.shadowColor = 'rgba(150,190,255,.8)'; vx.shadowBlur = on ? 26 : 0;
        vx.fillRect(x - L.w * S / 2, y - L.h * S / 2, L.w * S, L.h * S); vx.shadowBlur = 0; return;
      }
      glow(x, y, L.r * S * 0.9, L.col, on ? 1 : 0.08);
    });
    const [px, py] = P(b.x, b.y);
    const bOn = lit(4, t, 0) && t > covered;
    if (bOn && !lastOn) pulses.push({ x: b.x, y: b.y, t0: now });
    lastOn = bOn;
    for (let i = pulses.length - 1; i >= 0; i--) {
      const q = pulses[i], a = (now - q.t0) / 650;
      if (a >= 1) { pulses.splice(i, 1); continue; }
      const [qx, qy] = P(q.x, q.y);
      vx.strokeStyle = `rgba(93,224,138,${0.55 * (1 - a)})`; vx.lineWidth = 1.5;
      vx.beginPath(); vx.arc(qx, qy, S * (5 + 18 * a), 0, 6.2832); vx.stroke();
    }
    glow(px, py, 4.2 * S * 0.9, [120, 255, 170], bOn ? 1 : 0.05);
    if (glint && t < glint.until) { const [gx, gy] = P(glint.x, glint.y); glow(gx, gy, 3.5 * S, [255, 255, 255], 1); }

    // engine readings: every track it follows, with its measured blink rate
    const L = tracker.lock;
    vx.font = `600 ${Math.max(11, Math.round(S * 5))}px 'ZD Inter', system-ui, sans-serif`;
    vx.textBaseline = 'middle';
    const boxes = [];
    const pill = (txt, x, y, col, prefer) => {
      const w = vx.measureText(txt).width + 16, h = 22;
      let bx = prefer === 'left' ? x - w : x, by = y - h / 2;
      const hit = () => boxes.some(q => bx < q[0] + q[2] && bx + w > q[0] && by < q[1] + q[3] && by + h > q[1]);
      if (hit()) { bx = prefer === 'left' ? x : x - w; if (hit()) by += 24; }
      boxes.push([bx, by, w, h]);
      vx.fillStyle = 'rgba(10,12,16,.72)'; vx.beginPath(); vx.roundRect ? vx.roundRect(bx, by, w, h, 11) : vx.rect(bx, by, w, h); vx.fill();
      vx.fillStyle = col; vx.fillText(txt, bx + 8, by + h / 2 + 0.5);
    };
    tracker.tracks.forEach(tr => {
      if (L && Math.hypot(tr.x - L.x, tr.y - L.y) < 10) return;
      const [x, y] = P(tr.x, tr.y);
      const rr = Math.max(14, S * 11);
      let label, col;
      if (tr.freq && tr.depth >= 0.3) { label = tr.freq.toFixed(1) + ' Hz'; col = tr.passing ? '#5DE08A' : '#ff7a6e'; if (!tr.passing) label += '  ✕'; }
      else { label = 'steady  ✕'; col = 'rgba(235,235,240,.7)'; }
      vx.strokeStyle = col; vx.globalAlpha = 0.8; vx.lineWidth = 1.3; vx.setLineDash([2, 3]);
      vx.beginPath(); vx.arc(x, y, rr, 0, 6.2832); vx.stroke(); vx.setLineDash([]);
      vx.globalAlpha = 1;
      pill(label, x > VW * 0.7 ? x - rr - 6 : x + rr + 6, y, col, x > VW * 0.7 ? 'left' : 'right');
    });
    if (L && !hadLock) lockAt = now;
    hadLock = !!L;
    if (L) {
      const coast = tracker.state === 'COASTING';
      // the engine ran at the start of this display frame; carry its lock on by the
      // measured velocity for the fraction of a frame since, so it sits on the beacon
      const lx = L.x + (L.vx || 0) * frac, ly = L.y + (L.vy || 0) * frac;
      const [x, y] = P(lx, ly);
      const col = coast ? '#FFC85A' : '#5DE08A', rgb = coast ? '255,200,90' : '93,224,138';
      const ease = v => 1 - Math.pow(1 - Math.min(1, Math.max(0, v)), 3);
      const snap = ease((now - lockAt) / 450);                     // closes in on lock-on
      const r = Math.max(22, S * 13) * (1 + 1.6 * (1 - snap));
      // faint line from the boresight: this is the aim the gimbal is told to fix
      vx.strokeStyle = `rgba(${rgb},.28)`; vx.lineWidth = 1; vx.setLineDash([2, 5]);
      vx.beginPath(); vx.moveTo(bx0, by0); vx.lineTo(x, y); vx.stroke(); vx.setLineDash([]);
      vx.save();
      vx.shadowColor = `rgba(${rgb},.7)`; vx.shadowBlur = 8;
      vx.strokeStyle = col; vx.globalAlpha = 0.35 + 0.65 * snap;
      vx.lineWidth = 1.6; vx.setLineDash(coast ? [6, 4] : []);
      vx.beginPath(); vx.arc(x, y, r, 0, 6.2832); vx.stroke(); vx.setLineDash([]);
      vx.lineWidth = 1; vx.beginPath(); vx.arc(x, y, r * 0.2, 0, 6.2832); vx.stroke();
      // crosshair with a gap in the middle, running just past the ring
      vx.lineWidth = 1.5; vx.beginPath();
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => { vx.moveTo(x + dx * r * 0.3, y + dy * r * 0.3); vx.lineTo(x + dx * r * 1.4, y + dy * r * 1.4); });
      vx.stroke();
      // range ticks (mil-dots)
      vx.lineWidth = 1.2; vx.beginPath();
      [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
        [0.5, 0.68, 0.86].forEach((f, i) => { const tx = x + dx * r * f, ty = y + dy * r * f, h = i === 1 ? 4 : 2.5;
          vx.moveTo(tx - dy * h, ty - dx * h); vx.lineTo(tx + dy * h, ty + dx * h); });
      });
      vx.stroke();
      // four arcs turning slowly around the ring
      vx.lineWidth = 2.4; const rot = now * 0.0007;
      for (let i = 0; i < 4; i++) { const a0 = rot + i * Math.PI / 2 + 0.35; vx.beginPath(); vx.arc(x, y, r * 1.22, a0, a0 + 0.55); vx.stroke(); }
      vx.fillStyle = col; vx.beginPath(); vx.arc(x, y, 1.8, 0, 6.2832); vx.fill();
      vx.restore();
      // readout: state, rate, and the aim error against the true beacon position
      const errDeg = Math.hypot(lx - b.x, ly - b.y) / PW * FOV_H;
      const side = x > VW * 0.7 ? 'left' : 'right', lx0 = side === 'left' ? x - r * 1.45 - 6 : x + r * 1.45 + 6;
      pill((coast ? 'COAST' : 'LOCKED') + ' · 4.0 Hz', lx0, y - 12, col, side);
      pill(coast ? 'beacon dark · predicting' : 'aim error ' + errDeg.toFixed(2) + '°', lx0, y + 14, 'rgba(235,240,245,.85)', side);
    }
  };
  function glow(x, y, r, col, a) {
    const g = vx.createRadialGradient(x, y, 0, x, y, r * 4.2);
    g.addColorStop(0, `rgba(255,255,255,${a})`); g.addColorStop(0.18, `rgba(${col},${a})`); g.addColorStop(1, `rgba(${col},0)`);
    vx.fillStyle = g; vx.beginPath(); vx.arc(x, y, r * 4.2, 0, 6.2832); vx.fill();
  }

  /* ---- side panel: the four decisions, lit by the engine's state ---- */
  const steps = [...root.querySelectorAll('.dz-steps li[data-k]')];
  const setStep = (i, on, val, sub, tone) => {
    const li = steps[i]; li.classList.toggle('on', on); li.dataset.tone = tone || '';
    li.querySelector('strong').textContent = val; li.querySelector('span').textContent = sub;
    li.querySelector('em').textContent = on ? 'Active' : 'Waiting';
  };
  const sign = v => (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(1) + '°';
  const updatePanel = b => {
    const st = tracker.state, L = tracker.lock;
    const n = tracker.tracks.length;
    const rejected = tracker.tracks.filter(tr => !(L && Math.hypot(tr.x - L.x, tr.y - L.y) < 10)).length;
    setStep(0, true, n + (n === 1 ? ' light' : ' lights'), 'found in view');
    if (L) setStep(1, true, '4.0 Hz', 'beacon ✓ · ' + rejected + ' rejected', 'ok');
    else setStep(1, st === 'CONFIRMING', st === 'CONFIRMING' ? 'Checking' : 'Measuring', st === 'CONFIRMING' ? 'a 4 Hz candidate' : 'each light’s blink rate');
    if (L) setStep(2, true, st === 'COASTING' ? 'Coasting' : 'Locked', st === 'COASTING' ? 'through the blink gap' : 'holds through every blink', st === 'COASTING' ? 'warn' : 'ok');
    else setStep(2, false, st === 'REACQUIRING' ? 'Re-acquiring' : 'Searching', st === 'REACQUIRING' ? 'lost for a moment' : 'waiting for the beacon', st === 'REACQUIRING' ? 'warn' : '');
    if (L) {
      const az = (L.x - PW / 2) / PW * FOV_H, el = -(L.y - PH / 2) / PH * FOV_V;
      setStep(3, true, sign(az) + '  ' + sign(el), 'Δ azimuth · Δ elevation');
    } else setStep(3, false, '—', 'aim is sent to the gimbal');
    const chip = $('dzState');
    chip.dataset.s = st; chip.lastChild.textContent = st === 'CONFIRMING' ? 'IDENTIFYING' : st;
    // a wrong lock = the engine sitting on a decoy (not the beacon) for half a second
    if (L) {
      lockedFrames++;
      const offBeacon = Math.hypot(L.x - b.x, L.y - b.y) > 30;
      const onALight = lights.some(D => Math.hypot(L.x - D.x, L.y - D.y) < 16);
      onDecoy = offBeacon && onALight ? onDecoy + 1 : 0;
      if (onDecoy === 15) wrongLocks++;
    } else onDecoy = 0;
    $('dzWrong').textContent = String(wrongLocks);
    $('dzFrames').textContent = frames.toLocaleString('en-IN');
  };
  const t = () => simT;   // engine clock: a steady 30 frames per second, whatever the screen does

  /* ---- loop (about 30 fps, only while on screen) ---- */
  let on = false, lastStep = 0, raf = 0;
  const loop = now => {
    raf = 0; if (!on) return;
    raf = requestAnimationFrame(loop);
    if (now - lastStep >= 30) {                    // the engine: a steady 30 frames per second
      lastStep = now;
      simT += 1 / 30;
      const tt = simT;
      if (!glint || tt > glint.until + 1.8 + Math.random() * 3) glint = { x: 30 + Math.random() * (PW - 60), y: 30 + Math.random() * (PH - 60), until: tt + 0.05 };
      const b = drawCam(tt);
      const img = cx.getImageData(0, 0, PW, PH);
      tracker.process(img.data, PW, PH, tt);
      frames++;
      updatePanel(b);
    }
    // the picture: every display frame, moved on by the time since the engine ran
    const frac = Math.min(1, (now - lastStep) / (1000 / 30));
    drawView(simT + frac / 30, frac, now);
  };
  const start = () => { if (!on) { on = true; if (!raf) raf = requestAnimationFrame(loop); } };
  const stop = () => { on = false; };
  if ('IntersectionObserver' in window) new IntersectionObserver(es => es[0].isIntersecting ? start() : stop(), { threshold: 0.15 }).observe(root);
  else start();
  document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());

  $('dzHide').addEventListener('click', () => { covered = t() + 1.3; });
  $('dzDecoy').addEventListener('click', () => {
    if (extra >= EXTRA.length) return;
    lights.push(Object.assign({ ph: Math.random() }, EXTRA[extra++]));
    if (extra >= EXTRA.length) $('dzDecoy').disabled = true;
  });
  $('dzReset').addEventListener('click', () => { reset(); $('dzDecoy').disabled = false; });
  reset();
})();
