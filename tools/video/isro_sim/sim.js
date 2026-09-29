import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

// ZeroDrift - end-to-end field simulation (illustrative), v2 graphics.
// Deterministic: seek(t) draws the frame at t seconds. Numbers on screen: docs/PROJECT_STATE.md section 2 only.

const W = 1920, H = 1080, DUR = 100, D2R = Math.PI / 180;
const Y = new THREE.Vector3(0, 1, 0);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ss = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const win = (t, a, b, f = .6) => ss(a, a + f, t) * (1 - ss(b - f, b, t));
const frac = x => x - Math.floor(x);
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function hash2(x, y) { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); }
function vn(x, y) { const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi), b = hash2(xi + 1, yi), c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1); return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v; }
function fbm(x, y) { let s = 0, a = .5, f = 1; for (let i = 0; i < 5; i++) { s += a * vn(x * f, y * f); f *= 2.03; a *= .5; } return s; }
const NOISE = `
float h3(vec3 p){p=fract(p*.3183099+.1);p*=17.;return fract(p.x*p.y*p.z*(p.x+p.y+p.z));}
float n3(vec3 x){vec3 i=floor(x),f=fract(x);f=f*f*(3.-2.*f);return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z);}
float fb(vec3 p){float s=0.,a=.5;for(int i=0;i<6;i++){s+=a*n3(p);p*=2.03;a*=.5;}return s;}
`;

