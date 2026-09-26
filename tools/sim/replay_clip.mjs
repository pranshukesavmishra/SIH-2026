// Replay a real camera clip through the live tracker, frame by frame.
//
// Clips come from the live page's RECORD TEST CLIP button (raw camera feed,
// no overlay). Each frame is decoded at its own timestamp, scaled to the
// 640-wide frame the live page processes, and fed to docs/tracker-core.js
// exactly as the page does. Out come a per-frame log and an annotated video
// showing what the tracker locked, so every miss on a real camera in a real
// room can be seen and fixed.
//
//   node tools/sim/replay_clip.mjs clip.webm [--hz 4] [--red] [--out dir] [--no-video]
//
// --red replays with the RED BEACON FILTER on (colour frames, redness score).
//
// Needs ffmpeg and ffprobe on the PATH.
import { createRequire } from 'node:module';
import { spawnSync, spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(import.meta.url);
const Tracker = require(process.env.CORE || '../../docs/tracker-core.js');

const args = process.argv.slice(2);
const clip = args.find(a => !a.startsWith('--') && !/^\d/.test(a));
if (!clip) { console.error('usage: replay_clip.mjs clip.webm [--hz 4] [--out dir] [--no-video]'); process.exit(2); }
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const hzFromName = (/_(\d+(?:\.\d+)?)hz_/.exec(path.basename(clip)) || [])[1];
const hz = parseFloat(opt('--hz', hzFromName || '4'));
const outDir = opt('--out', path.join(path.dirname(clip), path.basename(clip).replace(/\.[^.]+$/, '') + '_replay'));
const wantVideo = !args.includes('--no-video');
const red = args.includes('--red');
fs.mkdirSync(outDir, { recursive: true });

// Geometry and per-frame timestamps.
const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
  '-of', 'csv=p=0', clip], { encoding: 'utf8' });
const [sw, sh] = probe.stdout.trim().split(',').map(Number);
const W = Math.min(640, sw), H = Math.round(sh * W / sw / 2) * 2;
const ts = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=best_effort_timestamp_time',
  '-of', 'csv=p=0', clip], { encoding: 'utf8', maxBuffer: 1 << 26 }).stdout.trim().split('\n').map(Number).filter(Number.isFinite);

const dec = spawnSync('ffmpeg', ['-v', 'error', '-i', clip, '-fps_mode', 'passthrough', '-vf', `scale=${W}:${H}`,
  '-pix_fmt', red ? 'rgb24' : 'gray', '-f', 'rawvideo', '-'], { maxBuffer: 2 ** 31 });
const C = red ? 3 : 1;
const Y = dec.stdout, nFrames = Math.floor(Y.length / (W * H * C));
console.log(`${path.basename(clip)}: ${sw}x${sh} -> ${W}x${H}, ${nFrames} frames, ${ts.length} timestamps, beacon ${hz} Hz`);

const tk = new Tracker({ targetHz: hz, redBoost: red });
const rgba = new Uint8ClampedArray(W * H * 4);
let enc = null;
if (wantVideo) enc = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', `${W}x${H}`, '-r', '30', '-i', '-',
  '-pix_fmt', 'yuv420p', '-crf', '20', path.join(outDir, 'annotated.mp4')]);
const rgb = Buffer.alloc(W * H * 3);
const log = ['t,state,lock_x,lock_y,lit,freq,score,tracks,drop'];
const count = {};
let lastDrop = null, locks = 0, prevLock = false;

function box(x, y, r, col) {
  const x0 = Math.round(x - r), x1 = Math.round(x + r), y0 = Math.round(y - r), y1 = Math.round(y + r);
  const put = (px, py) => { if (px < 0 || py < 0 || px >= W || py >= H) return; const i = (py * W + px) * 3; rgb[i] = col[0]; rgb[i + 1] = col[1]; rgb[i + 2] = col[2]; };
  for (let px = x0; px <= x1; px++) { put(px, y0); put(px, y1); put(px, y0 + 1); put(px, y1 - 1); }
  for (let py = y0; py <= y1; py++) { put(x0, py); put(x1, py); put(x0 + 1, py); put(x1 - 1, py); }
}

for (let f = 0; f < nFrames; f++) {
  const t = ts[f] !== undefined ? ts[f] : f / 30;
  const off = f * W * H * C;
  if (red) for (let i = 0, q = 0, o = off; i < W * H; i++, q += 4, o += 3) { rgba[q] = Y[o]; rgba[q + 1] = Y[o + 1]; rgba[q + 2] = Y[o + 2]; rgba[q + 3] = 255; }
  else for (let i = 0, q = 0; i < W * H; i++, q += 4) { const v = Y[off + i]; rgba[q] = rgba[q + 1] = rgba[q + 2] = v; rgba[q + 3] = 255; }
  tk.process(rgba, W, H, t, false);
  const L = tk.target;
  count[tk.state] = (count[tk.state] || 0) + 1;
  if (L && !prevLock) locks++;
  prevLock = !!L;
  const drop = tk.lastDrop && tk.lastDrop !== lastDrop ? tk.lastDrop.why : '';
  lastDrop = tk.lastDrop;
  log.push([t.toFixed(3), tk.state, L ? L.x.toFixed(1) : '', L ? L.y.toFixed(1) : '', L ? +L.lit : '',
            L ? L.freq.toFixed(2) : '', L ? L.score.toFixed(2) : '', tk.tracks.length, JSON.stringify(drop)].join(','));
  if (enc) {
    if (red) Y.copy(rgb, 0, off, off + W * H * 3);
    else for (let i = 0; i < W * H; i++) { const v = Y[off + i]; rgb[3 * i] = rgb[3 * i + 1] = rgb[3 * i + 2] = v; }
    for (const tr of tk.tracks) if (tr.hits >= 6 && tr.lit) box(tr.x, tr.y, Math.max(5, tr.size * 0.6), tr.pass > 0 ? [80, 200, 235] : [110, 110, 110]);
    if (L) box(L.x, L.y, Math.max(8, L.size * 0.8), L.lit ? [60, 220, 140] : [255, 190, 70]);
    enc.stdin.write(Buffer.from(rgb));
  }
}
fs.writeFileSync(path.join(outDir, 'frames.csv'), log.join('\n') + '\n');
const pct = k => (100 * (count[k] || 0) / Math.max(1, nFrames)).toFixed(1);
const summary = `frames ${nFrames}  locked ${pct('LOCKED')}%  coasting ${pct('COASTING')}%  searching ${pct('SEARCHING')}%  ` +
                `confirming ${pct('CONFIRMING')}%  reacquiring ${pct('REACQUIRING')}%  lock-starts ${locks}`;
console.log(summary);
fs.writeFileSync(path.join(outDir, 'summary.txt'), summary + '\n');
if (enc) { enc.stdin.end(); await new Promise(r => enc.on('close', r)); console.log('annotated video:', path.join(outDir, 'annotated.mp4')); }
