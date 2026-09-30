// MK1 and MK2, side by side, live in the browser.
//
// MK1 is the servo rig in the Mk1 demo video, modelled from primitives:
// grey carton, black pan-tilt kit, two blue SG90s, KY-008 laser, jumper
// wires, laptop. MK2 is the stepper terminal as it is built, every part and
// every wire, tracking a phone torch (mk2twin.js).
//
// Both track a beacon blinking at 4 Hz. Drag to rotate; click the view,
// then scroll to zoom. Nothing renders while the section is off screen.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { buildMk2Twin } from './mk2twin.js';

const BLINK_HZ = 4;
const std = (c, m = 0.1, r = 0.6, extra = {}) => new THREE.MeshStandardMaterial({ color: c, metalness: m, roughness: r, ...extra });

function makeViewer(canvas, { cam, target, autoRotate = 0.55, fog = [900, 2200], dist = [180, 1400], shadowR = 420, shadowMap = 1024 }) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'low-power' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x050a14);
  scene.fog = new THREE.Fog(0x050a14, fog[0], fog[1]);

  const camera = new THREE.PerspectiveCamera(34, 1, 1, 4000);
  camera.up.set(0, 0, 1);
  camera.position.set(...cam);

  const controls = new OrbitControls(camera, canvas);
  controls.target.set(...target);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.autoRotate = true; controls.autoRotateSpeed = autoRotate;
  controls.minDistance = dist[0]; controls.maxDistance = dist[1];
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
  key.shadow.mapSize.set(shadowMap, shadowMap);
  Object.assign(key.shadow.camera, { left: -shadowR, right: shadowR, top: shadowR, bottom: -shadowR, near: 10, far: 1800 });
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
  return { renderer, scene, camera, controls, grid };
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

/* Hover labels for the MK2 twin: every named part gets a small marker while
   the pointer is over the view; the nearest one is named in a card. On touch,
   a tap does the same. */
function hoverLabels(canvas, v, twin) {
  const host = canvas.parentElement;
  if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
  if (!document.getElementById('hsStyle')) {
    const st = document.createElement('style'); st.id = 'hsStyle';
    st.textContent = `
      .hs-layer{position:absolute;inset:0;pointer-events:none;z-index:3;transition:opacity .2s}
      .hs-dot{position:absolute;left:-5px;top:-5px;width:10px;height:10px;border-radius:50%;background:rgba(79,199,234,.25);border:1.5px solid #4FC7EA;box-shadow:0 0 8px rgba(79,199,234,.6)}
      .hs-dot.on{background:#4FC7EA;box-shadow:0 0 0 5px rgba(79,199,234,.25),0 0 14px #4FC7EA}
      .hs-tip{position:absolute;left:0;top:0;max-width:230px;padding:7px 10px;border-radius:8px;background:rgba(5,11,22,.92);border:1px solid rgba(79,199,234,.55);box-shadow:0 8px 24px rgba(0,0,0,.5);font:12px/1.35 ui-monospace,Menlo,Consolas,monospace;color:#cfe3f3}
      .hs-tip b{display:block;color:#fff;font-size:12.5px;margin-bottom:2px;letter-spacing:.3px}
      .hs-hint{position:absolute;right:12px;bottom:34px;pointer-events:none;z-index:3;font:10.5px ui-monospace,Menlo,Consolas,monospace;letter-spacing:.8px;color:#8fb3cf;background:rgba(5,11,22,.6);padding:3px 8px;border-radius:5px;border:1px solid rgba(79,199,234,.25)}`;
    document.head.appendChild(st);
  }
  const hint = document.createElement('div'); hint.className = 'hs-hint'; hint.textContent = 'HOVER TO NAME THE PARTS';
  const layer = document.createElement('div'); layer.className = 'hs-layer'; layer.style.opacity = 0;
  const tip = document.createElement('div'); tip.className = 'hs-tip'; layer.appendChild(tip);
  host.appendChild(layer); host.appendChild(hint);
  let mouse = null; const dots = []; const p = new THREE.Vector3();
  const at = e => { const r = canvas.getBoundingClientRect(); mouse = { x: e.clientX - r.left, y: e.clientY - r.top }; };
  canvas.addEventListener('pointermove', at);
  canvas.addEventListener('pointerdown', at);
  canvas.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') mouse = null; });
  function update() {
    layer.style.opacity = mouse ? 1 : 0; hint.style.display = mouse ? 'none' : 'block';
    if (!mouse) return;
    const w = canvas.clientWidth, h = canvas.clientHeight, hs = twin.hotspots();
    while (dots.length < hs.length) { const d = document.createElement('i'); d.className = 'hs-dot'; layer.insertBefore(d, tip); dots.push(d); }
    let best = null, bd = 44;
    hs.forEach((s, i) => {
      p.copy(s.p).project(v.camera);
      const ok = p.z < 1 && Math.abs(p.x) < 1 && Math.abs(p.y) < 1, x = (p.x + 1) / 2 * w, y = (1 - p.y) / 2 * h;
      dots[i].style.display = ok ? 'block' : 'none'; dots[i].style.transform = `translate(${x}px,${y}px)`;
      s.x = x; s.y = y;
      if (ok) { const d = Math.hypot(x - mouse.x, y - mouse.y); if (d < bd) { bd = d; best = s; } }
    });
    for (let i = hs.length; i < dots.length; i++) dots[i].style.display = 'none';
    dots.forEach((d, i) => d.classList.toggle('on', hs[i] === best));
    if (!best) { tip.style.display = 'none'; return; }
    tip.style.display = 'block'; tip.innerHTML = `<b>${best.name}</b>${best.text}`;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    const tx = best.x + 16 + tw > w ? best.x - 16 - tw : best.x + 16, ty = Math.min(Math.max(best.y - th / 2, 6), h - th - 6);
    tip.style.transform = `translate(${tx}px,${ty}px)`;
  }
  return { update };
}