// ---------------------------------------------------------------- renderer + post
const R = new THREE.WebGLRenderer({ canvas: document.getElementById('gl'), antialias: true, preserveDrawingBuffer: true });
R.setPixelRatio(1); R.setSize(W, H, false);
R.toneMapping = THREE.ACESFilmicToneMapping; R.toneMappingExposure = 1.05; R.outputColorSpace = THREE.SRGBColorSpace;
R.shadowMap.enabled = true; R.shadowMap.type = THREE.PCFSoftShadowMap;
const comp = new EffectComposer(R); comp.setPixelRatio(1); comp.setSize(W, H);
const rpass = new RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera()); comp.addPass(rpass);
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), .85, .6, .7); comp.addPass(bloom);
const film = new ShaderPass({ uniforms: { tDiffuse: { value: null }, time: { value: 0 }, ca: { value: 1 }, grain: { value: .03 } },
  vertexShader: `varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
  fragmentShader: `uniform sampler2D tDiffuse;uniform float time,ca,grain;varying vec2 vUv;
  float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233))+time*43.13)*43758.5453);}
  void main(){vec2 d=vUv-.5;float r2=dot(d,d);vec2 o=d*r2*.018*ca;
  vec3 c=vec3(texture2D(tDiffuse,vUv+o).r,texture2D(tDiffuse,vUv).g,texture2D(tDiffuse,vUv-o).b);
  float l=dot(c,vec3(.2126,.7152,.0722));
  c+=(h(vUv*vec2(1920.,1080.))-.5)*grain*(.15+sqrt(max(l,0.)));
  c=mix(c,c*vec3(1.035,1.,.95),smoothstep(.15,1.2,l));c+=vec3(0.,.0025,.007)*(1.-smoothstep(0.,.12,l));
  gl_FragColor=vec4(max(c,0.),1.);}` });
comp.addPass(film); comp.addPass(new OutputPass());
const pmrem = new THREE.PMREMGenerator(R);

const TL = new THREE.TextureLoader();
const loadTex = u => new Promise((res, rej) => TL.load(u, res, undefined, rej));
const loadImg = u => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = u; });
function canvasTex(w, h, draw, srgb = true) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; }
const DOT = canvasTex(64, 64, (x) => { const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(.18, 'rgba(255,255,255,.85)'); g.addColorStop(.45, 'rgba(255,255,255,.18)'); g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 64, 64); });
const MOON = canvasTex(256, 256, (x) => { const r = rng(5); const g = x.createRadialGradient(118, 116, 10, 128, 128, 120);
  g.addColorStop(0, '#fbf8ef'); g.addColorStop(.85, '#d6d0c0'); g.addColorStop(1, '#a9a495'); x.beginPath(); x.arc(128, 128, 118, 0, 7); x.fillStyle = g; x.fill();
  x.save(); x.clip(); for (let i = 0; i < 26; i++) { x.beginPath(); x.arc(40 + r() * 180, 40 + r() * 180, 6 + r() * 30, 0, 7); x.fillStyle = `rgba(90,88,80,${.06 + r() * .12})`; x.fill(); } x.restore(); });
const PANEL = canvasTex(512, 192, (x, w, h) => { const g = x.createLinearGradient(0, 0, w, h); g.addColorStop(0, '#12246a'); g.addColorStop(1, '#0a1640'); x.fillStyle = g; x.fillRect(0, 0, w, h);
  for (let i = 0; i < w; i += 32) for (let j = 0; j < h; j += 32) { x.fillStyle = `rgba(${40 + (i * 7 + j) % 30},${70 + (j * 3) % 40},${170 + (i % 50)},.9)`; x.fillRect(i + 2, j + 2, 28, 28); }
  x.strokeStyle = 'rgba(200,210,230,.6)'; x.lineWidth = 3; x.strokeRect(1, 1, w - 2, h - 2); });
const FOIL = canvasTex(512, 512, (x, w, h) => { const r = rng(3); x.fillStyle = '#a8772a'; x.fillRect(0, 0, w, h);
  for (let i = 0; i < 1400; i++) { const px = r() * w, py = r() * h, s = 10 + r() * 46, l = 110 + r() * 145; x.fillStyle = `rgba(${Math.min(255, l + 70)},${Math.min(255, l + 25)},${l * .3},${.25 + r() * .45})`;
    x.beginPath(); x.moveTo(px, py); x.lineTo(px + s * (r() - .5) * 2, py + s * r()); x.lineTo(px + s * (r() - .5) * 2, py - s * r()); x.fill(); } });
const DECAL = canvasTex(1024, 128, (x) => { x.clearRect(0, 0, 1024, 128); x.font = '700 76px "Bahnschrift","Segoe UI"'; x.fillStyle = '#123a7a'; x.fillText('ZERODRIFT', 10, 86);
  x.font = '500 40px "Bahnschrift","Segoe UI"'; x.fillStyle = '#2f6fc7'; x.fillText('MOBILE FSOC TERMINAL', 440, 84); });
function uiTex(locked) { return canvasTex(512, 320, (x, w, h) => { x.fillStyle = '#030b16'; x.fillRect(0, 0, w, h); x.fillStyle = '#0b2138'; x.fillRect(0, 0, w, 34);
  x.font = '700 18px Consolas'; x.fillStyle = '#4FC7EA'; x.fillText('ZERODRIFT  TRACKER', 12, 23); const r = rng(8);
  for (let i = 0; i < 90; i++) { x.fillStyle = `rgba(255,255,255,${.2 + r() * .6})`; x.fillRect(10 + r() * 330, 44 + r() * 230, 2, 2); }
  x.strokeStyle = locked ? '#5DE08A' : '#FFC85A'; x.lineWidth = 3; x.strokeRect(150, 120, 60, 60); x.beginPath(); x.arc(180, 150, 5, 0, 7); x.fillStyle = x.strokeStyle; x.fill();
  x.fillStyle = '#081a2c'; x.fillRect(354, 44, 150, 230); x.font = '700 20px Consolas'; x.fillStyle = locked ? '#5DE08A' : '#FFC85A'; x.fillText(locked ? 'LOCKED' : 'SEARCH', 368, 76);
  x.font = '16px Consolas'; x.fillStyle = '#9fb4cf'; x.fillText(locked ? '4.00 Hz' : 'scanning', 368, 102); x.fillText('AZ 23x.x', 368, 128); x.fillText('EL 5x.x', 368, 150);
  x.strokeStyle = '#5DE08A'; x.lineWidth = 2; x.beginPath(); for (let i = 0; i < 130; i++) x.lineTo(362 + i, 250 - (locked ? 10 + 6 * Math.sin(i * .4) : 50 + 20 * Math.sin(i * .2))); x.stroke();
  x.font = '14px Consolas'; x.fillStyle = '#4FC7EA'; x.fillText(locked ? 'BEACON  C1  VERIFIED' : 'CANDIDATES  5', 12, 300); }); }
const UI_SEARCH = uiTex(false), UI_LOCK = uiTex(true);

function starField(n, r, seed, hemi, sizeK = 1.6) {
  const g = new THREE.BufferGeometry(), p = new Float32Array(n * 3), c = new Float32Array(n * 3), s = new Float32Array(n), rr = rng(seed);
  for (let i = 0; i < n; i++) { let u = hemi ? Math.pow(rr(), .7) * 1.02 - .02 : rr() * 2 - 1; const th = rr() * Math.PI * 2, q = Math.sqrt(Math.max(0, 1 - u * u));
    p[i * 3] = r * q * Math.cos(th); p[i * 3 + 1] = r * u; p[i * 3 + 2] = r * q * Math.sin(th);
    const k = rr(), col = k < .14 ? [1, .82, .66] : k < .36 ? [.72, .84, 1] : [1, 1, 1], b = .35 + Math.pow(rr(), 3) * 1.8;
    c[i * 3] = col[0] * b; c[i * 3 + 1] = col[1] * b; c[i * 3 + 2] = col[2] * b; s[i] = 1 + Math.pow(rr(), 7) * 5.5; }
  g.setAttribute('position', new THREE.BufferAttribute(p, 3)); g.setAttribute('color', new THREE.BufferAttribute(c, 3)); g.setAttribute('size', new THREE.BufferAttribute(s, 1));
  const m = new THREE.ShaderMaterial({ uniforms: { map: { value: DOT }, op: { value: 1 } }, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float size;varying vec3 vC;void main(){vC=color;gl_PointSize=size*${sizeK.toFixed(2)};gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader: `uniform sampler2D map;uniform float op;varying vec3 vC;void main(){float a=texture2D(map,gl_PointCoord).a;gl_FragColor=vec4(vC*a*op,1.);}` });
  return new THREE.Points(g, m);
}
function beamMat(color, op, fres = 1.6, inv = 0) {
  return new THREE.ShaderMaterial({ uniforms: { col: { value: new THREE.Color(color) }, op: { value: op }, fres: { value: fres }, inv: { value: inv }, fade: { value: .8 }, time: { value: 0 } },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
    vertexShader: `varying vec3 vN;varying vec3 vW;varying float vY;void main(){vY=position.y;vN=normalize(mat3(modelMatrix)*normal);vec4 w=modelMatrix*vec4(position,1.);vW=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`,
    fragmentShader: `uniform vec3 col;uniform float op;uniform float fres;uniform float inv;uniform float fade;uniform float time;varying vec3 vN;varying vec3 vW;varying float vY;
      void main(){float f=abs(dot(normalize(vN),normalize(cameraPosition-vW)));f=mix(f,1.-f,inv);
      float sc=1.+.18*sin(vY*90.-time*9.)*sin(vY*37.+time*5.3);
      float a=pow(f,fres)*op*sc*smoothstep(0.,0.02,vY)*(1.-smoothstep(fade,1.,vY));gl_FragColor=vec4(col*a,1.);}` });
}
const CYL = new THREE.CylinderGeometry(1, 1, 1, 32, 1, true).translate(0, .5, 0);
const CONE = new THREE.ConeGeometry(1, 1, 72, 1, true).rotateX(Math.PI).translate(0, .5, 0);
function orient(m, start, dir, len, r) { m.position.copy(start); m.quaternion.setFromUnitVectors(Y, dir.clone().normalize()); m.scale.set(r, len, r); }
const mesh = (g, m) => new THREE.Mesh(g, m);
const sky = (frag) => new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
  vertexShader: `varying vec3 vD;void main(){vD=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`, fragmentShader: frag });

// ---------------------------------------------------------------- SPACE scene
const SPACE = new THREE.Scene();
const camS = new THREE.PerspectiveCamera(40, W / H, .0005, 900);
const sunL = new THREE.DirectionalLight(0xfff4e6, 3.6); SPACE.add(sunL); SPACE.add(new THREE.AmbientLight(0x3a4660, .22));
SPACE.add(starField(11000, 400, 11, false));
const earthG = new THREE.Group(); SPACE.add(earthG);
const eMat = new THREE.ShaderMaterial({ uniforms: { day: { value: null }, night: { value: null }, sun: { value: new THREE.Vector3(1, 0, 0) } },
  vertexShader: `varying vec2 vUv;varying vec3 vN;varying vec3 vW;void main(){vUv=uv;vN=normalize(mat3(modelMatrix)*normal);vec4 w=modelMatrix*vec4(position,1.);vW=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`,
  fragmentShader: `uniform sampler2D day;uniform sampler2D night;uniform vec3 sun;varying vec2 vUv;varying vec3 vN;varying vec3 vW;
  void main(){vec3 N=normalize(vN);vec3 V=normalize(cameraPosition-vW);float d=dot(N,sun);
  vec3 dc=texture2D(day,vUv).rgb;vec3 nc=texture2D(night,vUv).rgb;
  float dayK=smoothstep(-.06,.22,d);
  vec3 col=dc*(.015+1.3*max(d,0.))*dayK;
  col+=nc*vec3(1.,.76,.46)*2.6*(1.-smoothstep(-.22,.04,d));
  float ocean=smoothstep(.015,.10,dc.b-dc.r);
  vec3 Hh=normalize(sun+V);col+=vec3(1.,.9,.75)*pow(max(dot(N,Hh),0.),60.)*1.1*ocean*dayK;
  float fr=pow(1.-max(dot(N,V),0.),3.);
  vec3 air=mix(vec3(1.,.45,.2),vec3(.28,.58,1.),smoothstep(-.05,.35,d));
  col+=air*fr*(.08+1.15*smoothstep(-.3,.45,d));
  col+=vec3(1.,.5,.2)*.035*exp(-pow(d/.12,2.))*(1.-fr);
  gl_FragColor=vec4(col,1.);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
  }` });
earthG.add(mesh(new THREE.SphereGeometry(1, 192, 192), eMat));
const cloudMat = new THREE.ShaderMaterial({ uniforms: { sun: eMat.uniforms.sun, time: { value: 0 } }, transparent: true, depthWrite: false,
  vertexShader: `varying vec3 vP;varying vec3 vN;void main(){vP=normalize(position);vN=normalize(mat3(modelMatrix)*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
  fragmentShader: NOISE + `uniform vec3 sun;uniform float time;varying vec3 vP;varying vec3 vN;
  void main(){vec3 p=vP*3.4+vec3(time*.006,0.,time*.002);float n=fb(p)*.62+fb(p*3.3+7.)*.38;float lat=abs(vP.y);
  float cov=smoothstep(.52,.74,n+.07*sin(lat*10.))*(.55+.45*smoothstep(.05,.4,lat));
  vec3 N=normalize(vN);float d=dot(N,sun);float li=smoothstep(-.12,.3,d);
  vec3 col=mix(vec3(.012,.016,.03),vec3(1.,.98,.95)*(.22+1.15*max(d,0.)),li);col+=vec3(1.,.5,.2)*.35*exp(-pow(d/.09,2.));
  gl_FragColor=vec4(col,cov*(.28+.62*li));
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
  }` });
earthG.add(mesh(new THREE.SphereGeometry(1.0065, 160, 160), cloudMat));
const atm = mesh(new THREE.SphereGeometry(1.03, 128, 128), new THREE.ShaderMaterial({ uniforms: { sun: eMat.uniforms.sun }, side: THREE.BackSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `varying vec3 vN;varying vec3 vW;void main(){vN=normalize(mat3(modelMatrix)*normal);vec4 w=modelMatrix*vec4(position,1.);vW=w.xyz;gl_Position=projectionMatrix*viewMatrix*w;}`,
  fragmentShader: `uniform vec3 sun;varying vec3 vN;varying vec3 vW;void main(){vec3 N=normalize(vN);vec3 V=normalize(cameraPosition-vW);
  float g=pow(smoothstep(0.,.245,abs(dot(N,V))),2.2);float s=dot(N,sun);float l=smoothstep(-.45,.5,s);
  vec3 c=mix(vec3(1.,.42,.15),vec3(.32,.62,1.),smoothstep(-.15,.3,s));float fw=pow(max(dot(-V,sun),0.),6.)*2.5;
  gl_FragColor=vec4(c*g*(.12+1.6*l+fw*smoothstep(-.3,.1,s)),1.);}` }));
SPACE.add(atm);

function llv(lat, lon, r = 1) { const ph = ((lon / D2R + 180) / 360) * Math.PI * 2; return new THREE.Vector3(-Math.cos(ph) * Math.cos(lat), Math.sin(lat), Math.sin(ph) * Math.cos(lat)).multiplyScalar(r); }
const P = llv(13.0 * D2R, 77.6 * D2R);
const T = new THREE.Vector3().crossVectors(new THREE.Vector3(.45, 1, .15).normalize(), P).normalize();
const NR = new THREE.Vector3().crossVectors(P, T).normalize();
const OA = P.clone().addScaledVector(NR, .035).normalize(), RO = 1.085;
const satLocal = th => OA.clone().multiplyScalar(Math.cos(th) * RO).addScaledVector(T, Math.sin(th) * RO);
const rotY = t => 1.1 + t * .0035;

const orbPts = []; for (let i = 0; i <= 720; i++) orbPts.push(satLocal(i / 720 * Math.PI * 2));
const orbit = new THREE.Line(new THREE.BufferGeometry().setFromPoints(orbPts), new THREE.LineBasicMaterial({ color: 0x4fc7ea, transparent: true, opacity: .55, blending: THREE.AdditiveBlending, depthWrite: false }));
earthG.add(orbit);
const trkPts = []; for (let i = 0; i <= 300; i++) trkPts.push(satLocal(-1.2 + i / 300 * 1.6).normalize().multiplyScalar(1.0075));
const track = new THREE.Line(new THREE.BufferGeometry().setFromPoints(trkPts), new THREE.LineDashedMaterial({ color: 0xffc85a, dashSize: .012, gapSize: .008, transparent: true, opacity: 0, depthWrite: false }));
track.computeLineDistances(); earthG.add(track);

const term = new THREE.Group(); term.position.copy(P.clone().multiplyScalar(1.0072)); term.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), P); earthG.add(term);
const ringM = new THREE.MeshBasicMaterial({ color: 0x4fc7ea, transparent: true, opacity: 1, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
const ring1 = mesh(new THREE.RingGeometry(.0035, .0048, 64), ringM); term.add(ring1);
const ring2M = ringM.clone(); const ring2 = mesh(new THREE.RingGeometry(.0035, .0042, 64), ring2M); term.add(ring2);
const termDot = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: 0x9fe8ff, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); termDot.scale.setScalar(.008); term.add(termDot);

function makeSat() {
  const g = new THREE.Group();
  const foil = new THREE.MeshStandardMaterial({ map: FOIL, bumpMap: FOIL, bumpScale: 2.5, metalness: 1, roughness: .3, color: 0xffd08a });
  const white = new THREE.MeshStandardMaterial({ color: 0xe8ecf2, metalness: .2, roughness: .45 });
  const frame = new THREE.MeshStandardMaterial({ color: 0xb9c0cc, metalness: .9, roughness: .25 });
  const black = new THREE.MeshStandardMaterial({ color: 0x0b0d12, metalness: .4, roughness: .6 });
  const panelM = new THREE.MeshStandardMaterial({ map: PANEL, metalness: .6, roughness: .22, emissive: 0x040a24 });
  g.add(mesh(new RoundedBoxGeometry(1, 1, 1.4, 3, .05), foil));
  const deck = mesh(new THREE.BoxGeometry(1.02, 1.02, .05), white); deck.position.z = -.72; g.add(deck);
  for (const s of [-1, 1]) {
    const arm = mesh(new THREE.CylinderGeometry(.04, .04, .8, 12), frame); arm.rotation.z = Math.PI / 2; arm.position.x = s * .9; g.add(arm);
    const hinge = mesh(new THREE.CylinderGeometry(.09, .09, .14, 16), frame); hinge.position.x = s * 1.28; g.add(hinge);
    const pg = new THREE.Group(); pg.position.x = s * 2.75; pg.rotation.x = .85; g.add(pg);
    for (const k of [-1, 1]) { const pn = mesh(new THREE.BoxGeometry(1.36, .045, 1.08), panelM); pn.position.x = k * .71; pg.add(pn);
      const fr = mesh(new THREE.BoxGeometry(1.4, .06, 1.12), frame); fr.position.x = k * .71; fr.scale.set(1, .6, 1); fr.position.y = -.01; pg.add(fr); } }
  const boom = mesh(new THREE.CylinderGeometry(.03, .03, .9, 10), frame); boom.position.set(0, .9, -.2); g.add(boom);
  const dish = mesh(new THREE.SphereGeometry(.42, 32, 12, 0, Math.PI * 2, 0, Math.PI / 3.2), white); dish.position.set(0, 1.45, -.2); dish.rotation.x = Math.PI; g.add(dish);
  const feed = mesh(new THREE.ConeGeometry(.05, .3, 12), frame); feed.position.set(0, 1.2, -.2); g.add(feed);
  const base = mesh(new THREE.CylinderGeometry(.34, .38, .12, 32), frame); base.rotation.x = Math.PI / 2; base.position.z = .76; g.add(base);
  for (const s of [-1, 1]) { const fk = mesh(new THREE.BoxGeometry(.06, .5, .35), frame); fk.position.set(s * .3, 0, .95); g.add(fk); }
  const tel = mesh(new THREE.CylinderGeometry(.22, .22, .5, 32), white); tel.rotation.x = Math.PI / 2; tel.position.z = 1.05; g.add(tel);
  const shade = mesh(new THREE.CylinderGeometry(.27, .24, .26, 32, 1, true), black.clone()); shade.material.side = THREE.DoubleSide; shade.rotation.x = Math.PI / 2; shade.position.z = 1.38; g.add(shade);
  const lens = mesh(new THREE.CircleGeometry(.2, 32), new THREE.MeshBasicMaterial({ color: 0x66ffbb })); lens.position.z = 1.31; g.add(lens);
  for (const [x, y] of [[.42, .42], [-.42, .42]]) { const st = mesh(new THREE.CylinderGeometry(.07, .09, .22, 16), black); st.position.set(x, y, -.5); st.rotation.x = Math.PI / 2; g.add(st); }
  for (const [x, y] of [[.4, -.4], [-.4, -.4], [.4, .4], [-.4, .4]]) { const n = mesh(new THREE.ConeGeometry(.05, .12, 10, 1, true), frame); n.position.set(x, y, -.8); n.rotation.x = -Math.PI / 2; g.add(n); }
  const bm = new THREE.SpriteMaterial({ map: DOT, color: 0xbfffe4, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
  const b = new THREE.Sprite(bm); b.position.z = 1.55; b.scale.setScalar(1.3); g.add(b); g.userData.beacon = b;
  return g;
}
const sat = makeSat(); sat.scale.setScalar(.011); earthG.add(sat);
const nadirCone = mesh(CONE, beamMat(0x7dffc0, .9, 2.2, 1)); earthG.add(nadirCone);
const footM = new THREE.MeshBasicMaterial({ color: 0x7dffc0, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
const foot = mesh(new THREE.RingGeometry(.0016, .0024, 48), footM); earthG.add(foot);
const winCone = mesh(CONE, beamMat(0xffc85a, .5, 2.0, 1)); earthG.add(winCone);
const sBeamCore = mesh(CYL, beamMat(0xa6ffd2, 1.6, 1.2)); const sBeamGlow = mesh(CYL, beamMat(0x39ff9a, .16, 2.5)); earthG.add(sBeamCore, sBeamGlow);
const pk = []; for (let i = 0; i < 18; i++) { const m = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: i % 2 ? 0x7fe9ff : 0xb4ffcf, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); m.scale.setScalar(.0035); earthG.add(m); pk.push(m); }

// ---------------------------------------------------------------- GROUND scene
const GROUND = new THREE.Scene(); GROUND.fog = new THREE.FogExp2(0x07101c, .0048);
const camG = new THREE.PerspectiveCamera(38, W / H, .05, 2000);
const dirOf = (az, el) => new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
const MOONDIR = dirOf(118 * D2R, 21 * D2R);
GROUND.add(new THREE.HemisphereLight(0x46679c, 0x0a0c10, .9));
const moonL = new THREE.DirectionalLight(0xb3cbff, 2.1); moonL.position.copy(MOONDIR).multiplyScalar(60); GROUND.add(moonL);
moonL.castShadow = true; moonL.shadow.mapSize.set(2048, 2048); moonL.shadow.bias = -.0004; moonL.shadow.normalBias = .02;
Object.assign(moonL.shadow.camera, { left: -13, right: 13, top: 13, bottom: -13, near: 5, far: 140 }); moonL.shadow.camera.updateProjectionMatrix();
const work = new THREE.PointLight(0xffc98a, 9, 9, 2); work.position.set(4.4, 1.7, 2.6); GROUND.add(work);
const skyG = new THREE.Group(); GROUND.add(skyG);
const SKYFRAG = NOISE + `varying vec3 vD;
  void main(){float h=clamp(vD.y,-.2,1.);vec3 c=mix(vec3(.045,.09,.16),vec3(.004,.008,.022),pow(max(h,0.),.45));
  c+=vec3(.16,.09,.05)*exp(-max(h,0.)*16.)*.8;
  vec3 bn=normalize(vec3(.55,.3,-.78));float b=exp(-pow(dot(vD,bn)/.17,2.));float n=fb(vD*6.);float n2=fb(vD*22.);
  c+=vec3(.20,.21,.28)*b*(.2+1.1*n*n)*(.6+.8*n2)*smoothstep(0.,.3,h);
  c+=vec3(.12,.06,.09)*b*smoothstep(.55,.8,fb(vD*4.+9.))*smoothstep(0.,.3,h);
  c-=vec3(.05)*b*smoothstep(.55,.7,fb(vD*9.+3.))*smoothstep(0.,.3,h);
  gl_FragColor=vec4(max(c,0.),1.);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
  }`;
skyG.add(mesh(new THREE.SphereGeometry(900, 64, 32), sky(SKYFRAG)));
skyG.add(starField(6200, 860, 23, true, 1.35));
const moon = new THREE.Sprite(new THREE.SpriteMaterial({ map: MOON, fog: false, depthWrite: false, transparent: true })); skyG.add(moon);
const moonGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: 0x9fb8e6, fog: false, depthWrite: false, transparent: true, blending: THREE.AdditiveBlending, opacity: .35 })); skyG.add(moonGlow);
moon.position.copy(MOONDIR).multiplyScalar(800); moon.scale.setScalar(26); moonGlow.position.copy(MOONDIR).multiplyScalar(801); moonGlow.scale.setScalar(150);

const terrH = (x, z) => { const d = Math.hypot(x, z); return ss(95, 300, d) * Math.pow(fbm(x * .0055 + 11, z * .0055 + 4), 1.5) * 150 + (fbm(x * .06, z * .06) - .5) * 1.1 * ss(9, 35, d); };
{ const tg = new THREE.PlaneGeometry(1400, 1400, 300, 300); tg.rotateX(-Math.PI / 2); const pa = tg.attributes.position, cols = new Float32Array(pa.count * 3);
  const dirt = new THREE.Color(0x3a3630), grass = new THREE.Color(0x1f2a1c), rock = new THREE.Color(0x2c3038), gravel = new THREE.Color(0x4a4640), c = new THREE.Color();
  for (let i = 0; i < pa.count; i++) { const x = pa.getX(i), z = pa.getZ(i), h = terrH(x, z); pa.setY(i, h);
    const n = fbm(x * .03 + 5, z * .03 + 2), d = Math.hypot(x, z); c.copy(dirt).lerp(grass, ss(.35, .65, n)).lerp(rock, ss(20, 70, h)).lerp(gravel, 1 - ss(4, 9, d));
    c.multiplyScalar(.8 + .4 * fbm(x * .4, z * .4)); cols[i * 3] = c.r; cols[i * 3 + 1] = c.g; cols[i * 3 + 2] = c.b; }
  tg.setAttribute('color', new THREE.BufferAttribute(cols, 3)); tg.computeVertexNormals();
  const tm = mesh(tg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .97, metalness: 0 })); tm.receiveShadow = true; GROUND.add(tm); }
{ const r = rng(55), N = 260, rocks = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1, 1), new THREE.MeshStandardMaterial({ color: 0x3b3d42, roughness: .95, flatShading: true }), N), m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  for (let i = 0; i < N; i++) { let x, z; do { x = (r() - .5) * 120; z = (r() - .5) * 120; } while (Math.hypot(x, z) < 5.5 || (x > 1.5 && x < 5 && z > -1 && z < 3));
    const s = .08 + Math.pow(r(), 3) * .9; e.set(r() * 6, r() * 6, r() * 6); q.setFromEuler(e); m.compose(new THREE.Vector3(x, terrH(x, z) + s * .3, z), q, new THREE.Vector3(s * (1 + r()), s * (.5 + r() * .5), s * (1 + r()))); rocks.setMatrixAt(i, m); }
  rocks.castShadow = rocks.receiveShadow = true; GROUND.add(rocks);
  const G = 1400, tufts = new THREE.InstancedMesh(new THREE.ConeGeometry(.025, .32, 3), new THREE.MeshStandardMaterial({ color: 0x27301f, roughness: 1 }), G);
  for (let i = 0; i < G; i++) { let x, z; do { x = (r() - .5) * 90; z = (r() - .5) * 90; } while (Math.hypot(x, z) < 4.5);
    const s = .4 + r() * .8; e.set((r() - .5) * .7, r() * 6, (r() - .5) * .7); q.setFromEuler(e); m.compose(new THREE.Vector3(x, terrH(x, z) + .2 * s, z), q, new THREE.Vector3(s, s, s)); tufts.setMatrixAt(i, m); }
  tufts.receiveShadow = true; GROUND.add(tufts); }

