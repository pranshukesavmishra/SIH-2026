// MK2, as built: a digital twin of the stepper terminal on the team's table.
//
// Modelled part by part in the build's own millimetres (the numbers of the
// picture guide and docs/wiring3d.html), Y up, the head looking along +Z:
//   acrylic base plate on four legs, the pan NEMA17 hanging under it on four
//   M3 screws; the 9 cm disc glued to the shaft with M-Seal, the diametric
//   magnet on the shaft tip, the AS5600 on its acrylic strip 2 mm above it;
//   three M3 x 40 stilts (three nuts each) carrying the L-bracket; the tilt
//   NEMA17 bolted to it on the LEFT; the small disc glued to that shaft and
//   the open head box screwed to it; the webcam inside, its clip flat on the
//   floor and tied, the KY-008 laser on foam tape on top of the camera.
//   On the table: breadboard with the Nano, two A4988s, the TCA9548A, the
//   100 uF capacitors, the 12 V input -- every jumper drawn -- the laptop
//   with its USB hub, the 12 V adapter. Cables fixed to moving parts bend
//   as the head turns.
//
// The beacon is a phone whose torch blinks at 4 Hz; the decoy is the steady
// red LED box on three 18650 cells. The rig runs the real sequence -- search,
// lock, follow, the torch covered (it holds, it does not jump to the decoy),
// relock -- and the laptop and the inset show what the webcam actually sees.
import * as THREE from 'three';

const BLINK_HZ = 4;
const CYCLE = 24;                                   // one full demo loop, s
const PIVOT_Y = 138;                                // tilt shaft height above the table, mm
const LASER = new THREE.Vector3(41, 14.8, 14.3);    // KY-008 aperture, from the tilt pivot
const LENS = new THREE.Vector3(41, -7, 26.2);       // webcam lens, from the tilt pivot
const PAN_LIM = THREE.MathUtils.degToRad(90), TILT_LIM = THREE.MathUtils.degToRad(18);   // firmware soft limits
const CAM_VFOV = 29, CAM_ASPECT = 16 / 9;           // Logitech 720p: about 48 x 29 degrees
const HUD_W = 640, HUD_H = 360;                     // the webcam picture, px
const PAGE_W = 1024, PAGE_H = 664;                  // the /live page on the laptop, px
const CAMX = 24, CAMY = 116;                        // where the webcam picture sits on that page
const CORNERS = [[1, 1], [1, -1], [-1, 1], [-1, -1]];
const STILTS = [[-22, -15], [-22, 15], [-38, 0]];

/* ------------------------------------------------------------------ */
/* small builders                                                      */
/* ------------------------------------------------------------------ */
function mesh(geo, mat, parent, x = 0, y = 0, z = 0, shadow = true) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(x, y, z);
  m.castShadow = shadow; m.receiveShadow = true;
  parent.add(m);
  return m;
}
const boxG = (w, h, d) => new THREE.BoxGeometry(w, h, d);
function cylG(r, h, axis = 'y', seg = 24, rTop = r) {
  const g = new THREE.CylinderGeometry(rTop, r, h, seg);
  if (axis === 'x') g.rotateZ(-Math.PI / 2);        // +Y -> +X
  if (axis === 'z') g.rotateX(Math.PI / 2);         // +Y -> +Z
  return g;
}
function roundRect(w, h, r) {
  const s = new THREE.Shape(), x = -w / 2, y = -h / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.absarc(x + w - r, y + r, r, -Math.PI / 2, 0, false);
  s.lineTo(x + w, y + h - r); s.absarc(x + w - r, y + h - r, r, 0, Math.PI / 2, false);
  s.lineTo(x + r, y + h); s.absarc(x + r, y + h - r, r, Math.PI / 2, Math.PI, false);
  s.lineTo(x, y + r); s.absarc(x + r, y + r, r, Math.PI, Math.PI * 1.5, false);
  return s;
}
/* ShapeGeometry UVs are raw shape coordinates; stretch them to 0..1. */
function fitUV(geo) {
  geo.computeBoundingBox();
  const b = geo.boundingBox, uv = geo.attributes.uv, p = geo.attributes.position;
  for (let i = 0; i < uv.count; i++) {
    uv.setXY(i, (p.getX(i) - b.min.x) / (b.max.x - b.min.x), (p.getY(i) - b.min.y) / (b.max.y - b.min.y));
  }
  uv.needsUpdate = true;
  return geo;
}
function chamferSquare(s, c) {
  const h = s / 2, sh = new THREE.Shape();
  sh.moveTo(-h + c, -h); sh.lineTo(h - c, -h); sh.lineTo(h, -h + c); sh.lineTo(h, h - c);
  sh.lineTo(h - c, h); sh.lineTo(-h + c, h); sh.lineTo(-h, h - c); sh.lineTo(-h, -h + c); sh.closePath();
  return sh;
}
/* An extruded shape standing along +Y, from y = 0 to y = len. */
function prismY(shape, len) {
  const g = new THREE.ExtrudeGeometry(shape, { depth: len, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);
  return g;
}
/* A putty blob turned about Y (or X): [radius, height] pairs. */
function lathe(pts, axis = 'y') {
  const g = new THREE.LatheGeometry(pts.map(([r, h]) => new THREE.Vector2(r, h)), 28);
  if (axis === 'x') g.rotateZ(-Math.PI / 2);
  return g;
}
let GLOW_TEX = null;
function glow(color, size, opacity = 1) {
  if (!GLOW_TEX) {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d'), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.22, 'rgba(255,255,255,0.6)');
    r.addColorStop(0.5, 'rgba(255,255,255,0.14)'); r.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = r; g.fillRect(0, 0, 64, 64);
    GLOW_TEX = new THREE.CanvasTexture(c);
  }
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: GLOW_TEX, color, transparent: true, opacity,
    depthWrite: false, blending: THREE.AdditiveBlending }));
  sp.scale.setScalar(size);
  return sp;
}
function rr(g, x, y, w, h, r) {
  g.beginPath();
  if (g.roundRect) { g.roundRect(x, y, w, h, r); return; }
  g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
}
function canvasTex(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return { c, g: c.getContext('2d'), t };
}

/* ------------------------------------------------------------------ */
/* materials and light                                                 */
/* ------------------------------------------------------------------ */
function materials() {
  const std = (color, metalness = 0, roughness = 0.6, extra = {}) =>
    new THREE.MeshStandardMaterial({ color, metalness, roughness, ...extra });
  return {
    acrylic: new THREE.MeshPhysicalMaterial({ color: 0xd8f3ff, metalness: 0, roughness: 0.05, transparent: true, opacity: 0.22,
      clearcoat: 1, clearcoatRoughness: 0.05, depthWrite: false, side: THREE.DoubleSide, envMapIntensity: 1.5 }),
    acrEdge: new THREE.LineBasicMaterial({ color: 0xa8e9ff, transparent: true, opacity: 0.55 }),
    wood: std(0xc39a6a, 0, 0.8),
    desk: std(0x0f1827, 0, 0.93),
    alu: std(0xc9cfd7, 1, 0.3),
    stator: std(0x17191d, 0.5, 0.42),
    label: std(0xcfd4da, 0.3, 0.45),
    steel: std(0xdfe4ea, 1, 0.2),
    bolt: std(0xa2abb5, 1, 0.3),
    zinc: std(0xbac2cb, 1, 0.32),
    bracket: std(0xa6afba, 1, 0.33),
    putty: std(0x8d9074, 0, 0.95),
    magN: std(0xd8413c, 0.3, 0.35), magS: std(0x2f6ee0, 0.3, 0.35),
    camBody: std(0x141619, 0.1, 0.55),
    camRing: std(0x3d434c, 0.85, 0.28),
    glass: std(0x0a1320, 0.9, 0.05),
    lensIn: std(0x2b4280, 1, 0.12),
    foam: std(0xc0392f, 0, 0.85),
    pcbBlack: std(0x151515, 0.1, 0.55),
    nano: std(0x1d58ab, 0.1, 0.45),
    a4988: std(0x1c7a4b, 0.1, 0.45),
    as5600: std(0x6a31d2, 0.1, 0.45),
    mux: std(0x2349a0, 0.1, 0.45),
    chip: std(0x0d0e10, 0.2, 0.4),
    header: std(0x121418, 0, 0.6),
    gold: std(0xd9b44d, 1, 0.25),
    brass: std(0xd3b060, 1, 0.26),
    white: std(0xf0eee7, 0, 0.55),
    black: std(0x141619, 0.1, 0.5),
    heat: std(0xb9c0c9, 1, 0.35),
    capBlue: std(0x243f86, 0.2, 0.4),
    ledRed: new THREE.MeshStandardMaterial({ color: 0xff2a1a, emissive: 0xff2a10, emissiveIntensity: 2.2, roughness: 0.3 }),
    ledGreen: new THREE.MeshStandardMaterial({ color: 0x2cff7a, emissive: 0x19e060, emissiveIntensity: 1.6, roughness: 0.3 }),
    laptop: std(0x2c3440, 0.85, 0.34),
    bezel: std(0x04060a, 0.2, 0.18),
    trackpad: std(0x3a4350, 0.75, 0.3),
    hub: std(0x8f969f, 0.9, 0.32),
    phoneFrame: std(0xaeb6c0, 1, 0.22),
    phoneBack: std(0x5d6674, 0.3, 0.16),
    lensRing: std(0x50565f, 0.9, 0.25),
    cell: std(0x8d5cd8, 0.15, 0.35),
    holder: std(0x15171a, 0, 0.62),
    switchRed: std(0xe2402e, 0, 0.45),
    resistor: std(0x5fc9c0, 0, 0.5),
    cardboard: std(0x8a6a48, 0, 0.9),
    glue: new THREE.MeshPhysicalMaterial({ color: 0xf4f7f8, roughness: 0.35, transparent: true, opacity: 0.5, depthWrite: false }),
    brick: std(0x17191c, 0.15, 0.5),
  };
}

/* A small studio for reflections: key softbox, cool rim, warm fill, dark
   floor. Gives the aluminium, steel and acrylic something to reflect. */
function studio(renderer) {
  const env = new THREE.Scene();
  env.background = new THREE.Color(0x070d18);
  const panel = (w, h, pos, color, k) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), side: THREE.DoubleSide }));
    m.position.set(...pos); m.lookAt(0, 0, 0); env.add(m);
  };
  panel(5, 2.6, [2.2, -3, 5.5], 0xffffff, 5);       // key, front-right, above (world is Z-up)
  panel(3.5, 5, [-5.5, 2, 2.5], 0x9fd9ff, 2.2);     // cool rim, left
  panel(4, 3, [4.5, 4, 2], 0xffe2c4, 1.5);          // warm fill, behind-right
  panel(10, 10, [0, 0, -3.5], 0x16213a, 1);         // floor bounce
  const pm = new THREE.PMREMGenerator(renderer);
  const tex = pm.fromScene(env, 0.035).texture;
  pm.dispose();
  return tex;
}

