/* Home hero: a real-time scene, drawn in the browser.
   Earth's night side at the bottom with the sunrise on its limb, a detailed
   satellite drifting in orbit, and its laser terminal holding a beam on a
   ground station in India while the body moves (that is what ZeroDrift does).
   Earth textures: NASA Blue Marble / Black Marble (public domain). */
import * as THREE from 'three';
import { EffectComposer } from './vendor/three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from './vendor/three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from './vendor/three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from './vendor/three/addons/postprocessing/OutputPass.js';

const canvas = document.getElementById('heroGL');
const stage = canvas && canvas.closest('.hero');
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
const params = new URLSearchParams(location.search);
const FIXED_T = params.has('herot') ? +params.get('herot') : null;   // for poster renders
// One scene, three shots: home (as designed), about (the camera comes down from
// space over India to Jabalpur), live (the satellite arrives from above).
const SHOT = (stage && stage.dataset.shot) || 'home';
// Home: the page opens on black; the Earth grows from a point into a whole globe, turns,
// and the camera glides down to the horizon; only then do the menu and the words appear.
// (index.html sets "zd-intro" on <html> when the page opens at the top.)
const HOME_INTRO = SHOT === 'home' && document.documentElement.classList.contains('zd-intro') && FIXED_T === null;
const INTRO = SHOT === 'home' ? 0 : 4.0;                             // about/live: fly-in seconds (after the Earth has loaded)
const GROW = 1.6, GLIDE = 2.8, HOME_END = GROW + GLIDE;              // home intro phases, seconds
const ease = x => { x = Math.min(1, Math.max(0, x)); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };   // smooth in and out

// Until the Earth textures are in, the hero stays black (no still, no half-loaded
// scene); then the fly-in starts and the text drops in (class "go").
const go = () => {
  if (stage) stage.classList.add('gl-on', 'go');
  const h = document.documentElement;
  if (h.classList.contains('zd-intro')) { h.classList.remove('zd-intro'); h.classList.add('zd-in'); }
};
if (canvas && stage) {
  if (FIXED_T === null) stage.classList.add('gl-wait');
  try { init(); } catch (e) { console.warn('hero3d:', e); stage.classList.remove('gl-wait'); go(); }
  setTimeout(() => { if (!stage.classList.contains('gl-on')) { stage.classList.remove('gl-wait'); go(); } }, 8000);   // Earth never loaded: show the still
}

