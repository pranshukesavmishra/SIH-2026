// Headless benchmark for docs/tracker-core.js -- the live demo's tracker.
//
// Renders synthetic webcam frames of a room with the things that actually
// fool a beacon tracker (a ceiling lamp, a window, a monitor changing
// content, a lamp flickering just outside the band, a person moving, the
// camera's auto-exposure reacting to the beacon, uneven frame timing) and a
// blinking torch moving in ways a hand really moves it. Ground truth is
// exact, so every number below is measured, not eyeballed.
//
//   node tools/sim/live_tracker_bench.mjs            # all scenarios
//   node tools/sim/live_tracker_bench.mjs fast_lissajous
//
// Exit code is non-zero if any scenario misses its pass bar.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const Tracker = require(process.env.CORE || '../../docs/tracker-core.js');

const W = 640, H = 480;

function rng(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}
function gauss(r) { return Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r()); }

// ---- the static room ------------------------------------------------------
function buildRoom(r, lit, real) {
  const base = new Float32Array(W * H);
  // A lit room: walls at ~190 on the camera, a window near white, a pale
  // table -- the conditions where the torch barely stands above the scene.
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    base[y * W + x] = lit === 2 ? 212 + 18 * (y / H) + 8 * Math.sin(x / 90) : lit ? 178 + 26 * (y / H) + 10 * Math.sin(x / 90) : 70 + 40 * (y / H) + 15 * Math.sin(x / 90);
  }
  const rect = (x0, y0, w, h, v) => {
    for (let y = y0; y < y0 + h; y++) for (let x = x0; x < x0 + w; x++)
      if (x >= 0 && y >= 0 && x < W && y < H) base[y * W + x] = v;
  };
  rect(20, 300, 180, 160, lit ? 120 : 45);      // sofa
  rect(470, 330, 150, 120, lit ? 228 : 150);    // table top, pale
  rect(250, 380, 120, 90, lit ? 205 : 120);
  rect(40, 30, 150, 110, lit ? 252 : 236);      // window: large, bright, steady
  if (real) {
    // A real room is busy: shelves of bottles, posters, a cupboard -- small
    // bright and dark patches everywhere, which a moving person uncovers.
    for (let i = 0; i < 60; i++) {
      const w = 5 + 30 * r(), h = 5 + 45 * r();
      rect(Math.round(200 + 430 * r()), Math.round(20 + 300 * r()), Math.round(w), Math.round(h),
           lit ? 90 + 165 * r() : 25 + 190 * r());
    }
  }
  return base;
}

function disc(img, cx, cy, r, v, soft) {
  const R = Math.ceil(r + 3 * (soft || 0));
  for (let y = Math.max(0, Math.floor(cy - R)); y <= Math.min(H - 1, Math.ceil(cy + R)); y++)
    for (let x = Math.max(0, Math.floor(cx - R)); x <= Math.min(W - 1, Math.ceil(cx + R)); x++) {
      const d = Math.hypot(x - cx, y - cy);
      let a = d <= r ? 1 : (soft ? Math.exp(-((d - r) ** 2) / (2 * soft * soft)) : 0);
      if (a > 0.003) img[y * W + x] += v * a;
    }
}
function box(img, cx, cy, w, h, v) {
  for (let y = Math.max(0, Math.round(cy - h / 2)); y < Math.min(H, Math.round(cy + h / 2)); y++)
    for (let x = Math.max(0, Math.round(cx - w / 2)); x < Math.min(W, Math.round(cx + w / 2)); x++)
      img[y * W + x] += v;
}

