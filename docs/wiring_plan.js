/* ZeroDrift MK2 -- THE wiring plan. One file, every wiring view:
   the 2D breadboard page (wiring.html), the 3D page (wiring3d.html) and the
   printed PDF are all drawn from this, so they can never disagree.

   Pins match tools/rig/rig_firmware_v2.ino: pan STEP/DIR = D2/D3, tilt
   STEP/DIR = D4/D5, laser = D7, TCA9548A on A4 (SDA) / A5 (SCL) at 0x70 (A0-A2
   to GND), pan AS5600 on multiplexer channel 0, 1/16 microstepping (MS1-3 high).

   Breadboard: 830 points, columns 1-63 (1 on the LEFT), rows a-e | middle gap | f-j
   (a at the TOP). Rails: TOP red = +12 V, TOP blue = GND, BOTTOM red = +5 V,
   BOTTOM blue = GND. Rail holes come in groups of 5 (columns 3-7, 9-13 ... 57-61);
   every rail end below sits on one of them, straight above or below its pin.
   Endpoint names:  'a27' a hole  ·  'T+27' 'T-28' 'B+13' 'B-15' a rail hole at
   that column  ·  'dev:PIN' a pin on a part that is not on the breadboard. */
(function (root) {
  const C = {
    v12: '#e53935', v5: '#f59e0b', gnd: '#2b2f36', step: '#8b5cf6', dir: '#ec4899',
    sda: '#2f7bff', scl: '#d4a800', las: '#0d9488', link: '#64748b', usb: '#9aa3ad',
    mBlack: '#15171a', mGreen: '#16a34a', mRed: '#dc2626', mBlue: '#2563eb',
  };
  const ROWS = 'abcdefghij';
  const RAIL_COLS = [];
  for (let g = 3; g <= 57; g += 6) for (let k = 0; k < 5; k++) RAIL_COLS.push(g + k);
  const RAILS = {
    'T+': { name: 'TOP red rail', short: 'TOP red', net: '+12 V', color: C.v12 },
    'T-': { name: 'TOP blue rail', short: 'TOP blue', net: 'GND', color: C.gnd },
    'B+': { name: 'BOTTOM red rail', short: 'BOTTOM red', net: '+5 V', color: C.v5 },
    'B-': { name: 'BOTTOM blue rail', short: 'BOTTOM blue', net: 'GND', color: C.gnd },
  };

  const DRV_TOP = ['VMOT', 'GND', '2B', '2A', '1A', '1B', 'VDD', 'GND'];
  const DRV_BOT = ['EN', 'MS1', 'MS2', 'MS3', 'RST', 'SLP', 'STEP', 'DIR'];
  const parts = {
    nano: { label: 'ARDUINO NANO', note: 'USB-C to the LEFT', cols: [4, 18], rows: ['d', 'h'],
      top: ['D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'GND', 'RST', 'RX0', 'TX1'],
      bottom: ['D13', '3V3', 'REF', 'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', '5V', 'RST', 'GND', 'VIN'] },
    pan: { label: 'PAN DRIVER', note: 'A4988 · runs the bottom motor', cols: [27, 34], rows: ['d', 'g'], top: DRV_TOP, bottom: DRV_BOT },
    tilt: { label: 'TILT DRIVER', note: 'A4988 · runs the top motor', cols: [39, 46], rows: ['d', 'g'], top: DRV_TOP, bottom: DRV_BOT },
  };
  // off-board parts: their pins, as named in the wire list
  const devices = {
    jack: { label: 'DC JACK', note: 'barrel socket with 2 screw terminals', pins: ['+', '-'] },
    sw: { label: 'SWITCH', note: 'toggle · motor kill switch', pins: ['OUT', 'MID', 'spare'] },
    pm: { label: 'PAN MOTOR', note: 'the bottom motor', pins: ['A1', 'A2', 'B1', 'B2'] },
    tm: { label: 'TILT MOTOR', note: 'the top motor, in the head', pins: ['A1', 'A2', 'B1', 'B2'] },
    mux: { label: 'MULTIPLEXER', note: 'TCA9548A · off the breadboard', pins: ['VIN', 'GND', 'SDA', 'SCL', 'RST', 'A0', 'A1', 'A2', 'SD0', 'SC0'] },
    as: { label: 'AS5600', note: 'pan sensor · on the rig', pins: ['VCC', 'GND', 'DIR', 'SDA', 'SCL'] },
    las: { label: 'LASER', note: 'KY-008 · on the head', pins: ['-', 'mid', 'S'] },
    usb: { label: 'USB', pins: ['NANO'] }, laptop: { label: 'LAPTOP', pins: ['USB'] },
  };
  // 100 uF electrolytics: long leg (+) in TOP red, striped leg (-) in TOP blue, same column
  const caps = [{ id: 'C1', col: 25, step: 4, near: 'pan' }, { id: 'C2', col: 37, step: 5, near: 'tilt' }];

  // [number, step, from, to, colour, from-label, to-label]
  const W = [
    [1, 2, 'jack:+', 'sw:MID', C.v12, 'DC jack  + screw', 'switch  MIDDLE pin'],
    [2, 2, 'sw:OUT', 'T+53', C.v12, 'switch  outer pin', 'TOP red rail  (+12 V)'],
    [3, 2, 'jack:-', 'T-61', C.gnd, 'DC jack  − screw', 'TOP blue rail  (GND)'],
    [4, 3, 'j15', 'B+15', C.v5, 'Nano  5V', 'BOTTOM red rail  (+5 V)'],
    [5, 3, 'j17', 'B-17', C.gnd, 'Nano  GND', 'BOTTOM blue rail  (GND)'],
    [6, 3, 'T-59', 'B-59', C.gnd, 'TOP blue rail', 'BOTTOM blue rail  (joins the grounds)'],
  ];
  const driverWires = (P, first, step, name) => {
    const c0 = P.cols[0];
    return [
      [first + 0, step, `a${c0}`, `T+${c0}`, C.v12, `${name}  VMOT`, 'TOP red rail  (+12 V)'],
      [first + 1, step, `a${c0 + 1}`, `T-${c0 + 1}`, C.gnd, `${name}  GND (next to VMOT)`, 'TOP blue rail  (GND)'],
      [first + 2, step, `c${c0 + 6}`, `B+${c0 + 8}`, C.v5, `${name}  VDD`, 'BOTTOM red rail  (+5 V) · NEVER 12 V'],
      [first + 3, step, `a${c0 + 7}`, `T-${c0 + 7}`, C.gnd, `${name}  GND (next to VDD)`, 'TOP blue rail  (GND)'],
      [first + 4, step, `j${c0}`, `B-${c0}`, C.gnd, `${name}  EN`, 'BOTTOM blue rail  (GND)'],
      [first + 5, step, `j${c0 + 1}`, `B+${c0 + 1}`, C.v5, `${name}  MS1`, 'BOTTOM red rail  (+5 V)'],
      [first + 6, step, `j${c0 + 2}`, `B+${c0 + 2}`, C.v5, `${name}  MS2`, 'BOTTOM red rail  (+5 V)'],
      [first + 7, step, `j${c0 + 3}`, `B+${c0 + 3}`, C.v5, `${name}  MS3`, 'BOTTOM red rail  (+5 V)'],
      [first + 8, step, `j${c0 + 4}`, `j${c0 + 5}`, C.link, `${name}  RST`, `${name}  SLP  (short jumper)`],
    ];
  };
  W.push(...driverWires(parts.pan, 7, 4, 'pan'));
  W.push(...driverWires(parts.tilt, 16, 5, 'tilt'));
  W.push(
    [25, 6, 'a14', 'i33', C.step, 'Nano  D2', 'pan  STEP'],
    [26, 6, 'a13', 'h34', C.dir, 'Nano  D3', 'pan  DIR'],
    [27, 6, 'b12', 'h45', C.step, 'Nano  D4', 'tilt  STEP'],
    [28, 6, 'c11', 'i46', C.dir, 'Nano  D5', 'tilt  DIR'],
    [29, 7, 'pm:A1', 'b29', C.mBlack, 'pan motor  black', 'pan  2B'],
    [30, 7, 'pm:A2', 'b30', C.mGreen, 'pan motor  green', 'pan  2A'],
    [31, 7, 'pm:B1', 'b31', C.mRed, 'pan motor  red', 'pan  1A'],
    [32, 7, 'pm:B2', 'b32', C.mBlue, 'pan motor  blue', 'pan  1B'],
    [33, 7, 'tm:A1', 'b41', C.mBlack, 'tilt motor  black', 'tilt  2B'],
    [34, 7, 'tm:A2', 'b42', C.mGreen, 'tilt motor  green', 'tilt  2A'],
    [35, 7, 'tm:B1', 'b43', C.mRed, 'tilt motor  red', 'tilt  1A'],
    [36, 7, 'tm:B2', 'b44', C.mBlue, 'tilt motor  blue', 'tilt  1B'],
    [37, 8, 'mux:VIN', 'B+9', C.v5, 'multiplexer  VIN', 'BOTTOM red rail  (+5 V)'],
    [38, 8, 'mux:GND', 'B-10', C.gnd, 'multiplexer  GND', 'BOTTOM blue rail  (GND)'],
    [39, 8, 'mux:SDA', 'j11', C.sda, 'multiplexer  SDA', 'Nano  A4'],
    [40, 8, 'mux:SCL', 'j12', C.scl, 'multiplexer  SCL', 'Nano  A5'],
    [41, 8, 'mux:A0', 'B-13', C.gnd, 'multiplexer  A0', 'BOTTOM blue rail  (GND)'],
    [42, 8, 'mux:A1', 'B-16', C.gnd, 'multiplexer  A1', 'BOTTOM blue rail  (GND)'],
    [43, 8, 'mux:A2', 'B-18', C.gnd, 'multiplexer  A2', 'BOTTOM blue rail  (GND)'],
    [44, 8, 'mux:SD0', 'as:SDA', C.sda, 'multiplexer  SD0', 'AS5600  SDA'],
    [45, 8, 'mux:SC0', 'as:SCL', C.scl, 'multiplexer  SC0', 'AS5600  SCL'],
    [46, 8, 'as:VCC', 'B+51', C.v5, 'AS5600  VCC', 'BOTTOM red rail  (+5 V)'],
    [47, 8, 'as:GND', 'B-52', C.gnd, 'AS5600  GND', 'BOTTOM blue rail  (GND)'],
    [48, 8, 'as:DIR', 'B-53', C.gnd, 'AS5600  DIR (if your board has it)', 'BOTTOM blue rail  (GND)'],
    [49, 9, 'las:S', 'a9', C.las, 'laser  S', 'Nano  D7'],
    [50, 9, 'las:-', 'T-7', C.gnd, 'laser  −', 'TOP blue rail  (GND)'],
    [51, 10, 'usb:NANO', 'laptop:USB', C.usb, 'Nano  USB-C', 'laptop  (through the hub)'],
  );
  const wires = W.map(([n, step, from, to, color, a, b]) => ({ n, step, from, to, color, a, b }));

  /* An endpoint name -> what it is. */
  function parse(end) {
    let m = /^([TB][+-])(\d+)$/.exec(end);
    if (m) return { kind: 'rail', rail: m[1], col: +m[2] };
    m = /^([a-j])(\d+)$/.exec(end);
    if (m) return { kind: 'hole', row: m[1], col: +m[2] };
    const [dev, pin] = end.split(':');
    return { kind: 'dev', dev, pin };
  }
  /* Which part pin shares the 5-hole strip of this hole (null if nothing). */
  function stripPin(col, row) {
    const top = ROWS.indexOf(row) < 5;
    for (const [id, P] of Object.entries(parts)) {
      if (col < P.cols[0] || col > P.cols[1]) continue;
      const i = col - P.cols[0];
      return { part: id, pin: top ? P.top[i] : P.bottom[i] };
    }
    return null;
  }
  /* Human text for an endpoint: 'hole a27', 'TOP red rail, column 27', 'DC jack  + screw'. */
  function where(end) {
    const p = parse(end);
    if (p.kind === 'hole') return `hole ${p.row}${p.col}`;
    if (p.kind === 'rail') return `${RAILS[p.rail].name}, col ${p.col}`;
    return '';
  }

  const steps = [
    { title: 'Place the parts', short: 'nothing wired yet', parts: ['nano', 'pan', 'tilt'],
      text: 'Everything unplugged. Hold the breadboard so column 1 is on the LEFT and row a is at the TOP. Push each part in ACROSS the middle gap. Arduino Nano: columns 4-18, top pins in row d, bottom pins in row h, USB-C pointing LEFT. Pan driver: columns 27-34. Tilt driver: columns 39-46. Both drivers: pins in rows d and g, the pin marked VMOT at the TOP-LEFT. The 5 holes of one column on one side of the gap (a-e, or f-j) are joined inside the board.',
      tip: 'Nano 4-18 · pan driver 27-34 · tilt driver 39-46 · VMOT top-left' },
    { title: '12 V in from the adapter', short: 'adapter → DC jack → switch → TOP rails', warn: true, parts: ['jack', 'sw'],
      text: 'Adapter UNPLUGGED from the wall. Push its round plug into the DC jack. Wire 1: loosen the jack\'s + screw, push in the metal pin of a red jumper, tighten; the other end goes on the switch\'s MIDDLE pin. Wire 2: the switch\'s outer pin to the TOP red rail. Wire 3: the jack\'s − screw to the TOP blue rail. Test it: switch ON, adapter into the wall, multimeter on DC V, black probe in TOP blue, red probe in TOP red = about +12 V. A minus sign means + and − are swapped. Switch OFF and unplug again.',
      tip: 'TOP red = +12 V · TOP blue = GND · meter must read +12 V' },
    { title: '5 V and ONE ground', short: 'Nano 5V + GND, join the GND rails', warn: true,
      text: 'Wire 4: Nano 5V (hole j15) to the BOTTOM red rail: this rail is now +5 V. Wire 5: Nano GND (hole j17) to the BOTTOM blue rail. Wire 6: TOP blue to BOTTOM blue at column 59: now every GND is the same. Never join the two red rails. Then beep-test each rail from column 3 to column 61: some boards cut the rails in the middle. No beep = bridge the break with a short jumper.',
      tip: 'BOTTOM red = +5 V · blue rails joined · red rails NEVER joined' },
    { title: 'Pan driver', short: '9 wires + capacitor C1', warn: true, parts: ['pan'],
      text: 'VMOT (a27) to TOP red, the GND beside it (a28) to TOP blue, the last GND (a34) to TOP blue. VDD (c33) to BOTTOM red at column 35: it goes round the driver\'s corner, and it must never touch 12 V. EN (j27) to BOTTOM blue. MS1, MS2, MS3 (j28, j29, j30) to BOTTOM red for 1/16 steps. One short jumper from j31 to j32 joins RST and SLP. Capacitor C1 (100 µF) at column 25: long leg in TOP red, the leg on the striped side in TOP blue.',
      tip: 'VMOT → +12 V · VDD → +5 V · EN → GND · MS1-3 → +5 V · RST ↔ SLP · C1 stripe → blue' },
    { title: 'Tilt driver', short: 'the same, 12 columns right', parts: ['tilt'],
      text: 'Exactly the same nine wires, 12 columns to the right. VMOT (a39) to TOP red. GND (a40) and GND (a46) to TOP blue. VDD (c45) to BOTTOM red at column 47. EN (j39) to BOTTOM blue. MS1-3 (j40, j41, j42) to BOTTOM red. Jumper j43 to j44. Capacitor C2 at column 37: long leg in red, stripe in blue.',
      tip: 'same as the pan driver · C2 stripe → blue' },
    { title: 'STEP and DIR', short: 'D2 D3 pan · D4 D5 tilt',
      text: 'Four long jumpers from the Nano\'s top holes to the drivers\' bottom holes. D2 (a14) to pan STEP (i33). D3 (a13) to pan DIR (h34). D4 (b12) to tilt STEP (h45). D5 (c11) to tilt DIR (i46). The picture shows a tidy route. Any route is fine as long as both ends are in the right holes.',
      tip: 'D2 → pan STEP · D3 → pan DIR · D4 → tilt STEP · D5 → tilt DIR' },
    { title: 'Motors', short: 'find the two pairs first', warn: true, parts: ['pm', 'tm'],
      text: 'Each motor has 4 wires = 2 coils. Multimeter on Ω: two wires that read about 2-4 Ω are one pair (usually black + green and red + blue, but measure). Pan motor (bottom): black b29, green b30, red b31, blue b32. Tilt motor (top): black b41, green b42, red b43, blue b44. Never plug or unplug a motor while 12 V is on.',
      tip: 'pair 1 → 2B 2A · pair 2 → 1A 1B · never while powered' },
    { title: 'Pan sensor', short: 'multiplexer + AS5600', parts: ['mux', 'as'],
      text: 'The multiplexer (TCA9548A) stays OFF the breadboard, below it. Use male-to-female jumpers: female on its pin, male in the hole. VIN to BOTTOM red. GND to BOTTOM blue. SDA to j11 (Nano A4). SCL to j12 (Nano A5). A0, A1, A2 to BOTTOM blue. RST: nothing. Channel 0: SD0 to the AS5600\'s SDA, SC0 to its SCL. AS5600: VCC to BOTTOM red, GND and DIR to BOTTOM blue.',
      tip: 'go by the labels printed on your boards · SDA → A4 · SCL → A5 · SD0/SC0 → AS5600' },
    { title: 'Laser', short: 'S → D7, − → GND', parts: ['las'],
      text: 'Laser board (KY-008): S to hole a9 (Nano D7). − to the TOP blue rail. The middle pin connects to nothing.',
      tip: 'S → D7 · − → GND · middle → nothing' },
    { title: 'USB', short: 'Nano to the laptop',
      text: 'The Nano\'s USB-C to the laptop (through the hub). The webcam\'s USB goes to the laptop too: it never touches the breadboard. Upload the rig code now: tools/rig/flash.sh rig.',
      tip: 'USB 1 = Nano · USB 2 = webcam' },
    { title: 'Set the current', short: 'Vref 0.55 V · 12 V stays OFF', parts: ['pan', 'tilt'],
      text: 'No new wires. USB in, 12 V switch OFF. Multimeter on DC V: black probe in any blue rail, red probe touching the metal top of the small screw on the pan driver. Turn the screw gently with a small screwdriver until it reads 0.55 V. Then the same on the tilt driver.',
      tip: 'Vref = 0.55 V on both drivers' },
    { title: 'Check, then power on', short: 'multimeter first', warn: true, all: true,
      text: 'Everything unplugged: beep-test TOP red to BOTTOM red, and TOP red to TOP blue. Neither may beep (a short chirp is the capacitor charging, that is fine). USB in: BOTTOM red reads about 5 V. Switch OFF, adapter in, switch ON: TOP red reads about 12 V, both motor shafts go stiff, nothing gets hot. Live page: CONNECT RIG, then TEST MOTION. To stop: 12 V off first, then USB.',
      tip: 'on: USB, then 12 V · off: 12 V, then USB' },
  ];
  root.ZD_WIRING = { C, ROWS, RAIL_COLS, RAILS, parts, devices, caps, wires, steps, parse, stripPin, where };
})(typeof window !== 'undefined' ? window : globalThis);
