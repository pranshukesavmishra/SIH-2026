// MK1 and MK2, side by side, live in the browser.
//
// MK1 is the servo rig in the Mk1 demo video, modelled from primitives:
// grey carton, black pan-tilt kit, two blue SG90s, KY-008 laser, jumper
// wires, laptop. MK2 is the stepper terminal, loaded from the project's own
// CAD meshes (docs/cad/web, the same files as the 3D assembly page).
//
// Both track a beacon blinking at 4 Hz. Drag to rotate; click the view,
// then scroll to zoom. Nothing renders while the section is off screen.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

const BLINK_HZ = 4;
const std = (c, m = 0.1, r = 0.6, extra = {}) => new THREE.MeshStandardMaterial({ color: c, metalness: m, roughness: r, ...extra });

function makeViewer(canvas, { cam, target, autoRotate = 0.55 }) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x050a14);
  scene.fog = new THREE.Fog(0x050a14, 900, 2200);

  const camera = new THREE.PerspectiveCamera(34, 1, 1, 4000);
  camera.up.set(0, 0, 1);
  camera.position.set(...cam);

  const controls = new OrbitControls(camera, canvas);
  controls.target.set(...target);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.autoRotate = true; controls.autoRotateSpeed = autoRotate;
  controls.minDistance = 180; controls.maxDistance = 1400;
  controls.maxPolarAngle = Math.PI * 0.49;
  // Scroll-to-zoom only after the view is clicked, so the page still
  // scrolls normally past it.
  controls.enableZoom = false;
  canvas.addEventListener('pointerdown', () => { controls.enableZoom = true; controls.autoRotate = false; });
  canvas.addEventListener('pointerleave', () => { controls.enableZoom = false; });
  canvas.addEventListener('dblclick', () => { controls.autoRotate = true; });

  scene.add(new THREE.HemisphereLight(0x9fc3e6, 0x0a1020, 1.05));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(260, -300, 520); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -420, right: 420, top: 420, bottom: -420, near: 10, far: 1600 });
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x4FC7EA, 0.55); rim.position.set(-300, 260, 200); scene.add(rim);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(3000, 3000), std(0x0b1422, 0.2, 0.85));
  floor.receiveShadow = true; scene.add(floor);
  const grid = new THREE.GridHelper(1600, 32, 0x1b2c46, 0x111d31);
  grid.rotation.x = Math.PI / 2; grid.position.z = 0.3; scene.add(grid);

  function resize() {
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    renderer.setSize(r.width, r.height, false);
    camera.aspect = r.width / r.height; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(canvas); resize();
  return { renderer, scene, camera, controls };
}

/* A beam from a point along a direction: thin additive cylinder. */
function makeBeam(len, color = 0xff2a2a) {
  const g = new THREE.CylinderGeometry(0.8, 3.2, len, 10, 1, true);
  g.translate(0, -len / 2, 0);
  return new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.55,
    depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide }));
}

/* Smoothly aim a (pan, tilt) pair at a target, with a rate limit. */
function aimer(rate, gain) {
  const s = { pan: 0, tilt: 0 };
  return (wantPan, wantTilt, dt) => {
    const step = (cur, want) => cur + Math.max(-rate * dt, Math.min(rate * dt, (want - cur) * Math.min(1, gain * dt)));
    s.pan = step(s.pan, wantPan); s.tilt = step(s.tilt, wantTilt);
    return s;
  };
}