// ---- trajectories ---------------------------------------------------------
const traj = {
  static: () => [410, 250],
  circle: t => [320 + 130 * Math.cos(2 * Math.PI * t / 5), 240 + 110 * Math.sin(2 * Math.PI * t / 5)],
  medium: t => [320 + 200 * Math.sin(2 * Math.PI * 0.45 * t), 240 + 140 * Math.sin(2 * Math.PI * 0.7 * t + 1)],
  fast: t => [320 + 220 * Math.sin(2 * Math.PI * 0.7 * t), 240 + 150 * Math.sin(2 * Math.PI * 1.05 * t + 1)],
  // across the ceiling lamp at (520, 90) and back
  overLamp: t => { const u = 0.5 - 0.5 * Math.cos(2 * Math.PI * t / 4); return [300 + 300 * u, 250 - 180 * u]; },
};
// Jerky hand: a new random direction every 0.25-0.6 s at 6-24 px/frame,
// bouncing off the frame edges. A real hand cannot reverse instantly -- it
// decelerates -- so velocity eases toward each new heading with a 90 ms
// time constant (an instant 40 px/frame reversal is not a hand, it is a
// teleport). Integrated at 1 kHz so any time can be queried.
function jerky(seed) {
  const r = rng(seed); const dt = 0.001, pts = [];
  let t = 0, x = 320, y = 240, vx = 0, vy = 0, tx = 0, ty = 0, next = 0;
  while (t < 30) {
    if (t >= next) {
      const sp = (6 + 18 * r()) * 30, a = 2 * Math.PI * r();
      tx = sp * Math.cos(a); ty = sp * Math.sin(a); next = t + 0.25 + 0.35 * r();
    }
    vx += (tx - vx) * dt / 0.09; vy += (ty - vy) * dt / 0.09;
    x += vx * dt; y += vy * dt;
    if (x < 50 || x > W - 50) { vx = -vx; tx = -tx; x = Math.max(50, Math.min(W - 50, x)); }
    if (y < 50 || y > H - 50) { vy = -vy; ty = -ty; y = Math.max(50, Math.min(H - 50, y)); }
    pts.push([x, y]); t += dt;
  }
  return tt => pts[Math.max(0, Math.min(pts.length - 1, Math.round(tt / dt)))];
}

// ---- scenarios ------------------------------------------------------------
const SCEN = [
  { name: 'static',          path: traj.static,   dur: 6 },
  { name: 'slow_circle',     path: traj.circle,   dur: 10 },
  { name: 'medium_lissajous',path: traj.medium,   dur: 12 },
  { name: 'fast_lissajous',  path: traj.fast,     dur: 12 },
  { name: 'jerky_hand',      path: jerky(7),      dur: 14 },
  { name: 'jerky_hand_2',    path: jerky(99),     dur: 14 },
  { name: 'across_the_lamp', path: traj.overLamp, dur: 12 },
  { name: 'phone_screen_dim',path: traj.circle,   dur: 10, screen: true },
  { name: 'off_nominal_4.6Hz', path: traj.medium, dur: 10, hz: 4.6 },
  { name: 'turning_torch',   path: traj.medium,   dur: 12, turning: true },
  // Stretch case, reported but not gating: at 20 fps the same hand speed
  // is 1.5x the pixels per frame and the beacon is dark for 2.5 frames.
  { name: 'camera_20fps',    path: traj.medium,   dur: 12, fps: 20, stretch: true },
  { name: 'jerky_hand_3',    path: jerky(2024),   dur: 14 },
  { name: 'wrong_rate_blinkers', path: traj.medium, dur: 12, blinkers: true },
  { name: 'lit_static',      path: traj.static,   dur: 6,  lit: true },
  { name: 'lit_figure8',     path: traj.medium,   dur: 12, lit: true },
  { name: 'lit_hand',        path: jerky(31),     dur: 14, lit: true },
  { name: 'lit_phone_screen',path: traj.circle,   dur: 10, lit: true, screen: true },
  { name: 'no_beacon',       path: null,          dur: 12 },
  { name: 'bright_figure8',  path: traj.medium,   dur: 12, lit: 2 },
  { name: 'bright_hand',     path: jerky(47),     dur: 14, lit: 2 },
  { name: 'bright_screen',   path: traj.circle,   dur: 10, lit: 2, screen: true },
  { name: 'lit_no_beacon',   path: null,          dur: 12, lit: true, blinkers: true },
  { name: 'bright_no_beacon',path: null,          dur: 12, lit: 2, blinkers: true },
  { name: 'blinkers_only',   path: null,          dur: 12, blinkers: true },
  // Real-room scenes: busy shelves, a moving operator, webcam noise. The
  // no-beacon ones gate (a lock on a face or a shelf is the failure seen on
  // a real webcam); following the beacon through that much clutter at
  // jerky-hand speed is reported, not gated.
  { name: 'real_dark_hand',  path: jerky(61),     dur: 14, real: true, stretch: true },
  { name: 'real_lit_hand',   path: jerky(62),     dur: 14, real: true, lit: true, stretch: true },
  { name: 'real_bright_hand',path: jerky(63),     dur: 14, real: true, lit: 2, stretch: true },
  { name: 'real_dark_none',  path: null,          dur: 40, real: true },
  { name: 'real_lit_none',   path: null,          dur: 40, real: true, lit: true },
  { name: 'real_bright_none',path: null,          dur: 40, real: true, lit: 2 },
];