/* ------------------------------------------------------------------ */
/* parts                                                               */
/* ------------------------------------------------------------------ */
/* NEMA17, 42.3 mm square, 40 mm body. Front face at y = 0, shaft along +Y. */
function nema17(parent, M) {
  const g = new THREE.Group(); parent.add(g);
  const sq = chamferSquare(42.3, 4.6), core = chamferSquare(41.4, 4.2);
  mesh(prismY(sq, 8), M.alu, g, 0, -8, 0);                 // front end cap
  mesh(prismY(core, 24), M.stator, g, 0, -32, 0);          // laminated stator
  mesh(prismY(sq, 8), M.alu, g, 0, -40, 0);                // rear end cap
  mesh(cylG(11, 2, 'y', 40), M.alu, g, 0, 1, 0);           // pilot boss
  mesh(cylG(2.5, 24, 'y', 20), M.steel, g, 0, 12, 0);      // 5 mm shaft, 24 mm long
  for (const [a, b] of CORNERS) mesh(cylG(2.75, 3, 'y', 16), M.bolt, g, 15.5 * a, -41.5, 15.5 * b);
  const lab = mesh(new THREE.PlaneGeometry(22, 30), M.label, g, -20.8, -20, 0, false);   // rating label, -X face
  lab.rotation.y = -Math.PI / 2;
  return g;
}

function breadboardTexture() {
  const K = 10, W = 165 * K, H = 55 * K;                   // 10 px per mm
  const { c, g, t } = canvasTex(W, H);
  g.fillStyle = '#f3f2ed'; g.fillRect(0, 0, W, H);
  g.fillStyle = '#dcdbd4'; g.fillRect(0, 26 * K, W, 3 * K);          // centre channel
  const hole = (x, z) => { g.fillStyle = '#44423d'; g.fillRect(x * K - 5, z * K - 5, 10, 10); };
  for (let i = 0; i < 63; i++) {
    const x = 3.8 + i * 2.54;
    for (let r = 0; r < 5; r++) { hole(x, 27.5 - 3.81 - r * 2.54); hole(x, 27.5 + 3.81 + r * 2.54); }
  }
  for (let i = 0; i < 60; i++) {
    const x = 9 + i * 2.54 + Math.floor(i / 5) * 2.54;
    if (x > 158) break;
    for (const z of [3, 8, 47, 52]) hole(x, z);
  }
  g.fillStyle = '#d6352f'; g.fillRect(6 * K, 1.1 * K, 153 * K, 5); g.fillRect(6 * K, 45.1 * K, 153 * K, 5);
  g.fillStyle = '#2f5fd3'; g.fillRect(6 * K, 9.9 * K, 153 * K, 5); g.fillRect(6 * K, 53.9 * K, 153 * K, 5);
  g.fillStyle = '#9a9890'; g.font = `${2.2 * K}px Arial`;
  for (let i = 0; i < 63; i += 5) g.fillText(String(i + 1), (3.8 + i * 2.54) * K - 8, 13.2 * K);
  void c;
  t.anisotropy = 8;
  return t;
}

function keyboardTexture() {
  const { g, t } = canvasTex(1088, 448);
  g.fillStyle = '#161a20'; g.fillRect(0, 0, 1088, 448);
  const key = (x, y, w, h) => {
    g.fillStyle = '#07090c'; rr(g, x, y, w, h, 6); g.fill();
    g.strokeStyle = 'rgba(255,255,255,0.05)'; g.stroke();
  };
  for (let i = 0; i < 14; i++) key(8 + i * 76.8, 8, 70, 34);                       // function row
  const rows = [[14, 0], [14, 34], [13, 50], [12, 80]];
  rows.forEach(([n, off], r) => {
    const y = 50 + r * 76, w = (1072 - off - (n - 1) * 6) / n;
    for (let i = 0; i < n; i++) key(8 + off + i * (w + 6), y, w, 70);
  });
  const y = 50 + 4 * 76;
  [[8, 84], [98, 84], [188, 84], [278, 98], [382, 420], [808, 98], [912, 70]].forEach(([x, w]) => key(x, y, w, 70));
  key(988, y + 36, 44, 34); key(1036, y, 44, 34); key(1036, y + 36, 44, 34);
  return t;
}

/* A phone held up to the rig, torch side toward it. Local +Z is the back. */
function makePhone(M) {
  const g = new THREE.Group();
  const W = 71.5, H = 147, T = 7.8;
  const body = new THREE.ExtrudeGeometry(roundRect(W - 1.2, H - 1.2, 9.5),
    { depth: T - 1.2, bevelEnabled: true, bevelThickness: 0.6, bevelSize: 0.6, bevelSegments: 3, curveSegments: 12 });
  body.translate(0, 0, -(T - 1.2) / 2);
  mesh(body, M.phoneFrame, g);
  mesh(new THREE.ShapeGeometry(roundRect(W - 3, H - 3, 8.5), 12), M.phoneBack, g, 0, 0, T / 2 + 0.25, false);
  // camera module, top left seen from the back: two lenses, the torch, a mic
  const mod = new THREE.ExtrudeGeometry(roundRect(31, 31, 7), { depth: 1.4, bevelEnabled: false, curveSegments: 10 });
  mesh(mod, M.phoneBack, g, -17.5, 55, T / 2);
  for (const y of [63.5, 47]) {
    mesh(cylG(6.6, 1.6, 'z', 32), M.lensRing, g, -25, y, T / 2 + 2.1);
    mesh(cylG(4.4, 1.7, 'z', 32), M.glass, g, -25, y, T / 2 + 2.3);
    mesh(cylG(1.8, 0.3, 'z', 20), M.lensIn, g, -25, y, T / 2 + 3.2);
  }
  const torchMat = new THREE.MeshStandardMaterial({ color: 0xfff1d6, emissive: 0xfff1d6, emissiveIntensity: 0, roughness: 0.3 });
  mesh(cylG(2.6, 0.5, 'z', 24), torchMat, g, -9.5, 63.5, T / 2 + 1.65);
  mesh(cylG(0.9, 0.3, 'z', 12), M.chip, g, -9.5, 47, T / 2 + 1.5);
  // side keys
  mesh(boxG(1, 18, 3), M.phoneFrame, g, W / 2 + 0.3, 30, 0);
  for (const [y, h] of [[45, 12], [26, 12], [62, 6]]) mesh(boxG(1, h, 3), M.phoneFrame, g, -W / 2 - 0.3, y, 0);
  // the screen, facing away from the rig: a strobe app running
  const scr = canvasTex(256, 512);
  const screenMat = new THREE.MeshBasicMaterial({ map: scr.t, toneMapped: false });
  const s = mesh(fitUV(new THREE.ShapeGeometry(roundRect(W - 4, H - 4, 8), 12)), screenMat, g, 0, 0, -T / 2 - 0.25, false);
  s.rotation.y = Math.PI;
  // a cardboard card, slid over the torch to cover it
  const card = mesh(boxG(64, 52, 1.6), M.cardboard, g, 0, 52, T / 2 + 10);
  card.visible = false;
  return { g, torchMat, torch: new THREE.Vector3(-9.5, 63.5, T / 2 + 2.2), card, screen: scr, W, H, T };
}

function drawPhoneScreen(g, on) {
  g.fillStyle = '#05070b'; g.fillRect(0, 0, 256, 512);
  g.fillStyle = '#e9eef5'; g.font = '600 15px Arial'; g.fillText('4:53', 26, 30);
  g.fillRect(206, 20, 24, 11); g.fillStyle = '#05070b'; g.fillRect(208, 22, 16, 7);
  g.fillStyle = '#9aa7b8'; g.font = '700 13px Arial'; g.textAlign = 'center';
  g.fillText('STROBE', 128, 86);
  g.lineWidth = 10; g.strokeStyle = on ? '#fff3d6' : '#2b3340';
  g.beginPath(); g.arc(128, 220, 82, 0, Math.PI * 2); g.stroke();
  g.fillStyle = on ? '#fff3d6' : '#6b7686'; g.font = '700 46px Arial'; g.fillText('4 Hz', 128, 236);
  g.fillStyle = '#9aa7b8'; g.font = '600 13px Arial'; g.fillText('flashes per second', 128, 262);
  g.fillStyle = on ? '#3bd68c' : '#39424f'; rr(g, 88, 350, 80, 40, 20); g.fill();
  g.fillStyle = '#ffffff'; g.beginPath(); g.arc(on ? 148 : 108, 370, 16, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#9aa7b8'; g.font = '700 14px Arial'; g.fillText(on ? 'TORCH ON' : 'TORCH OFF', 128, 420);
  g.textAlign = 'left';
}

/* The decoy: clear box, three purple 18650s in a black holder, red toggle
   switch through the side, 1 kOhm, a red LED through the lid. Steady. */
function makeDecoy(M, acrylic) {
  const g = new THREE.Group();
  acrylic(boxG(100, 3, 70), g, 0, 1.5, 0);
  acrylic(boxG(100, 40, 3), g, 0, 23, 33.5); acrylic(boxG(100, 40, 3), g, 0, 23, -33.5);
  acrylic(boxG(3, 40, 64), g, 48.5, 23, 0); acrylic(boxG(3, 40, 64), g, -48.5, 23, 0);
  acrylic(boxG(100, 3, 70), g, 0, 44.5, 0);
  for (const [x, z] of [[48.5, 33.5], [-48.5, 33.5], [48.5, -33.5], [-48.5, -33.5]]) mesh(cylG(1.4, 40, 'y', 8), M.glue, g, x * 0.97, 23, z * 0.95, false);
  // holder and cells, in series (alternate ends)
  mesh(boxG(78, 2.5, 62), M.holder, g, -6, 4.25, 0);
  for (const x of [-44, 32]) mesh(boxG(2.5, 17, 62), M.holder, g, x, 11, 0);
  for (const z of [-30, 30]) mesh(boxG(78, 10, 2), M.holder, g, -6, 8.5, z);
  [-19.5, 0, 19.5].forEach((z, i) => {
    mesh(cylG(9.2, 65, 'x', 28), M.cell, g, -6, 14.7, z);
    mesh(cylG(3.4, 1.4, 'x', 16), M.steel, g, i % 2 ? -39.2 : 27.2, 14.7, z);
  });
  // red toggle switch through the right wall
  mesh(boxG(10, 8, 12.7), M.switchRed, g, 41, 26, 12);
  mesh(cylG(3, 7, 'x', 20), M.zinc, g, 53.5, 26, 12);
  mesh(cylG(4.4, 1.6, 'x', 6), M.zinc, g, 51, 26, 12);
  const lever = mesh(cylG(0.9, 10, 'x', 10), M.steel, g, 61, 27.5, 12); lever.rotation.z = 0.3;
  mesh(cylG(1.8, 6, 'x', 12, 1.5), M.switchRed, g, 67.5, 29.4, 12).rotation.z = 0.3;
  // 1 kOhm: body + bands (brown black red gold)
  mesh(cylG(1.2, 6.3, 'x', 14), M.resistor, g, 18, 33, 12);
  [[0x6b3a1a, -2], [0x111111, -0.8], [0xd63a2a, 0.4], [0xc9a227, 2.2]].forEach(([c, dx]) =>
    mesh(cylG(1.25, 0.6, 'x', 14), new THREE.MeshStandardMaterial({ color: c, roughness: 0.5 }), g, 18 + dx, 33, 12, false));
  // the LED through the lid, legs down to the wiring
  const led = new THREE.MeshStandardMaterial({ color: 0xff3a2a, emissive: 0xff2a14, emissiveIntensity: 2.4, roughness: 0.25,
    transparent: true, opacity: 0.95 });
  mesh(cylG(2.5, 5.5, 'y', 20), led, g, 0, 48.8, 0);
  mesh(new THREE.SphereGeometry(2.5, 20, 10, 0, Math.PI * 2, 0, Math.PI / 2), led, g, 0, 51.5, 0);
  mesh(cylG(2.9, 1, 'y', 20), led, g, 0, 46.4, 0);
  const wire = (pts, color, r = 0.5) => {
    const c = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)));
    mesh(new THREE.TubeGeometry(c, 30, r, 6, false), new THREE.MeshStandardMaterial({ color, roughness: 0.5 }), g, 0, 0, 0, false);
  };
  wire([[27.2, 14.7, -19.5], [34, 22, -6], [37, 26, 8], [36.5, 26, 12]], 0xd63a2a, 0.8);   // + to the switch
  wire([[36, 27, 15], [28, 31, 14], [21.2, 33, 12]], 0xd63a2a);                                // switch to the resistor
  wire([[14.8, 33, 12], [6, 36, 6], [0.7, 40, 1], [0.7, 45.8, 0]], 0xc9ccd1, 0.35);           // resistor to the long leg
  wire([[-39.2, 14.7, 19.5], [-30, 26, 12], [-10, 38, 3], [-0.7, 45.8, 0]], 0x1a1c20, 0.8);  // - to the short leg
  const halo = glow(0xff3322, 58, 0.9); halo.position.set(0, 51, 0); g.add(halo);
  const light = new THREE.PointLight(0xff3a22, 1.2e4, 520, 2); light.position.set(0, 58, 0); g.add(light);
  return { g, led: new THREE.Vector3(0, 51, 0) };
}