// the terminal vehicle
const van = new THREE.Group(); GROUND.add(van);
const M = {
  paint: new THREE.MeshPhysicalMaterial({ color: 0xe9eef4, metalness: .25, roughness: .32, clearcoat: 1, clearcoatRoughness: .12 }),
  dark: new THREE.MeshStandardMaterial({ color: 0x11161d, roughness: .6, metalness: .35 }),
  rubber: new THREE.MeshStandardMaterial({ color: 0x0b0c0e, roughness: .9 }),
  glass: new THREE.MeshPhysicalMaterial({ color: 0x0a1624, roughness: .04, metalness: .3, clearcoat: 1 }),
  blue: new THREE.MeshPhysicalMaterial({ color: 0x1f63c6, roughness: .35, metalness: .3, clearcoat: 1 }),
  cyan: new THREE.MeshStandardMaterial({ color: 0x2aa9d6, roughness: .4, metalness: .3 }),
  metal: new THREE.MeshStandardMaterial({ color: 0xa8b0ba, roughness: .25, metalness: .95 }),
  gwhite: new THREE.MeshPhysicalMaterial({ color: 0xf1f4f8, metalness: .15, roughness: .28, clearcoat: 1, clearcoatRoughness: .1 }),
};
const add = (g, m, x, y, z, p = van) => { const b = mesh(g, m); b.position.set(x, y, z); p.add(b); return b; };
const rbox = (w, h, d, r, m, x, y, z, p = van) => add(new RoundedBoxGeometry(w, h, d, 4, r), m, x, y, z, p);
rbox(2.25, 2.4, 4.4, .14, M.paint, 0, 1.78, -.6);
rbox(2.25, 1.35, 1.8, .2, M.paint, 0, 1.2, 2.3);
const hood = rbox(2.2, .5, 1.0, .15, M.paint, 0, 1.75, 2.0); hood.rotation.x = -.25;
const ws = add(new THREE.PlaneGeometry(2.0, .78), M.glass, 0, 2.24, 2.62); ws.rotation.x = -.55;
rbox(2.3, .36, .26, .08, M.dark, 0, .6, 3.2); rbox(2.3, .36, .26, .08, M.dark, 0, .6, -2.85);
add(new THREE.BoxGeometry(2.27, .17, 6.0), M.blue, 0, 1.6, .15); add(new THREE.BoxGeometry(2.27, .05, 6.0), M.cyan, 0, 1.43, .15);
for (const s of [-1, 1]) {
  add(new THREE.PlaneGeometry(1.0, .55), M.glass, s * 1.135, 1.95, 2.25).rotation.y = s * Math.PI / 2;
  add(new THREE.PlaneGeometry(2.7, .55), M.glass, s * 1.135, 2.4, -.6).rotation.y = s * Math.PI / 2;
  const dec = add(new THREE.PlaneGeometry(3.4, .425), new THREE.MeshStandardMaterial({ map: DECAL, transparent: true, roughness: .4 }), s * 1.137, 1.05, -.55); dec.rotation.y = s * Math.PI / 2;
  add(new THREE.BoxGeometry(.01, 1.7, .02), M.dark, s * 1.13, 1.6, .9); add(new THREE.BoxGeometry(.01, 1.7, .02), M.dark, s * 1.13, 1.6, .1);
  for (const z of [2.1, -1.9]) { const tire = add(new THREE.TorusGeometry(.33, .15, 16, 36), M.rubber, s * 1.02, .48, z); tire.rotation.y = Math.PI / 2;
    const rim = add(new THREE.CylinderGeometry(.27, .27, .2, 24), M.metal, s * 1.03, .48, z); rim.rotation.z = Math.PI / 2;
    const arch = add(new THREE.TorusGeometry(.56, .06, 8, 24, Math.PI), M.dark, s * 1.13, .48, z); arch.rotation.y = Math.PI / 2; }
  for (const z of [2.95, -2.65]) { add(new THREE.CylinderGeometry(.06, .06, .9, 10), M.metal, s * 1.28, .45, z); add(new THREE.CylinderGeometry(.2, .2, .04, 16), M.dark, s * 1.28, .02, z); }
}
for (let i = 0; i < 6; i++) add(new THREE.CylinderGeometry(.025, .025, .9, 8), M.metal, .6, .9 + i * .3, -2.83).rotation.z = Math.PI / 2;
add(new THREE.BoxGeometry(1.95, .06, 3.4), M.dark, 0, 3.0, -.7); for (const s of [-1, 1]) add(new THREE.BoxGeometry(.05, .12, 3.4), M.metal, s * .95, 3.06, -.7);
rbox(.8, .28, .9, .06, M.gwhite, .5, 3.14, .7);
rbox(1.5, .12, .2, .05, M.dark, 0, 1.95, 2.95);
const hlM = new THREE.MeshStandardMaterial({ color: 0x222222, emissive: 0xfff1d0, emissiveIntensity: 6 });
const tlM = new THREE.MeshStandardMaterial({ color: 0x220000, emissive: 0xff2a1a, emissiveIntensity: 3 });
const amberM = new THREE.MeshStandardMaterial({ color: 0x221100, emissive: 0xffa31a, emissiveIntensity: 2.5 });
for (const s of [-1, 1]) { rbox(.4, .2, .06, .04, hlM, s * .75, 1.0, 3.33); rbox(.2, .34, .06, .04, tlM, s * .95, 1.25, -2.84); for (const k of [.2, .5]) rbox(.16, .07, .05, .02, amberM, s * k, 1.95, 3.06); }
for (const s of [-1, 1]) { const b = mesh(CONE, beamMat(0xfff0d0, .09, 1.0, 0)); b.material.uniforms.fade.value = .4; orient(b, new THREE.Vector3(s * .75, 1.0, 3.36), new THREE.Vector3(s * .05, -.08, 1), 22, 4); van.add(b);
  const sp = new THREE.SpotLight(0xfff1d6, 60, 40, .45, .6, 1.6); sp.position.set(s * .75, 1.0, 3.3); sp.target.position.set(s * 1.5, 0, 16); van.add(sp, sp.target); }