// ======================================================================
// MK1 — servo rig on a carton, laptop behind
// ======================================================================
function buildMk1(v) {
  const { scene } = v;
  const root = new THREE.Group(); scene.add(root);
  const add = (geo, mat, x, y, z, parent = root) => {
    const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m;
  };
  const BLACK = std(0x141619, 0.2, 0.55), BLUE = std(0x2d63d6, 0.05, 0.35, { transparent: true, opacity: 0.92 });

  // laptop: base, keyboard, hinged lid with the live page on screen
  const lap = new THREE.Group(); lap.position.set(0, 150, 0); root.add(lap);
  add(new THREE.BoxGeometry(340, 235, 18), std(0x26292e, 0.55, 0.45), 0, 0, 9, lap);
  add(new THREE.BoxGeometry(290, 105, 1.5), std(0x16181b, 0.2, 0.7), 0, 20, 18.5, lap);
  add(new THREE.BoxGeometry(110, 62, 1), std(0x1d2024, 0.3, 0.5), 0, -68, 18.3, lap);
  const lid = new THREE.Group(); lid.position.set(0, 117, 18); lid.rotation.x = -0.32; lap.add(lid);
  add(new THREE.BoxGeometry(340, 7, 225), std(0x26292e, 0.55, 0.45), 0, 0, 112, lid);
  const sc = document.createElement('canvas'); sc.width = 512; sc.height = 320;
  const g = sc.getContext('2d');
  g.fillStyle = '#040915'; g.fillRect(0, 0, 512, 320);
  g.fillStyle = '#6d7480'; g.fillRect(24, 36, 330, 250);
  g.fillStyle = '#0A1224'; g.fillRect(370, 36, 120, 250);
  g.strokeStyle = '#3BD68C'; g.lineWidth = 4;
  [[150, 130]].forEach(([x, y]) => { g.beginPath(); for (const [dx, dy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
    g.moveTo(x + dx * 26, y + dy * 26 - dy * 11); g.lineTo(x + dx * 26, y + dy * 26); g.lineTo(x + dx * 26 - dx * 11, y + dy * 26); } g.stroke(); });
  g.fillStyle = '#3BD68C'; g.fillRect(380, 50, 100, 22);
  g.fillStyle = '#4FC7EA'; for (let i = 0; i < 6; i++) g.fillRect(380, 90 + i * 26, 60 + (i * 17) % 40, 8);
  const tex = new THREE.CanvasTexture(sc); tex.colorSpace = THREE.SRGBColorSpace;
  const screen = new THREE.Mesh(new THREE.PlaneGeometry(318, 200), new THREE.MeshBasicMaterial({ map: tex }));
  screen.position.set(0, -3.6, 112); screen.rotation.x = Math.PI / 2; lid.add(screen);
  add(new THREE.CylinderGeometry(2.2, 2.2, 1, 12), std(0x050505), 0, -3.8, 218, lid).rotation.x = Math.PI / 2;

  // grey carton the rig sits on
  add(new THREE.BoxGeometry(150, 112, 96), std(0x8e9296, 0.05, 0.92), 0, -40, 48);
  add(new THREE.PlaneGeometry(46, 30), std(0xe9e9e6, 0, 0.8), 52, -96.2, 40).rotation.x = Math.PI / 2;

  // pan-tilt kit: base plate, pan servo, pan bracket
  // Drawn 1.3x so a 5 cm kit reads at this viewing distance.
  const KIT = 1.3;
  const base = new THREE.Group(); base.position.set(0, -40, 96); base.scale.setScalar(KIT); root.add(base);
  add(new THREE.BoxGeometry(46, 46, 4), BLACK, 0, 0, 2, base);
  add(new THREE.BoxGeometry(23, 12.5, 22.5), BLUE, 0, 0, 15, base);
  const pan = new THREE.Group(); pan.position.set(0, 0, 27); base.add(pan);
  add(new THREE.CylinderGeometry(13, 13, 3, 28), BLACK, 0, 0, 1.5, pan).rotation.x = Math.PI / 2;
  add(new THREE.BoxGeometry(34, 4, 30), BLACK, 0, 14, 17, pan);
  add(new THREE.BoxGeometry(34, 4, 30), BLACK, 0, -14, 17, pan);
  add(new THREE.BoxGeometry(12.5, 23, 22.5), BLUE, 23, 0, 20, pan);          // tilt servo, on the side
  const tilt = new THREE.Group(); tilt.position.set(0, 0, 24); pan.add(tilt);
  add(new THREE.BoxGeometry(30, 26, 3), BLACK, 0, 0, 12, tilt);
  add(new THREE.BoxGeometry(3, 26, 14), BLACK, 14, 0, 5, tilt);
  add(new THREE.BoxGeometry(3, 26, 14), BLACK, -14, 0, 5, tilt);
  // KY-008 laser on top: black PCB, silver barrel, red aperture
  add(new THREE.BoxGeometry(18, 15, 1.6), std(0x0c0c0c, 0.1, 0.5), 0, 0, 14.5, tilt);
  const barrel = add(new THREE.CylinderGeometry(3.4, 3.4, 13, 16), std(0xb8bcc2, 0.9, 0.25), 0, -9, 18, tilt);
  const dot = add(new THREE.CircleGeometry(1.8, 16), new THREE.MeshBasicMaterial({ color: 0xff2020 }), 0, -15.6, 18, tilt);
  dot.rotation.x = Math.PI / 2;
  void barrel;
  const beam = makeBeam(600); beam.position.set(0, -15.8, 18); tilt.add(beam);

  // jumper wires from the servos down the carton toward the laptop
  const wire = (col, pts) => {
    const curve = new THREE.CatmullRomCurve3(pts.map(p => new THREE.Vector3(...p)));
    const m = new THREE.Mesh(new THREE.TubeGeometry(curve, 48, 0.9, 6), std(col, 0.1, 0.5));
    m.castShadow = true; root.add(m);
  };
  const W = [[0xf2c200, 0], [0xff7a1a, 3], [0xd01818, 6], [0x6b3a1a, 9]];
  for (const [col, o] of W) wire(col, [[12 + o * 0.3, -40, 130], [45, -30 + o, 150], [80, -10 + o, 118], [88, 10 + o, 70], [100, 60 + o, 20], [120, 95 + o, 12]]);

  // beacon: a phone with its torch blinking, moved by hand in front
  const phone = new THREE.Group(); root.add(phone);
  add(new THREE.BoxGeometry(72, 8, 150), std(0x101216, 0.4, 0.35), 0, 0, 0, phone);
  const torch = add(new THREE.SphereGeometry(5, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }), -20, 4.5, 55, phone);
  const glow = new THREE.PointLight(0xffffff, 0, 260); glow.position.set(-20, 20, 55); phone.add(glow);

  // SG90s are slow and coarse: ~1° steps, ~0.1 s/60°
  const aim = aimer(THREE.MathUtils.degToRad(300), 9);
  return (t, dt) => {
    const bx = 150 * Math.sin(2 * Math.PI * 0.09 * t), bz = 190 + 70 * Math.sin(2 * Math.PI * 0.14 * t + 1);
    const by = -420;
    phone.position.set(bx, by, bz);
    const lit = (t * BLINK_HZ) % 1 < 0.5;
    torch.material.color.setHex(lit ? 0xffffff : 0x222222); glow.intensity = lit ? 2.2e4 : 0;
    const pivot = new THREE.Vector3(0, -40, 96 + KIT * (27 + 24 + 18));
    const tx = bx - 20 - pivot.x, ty = by + 4.5 - pivot.y, tz = bz + 55 - pivot.z;
    let wantPan = Math.atan2(tx, -ty), wantTilt = -Math.atan2(tz, Math.hypot(tx, ty));
    const q = THREE.MathUtils.degToRad(1);                // servo resolution
    wantPan = Math.round(wantPan / q) * q; wantTilt = Math.round(wantTilt / q) * q;
    const s = aim(wantPan, wantTilt, dt);
    pan.rotation.z = s.pan; tilt.rotation.x = s.tilt;
    const dist = Math.hypot(tx, ty, tz);
    beam.scale.y = dist / KIT / 600;
    beam.material.opacity = 0.5;
    return { pan: s.pan, tilt: -s.tilt };
  };
}