/* MacBook-sized laptop: local +Z is the user's side, the screen faces +Z. */
function makeLaptop(M, pageTex, camTex, hudTex, kbTex) {
  const g = new THREE.Group();
  const W = 304, D = 215, TH = 11.3;
  const base = new THREE.ExtrudeGeometry(roundRect(W, D, 10), { depth: TH, bevelEnabled: false, curveSegments: 8 });
  base.rotateX(-Math.PI / 2);
  mesh(base, M.laptop, g);
  const kb = mesh(new THREE.PlaneGeometry(272, 112), new THREE.MeshStandardMaterial({ map: kbTex, roughness: 0.7 }), g, 0, TH + 0.06, -42, false);
  kb.rotation.x = -Math.PI / 2;
  const tp = mesh(new THREE.PlaneGeometry(134, 84), M.trackpad, g, 0, TH + 0.06, 58, false);
  tp.rotation.x = -Math.PI / 2;
  const lid = new THREE.Group(); lid.position.set(0, TH, -D / 2 + 1.5); lid.rotation.x = -0.36; g.add(lid);
  const lidG = new THREE.ExtrudeGeometry(roundRect(W, 212, 10), { depth: 4.2, bevelEnabled: false, curveSegments: 8 });
  lidG.translate(0, 106, -4.2);
  mesh(lidG, M.laptop, lid);
  mesh(new THREE.ShapeGeometry(roundRect(W - 3, 209, 9), 8), M.bezel, lid, 0, 106, 0.05, false);
  const DW = 288, DH = 187, disp = new THREE.Group(); disp.position.set(0, 108.5, 0.12); lid.add(disp);
  const k = DW / PAGE_W, kh = DH / PAGE_H;
  const page = new THREE.Mesh(new THREE.PlaneGeometry(DW, DH), new THREE.MeshBasicMaterial({ map: pageTex, toneMapped: false }));
  disp.add(page);
  const cw = HUD_W * k, ch = HUD_H * kh;
  const cx = -DW / 2 + (CAMX + HUD_W / 2) * k, cy = DH / 2 - (CAMY + HUD_H / 2) * kh;
  const cam = new THREE.Mesh(new THREE.PlaneGeometry(cw, ch), new THREE.MeshBasicMaterial({ map: camTex, color: new THREE.Color(2.4, 2.4, 2.4) }));
  cam.position.set(cx, cy, 0.05); disp.add(cam);
  const hud = new THREE.Mesh(new THREE.PlaneGeometry(cw, ch), new THREE.MeshBasicMaterial({ map: hudTex, transparent: true, toneMapped: false }));
  hud.position.set(cx, cy, 0.1); disp.add(hud);
  const notch = mesh(new THREE.ShapeGeometry(roundRect(32, 7, 3)), M.bezel, disp, 0, DH / 2 - 1.5, 0.15, false);
  void notch;
  disp.traverse(o => o.layers.set(1));     // the webcam never films its own picture
  return g;
}