const mastPole = add(new THREE.CylinderGeometry(.05, .07, 4.6, 12), M.dark, -.85, 5.2, -2.55);
const mDish = add(new THREE.SphereGeometry(.28, 20, 10, 0, Math.PI * 2, 0, Math.PI / 3), M.gwhite, -.85, 6.9, -2.3); mDish.rotation.x = -Math.PI / 2 + .3;
const mastLamp = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: 0xff3322, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true })); mastLamp.position.set(-.85, 7.6, -2.55); mastLamp.scale.setScalar(.7); van.add(mastLamp);
// pan-tilt gimbal
add(new THREE.CylinderGeometry(.38, .46, .24, 40), M.dark, 0, 3.15, -1.2);
add(new THREE.TorusGeometry(.42, .025, 8, 40), M.metal, 0, 3.27, -1.2).rotation.x = Math.PI / 2;
const panG = new THREE.Group(); panG.position.set(0, 3.28, -1.2); van.add(panG);
add(new THREE.CylinderGeometry(.36, .36, .1, 40), M.gwhite, 0, .03, 0, panG);
for (const s of [-1, 1]) { rbox(.1, .78, .36, .04, M.gwhite, s * .4, .42, 0, panG); const mo = add(new THREE.CylinderGeometry(.13, .13, .14, 24), M.dark, s * .5, .62, 0, panG); mo.rotation.z = Math.PI / 2;
  add(new THREE.CylinderGeometry(.14, .14, .02, 24), M.metal, s * .575, .62, 0, panG).rotation.z = Math.PI / 2; }
const tiltG = new THREE.Group(); tiltG.position.set(0, .62, 0); panG.add(tiltG);
rbox(.66, .48, .72, .07, M.gwhite, 0, 0, 0, tiltG); add(new THREE.BoxGeometry(.67, .05, .73), M.blue, 0, .12, 0, tiltG);
{ const l = add(new THREE.CylinderGeometry(.14, .16, .3, 36), M.dark, -.16, .02, .48, tiltG); l.rotation.x = Math.PI / 2;
  const hm = M.rubber.clone(); hm.side = THREE.DoubleSide; const hoodC = add(new THREE.CylinderGeometry(.19, .16, .18, 36, 1, true), hm, -.16, .02, .7, tiltG); hoodC.rotation.x = Math.PI / 2;
  add(new THREE.CircleGeometry(.12, 36), new THREE.MeshPhysicalMaterial({ color: 0x07142a, emissive: 0x1f5a9a, emissiveIntensity: .6, metalness: .9, roughness: .02, clearcoat: 1 }), -.16, .02, .63, tiltG);
  const tube = add(new THREE.CylinderGeometry(.08, .08, .56, 28), M.metal, .19, .02, .52, tiltG); tube.rotation.x = Math.PI / 2;
  add(new THREE.TorusGeometry(.085, .015, 8, 28), M.dark, .19, .02, .8, tiltG); }
const aptM = new THREE.MeshStandardMaterial({ color: 0x0, emissive: 0x3dff9a, emissiveIntensity: 0 });
const apt = add(new THREE.CircleGeometry(.065, 24), aptM, .19, .02, .805, tiltG);
const lensAnchor = new THREE.Object3D(); lensAnchor.position.set(-.16, .02, .65); tiltG.add(lensAnchor);
const ledG = new THREE.MeshStandardMaterial({ color: 0x001100, emissive: 0x33ff77, emissiveIntensity: 3 }), ledR = new THREE.MeshStandardMaterial({ color: 0x110000, emissive: 0xff4422, emissiveIntensity: 0 });
add(new THREE.SphereGeometry(.018, 10, 8), ledG, .2, .18, -.36, tiltG); add(new THREE.SphereGeometry(.018, 10, 8), ledR, .26, .18, -.36, tiltG);
{ const cv = new THREE.CatmullRomCurve3([new THREE.Vector3(.1, -.2, -.36), new THREE.Vector3(.35, -.45, -.5), new THREE.Vector3(.3, -.7, -.3), new THREE.Vector3(.2, -.62, 0)]);
  add(new THREE.TubeGeometry(cv, 30, .018, 8), M.rubber, 0, 0, 0, tiltG); }
// operator table with laptop
const table = new THREE.Group(); table.position.set(3.4, 0, .9); table.rotation.y = -.5; GROUND.add(table);
rbox(1.3, .05, .75, .02, M.metal, 0, .82, 0, table); for (const [x, z] of [[.6, .33], [-.6, .33], [.6, -.33], [-.6, -.33]]) add(new THREE.CylinderGeometry(.02, .02, .82, 8), M.metal, x, .41, z, table);
rbox(.4, .02, .28, .01, M.dark, -.1, .86, .05, table);
const screenM = new THREE.MeshBasicMaterial({ map: UI_SEARCH, toneMapped: false });
const scr = add(new THREE.PlaneGeometry(.4, .25), screenM, -.1, .99, -.09, table); scr.rotation.x = -.2;
add(new THREE.BoxGeometry(.42, .27, .01), M.dark, -.1, .99, -.1, table).rotation.x = -.2;
rbox(.5, .35, .35, .04, M.dark, .9, .18, -2.4, table); add(new THREE.SphereGeometry(.02, 8, 6), ledG, .9, .3, -2.22, table);
const scrLight = new THREE.PointLight(0x4fc7ea, 2.2, 3, 2); scrLight.position.set(-.1, 1.1, .3); table.add(scrLight);
van.traverse(o => { if (o.isMesh && !(o.material && o.material.blending === THREE.AdditiveBlending)) { o.castShadow = true; o.receiveShadow = true; } });
table.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });

const gSat = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: 0xd6fff0, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false })); GROUND.add(gSat);
const gBeamCore = mesh(CYL, beamMat(0xb6ffd9, 2.0, 1.2)); const gBeamGlow = mesh(CYL, beamMat(0x39ff9a, .3, 2.4)); GROUND.add(gBeamCore, gBeamGlow);
const gCone = mesh(CONE, beamMat(0xffc85a, .55, 2.2, 1)); GROUND.add(gCone);
const tower = new THREE.Group(); GROUND.add(tower);
{ const x = -150, z = -118, h = terrH(x, z); tower.position.set(x, h, z);
  const tw = mesh(new THREE.CylinderGeometry(.4, 1.2, 24, 6), M.dark); tw.position.y = 12; tower.add(tw);
  const lamp = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: 0xff3a2a, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false })); lamp.position.y = 24.5; lamp.scale.setScalar(5); tower.add(lamp); }
const villages = new THREE.Group(); GROUND.add(villages);
{ const r = rng(31); for (let i = 0; i < 60; i++) { const a = (140 + r() * 140) * D2R, d = 230 + r() * 180; const x = Math.sin(a) * d, z = Math.cos(a) * d;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: DOT, color: r() < .5 ? 0xffc27a : 0xffe2b0, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false, opacity: .8 }));
  s.position.set(x, terrH(x, z) + 1.5, z); s.scale.setScalar(1.6 + r() * 2.6); villages.add(s); } }
const azT = t => lerp(214, 250, clamp((t - 31) / 44)) * D2R, elT = t => lerp(50, 63, clamp((t - 31) / 44)) * D2R;

// ---------------------------------------------------------------- HUD (2D)
const hud = document.getElementById('hud').getContext('2d');
const FT = '"Bahnschrift","Segoe UI",sans-serif', FM = '"Cascadia Mono","Consolas",monospace';
const IMG = {};
const CY = '#4FC7EA', GR = '#5DE08A', RD = '#FF5A4E', AM = '#FFC85A', INK = '#EAF4FD', MU = '#93A9C8';
function T2(s, x, y, size, col, { w = 400, al = 'left', f = FT, a = 1, ls = 0, glow = 0 } = {}) {
  if (a <= 0) return; hud.save(); hud.globalAlpha = a; hud.font = `${w} ${size}px ${f}`; hud.fillStyle = col; hud.textAlign = al; hud.letterSpacing = ls + 'px';
  if (glow) { hud.shadowColor = col; hud.shadowBlur = glow; } hud.fillText(s, x, y); hud.restore(); }
function rr(x, y, w, h, r) { hud.beginPath(); hud.moveTo(x + r, y); hud.arcTo(x + w, y, x + w, y + h, r); hud.arcTo(x + w, y + h, x, y + h, r); hud.arcTo(x, y + h, x, y, r); hud.arcTo(x, y, x + w, y, r); hud.closePath(); }
function panel(x, y, w, h, a, border = 'rgba(79,199,234,.35)') { if (a <= 0) return; hud.save(); hud.globalAlpha = a; rr(x, y, w, h, 14);
  const g = hud.createLinearGradient(x, y, x, y + h); g.addColorStop(0, 'rgba(8,20,38,.78)'); g.addColorStop(1, 'rgba(3,9,18,.72)'); hud.fillStyle = g; hud.fill(); hud.strokeStyle = border; hud.lineWidth = 1.5; hud.stroke();
  hud.fillStyle = border; hud.fillRect(x + 18, y, 60, 2); hud.restore(); }
function proj(v, cam) { const p = v.clone().project(cam); return { x: (p.x * .5 + .5) * W, y: (-p.y * .5 + .5) * H, ok: p.z < 1 && p.z > -1 }; }
function label(v, cam, text, sub, a, dx, dy, col = CY) {
  if (a <= 0) return; const p = proj(v, cam); if (!p.ok || p.x < 20 || p.x > W - 20 || p.y < 20 || p.y > H - 20) return; const x2 = p.x + dx, y2 = p.y + dy, k = ease(clamp(a));
  hud.save(); hud.globalAlpha = a; hud.strokeStyle = col; hud.lineWidth = 2; hud.shadowColor = col; hud.shadowBlur = 8; hud.beginPath(); hud.arc(p.x, p.y, 7, 0, 7); hud.stroke();
  hud.beginPath(); hud.moveTo(p.x + (dx > 0 ? 7 : -7), p.y); hud.lineTo(lerp(p.x, x2, k), lerp(p.y, y2, k)); if (k > .99) hud.lineTo(x2 + (dx > 0 ? 40 : -40), y2); hud.stroke(); hud.restore();
  const al = dx > 0 ? 'left' : 'right', tx = x2 + (dx > 0 ? 50 : -50);
  T2(text, tx, y2 + 2, 30, INK, { w: 600, al, a: a * ss(.5, 1, a) }); if (sub) T2(sub, tx, y2 + 34, 22, MU, { al, a: a * ss(.6, 1, a) }); }
function caption(step, l1, l2, a) {
  if (a <= 0) return; hud.save(); hud.globalAlpha = a;
  const g = hud.createLinearGradient(0, H - 320, 0, H); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,4,10,.85)'); hud.fillStyle = g; hud.fillRect(0, H - 320, W, 320);
  hud.fillStyle = CY; hud.shadowColor = CY; hud.shadowBlur = 12; hud.fillRect(80, H - 172, 5, l2 ? 118 : 78); hud.restore();
  const k = ease(clamp(a)), dx = (1 - k) * 30;
  if (step) T2(step, 106 + dx, H - 150, 22, CY, { w: 700, f: FM, ls: 5, a });
  T2(l1, 104 + dx, H - (step ? 102 : 118), 46, INK, { w: 600, a }); if (l2) T2(l2, 106 + dx, H - 58, 30, '#b4c7de', { a: a * ss(.3, 1, a) }); }
function brand(a) {
  if (a <= 0) return; hud.save(); hud.globalAlpha = a; if (IMG.mark) hud.drawImage(IMG.mark, 56, 34, 50, 50); hud.restore();
  T2('ZERODRIFT', 120, 66, 28, INK, { w: 700, ls: 4, a }); T2('SIH26169  ·  problem statement by ISRO', 120, 90, 18, MU, { a });
  T2('SIMULATION · ILLUSTRATIVE', W - 60, 62, 17, 'rgba(147,169,200,.8)', { al: 'right', f: FM, ls: 3, a }); }
function stat(x, y, big, small, a, col = GR, w = 470) {
  if (a <= 0) return; const k = ease(clamp(a)); panel(x, y + (1 - k) * 16, w, 104, a); T2(big, x + 26, y + 58 + (1 - k) * 16, 46, col, { w: 700, a, glow: 14 });
  T2(small, x + 26, y + 88 + (1 - k) * 16, 21, MU, { a }); }