function start() {
  const c1 = document.getElementById('rigMk1'), c2 = document.getElementById('rigMk2');
  if (!c2) return;                                   // the SOP page shows MK2 only
  // Both framed from the side, so the mechanism, the beam and the beacon
  // it is chasing are all in view.
  const v1 = c1 ? makeViewer(c1, { cam: [820, -300, 520], target: [0, -120, 130] }) : null;
  // MK2 orbits the centre of the whole bench -- rig, phone, decoy, laptop and
  // adapter -- from far enough out that the laptop never leaves the frame.
  const v2 = makeViewer(c2, { cam: [944, -163, 665], target: [-40, -10, 90], autoRotate: -0.3,
    fog: [2000, 4600], dist: [160, 2800], shadowR: 700, shadowMap: 2048 });
  const step1 = v1 ? buildMk1(v1) : null, mk2 = buildMk2Twin(v2);
  window.__zdViewers = { v1, v2, mk2 };                                // test hook (screenshots)
  const labels = mk2.hotspots ? hoverLabels(c2, v2, mk2) : null;
  const view2 = c2.closest('.rig-view'), view1 = c1 ? c1.closest('.rig-view') : null;
  const t0 = parseFloat(new URLSearchParams(location.search).get('mk2t')) || 0;   // start the MK2 run at a given second
  const out1 = document.getElementById('rigMk1Read'), out2 = document.getElementById('rigMk2Read');
  const deg = r => (r * 180 / Math.PI).toFixed(1).padStart(6);

  let visible = false, last = performance.now() / 1000, t = 0;
  new IntersectionObserver(es => { visible = es.some(e => e.isIntersecting); }, { threshold: 0.05 })
    .observe((c1 || c2).closest('section') || c2);
  function frame() {
    requestAnimationFrame(frame);
    const now = performance.now() / 1000, dt = Math.min(0.05, now - last); last = now;
    if (!visible || document.hidden) return;
    t += dt;
    if (step1 && !(view1 && view1.classList.contains('flat'))) {   // skip MK1 while its PHOTO / VIDEO tab is up
      const a = step1(t, dt);
      v1.controls.update(); v1.renderer.render(v1.scene, v1.camera);
      if (out1) out1.textContent = `PAN ${deg(a.pan)}°  TILT ${deg(a.tilt)}°`;
    }
    if (!(view2 && view2.classList.contains('flat'))) {        // skip MK2 while its PHOTO / VIDEO tab is up
      const b = mk2.step(t + t0, dt);
      v2.controls.update(); mk2.render();
      if (labels) labels.update();
      if (out2) { out2.textContent = `${b.state.padEnd(9)}  PAN ${deg(b.pan)}°  TILT ${deg(b.tilt)}°`; out2.dataset.state = b.state; }
    }
  }
  frame();
}

// WebGL is optional: a browser without it keeps the static fallback.
try { const t = document.createElement('canvas'); if (t.getContext('webgl2') || t.getContext('webgl')) start(); }
catch (e) { console.warn('3D view unavailable', e); }
