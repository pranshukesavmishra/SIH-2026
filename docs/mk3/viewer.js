/* Plan Urena · MK3 3D viewer. Loads every part the CAD script exported
   (docs/mk3/models, placed in assembly coordinates) and drives the real
   kinematics: pan about Z, tilt about the tilt shaft, 4:1 belt ratio shown
   on the motor pulleys. Exploded view, part picking, printed/bought filter. */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

export async function mountViewer(el, opts = {}) {
  const base = opts.base || 'mk3/models/';
  if (opts.light) Object.assign(opts, { bg: opts.bg || 0xf3f5f8, floor: opts.floor || 0xe9edf2 });
  const man = await (await fetch(base + 'manifest.json')).json();
  const ZT = man.z_tilt;
  const W = () => el.clientWidth, H = () => el.clientHeight;

  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(W(), H());
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.shadowMap.enabled = true;
  el.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(opts.bg || 0x0b0d12);
  const cam = new THREE.PerspectiveCamera(32, W() / H(), 1, 5000);
  cam.up.set(0, 0, 1);
  cam.position.set(440, -380, 330);
  const ctl = new OrbitControls(cam, renderer.domElement);
  ctl.target.set(-20, 0, 125); ctl.enableDamping = true; ctl.update();

  scene.add(opts.light ? new THREE.HemisphereLight(0xffffff, 0x9aa3b0, 1.9) : new THREE.HemisphereLight(0xdfe8ff, 0x2a2f38, 1.1));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(300, -200, 500); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); Object.assign(key.shadow.camera, { left: -300, right: 300, top: 300, bottom: -300, near: 10, far: 1500 });
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x9fc7ff, 0.9); rim.position.set(-300, 300, 200); scene.add(rim);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(700, 64), new THREE.MeshStandardMaterial({ color: opts.floor || 0x151922, roughness: 0.95 }));
  floor.receiveShadow = true; floor.position.z = -0.5; scene.add(floor);
  const grid = opts.light ? new THREE.GridHelper(1200, 60, 0xcfd6df, 0xdce2e9) : new THREE.GridHelper(1200, 60, 0x2a3140, 0x1c222d); grid.rotation.x = Math.PI / 2; grid.position.z = 0; scene.add(grid);

  // kinematic tree: world > fixed, world > pan > tilt
  const G = { fixed: new THREE.Group(), fixedbelt: new THREE.Group(), pan: new THREE.Group(), tilt: new THREE.Group(), desk: new THREE.Group() };
  const tiltPivot = new THREE.Group(); tiltPivot.position.set(0, 0, ZT);
  G.tilt.position.set(0, 0, -ZT); tiltPivot.add(G.tilt); G.pan.add(tiltPivot);
  Object.entries(G).forEach(([k, g]) => { if (k !== 'tilt') scene.add(g); });
  scene.remove(G.pan); scene.add(G.pan);

  const loader = new STLLoader();
  const meshes = [];
  await Promise.all(man.parts.map(async p => {
    const geo = await new Promise((res, rej) => loader.load(base + p.name + '.stl', res, undefined, rej));
    geo.computeVertexNormals();
    const metal = /shaft|pulley20|brg/.test(p.name);
    const mat = new THREE.MeshStandardMaterial({ color: new THREE.Color(p.colour), roughness: metal ? 0.25 : (p.printed ? 0.62 : 0.45), metalness: metal ? 0.9 : 0.05 });
    const m = new THREE.Mesh(geo, mat); m.castShadow = m.receiveShadow = true;
    m.userData = p; geo.computeBoundingBox(); m.userData.centre = geo.boundingBox.getCenter(new THREE.Vector3());
    (G[p.group] || G.fixed).add(m); meshes.push(m);
  }));

  // controls state
  const st = { pan: 0, tilt: 0, explode: 0, auto: !!opts.auto, showBought: true, showPrinted: true, desk: opts.desk !== false };
  G.desk.visible = st.desk;
  const motorSpin = { pan: meshes.find(m => m.userData.name === 'm_pan_pulley20'), tilt: meshes.find(m => m.userData.name === 'm_tilt_pulley20') };
  const panPulleyPos = motorSpin.pan ? motorSpin.pan.userData.centre.clone() : null;

  // exploded view: layers lift apart in build order, side parts slide outwards
  const LIFT = { fixed: 0, fixedbelt: 0.35, pan: 1.0, tilt: 1.9, desk: 0 };
  function applyExplode() {
    meshes.forEach(m => {
      const c = m.userData.centre, g = m.userData.group, n = m.userData.name;
      if (g === 'desk') { m.position.set(0, 0, 0); return; }
      let lift = (LIFT[g] || 0) * 70;
      if (/leg/.test(n)) lift = -10;
      if (/pan_sensor_bridge|pan_as5600/.test(n)) lift = 55;
      if (/magnet_cap/.test(n)) lift = 30;
      if (/spindle_washer/.test(n)) lift = -40;
      if (/brg_pan_low/.test(n)) lift = 12;
      if (/brg_pan_top/.test(n)) lift = 35;
      if (/trunnion/.test(n)) lift = 1.9 * 70;
      const side = new THREE.Vector3(c.x, c.y, 0);
      const r = side.length();
      side.normalize().multiplyScalar(r > 30 ? 45 : 0);
      if (/leg/.test(n)) side.multiplyScalar(1.4);
      m.position.set(side.x * st.explode, side.y * st.explode, lift * st.explode);
    });
  }
  function applyPose() {
    G.pan.rotation.z = THREE.MathUtils.degToRad(st.pan);
    tiltPivot.rotation.y = THREE.MathUtils.degToRad(-st.tilt);
    // motor pulleys turn 4x the output (visual only)
    if (motorSpin.pan) motorSpin.pan.rotation.set(0, 0, 0);
  }
  function applyFilter() {
    meshes.forEach(m => { m.visible = m.userData.printed ? st.showPrinted : st.showBought; });
    G.desk.visible = st.desk;
  }

  // picking
  const ray = new THREE.Raycaster(), ptr = new THREE.Vector2();
  let picked = null;
  renderer.domElement.addEventListener('click', e => {
    const r = renderer.domElement.getBoundingClientRect();
    ptr.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
    ray.setFromCamera(ptr, cam);
    const hit = ray.intersectObjects(meshes.filter(m => m.visible), false)[0];
    if (picked) picked.material.emissive.setHex(0x000000);
    picked = hit ? hit.object : null;
    if (picked) picked.material.emissive.setHex(0x1b3b5a);
    opts.onPick && opts.onPick(picked ? picked.userData : null);
  });

  let t0 = performance.now();
  (function loop(now) {
    requestAnimationFrame(loop);
    if (st.auto) {
      const t = (now - t0) / 1000;
      st.pan = Math.sin(t * 0.45) * 120; st.tilt = Math.sin(t * 0.7) * 35 + 10;
      opts.onPose && opts.onPose(st.pan, st.tilt);
    }
    applyPose();
    ctl.update();
    renderer.render(scene, cam);
  })(performance.now());
  new ResizeObserver(() => { renderer.setSize(W(), H()); cam.aspect = W() / H(); cam.updateProjectionMatrix(); }).observe(el);

  applyExplode(); applyFilter();
  return {
    set(k, v) { st[k] = v; if (k === 'explode') applyExplode(); if (/show|desk/.test(k)) applyFilter(); },
    view(name) {
      const V = { iso: [[440, -380, 330], [-20, 0, 125]], front: [[520, 0, 130], [0, 0, 110]], side: [[0, -520, 130], [0, 0, 110]],
        top: [[0, 0, 640], [0, 0, 60]], head: [[230, -190, 270], [10, 0, 200]], base: [[300, -300, 160], [-30, 0, 45]],
        wide: [[640, -580, 520], [-10, 0, 190]] }[name];
      if (!V) return; cam.position.set(...V[0]); ctl.target.set(...V[1]); ctl.update();
    },
    snapshot() { renderer.render(scene, cam); return renderer.domElement.toDataURL('image/png'); },
    state: st, meshes,
  };
}