function run(sc, verbose) {
  const r = rng(12345 + sc.name.length * 77 + 1000 * (+process.env.SEED || 0));
  const room = buildRoom(r, sc.lit, sc.real);
  const head = sc.real ? jerky(900 + (+process.env.SEED || 0)) : null;
  const wave = sc.real && !sc.path ? jerky(500 + (+process.env.SEED || 0)) : null;
  const img = new Float32Array(W * H);
  const rgba = new Uint8ClampedArray(W * H * 4);
  const tk = new Tracker({ targetHz: 4 });
  const fps = sc.fps || 30, hz = sc.hz || 4, phase0 = r();
  let t = 0, agc = 1;
  const out = { litErrs: [], missHist: {}, acq: null, inAfter: 0, n: 0, inFrame: 0, good: 0, wrong: 0, errs: [], lockedFrames: 0, maxGap: 0 };
  let gap = 0;
  while (t < sc.dur) {
    // timing jitter and the odd dropped frame, like a real browser camera
    t += 1 / fps + (r() - 0.5) * 0.012 + (r() < 0.02 ? 1 / fps : 0);
    img.set(room);
    // ceiling lamp: steady, saturated, with bloom
    disc(img, 520, 90, 11, 255, 6);
    // monitor: content changes every half second
    const mon = 150 + 70 * Math.floor(((t * 2) | 0) * 9301 % 7) / 7;
    box(img, 470, 250, 110, 70, mon - 100);
    // lamp flickering at 5.35 Hz (just outside a 3-5 Hz band), 30% depth
    disc(img, 250, 120, 8, 200 * (0.85 + 0.15 * Math.sin(2 * Math.PI * 5.35 * t)), 4);
    // Other blinking lights at the WRONG rate: a slow 1.5 Hz indicator and
    // a fast 7.5 Hz strobe. Blinking alone must not be enough.
    if (sc.blinkers) {
      if (((t * 1.5) % 1) < 0.5) disc(img, 360, 420, 5, 300, 4);
      if (((t * 7.5) % 1) < 0.5) disc(img, 600, 200, 5, 300, 4);
    }
    // a person drifting across: large, mid-bright, moving
    if (!sc.real) disc(img, 120 + 60 * Math.sin(t * 0.6), 250, 38, 75, 8);
    else {
      // The operator: head and shoulders that sway and jerk, a face with a
      // specular shine, dark shirt, blue headphones -- sitting in front of
      // the busy shelves, covering and uncovering them.
      const [hx0, hy0] = head(t);
      const px = 250 + 0.25 * (hx0 - 320), py = 290 + 0.15 * (hy0 - 240);
      for (let y = Math.round(py + 60); y < H; y++) for (let x = Math.round(px - 150); x < Math.round(px + 150); x++)
        if (x >= 0 && x < W) img[y * W + x] = 38;
      const skin = sc.lit === 2 ? 185 : sc.lit ? 160 : 95;
      for (let y = Math.round(py - 60); y < Math.round(py + 60); y++) for (let x = Math.round(px - 45); x < Math.round(px + 45); x++) {
        if (x < 0 || x >= W || y < 0 || y >= H) continue;
        const e = ((x - px) / 45) ** 2 + ((y - py) / 60) ** 2;
        if (e < 1) img[y * W + x] = y < py - 30 ? 30 : skin;           // hair on top
      }
      disc(img, px - 50, py, 14, 0, 0); box(img, px - 50, py, 22, 40, 60); box(img, px + 50, py, 22, 40, 60);
      disc(img, px + 8 + 6 * Math.sin(t * 1.3), py - 18, 3, 70, 2);    // shine on the forehead
      disc(img, px + 3, py + 8, 2, 50, 1.5);                              // and the nose
    }
    // A phone waved around with its light OFF: a dark body sweeping across
    // bright things, which "appear" as it passes.
    if (wave) {
      const [wx, wy] = wave(t);
      for (let y = Math.max(0, Math.round(wy - 30)); y < Math.min(H, Math.round(wy + 30)); y++)
        for (let x = Math.max(0, Math.round(wx - 15)); x < Math.min(W, Math.round(wx + 15)); x++) img[y * W + x] = 30;
      box(img, wx, wy + 45, 26, 40, sc.lit ? 140 : 80);                  // the hand
    }

    let truth = null;
    if (sc.path) {
      // The phone itself: a dark body that hides whatever is behind it,
      // lit or not -- so the dark phase is the phone, not the room.
      const [hx, hy] = sc.path(t - 0.005);
      for (let y = Math.max(0, Math.round(hy - 26)); y < Math.min(H, Math.round(hy + 44)); y++)
        for (let x = Math.max(0, Math.round(hx - 17)); x < Math.min(W, Math.round(hx + 17)); x++)
          img[y * W + x] = 32;
      // exposure-averaged blink, motion blur over the exposure
      const exp = 0.010, sub = 4;
      for (let s = 0; s < sub; s++) {
        const ts = t - exp + (s + 0.5) * exp / sub;
        const on = ((ts * hz + phase0) % 1) < 0.5 ? 1 : 0;
        if (!on) continue;
        const [bx, by] = sc.path(ts);
        let amp = 1;
        if (sc.turning) amp = 0.35 + 0.65 * (0.5 + 0.5 * Math.cos(2 * Math.PI * 0.4 * ts));
        // A phone screen at full white reads ~220 on a webcam across a room.
        if (sc.screen) box(img, bx, by, 18, 30, 190 * amp / sub);
        else if (sc.real) { disc(img, bx, by, 7, 450 * amp / sub, 0); disc(img, bx, by, 8, 160 * amp / sub, 12); }
        else { disc(img, bx, by, 6, 400 * amp / sub, 0); disc(img, bx, by, 6, 110 * amp / sub, 9); }
      }
      truth = sc.path(t - exp / 2);
      const lit = ((t * hz + phase0) % 1) < 0.5;
      agc += ((lit ? 0.9 : 1.0) - agc) * 0.35;      // auto-exposure chasing the blink
    }
    let flick = 1 + 0.02 * Math.sin(2 * Math.PI * 10 * t);   // mains alias
    if (!sc.real) {
      for (let i = 0, q = 0; i < W * H; i++, q += 4) {
        const v = Math.min(255, Math.max(0, img[i] * agc * flick + 4 * gauss(r)));
        rgba[q] = rgba[q + 1] = rgba[q + 2] = v; rgba[q + 3] = 255;
      }
    } else {
      // A laptop webcam: more sensor noise, exposure that jitters frame to
      // frame, and compression blocks that shift level independently.
      flick *= 1 + 0.03 * gauss(r);
      const bo = new Float32Array((W / 8) * (H / 8));
      for (let i = 0; i < bo.length; i++) bo[i] = 3 * gauss(r);
      for (let y = 0, i = 0, q = 0; y < H; y++) for (let x = 0; x < W; x++, i++, q += 4) {
        const v = Math.min(255, Math.max(0, img[i] * agc * flick + 6 * gauss(r) + bo[(y >> 3) * (W / 8) + (x >> 3)]));
        rgba[q] = rgba[q + 1] = rgba[q + 2] = v; rgba[q + 3] = 255;
      }
    }
    tk.process(rgba, W, H, t, false);

    out.n++;
    const tg = tk.target;
    if (process.env.DBG) {
      const [a, b] = process.env.DBG.split(',').map(Number);
      if (t >= a && t <= b) {
        console.log('  t', t.toFixed(3), 'truth', truth && truth.map(v => v.toFixed(0)).join(','), 'locked', tk.lockedId);
        for (const q of tk.tracks) console.log('   #' + q.id, q.x.toFixed(0), q.y.toFixed(0), 'v', q.vx.toFixed(1), q.vy.toFixed(1),
          'hits', q.hits, 'miss', q.misses, 'lit', q.lit, 'pass', q.pass, q.passing, 's', q.score.toFixed(2), 'steady', q.steady, 'gate', (q.gate||0).toFixed(0));
      }
    }
    const inFrame = truth && truth[0] > 0 && truth[1] > 0 && truth[0] < W && truth[1] < H;
    if (tg) out.lockedFrames++;
    if (!truth) { if (tg) out.wrong++; continue; }
    if (!inFrame) continue;
    out.inFrame++;
    const e = tg ? Math.hypot(tg.x - truth[0], tg.y - truth[1]) : Infinity;
    if (tg && e < 30 && out.acq === null) out.acq = t;
    if (out.acq !== null) out.inAfter++;
    if (tg && tg.lit && e < 60) out.litErrs.push(e);
    if (tg && e < 60) {
      if (out.acq !== null) { out.good++; out.errs.push(e); }
      gap = 0;
    } else {
      if (tg && e > 90) { out.wrong++; if (process.env.WRONG) console.log('WRONG', t.toFixed(3), tk.state, truth.map(v => v.toFixed(0)).join(','), tg.x.toFixed(0) + ',' + tg.y.toFixed(0), 'lit', tg.lit, 'score', tg.score.toFixed(2)); }
      if (tg && out.acq !== null) { const kx = Math.min(tg.misses, 9) + (tg.lit ? 'L' : 'D'); out.missHist[kx] = (out.missHist[kx] || 0) + 1; }
      else if (out.acq !== null) out.missHist['none'] = (out.missHist['none'] || 0) + 1;
      if (out.acq !== null) { gap++; out.maxGap = Math.max(out.maxGap, gap); }
    }
    if (verbose) console.log(t.toFixed(3), tk.state, truth.map(v => v.toFixed(0)).join(','),
      tg ? `${tg.x.toFixed(0)},${tg.y.toFixed(0)} s=${tg.score.toFixed(2)} f=${tg.freq.toFixed(1)}` : '-',
      tk.tracks.length);
  }
  return out;
}