function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
  renderer.setClearColor(0x000000, 1);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 16 / 9, 0.1, 4000);
  const manager = new THREE.LoadingManager();
  var t0 = performance.now();
  let texReady = false;
  manager.onLoad = () => { texReady = true; t0 = performance.now(); stage.classList.add('gl-on'); if (!HOME_INTRO) go(); if (FIXED_T !== null) requestAnimationFrame(frame); };
  // any scroll, click or key skips the home intro to its end
  let introDone = !HOME_INTRO;
  if (HOME_INTRO) {
    const skip = () => { if (!introDone && texReady) t0 = Math.min(t0, performance.now() - HOME_END * 1000); };
    ['wheel', 'touchstart', 'keydown', 'pointerdown'].forEach(ev => addEventListener(ev, skip, { passive: true }));
  }
  const loader = new THREE.TextureLoader(manager);
  const maxAniso = renderer.capabilities.getMaxAnisotropy();

  /* ---------------- environment for metal reflections ---------------- */
  const pmrem = new THREE.PMREMGenerator(renderer);
  {
    const envScene = new THREE.Scene();
    const envMat = new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false,
      uniforms: {},
      vertexShader: 'varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
      fragmentShader: `varying vec3 vD;
        void main(){
          vec3 d = normalize(vD);
          vec3 c = vec3(0.0);
          c += vec3(0.05,0.12,0.26) * smoothstep(0.1,-0.6,d.y) * 1.6;          // earth below: blue
          c += vec3(1.0,0.8,0.56) * pow(max(dot(d, normalize(vec3(-0.75,0.35,0.45))),0.0), 60.0) * 9.0;  // sun
          c += vec3(1.0,0.6,0.3) * pow(max(dot(d, normalize(vec3(-0.9,-0.12,-0.3))),0.0), 12.0) * 1.2;   // sunrise glow on the limb
          c += vec3(0.5,0.55,0.62) * 0.04;
          gl_FragColor = vec4(c,1.0);
        }`
    });
    envScene.add(new THREE.Mesh(new THREE.SphereGeometry(10, 48, 24), envMat));
    scene.environment = pmrem.fromScene(envScene, 0.02).texture;
  }

  /* ---------------- lights (satellite only; Earth has its own shader) ---------------- */
  const key = new THREE.DirectionalLight(0xfff0dc, 3.4); key.position.set(-7, 5, 7); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffb070, 2.6); rim.position.set(-9, -1.5, -8); scene.add(rim);
  const fill = new THREE.HemisphereLight(0x0a0f18, 0x21456f, 0.9); scene.add(fill);

  /* ---------------- Earth: NASA Blue Marble, relief, ocean glint, moving clouds ---------------- */
  const R = 34;
  const EARTH_C = new THREE.Vector3(-2, -R - 4.2, -28);
  const SUN = new THREE.Vector3(-0.8, 0.46, 0.22).normalize();         // from the upper left: day side faces us, night on the right
  const dayTex = loader.load('media/site/earth_day.jpg');
  const nightTex = loader.load('media/site/earth_night.jpg');
  const dataTex = loader.load('media/site/earth_data.jpg');           // R relief · G ocean mask · B clouds
  [dayTex, nightTex].forEach(t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = maxAniso; });
  dataTex.anisotropy = maxAniso; dataTex.wrapS = THREE.RepeatWrapping;
  const earthU = { dayMap: { value: dayTex }, nightMap: { value: nightTex }, dataMap: { value: dataTex }, sunDir: { value: SUN },
    northW: { value: new THREE.Vector3(0, 1, 0) }, cloudShift: { value: 0 } };
  const earthMat = new THREE.ShaderMaterial({
    uniforms: earthU,
    vertexShader: `varying vec2 vUv; varying vec3 vN; varying vec3 vW;
      void main(){ vUv = uv; vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix*vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix*viewMatrix*w; }`,
    fragmentShader: `uniform sampler2D dayMap, nightMap, dataMap; uniform vec3 sunDir, northW; uniform float cloudShift;
      varying vec2 vUv; varying vec3 vN; varying vec3 vW;
      void main(){
        vec3 n = normalize(vN);
        vec3 V = normalize(cameraPosition - vW);
        // relief: bend the normal along the height map's slope
        vec3 east = normalize(cross(northW, n)); vec3 north = cross(n, east);
        vec2 e = vec2(1.0/4096.0, 1.0/2048.0);
        float hx = texture2D(dataMap, vUv + vec2(e.x,0.)).r - texture2D(dataMap, vUv - vec2(e.x,0.)).r;
        float hy = texture2D(dataMap, vUv + vec2(0.,e.y)).r - texture2D(dataMap, vUv - vec2(0.,e.y)).r;
        vec3 nb = normalize(n - 1.6 * (hx * east + hy * north));
        vec4 d = texture2D(dataMap, vUv);
        float water = smoothstep(0.35, 0.65, d.g);
        vec2 cuv = vUv + vec2(cloudShift, 0.0);
        float cloud = smoothstep(0.06, 0.85, texture2D(dataMap, cuv).b);
        float cshadow = smoothstep(0.06, 0.85, texture2D(dataMap, cuv + sunDir.xz * 0.0015).b);
        float ndl0 = dot(n, sunDir), ndl = dot(nb, sunDir);
        float day = smoothstep(-0.10, 0.20, ndl0);

        vec3 dayC = texture2D(dayMap, vUv).rgb;
        dayC = mix(dayC, dayC * vec3(0.78, 0.95, 1.22), water);          // deeper, bluer oceans
        vec3 col = dayC * (max(ndl, 0.0) * 1.85 + 0.015);
        col *= 1.0 - 0.38 * cshadow * day;                               // cloud shadows on the ground
        vec3 H = normalize(sunDir + V); float nh = max(dot(n, H), 0.0);
        col += vec3(1.0, 0.94, 0.82) * (pow(nh, 160.0) * 3.0 + pow(nh, 22.0) * 0.14) * water * day * (1.0 - cloud);
        vec3 cloudC = vec3(1.0, 1.0, 1.02) * (max(ndl0, 0.0) * 1.45 + 0.012);
        col = mix(col, cloudC, cloud * 0.95 * smoothstep(-0.2, 0.1, ndl0));

        vec3 night = texture2D(nightMap, vUv).rgb;
        float lum = dot(night, vec3(0.3, 0.5, 0.2));
        col += vec3(1.0, 0.76, 0.45) * pow(lum, 1.3) * 4.2 * (1.0 - day) * (1.0 - cloud * 0.85);

        // atmosphere seen through: blue haze that thickens towards the limb
        float ndv = max(dot(n, V), 0.0);
        float haze = pow(1.0 - ndv, 2.4);
        float litA = smoothstep(-0.25, 0.4, ndl0);
        col = mix(col, vec3(0.36, 0.62, 1.0) * (0.12 + 1.35 * max(ndl0, 0.0)), haze * 0.78 * litA);
        col += vec3(0.05, 0.12, 0.3) * haze * litA;
        gl_FragColor = vec4(col, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`
  });
  const earth = new THREE.Mesh(new THREE.SphereGeometry(R, 256, 160), earthMat);
  earth.position.copy(EARTH_C);
  scene.add(earth);

  // atmosphere: two shades of blue above the limb (a thin bright line and a broad soft halo)
  const halo = new THREE.Mesh(new THREE.SphereGeometry(R * 1.07, 192, 128), new THREE.ShaderMaterial({
    uniforms: { center: { value: EARTH_C }, R: { value: R }, sunDir: { value: SUN } },
    side: THREE.BackSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: 'varying vec3 vW; void main(){ vec4 w = modelMatrix*vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix*viewMatrix*w; }',
    fragmentShader: `uniform vec3 center, sunDir; uniform float R; varying vec3 vW;
      void main(){
        vec3 rd = normalize(vW - cameraPosition);
        vec3 oc = center - cameraPosition; float tca = dot(oc, rd);
        vec3 p = cameraPosition + rd * tca; float b = length(p - center);
        float x = max(b - R, 0.0) / R;                        // height of the ray's closest point, in Earth radii
        float inner = exp(-x * 520.0);                         // shade 1: thin bright line hugging the limb
        float mid = exp(-x * 150.0);
        float outer = exp(-x * 30.0) * smoothstep(0.069, 0.035, x);   // shade 2: soft deep-blue glow radiating upwards
        vec3 up = normalize(p - center);
        float lit = smoothstep(-0.45, 0.6, dot(up, sunDir));
        vec3 c = vec3(0.78, 0.93, 1.0) * inner * 1.5 + vec3(0.3, 0.62, 1.0) * mid * 0.6 + vec3(0.1, 0.32, 0.98) * outer * 0.55;
        gl_FragColor = vec4(c * (0.08 + 1.05 * lit), 1.0);
      }`
  }));
  halo.position.copy(EARTH_C);
  scene.add(halo);

  // the ground terminal the beam holds on (India at the start; Earth turns slowly beneath it)
  const STATION_DIR = new THREE.Vector3(0.16, 0.975, 0.16).normalize();
  const lon = THREE.MathUtils.degToRad(SHOT === 'about' ? 79.95 : 79), lat = THREE.MathUtils.degToRad(SHOT === 'about' ? 23.18 : 21);   // about: Jabalpur
  const india = new THREE.Vector3(Math.cos(lat) * Math.cos(lon), Math.sin(lat), -Math.cos(lat) * Math.sin(lon));
  const baseQ = new THREE.Quaternion().setFromUnitVectors(india, STATION_DIR);
  earth.quaternion.copy(baseQ);
  const station = EARTH_C.clone().add(STATION_DIR.clone().multiplyScalar(R * 1.001));
  const SPIN = 0.0045;                                                 // rad/s
  const spinQ = new THREE.Quaternion(), Y = new THREE.Vector3(0, 1, 0);

  /* ---------------- stars: few, small, slowly drifting down ---------------- */
  const starGeo = new THREE.BufferGeometry();
  const N = 520, pos = new Float32Array(N * 3), sz = new Float32Array(N), ph = new Float32Array(N);
  let rs = 7;
  const rnd = () => (rs = (rs * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < N; i++) {
    const u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, r = 900;
    const y = Math.abs(u) * 0.95 + 0.05;
    const s = Math.sqrt(1 - y * y);
    pos.set([r * s * Math.cos(th), r * (y * 0.8 - 0.1), -Math.abs(r * s * Math.sin(th)) - 200], i * 3);
    const b = rnd();
    sz[i] = b > 0.985 ? 2.6 : b > 0.9 ? 1.7 : 1.0;
    ph[i] = rnd() * 6.28;
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  starGeo.setAttribute('size', new THREE.BufferAttribute(sz, 1));
  starGeo.setAttribute('phase', new THREE.BufferAttribute(ph, 1));
  const starMat = new THREE.ShaderMaterial({
    uniforms: { t: { value: 0 }, dpr: { value: 1 } },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float size; attribute float phase; uniform float t; uniform float dpr; varying float vA;
      void main(){ vA = (0.55 + 0.45 * sin(t * 1.3 + phase)) * (size > 2.0 ? 1.0 : size > 1.5 ? 0.75 : 0.45);
        gl_PointSize = size * dpr; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `varying float vA; void main(){ float d = length(gl_PointCoord - 0.5); float a = smoothstep(0.5, 0.0, d); gl_FragColor = vec4(vec3(0.86,0.9,1.0) * a * vA, 1.0); }`
  });
  const stars = new THREE.Points(starGeo, starMat);
  scene.add(stars);

  /* ---------------- satellite ---------------- */
  const sat = buildSatellite(scene.environment);
  scene.add(sat.group);

  /* ---------------- laser beam (camera-facing ribbon) ---------------- */
  const beamGeo = new THREE.BufferGeometry();
  beamGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(12), 3));
  beamGeo.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 0, 1, 1, 1]), 2));
  beamGeo.setIndex([0, 1, 2, 2, 1, 3]);
  const beamMat = new THREE.ShaderMaterial({
    uniforms: { t: { value: 0 } }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }',
    fragmentShader: `uniform float t; varying vec2 vUv;
      void main(){
        float x = abs(vUv.x - 0.5) * 2.0;
        float core = exp(-x * x * 90.0);
        float glow = exp(-x * x * 7.0) * 0.28;
        float along = vUv.y;                                     // 0 at the terminal, 1 at the ground
        float pulses = 0.55 + 0.45 * smoothstep(0.55, 1.0, sin((along * 26.0 - t * 5.0)));
        float fade = smoothstep(0.0, 0.03, along) * (1.0 - smoothstep(0.93, 1.0, along) * 0.6);
        vec3 c = vec3(0.35,1.0,0.62) * glow * pulses + vec3(0.85,1.0,0.9) * core * (0.75 + 0.25 * pulses);
        gl_FragColor = vec4(c * fade * 1.25, 1.0);
      }`
  });
  const beam = new THREE.Mesh(beamGeo, beamMat);
  beam.frustumCulled = false;
  scene.add(beam);
  const glowTex = radialTexture([[0, 'rgba(230,255,240,1)'], [0.12, 'rgba(120,255,170,.85)'], [0.4, 'rgba(60,220,120,.18)'], [1, 'rgba(40,200,100,0)']]);
  const emit = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  emit.scale.setScalar(0.55); scene.add(emit);
  const spot = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: .9 }));
  scene.add(spot);

  /* ---------------- post ---------------- */
  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(512, 512), 0.55, 0.5, 0.86);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  /* ---------------- layout ---------------- */
  let W = 0, H = 0, wide = true;
  const size = () => {
    const r = stage.getBoundingClientRect();
    W = Math.max(1, Math.round(r.width)); H = Math.max(1, Math.round(r.height));
    const dpr = Math.min(window.devicePixelRatio || 1, W > 1400 ? 1.5 : 1.75);
    renderer.setPixelRatio(dpr); renderer.setSize(W, H, false);
    composer.setPixelRatio(dpr); composer.setSize(W, H);
    starMat.uniforms.dpr.value = dpr;
    camera.aspect = W / H;
    wide = W / H > 1.05;
    camera.fov = wide ? 30 : 44;
    camera.updateProjectionMatrix();
  };
  size();
  new ResizeObserver(size).observe(stage);

  const mouse = { x: 0, y: 0, sx: 0, sy: 0 };
  window.addEventListener('pointermove', e => { mouse.x = e.clientX / innerWidth - 0.5; mouse.y = e.clientY / innerHeight - 0.5; }, { passive: true });

  /* ---------------- animate ---------------- */
  const tmpA = new THREE.Vector3(), tmpB = new THREE.Vector3(), side = new THREE.Vector3(), toCam = new THREE.Vector3();
  let visible = true, running = false, last = 0, clockOn = false, lastNow = 0;
  const frame = now => {
    running = visible && !document.hidden;
    if (!running) return;
    // The clock starts once the Earth has loaded, and a very slow frame (first texture
    // upload, a busy laptop) pauses it instead of skipping the intro.
    if (texReady && !clockOn) { clockOn = true; t0 = now; }
    else if (clockOn && now - lastNow > 400) t0 += now - lastNow - 50;
    lastNow = now;
    const t = FIXED_T !== null ? FIXED_T : clockOn ? (now - t0) / 1000 : 0;
    mouse.sx += (mouse.x - mouse.sx) * 0.04; mouse.sy += (mouse.y - mouse.sy) * 0.04;
    const sc = Math.min(1, Math.max(0, window.scrollY / Math.max(1, H)));

    // camera: slow push-in + pointer parallax + scroll rise
    const up = INTRO ? 1 - ease(t / INTRO) : 0;                      // 1 -> 0 during the fly-in (about/live)
    const cx = wide ? 0 : 0.6, cz = wide ? 15.5 : 19;
    const hi = SHOT === 'live' ? up * 2.5 : up * 15;                 // about: start high above, looking down
    camera.position.set(cx + mouse.sx * 0.9, 0.35 - mouse.sy * 0.5 + sc * 1.4 + hi, cz - Math.min(t, 40) * 0.012 + up * 4);
    tmpA.set(cx * 0.6 + mouse.sx * 0.25, 0.15 + sc * 1.1 - (SHOT === 'live' ? 0 : up * 10), 0);
    let hk = 1;                                                      // home: 0 = whole globe, 1 = hero view
    if (HOME_INTRO && t < HOME_END) {
      const g1 = ease(Math.min(1, t / GROW) * 0.5 + 0.5) * 2 - 1;   // ease-out: the globe grows from a point
      const dist = Math.exp(Math.log(2600) + (Math.log(wide ? 150 : 175) - Math.log(2600)) * g1);
      hk = ease((t - GROW) / GLIDE);
      tmpB.set(0, 0.07, 1).normalize().multiplyScalar(dist).add(EARTH_C);   // far camera, square on the globe
      camera.position.lerp(tmpB, 1 - hk);
      tmpA.lerp(EARTH_C, 1 - hk);
    } else if (HOME_INTRO && !introDone) { introDone = true; go(); }
    camera.lookAt(tmpA);
    stars.position.set(camera.position.x, camera.position.y - 0.35, camera.position.z - cz);   // stars stay at infinity

    // satellite: drifts along its orbit, body sways, arrays track the sun
    const g = sat.group;
    const drift = Math.sin(t * 0.085) * 0.45;
    if (SHOT === 'about') {                                         // small and far: the Earth is the subject
      g.position.set(wide ? 5.4 + drift * 0.6 : 1.4 + drift * 0.4, wide ? 2.7 + Math.sin(t * 0.13) * 0.1 : 4.4, -7);
      g.scale.setScalar(0.62);
    } else if (SHOT === 'live') {                                   // close, and it arrives from above
      g.position.set(wide ? 5.3 + drift * 0.5 : 0.9 + drift * 0.4, (wide ? 1.55 + Math.sin(t * 0.13) * 0.12 : 4.4) + up * 7, wide ? 1.6 : 0);
      g.scale.setScalar(wide ? 0.9 : 0.85);
    } else {
      // home: after the camera settles, the satellite glides in from the middle of the screen
      const k = HOME_INTRO ? ease((t - GROW - GLIDE * 0.45) / (GLIDE * 0.75)) : 1;
      beam.visible = emit.visible = spot.visible = k > 0.35;
      g.position.set(wide ? 4.15 + drift * 0.8 : 0.9 + drift * 0.5, wide ? 1.45 + Math.sin(t * 0.13) * 0.12 : 3.4, wide ? 0 : -1);
      g.position.lerp(tmpB.set(0, 1.1, -14), 1 - k);
      g.scale.setScalar(0.8 * (0.25 + 0.75 * k));
    }
    g.rotation.set(0.32 + Math.sin(t * 0.11) * 0.05, -0.72 + Math.sin(t * 0.07) * 0.16 + (SHOT === 'live' ? up * 1.4 : 0), 0.12 + Math.sin(t * 0.09) * 0.04);
    sat.wings.forEach(w => { w.rotation.x = 0.35 + Math.sin(t * 0.05) * 0.08; });
    g.updateMatrixWorld(true);

    // terminal keeps the beam on the station whatever the body does
    sat.head.lookAt(station);
    sat.lens.getWorldPosition(tmpA);
    tmpB.copy(station);
    emit.position.copy(tmpA);
    spot.position.copy(tmpB).addScaledVector(STATION_DIR, 0.05);
    spot.scale.setScalar(1.4 + 0.25 * Math.sin(t * 6.0));
    // ribbon facing the camera
    const axis = tmpB.clone().sub(tmpA);
    toCam.copy(camera.position).sub(tmpA);
    side.crossVectors(axis, toCam).normalize();
    const w0 = 0.07, w1 = 0.5;
    const P = beamGeo.attributes.position.array;
    const a0 = tmpA.clone().addScaledVector(side, -w0), a1 = tmpA.clone().addScaledVector(side, w0);
    const b0 = tmpB.clone().addScaledVector(side, -w1), b1 = tmpB.clone().addScaledVector(side, w1);
    P.set([a0.x, a0.y, a0.z, a1.x, a1.y, a1.z, b0.x, b0.y, b0.z, b1.x, b1.y, b1.z]);
    beamGeo.attributes.position.needsUpdate = true;
    beamMat.uniforms.t.value = t;

    // Earth: a hint of rotation; stars drift slowly downward
    spinQ.setFromAxisAngle(Y, (t - 12) * SPIN - (HOME_INTRO ? 1.3 * (1 - ease(t / HOME_END)) : 0));   // the globe turns India into place
    earth.quaternion.copy(baseQ).multiply(spinQ);
    earthU.northW.value.copy(Y).applyQuaternion(earth.quaternion);
    earthU.cloudShift.value = t * 0.0009;
    stars.rotation.x = -t * 0.0016;
    starMat.uniforms.t.value = t;

    composer.render();
    last = now;
    if (FIXED_T === null && !still) requestAnimationFrame(frame);
    else if (texReady) canvas.dataset.ready = '1';
  };
  const kick = () => { if (!running && visible && !document.hidden) requestAnimationFrame(frame); };
  new IntersectionObserver(es => { visible = es[0].isIntersecting; kick(); }, { threshold: 0 }).observe(stage);
  document.addEventListener('visibilitychange', kick);
  requestAnimationFrame(t => frame(t));
}