function vignette() { const g = hud.createRadialGradient(W / 2, H / 2, H * .45, W / 2, H / 2, H * 1.05); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.55)'); hud.fillStyle = g; hud.fillRect(0, 0, W, H); }
function black(a) { if (a <= 0) return; hud.fillStyle = `rgba(0,0,0,${clamp(a)})`; hud.fillRect(0, 0, W, H); }
const GRAIN = document.createElement('canvas'); GRAIN.width = GRAIN.height = 512;
{ const g = GRAIN.getContext('2d'), d = g.createImageData(512, 512), r = rng(9); for (let i = 0; i < d.data.length; i += 4) { const v = r() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; } g.putImageData(d, 0, 0); }
function sunFlare(cam, sunDir, k = 1) {
  const c = cam.position, u = sunDir; const b = c.dot(u), cc = c.lengthSq() - 1.03 * 1.03, disc = b * b - cc;
  const hit = disc > 0 && (-b - Math.sqrt(disc)) > 0;
  const ang = Math.acos(clamp(-c.clone().normalize().dot(u), -1, 1)), rE = Math.asin(1.0 / c.length());
  const vis = k * (hit ? 0 : 1) * ss(rE + .002, rE + .03, ang); if (vis <= 0) return;
  const p = proj(c.clone().addScaledVector(u, 300), cam); if (!p.ok || p.x < -400 || p.x > W + 400 || p.y < -400 || p.y > H + 400) return;
  hud.save(); hud.globalCompositeOperation = 'lighter'; hud.globalAlpha = vis;
  let g = hud.createRadialGradient(p.x, p.y, 0, p.x, p.y, 420); g.addColorStop(0, 'rgba(255,245,225,.9)'); g.addColorStop(.06, 'rgba(255,230,190,.55)'); g.addColorStop(.3, 'rgba(255,170,90,.12)'); g.addColorStop(1, 'rgba(255,150,80,0)'); hud.fillStyle = g; hud.fillRect(p.x - 420, p.y - 420, 840, 840);
  g = hud.createRadialGradient(p.x, p.y, 0, p.x, p.y, 38); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(1, 'rgba(255,255,255,0)'); hud.fillStyle = g; hud.beginPath(); hud.arc(p.x, p.y, 38, 0, 7); hud.fill();
  hud.save(); hud.translate(p.x, p.y); hud.scale(1, .012); g = hud.createRadialGradient(0, 0, 0, 0, 0, 900); g.addColorStop(0, 'rgba(160,210,255,.9)'); g.addColorStop(1, 'rgba(120,180,255,0)'); hud.fillStyle = g; hud.beginPath(); hud.arc(0, 0, 900, 0, 7); hud.fill(); hud.restore();
  const cx = W / 2, cy = H / 2; for (const [f, r, col] of [[.35, 26, '120,200,255'], [.62, 60, '140,255,200'], [.9, 18, '255,200,120'], [1.25, 90, '120,160,255'], [1.6, 40, '255,140,200']]) {
    const x = p.x + (cx - p.x) * f * 2, y = p.y + (cy - p.y) * f * 2; g = hud.createRadialGradient(x, y, r * .5, x, y, r); g.addColorStop(0, `rgba(${col},.05)`); g.addColorStop(.85, `rgba(${col},.10)`); g.addColorStop(1, `rgba(${col},0)`); hud.fillStyle = g; hud.beginPath(); hud.arc(x, y, r, 0, 7); hud.fill(); }
  hud.restore();
}

// ---------------------------------------------------------------- scene logic
function renderScene(scene, cam, t) { rpass.scene = scene; rpass.camera = cam; film.uniforms.time.value = t; comp.render(); }
function setBeamTime(t) { for (const m of [sBeamCore, sBeamGlow, gBeamCore, gBeamGlow]) m.material.uniforms.time.value = t; }
function setupSpace(t, th, showSat = true) {
  earthG.rotation.y = rotY(t); earthG.updateMatrixWorld(true); cloudMat.uniforms.time.value = t;
  sat.visible = showSat; sat.position.copy(satLocal(th)); sat.lookAt(0, 0, 0);
  sat.userData.beacon.material.opacity = frac(t * 4) < .5 ? 1 : .15;
  const pw = P.clone().applyMatrix4(earthG.matrixWorld), sw = sat.position.clone().applyMatrix4(earthG.matrixWorld);
  const vel = satLocal(th + .002).sub(satLocal(th)).normalize().applyQuaternion(earthG.quaternion);
  return { pw, sw, vel };
}
function hideSpaceFx() { orbit.material.opacity = .55; track.material.opacity = 0; nadirCone.visible = foot.visible = winCone.visible = false; sBeamCore.visible = sBeamGlow.visible = false; pk.forEach(p => p.visible = false); term.visible = false; }
function gimbalAim(pan, tilt) { panG.rotation.y = pan; tiltG.rotation.x = -tilt; van.updateMatrixWorld(true); }
const V3 = () => new THREE.Vector3();
const shake = (t, a) => new THREE.Vector3(Math.sin(t * 1.7) * .6 + Math.sin(t * 4.3) * .25, Math.sin(t * 1.3 + 1) * .5 + Math.sin(t * 3.7) * .2, Math.sin(t * 1.1 + 2) * .5).multiplyScalar(a);
function groundCommon(t) {
  const az = azT(t), el = elT(t), sd = dirOf(az, el);
  gSat.position.copy(sd.clone().multiplyScalar(420).add(new THREE.Vector3(0, 3.9, -1.2))); const blink = frac(t * 4) < .5;
  gSat.scale.setScalar(blink ? 4.2 : 2.2); gSat.material.opacity = blink ? 1 : .45;
  mastLamp.material.opacity = frac(t * .9) < .2 ? 1 : .08; mastPole.visible = mDish.visible = mastLamp.visible = !(t >= 61 && t < 68);
  return { az, el, sd };
}