// ======================================================================
// MK2 — stepper terminal, from the CAD meshes
// ======================================================================
const TILT_PIVOT = new THREE.Vector3(0, 6, 62);
const MK2_PARTS = {
  base: ['fixed', { c: 0xa8d8ef, m: 0, r: .15, o: .55 }], pan_motor: ['fixed', { c: 0x2b2f36, m: .85, r: .42 }],
  pan_encoder: ['fixed', { c: 0x1f7a4d, m: .3, r: .5 }], platform: ['pan', { c: 0xa8d8ef, m: 0, r: .15, o: .7 }],
  riser: ['pan', { c: 0xc9a227, m: .9, r: .25 }], bracket: ['pan', { c: 0x7d8a99, m: .85, r: .3 }],
  tilt_motor: ['pan', { c: 0x2b2f36, m: .85, r: .42 }], tilt_encoder: ['pan', { c: 0x1f7a4d, m: .3, r: .5 }],
  vibration: ['pan', { c: 0x8a6a3a, m: .6, r: .45 }], tilt_magnet: ['tilt', { c: 0x9aa4b0, m: .8, r: .3 }],
  standoff: ['tilt', { c: 0xd4a94a, m: .95, r: .2 }], head: ['tilt', { c: 0xe8dcc8, m: .1, r: .6 }],
};

