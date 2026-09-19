// Runs docs/assembly.html's tracking simulation headlessly.
//
// The page's sim cannot be checked by screenshot: a headless browser's
// virtual clock barely advances the animation loop, so every screenshot
// catches it at t < 0.3 s and the interesting states never appear. This
// lifts simReset() and simStep() straight out of the page -- not a copy
// of them -- and drives them with a fixed timestep.
//
// It asserts the two claims the page makes in words:
//   1. with the type-2 loop ON, the error converges and reaches LOCK
//   2. with it OFF, a constant-velocity drift leaves a standing error
// If either stops being true, the page is lying to a judge.
import {readFileSync} from 'node:fs';

const src = readFileSync(new URL('../../docs/assembly.html', import.meta.url), 'utf8');
const grab = (start, end) => {
  const a = src.indexOf(start);
  const b = src.indexOf(end, a);
  if (a < 0 || b < 0) throw new Error(`cannot find ${start}`);
  return src.slice(a, b);
};

// Pull out exactly the two functions, by brace matching. Stripping the
// DOM wiring with a regex instead was fragile and silently produced
// invalid JavaScript -- the kind of test harness that fails for its own
// reasons rather than the code's.
function extract(name) {
  const head = src.indexOf(`function ${name}(`);
  if (head < 0) throw new Error(`no function ${name} in the page`);
  let i = src.indexOf('{', head), depth = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === '{') depth++;
    else if (src[j] === '}' && --depth === 0) return src.slice(head, j + 1);
  }
  throw new Error(`unbalanced braces in ${name}`);
}

const FOV = 4.0, PXDEG = 160;
const S = {};
const mk = new Function('S', 'FOV', 'PXDEG',
  extract('simReset') + '\n' + extract('simStep') + '\nreturn {simReset, simStep};');
const {simReset, simStep} = mk(S, FOV, PXDEG);

function run({loop2, drift, seconds = 40, dt = 1 / 60}) {
  simReset();
  S.run = true; S.loop2 = loop2; S.drift = drift; S.noise = false;
  let lockAt = null;
  const tail = [];
  for (let i = 0; i < seconds / dt; i++) {
    simStep(dt);
    if (lockAt === null && S.state === 'LOCK') lockAt = S.t;
    if (S.t > seconds - 6) tail.push(S.err);
  }
  const finite = tail.filter(Number.isFinite);
  const mean = finite.reduce((a, b) => a + b, 0) / Math.max(1, finite.length);
  return {state:S.state, acq:S.acqAt, lockAt, meanTailErr:mean};
}

let bad = 0;
const say = (ok, msg) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${msg}`); if (!ok) bad++; };

const on  = run({loop2:true,  drift:true});
const off = run({loop2:false, drift:true});
const still = run({loop2:true, drift:false});

console.log('type-2 ON,  drift ON :', JSON.stringify(on));
console.log('type-2 OFF, drift ON :', JSON.stringify(off));
console.log('type-2 ON,  drift OFF:', JSON.stringify(still));
console.log('');

say(on.acq !== null && on.acq < 6, `acquires the 4 Hz beacon (at ${on.acq?.toFixed(2)} s)`);
say(on.lockAt !== null, 'reaches LOCK with the type-2 loop on');
say(on.meanTailErr < 12, `settled error ${on.meanTailErr.toFixed(1)} px is inside the 12 px lock gate`);
say(off.meanTailErr > on.meanTailErr * 2,
    `type-2 OFF leaves a larger standing error (${off.meanTailErr.toFixed(1)} px vs ${on.meanTailErr.toFixed(1)} px)`);
say(still.meanTailErr < 12, `no drift, still locks (${still.meanTailErr.toFixed(1)} px)`);

process.exit(bad ? 1 : 0);