function seek(t) {
  hud.clearRect(0, 0, W, H); setBeamTime(t);
  const cuts = [7, 19, 31, 43, 61, 75, 86];
  let fade = 0; for (const c of cuts) fade = Math.max(fade, 1 - ss(0, .45, Math.abs(t - c)));
  fade = Math.max(fade, 1 - ss(0, 1.2, t), ss(99.2, 100, t));
  const sunDir = eMat.uniforms.sun.value;

  if (t < 31 || t >= 75) {
    hideSpaceFx(); bloom.strength = .85; bloom.threshold = .7;
    if (t < 7) { // --- S1 sunrise over Earth + title
      setupSpace(t, 0, false); orbit.material.opacity = 0;
      const ang = lerp(.265, .335, ease(ss(.8, 6.6, t)));
      const cd = sunDir.clone().negate().applyAxisAngle(Y, ang), pos = cd.multiplyScalar(lerp(3.5, 3.3, t / 7));
      camS.position.copy(pos); camS.up.set(0, 1, 0);
      const fwd = pos.clone().negate().normalize(), right = new THREE.Vector3().crossVectors(fwd, Y).normalize(); camS.lookAt(right.multiplyScalar(-.7).add(new THREE.Vector3(0, .12, 0)));
      renderScene(SPACE, camS, t); sunFlare(camS, sunDir); vignette();
      const o = 1 - ss(6.2, 6.9, t), a1 = ss(1.2, 2, t) * o, a2 = ss(1.8, 2.7, t) * o, a3 = ss(2.8, 3.7, t) * o, a4 = ss(3.8, 4.6, t) * o;
      T2('SMART INDIA HACKATHON 2026  ·  PS SIH26169  ·  ISRO', 140, 330, 22, CY, { w: 700, f: FM, ls: lerp(12, 4, ease(a1)), a: a1 });
      hud.save(); hud.globalAlpha = a2; if (IMG.mark) { const s = lerp(.7, 1, ease(a2)); hud.drawImage(IMG.mark, 196 - 60 * s, 432 - 60 * s, 120 * s, 120 * s); } hud.restore();
      T2('ZeroDrift', 280, 470, 128, INK, { w: 700, a: a2, glow: 30 });
      T2('AI virtual-camera tracking for coarse alignment', 142, 560, 40, INK, { a: a3 }); T2('of mobile free-space optical (FSOC) terminals', 142, 610, 40, INK, { a: a3 });
      T2('How it would work in the field: an end-to-end simulation', 142, 690, 28, MU, { a: a4 });
      hud.save(); hud.globalAlpha = a4; for (const [im, x] of [[IMG.isro, 142], [IMG.sih, 322]]) { if (!im) continue; rr(x, 740, 160, 84, 12); hud.fillStyle = '#fff'; hud.fill(); const s = Math.min(140 / im.width, 66 / im.height); hud.drawImage(im, x + 80 - im.width * s / 2, 782 - im.height * s / 2, im.width * s, im.height * s); } hud.restore();
    } else if (t < 19) { // --- S2 orbit + narrow beam
      const th = -2.15 + (t - 7) * .018; const { sw, vel } = setupSpace(t, th);
      const rad = sw.clone().normalize(), side = new THREE.Vector3().crossVectors(vel, rad).normalize();
      const k = 1 + 3.2 * ease(ss(12.5, 17.5, t)), orb = lerp(-.25, .25, (t - 7) / 12);
      camS.position.copy(sw).addScaledVector(vel, -.19 * k * Math.cos(orb)).addScaledVector(rad, .045 * k).addScaledVector(side, .07 * k + Math.sin(orb) * .05 * k);
      camS.up.copy(rad); camS.lookAt(sw.clone().addScaledVector(vel, .08).addScaledVector(rad, -.07 * k));
      const nb = ss(13, 14.5, t); nadirCone.visible = foot.visible = nb > 0;
      const sl = satLocal(th), nd = sl.clone().normalize(); orient(nadirCone, sl, nd.clone().negate(), sl.length() - 1, .0011); nadirCone.material.uniforms.op.value = 1.4 * nb; nadirCone.material.uniforms.fade.value = .97;
      foot.position.copy(nd.clone().multiplyScalar(1.0072)); foot.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), nd); footM.opacity = nb;
      renderScene(SPACE, camS, t); sunFlare(camS, sunDir, .8); vignette(); brand(1);
      label(sw, camS, 'LEO satellite', 'optical (laser) terminal on board', win(t, 8.2, 12.6), 120, -110);
      caption('THE CHALLENGE', 'A laser link moves far more data than radio, but its beam is very narrow.', 'Both terminals must point at each other within micro-radians, or the link is lost.', win(t, 7.6, 18.6));
    } else if (t < 31) { // --- S3 fly to India, predicted pass
      const th = -.95 + (t - 19) * .04; const { pw, sw } = setupSpace(t, th);
      term.visible = true; const pul = frac(t * .8); ring2.scale.setScalar(1 + pul * 3.5); ring2M.opacity = 1 - pul; ringM.opacity = .9;
      track.material.opacity = .9 * ss(21.5, 23, t);
      const north = Y.clone().addScaledVector(pw, -pw.y).normalize();
      const k = ease(ss(19.2, 27.5, t));
      const p0 = pw.clone().addScaledVector(north, -.9).normalize().multiplyScalar(3.0), p1 = pw.clone().multiplyScalar(1.36).addScaledVector(north, -.22);
      camS.position.lerpVectors(p0, p1, k); camS.up.copy(north); camS.lookAt(pw.clone().multiplyScalar(lerp(0, 1, k)).addScaledVector(north, .06 * k));
      const w = ss(25.5, 27, t); winCone.visible = w > 0; const sl = satLocal(th), dir = sl.clone().sub(P);
      orient(winCone, P.clone().multiplyScalar(1.007), dir, .045, .045 * Math.tan(9 * D2R)); winCone.material.uniforms.op.value = .6 * w;
      renderScene(SPACE, camS, t); vignette(); brand(1);
      label(pw, camS, 'Mobile FSOC terminal', 'deployed in India (illustrative site)', win(t, 22.5, 30.6), -130, 120, CY);
      label(sw, camS, 'Predicted pass', 'from the satellite\'s orbit elements', win(t, 23.5, 30.6), 110, -90, AM);
      caption('STEP 1  ·  PREDICT', 'Orbit prediction tells the terminal roughly where to look.', 'But a rough pointing window is far too wide for a laser.', win(t, 19.6, 30.6));
    } else if (t < 86) { // --- S7 link closes
      const th = -.10 + (t - 75) * .02; const { pw, sw } = setupSpace(t, th);
      term.visible = true; ringM.opacity = .5; ring2M.opacity = 0;
      const Tw = T.clone().applyQuaternion(earthG.quaternion), Nw = NR.clone().applyQuaternion(earthG.quaternion), mid = pw.clone().add(sw).multiplyScalar(.5);
      const a = lerp(-.25, .25, (t - 75) / 11), sideV = Tw.clone().multiplyScalar(Math.cos(a)).addScaledVector(Nw, Math.sin(a));
      camS.position.copy(mid).addScaledVector(sideV, .16).addScaledVector(pw, .006); camS.up.copy(pw); camS.lookAt(mid.clone().addScaledVector(pw, .004));
      const bp = ss(76, 77.4, t), sl = satLocal(th), st = P.clone().multiplyScalar(1.0075), dir = sl.clone().sub(st), len = dir.length();
      sBeamCore.visible = sBeamGlow.visible = true; orient(sBeamCore, st, dir, len * bp, .00022); orient(sBeamGlow, st, dir, len * bp, .0012);
      sBeamCore.material.uniforms.fade.value = sBeamGlow.material.uniforms.fade.value = bp < 1 ? .8 : .999;
      const fl = ss(78, 79, t); pk.forEach((p, i) => { p.visible = fl > 0; const u = frac(t * .45 + i / 9); p.position.copy(st).addScaledVector(dir, i % 2 ? 1 - u : u); p.material.opacity = fl * Math.sin(u * Math.PI); });
      renderScene(SPACE, camS, t); sunFlare(camS, sunDir, .7); vignette(); brand(1);
      const sp = proj(sw, camS), fc = ss(76.8, 78.2, t) * (1 - ss(84.8, 85.6, t));
      if (sp.ok && fc > 0) { hud.save(); hud.globalAlpha = fc; hud.strokeStyle = GR; hud.shadowColor = GR; hud.shadowBlur = 10; hud.lineWidth = 2;
        const r0 = lerp(140, 34, ease(ss(76.8, 78.2, t))); for (const m of [1, 1.5]) { hud.beginPath(); hud.arc(sp.x, sp.y, r0 * m, 0, 7); hud.stroke(); } hud.restore();
        T2('FINE STAGE · CAPTURED', sp.x - 190, sp.y + 132, 18, GR, { w: 700, f: FM, ls: 2, al: 'right', a: fc * ss(78, 78.6, t), glow: 8 }); }
      label(sw, camS, 'Satellite optical terminal', null, win(t, 76.5, 85.6), -140, 90, GR); label(pw, camS, 'Ground terminal', null, win(t, 76.5, 85.6), 150, -170, GR);
      stat(W - 560, 150, '99.3%', 'link closure with the modelled fine stage', ss(78.2, 79, t) * (1 - ss(85.4, 86, t)));
      stat(W - 560, 272, '14.7%', 'with the coarse stage alone', ss(79.2, 80, t) * (1 - ss(85.4, 86, t)), AM);
      caption('STEP 4  ·  LINK', 'Coarse lock hands off to the fine-steering stage.', 'The optical link closes and data flows both ways.', win(t, 75.6, 85.6));
    } else { // --- S8 pipeline + end card
      const { pw } = setupSpace(t, .3 + (t - 86) * .03); orbit.material.opacity = .3;
      const cd = pw.clone().applyAxisAngle(Y, -.95 + (t - 86) * .025); camS.position.copy(cd.multiplyScalar(3.5).add(new THREE.Vector3(0, .9, 0))); camS.up.set(0, 1, 0); camS.lookAt(0, -.35, 0);
      renderScene(SPACE, camS, t); hud.fillStyle = 'rgba(2,6,14,.62)'; hud.fillRect(0, 0, W, H); vignette();
      const pa = 1 - ss(95, 95.8, t);
      T2('END TO END', W / 2, 190, 22, CY, { w: 700, f: FM, ls: 6, al: 'center', a: ss(86.4, 87.2, t) * pa });
      T2('From a wide camera to a closed optical link', W / 2, 256, 54, INK, { w: 600, al: 'center', a: ss(86.6, 87.4, t) * pa, glow: 18 });
      const nodes = [['Wide-field camera', 'sees the whole sky'], ['Detection', 'every bright point'], ['Beacon check', '4 Hz signature + NN'], ['Kalman predictor', 'rides through vibration'], ['Pan-tilt gimbal', 'coarse pointing'], ['Fine-steering stage', 'micro-radian trim'], ['Optical link', 'data flows']];
      const nw = 226, gap = 30, x0 = (W - (7 * nw + 6 * gap)) / 2, ny = 320, hot = Math.floor(frac(Math.max(0, t - 90) / 3.5) * 7);
      nodes.forEach(([a1, b1], i) => { const a = ss(87 + i * .42, 87.6 + i * .42, t) * pa; if (a <= 0) return; const x = x0 + i * (nw + gap), on = t > 90 && i === hot;
        panel(x, ny + (1 - a) * 20, nw, 142, a, on || i === 2 ? 'rgba(93,224,138,.8)' : 'rgba(79,199,234,.4)');
        T2(String(i + 1).padStart(2, '0'), x + 18, ny + 44 + (1 - a) * 20, 20, on || i === 2 ? GR : CY, { w: 700, f: FM, a, glow: on ? 12 : 0 });
        T2(a1, x + 18, ny + 86 + (1 - a) * 20, 23, INK, { w: 600, a }); T2(b1, x + 18, ny + 118 + (1 - a) * 20, 19, MU, { a });
        if (i < 6) { const ax = x + nw + 4, aa = ss(90, 90.6, t) * pa; hud.save(); hud.globalAlpha = aa; hud.fillStyle = CY; for (let d = 0; d < 3; d++) { const u = frac(t * 1.2 + d / 3); hud.beginPath(); hud.arc(ax + u * (gap - 8), ny + 71, 3, 0, 7); hud.fill(); } hud.restore(); } });
      const sw4 = 400, sg = 28, sx = (W - (4 * sw4 + 3 * sg)) / 2;
      [['1.27 s', 'median acquisition time'], ['100%', 'acquisition, 64-run Monte Carlo'], ['0 / 64', 'runs that locked onto a decoy'], ['99.3%', 'link closure, modelled fine stage']]
        .forEach(([b, s], i) => stat(sx + i * (sw4 + sg), 540, b, s, ss(91.3 + i * .4, 92 + i * .4, t) * pa, GR, sw4));
      T2('250 / 251 automated tests pass  ·  tracker runs in 8–21 ms per 33 ms frame on 2 CPU cores', W / 2, 720, 26, MU, { al: 'center', a: ss(93.2, 94, t) * pa });
      const ea = ss(95.6, 96.6, t);
      if (ea > 0) { hud.save(); hud.globalAlpha = ea; if (IMG.mark) { const s = lerp(.8, 1, ease(ea)); hud.drawImage(IMG.mark, W / 2 - 70 * s, 320 - 70 * s, 140 * s, 140 * s); } hud.restore();
        T2('ZeroDrift', W / 2, 510, 110, INK, { w: 700, al: 'center', a: ea, glow: 30 });
        T2('Jabalpur Engineering College  ·  Smart India Hackathon 2026', W / 2, 580, 32, INK, { al: 'center', a: ea });
        T2('Problem statement SIH26169, set by ISRO', W / 2, 626, 26, MU, { al: 'center', a: ea });
        hud.save(); hud.globalAlpha = ss(96.2, 97.2, t); for (const [im, x] of [[IMG.isro, W / 2 - 180], [IMG.sih, W / 2 + 20]]) { if (!im) continue; rr(x, 680, 160, 84, 12); hud.fillStyle = '#fff'; hud.fill(); const s = Math.min(140 / im.width, 66 / im.height); hud.drawImage(im, x + 80 - im.width * s / 2, 722 - im.height * s / 2, im.width * s, im.height * s); } hud.restore();
        T2('Simulation: an illustrative visualisation. Numbers are from our 64-run Monte Carlo campaign and test suite.', W / 2, 860, 20, 'rgba(147,169,200,.85)', { al: 'center', a: ss(96.6, 97.4, t) }); }
    }
  } else if (t < 43 || t >= 61) {
    bloom.strength = .8; bloom.threshold = .75;
    const { az, el, sd } = groundCommon(t);
    const errAz = 5 * D2R, errEl = -3.6 * D2R;
    let pan, tilt, coneA = 0, coneAng = 8 * D2R, beam = 0;
    if (t < 43) { const k = ease(ss(34.5, 39.5, t)); pan = lerp(0, az + errAz, k); tilt = lerp(0, el + errEl, k); coneA = ss(39.5, 40.6, t); }
    else { const dk = Math.exp(-Math.max(0, t - 62) / .75), jit = (Math.sin(t * 23.1) * Math.sin(t * 7.7) + Math.sin(t * 13.3) * .5) * .05 * D2R;
      pan = az + errAz * dk + jit; tilt = el + errEl * dk + jit * .7; coneA = 1 - ss(64.2, 65.2, t); coneAng = lerp(8 * D2R, .25 * D2R, ease(ss(61.8, 64.2, t))); beam = ss(64.3, 65.1, t); }
    gimbalAim(pan, tilt); screenM.map = t < 61 ? UI_SEARCH : UI_LOCK; ledR.emissiveIntensity = beam > 0 ? 4 : 0;
    const ap = apt.getWorldPosition(V3()), hd = dirOf(pan, tilt), toSat = gSat.position.clone().sub(ap);
    gCone.visible = coneA > 0; orient(gCone, ap, hd, 60, 60 * Math.tan(coneAng)); gCone.material.uniforms.op.value = .7 * coneA;
    gBeamCore.visible = gBeamGlow.visible = beam > 0; const bd = beam >= 1 ? toSat : hd.clone().multiplyScalar(toSat.length());
    orient(gBeamCore, ap, bd, bd.length() * beam, .035); orient(gBeamGlow, ap, bd, bd.length() * beam, .32);
    gBeamCore.material.uniforms.fade.value = gBeamGlow.material.uniforms.fade.value = beam < 1 ? .85 : .995; aptM.emissiveIntensity = 6 * beam;
    const gp = panG.getWorldPosition(V3()).add(new THREE.Vector3(0, .62, 0));
    if (t < 43) { const k1 = ease(ss(31, 37, t)), k2 = ease(ss(36.5, 42.8, t));
      camG.position.copy(new THREE.Vector3(24, 3.2, 21).lerp(new THREE.Vector3(12.5, 2.4, 11), k1).lerp(new THREE.Vector3(7.2, 2.0, 7.4), k2)).add(shake(t, .04));
      camG.lookAt(new THREE.Vector3(0, 1.8, 0).lerp(gp.clone().add(new THREE.Vector3(-1.4, 2.0, -1.4)), k2)); }
    else { const k = ease(ss(66.8, 74.5, t));
      const c0 = gp.clone().add(new THREE.Vector3(3.3, -.7, 2.7)), c1 = new THREE.Vector3(14, 4.2, 12);
      camG.position.lerpVectors(c0, c1, k).add(shake(t, .025)); const l0 = gp.clone().addScaledVector(sd, 2.2), l1 = gp.clone().addScaledVector(sd, 3.4); camG.lookAt(l0.lerp(l1, k)); }
    skyG.position.copy(camG.position);
    renderScene(GROUND, camG, t); vignette(); brand(1);
    if (t < 43) {
      label(gp, camG, 'Pan-tilt gimbal', 'coarse pointing', win(t, 33, 38.6), 150, -120);
      label(scr.getWorldPosition(V3()), camG, 'Operator laptop', 'ZeroDrift tracker running', win(t, 33.4, 38.6), -160, 90, CY);
      label(lensAnchor.getWorldPosition(V3()), camG, 'Wide-field camera', 'the "virtual camera" input', win(t, 39.4, 42.6), -170, 60);
      label(ap.clone().addScaledVector(hd, 7), camG, 'Open-loop pointing error', 'several degrees: the laser would miss', win(t, 40.2, 42.6), 160, 60, AM);
      caption('STEP 1  ·  SLEW', 'The terminal slews to the predicted direction.', 'Close, but the uncertainty cone is far wider than a laser beam.', win(t, 31.6, 42.6));
    } else {
      label(gSat.position, camG, 'Beacon locked', 'satellite, 4 Hz', win(t, 62.2, 66.6), -160, 90, GR);
      const pa = win(t, 61.8, 74.6); panel(W - 600, 130, 540, 330, pa);
      T2('POINTING ERROR  ·  µrad (log)', W - 572, 172, 18, CY, { w: 700, f: FM, ls: 2, a: pa });
      if (pa > 0) { hud.save(); hud.globalAlpha = pa; const gx = W - 572, gy = 196, gw = 484, gh = 220;
        hud.strokeStyle = 'rgba(147,169,200,.25)'; hud.lineWidth = 1; for (const v of [100, 1000, 10000]) { const yy = gy + gh - (Math.log10(v) - 2) / 2 * gh; hud.beginPath(); hud.moveTo(gx, yy); hud.lineTo(gx + gw, yy); hud.stroke();
          T2(v >= 1000 ? (v / 1000) + 'k' : String(v), gx + gw + 8, yy + 6, 16, MU, { f: FM, a: pa }); }
        const e = s => 4200 * Math.exp(-s / .85) + 198 * (1 + .32 * Math.sin(s * 7.1) * Math.sin(s * 2.3) + .12 * Math.sin(s * 17.7));
        const now = t - 61.8, pts = []; for (let i = 0; i <= 240; i++) { const s = i / 240 * 12; if (s > now) break; pts.push([gx + s / 12 * gw, gy + gh - (clamp(Math.log10(e(s)), 2, 4) - 2) / 2 * gh]); }
        if (pts.length > 1) { const fg = hud.createLinearGradient(0, gy, 0, gy + gh); fg.addColorStop(0, 'rgba(93,224,138,.28)'); fg.addColorStop(1, 'rgba(93,224,138,0)'); hud.fillStyle = fg;
          hud.beginPath(); hud.moveTo(pts[0][0], gy + gh); pts.forEach(p => hud.lineTo(p[0], p[1])); hud.lineTo(pts[pts.length - 1][0], gy + gh); hud.fill();
          hud.strokeStyle = GR; hud.lineWidth = 3; hud.shadowColor = GR; hud.shadowBlur = 10; hud.beginPath(); pts.forEach((p, i) => i ? hud.lineTo(p[0], p[1]) : hud.moveTo(p[0], p[1])); hud.stroke();
          const lp = pts[pts.length - 1]; hud.fillStyle = GR; hud.beginPath(); hud.arc(lp[0], lp[1], 5, 0, 7); hud.fill(); hud.shadowBlur = 0; }
        hud.setLineDash([8, 8]); hud.strokeStyle = 'rgba(93,224,138,.5)'; const y198 = gy + gh - (Math.log10(198) - 2) / 2 * gh; hud.beginPath(); hud.moveTo(gx, y198); hud.lineTo(gx + gw, y198); hud.stroke(); hud.setLineDash([]); hud.restore();
        T2('demo-run median 198 µrad', gx + gw - 4, y198 + 26, 18, GR, { al: 'right', a: pa * ss(65, 66, t) }); }
      stat(W - 600, 486, '97.5%', 'lock retention, campaign median', ss(66, 66.8, t) * (1 - ss(74.4, 75, t)), GR, 540);
      stat(W - 600, 606, '768 µrad', 'p95 pointing error, campaign median', ss(67, 67.8, t) * (1 - ss(74.4, 75, t)), CY, 540);
      caption('STEP 3  ·  LOCK & TRACK', 'The gimbal closes the loop on the beacon, then tracks the pass.', 'A Kalman predictor rides through vehicle vibration between frames.', win(t, 61.6, 74.6));
    }
  } else {
    R.setRenderTarget(null); R.setClearColor(0, 1); R.clear();
    camView(t - 43, t);
  }
  black(fade);
}