/* Soft additive glow, for LEDs that are lit. */
function glowSprite(color, size) {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), r = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(0.25, 'rgba(255,255,255,0.55)'); r.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = r; g.fillRect(0, 0, 64, 64);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), color,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  sp.scale.setScalar(size); return sp;
}

/* A mesh plus its hard edges drawn in dark lines: the CAD look. */
function cadMesh(geo, mat, edgeOpacity = 0.32) {
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = m.receiveShadow = true;
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 28),
    new THREE.LineBasicMaterial({ color: 0x06101c, transparent: true, opacity: edgeOpacity }));
  m.add(e);
  return m;
}

/* One of the stage targets, loaded from its CAD parts, turned to face the
   gimbal (its LED looks along +Z in the model; the gimbal is at +Y). */
function loadUnit(loader, parts, centre, onMesh) {
  const g = new THREE.Group(), inner = new THREE.Group();
  inner.rotation.x = -Math.PI / 2;                 // model +Z -> world +Y
  inner.position.set(0, 0, 0);
  g.add(inner);
  for (const [name, mat] of parts) {
    loader.load(`cad/web/${name}.stl`, geo => {
      geo.computeVertexNormals();
      geo.translate(-centre[0], -centre[1], -centre[2]);
      const m = cadMesh(geo, mat, 0.25);
      inner.add(m); if (onMesh) onMesh(name, m);
    });
  }
  return g;
}