function pct(a, p) { if (!a.length) return NaN; const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; }

const only = process.argv[2];
const verbose = process.argv.includes('-v');
let fail = 0;
// held%   : frames locked on the beacon (within 60 px) after first acquisition
// lit err : median / p95 error on frames where the beacon is lit and seen
// dark err: all locked frames, including the dark phase, where position is
//           predicted -- a hand that turns while the light is off cannot be
//           seen turning by anything
console.log('scenario              acquire   held%   lit-err p50/p95   all p50/p95   wrong  longest-loss');
for (const sc of SCEN) {
  if (only && only !== '-v' && sc.name !== only) continue;
  const o = run(sc, verbose);
  if (!sc.path) {
    const ok = o.wrong === 0;   // any lock at all with no beacon is a failure
    if (!ok) fail++;
    console.log(`${sc.name.padEnd(20)}  ${'—'.padStart(6)}   ${'—'.padStart(5)}   ${'—'.padStart(5)}  ${'—'.padStart(4)}  ${String(o.wrong).padStart(5)}  ${ok ? 'PASS (never locked)' : 'FAIL: locked on a decoy'}`);
    continue;
  }
  const after = o.inAfter;
  const held = after > 0 ? 100 * o.good / Math.max(1, after) : 0;
  if (process.env.HIST) console.log(JSON.stringify(o.missHist));
  const ok = o.acq !== null && o.acq < 2.0 && held > 90 && o.wrong <= 0.02 * o.n;
  if (!ok && !sc.stretch) fail++;
  console.log(`${sc.name.padEnd(20)}  ${o.acq === null ? '  none' : (o.acq.toFixed(2) + ' s').padStart(6)}   ${held.toFixed(1).padStart(5)}   ${pct(o.litErrs, .5).toFixed(1).padStart(6)} / ${pct(o.litErrs, .95).toFixed(1).padStart(5)}   ${pct(o.errs, .5).toFixed(1).padStart(5)} / ${pct(o.errs, .95).toFixed(1).padStart(5)}  ${String(o.wrong).padStart(5)}  ${String(o.maxGap).padStart(3)} fr  ${ok ? 'PASS' : sc.stretch ? 'LIMIT' : 'FAIL'}`);
}
process.exit(fail ? 1 : 0);