/* ------------------------------------------------------------------ */
/* the laptop's /live page and the webcam overlay                      */
/* ------------------------------------------------------------------ */
const STATE_COL = { LOCKED: '#3BD68C', COASTING: '#FFC24D', SEARCHING: '#8EA4C4' };
const sgn = v => (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(1);

function drawHud(g, st) {
  const W = HUD_W, H = HUD_H, cx = W / 2, cy = H / 2;
  g.clearRect(0, 0, W, H);
  g.lineCap = 'round';
  // boresight
  g.strokeStyle = 'rgba(234,244,253,0.6)'; g.lineWidth = 2.2; g.beginPath();
  for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { g.moveTo(cx + dx * 6, cy + dy * 6); g.lineTo(cx + dx * 20, cy + dy * 20); }
  g.stroke();
  // the decoy: seen, measured steady, ignored
  if (st.decoy) {
    const { x, y } = st.decoy;
    g.strokeStyle = 'rgba(142,164,196,0.8)'; g.lineWidth = 1.6; g.strokeRect(x - 16, y - 16, 32, 32);
    g.fillStyle = 'rgba(170,190,215,0.95)'; g.font = '700 16px ui-monospace, Menlo, monospace'; g.fillText('STEADY', x - 16, y - 22);
  }
  const col = STATE_COL[st.state];
  if (st.target && (st.state === 'LOCKED' || st.state === 'COASTING')) {
    const { x, y } = st.target, s = 26;
    g.setLineDash([3, 4]); g.strokeStyle = 'rgba(234,244,253,0.35)'; g.lineWidth = 1;
    g.beginPath(); g.moveTo(cx, cy); g.lineTo(x, y); g.stroke(); g.setLineDash([]);
    g.strokeStyle = col; g.lineWidth = 3; g.beginPath();
    for (const [a, b] of CORNERS) {
      g.moveTo(x + a * s, y + b * (s - 10)); g.lineTo(x + a * s, y + b * s); g.lineTo(x + a * (s - 10), y + b * s);
    }
    g.stroke();
    // motion arrow
    if (st.vel) { g.strokeStyle = col; g.lineWidth = 2.2; g.beginPath(); g.moveTo(x, y); g.lineTo(x + st.vel.x, y + st.vel.y); g.stroke(); }
    const l1 = `${st.state === 'LOCKED' ? 'LOCK' : 'COAST'}  ${st.hz.toFixed(1)} Hz`, l2 = `AZ ${sgn(st.az)}°  EL ${sgn(st.el)}°`;
    g.font = '700 18px ui-monospace, Menlo, monospace';
    const w1 = g.measureText(l1).width; g.font = '600 15px ui-monospace, Menlo, monospace';
    const tw = Math.max(w1, g.measureText(l2).width) + 22;
    let tx = x + s + 10; if (tx + tw > W - 6) tx = x - s - 10 - tw;
    const ty = Math.max(40, Math.min(H - 96, y - s - 8));
    g.fillStyle = 'rgba(4,9,21,0.82)'; g.fillRect(tx, ty, tw, 50); g.fillStyle = col; g.fillRect(tx, ty, 3, 50);
    g.font = '700 18px ui-monospace, Menlo, monospace'; g.fillText(l1, tx + 11, ty + 21);
    g.fillStyle = '#EAF4FD'; g.font = '600 15px ui-monospace, Menlo, monospace'; g.fillText(l2, tx + 11, ty + 41);
  } else if (st.target && st.checking) {
    const { x, y } = st.target;
    g.setLineDash([6, 5]); g.strokeStyle = '#4FC7EA'; g.lineWidth = 2.4; g.strokeRect(x - 28, y - 28, 56, 56); g.setLineDash([]);
    g.fillStyle = '#4FC7EA'; g.font = '700 17px ui-monospace, Menlo, monospace'; g.fillText('CHECKING', x - 28, y - 35);
  }
  // status strip
  const txt = `${st.state}   30 FPS   MK2 CAM`;
  g.font = '700 18px ui-monospace, Menlo, monospace';
  const w = g.measureText(txt).width + 40;
  g.fillStyle = 'rgba(4,9,21,0.78)'; g.fillRect(8, 8, w, 32);
  g.fillStyle = col; g.beginPath(); g.arc(23, 24, 5.5, 0, Math.PI * 2); g.fill(); g.fillText(txt, 36, 30.5);
  // what is happening, in words
  if (st.caption) {
    g.font = '600 18px ui-sans-serif, Arial, sans-serif';
    const cw = Math.min(W - 16, g.measureText(st.caption).width + 28);
    g.fillStyle = 'rgba(4,9,21,0.8)'; g.fillRect(cx - cw / 2, H - 42, cw, 32);
    g.fillStyle = '#dce7f3'; g.textAlign = 'center'; g.fillText(st.caption, cx, H - 20); g.textAlign = 'left';
  }
}

function drawPage(g, st) {
  const W = PAGE_W, H = PAGE_H, mono = 'ui-monospace, Menlo, monospace';
  g.fillStyle = '#060c17'; g.fillRect(0, 0, W, H);
  // nav
  g.fillStyle = '#0a1322'; g.fillRect(0, 0, W, 54);
  g.font = `700 20px ${mono}`; g.fillStyle = '#EAF4FD'; g.fillText('ZERO', 24, 34); g.fillStyle = '#4FC7EA'; g.fillText('DRIFT', 76, 34);
  g.font = `600 13px ${mono}`;
  for (const [t, x] of [['HOME', 560], ['CONSOLE', 650], ['LIVE DEMO', 768], ['ABOUT US', 898]]) {
    const on = t === 'LIVE DEMO';
    if (on) { g.strokeStyle = '#2a6f8a'; g.lineWidth = 1.5; g.strokeRect(x - 12, 13, 112, 28); }
    g.fillStyle = on ? '#7FE0F8' : '#9fb2c8'; g.fillText(t, x, 32);
  }
  // hint
  g.fillStyle = 'rgba(255,194,77,0.08)'; g.fillRect(24, 66, W - 48, 34);
  g.strokeStyle = 'rgba(255,194,77,0.35)'; g.lineWidth = 1; g.strokeRect(24.5, 66.5, W - 49, 33);
  g.fillStyle = '#e8d3a0'; g.font = '14px Arial'; g.fillText('Works best in a dark or dim room. Only the set BEACON RATE locks.', 44, 88);
  // webcam frame (the picture and its overlay are separate layers on top)
  g.fillStyle = '#02050b'; g.fillRect(CAMX, CAMY, HUD_W, HUD_H);
  g.strokeStyle = '#1b2a44'; g.lineWidth = 2; g.strokeRect(CAMX - 1, CAMY - 1, HUD_W + 2, HUD_H + 2);
  const card = (x, y, w, h, title) => {
    g.fillStyle = '#0a1426'; g.fillRect(x, y, w, h); g.strokeStyle = '#15263F'; g.lineWidth = 1.5; g.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
    g.fillStyle = '#6f86a6'; g.font = `700 12px ${mono}`; g.fillText(title, x + 14, y + 24);
  };
  const button = (x, y, w, t, kind) => {
    const c = { on: ['#0f2e3d', '#4FC7EA', '#7FE0F8'], ok: ['#0d2a1d', '#2f9e68', '#86EFAC'], dim: ['#0b1628', '#1e3350', '#6f86a6'] }[kind];
    g.fillStyle = c[0]; g.fillRect(x, y, w, 34); g.strokeStyle = c[1]; g.lineWidth = 1.5; g.strokeRect(x + 0.5, y + 0.5, w - 1, 33);
    g.fillStyle = c[2]; g.font = `700 13px ${mono}`; g.textAlign = 'center'; g.fillText(t, x + w / 2, y + 22); g.textAlign = 'left';
  };
  const rx = 684, rw = W - rx - 24;
  card(rx, CAMY, rw, 250, 'CONTROL');
  button(rx + 14, CAMY + 38, rw - 28, '■  STOP CAMERA', 'on');
  button(rx + 14, CAMY + 80, rw - 28, 'CONNECT RIG  ✓', 'ok');
  button(rx + 14, CAMY + 122, rw - 28, 'MK2 CAMERA (USB)  ✓', 'ok');
  button(rx + 14, CAMY + 164, rw - 28, 'TEST MOTION', 'dim');
  button(rx + 14, CAMY + 206, rw - 28, 'USE AS BEACON', 'dim');
  const sy = CAMY + 262;
  card(rx, sy, rw, H - sy - 24, 'STATUS');
  const col = STATE_COL[st.state];
  g.strokeStyle = col; g.lineWidth = 1.5; g.fillStyle = 'rgba(255,255,255,0.03)';
  g.fillRect(rx + 14, sy + 36, rw - 28, 32); g.strokeRect(rx + 14.5, sy + 36.5, rw - 29, 31);
  g.fillStyle = col; g.beginPath(); g.arc(rx + rw / 2 - 52, sy + 52, 4.5, 0, Math.PI * 2); g.fill();
  g.font = `700 15px ${mono}`; g.fillText(st.state, rx + rw / 2 - 40, sy + 57);
  const tracking = st.state === 'LOCKED' || st.state === 'COASTING';
  const rows = [
    ['BLINK RATE', tracking ? `${st.hz.toFixed(1)} Hz` : '—', tracking ? '#3BD68C' : '#EAF4FD'],
    ['OFFSET AZ / EL', tracking ? `${sgn(st.az)}° / ${sgn(st.el)}°` : '—'],
    ['TARGET SPEED', tracking ? `${st.speed.toFixed(1)} °/s` : '—'],
    ['FRAME RATE', '30'],
    ['PROCESSING', `${st.proc.toFixed(1)} ms`],
    ['RIG', 'connected · encoders=pan', '#86EFAC'],
  ];
  rows.forEach(([k, v, c], i) => {
    const y = sy + 96 + i * 28;
    g.fillStyle = '#6f86a6'; g.font = `600 12px ${mono}`; g.fillText(k, rx + 14, y);
    g.fillStyle = c || '#EAF4FD'; g.font = `700 13px ${mono}`; g.textAlign = 'right'; g.fillText(v, rx + rw - 14, y); g.textAlign = 'left';
    g.strokeStyle = '#13233a'; g.beginPath(); g.moveTo(rx + 14, y + 10); g.lineTo(rx + rw - 14, y + 10); g.stroke();
  });
  // gimbal card: angles and the last 12 s of pan
  const gy = CAMY + HUD_H + 16;
  card(CAMX, gy, HUD_W, H - gy - 24, 'GIMBAL · MK2 · STEPPERS');
  g.fillStyle = '#EAF4FD'; g.font = `700 22px ${mono}`;
  g.fillText(`PAN  ${sgn(st.pan)}°`, CAMX + 16, gy + 62); g.fillText(`TILT ${sgn(st.tilt)}°`, CAMX + 16, gy + 96);
  const px = CAMX + 230, pw = HUD_W - 250, py = gy + 34, ph = H - gy - 24 - 50;
  g.strokeStyle = '#13233a'; g.lineWidth = 1; g.strokeRect(px + 0.5, py + 0.5, pw, ph);
  g.beginPath(); g.moveTo(px, py + ph / 2); g.lineTo(px + pw, py + ph / 2); g.stroke();
  if (st.hist.length > 1) {
    const n = st.hist.length;
    g.strokeStyle = '#4FC7EA'; g.lineWidth = 2; g.beginPath();
    st.hist.forEach((v, i) => { const x = px + (i / (n - 1)) * pw, y = py + ph / 2 - (v / 35) * (ph / 2); i ? g.lineTo(x, y) : g.moveTo(x, y); });
    g.stroke();
  }
  g.fillStyle = '#6f86a6'; g.font = `600 11px ${mono}`; g.fillText('PAN, LAST 12 s', px + 8, py + 16);
}

/* ------------------------------------------------------------------ */
/* the twin                                                            */
/* ------------------------------------------------------------------ */
export function buildMk2Twin(v) {
  const { renderer, scene, camera } = v;
  const M = materials();
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;
  renderer.shadowMap.autoUpdate = false;
  scene.environment = studio(renderer);
  camera.layers.enable(1);
  if (v.grid) v.grid.layers.set(1);

  // Model space: millimetres, Y up, the head looking along +Z. The page's
  // world is Z up with the rig looking along -Y: one quarter turn about X.
  const model = new THREE.Group(); model.rotation.x = Math.PI / 2; scene.add(model);
  const acrylic = (geo, parent, x, y, z) => {
    const m = mesh(geo, M.acrylic, parent, x, y, z, false);
    m.renderOrder = 2;
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25), M.acrEdge));
    return m;
  };
  const wireMats = new Map();
  const wireMat = c => { if (!wireMats.has(c)) wireMats.set(c, new THREE.MeshStandardMaterial({ color: c, roughness: 0.42, metalness: 0.05 })); return wireMats.get(c); };
  const V = p => new THREE.Vector3(...p);
  function wire(pts, color, r = 0.6, parent = model) {
    const curve = new THREE.CatmullRomCurve3(pts.map(V), false, 'centripetal');
    const seg = Math.max(16, Math.round(curve.getLength() / 2.2));
    const m = mesh(new THREE.TubeGeometry(curve, seg, r, r > 1.2 ? 10 : 6, false), wireMat(color), parent, 0, 0, 0, r > 1.2);
    return { mesh: m, curve };
  }

  // desk mat
  const desk = new THREE.ShapeGeometry(roundRect(1000, 900, 24), 8); desk.rotateX(-Math.PI / 2);
  mesh(desk, M.desk, model, -10, 0.3, 80, false);

  /* ---------------- fixed: legs, base, pan motor, sensor arm ---------------- */
  for (const [a, b] of CORNERS) mesh(boxG(12, 60, 12), M.wood, model, 65 * a, 30, 65 * b);
  acrylic(boxG(150, 3, 150), model, 0, 61.5, 0);
  for (const [a, b] of CORNERS) mesh(cylG(2.8, 1.8, 'y', 16), M.bolt, model, 15.5 * a, 63.9, 15.5 * b);   // M3 x 12 into the motor
  nema17(model, M).position.set(0, 58, 0);                                   // hangs under the plate, shaft up
  mesh(boxG(15, 6, 5.5), M.white, model, 0, 30, 23.9);                       // its 6-pin connector, toward the breadboard
  mesh(cylG(1.5, 38, 'y', 12), M.steel, model, 50, 77, 0);                   // M3 rod for the sensor arm
  for (const y of [58.8, 64.2, 87.9, 93.3]) mesh(cylG(3.15, 2.4, 'y', 6), M.zinc, model, 50, y, 0);
  acrylic(boxG(60, 3, 15), model, 25, 90.6, 0);                              // the 1.5 x 6 cm strip
  mesh(boxG(23, 1.6, 23), M.as5600, model, 0, 88.3, 0);                     // AS5600 board, chip down
  mesh(boxG(4.4, 1, 5), M.chip, model, 0, 87, 0);
  for (let i = 0; i < 4; i++) mesh(cylG(0.8, 1.7, 'y', 10), M.gold, model, 10, 88.3, -3.8 + i * 2.54, false);

  /* ---------------- pan: disc, magnet, stilts, bracket, tilt motor ---------------- */
  const gPan = new THREE.Group(); model.add(gPan);
  acrylic(cylG(45, 3, 'y', 72), gPan, 0, 77.5, 0);                         // 9 cm disc, y 76..79
  mesh(lathe([[2.5, 0], [6, 0.8], [7.8, 3], [7.2, 5.6], [5, 7], [2.5, 7]]), M.putty, gPan, 0, 69, 0);   // M-Seal under
  mesh(lathe([[2.5, 0], [5, 0.5], [5.2, 1.8], [3.6, 2.8], [2.5, 3]]), M.putty, gPan, 0, 79, 0);         // and on top
  mesh(new THREE.CylinderGeometry(3, 3, 2.5, 20, 1, false, 0, Math.PI), M.magN, gPan, 0, 83.25, 0);     // diametric magnet
  mesh(new THREE.CylinderGeometry(3, 3, 2.5, 20, 1, false, Math.PI, Math.PI), M.magS, gPan, 0, 83.25, 0);
  for (const [x, z] of STILTS) {
    mesh(cylG(2.8, 2, 'y', 16), M.bolt, gPan, x, 75, z);                    // head under the disc
    mesh(cylG(1.5, 40, 'y', 12), M.steel, gPan, x, 96, z);                  // M3 x 40
    for (const y of [80.2, 108.8, 113.7]) mesh(cylG(3.15, 2.4, 'y', 6), M.zinc, gPan, x, y, z);   // nuts #1 #2 #3
  }
  mesh(boxG(52, 2.5, 50), M.bracket, gPan, -34, 111.25, 0);                // L-bracket foot
  mesh(boxG(2.5, 57, 50), M.bracket, gPan, -6.8, 138.5, 0);                // and its upright
  const tm = nema17(gPan, M); tm.position.set(-8.05, PIVOT_Y, 0); tm.rotation.z = -Math.PI / 2;   // tilt motor on the LEFT, shaft +X
  for (const [a, b] of CORNERS) mesh(cylG(2.8, 2, 'x', 16), M.bolt, gPan, -4.55, PIVOT_Y + 15.5 * a, 15.5 * b);   // M3 x 6, no nuts
  mesh(boxG(6, 15, 5.5), M.white, gPan, -37, PIVOT_Y, -23.9);              // its connector, on the back

  /* ---------------- tilt: small disc, head box, webcam, laser ---------------- */
  const gTilt = new THREE.Group(); gTilt.position.set(0, PIVOT_Y, 0); gPan.add(gTilt);
  acrylic(cylG(20, 3, 'x', 56), gTilt, 12.5, 0, 0);                        // 4 cm disc on the tilt shaft
  mesh(lathe([[2.5, 0], [5.5, 0.6], [7, 2.4], [6.5, 4], [4, 4.5], [2.5, 4.5]], 'x'), M.putty, gTilt, 6.5, 0, 0);
  for (const z of [-12, 12]) {                                              // two M3 through E and the disc
    mesh(cylG(2.8, 2, 'x', 16), M.bolt, gTilt, 18, 0, z);
    mesh(cylG(1.5, 11, 'x', 10), M.steel, gTilt, 13.5, 0, z);
    mesh(cylG(3.15, 2.4, 'x', 6), M.zinc, gTilt, 9.8, 0, z);
  }
  acrylic(boxG(87, 3, 50), gTilt, 57.5, -24.5, 0);                         // A floor
  acrylic(boxG(87, 3, 50), gTilt, 57.5, 24.5, 0);                          // B lid
  acrylic(boxG(3, 46, 50), gTilt, 15.5, 0, 0);                             // E, motor side
  acrylic(boxG(3, 46, 50), gTilt, 99.5, 0, 0);                             // F
  const camShape = new THREE.Shape();
  camShape.moveTo(-20.5, -15.2); camShape.lineTo(20.5, -15.2); camShape.absarc(20.5, 0, 15.2, -Math.PI / 2, Math.PI / 2, false);
  camShape.lineTo(-20.5, 15.2); camShape.absarc(-20.5, 0, 15.2, Math.PI / 2, Math.PI * 1.5, false);
  mesh(new THREE.ExtrudeGeometry(camShape, { depth: 27, bevelEnabled: true, bevelThickness: 1, bevelSize: 0.8, bevelSegments: 3, curveSegments: 28 }),
    M.camBody, gTilt, 57.5, -7, -3);                                         // webcam, face flush with the open front
  mesh(cylG(6.8, 1.2, 'z', 36), M.camRing, gTilt, 41, -7, 25.5);
  mesh(cylG(4.6, 1.2, 'z', 36), M.glass, gTilt, 41, -7, 25.9);
  mesh(cylG(2, 0.4, 'z', 24), M.lensIn, gTilt, 41, -7, 26.4);
  mesh(cylG(0.9, 0.4, 'z', 12), new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xbfe6ff, emissiveIntensity: 1.1 }), gTilt, 78, -7, 25.2, false);
  mesh(boxG(30, 3, 44), M.camBody, gTilt, 57.5, -21.5, -26);               // clip, lower jaw flat on the floor, out of the back
  mesh(boxG(30, 3, 40), M.camBody, gTilt, 57.5, -15, -24);
  mesh(cylG(3.5, 30, 'x', 20), M.camBody, gTilt, 57.5, -18, -5);
  const tie = new THREE.CatmullRomCurve3([[41.5, -26.9, -15], [73.5, -26.9, -15], [74.4, -23, -15], [73.5, -19.1, -15], [41.5, -19.1, -15], [40.6, -23, -15]].map(V), true);
  mesh(new THREE.TubeGeometry(tie, 48, 0.8, 6, true), M.black, gTilt);      // cable tie round clip + floor
  mesh(boxG(4, 4, 4.5), M.black, gTilt, 75.8, -23, -15);
  mesh(boxG(15, 1.2, 18), M.foam, gTilt, 41, 9.6, 2);                      // foam tape
  mesh(boxG(15.2, 1.6, 18.5), M.pcbBlack, gTilt, 41, 11, 2);               // KY-008
  mesh(cylG(3, 11, 'z', 24), M.brass, gTilt, 41, 14.8, 7.9);
  const apMat = new THREE.MeshStandardMaterial({ color: 0x551111, emissive: 0xff2a1a, emissiveIntensity: 0, roughness: 0.2 });
  mesh(cylG(1.7, 0.6, 'z', 16), apMat, gTilt, 41, 14.8, 13.7, false);
  for (const dx of [-2.54, 0, 2.54]) mesh(boxG(0.64, 0.64, 8), M.gold, gTilt, 41 + dx, 12.4, -9, false);   // S, middle (empty), -
  for (const dx of [-2.54, 2.54]) mesh(boxG(2.54, 2.54, 14), M.black, gTilt, 41 + dx, 12.4, -19);          // jumper housings on S and -
  const headCam = new THREE.PerspectiveCamera(CAM_VFOV, CAM_ASPECT, 5, 6000);
  headCam.position.copy(LENS); headCam.rotation.y = Math.PI; gTilt.add(headCam);
  // the beam (for us; the webcam does not see it) and its dot (the webcam does)
  const beamG = new THREE.CylinderGeometry(0.45, 0.45, 1, 8, 1, true); beamG.rotateX(Math.PI / 2); beamG.translate(0, 0, 0.5);
  const beam = new THREE.Group(); beam.position.copy(LASER); gTilt.add(beam);
  beam.add(new THREE.Mesh(beamG, new THREE.MeshBasicMaterial({ color: 0xff3a30, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false })));
  const halo = new THREE.Mesh(beamG, new THREE.MeshBasicMaterial({ color: 0xff2020, transparent: true, opacity: 0.12, blending: THREE.AdditiveBlending, depthWrite: false }));
  halo.scale.set(4, 4, 1); beam.add(halo);
  beam.traverse(o => o.layers.set(1));
  const apGlow = glow(0xff3322, 10, 0.9); apGlow.position.set(41, 14.8, 14.8); gTilt.add(apGlow);
  const dot = glow(0xff3a2a, 16); const dotCore = glow(0xffe4dc, 5); model.add(dot, dotCore);
  // For the page viewer only (layer 1, the webcam never sees them): a wide
  // halo and a pulsing ring, so the spot where the laser lands on the phone
  // reads from across the bench.
  const dotHalo = glow(0xff2a18, 70, 1); dotHalo.layers.set(1); model.add(dotHalo);
  const dotRing = new THREE.Mesh(new THREE.RingGeometry(12, 16, 48),
    new THREE.MeshBasicMaterial({ color: 0xff4a3a, transparent: true, opacity: 0.9, side: THREE.DoubleSide, depthWrite: false, blending: THREE.AdditiveBlending }));
  dotRing.layers.set(1); model.add(dotRing);

  /* ---------------- the breadboard and everything on it ---------------- */
  const bbTop = new THREE.MeshStandardMaterial({ map: breadboardTexture(), roughness: 0.75 });
  const bb = new THREE.Mesh(boxG(165, 8.5, 55), [M.white, M.white, bbTop, M.white, M.white, M.white]);
  bb.position.set(-2.5, 4.25, 147.5); bb.receiveShadow = true; bb.castShadow = true; model.add(bb);
  // Nano (USB-C clone): pins in the board, USB at the left end
  for (const z of [141.4, 156.6]) mesh(boxG(38.1, 2.5, 2.54), M.header, model, -53.4, 9.75, z);
  mesh(boxG(43.2, 1.6, 18.5), M.nano, model, -53.4, 11.8, 149);
  mesh(boxG(7, 1, 7), M.chip, model, -47, 13.1, 149).rotation.y = Math.PI / 4;
  mesh(boxG(4, 1, 7), M.chip, model, -63, 13.1, 149);
  mesh(boxG(3.5, 1.4, 6), M.white, model, -56, 13.3, 149);
  mesh(boxG(1.6, 0.6, 0.9), M.ledRed, model, -68, 12.9, 143.5, false);
  mesh(boxG(7.5, 3.2, 9), M.alu, model, -74.2, 14.2, 149);
  mesh(boxG(10, 6, 11), M.white, model, -84.5, 14.2, 149);                 // the USB-C plug
  // A4988 x 2 with heatsinks, straddling the channel
  const DRV = { pan: -12, tilt: 20 };
  for (const x0 of Object.values(DRV)) {
    const cx = x0 + 10;
    for (const z of [141.15, 153.85]) mesh(boxG(20.3, 2.5, 2.54), M.header, model, cx, 9.75, z);
    mesh(boxG(20.3, 1.6, 15.2), M.a4988, model, cx, 11.8, 147.5);
    mesh(boxG(9, 1.2, 9), M.heat, model, cx + 1, 13.2, 147.5);
    for (let i = 0; i < 6; i++) mesh(boxG(9, 5, 0.8), M.heat, model, cx + 1, 16.3, 143.9 + i * 1.44);
    mesh(cylG(1.7, 1.3, 'y', 14), M.alu, model, x0 + 3.2, 13.2, 151);       // Vref trimmer, 0.55 V
    // 100 uF across VMOT / GND, right by the driver, standing over the back rails
    mesh(cylG(3.15, 11, 'y', 20), M.capBlue, model, x0 + 23, 16, 125.5);
    mesh(cylG(3.15, 0.4, 'y', 20), M.alu, model, x0 + 23, 21.7, 125.5);
    mesh(boxG(1.2, 11, 0.2), M.white, model, x0 + 20.2, 16, 125.5, false);  // the - stripe
  }
  // TCA9548A
  for (const z of [138.2, 156.8]) mesh(boxG(20.3, 2.5, 2.54), M.header, model, 55.8, 9.75, z);
  mesh(boxG(30, 1.6, 21), M.mux, model, 61, 11.8, 147.5);
  mesh(boxG(6.5, 1, 4.4), M.chip, model, 61, 13.1, 147.5);
  // 12 V in: barrel jack, plug, switch
  mesh(boxG(9, 11, 14), M.black, model, 106, 5.5, 116);
  mesh(cylG(4.2, 16, 'z', 18), M.black, model, 106, 5.5, 101);
  mesh(boxG(8, 6, 8), M.black, model, 92, 3, 121); mesh(boxG(2.4, 3, 2.4), M.white, model, 92, 7.3, 121);
  // the 12 V adapter behind, its mains lead off to the wall
  mesh(boxG(50, 33, 95), M.brick, model, 175, 16.5, -160);
  mesh(cylG(1.1, 0.5, 'y', 10), M.ledGreen, model, 175, 33.2, -126, false);

  /* ---------------- laptop and hub, behind the rig, facing the operator ---------------- */
  const hud = canvasTex(HUD_W, HUD_H), page = canvasTex(PAGE_W, PAGE_H);
  const camRT = new THREE.WebGLRenderTarget(HUD_W, HUD_H, { samples: 4 });
  const laptop = makeLaptop(M, page.t, camRT.texture, hud.t, keyboardTexture());
  laptop.position.set(-270, 0, -420); laptop.rotation.y = Math.PI - 0.3; model.add(laptop);
  // USB hub beside the laptop's left side, its tail in the laptop's port
  const hubL = new THREE.Vector3(-186, 0, -16);
  mesh(boxG(30, 11, 112), M.hub, laptop, hubL.x, 5.5, hubL.z);
  mesh(boxG(26, 0.4, 100), new THREE.MeshStandardMaterial({ color: 0x1b2330, roughness: 0.5 }), laptop, hubL.x, 11.1, hubL.z, false);
  const toModel = p => p.clone().applyMatrix4(laptop.matrix);
  laptop.updateMatrix();
  wire([[-186, 5.5, -72], [-182, 5, -86], [-165, 5.2, -92], [-154, 5.5, -80]].map(p => toModel(V(p)).toArray()), 0x6c737c, 1.8);
  const port = z => toModel(V([hubL.x - 15 - 21, 5.5, z]));
  for (const z of [-40, -10]) {                                               // USB-A plugs in the hub's outer side
    const plug = mesh(boxG(22, 8, 13), M.black, laptop, hubL.x - 15 - 10, 5.5, z);
    void plug;
  }
  const portCam = port(-40), portNano = port(-10);

  /* ---------------- the breadboard wiring (static) ---------------- */
  const Y = 8.8;
  const RAIL = { v12: 123, g12: 128, v5: 167, g5: 172 };
  const rail = (n, x) => [x, Y, RAIL[n]];
  const NANO = {};
  ['D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'GND', 'RST', 'RX0', 'TX1'].forEach((n, i) => { NANO[n] = [-71.2 + i * 2.54, Y, 159.2]; });
  ['D13', '3V3', 'REF', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', '5V', 'RSTa', 'GNDa', 'VIN'].forEach((n, i) => { NANO[n] = [-71.2 + i * 2.54, Y, 138.8]; });
  const drv = x0 => ({
    EN: [x0 + 1.11, Y, 156.4], MS1: [x0 + 3.65, Y, 156.4], MS2: [x0 + 6.19, Y, 156.4], MS3: [x0 + 8.73, Y, 156.4],
    RST: [x0 + 11.27, Y, 156.4], SLP: [x0 + 13.81, Y, 156.4], STEP: [x0 + 16.35, Y, 156.4], DIR: [x0 + 18.89, Y, 156.4],
    VMOT: [x0 + 18.89, Y, 138.6], GNDm: [x0 + 16.35, Y, 138.6], B2: [x0 + 13.81, Y, 138.6], A2: [x0 + 11.27, Y, 138.6],
    A1: [x0 + 8.73, Y, 138.6], B1: [x0 + 6.19, Y, 138.6], VDD: [x0 + 3.65, Y, 138.6], GNDl: [x0 + 1.11, Y, 138.6] });
  const PP = drv(DRV.pan), TP = drv(DRV.tilt);
  const MUX = { vin: [49.5, Y, 159.2], gnd: [52, Y, 159.2], sda: [54.6, Y, 159.2], scl: [57.1, Y, 159.2], a0: [59.7, Y, 159.2],
    sd0: [54.6, Y, 135.8], sc0: [57.1, Y, 135.8] };
  const COL = { v12: 0xe0443e, v5: 0xf08c2a, gnd: 0x2a2d33, step: 0x9b6cff, dir: 0xff6fb5, sda: 0x3b82f6, scl: 0xe8c23a, las: 0x2dd4bf,
    mA: 0x1e2024, mB: 0x2faa5a, mC: 0xe0443e, mD: 0x3b82f6 };
  const sleeves = [];
  const sleeve = p => sleeves.push([p[0], p[1] + 2.4, p[2]]);
  // a breadboard jumper: up out of the hole, over, down into the other
  function J(a, b, h, color) {
    const m = [(a[0] + b[0]) / 2, Math.max(a[1], b[1]) + h, (a[2] + b[2]) / 2];
    const up = p => [p[0] + (m[0] - p[0]) * 0.1, p[1] + Math.min(h * 0.6, 6 + h * 0.3), p[2] + (m[2] - p[2]) * 0.1];
    wire([[a[0], a[1] + 4, a[2]], up(a), m, up(b), [b[0], b[1] + 4, b[2]]], color, 0.55);
    sleeve(a); sleeve(b);
  }
  J(NANO['5V'], rail('v5', NANO['5V'][0] + 2.54), 14, COL.v5);                     // 5V (A side) over the Nano to the front + rail
  J(NANO.GND, rail('g5', NANO.GND[0] - 2.54), 6, COL.gnd);                          // GND (D side) to the front - rail
  J(rail('g12', 77), rail('g5', 77), 22, COL.gnd);                          // one jumper joins the two GND rails
  for (const P of [PP, TP]) {
    J(P.EN, rail('g5', P.EN[0]), 6, COL.gnd);
    ['MS1', 'MS2', 'MS3'].forEach(k => J(P[k], rail('v5', P[k][0]), 5, COL.v5));   // 1/16 step
    J(P.RST, P.SLP, 3, COL.step);
    J(P.VDD, rail('v5', P.VDD[0] - 1.27), 24, COL.v5); J(P.GNDl, rail('g5', P.GNDl[0] - 1.27), 27, COL.gnd);
    J(P.VMOT, rail('v12', P.VMOT[0]), 6, COL.v12); J(P.GNDm, rail('g12', P.GNDm[0]), 5, COL.gnd);
  }
  J(NANO.D2, PP.STEP, 14, COL.step); J(NANO.D3, PP.DIR, 17, COL.dir);        // pan STEP / DIR
  J(NANO.D4, TP.STEP, 20, COL.step); J(NANO.D5, TP.DIR, 23, COL.dir);        // tilt STEP / DIR
  J(NANO.A4, MUX.sda, 32, COL.sda); J(NANO.A5, MUX.scl, 36, COL.scl);        // I2C to the multiplexer
  J(MUX.vin, rail('v5', 49.5), 6, COL.v5); J(MUX.gnd, rail('g5', 52), 7, COL.gnd); J(MUX.a0, rail('g5', 59.7), 5, COL.gnd);
  for (const x0 of Object.values(DRV)) {                                     // capacitor legs into the back rails
    wire([[x0 + 21.8, 10.6, 125.5], [x0 + 21.8, 9.6, 123.6], rail('v12', x0 + 21.8)], 0xb8bec6, 0.3);
    wire([[x0 + 24.2, 10.6, 125.5], [x0 + 24.2, 9.6, 127.4], rail('g12', x0 + 24.2)], 0xb8bec6, 0.3);
  }
  // pan motor: 4 wires from its connector straight forward to the pan driver
  [['B2', COL.mA], ['A2', COL.mB], ['A1', COL.mC], ['B1', COL.mD]].forEach(([k, c], i) => {
    const o = (i - 1.5) * 1.8, e = PP[k];
    wire([[o, 30, 26.7], [o, 27, 36], [o * 1.4, 10, 54], [o * 2, 1.3, 80], [e[0] - 1.5, 1.6, 106], [e[0] - 0.5, 13, 117], [e[0], 17, 127], [e[0], 12, e[2]], e], c, 0.7);
    sleeve(e);
  });
  // AS5600: 4 wires along the strip, down the rod, off the front of the plate, to the mux and the rails
  [[COL.v5, rail('v5', 66)], [COL.gnd, rail('g5', 69)], [COL.sda, MUX.sd0], [COL.scl, MUX.sc0]].forEach(([c, e], i) => {
    const o = (i - 1.5) * 2.54;
    wire([[10.6, 88.3, o], [22, 87.3, o * 0.9], [44, 87.3, o * 0.7], [48.3, 83, 2.4 + o * 0.35], [48.6, 70, 2.6 + o * 0.3],
      [50, 64.6, 7 + o], [58, 63.9, 30 + o], [66, 63.9, 60 + o], [70, 62.5, 76 + o * 0.6], [72, 42, 86 + o * 0.5], [73, 1.3, 101 + o],
      [e[0] + 1.5, 1.6, 108], [e[0] + 1, 14, 117], [e[0], 18, Math.min(e[2] - 10, 128)], [e[0], 12, e[2]], e], c, 0.55);
    sleeve(e);
  });
  // 12 V: adapter -> plug -> jack -> switch -> + rail; jack - -> GND rail
  wire([[175, 12, -112], [168, 1.6, -80], [150, 1.6, -10], [134, 1.6, 50], [114, 2.4, 82], [106, 5.5, 93]], 0x15171a, 1.6);
  wire([[175, 16.5, -207.5], [180, 1.8, -236], [240, 1.8, -320], [340, 1.8, -400], [440, 1.8, -440]], 0x15171a, 2.6);
  wire([[101.5, 6, 121], [97, 9.5, 122], [94, 6.5, 121]], COL.v12, 0.6);
  wire([[90, 6.5, 121], [85, 12, 122], [78.5, 12, 123], rail('v12', 78.5)], COL.v12, 0.6); sleeve(rail('v12', 78.5));
  wire([[103, 6, 122.5], [95, 13, 127], [80.5, 13, 128], rail('g12', 80.5)], COL.gnd, 0.6); sleeve(rail('g12', 80.5));
  // Nano USB-C -> round the rig's left -> the hub
  const usbNano = wire([[-89.5, 14.2, 149], [-104, 4, 150], [-132, 2.2, 122], [-148, 2.2, 40], [-140, 2.2, -40], [-118, 2.2, -92],
    [portNano.x + 8, 3.5, portNano.z + 18], portNano.toArray()], 0xe8e6e0, 1.9);

  /* ---------------- cables on moving parts (rebuilt as the head turns) ---------------- */
  const FIX = 0, PAN = 1, TILT = 2;
  const dyn = [];
  function dynWire(pts, color, r) {
    const m = mesh(new THREE.BufferGeometry(), wireMat(color), model, 0, 0, 0, r > 1.2);
    const w = { pts, r, mesh: m, curve: null, seg: 60 };
    dyn.push(w); return w;
  }
  const loop = (cx, cz, r, y, n = 9) => Array.from({ length: n }, (_, i) => [FIX, cx + r * Math.cos(Math.PI * 0.6 + i / (n - 1) * Math.PI * 1.8), y + i * 0.35, cz + r * Math.sin(Math.PI * 0.6 + i / (n - 1) * Math.PI * 1.8)]);
  // tilt motor: from its connector down the back stilt, over the disc edge, a service loop on
  // the plate (the top turns), off the back-left corner, round to the tilt driver
  [['B2', COL.mA], ['A2', COL.mB], ['A1', COL.mC], ['B1', COL.mD]].forEach(([k, c], i) => {
    const o = (i - 1.5) * 2.1, e = TP[k];
    dynWire([[PAN, -37, PIVOT_Y + o, -26.9], [PAN, -38, 128 + o * 0.6, -33], [PAN, -30, 112, -30 + o * 0.4], [PAN, -23, 100, -19.5 + o * 0.3],
      [PAN, -24, 88, -20 + o * 0.3], [PAN, -30, 82, -34.5 + o * 0.3], ...loop(-47, -47, 14, 64.3 + i * 0.1), [FIX, -64, 64.2, -62 + o * 0.3],
      [FIX, -76, 58, -71], [FIX, -84, 30, -74 + o], [FIX, -94, 1.3, -58 + o], [FIX, -106 + o, 1.3, 20], [FIX, -97 + o, 1.3, 104],
      [FIX, e[0] - 2, 1.6, 108], [FIX, e[0] - 1, 13, 117], [FIX, e[0], 17, 127], [FIX, e[0], 12, e[2]], [FIX, ...e]], c, 0.7);
    sleeve(e);
  });
  mesh(new THREE.TorusGeometry(4.2, 0.8, 8, 20), M.black, gPan, -23, 94, -17.5).rotation.x = Math.PI / 2;   // tie to the stilt
  // webcam USB: out of the camera's back, over the floor's back edge, hanging, down behind, to the hub
  const usbCam = dynWire([[TILT, 80, -12, -4.6], [TILT, 81, -17, -16], [TILT, 82, -20, -30], [TILT, 84, -32, -46], [PAN, 88, 92, -66],
    [FIX, 72, 48, -92], [FIX, 40, 2.2, -112], [FIX, -10, 2.2, -126], [FIX, portCam.x + 30, 2.2, portCam.z + 10], [FIX, portCam.x + 10, 4, portCam.z + 3],
    [FIX, ...portCam.toArray()]], 0x1a1c20, 1.9);
  // laser S and -: bundled with the USB, then round the left of the rig to D7 and the - rail
  [[-2.54, COL.las, NANO.D7], [2.54, COL.gnd, rail('g5', -66)]].forEach(([dx, c, e]) => {
    dynWire([[TILT, 41 + dx, 12.4, -26], [TILT, 44 + dx, 12, -34], [TILT, 62 + dx, 2, -42], [TILT, 79 + dx * 0.5, -24, -47], [PAN, 86 + dx * 0.4, 92, -64],
      [FIX, 70 + dx * 0.4, 48, -90], [FIX, 38, 3.4, -109 + dx], [FIX, -40, 3.4, -117 + dx], [FIX, -120 + dx, 3.4, -78], [FIX, -126 + dx, 3.4, 40],
      [FIX, -104, 3.4, 176 + dx], [FIX, e[0] - 4, 15, e[2] + 8], [FIX, e[0], 12, e[2]], [FIX, ...e]], c, 0.6);
    sleeve(e);
  });
  mesh(new THREE.TorusGeometry(4.5, 0.8, 8, 20), M.black, gPan, 87, 92, -65).rotation.x = Math.PI / 2;      // tie on the bundle

  const sleeveMesh = new THREE.InstancedMesh(boxG(2.2, 5, 2.2), M.black, sleeves.length);
  sleeves.forEach((p, i) => sleeveMesh.setMatrixAt(i, new THREE.Matrix4().makeTranslation(...p)));
  sleeveMesh.receiveShadow = true; model.add(sleeveMesh);
  const tiltM = new THREE.Matrix4();
  let builtPan = 1e9, builtTilt = 1e9;
  function rebuild(force) {
    gPan.updateMatrix(); gTilt.updateMatrix();
    tiltM.multiplyMatrices(gPan.matrix, gTilt.matrix);
    if (!force && Math.abs(gPan.rotation.y - builtPan) < 3e-4 && Math.abs(gTilt.rotation.x - builtTilt) < 3e-4) return;
    builtPan = gPan.rotation.y; builtTilt = gTilt.rotation.x;
    for (const w of dyn) {
      const pts = w.pts.map(([f, x, y, z]) => {
        const p = new THREE.Vector3(x, y, z);
        if (f === PAN) p.applyMatrix4(gPan.matrix); else if (f === TILT) p.applyMatrix4(tiltM);
        return p;
      });
      w.curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
      const g = new THREE.TubeGeometry(w.curve, w.seg, w.r, w.r > 1.2 ? 10 : 6, false);
      w.mesh.geometry.dispose(); w.mesh.geometry = g;
    }
  }
  rebuild(true);

  // data on the USB cables: frames to the laptop, steps back to the Nano
  const pulses = [];
  const pulse = (color, n, cable, speed, reverse) => {
    for (let i = 0; i < n; i++) {
      const s = new THREE.Mesh(new THREE.SphereGeometry(2.4, 10, 8), new THREE.MeshBasicMaterial({ color, toneMapped: false }));
      s.layers.set(1); model.add(s); pulses.push({ s, cable, off: i / n, speed, reverse });
    }
  };
  pulse(0xffffff, 6, usbCam, 0.55, false);
  pulse(0x4FC7EA, 4, usbNano, 0.7, true);

  /* ---------------- the targets ---------------- */
  const phone = makePhone(M); model.add(phone.g);
  const phoneLight = new THREE.PointLight(0xfff1dc, 0, 900, 2); phone.g.add(phoneLight); phoneLight.position.copy(phone.torch).add(V([0, 0, 6]));
  const torchGlow = glow(0xfff4e2, 70); torchGlow.position.copy(phone.torch).add(V([0, 0, 1.5])); phone.g.add(torchGlow);
  const torchCore = glow(0xffffff, 16); torchCore.position.copy(torchGlow.position); phone.g.add(torchCore);
  let screenOn = null;
  const decoy = makeDecoy(M, acrylic);
  decoy.g.position.set(-45, 0, 480); decoy.g.rotation.y = -0.35; model.add(decoy.g);
  decoy.g.updateMatrix();
  const decoyLed = decoy.led.clone().applyMatrix4(decoy.g.matrix);

  /* ---------------- webcam inset on the card (bottom left) ---------------- */
  const pipScene = new THREE.Scene(), pipCam = new THREE.OrthographicCamera(0, 1, 1, 0, -10, 10);
  const quad = new THREE.PlaneGeometry(1, 1);
  const pipFrame = new THREE.Mesh(quad, new THREE.MeshBasicMaterial({ color: 0x4FC7EA, transparent: true, opacity: 0.6, toneMapped: false }));
  const pipView = new THREE.Mesh(quad, new THREE.MeshBasicMaterial({ map: camRT.texture, color: new THREE.Color(2.4, 2.4, 2.4) }));   // webcam auto-exposure
  const pipHud = new THREE.Mesh(quad, new THREE.MeshBasicMaterial({ map: hud.t, transparent: true, toneMapped: false }));
  pipFrame.position.z = -1; pipHud.position.z = 1;
  pipScene.add(pipFrame, pipView, pipHud);

  /* ---------------- motion ---------------- */
  const follower = (wn, maxV, maxA) => {
    const s = { x: 0, v: 0 };
    s.step = (target, dt) => {
      const a = THREE.MathUtils.clamp(wn * wn * (target - s.x) - 2 * wn * s.v, -maxA, maxA);
      s.v = THREE.MathUtils.clamp(s.v + a * dt, -maxV, maxV); s.x += s.v * dt;
      return s.x;
    };
    return s;
  };
  const panF = follower(12, 2.6, 22), tiltF = follower(12, 2.2, 22);
  // Aim the laser through a point (model frame): the laser sits 41 mm right of the pan
  // axis and 14.8 mm above the tilt axis, so both angles are solved, not guessed.
  function solveAim(T) {
    const zp = Math.sqrt(Math.max(1, T.x * T.x + T.z * T.z - LASER.x * LASER.x));
    const pan = Math.atan2(T.x, T.z) - Math.atan2(LASER.x, zp);
    const Yr = T.y - PIVOT_Y, R = Math.hypot(Yr, zp);
    const tilt = Math.atan2(zp, Yr) - Math.acos(Math.min(1, LASER.y / R));
    return { pan: THREE.MathUtils.clamp(pan, -PAN_LIM, PAN_LIM), tilt: THREE.MathUtils.clamp(tilt, -TILT_LIM, TILT_LIM) };
  }
  const W2 = 2 * Math.PI / CYCLE;
  const phonePath = t => V([
    25 + 125 * Math.sin(2 * W2 * t + 1.3) + 35 * Math.sin(3 * W2 * t + 0.4),
    150 + 40 * Math.sin(3 * W2 * t + 1.1) + 12 * Math.sin(5 * W2 * t + 0.3),
    375 + 30 * Math.sin(2 * W2 * t + 2.0)]);
  function phaseAt(tc) {
    if (tc < 0.9) return ['SEARCHING', 'torch on · checking its blink rate…'];
    if (tc < 13) return ['LOCKED', 'locked on the 4 Hz torch · the steady decoy is ignored'];
    if (tc < 14) return ['COASTING', 'torch covered · holding on the prediction'];
    if (tc < 15) return ['SEARCHING', 'still covered · it waits, it does not jump to the decoy'];
    if (tc < 15.5) return ['SEARCHING', 'uncovered · checking the blink again'];
    if (tc < 22) return ['LOCKED', 'locked again · following the phone'];
    return ['SEARCHING', 'torch off · searching'];
  }

  const hist = [];                 // torch positions, model frame, for the tracker's estimate
  const panHist = [];              // pan angle, degrees, for the laptop's trace
  let lastPage = -1, lost = null, prevState = 'SEARCHING';
  const tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3(), phoneInv = new THREE.Matrix4();
  const lensM = new THREE.Vector3();
  const st = { state: 'SEARCHING', hz: 4, az: 0, el: 0, speed: 0, proc: 9, pan: 0, tilt: 0, hist: panHist, target: null, decoy: null, caption: '' };
  const toPix = pModel => {
    tmpA.copy(pModel); model.localToWorld(tmpA);
    const inFront = tmpB.copy(tmpA).applyMatrix4(headCam.matrixWorldInverse).z < 0;
    tmpA.project(headCam);
    if (!inFront || Math.abs(tmpA.x) > 1.02 || Math.abs(tmpA.y) > 1.02) return null;
    return { x: (tmpA.x + 1) / 2 * HUD_W, y: (1 - tmpA.y) / 2 * HUD_H, nx: tmpA.x, ny: tmpA.y };
  };
  const sample = tq => {
    if (!hist.length) return null;
    for (let i = hist.length - 1; i > 0; i--) if (hist[i - 1].t <= tq) {
      const a = hist[i - 1], b = hist[i], u = (tq - a.t) / Math.max(1e-6, b.t - a.t);
      return a.p.clone().lerp(b.p, THREE.MathUtils.clamp(u, 0, 1));
    }
    return hist[0].p.clone();
  };

  function step(t, dt) {
    const tc = ((t % CYCLE) + CYCLE) % CYCLE;
    const [state, caption] = phaseAt(tc);

    // the phone: moved by hand, torch side toward the head
    const p = phonePath(t);
    phone.g.position.copy(p);
    lensM.copy(LENS).applyMatrix4(tiltM);
    const d = lensM.clone().sub(p);
    phone.g.rotation.set(-Math.atan2(d.y, Math.hypot(d.x, d.z)) + 0.05 * Math.sin(0.9 * t + 1),
      Math.atan2(d.x, d.z) + 0.05 * Math.sin(0.7 * t), 0.07 * Math.sin(1.3 * t), 'YXZ');
    phone.g.updateMatrix();
    const torchM = phone.torch.clone().applyMatrix4(phone.g.matrix);
    const strobe = tc < 22, covered = tc >= 13 && tc < 15;
    const lit = strobe && (t * BLINK_HZ) % 1 < 0.5;
    phone.torchMat.emissiveIntensity = lit ? 7 : 0;
    torchGlow.visible = torchCore.visible = lit && !covered;
    phoneLight.intensity = lit && !covered ? 3.2e4 : 0;
    const cover = THREE.MathUtils.smoothstep(tc, 12.55, 13) - THREE.MathUtils.smoothstep(tc, 15, 15.45);
    phone.card.visible = cover > 0.01; phone.card.position.x = -9.5 + (1 - cover) * 95;
    if (screenOn !== strobe) { screenOn = strobe; drawPhoneScreen(phone.screen.g, strobe); phone.screen.t.needsUpdate = true; }

    // the tracker: sees the torch 50 ms late; locked -> aims at it; coasting -> the prediction; else holds
    hist.push({ t, p: torchM.clone() });
    while (hist.length && hist[0].t < t - 1.2) hist.shift();
    const est = sample(t - 0.05), estOld = sample(t - 0.25);
    const vel = est && estOld ? est.clone().sub(estOld).multiplyScalar(5) : new THREE.Vector3();
    if (state === 'LOCKED') lost = null;
    if (state === 'COASTING' && prevState === 'LOCKED') lost = { t, p: est.clone(), v: vel.clone() };
    prevState = state;
    let aim = null;
    if (state === 'LOCKED') aim = est;
    else if (state === 'COASTING' && lost) aim = lost.p.clone().addScaledVector(lost.v, Math.min(1, t - lost.t) * 0.6);
    if (aim) { const a = solveAim(aim); panF.step(a.pan, dt); tiltF.step(a.tilt, dt); }
    else { panF.step(panF.x, dt); tiltF.step(tiltF.x, dt); }
    gPan.rotation.y = panF.x; gTilt.rotation.x = tiltF.x;
    rebuild(false);

    // the laser: on while tracking; its dot lands on the phone (or the card over it)
    const laserOn = state === 'LOCKED' || state === 'COASTING';
    beam.visible = apGlow.visible = laserOn; apMat.emissiveIntensity = laserOn ? 3 : 0;
    const o = LASER.clone().applyMatrix4(tiltM), dir = V([0, 0, 1]).transformDirection(tiltM);
    const n = V([0, 0, 1]).transformDirection(phone.g.matrix);
    const planeP = p.clone().addScaledVector(n, phone.T / 2 + (phone.card.visible ? 10.8 : 1.6));
    const den = dir.dot(n);
    let len = 900, hit = null;
    if (Math.abs(den) > 1e-3) {
      const s = planeP.clone().sub(o).dot(n) / den;
      if (s > 0) {
        const h = o.clone().addScaledVector(dir, s);
        phoneInv.copy(phone.g.matrix).invert();
        const l = h.clone().applyMatrix4(phoneInv);
        if (Math.abs(l.x) < phone.W / 2 && Math.abs(l.y) < phone.H / 2) { len = s; hit = h.addScaledVector(n, 0.4); }
      }
    }
    beam.scale.z = len;
    dot.visible = dotCore.visible = dotHalo.visible = dotRing.visible = laserOn && !!hit;
    if (hit) {
      dot.position.copy(hit); dotCore.position.copy(hit); dotHalo.position.copy(hit);
      dotRing.position.copy(hit).addScaledVector(n, 0.3); dotRing.lookAt(dotRing.position.clone().add(n));
      const ph = (t * 1.6) % 1;                                       // ring grows and fades, 1.6 per second
      dotRing.scale.setScalar(0.8 + ph * 1.6); dotRing.material.opacity = 0.9 * (1 - ph);
    }

    // what the webcam sees, for the overlay
    model.updateMatrixWorld(true); headCam.updateMatrixWorld(true);
    const tp = (strobe && !covered) || state !== 'SEARCHING' ? toPix(torchM) : null;
    const tgt = state === 'COASTING' && aim ? toPix(aim) : tp;
    const hfov = Math.atan(Math.tan(THREE.MathUtils.degToRad(CAM_VFOV / 2)) * CAM_ASPECT);
    st.state = state; st.caption = caption;
    st.checking = state === 'SEARCHING' && !covered && strobe && ((tc > 0.35 && tc < 0.9) || (tc > 15 && tc < 15.5));
    st.target = (state === 'LOCKED' || state === 'COASTING' || st.checking) ? tgt : null;
    st.decoy = toPix(decoyLed);
    if (st.target) {
      st.az = Math.atan(st.target.nx * Math.tan(hfov)) * 180 / Math.PI;
      st.el = Math.atan(st.target.ny * Math.tan(THREE.MathUtils.degToRad(CAM_VFOV / 2))) * 180 / Math.PI;
      const vp = toPix(torchM.clone().addScaledVector(vel, 0.35));
      st.vel = vp && state === 'LOCKED' ? { x: vp.x - st.target.x, y: vp.y - st.target.y } : null;
    }
    const dist = Math.max(1, est ? est.distanceTo(lensM) : 400);
    st.speed = vel.length() / dist * 180 / Math.PI;
    st.hz = 4 + 0.08 * Math.sin(t * 1.7) * Math.sin(t * 0.37);
    st.proc = 9 + 1.6 * Math.sin(t * 2.3) + 0.8 * Math.sin(t * 5.1);
    st.pan = -panF.x * 180 / Math.PI; st.tilt = -tiltF.x * 180 / Math.PI;
    drawHud(hud.g, st); hud.t.needsUpdate = true;
    if (t - lastPage > 0.2 || t < lastPage) {
      lastPage = t;
      panHist.push(st.pan); if (panHist.length > 60) panHist.shift();
      drawPage(page.g, st); page.t.needsUpdate = true;
    }

    // data pulses
    const flowing = state === 'LOCKED' || state === 'COASTING';
    for (const q of pulses) {
      const c = q.cable.curve;
      q.s.visible = !!c && (q.speed < 0.6 || flowing);
      if (!q.s.visible) continue;
      let u = (t * q.speed + q.off) % 1; if (q.reverse) u = 1 - u;
      q.s.position.copy(c.getPointAt(u));
    }
    return { pan: -panF.x, tilt: -tiltF.x, state };
  }

  model.updateMatrixWorld(true);
  const bs = new THREE.Sphere();
  model.traverse(o => { if (o.isMesh && o.castShadow && o.geometry.attributes.position) {
    o.geometry.computeBoundingSphere(); bs.copy(o.geometry.boundingSphere);
    if (bs.radius < 6) o.castShadow = false;
  } });
  const size = new THREE.Vector2();
  let frameNo = 0;
  function render() {
    renderer.shadowMap.needsUpdate = true;
    if (frameNo++ % 2 === 0) {                         // the webcam picture at half the frame rate is plenty
      renderer.setRenderTarget(camRT);
      renderer.render(scene, headCam);
      renderer.setRenderTarget(null);
    }
    renderer.render(scene, camera);
    renderer.getSize(size);
    if (size.x < 300) return;
    const narrow = size.x < 480;                       // on a phone the inset sits above the angle readout
    const pw = Math.round(THREE.MathUtils.clamp(size.x * (narrow ? 0.4 : 0.36), 130, 300)), ph = Math.round(pw * 9 / 16);
    const mx = 12, my = narrow ? 42 : 12;
    pipCam.right = size.x; pipCam.top = size.y; pipCam.updateProjectionMatrix();
    for (const q of [pipView, pipHud]) { q.scale.set(pw, ph, 1); q.position.set(mx + pw / 2, my + ph / 2, q.position.z); }
    pipFrame.scale.set(pw + 2, ph + 2, 1); pipFrame.position.set(mx + pw / 2, my + ph / 2, -1);
    renderer.autoClear = false; renderer.clearDepth(); renderer.render(pipScene, pipCam); renderer.autoClear = true;
  }
  /* Named parts for the page's hover labels, in world coordinates. */
  const at = (obj, p) => () => obj.localToWorld(V(p));
  const HOT = [
    ['Webcam', 'USB camera in the head: the tracker\'s eye', () => gTilt.localToWorld(LENS.clone())],
    ['KY-008 laser', 'Rides with the camera; on while the beacon is locked', () => gTilt.localToWorld(LASER.clone())],
    ['Laser dot', 'Where the beam lands: on the phone, every locked frame', () => (dot.visible ? model.localToWorld(dot.position.clone()) : null)],
    ['Tilt motor · NEMA17', 'Nods the head, soft limit ±18°', at(gPan, [-28, PIVOT_Y, 0])],
    ['Pan motor · NEMA17', 'Turns the whole top, soft limit ±90°', at(model, [0, 36, 0])],
    ['AS5600 encoder', 'Magnetic angle sensor over the pan shaft: closes the loop', at(model, [0, 92, 0])],
    ['Arduino Nano', 'Firmware: takes P / T moves over USB, drives STEP / DIR', at(model, [-53.4, 14, 149])],
    ['2 × A4988 drivers', '1/16 microstepping, current set to Vref 0.55 V', at(model, [14, 18, 147.5])],
    ['TCA9548A multiplexer', 'I²C switch: sensors share one bus (A4 / A5)', at(model, [61, 14, 147.5])],
    ['12 V adapter', 'Motor power only, through the DC jack and kill switch', at(model, [175, 35, -160])],
    ['Beacon · phone torch', 'Blinks at 4 Hz: the one light it must follow', () => phone.g.localToWorld(phone.torch.clone())],
    ['Decoy', 'Steady red LED: seen, measured, ignored', () => decoy.g.localToWorld(decoy.led.clone())],
    ['Laptop · /live page', 'Runs the tracker and shows what the webcam sees', at(laptop, [0, 113, -144])],
  ];
  function hotspots() {
    return HOT.map(([name, text, get]) => ({ name, text, p: get() })).filter(h => h.p);
  }
  return { step, render, hotspots };
}