function buildMk2(v, onLoaded) {
  const { scene } = v;
  // The pan motor hangs 43 mm under the base plate, so the plate stands on
  // four legs; everything is lifted by their height.
  const LEG = 46, K = 1.7;
  const root = new THREE.Group(); root.scale.setScalar(K); root.position.z = LEG * K; scene.add(root);
  for (const [x, y] of [[-66, -66], [66, -66], [66, 66], [-66, 66]]) {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(3, 3, LEG, 12), std(0xd4a94a, 0.95, 0.2));
    leg.rotation.x = Math.PI / 2; leg.position.set(x, y, -3 - LEG / 2); leg.castShadow = true; root.add(leg);
  }
  const gFixed = new THREE.Group(), gPan = new THREE.Group(), gTilt = new THREE.Group();
  gTilt.position.copy(TILT_PIVOT); gPan.add(gTilt); root.add(gFixed, gPan);
  const G = { fixed: gFixed, pan: gPan, tilt: gTilt };
  const loader = new STLLoader();
  let n = 0;
  for (const [name, [grp, sp]] of Object.entries(MK2_PARTS)) {
    loader.load(`cad/web/${name}.stl`, geo => {
      geo.computeVertexNormals();
      if (grp === 'tilt') geo.translate(-TILT_PIVOT.x, -TILT_PIVOT.y, -TILT_PIVOT.z);
      const o = name === 'head' ? 0.88 : sp.o;
      G[grp].add(cadMesh(geo, std(sp.c, sp.m, sp.r, o ? { transparent: true, opacity: o } : {})));
      if (++n === Object.keys(MK2_PARTS).length && onLoaded) onLoaded();
    });
  }

  // Head front face (y = -88 from the tilt pivot): the webcam lens behind
  // its red filter, and the KY-008 laser beside it -- boresighted.
  const lens = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 4, 24), std(0x0a0a0c, 0.6, 0.25));
  lens.position.set(-16, -90, 0); gTilt.add(lens);
  const glass = new THREE.Mesh(new THREE.CircleGeometry(4.2, 24), std(0x1a2a44, 0.9, 0.05));
  glass.rotation.x = Math.PI / 2; glass.position.set(-16, -92.1, 0); gTilt.add(glass);
  const filt = new THREE.Mesh(new THREE.BoxGeometry(22, 0.8, 22), new THREE.MeshStandardMaterial({
    color: 0xd01c1c, transparent: true, opacity: 0.45, roughness: 0.2, metalness: 0 }));
  filt.position.set(-16, -92.8, 0); gTilt.add(filt);
  const barrel = new THREE.Mesh(new THREE.CylinderGeometry(3.25, 3.25, 5, 20), std(0xc9a227, 0.95, 0.2));
  barrel.position.set(20, -90.5, -2); gTilt.add(barrel);
  const aperture = new THREE.Mesh(new THREE.CircleGeometry(1.6, 16), new THREE.MeshBasicMaterial({ color: 0xff2020 }));
  aperture.rotation.x = Math.PI / 2; aperture.position.set(20, -93.1, -2); gTilt.add(aperture);

  // the laser, modulated at 7 Hz so the camera can tell its own dot apart
  const beam = makeBeam(400); beam.position.set(20, -93, -2); gTilt.add(beam);

  // ---- the beacon: ABS box, red LED under a ping-pong diffuser, a Nano ----
  const beacon = loadUnit(loader, [
    ['beacon_case', std(0xd9c3a6, 0.05, 0.7, { transparent: true, opacity: 0.6 })],
    ['beacon_led', new THREE.MeshStandardMaterial({ color: 0xff4040, emissive: 0xff1a1a, emissiveIntensity: 1, roughness: 0.5 })],
    ['beacon_nano', std(0x2b5c8a, 0.4, 0.5)],
    ['beacon_switch', std(0x8892a0, 0.8, 0.35)],
  ], [45, 30, 21], (name, m) => { if (name === 'beacon_led') beacon.userData.led = m; });
  beacon.scale.setScalar(K); scene.add(beacon);
  // glow at the diffuser, which sits ~45 mm in front of the box centre
  const bGlow = glowSprite(0xff3030, 90); bGlow.position.set(0, 45, 0); beacon.add(bGlow);
  const bLight = new THREE.PointLight(0xff3030, 0, 380); bLight.position.set(0, 60, 0); beacon.add(bLight);

  // ---- the decoy: same red light, steady (never blinks) -- and ignored ----
  const decoy = loadUnit(loader, [
    ['decoy_case', std(0xc9cdd2, 0.05, 0.7, { transparent: true, opacity: 0.6 })],
    ['decoy_led', new THREE.MeshStandardMaterial({ color: 0xff5a48, emissive: 0xff4a38, emissiveIntensity: 1 })],
    ['decoy_cells', std(0x6b7f94, 0.5, 0.5)],
    ['decoy_switch', std(0x8892a0, 0.8, 0.35)],
  ], [35, 27, 14]);
  decoy.scale.setScalar(K); decoy.position.set(-300, -660, 150); scene.add(decoy);
  const dGlow = glowSprite(0xff5a48, 110); dGlow.position.set(0, 26, 0); decoy.add(dGlow);
  const dLight = new THREE.PointLight(0xff5a48, 3.5e4, 420); dLight.position.set(0, 60, 0); decoy.add(dLight);
  const post = (x, y, z, h) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(4, 4, h, 12), std(0x2a3446, 0.6, 0.4));
    m.rotation.x = Math.PI / 2; m.position.set(x, y, h / 2); m.castShadow = true; scene.add(m); };
  post(-300, -660, 150 - 30);

  // steppers: fast and fine
  const aim = aimer(THREE.MathUtils.degToRad(600), 14);
  return (t, dt) => {
    const bx = 60 + 170 * Math.sin(2 * Math.PI * 0.08 * t), bz = 170 + 70 * Math.sin(2 * Math.PI * 0.16 * t + 0.5);
    const by = -640;
    beacon.position.set(bx, by, bz);
    const lit = (t * BLINK_HZ) % 1 < 0.5;
    const led = beacon.userData.led;
    if (led) { led.material.emissiveIntensity = lit ? 1.4 : 0.02; led.material.color.setHex(lit ? 0xff4040 : 0x4a1414); }
    bGlow.visible = lit; bLight.intensity = lit ? 3e4 : 0;
    const P = TILT_PIVOT.clone().multiplyScalar(K).add(new THREE.Vector3(0, 0, LEG * K));
    const tx = bx - P.x, ty = by + 40 * K - P.y, tz = bz - P.z;
    const s = aim(Math.atan2(tx, -ty), -Math.atan2(tz, Math.hypot(tx, ty)), dt);
    gPan.rotation.z = s.pan; gTilt.rotation.x = s.tilt;
    beam.scale.y = Math.hypot(tx, ty, tz) / K / 400;
    beam.material.opacity = (t * 7) % 1 < 0.5 ? 0.6 : 0.18;
    return { pan: s.pan, tilt: -s.tilt };
  };
}