// ---------------------------------------------------------------- S5: what the camera sees
const CVS = (() => { const r = rng(77), a = []; for (let i = 0; i < 700; i++) a.push({ x: r() * 2600 - 340, y: r() * 1200 - 120, m: Math.pow(r(), 4.5), c: r(), p: r() * 6 }); return a; })();
function glow(x, y, r, col, a) { if (a <= 0) return; hud.save(); hud.globalAlpha = a; hud.globalCompositeOperation = 'lighter'; const g = hud.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, col); g.addColorStop(.12, col); g.addColorStop(.35, col.replace('1)', '.25)')); g.addColorStop(1, col.replace('1)', '0)')); hud.fillStyle = g; hud.beginPath(); hud.arc(x, y, r, 0, 7); hud.fill();
  hud.globalAlpha = a * .5; hud.fillStyle = col.replace('1)', '.5)'); hud.fillRect(x - r * 1.6, y - .8, r * 3.2, 1.6); hud.fillRect(x - .8, y - r * 1.2, 1.6, r * 2.4); hud.restore(); }
function brackets(x, y, s, col, a, lw = 2.5) { if (a <= 0) return; hud.save(); hud.globalAlpha = a; hud.strokeStyle = col; hud.lineWidth = lw; hud.shadowColor = col; hud.shadowBlur = 6; const L = s * .38;
  for (const [sx, sy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { hud.beginPath(); hud.moveTo(x + sx * s, y + sy * (s - L)); hud.lineTo(x + sx * s, y + sy * s); hud.lineTo(x + sx * (s - L), y + sy * s); hud.stroke(); } hud.restore(); }
function skyPlot(x, y, r, u, t, a) {
  if (a <= 0) return; panel(x - r - 30, y - r - 62, 2 * r + 60, 2 * r + 110, a);
  T2('SKY PLOT  ·  AZ / EL', x - r - 8, y - r - 28, 16, CY, { w: 700, f: FM, ls: 2, a });
  hud.save(); hud.globalAlpha = a; hud.strokeStyle = 'rgba(79,199,234,.28)'; hud.lineWidth = 1;
  for (const e of [0, 30, 60]) { hud.beginPath(); hud.arc(x, y, r * (90 - e) / 90, 0, 7); hud.stroke(); }
  hud.beginPath(); hud.moveTo(x - r, y); hud.lineTo(x + r, y); hud.moveTo(x, y - r); hud.lineTo(x, y + r); hud.stroke(); hud.restore();
  for (const [s, dx, dy] of [['N', 0, -r - 8], ['E', r + 14, 5], ['S', 0, r + 20], ['W', -r - 14, 5]]) T2(s, x + dx, y + dy, 14, MU, { f: FM, al: 'center', a });
  const pt = (az, el) => [x + r * (90 - el / D2R) / 90 * Math.sin(az), y - r * (90 - el / D2R) / 90 * Math.cos(az)];
  hud.save(); hud.globalAlpha = a; hud.strokeStyle = AM; hud.setLineDash([5, 5]); hud.lineWidth = 2; hud.beginPath();
  for (let i = 0; i <= 40; i++) { const tt = 31 + i / 40 * 44, [px, py] = pt(azT(tt), elT(tt)); i ? hud.lineTo(px, py) : hud.moveTo(px, py); } hud.stroke(); hud.setLineDash([]);
  const [bx, by] = pt(azT(t), elT(t)); hud.fillStyle = GR; hud.shadowColor = GR; hud.shadowBlur = 10; hud.beginPath(); hud.arc(bx, by, 5, 0, 7); hud.fill();
  const lk = ease(ss(13.2, 15.4, u)), [cx, cy] = pt(azT(t) + 5 * D2R * (1 - lk), elT(t) - 3.6 * D2R * (1 - lk));
  hud.strokeStyle = CY; hud.shadowColor = CY; hud.lineWidth = 2; hud.beginPath(); hud.moveTo(cx - 9, cy); hud.lineTo(cx + 9, cy); hud.moveTo(cx, cy - 9); hud.lineTo(cx, cy + 9); hud.stroke(); hud.restore();
  T2('— predicted pass', x - r - 8, y + r + 40, 15, AM, { f: FM, a }); T2('+ boresight', x + 40, y + r + 40, 15, CY, { f: FM, a });
}
function camView(u, t) {
  const bx0 = 1060 + u * 7, by0 = 330 - u * 2.4, k = ease(ss(13.4, 15.8, u)), ox = (960 - bx0) * k + Math.sin(t * 9) * .8, oy = (540 - by0) * k + Math.sin(t * 7.3) * .8;
  const g = hud.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#010309'); g.addColorStop(.62, '#050d1b'); g.addColorStop(.9, '#0e1a2a'); g.addColorStop(1, '#1a2230'); hud.fillStyle = g; hud.fillRect(0, 0, W, H);
  hud.save(); hud.globalCompositeOperation = 'lighter'; const mw = hud.createLinearGradient(200 + ox, -100 + oy, 1500 + ox, 1100 + oy); mw.addColorStop(0, 'rgba(60,70,110,0)'); mw.addColorStop(.45, 'rgba(70,80,120,.10)'); mw.addColorStop(.55, 'rgba(90,90,130,.13)'); mw.addColorStop(1, 'rgba(60,70,110,0)'); hud.fillStyle = mw; hud.fillRect(0, 0, W, H); hud.restore();
  for (const s of CVS) { const x = s.x + ox, y = s.y + oy; if (x < -5 || x > W + 5 || y < -5 || y > H) continue; const tw = .75 + .25 * Math.sin(t * 3 + s.p);
    hud.fillStyle = s.c < .2 ? `rgba(255,214,180,${(.2 + .8 * s.m) * tw})` : s.c < .45 ? `rgba(190,215,255,${(.2 + .8 * s.m) * tw})` : `rgba(255,255,255,${(.2 + .8 * s.m) * tw})`;
    const r = .7 + s.m * 2.2; hud.beginPath(); hud.arc(x, y, r, 0, 7); hud.fill(); }
  hud.save(); const hg = hud.createRadialGradient(260 + ox, 1010 + oy, 10, 260 + ox, 1010 + oy, 760); hg.addColorStop(0, 'rgba(255,150,70,.24)'); hg.addColorStop(1, 'rgba(255,150,70,0)'); hud.fillStyle = hg; hud.fillRect(0, 0, W, H);
  hud.fillStyle = '#03060b'; hud.beginPath(); hud.moveTo(-50, H + 50); for (let x = -50; x <= W + 350; x += 16) hud.lineTo(x + ox, 900 + oy - fbm(x * .004, 3) * 150 - fbm(x * .02, 7) * 28); hud.lineTo(W + 350, H + 400); hud.closePath(); hud.fill(); hud.restore();
  const objs = [
    { id: 'C1', x: bx0, y: by0, col: 'rgba(214,255,238,1)', b: frac(t * 4) < .5 ? 1 : .12, name: 'Satellite beacon', f: '4.00 Hz', ok: true, v: 10.3, tr: s => frac(s * 4) < .5 ? 1 : .12 },
    { id: 'C2', x: 820, y: 468, col: 'rgba(205,225,255,1)', b: .82 + .12 * Math.sin(t * 19), name: 'Star', f: 'steady', v: 7.3, tr: s => .82 + .12 * Math.sin(s * 19) },
    { id: 'C3', x: 1240, y: 700, col: 'rgba(255,232,180,1)', b: .9, name: 'Planet', f: 'steady', v: 8.0, tr: () => .9 },
    { id: 'C4', x: 200 + u * 40, y: 250 + u * 5, col: 'rgba(255,255,255,1)', b: frac(t * 1) < .08 ? 1 : .28, name: 'Aircraft strobe', f: '1.0 Hz', v: 8.7, tr: s => frac(s) < .08 ? 1 : .28 },
    { id: 'C5', x: 540, y: 842, col: 'rgba(255,80,60,1)', b: .95, name: 'Decoy lamp (steady red)', f: 'steady', v: 9.4, tr: () => .95 },
  ];
  for (const o of objs) { o.sx = o.x + ox; o.sy = o.y + oy; glow(o.sx, o.sy, 10 + o.b * 26, o.col, .35 + .65 * o.b); }
  glow(objs[3].sx + 10, objs[3].sy + 4, 9, 'rgba(255,60,50,1)', .8);
  hud.save(); hud.globalAlpha = .06; hud.globalCompositeOperation = 'lighter'; const fo = Math.floor(t * 30) * 97; for (let x = -(fo % 512); x < W; x += 512) for (let y = -((fo * 3) % 512); y < H; y += 512) hud.drawImage(GRAIN, x, y); hud.restore();
  hud.save(); hud.fillStyle = 'rgba(79,199,234,.05)'; for (let y = 0; y < H; y += 4) hud.fillRect(0, y, W, 1); hud.restore();
  hud.save(); hud.strokeStyle = 'rgba(79,199,234,.55)'; hud.lineWidth = 1.5; hud.beginPath(); hud.moveTo(W / 2 - 22, H / 2); hud.lineTo(W / 2 + 22, H / 2); hud.moveTo(W / 2, H / 2 - 22); hud.lineTo(W / 2, H / 2 + 22); hud.stroke();
  hud.beginPath(); hud.arc(W / 2, H / 2, 60, 0, 7); hud.globalAlpha = .4; hud.stroke(); hud.restore();
  for (const [x, y, sx, sy] of [[40, 130, 1, 1], [W - 40, 130, -1, 1], [40, H - 40, 1, -1], [W - 40, H - 40, -1, -1]]) { hud.save(); hud.strokeStyle = 'rgba(79,199,234,.35)'; hud.lineWidth = 2; hud.beginPath(); hud.moveTo(x, y + sy * 40); hud.lineTo(x, y); hud.lineTo(x + sx * 40, y); hud.stroke(); hud.restore(); }
  const err = u < 13.4 ? 4.2 + .15 * Math.sin(u * 3) : .198 + 4.0 * Math.exp(-(u - 13.4) / .7);
  T2('VIRTUAL CAMERA  ·  WIDE FIELD  ·  30 FPS', W / 2, 60, 20, CY, { w: 700, f: FM, ls: 3, al: 'center' });
  T2(`AZ ${(azT(t) / D2R).toFixed(2)}°   EL ${(elT(t) / D2R).toFixed(2)}°   ERR ${err.toFixed(2)} mrad`, W / 2, 92, 20, err < .5 ? GR : AM, { f: FM, al: 'center', glow: 6 });
  hud.save(); hud.fillStyle = frac(t) < .5 ? RD : 'rgba(255,90,78,.3)'; hud.beginPath(); hud.arc(W / 2 - 430, 54, 7, 0, 7); hud.fill(); hud.restore(); T2('REC', W / 2 - 416, 60, 16, RD, { w: 700, f: FM });
  if (u > 1.8 && u < 3.6) { const sy = lerp(-20, H, (u - 1.8) / 1.8); hud.save(); const sg = hud.createLinearGradient(0, sy - 80, 0, sy); sg.addColorStop(0, 'rgba(79,199,234,0)'); sg.addColorStop(1, 'rgba(79,199,234,.28)'); hud.fillStyle = sg; hud.fillRect(0, sy - 80, W, 80); hud.fillStyle = 'rgba(79,199,234,.9)'; hud.fillRect(0, sy, W, 2); hud.restore(); }
  const lockA = ss(11, 11.6, u);
  objs.forEach((o, i) => { const ap = ss(2.1 + i * .3, 2.4 + i * .3, u); const decided = u > o.v; const col = decided ? (o.ok ? GR : RD) : CY;
    const a = ap * (decided && !o.ok ? lerp(1, .55, ss(o.v, o.v + 1.5, u)) : 1) * (o.ok ? 1 - lockA : 1);
    brackets(o.sx, o.sy, lerp(60, 34, ease(ap)), col, a); T2(o.id, o.sx - 34, o.sy - 44, 18, col, { w: 700, f: FM, a });
    if (decided && !o.ok) { hud.save(); hud.globalAlpha = a; hud.strokeStyle = RD; hud.lineWidth = 3; hud.beginPath(); hud.moveTo(o.sx - 12, o.sy - 12); hud.lineTo(o.sx + 12, o.sy + 12); hud.moveTo(o.sx + 12, o.sy - 12); hud.lineTo(o.sx - 12, o.sy + 12); hud.stroke(); hud.restore(); } });
  const pa = ss(4.6, 5.4, u); const px = 1390, py = 150, pw = 480;
  panel(px, py, pw, 610, pa); T2('TEMPORAL SIGNATURE  ·  LAST 2 s', px + 24, py + 42, 18, CY, { w: 700, f: FM, ls: 2, a: pa });
  [0, 1, 2, 3, 4].forEach((idx, r) => { const o = objs[idx], ra = ss(5 + r * .3, 5.5 + r * .3, u) * pa; if (ra <= 0) return; const ry = py + 72 + r * 104, decided = u > o.v;
    T2(o.id, px + 24, ry + 26, 18, decided ? (o.ok ? GR : RD) : CY, { w: 700, f: FM, a: ra }); T2(decided ? o.name : 'analysing…', px + 70, ry + 26, 21, decided ? INK : MU, { w: 600, a: ra });
    hud.save(); hud.globalAlpha = ra; const lc = decided ? (o.ok ? GR : 'rgba(255,90,78,.85)') : 'rgba(79,199,234,.9)'; hud.strokeStyle = lc; hud.shadowColor = lc; hud.shadowBlur = 6; hud.lineWidth = 2; hud.beginPath();
    for (let i = 0; i <= 120; i++) { const s = t - 2 + i / 60, v = o.tr(s), xx = px + 24 + i / 120 * 300, yy = ry + 84 - v * 40; if (i === 0) hud.moveTo(xx, yy); else hud.lineTo(xx, yy); } hud.stroke(); hud.restore();
    T2(decided ? o.f : '…', px + 340, ry + 64, 20, decided ? (o.ok ? GR : MU) : MU, { f: FM, a: ra });
    if (decided) { const va = ss(o.v, o.v + .35, u) * ra; hud.save(); hud.globalAlpha = va; rr(px + 340, ry + 72, o.ok ? 118 : 100, 26, 6); hud.fillStyle = o.ok ? 'rgba(93,224,138,.2)' : 'rgba(255,90,78,.18)'; hud.fill(); hud.restore();
      T2(o.ok ? 'BEACON ✓' : 'REJECT', px + 350, ry + 91, 16, o.ok ? GR : RD, { w: 700, f: FM, ls: 1, a: va }); } });
  const na = ss(10.6, 11.3, u); panel(px, py + 628, pw, 92, na, 'rgba(93,224,138,.6)');
  T2('NEURAL VERIFIER  ·  AUC 0.957', px + 24, py + 668, 20, GR, { w: 700, f: FM, a: na, glow: 8 }); T2('vs 0.900 for the classical check (short window)', px + 24, py + 698, 19, MU, { a: na });
  if (lockA > 0) { const b = objs[0], s = lerp(90, 46, ease(ss(11, 11.8, u))), rot = lerp(Math.PI / 4, 0, ease(ss(11, 11.8, u)));
    hud.save(); hud.translate(b.sx, b.sy); hud.rotate(rot); brackets(0, 0, s, GR, lockA, 3); hud.restore();
    hud.save(); hud.globalAlpha = lockA * (.5 + .5 * Math.sin(u * 8)); hud.strokeStyle = GR; hud.lineWidth = 1.5; hud.beginPath(); hud.arc(b.sx, b.sy, s * 1.5, 0, 7); hud.stroke();
    const pr = frac(u * 1.2); hud.globalAlpha = lockA * (1 - pr); hud.beginPath(); hud.arc(b.sx, b.sy, s * (1.5 + pr * 2.5), 0, 7); hud.stroke(); hud.restore();
    T2('BEACON LOCKED', b.sx - 80, b.sy - 8, 26, GR, { w: 700, f: FM, ls: 2, al: 'right', a: lockA, glow: 12 }); T2('4.00 Hz · verified', b.sx - 80, b.sy + 22, 20, INK, { f: FM, al: 'right', a: lockA }); }
  brand(1);
  skyPlot(250, 560, 120, u, t, ss(1, 1.8, u) * (1 - ss(13.8, 14.4, u)));
  stat(80, 150, '1.27 s', 'median acquisition time (64 runs)', ss(14.2, 14.9, u) * (1 - ss(17.4, 18, u)), GR, 420);
  stat(80, 272, '0 / 64', 'runs that ever locked a decoy', ss(14.8, 15.5, u) * (1 - ss(17.4, 18, u)), GR, 420);
  caption('STEP 2  ·  DETECT & VERIFY', 'ZeroDrift\'s virtual camera finds the partner\'s 4 Hz beacon.', 'Stars, planets, aircraft and decoy lamps are rejected by their time signature.', win(u, .6, 17.6));
  vignette();
}

// ---------------------------------------------------------------- boot
const [day, night, mark, isro, sih] = await Promise.all([loadTex('earth-blue-marble.jpg'), loadTex('earth-night.jpg'), loadImg('zerodrift_mark.png'), loadImg('isro.png'), loadImg('sih2026.png')]);
for (const tx of [day, night]) { tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 16; }
eMat.uniforms.day.value = day; eMat.uniforms.night.value = night; Object.assign(IMG, { mark, isro, sih });
let RADIAL;
{ earthG.rotation.y = rotY(25); earthG.updateMatrixWorld(true); const pw = P.clone().applyMatrix4(earthG.matrixWorld); RADIAL = pw.clone();
  const sun = pw.applyAxisAngle(Y, -2.25); sun.y += .2; sun.normalize(); eMat.uniforms.sun.value.copy(sun); sunL.position.copy(sun).multiplyScalar(10); }
{ const s = eMat.uniforms.sun.value, e = RADIAL, f = n => n.toFixed(4);
  const sc = new THREE.Scene(); sc.add(mesh(new THREE.SphereGeometry(10, 64, 32), sky(`varying vec3 vD;void main(){vec3 s=normalize(vec3(${f(s.x)},${f(s.y)},${f(s.z)}));vec3 e=normalize(vec3(${f(e.x)},${f(e.y)},${f(e.z)}));
    float sd=max(dot(vD,s),0.);float earth=smoothstep(-.05,.35,dot(vD,-e));vec3 c=vec3(.10,.2,.42)*earth*1.4+vec3(1.,.95,.85)*(pow(sd,300.)*80.+pow(sd,6.)*.5)+vec3(.01,.012,.02);gl_FragColor=vec4(c,1.);}`)));
  SPACE.environment = pmrem.fromScene(sc, 0).texture; SPACE.environmentIntensity = 1.0;
  const gc = new THREE.Scene(); const m = MOONDIR; gc.add(mesh(new THREE.SphereGeometry(10, 64, 32), sky(`varying vec3 vD;void main(){float h=vD.y;vec3 m=normalize(vec3(${f(m.x)},${f(m.y)},${f(m.z)}));
    vec3 c=mix(vec3(.02,.025,.03),mix(vec3(.10,.16,.26),vec3(.02,.04,.09),smoothstep(0.,.6,h)),smoothstep(-.05,.02,h));c+=vec3(.9,.95,1.)*pow(max(dot(vD,m),0.),200.)*20.;
    c+=vec3(1.,.75,.45)*.4*exp(-pow((vD.x-.9)*3.,2.))*smoothstep(.3,-.1,h);gl_FragColor=vec4(c,1.);}`)));
  GROUND.environment = pmrem.fromScene(gc, 0).texture; GROUND.environmentIntensity = .7; }
await document.fonts.ready;
window.seek = seek; window.DUR = DUR;
const q = new URLSearchParams(location.search);
if (q.has('play')) { const wrap = document.getElementById('wrap'); const fit = () => { const s = Math.min(innerWidth / W, innerHeight / H); wrap.style.transform = `scale(${s})`; }; fit(); addEventListener('resize', fit);
  const t0 = performance.now() - (+q.get('t') || 0) * 1000; const loop = () => { const t = ((performance.now() - t0) / 1000) % DUR; seek(t); requestAnimationFrame(loop); }; loop(); }
else seek(+q.get('t') || 0);
window.READY = true;
