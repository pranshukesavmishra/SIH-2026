/*
 * ZeroDrift live tracker core — no DOM, so it can be benchmarked headlessly
 * (node tools/sim/live_tracker_bench.mjs) as well as run on a webcam in
 * live.html.
 *
 * Two jobs, two mechanisms.
 *
 * IDENTIFY. Every bright blob becomes a track, and each track's own
 * brightness history is tested for the beacon's blink. The test rides the
 * track, not a fixed pixel, so a moving torch is identified as easily as a
 * still one. Lamps, windows and screens are steady, a face never switches
 * off, and mains flicker sits far outside the band -- none of them passes.
 *
 * FOLLOW. Once identified, a dedicated beacon filter takes over. It knows
 * three things no generic tracker does: how bright the beacon is when lit,
 * WHEN it will next be lit (its measured frequency and phase), and that a
 * beacon switching on shows up as light that was not there a frame ago.
 * A steady lamp can never produce that last cue, which is what lets the
 * filter use a wide gate -- wide enough for a hand flicking a phone around
 * -- without being captured by the lamps it sweeps past.
 */
(function (root) {
  "use strict";

  const DEFAULTS = {
    targetHz: 4,
    rateTol: 0.10,         // accepted blink rate: targetHz within ±10%
    minBright: 150,        // a blob must reach this luma to be seeded
    minDepth: 0.30,        // (on - off) / on along a track
    seedContrast: 38,      // luma above local background to seed a blob
    block: 32,             // background block size, px
    maxBlobs: 64,
    maxTracks: 48,
    minArea: 2,
    windowS: 1.6,          // blink-test window
    minSpanS: 0.85,        // shortest history the blink test will judge
    minFrac: 0.42,         // share of a track's variance at the blink rate
    confirmFrames: 3,      // consecutive passes before a lock is declared
    coastS: 1.0,           // how long a lock may go unseen before it is lost
    reacquireS: 2.5,       // how long a lost lock is hunted for
    selfLaserMatch: 0.85,
  };

  function Tracker(opts) {
    this.o = Object.assign({}, DEFAULTS, opts || {});
    this.reset();
  }

  Tracker.prototype.reset = function () {
    this.tracks = [];
    this.nextId = 1;
    this.lock = null;
    this.lost = null;          // {x, y, t, ...} of the last lost lock
    this.prov = null;          // provisional relight event while reacquiring
    this.state = "SEARCHING";
    this.frame = 0;
    this.lastT = null;
    this.fps = 0;
    this.w = 0; this.h = 0;
    this.target = null; this.candidate = null;
    this.statics = [];         // lights proven steady by the lock itself
    this.events = []; this.hot = [];
  };

  Tracker.prototype.setOption = function (k, v) { this.o[k] = v; };

  /* ---------------------------------------------------------------- */
  Tracker.prototype._alloc = function (w, h) {
    if (w === this.w && h === this.h) return;
    this.w = w; this.h = h;
    this.Y = new Uint8Array(w * h);
    this.prevY = new Uint8Array(w * h);
    this.hasPrev = false;
    this.mark = new Int32Array(w * h);
    this.owner = new Int32Array(w * h);
    this.stack = new Int32Array(w * h);
    this.bw = Math.ceil(w / this.o.block);
    this.bh = Math.ceil(h / this.o.block);
    this.bmean = new Float32Array(this.bw * this.bh);
    this.bcnt = new Float32Array(this.bw * this.bh);
    this.bbg = new Float32Array(this.bw * this.bh);
    this.seeds = new Int32Array(Math.ceil(w * h / 4) + 1);
    this.order = new Int32Array(Math.ceil(w * h / 4) + 1);
    this.tracks = []; this.lock = null; this.lost = null; this.prov = null;
  };

  // Every pixel constant is written for a 640-wide frame; scale to the camera.
  Tracker.prototype._k = function () { return this.w / 640; };

  Tracker.prototype._luma = function (rgba) {
    const Y = this.Y, n = this.w * this.h;
    for (let i = 0, q = 0; i < n; i++, q += 4) {
      Y[i] = (rgba[q] * 77 + rgba[q + 1] * 150 + rgba[q + 2] * 29) >> 8;
    }
  };

  /* Local background: each block's mean, then the MIN over its 3x3 block
     neighbourhood -- a torch filling its own block must not raise the
     background it is measured against. */
  Tracker.prototype._background = function () {
    const { w, h, Y, bw, bh, bmean, bcnt, bbg } = this, B = this.o.block;
    bmean.fill(0); bcnt.fill(0);
    for (let y = 0; y < h; y += 2) {
      const by = (y / B) | 0, row = y * w;
      for (let x = 0; x < w; x += 2) {
        const bi = by * bw + ((x / B) | 0);
        bmean[bi] += Y[row + x]; bcnt[bi]++;
      }
    }
    let sum = 0;
    for (let i = 0; i < bmean.length; i++) { bmean[i] /= Math.max(1, bcnt[i]); sum += bmean[i]; }
    this.sceneMean = sum / bmean.length;
    for (let by = 0; by < bh; by++) for (let bx = 0; bx < bw; bx++) {
      let m = 255;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const yy = by + dy, xx = bx + dx;
        if (yy < 0 || xx < 0 || yy >= bh || xx >= bw) continue;
        const v = bmean[yy * bw + xx]; if (v < m) m = v;
      }
      bbg[by * bw + bx] = m;
    }
  };

  Tracker.prototype._bgAt = function (x, y) {
    const B = this.o.block;
    const bx = Math.min(this.bw - 1, Math.max(0, (x / B) | 0));
    const by = Math.min(this.bh - 1, Math.max(0, (y / B) | 0));
    return this.bbg[by * this.bw + bx];
  };

  /* Bright blobs, 8-connected. Seeds are grown brightest first, each down
     to half its own height above background, so a torch held in front of a
     lit shirt or a pale table stays its own blob instead of being swallowed
     by the dimmer surface behind it. Each blob is located by its core. */
  Tracker.prototype._blobs = function () {
    const { w, h, Y, mark, owner, stack, o, seeds, order } = this, B = o.block, bw = this.bw;
    const stamp = this.frame + 1;
    const cnt = new Int32Array(257);
    let ns = 0;
    for (let y = 1; y < h - 1; y += 2) {
      const by = (y / B) | 0;
      for (let x = 1; x < w - 1; x += 2) {
        const i = y * w + x, v = Y[i];
        if (v < o.minBright) continue;
        if (v < this.bbg[by * bw + ((x / B) | 0)] + o.seedContrast) continue;
        if (ns < seeds.length) { seeds[ns++] = i; cnt[v]++; }
      }
    }
    const start = new Int32Array(256);
    for (let v = 255, acc = 0; v >= 0; v--) { start[v] = acc; acc += cnt[v]; }
    for (let s = 0; s < ns; s++) { const v = Y[seeds[s]]; order[start[v]++] = seeds[s]; }

    const blobs = [];
    for (let s = 0; s < ns && blobs.length < 4 * o.maxBlobs; s++) {
      const i = order[s];
      if (mark[i] === stamp) continue;
      const y = (i / w) | 0, x = i - y * w, v = Y[i];
      const bg = this.bbg[((y / B) | 0) * bw + ((x / B) | 0)];
      const grow = Math.max(bg + 0.6 * o.seedContrast, 0.8 * o.minBright, v - 0.5 * (v - bg));
      const me = blobs.length;
      let sp = 0; stack[sp++] = i; mark[i] = stamp; owner[i] = me;
      let area = 0, peak = 0, peakI = i, x0 = x, x1 = x, y0 = y, y1 = y, touches = -1;
      while (sp > 0) {
        const j = stack[--sp];
        const jy = (j / w) | 0, jx = j - jy * w, vj = Y[j];
        area++;
        if (vj > peak) { peak = vj; peakI = j; }
        if (jx < x0) x0 = jx; if (jx > x1) x1 = jx;
        if (jy < y0) y0 = jy; if (jy > y1) y1 = jy;
        if (area > 60000) continue;             // a window: stop growing
        for (let dy = -1; dy <= 1; dy++) {
          const ny = jy + dy; if (ny < 0 || ny >= h) continue;
          for (let dx = -1; dx <= 1; dx++) {
            const nx = jx + dx; if (nx < 0 || nx >= w) continue;
            const n = ny * w + nx;
            if (mark[n] === stamp) { if (owner[n] !== me && owner[n] >= 0) touches = owner[n]; continue; }
            if (Y[n] < grow) continue;
            mark[n] = stamp; owner[n] = me; stack[sp++] = n;
          }
        }
      }
      // A dimmer region wrapped around a brighter blob it touches is that
      // blob's bloom, not a second light. Left separate, a lamp's halo and
      // its core traded places frame to frame and the lamp "blinked".
      if (touches >= 0 && blobs[touches] && area < 4 * blobs[touches].area) {
        for (let yy = y0; yy <= y1; yy++) for (let xx = x0; xx <= x1; xx++) {
          const n = yy * w + xx; if (mark[n] === stamp && owner[n] === me) owner[n] = touches;
        }
        continue;
      }
      if (area < o.minArea) { for (let yy = y0; yy <= y1; yy++) for (let xx = x0; xx <= x1; xx++) { const n = yy * w + xx; if (mark[n] === stamp && owner[n] === me) owner[n] = -1; } continue; }
      // Core: the top quarter of the blob's own range.
      const cut = peak - 0.25 * (peak - bg);
      let qx = 0, qy = 0, qw = 0, qx0 = x1, qx1 = x0, qy0 = y1, qy1 = y0, rise = 0;
      for (let yy = y0; yy <= y1; yy++) {
        const row = yy * w;
        for (let xx = x0; xx <= x1; xx++) {
          const n = row + xx;
          if (mark[n] !== stamp || owner[n] !== me) continue;
          const vv = Y[n]; if (vv < cut) continue;
          const wt = vv - cut + 1; qx += xx * wt; qy += yy * wt; qw += wt;
          if (xx < qx0) qx0 = xx; if (xx > qx1) qx1 = xx;
          if (yy < qy0) qy0 = yy; if (yy > qy1) qy1 = yy;
          // How much of this light is NEW since the previous frame.
          if (this.hasPrev) { const d = vv - this.prevY[n]; if (d > rise) rise = d; }
        }
      }
      blobs.push({ x: qx / qw, y: qy / qw, area, peak, bg, c: peak - bg, rise,
                   size: Math.max(qx1 - qx0 + 1, qy1 - qy0 + 1), taken: false, owner: null });
    }
    blobs.sort((a, b) => b.c - a.c);
    if (blobs.length > o.maxBlobs) blobs.length = o.maxBlobs;
    return blobs;
  };

  /* Brightest luma within r of a point. */
  Tracker.prototype._peakNear = function (x, y, r) {
    const { w, h, Y } = this;
    const xi = Math.round(x), yi = Math.round(y), R = Math.max(2, Math.round(r));
    let m = 0;
    for (let yy = Math.max(0, yi - R); yy <= Math.min(h - 1, yi + R); yy++) {
      const row = yy * w;
      for (let xx = Math.max(0, xi - R); xx <= Math.min(w - 1, xi + R); xx++) {
        const v = Y[row + xx]; if (v > m) m = v;
      }
    }
    return m;
  };

  /* Mean luma over a small disc: the level AT the light, not the brightest
     thing near it. Used to see a switch-on switch off again: in a lit room
     the torch's dark phase is the phone body with a white wall a few pixels
     away, and a max over the neighbourhood would read the wall. */
  Tracker.prototype._meanNear = function (x, y, r) {
    const { w, h, Y } = this;
    const xi = Math.round(x), yi = Math.round(y), R = Math.max(1, Math.round(r)), r2 = R * R;
    let s = 0, n = 0;
    for (let yy = Math.max(0, yi - R); yy <= Math.min(h - 1, yi + R); yy++) {
      const row = yy * w, dy = yy - yi;
      for (let xx = Math.max(0, xi - R); xx <= Math.min(w - 1, xi + R); xx++) {
        const dx = xx - xi; if (dx * dx + dy * dy > r2) continue;
        s += Y[row + xx]; n++;
      }
    }
    return n ? s / n : 0;
  };

  /* ================================================================
     IDENTIFY: generic tracks + blink test
     ================================================================ */
  function newTrack(id, b, t) {
    return { id, x: b.x, y: b.y, vx: 0, vy: 0, size: b.size, born: t,
             lastSeen: t, hits: 1, misses: 0, path: 0, anchored: false,
             hist: [{ t, c: b.c }], onLevel: b.c, bgLevel: b.bg,
             score: 0, freq: 0, depth: 0, phase: 0, t0: t,
             pass: 0, passing: false, lit: true };
  }

  // The accepted band around the set rate: ±10%, never tighter than
  // ±0.3 Hz (what a 30 fps camera can resolve over one identification).
  Tracker.prototype._tol = function () {
    return Math.max(0.3, this.o.rateTol * this.o.targetHz);
  };

  Tracker.prototype._score = function (tr, now) {
    const o = this.o, H = tr.hist;
    const from = now - o.windowS;
    let i0 = 0; while (i0 < H.length && H[i0].t < from) i0++;
    const n = H.length - i0;
    const span = n > 1 ? H[H.length - 1].t - H[i0].t : 0;
    tr.score = 0; tr.freq = 0; tr.depth = 0;
    if (n < 16 || span < o.minSpanS) { tr.wrongRate = false; return false; }

    let mean = 0;
    for (let i = i0; i < H.length; i++) mean += H[i].c;
    mean /= n;
    let pow = 0;
    for (let i = i0; i < H.length; i++) { const d = H[i].c - mean; pow += d * d; }
    if (pow < 1e-6) return false;

    // The blink rate is whatever rate dominates this light's brightness --
    // searched well beyond the band, so a light blinking at 3 or 5 Hz is
    // measured AS 3 or 5 Hz and refused at a 4 Hz setting, instead of
    // leaking into the band edge and passing.
    const tol = this._tol(), f0 = o.targetHz;
    let best = 0, bestF = 0, bestRe = 0, bestIm = 0, dom = 0, domF = 0;
    const t0 = H[i0].t;
    const nyq = 0.5 * (this.fps || 30);
    for (let f = 0.75; f < nyq - 0.4; f += 0.05) {
      let re = 0, im = 0;
      const wv = 2 * Math.PI * f;
      for (let i = i0; i < H.length; i++) {
        const th = wv * (H[i].t - t0), d = H[i].c - mean;
        re += d * Math.cos(th); im -= d * Math.sin(th);
      }
      const frac = (2 * (re * re + im * im) / n) / pow;
      // (Below 1.25 Hz is drift -- a hand moving the light across
      // brighter and darker background -- not a blink rate.)
      if (f >= 1.25 && frac > dom) { dom = frac; domF = f; }
      if (Math.abs(f - f0) <= tol && frac > best) { best = frac; bestF = f; bestRe = re; bestIm = im; }
    }
    const s = []; for (let i = i0; i < H.length; i++) s.push(H[i].c);
    s.sort((a, b) => a - b);
    const p10 = s[Math.floor(0.1 * (n - 1))], p90 = s[Math.floor(0.9 * (n - 1))];
    // Depth against the lit level including background: a beacon's off
    // phase in a lit room is not black, it is back down at the background.
    const depth = p90 > 0 ? (p90 - p10) / (p90 + (tr.bgLevel || 0)) : 0;
    // The dominant rate must BE the set rate (within the band): energy that
    // peaks outside it -- a slower or faster blinker, mains flicker aliasing
    // in -- is a different light, however much of it spills into the band.
    const onRate = Math.abs(domF - f0) <= tol;
    // A light clearly blinking, but at another rate, is marked so the lock
    // can refuse it on sight rather than after following it a while.
    tr.wrongRate = depth >= o.minDepth && dom > 0.35 && !onRate && dom > 1.6 * best;
    tr.score = Math.min(1, best); tr.freq = domF; tr.depth = depth;
    tr.phase = Math.atan2(bestIm, bestRe); tr.t0 = t0;
    return best >= o.minFrac && onRate && depth >= o.minDepth && p10 <= 0.6 * p90 && p90 >= 25 && !tr.wrongRate;
  };

  Tracker.prototype._updateTracks = function (blobs, t) {
    const o = this.o, k = this._k(), fps = this.fps || 30;
    for (const tr of this.tracks) {
      const nf = Math.max(1, Math.round((t - tr.lastSeen) * fps));
      const np = Math.min(nf, Math.round(0.35 * fps));
      tr.px = tr.x + tr.vx * np; tr.py = tr.y + tr.vy * np; tr.nf = nf;
      const spd = Math.hypot(tr.vx, tr.vy);
      tr.gate = tr.anchored ? Math.max(7 * k, Math.min(0.7 * tr.size, 24 * k))
        : Math.min(190 * k, (26 + 0.5 * tr.size) * k + 0.6 * spd * nf + 1.6 * k * nf * nf);
    }
    const pairs = [];
    this.tracks.forEach((tr, ti) => blobs.forEach((b, bi) => {
      const d = Math.hypot(b.x - tr.px, b.y - tr.py);
      if (d <= tr.gate) pairs.push([d / tr.gate, ti, bi]);
    }));
    pairs.sort((a, b) => a[0] - b[0]);
    const used = new Uint8Array(this.tracks.length);
    for (const [, ti, bi] of pairs) {
      if (used[ti] || blobs[bi].taken) continue;
      used[ti] = 1; blobs[bi].taken = true;
      const tr = this.tracks[ti], b = blobs[bi];
      b.owner = tr;
      const rx = b.x - tr.px, ry = b.y - tr.py;
      if (tr.hits < 2) { tr.vx = (b.x - tr.x) / tr.nf; tr.vy = (b.y - tr.y) / tr.nf; }
      else { tr.vx += 0.45 * rx / tr.nf; tr.vy += 0.45 * ry / tr.nf; }
      tr.path += Math.hypot(b.x - tr.x, b.y - tr.y);
      const a = tr.anchored ? 0.3 : 0.85;
      tr.x = tr.px + a * rx; tr.y = tr.py + a * ry;
      if (tr.anchored) { tr.vx = 0; tr.vy = 0; }
      tr.size = 0.7 * tr.size + 0.3 * b.size;
      tr.area = 0.7 * (tr.area || b.area) + 0.3 * b.area;
      tr.lastSeen = t; tr.hits++; tr.misses = 0; tr.lit = true;
      tr.onLevel = Math.max(b.c, tr.onLevel * 0.97); tr.bgLevel = b.bg;
      tr.anchored = tr.hits >= 15 && tr.path / tr.hits < 0.8 * k;
      tr.hist.push({ t, c: b.c });
    }
    this.tracks.forEach((tr, ti) => {
      if (used[ti]) return;
      // Measure the dark phase where the light should be, rather than
      // assume it: a steady light that association missed must not look
      // like it blinked.
      tr.misses++; tr.lit = false;
      const c = Math.max(0, this._peakNear(tr.px, tr.py, Math.max(3 * k, 0.6 * tr.size)) - this._bgAt(tr.px, tr.py));
      tr.hist.push({ t, c });
    });
    for (const b of blobs) {
      if (b.taken || this.tracks.length >= o.maxTracks) continue;
      const tr = newTrack(this.nextId++, b, t);
      b.owner = tr;
      this.tracks.push(tr);
    }
    // Two tracks moving together on one light are one track.
    for (let i = 0; i < this.tracks.length; i++) for (let j = i + 1; j < this.tracks.length; j++) {
      const a = this.tracks[i], b = this.tracks[j];
      if (a._dead || b._dead || a.anchored || b.anchored) continue;
      if (Math.hypot(a.vx - b.vx, a.vy - b.vy) > 6 * k) continue;
      if (Math.hypot(a.x - b.x, a.y - b.y) > Math.min(30 * k, Math.max(10 * k, 0.6 * Math.min(a.size, b.size)))) continue;
      const pr = q => (q.passing ? 1e4 : 0) + q.hits;
      (pr(a) >= pr(b) ? b : a)._dead = true;
    }
    const keep = [];
    for (const tr of this.tracks) {
      if (tr._dead) continue;
      if (t - tr.lastSeen > (tr.passing ? 0.8 : 0.45)) continue;
      if (tr.hist.length > 90) tr.hist.splice(0, tr.hist.length - 90);
      const pass = this._score(tr, t);
      tr.pass = pass ? tr.pass + 1 : 0;
      tr.passing = tr.pass >= o.confirmFrames;
      // Remember proven-steady lights beyond the life of their track. The
      // phone passing in front of a lamp hides it long enough for its track
      // to die, and when the phone moves off, the lamp "switches on" -- a
      // light that appears where a known lamp stands is that lamp.
      if (tr.anchored && tr.hist.length > 30 && !tr.passing && tr.depth < 0.6 * o.minDepth) {
        const s0 = this.statics.find(q => q.ttl && Math.hypot(q.x - tr.x, q.y - tr.y) < 8 * k);
        if (s0) { s0.t = t; } else this.statics.push({ x: tr.x, y: tr.y, t, ttl: 30 });
      }
      keep.push(tr);
    }
    this.tracks = keep;
  };

  /* ================================================================
     FOLLOW: the beacon filter
     ================================================================ */
  Tracker.prototype._startLock = function (src, t, how) {
    const period = 1 / (src.freq && Math.abs(src.freq - this.o.targetHz) <= this._tol() ? src.freq : this.o.targetHz);
    // Phase from the identification's own Fourier coefficient: the
    // fundamental of a 50% square wave peaks mid-way through the lit half,
    // so switch-on is a quarter period before that peak.
    let tOn = t;
    if (src.freq && src.t0 !== undefined) {
      const w = 2 * Math.PI * src.freq;
      tOn = src.t0 - src.phase / w - 0.25 * period;
    }
    // Start from where the source is NOW: a track confirmed during its dark
    // phase was last measured a few frames ago, and at speed that is far.
    const nf0 = src.lastSeen !== undefined ? Math.min(9, Math.max(0, Math.round((t - src.lastSeen) * (this.fps || 30)))) : 0;
    const x0 = Math.min(this.w - 1, Math.max(0, src.x + (src.vx || 0) * nf0));
    const y0 = Math.min(this.h - 1, Math.max(0, src.y + (src.vy || 0) * nf0));
    this.lock = {
      x: x0, y: y0, mx: src.x, my: src.y, vx: src.vx || 0, vy: src.vy || 0,
      size: src.size || 10, area: src.area || 400, onLevel: src.onLevel || 100, bgLevel: src.bgLevel || 0,
      // Seen when the source was last actually seen -- a track confirmed in
      // its dark phase has been predicted since, and the rescue logic needs
      // to know how blind it really is.
      period, tOn, lastSeen: src.lastSeen !== undefined ? src.lastSeen : t, litSince: t, prevLit: true, seen: 1,
      score: src.score || 0.6, freq: 1 / period, since: t, how,
      trail: [{ x: src.x, y: src.y, t, lit: true }], lit: true, misses: 0, hist: [],
    };
    this.lost = null; this.prov = null;
  };

  // Phase within the blink cycle, 0..1, 0 = switch-on.
  Tracker.prototype._phase = function (L, t) {
    const p = ((t - L.tOn) / L.period) % 1;
    return p < 0 ? p + 1 : p;
  };

  /* Phase-locked loop on the blink. Every lit observation says "this is
     mid-lit" (phase 0.25), every dark one "mid-dark" (0.75); the error
     nudges the phase, and its running sum trims the period. Re-anchoring on
     the first lit frame after a gap, as a first version did, drifted: one
     missed flash made the next frame look like a switch-on, the phase slid
     late, the dark-phase gate then skipped a real flash, and the error fed
     itself. */
  Tracker.prototype._pll = function (L, t, target) {
    let e = this._phase(L, t) - target;
    e -= Math.round(e);                       // wrap to [-0.5, 0.5)
    if (Math.abs(e) > 0.4) return;            // ambiguous: ignore
    L.tOn += 0.12 * e * L.period;
    L.perr = 0.9 * (L.perr || 0) + e;
    const tol = this._tol(), lo = 1 / (this.o.targetHz + tol), hi = 1 / Math.max(0.5, this.o.targetHz - tol);
    L.period = Math.min(hi, Math.max(lo, L.period * (1 + 0.004 * L.perr)));
    L.freq = 1 / L.period;
  };

  // A blob owned by a generic track that sits still AND does not blink.
  // Stillness alone is not enough -- a beacon on a table sits still too.
  Tracker.prototype._steadyOwner = function (b) {
    const q = b.owner;
    // Judged by modulation DEPTH, not by the spectral score: auto-exposure
    // chasing the beacon makes every steady lamp swing a few percent at
    // exactly the blink rate, which scores well and means nothing.
    return !!(q && q.anchored && !q.passing && q.hist.length > 20 && q.depth < 0.6 * this.o.minDepth);
  };

  Tracker.prototype._isStatic = function (b, t) {
    const k = this._k();
    this.statics = this.statics.filter(s => t - s.t < (s.ttl || 4));
    return this.statics.some(s => Math.hypot(b.x - s.x, b.y - s.y) < 14 * k);
  };

  Tracker.prototype._follow = function (blobs, t) {
    const L = this.lock, o = this.o, k = this._k(), fps = this.fps || 30;
    const nf = Math.max(1, Math.round((t - L.lastSeen) * fps));
    const np = Math.min(nf, Math.round(0.3 * fps));
    // Constant velocity plus a damped share of the measured acceleration: a
    // hand sweeping an arc is turning the whole time the torch is dark.
    const na = Math.min(np, 5), ax = L.ax || 0, ay = L.ay || 0;
    const px = Math.min(this.w - 1, Math.max(0, L.mx + L.vx * np + 0.5 * ax * na * na));
    const py = Math.min(this.h - 1, Math.max(0, L.my + L.vy * np + 0.5 * ay * na * na));
    const spd = Math.hypot(L.vx, L.vy);
    const G = Math.min(280 * k, (32 + 0.6 * L.size) * k + 1.0 * spd * nf + 2.2 * k * nf * nf);
    const ph = this._phase(L, t);
    // Deep in the dark half of the cycle the beacon cannot be lit; anything
    // bright near it then is by definition something else.
    const deepDark = ph > 0.66 && ph < 0.9 && L.seen > 8;

    const blind = t - L.lastSeen > 0.9 * L.period;
    const Gr = 0.45 * Math.hypot(this.w, this.h);
    let best = null, bestCost = Infinity;
    {
      for (const b of blobs) {
        if (b.c < 0.45 * L.onLevel) continue;                 // not lit like the beacon
        if (b.size > Math.max(60 * k, 3.5 * L.size)) continue; // not compact like it
        if (b.area > Math.max(2500 * k * k, 6 * (L.area || 400))) continue;
        const d = Math.hypot(b.x - px, b.y - py);
        const fresh = b.rise >= 0.35 * L.onLevel;             // light that just appeared
        // Blind for a whole cycle: the hand went where the prediction did
        // not. The beacon will switch on again on schedule, so a light that
        // switches on, lit and sized like it, is taken from much further out.
        // Anything wrong this admits is thrown out by the dark-phase vetoes.
        const rescue = blind && fresh && d <= Gr;
        if (d > G && !rescue) continue;
        // A light a generic track has proven stationary, or that this lock
        // has caught being steady, is a poor candidate: only right on the
        // prediction, and even then it loses to anything that just switched
        // on. (Fresh alone is not enough to rescue it -- a lamp uncovered
        // by the moving phone "appears" too.)
        // A light proven steady is never the beacon. Letting it be taken
        // "when right on the prediction" meant a torch swept across a lamp
        // left the lock sitting on the lamp, seeing it every frame and so
        // never blind enough to go looking for the torch.
        if (this._steadyOwner(b) || this._isStatic(b, t)) continue;
        if (b.owner && b.owner.wrongRate) continue;
        let cost = d > G ? 1 + d / Gr : d / G;
        if (fresh) cost -= 0.25;
        // Lit when the phase says dark: possible (the phase can be off),
        // but a strike against it.
        if (deepDark) cost += 0.35;
        cost += 0.25 * Math.min(2, Math.abs(Math.log((b.c + 1) / (L.onLevel + 1))));
        if (cost < bestCost) { bestCost = cost; best = b; }
      }
    }

    if (best) {
      const rx = best.x - px, ry = best.y - py;
      // Rescued from far outside the gate: the old velocity is exactly what
      // was wrong, so start over -- position from this light, velocity from
      // the next one (the seen < 3 branch below).
      const rescued = Math.hypot(rx, ry) > G;
      if (rescued) {
        // Borrow the velocity of the generic track that owns this light, if
        // it has one worth borrowing; otherwise start from rest.
        const q = best.owner;
        const ok = q && q.hits >= 3 && t - q.lastSeen < 0.05;
        L.vx = ok ? q.vx : 0; L.vy = ok ? q.vy : 0; L.seen = ok ? 3 : 0; L.mx = best.x; L.my = best.y;
        L.ax = 0; L.ay = 0;
      }
      else if (nf > 1 && L.seen < 3) { L.vx = (best.x - L.mx) / nf; L.vy = (best.y - L.my) / nf; }
      else {
        const beta = nf > 1 ? 0.6 : 0.5;
        const ovx = L.vx, ovy = L.vy;
        L.vx += beta * rx / nf; L.vy += beta * ry / nf;
        const amax = 4 * k;
        const mx_ = Math.max(-amax, Math.min(amax, (L.vx - ovx) / nf));
        const my_ = Math.max(-amax, Math.min(amax, (L.vy - ovy) / nf));
        L.ax = 0.6 * (L.ax || 0) + 0.4 * mx_; L.ay = 0.6 * (L.ay || 0) + 0.4 * my_;
      }
      const vmax = 50 * k, sp = Math.hypot(L.vx, L.vy);
      if (sp > vmax) { L.vx *= vmax / sp; L.vy *= vmax / sp; }
      if (rescued) { L.x = best.x; L.y = best.y; }
      else { L.mx = L.x = px + 0.85 * rx; L.my = L.y = py + 0.85 * ry; }
      // A lit run starts after any frame the beacon was not taken -- whether
      // or not the dark was seen (the prediction may have sat over a bright
      // wall). A steady light, taken every frame, never gets that reset.
      if (!L.prevLit || nf > 1) {
        L.litSince = t; L.litX = L.mx; L.litY = L.my; L.litVx = L.vx; L.litVy = L.vy;
        // A genuine switch-on for the rate measurement: darkness actually
        // seen at the beacon, then a sharp rise. A frame skipped mid-flash,
        // or a stray light taken for a moment, is not one -- counting those
        // read a 4 Hz beacon as 4.6-5.2 Hz.
        if (!L.prevLit && L.darkSeen && best.rise >= 0.5 * L.onLevel && this._rateCheck(L, t)) return;
      }
      // What we are following is lit when its own phase says dark. Once is
      // phase error; three times in quick succession is a different light.
      // (Counted only for a light we actually TOOK: coasting over a bright
      // shirt in the dark phase says nothing about the beacon.)
      if (deepDark) {
        L.wrongLit = (L.wrongLit || 0) + 1;
        if (L.wrongLit >= 3) { this._reject(L, best, t, 'lit when it should be dark'); return; }
      } else L.wrongLit = Math.max(0, (L.wrongLit || 0) - 0.34);
      this._pll(L, t, 0.25);
      L.lastSeen = t; L.lit = true; L.prevLit = true; L.darkSeen = false; L.seen++; L.misses = 0;
      L.size = 0.8 * L.size + 0.2 * best.size;
      L.area = 0.8 * (L.area || best.area) + 0.2 * best.area;
      L.onLevel = 0.9 * L.onLevel + 0.1 * best.c;
      L.freq = 1 / L.period;
      best.lockTaken = true;
      // Steady veto: a real beacon at the bottom of the band stays lit for
      // at most half a period. Following something lit for much longer means
      // we are on a steady light: remember it as such and let go.
      const litMax = 1.7 * 0.5 / Math.max(1, o.targetHz - this._tol());
      if (t - L.litSince > litMax) { this._reject(L, best, t, 'steady light'); return; }
    } else {
      L.misses = nf; L.lit = false;
      const r = Math.max(4 * k, 0.8 * L.size);
      const bg = this._bgAt(px, py);
      const c = this._peakNear(px, py, r) - bg;
      // Only a dark phase actually SEEN counts as one. Assuming it from a
      // skipped frame let a lamp the lock had slid onto look like it blinked.
      if (c < 0.45 * L.onLevel) {
        L.prevLit = false; L.darkSeen = true; L.wrongLit = Math.max(0, (L.wrongLit || 0) - 0.5);
        if (t - L.lastSeen < 0.6 * L.period) this._pll(L, t, 0.75);
      }

      // Dim-but-lit beacon (a torch turned partly away): refine on the local
      // light, if the phase says it should be on.
      // Never onto a light already known to be steady: that refine is how a
      // lock used to settle on a lamp and, seeing it every frame, never
      // notice the torch had moved on.
      const onSteady = blobs.some(b => (this._steadyOwner(b) || this._isStatic(b, t)) &&
                                       Math.hypot(b.x - px, b.y - py) < 2 * r + 0.5 * b.size);
      if (!deepDark && !onSteady && ph < 0.5 && c > Math.max(18, 0.3 * L.onLevel)) {
        const ref = this._centroid(px, py, 2 * r, bg + 0.5 * c);
        // Position only. It does NOT count as seeing the beacon: a refine
        // that refreshed lastSeen kept a lock that had coasted into a frame
        // corner "seeing" the corner forever, so it never went looking.
        if (ref && Math.hypot(ref.x - px, ref.y - py) < r && t - L.lastSeen < 0.5 * L.period) {
          L.x = ref.x; L.y = ref.y;
        } else { L.x = px; L.y = py; }
      } else { L.x = px; L.y = py; }
      if (t - L.lastSeen > o.coastS) { this._loseLock(t, 'not seen'); return; }
    }
    // Rate check on the lock's own brightness history. A 50%-duty beacon
    // has no energy at twice its rate; a strobe running at twice the rate
    // has most of it there. Onset spacing alone cannot tell them apart.
    L.hist.push({ t, c: best ? best.c : Math.max(0, this._peakNear(L.x, L.y, Math.max(4 * k, 0.8 * L.size)) - this._bgAt(L.x, L.y)) });
    while (L.hist.length && t - L.hist[0].t > 1.5) L.hist.shift();
    // Rate check on the lock's own brightness over the last 0.8 s (short,
    // so a decoy the lock has slid onto soon dominates the window): the
    // strongest rate outside the band must not beat the strongest inside
    // it. Onset spacing alone cannot tell a beacon from a strobe at twice
    // its rate, or from a slow indicator, and this can.
    const Hs = L.hist.filter(h => t - h.t <= 0.8);
    if (t - L.since > 0.6 && Hs.length > 14) {
      let m = 0, v = 0;
      for (const h of Hs) m += h.c;
      m /= Hs.length;
      for (const h of Hs) v += (h.c - m) * (h.c - m);
      const frac = f => {
        let re = 0, im = 0;
        for (const h of Hs) { const a = 2 * Math.PI * f * h.t; re += (h.c - m) * Math.cos(a); im += (h.c - m) * Math.sin(a); }
        return 2 * (re * re + im * im) / Hs.length / Math.max(v, 1e-6);
      };
      const f0 = o.targetHz, nyq = 0.5 * fps;
      let fin = 0, fout = 0;
      for (let f = Math.max(0.5, f0 - 1); f <= f0 + 1.001; f += 0.25) fin = Math.max(fin, frac(f));
      for (let f = f0 + 2; f < nyq - 0.5; f += 0.5) fout = Math.max(fout, frac(f));
      for (let f = 0.75; f <= f0 - 2; f += 0.25) fout = Math.max(fout, frac(f));
      if (v > 1e-3 && fout > 0.35 && fout > 1.6 * fin) {
        this._reject(L, { x: L.x, y: L.y }, t, 'blinks at the wrong rate');
        return;
      }
    }
    L.trail.push({ x: L.x, y: L.y, t, lit: L.lit });
    while (L.trail.length && t - L.trail[0].t > 0.6) L.trail.shift();
    // Confidence: how much of the recent time the beacon behaved like one.
    L.score = Math.max(0, Math.min(1, 1 - (t - L.lastSeen) / o.coastS));
  };

  /* The light being followed has just proved it is not the beacon (it
     stayed lit, or lit out of phase) -- typically a lamp the torch was swept
     across. That condemns the LIGHT, not the lock: mark it steady, wind the
     lock back to where it was before it took that light, and let it go
     blind, so the next switch-on anywhere nearby is picked up by the
     rescue path in a fraction of a second instead of a fresh identification. */
  Tracker.prototype._reject = function (L, b, t, why) {
    this.statics.push({ x: b.x, y: b.y, t });
    this.lastDrop = { why: why + ' (rejected, lock kept)', t: +t.toFixed(2) };
    // Back to where it was before it took that light, standing still: the
    // velocity learned since was learned from the wrong light.
    if (L.litX !== undefined) { L.mx = L.x = L.litX; L.my = L.y = L.litY; }
    L.vx = 0; L.vy = 0; L.seen = 0; L.ax = 0; L.ay = 0;
    L.lastSeen = Math.min(L.lastSeen, L.litSince) - 1 / (this.fps || 30);
    L.lit = false; L.prevLit = false; L.wrongLit = 0; L.litSince = t;
    if (t - L.lastSeen > this.o.coastS) this._loseLock(t, why);
  };

  /* The blink rate, measured from the lock's own switch-ons: the median
     spacing of the last few seconds' relights. This is the number shown,
     and the lock is let go if it sits outside the set rate's band for a
     second -- a 3 or 5 Hz light is never followed at a 4 Hz setting. */
  Tracker.prototype._rateCheck = function (L, t) {
    const f0 = this.o.targetHz, tol = this._tol();
    (L.ons = L.ons || []).push(t);
    while (L.ons.length && t - L.ons[0] > 3) L.ons.shift();
    const iv = [];
    for (let i = 1; i < L.ons.length; i++) {
      const d = L.ons[i] - L.ons[i - 1];
      if (d >= 0.55 / f0 && d <= 1.5 / f0) iv.push(d);      // skip missed flashes
    }
    if (iv.length < 6) return false;
    // Trimmed mean, not median: frames arrive in 33 ms steps, so single
    // intervals are quantised and a median of them cannot tell 3.5 Hz from
    // 3.75; the mean of several can.
    iv.sort((a, b) => a - b);
    const cut = iv.length >= 6 ? 1 : 0;
    let sum = 0; for (let i = cut; i < iv.length - cut; i++) sum += iv[i];
    L.rate = (iv.length - 2 * cut) / sum;
    if (Math.abs(L.rate - f0) > 1.2 * tol) {
      if (L.rateBad === undefined) L.rateBad = t;
      if (t - L.rateBad > 1.0) { this._loseLock(t, `blinks at ${L.rate.toFixed(1)} Hz, set to ${f0} Hz`); return true; }
    } else L.rateBad = undefined;
    return false;
  };

  Tracker.prototype._loseLock = function (t, why) {
    const L = this.lock;
    this.lost = { x: L.x, y: L.y, vx: L.vx, vy: L.vy, t, onLevel: L.onLevel, size: L.size,
                  period: L.period, why };
    this.lastDrop = { why, t: +t.toFixed(2) };
    this.lock = null; this.prov = null; this.events = [];
  };

  /* Identification from switch-on events, for a beacon moving too fast for
     any track to hold it long enough for the spectral test.

     An onset is a compact light, lit like a beacon, that was not there a
     frame ago and has no lit neighbour in the previous frame it could have
     moved from. The beacon produces one every cycle, wherever the hand has
     taken it; lamps, windows and screens never do. Three onsets a blink
     period apart, each within reach of the last, are a beacon -- about
     half a second, at any speed. After a loss two suffice near where the
     lock was, since the beacon is already known. */
  Tracker.prototype._onsets = function (blobs, t) {
    const k = this._k(), o = this.o, R = this.lost;
    const tol = this._tol(), pLo = 1 / (o.targetHz + tol), pHi = 1 / Math.max(0.5, o.targetHz - tol);
    this.events = (this.events || []).filter(e => t - e.t < 3 * pHi);
    // Watch each recent switch-on for its switch-off: the mean level AT the
    // light (not the brightest pixel near it -- in a lit room that is the
    // wall beside the phone) falling most of the way back to background.
    for (const e of this.events) {
      if (e.off || t - e.t > 0.75 * pHi || t === e.t) continue;
      const q = e.owner, seen = q && q.lastSeen === t;
      const x = q ? (seen ? q.x : q.px) : e.x, y = q ? (seen ? q.y : q.py) : e.y;
      if (this._meanNear(x, y, e.r) - e.bg < 0.4 * (e.m0 - e.bg)) e.off = true;
    }
    const prev = this.prevBlobs || [];
    for (const b of blobs) {
      if (b.lockTaken) continue;           // (generic tracks take everything; that is fine)
      if (b.c < (R ? Math.max(40, 0.45 * R.onLevel) : 60)) continue;
      if (b.area > 2500 * k * k || b.size > 60 * k) continue;
      if (b.rise < 0.6 * b.c) continue;
      if (this._steadyOwner(b) || this._isStatic(b, t)) continue;
      if (b.owner && b.owner.wrongRate) continue;
      if (prev.some(q => q.c >= 0.5 * b.c && Math.hypot(q.x - b.x, q.y - b.y) < 70 * k)) continue;
      // A fragment of a brighter onset this same frame (motion blur splits
      // a fast torch) is that onset, not a second light -- and certainly
      // not a strobe firing twice.
      if (this.events.some(e => e.t === t && Math.hypot(b.x - e.x, b.y - e.y) < 40 * k)) continue;
      // An onset too soon after another one in reach is a strobe faster
      // than the band: its every-other flash spaced like a beacon was how a
      // 7.5 Hz indicator first got locked (a subharmonic at 3.75 Hz).
      let fast = this.events.some(e => t - e.t < 0.8 * pLo &&
        Math.hypot(b.x - e.x, b.y - e.y) < (50 + 1100 * (t - e.t)) * k);
      // A strobe caught once is a strobe for a while: a dropped frame can
      // stretch one of its gaps to a beacon-like period, and that onset --
      // or one it fired before it was caught -- then seeded a chain that
      // ended on some other light. The place is marked, not just the event.
      this.hot = (this.hot || []).filter(q => t - q.t < 1.5);
      if (!fast && this.hot.some(q => Math.hypot(b.x - q.x, b.y - q.y) < 20 * k)) fast = true;
      if (fast) {
        this.hot.push({ x: b.x, y: b.y, t });
        for (const e of this.events) if (Math.hypot(b.x - e.x, b.y - e.y) < 20 * k) e.fast = true;
      }
      let best = null;
      for (const e of fast ? [] : this.events) {
        if (e.fast) continue;
        const dt = t - e.t;
        if (dt < 0.85 * pLo || dt > 1.15 * pHi) continue;
        if (e.per && Math.abs(dt - e.per) > 0.3 * e.per) continue;
        if (Math.hypot(b.x - e.x, b.y - e.y) > (50 + 1100 * dt) * k) continue;
        if (b.c > 2 * e.c || b.c < 0.5 * e.c) continue;
        if (!best || e.len > best.len || (e.len === best.len && e.t > best.t)) best = e;
      }
      const ev = { t, fast, x: b.x, y: b.y, c: b.c, bg: b.bg, size: b.size, area: b.area, owner: b.owner,
                   r: Math.max(2 * k, 0.35 * b.size), m0: this._meanNear(b.x, b.y, Math.max(2 * k, 0.35 * b.size)),
                   // Period: the chain's true mean, first switch-on to this one.
                   // A running average let one short gap drag a 5 Hz chain
                   // into a 6 Hz band.
                   t0: best ? best.t0 : t,
                   len: best ? best.len + 1 : 1, per: best ? (t - best.t0) / best.len : 0,
                   from: best };
      this.events.push(ev);
      const near = R && Math.hypot(b.x - R.x, b.y - R.y) < (120 + 900 * (t - R.t)) * k;
      // The chain's mean period must sit in the set rate's band (a little
      // slack for frame timing): 3 or 5 Hz flashing at a 4 Hz setting is not
      // the beacon, however regular it is.
      const perOk = ev.per >= pLo && ev.per <= pHi;
      // Every earlier link must have switched OFF again after switching on.
      // A beacon does, within half a cycle; a shelf, a poster, a patch of
      // wall that a moving hand or head uncovers "switches on" too -- and
      // then stays on. Chains of those were the false locks in lit rooms.
      // Four switch-ons on schedule (three periods) before believing a
      // chain: at 30 fps, two periods cannot tell 3.5 Hz from 3.7 Hz, and a
      // lit room has more for a moving hand or head to cover and uncover.
      const need = 4;
      // (The links that make up the required length; an older, partial
      // first flash at the head of a long chain is not held against it.)
      let offOk = true, depth = 0;
      for (let e = best; e && depth < need - 1; e = e.from, depth++) if (!e.off) { offOk = false; break; }
      if (offOk && perOk && (ev.len >= need || (ev.len >= 2 && near))) {
        const nf = Math.max(1, Math.round((t - best.t) * (this.fps || 30)));
        this._startLock({ x: b.x, y: b.y, vx: 0.5 * (b.x - best.x) / nf, vy: 0.5 * (b.y - best.y) / nf,
                          size: b.size, area: b.area, onLevel: b.c, bgLevel: b.bg,
                          freq: 1 / ev.per, score: 0.6, lastSeen: t }, t, R ? 'relight' : 'onsets');
        this.lock.tOn = t - 0.02;
        this.lock.seen = 1;
        b.lockTaken = true;
        this.events = [];
        return;
      }
    }
  };

  Tracker.prototype.process = function (rgba, w, h, t, laserOn) {
    this._alloc(w, h);
    const o = this.o;
    if (this.lastT !== null) {
      const dt = t - this.lastT;
      if (dt > 0) this.fps = this.fps ? this.fps + 0.1 * (1 / dt - this.fps) : 1 / dt;
    }
    this.lastT = t;
    this.frame++;

    this._luma(rgba);
    this._background();
    const blobs = this._blobs();
    this._updateTracks(blobs, t);

    if (this.lock) this._follow(blobs, t);
    if (!this.lock) this._onsets(blobs, t);
    if (!this.lock) {
      // Fresh identification: best passing track, nearest the last lock on a tie.
      let best = null, bs = -1;
      for (const tr of this.tracks) {
        if (!tr.passing) continue;
        if (this._isStatic(tr, t)) continue;
        // A beacon is a compact light. A window or a lit shirt that the
        // torch was swept across picks up the torch's blink for a moment,
        // but it is not what should be locked.
        if ((tr.area || 0) > 2500 * this._k() * this._k()) continue;
        let s = tr.score;
        if (this.lost) s += 0.3 * Math.exp(-Math.hypot(tr.x - this.lost.x, tr.y - this.lost.y) / (80 * this._k()));
        if (s > bs) { bs = s; best = tr; }
      }
      if (best) this._startLock(best, t, 'blink');
    }
    if (this.lost && t - this.lost.t > o.reacquireS) this.lost = null;

    let cand = null;
    if (!this.lock) for (const tr of this.tracks) if (tr.pass > 0 && (!cand || tr.pass > cand.pass)) cand = tr;
    if (this.lock) this.state = (t - this.lock.lastSeen > 0.45) ? "COASTING" : "LOCKED";
    else if (this.lost) this.state = "REACQUIRING";
    else this.state = cand ? "CONFIRMING" : "SEARCHING";
    this.target = this.lock;
    this.candidate = cand;

    const tmp = this.prevY; this.prevY = this.Y; this.Y = tmp; this.hasPrev = true;
    this.prevBlobs = blobs.map(b => ({ x: b.x, y: b.y, c: b.c }));
    void laserOn;
    return this;
  };

  /* Ego-motion: when the camera itself turns (MK2 -- it rides the gimbal),
     everything in the image slides by the same pixel amount. Shifting every
     remembered position by that amount keeps tracks, the lock and the
     steady-light memory aligned with the scene instead of reading the
     camera's own motion as the world moving. */
  Tracker.prototype.egoShift = function (dx, dy) {
    if (!dx && !dy) return;
    const mv = o => { if (o) { o.x += dx; o.y += dy; } };
    for (const tr of this.tracks) {
      tr.x += dx; tr.y += dy;
      if (tr.px !== undefined) { tr.px += dx; tr.py += dy; }
    }
    const L = this.lock;
    if (L) {
      L.x += dx; L.y += dy; L.mx += dx; L.my += dy;
      if (L.litX !== undefined) { L.litX += dx; L.litY += dy; }
      for (const q of L.trail) mv(q);
    }
    for (const q of this.statics) mv(q);
    for (const q of this.prevBlobs || []) mv(q);
    for (const q of this.events || []) mv(q);
    for (const q of this.hot || []) mv(q);
    mv(this.lost); mv(this.prov);
    // A big jump means the previous frame no longer lines up with this one,
    // so nothing can be called "new" by comparing the two. Small corrections
    // keep the comparison: a few pixels of misregistration is far less than
    // a beacon switching on.
    if (Math.hypot(dx, dy) > 3 * this._k()) this.hasPrev = false;
  };

  /* Where the locked beacon will be `lead` seconds from now. */
  Tracker.prototype.predict = function (lead) {
    const L = this.lock; if (!L) return null;
    const f = Math.min(lead, 0.3) * (this.fps || 30);
    return { x: L.x + L.vx * f, y: L.y + L.vy * f };
  };

  Tracker.prototype._centroid = function (cx, cy, r, cut) {
    const { w, h, Y } = this;
    const R = Math.round(r), xi = Math.round(cx), yi = Math.round(cy);
    let sx = 0, sy = 0, sw = 0;
    for (let y = Math.max(0, yi - R); y <= Math.min(h - 1, yi + R); y++) {
      const row = y * w;
      for (let x = Math.max(0, xi - R); x <= Math.min(w - 1, xi + R); x++) {
        const v = Y[row + x]; if (v < cut) continue;
        const wt = v - cut + 1; sx += x * wt; sy += y * wt; sw += wt;
      }
    }
    return sw > 4 ? { x: sx / sw, y: sy / sw } : null;
  };

  root.ZeroDriftTracker = Tracker;
  if (typeof module !== "undefined" && module.exports) module.exports = Tracker;
})(typeof window !== "undefined" ? window : globalThis);