// ======================================================================
function start() {
  const c1 = document.getElementById('rigMk1'), c2 = document.getElementById('rigMk2');
  if (!c1 || !c2) return;
  // Both framed from the side, so the mechanism, the beam and the beacon
  // it is chasing are all in view.
  const v1 = makeViewer(c1, { cam: [820, -300, 520], target: [0, -120, 130] });
  const v2 = makeViewer(c2, { cam: [760, 520, 560], target: [-40, -290, 150], autoRotate: -0.45 });
  const step1 = buildMk1(v1), step2 = buildMk2(v2);
  const out1 = document.getElementById('rigMk1Read'), out2 = document.getElementById('rigMk2Read');
  const deg = r => (r * 180 / Math.PI).toFixed(1).padStart(6);

  let visible = false, last = performance.now() / 1000, t = 0;
  new IntersectionObserver(es => { visible = es.some(e => e.isIntersecting); }, { threshold: 0.05 })
    .observe(c1.closest('section') || c1);
  function frame() {
    requestAnimationFrame(frame);
    const now = performance.now() / 1000, dt = Math.min(0.05, now - last); last = now;
    if (!visible || document.hidden) return;
    t += dt;
    const a = step1(t, dt), b = step2(t, dt);
    v1.controls.update(); v2.controls.update();
    v1.renderer.render(v1.scene, v1.camera); v2.renderer.render(v2.scene, v2.camera);
    if (out1) out1.textContent = `PAN ${deg(a.pan)}°  TILT ${deg(a.tilt)}°`;
    if (out2) out2.textContent = `PAN ${deg(b.pan)}°  TILT ${deg(b.tilt)}°`;
  }
  frame();
}

// WebGL is optional: a browser without it keeps the static fallback.
try { const t = document.createElement('canvas'); if (t.getContext('webgl2') || t.getContext('webgl')) start(); }
catch (e) { console.warn('3D view unavailable', e); }
