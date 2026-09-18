// Synthetic camera: a canvas-backed MediaStream with a moving 4 Hz beacon,
// a steady bright lamp, and textured background. Exposes window.__truth().
(() => {
  const W = 320, H = 240;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const cx = cv.getContext('2d');
  // static background texture (so the CFAR reference sees structure)
  const bg = document.createElement('canvas'); bg.width = W; bg.height = H;
  const bx = bg.getContext('2d');
  const img = bx.createImageData(W, H);
  let seed = 12345;
  const rnd = () => (seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff;
  for (let i = 0; i < W * H; i++) {
    const v = 38 + 14 * ((i % W) / W) + (rnd() - 0.5) * 14;
    img.data[i*4] = img.data[i*4+1] = img.data[i*4+2] = v; img.data[i*4+3] = 255;
  }
  bx.putImageData(img, 0, 0);

  let t0 = null;
  function path(t) {
    if (t < 4.5) return [80, 120];
    if (t < 5.7) { const k = (t - 4.5) / 1.2; return [80 + k*160, 120 - k*30]; }
    if (t < 9.0) return [240, 90];
    if (t < 10.0){ const k = (t - 9.0);      return [240 - k*120, 90 + k*80]; }
    return [120, 170];
  }
  window.__truth = () => {
    if (t0 === null) return null;
    const t = (performance.now() - t0) / 1000;
    return { t, p: path(t), on: (t * 4.0) % 1.0 < 0.5 };
  };
  function spot(u, v) {
    const g = cx.createRadialGradient(u, v, 0, u, v, 7);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.45, 'rgba(255,255,255,0.95)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    cx.fillStyle = g; cx.beginPath(); cx.arc(u, v, 7, 0, 7); cx.fill();
  }
  function draw() {
    cx.drawImage(bg, 0, 0);
    const s = window.__truth();
    if (s) { if (s.on) spot(s.p[0], s.p[1]); spot(270, 200); }
    requestAnimationFrame ? setTimeout(draw, 25) : null;
  }
  navigator.mediaDevices.getUserMedia = async () => {
    if (t0 === null) { t0 = performance.now(); draw(); }
    return cv.captureStream(30);
  };
})();