/* ---------------------------------------------------------------- helpers */
function radialTexture(stops) {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'), g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
  stops.forEach(([o, col]) => g.addColorStop(o, col));
  x.fillStyle = g; x.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function streakTexture() {
  const c = document.createElement('canvas'); c.width = 512; c.height = 32;
  const x = c.getContext('2d');
  const g = x.createLinearGradient(0, 0, 512, 0);
  g.addColorStop(0, 'rgba(255,170,90,0)'); g.addColorStop(0.5, 'rgba(255,225,190,1)'); g.addColorStop(1, 'rgba(255,170,90,0)');
  x.fillStyle = g; x.fillRect(0, 0, 512, 32);
  const v = x.createLinearGradient(0, 0, 0, 32);
  v.addColorStop(0, 'rgba(0,0,0,1)'); v.addColorStop(0.5, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,1)');
  x.globalCompositeOperation = 'destination-out'; x.fillStyle = v; x.fillRect(0, 0, 512, 32);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function canvasTex(w, h, draw, srgb = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

/* Gold multi-layer insulation: crumpled foil. Each facet gets its own random normal,
   so the foil breaks the light into many small reflections, like the real thing. */
function foilTextures() {
  let s = 11; const r = () => (s = (s * 16807) % 2147483647) / 2147483647;
  const facets = [];
  for (let i = 0; i < 1400; i++) facets.push([r() * 512, r() * 512, 10 + r() * 30, r() * 6.28, r(), r(), r()]);
  const poly = (x, px, py, sz, a) => { x.beginPath(); for (let k = 0; k < 5; k++) { const aa = a + k * 1.2566 + Math.sin(k * 3.1 + a) * 0.35, rr = sz * (0.7 + 0.3 * Math.sin(a * 5 + k)); x.lineTo(px + Math.cos(aa) * rr, py + Math.sin(aa) * rr); } x.closePath(); };
  const color = canvasTex(512, 512, (x, w, h) => {
    x.fillStyle = '#c7962f'; x.fillRect(0, 0, w, h);
    facets.forEach(([px, py, sz, a, v]) => { x.fillStyle = `hsl(${39 + v * 6}, ${72 + v * 10}%, ${46 + v * 14}%)`; poly(x, px, py, sz, a); x.fill(); });
  });
  const normal = canvasTex(512, 512, (x, w, h) => {
    x.fillStyle = 'rgb(128,128,255)'; x.fillRect(0, 0, w, h);
    facets.forEach(([px, py, sz, a, , u, v]) => {
      const tilt = 0.12 + u * 0.42, dir = v * 6.283;
      const nx = Math.sin(tilt) * Math.cos(dir), ny = Math.sin(tilt) * Math.sin(dir), nz = Math.cos(tilt);
      x.fillStyle = `rgb(${(nx * 0.5 + 0.5) * 255 | 0},${(ny * 0.5 + 0.5) * 255 | 0},${(nz * 0.5 + 0.5) * 255 | 0})`;
      poly(x, px, py, sz, a); x.fill();
    });
    x.strokeStyle = 'rgba(128,128,255,.9)'; x.lineWidth = 1.2;
    facets.slice(0, 500).forEach(([px, py, sz, a]) => { poly(x, px, py, sz, a); x.stroke(); });
  }, false);
  const rough = canvasTex(256, 256, (x, w, h) => {
    x.fillStyle = '#3c3c3c'; x.fillRect(0, 0, w, h);
    for (let i = 0; i < 500; i++) { const v = 30 + r() * 80 | 0; x.fillStyle = `rgb(${v},${v},${v})`; x.fillRect(r() * w, r() * h, 6 + r() * 22, 6 + r() * 22); }
  }, false);
  return { color, normal, rough };
}

/* Solar cells: dark blue cells, silver bus bars, fine fingers. */
function cellTexture() {
  return canvasTex(1024, 512, (x, w, h) => {
    x.fillStyle = '#c9ccd2'; x.fillRect(0, 0, w, h);
    const cols = 12, rows = 6, gx = 3, gy = 3;
    const cw = (w - gx * (cols + 1)) / cols, ch = (h - gy * (rows + 1)) / rows;
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
      const X = gx + i * (cw + gx), Y = gy + j * (ch + gy);
      const g = x.createLinearGradient(X, Y, X + cw, Y + ch);
      const v = (i * 7 + j * 3) % 5;
      g.addColorStop(0, `rgb(${14 + v},${26 + v * 2},${70 + v * 4})`); g.addColorStop(1, `rgb(${10 + v},${18 + v},${48 + v * 3})`);
      x.fillStyle = g; x.fillRect(X, Y, cw, ch);
      x.fillStyle = 'rgba(190,200,215,.55)';
      for (let k = 1; k < 3; k++) x.fillRect(X + cw * k / 3 - 1, Y, 2, ch);
      x.fillStyle = 'rgba(160,175,200,.16)';
      for (let k = 1; k < 16; k++) x.fillRect(X, Y + ch * k / 16, cw, 1);
    }
  });
}

function buildSatellite(envMap) {
  const group = new THREE.Group();
  const body = new THREE.Group(); group.add(body);
  const foil = foilTextures();
  [foil.color, foil.normal, foil.rough].forEach(tx => tx.repeat.set(1.3, 1.3));
  const mFoil = new THREE.MeshPhysicalMaterial({ map: foil.color, normalMap: foil.normal, normalScale: new THREE.Vector2(1.1, 1.1), roughnessMap: foil.rough, roughness: 0.5, metalness: 1, envMapIntensity: 1.25 });
  const mWhite = new THREE.MeshStandardMaterial({ color: 0xe9ebee, roughness: 0.55, metalness: 0.05 });
  const mAlu = new THREE.MeshStandardMaterial({ color: 0xc8ccd2, roughness: 0.28, metalness: 1, envMapIntensity: 1.4 });
  const mDark = new THREE.MeshStandardMaterial({ color: 0x17191d, roughness: 0.38, metalness: 0.75, envMapIntensity: 1.1 });
  const mBlack = new THREE.MeshStandardMaterial({ color: 0x050506, roughness: 0.9, metalness: 0 });
  const cell = cellTexture();
  const mCell = new THREE.MeshPhysicalMaterial({ map: cell, metalness: 0.35, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.08, envMapIntensity: 1.5 });
  const mCellBack = new THREE.MeshStandardMaterial({ color: 0x9aa0a8, roughness: 0.6, metalness: 0.3 });

  const box = (w, h, d, m) => new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  const cyl = (rt, rb, h, m, seg = 32, open = false) => new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg, 1, open), m);

  // bus: foil sides, white radiators top and bottom, aluminium frame edges
  const BW = 1.5, BH = 1.25, BD = 1.25;
  const osr = canvasTex(512, 512, (x, w, h) => {
    x.fillStyle = '#6d7079'; x.fillRect(0, 0, w, h);
    const n = 12, g = 3, c = (w - g * (n + 1)) / n;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) { const v = 118 + ((i * 13 + j * 7) % 9) * 6; x.fillStyle = `rgb(${v},${v + 2},${v + 6})`; x.fillRect(g + i * (c + g), g + j * (c + g), c, c); }
  });
  const mOSR = new THREE.MeshPhysicalMaterial({ map: osr, metalness: 1, roughness: 0.16, envMapIntensity: 0.55, clearcoat: 1 });
  const mBlackMLI = new THREE.MeshStandardMaterial({ color: 0x141416, roughness: 0.55, metalness: 0.4, normalMap: foil.normal, normalScale: new THREE.Vector2(0.6, 0.6) });
  const busMats = [mFoil, mFoil, mWhite, mWhite, mFoil, mBlackMLI];
  const bus = new THREE.Mesh(new THREE.BoxGeometry(BW, BH, BD, 1, 1, 1), busMats);
  body.add(bus);
  const rad = new THREE.Mesh(new THREE.PlaneGeometry(BW * 0.78, BH * 0.7), mOSR); rad.position.set(0, 0.04, BD / 2 + 0.004); body.add(rad);
  const radB = new THREE.Mesh(new THREE.PlaneGeometry(BW * 0.78, BH * 0.7), mOSR); radB.position.set(0, 0.04, -BD / 2 - 0.004); radB.rotation.y = Math.PI; body.add(radB);
  // harness and small boxes on the gold faces
  for (let i = 0; i < 3; i++) { const m = box(0.02, 0.16 + i * 0.05, 0.22, mDark); m.position.set(BW / 2 + 0.01, -0.3 + i * 0.28, -0.2 + i * 0.15); body.add(m); }
  const e = 0.035;
  [[BW, e, e, 0, 1, 1], [BW, e, e, 0, 1, -1], [BW, e, e, 0, -1, 1], [BW, e, e, 0, -1, -1]].forEach(([w, h, d, , sy, sz]) => { const m = box(w + e, h, d, mAlu); m.position.set(0, sy * BH / 2, sz * BD / 2); body.add(m); });
  [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([sx, sz]) => { const m = box(e, BH + e, e, mAlu); m.position.set(sx * BW / 2, 0, sz * BD / 2); body.add(m); });
  [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([sx, sy]) => { const m = box(e, e, BD + e, mAlu); m.position.set(sx * BW / 2, sy * BH / 2, 0); body.add(m); });
  // radiator louvres on the top face
  for (let i = 0; i < 7; i++) { const m = box(0.16, 0.012, 0.9, mAlu); m.position.set(-0.55 + i * 0.18, BH / 2 + 0.01, 0); body.add(m); }
  // launch adapter ring at the back
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.045, 12, 48), mAlu); ring.position.set(0, 0, -BD / 2 - 0.05); body.add(ring);
  const cone = cyl(0.42, 0.5, 0.12, mDark, 48, true); cone.rotation.x = Math.PI / 2; cone.position.set(0, 0, -BD / 2 - 0.02); body.add(cone);
  // thrusters
  [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([sx, sz]) => { const n = cyl(0.02, 0.055, 0.1, mDark, 16); n.position.set(sx * (BW / 2 - 0.1), -BH / 2 - 0.05, sz * (BD / 2 - 0.1)); body.add(n); });
  // star trackers with black baffles
  [[-0.45, 0.35], [-0.2, 0.52]].forEach(([x, z], i) => {
    const st = new THREE.Group();
    const b = cyl(0.07, 0.09, 0.22, mDark, 24); st.add(b);
    const baf = cyl(0.12, 0.08, 0.16, mBlack, 24, true); baf.position.y = 0.18; st.add(baf);
    st.position.set(x, BH / 2 + 0.12, z); st.rotation.set(0.5 + i * 0.2, 0, 0.3 - i * 0.5); body.add(st);
  });
  // omni antennas
  [[0.62, 0.55], [-0.62, -0.5]].forEach(([x, z]) => { const a = cyl(0.008, 0.008, 0.5, mAlu, 8); a.position.set(x, BH / 2 + 0.25, z); body.add(a); const k = new THREE.Mesh(new THREE.SphereGeometry(0.025, 12, 8), mAlu); k.position.set(x, BH / 2 + 0.5, z); body.add(k); });

  // high-gain dish on a short boom (top, towards the back)
  const dish = new THREE.Group();
  const pts = []; for (let i = 0; i <= 24; i++) { const r = 0.62 * i / 24; pts.push(new THREE.Vector2(r, r * r * 0.55)); }
  const dMesh = new THREE.Mesh(new THREE.LatheGeometry(pts, 64), new THREE.MeshStandardMaterial({ color: 0xe6e6e3, roughness: 0.82, metalness: 0.0, envMapIntensity: 0.35, side: THREE.DoubleSide }));
  dish.add(dMesh);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.012, 8, 64), mAlu); rim.rotation.x = Math.PI / 2; rim.position.y = 0.62 * 0.62 * 0.55; dish.add(rim);
  const feed = cyl(0.035, 0.05, 0.1, mDark, 16); feed.position.y = 0.42; dish.add(feed);
  for (let k = 0; k < 3; k++) {
    const a = k * 2.094, p0 = new THREE.Vector3(Math.cos(a) * 0.6, 0.2, Math.sin(a) * 0.6), p1 = new THREE.Vector3(0, 0.4, 0);
    const len = p0.distanceTo(p1); const s = cyl(0.007, 0.007, len, mAlu, 6);
    s.position.copy(p0).add(p1).multiplyScalar(0.5); s.lookAt(p1); s.rotateX(Math.PI / 2); dish.add(s);
  }
  const boom = cyl(0.03, 0.03, 0.55, mAlu, 12); boom.position.y = -0.28; dish.add(boom);
  dish.position.set(0.35, BH / 2 + 0.55, -0.25); dish.rotation.set(-0.5, 0, 0.55); body.add(dish);

  // solar array wings
  const wings = [];
  [1, -1].forEach(sgn => {
    const yoke = new THREE.Group();
    yoke.position.set(sgn * BW / 2, 0, 0);
    const arm = cyl(0.025, 0.025, 0.7, mAlu, 12); arm.rotation.z = Math.PI / 2; arm.position.x = sgn * 0.35; yoke.add(arm);
    const drive = cyl(0.09, 0.09, 0.12, mDark, 24); drive.rotation.z = Math.PI / 2; drive.position.x = sgn * 0.06; yoke.add(drive);
    const wing = new THREE.Group(); wing.position.x = sgn * 0.72; yoke.add(wing);
    const PW = 1.38, PH = 1.02, gap = 0.07;
    for (let i = 0; i < 3; i++) {
      const panel = new THREE.Group();
      const front = new THREE.Mesh(new THREE.PlaneGeometry(PW, PH), mCell); front.position.y = 0.012; front.rotation.x = -Math.PI / 2; panel.add(front);
      const back = new THREE.Mesh(new THREE.PlaneGeometry(PW, PH), mCellBack); back.position.y = -0.012; back.rotation.x = Math.PI / 2; panel.add(back);
      const fr = [[PW + 0.03, 0.03, 0.03, 0, PH / 2], [PW + 0.03, 0.03, 0.03, 0, -PH / 2]];
      fr.forEach(([w, h, d, x, z]) => { const m = box(w, h, d, mAlu); m.position.set(x, 0, z); panel.add(m); });
      [PW / 2, -PW / 2].forEach(x => { const m = box(0.03, 0.03, PH, mAlu); m.position.set(x, 0, 0); panel.add(m); });
      panel.position.x = sgn * (PW / 2 + i * (PW + gap));
      wing.add(panel);
      if (i) { const h = cyl(0.02, 0.02, 0.2, mAlu, 8); h.rotation.x = Math.PI / 2; h.position.x = sgn * (i * (PW + gap) - gap / 2); wing.add(h); }
    }
    body.add(yoke);
    wings.push(wing);
  });

  // laser communication terminal: fork gimbal + telescope, on the Earth-facing face
  const term = new THREE.Group();
  term.position.set(-0.15, -BH / 2 - 0.02, 0.28);
  body.add(term);
  const base = cyl(0.2, 0.24, 0.08, mDark, 32); base.position.y = -0.04; term.add(base);
  const yaw = new THREE.Group(); yaw.position.y = -0.16; term.add(yaw);
  const head = new THREE.Group(); yaw.add(head);
  [-1, 1].forEach(sx => { const f = box(0.04, 0.26, 0.12, mAlu); f.position.set(sx * 0.2, 0.06, 0); yaw.add(f); });
  const tube = cyl(0.15, 0.15, 0.46, mDark, 40); tube.rotation.x = Math.PI / 2; tube.position.z = 0.06; head.add(tube);
  const shade = cyl(0.18, 0.155, 0.22, mBlack, 40, true); shade.rotation.x = Math.PI / 2; shade.position.z = 0.4; head.add(shade);
  const band = cyl(0.158, 0.158, 0.04, mAlu, 40); band.rotation.x = Math.PI / 2; band.position.z = -0.1; head.add(band);
  const glass = new THREE.Mesh(new THREE.CircleGeometry(0.135, 40), new THREE.MeshPhysicalMaterial({ color: 0x0a2a1a, emissive: 0x1bd36a, emissiveIntensity: 0.9, metalness: 0.2, roughness: 0.05, clearcoat: 1 }));
  glass.position.z = 0.3; head.add(glass);
  const lens = new THREE.Object3D(); lens.position.z = 0.32; head.add(lens);
  const axle = cyl(0.03, 0.03, 0.44, mAlu, 12); axle.rotation.z = Math.PI / 2; yaw.add(axle);

  group.scale.setScalar(1);
  return { group, wings, head, lens };
}
