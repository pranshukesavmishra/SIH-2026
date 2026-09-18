# ZeroDrift Terminal Mk3 — design, parts, and build

**This supersedes `rig_mk2_build_guide.md` and the servo-based Mk1.**
Mk1 and Mk2 were table demos: a camera on a tripod watching from the
side, a laser on a gimbal, a laptop in the middle. Mk3 is a *terminal* —
one self-contained unit that scans for the beacon with its own camera,
identifies it, and puts its own laser on it, with the alignment loop
closed on-board.

That is the thing PS26169 actually describes, and it is the difference
between "we simulated a terminal" and "here is one."

---
## 0. The idea the whole design rests on

The camera rides on the gimbal, boresighted with the laser. So the
camera sees **both** the beacon and its own laser dot.

That removes the hardest problem in this build. Camera and laser cannot
occupy the same point in space, so "beacon centred in the image" is not
"laser on the beacon" — the offset between them is parallax, and it
depends on range:

| Separation | @ 0.6 m | @ 1 m | @ 2 m | @ 3 m | @ 5 m |
|---|---|---|---|---|---|
| 60 mm | 100 mrad | 60 mrad | 30 mrad | 20 mrad | 12 mrad |
| 20 mm | 33 mrad | 20 mrad | 10 mrad | 6.7 mrad | 4 mrad |

Against a ~1 mrad pointing budget, parallax is not a correction — it is
10× to 100× the entire error budget. Every approach that *models* it
(calibrate an offset, estimate range, measure the baseline) is fighting
a losing battle against mount flex, thermal drift and unknown range.

**So don't model it. Measure it.**

1. The beacon modulates at **4.0 Hz**. The laser modulates at **7.0 Hz**.
2. Both appear in the camera image. Both are identified by their
   modulation, using the same Goertzel scoring the simulator already
   uses — brightness is not identity, modulation is.
3. The control error is the pixel vector **from the laser dot to the
   beacon**, driven to zero.

Parallax, boresight misalignment, mount flex, thermal drift, range, and
every mechanical tolerance in the build cancel identically, because they
all displace the dot and the loop is closed on the dot. The camera is
the metrology instrument, not a proxy for one.

This maps cleanly onto the problem statement's architecture:

| PS26169 stage | Mk3 |
|---|---|
| Coarse acquisition | Gimbal scans, finds the 4 Hz beacon by modulation, slews to centre it |
| Handoff | Laser on; dot enters the FOV |
| Fine alignment | Closed loop on (dot → beacon) pixel error |

---
## 1. Architecture

```
            ┌─────────────────────────────────────────┐
            │  HEAD  — rides on the gimbal            │
            │    Global-shutter camera + 12 mm lens   │
            │    650 nm bandpass filter               │
            │    650 nm laser, modulated at 7 Hz      │
            │    ~20 mm between optical axes          │
            └───────────────────┬─────────────────────┘
                     CSI ribbon │ + laser wire, service loop
            ┌───────────────────┴─────────────────────┐
            │  GIMBAL                                 │
            │    TILT: NEMA17 0.9° + GT2 3:1 + AS5600 │
            │    PAN : NEMA17 0.9° + GT2 3:1 + AS5600 │
            └───────────────────┬─────────────────────┘
                                │
            ┌───────────────────┴─────────────────────┐
            │  BASE                                   │
            │    Raspberry Pi 5    — vision, pipeline │
            │    Arduino Nano      — motion, real-time│
            │    2× TMC2209        — 1/32 microstep   │
            │    TCA9548A          — encoder mux      │
            │    12 V 5 A PSU + 5 V buck              │
            └─────────────────────────────────────────┘
```

**Why two processors.** Linux is not a real-time OS. A Pi cannot emit
step pulses with reliable microsecond timing — jitter there *is* a
skipped step, which is exactly the failure the encoders exist to catch.
So the Nano does motion and nothing else, the Pi does vision and the
pipeline, and they speak over USB serial. This is how real pointing
systems are built, and it is a good answer when a judge asks why the
architecture is split.

**Why no servos, anywhere.** Mk1 stripped two. A hobby servo holds
position by fighting its own gear train, so the tilt axis is loaded even
at rest, and there is no clutch between a knock and a brass gear. Its
backlash (~1°, 17 mrad) is also larger than the error this rig is built
to measure. Resolution now comes from microstepping and a belt, neither
of which has teeth to shear.

**Why a belt and not a gearbox.** A planetary gearhead has 1–2° of
backlash, which would swamp everything. A tensioned GT2 belt has
effectively none, and the 3:1 reduction divides the motor's *own*
positioning error by three — not just the step size. That distinction
matters: microstepping buys resolution, not accuracy. A stepper's true
error is roughly ±5% of a full step regardless of how finely you divide
it. The belt is the only item in this build that attacks that directly.

### Resolution budget

| Stage | Value |
|---|---|
| NEMA17 0.9°/step, TMC2209 @ 1/32 | 0.0281°/step |
| ÷ GT2 3:1 belt | **0.0094°/step = 0.16 mrad** |
| AS5600 12-bit on motor shaft, ÷3 | 0.0293° → **0.51 mrad** measured |
| Camera, 12 mm lens, 1456 px across 22° | 0.0151°/px = **0.26 mrad/px** |
| Centroid, ~1/5 px on a clean spot | **~0.05 mrad** |

The mechanism is the limit at roughly **0.5 mrad**, encoder-verified.
That is an honest, defensible number for a hackathon build — and it is
8× better than the Mk2 design it replaces. It is *not* the simulator's
microradian figure, and `docs/defence_brief.md` already takes the
position that saying so plainly reads as rigour.

---
## 2. Bill of materials

Prices marked ✅ were verified against live Amazon.in listings in the
September pricing pass. Everything else is an estimate from component-class
market ranges and **must be checked before ordering** — say which is which
if a judge asks what the rig cost.

### 2.1 Head — optics

| Item | Qty | Est. unit | Notes |
|---|---|---|---|
| Raspberry Pi Global Shutter Camera (IMX296, C/CS mount) | 1 | ₹5,500–7,000 | **Global shutter is not optional.** A rolling shutter smears a blinking source while the head is slewing, and can alias against the 4 Hz blink outright. |
| C-mount 12 mm lens, 1/2.9″ or larger | 1 | ₹1,200–2,500 | ~22° horizontal FOV. Manual iris and focus — lock both once set. |
| 650 nm bandpass filter, 25 mm, ~±20 nm | 1 | ₹1,500–3,000 | Threads or tapes in front of the lens. Rejects room lighting. The single biggest detection-reliability win in the build. |
| 650 nm laser diode module, 5 mW, focusable, TTL input | 1 | ₹250–600 | 5 mW = Class 3R. Do not exceed it. TTL input so the Nano can modulate it at 7 Hz. |
| Head bracket, laser-cut aluminium or 3D printed | 1 | ₹300–800 | Holds camera and laser rigidly, optical axes ~20 mm apart, parallel. |

### 2.2 Gimbal — motion

| Item | Qty | Est. unit | Notes |
|---|---|---|---|
| NEMA17 stepper, **0.9°/step**, **dual shaft** | 2 | ₹1,100–1,600 | **Both properties are mandatory.** Dual shaft: the encoder magnet glues to the rear shaft. 0.9°: halves the error of a standard 1.8° motor. |
| TMC2209 stepper driver | 2 | ₹450–1,100 ✅ | 1/32 microstepping, quiet, and StallGuard gives a second, independent stall signal alongside the encoders. |
| AS5600 magnetic encoder breakout | 2 | ₹249 ✅ | |
| **Diametrically magnetised** magnet, 6×2.5 mm | 2 | ₹80–150 | **Read this twice.** An axially magnetised magnet will not work and is what usually ships in cheap kits. |
| TCA9548A I²C multiplexer | 1 | ₹199 ✅ | Both AS5600s are fixed at address 0x36 and cannot share a bus. |
| GT2 pulley 20 T, 5 mm bore | 2 | ₹120–200 | Motor side. |
| GT2 pulley 60 T, 8 mm bore | 2 | ₹250–450 | Output side. 3:1. |
| GT2 closed belt, 6 mm wide, ~200–300 mm | 2 | ₹150–250 | Measure your centre distance before ordering the length. |
| 608ZZ bearing | 4 | ₹40–80 | Two per output shaft. |
| 8 mm steel shaft, 100 mm | 2 | ₹100–200 | Output shafts. |
| Aluminium or acrylic structure, 5 mm | 1 set | ₹800–1,500 | Base plate, pan platform, tilt yoke. Laser-cut from the drawings you make; do not improvise this in wood. |

### 2.3 Base — compute and power

| Item | Qty | Est. unit | Notes |
|---|---|---|---|
| Raspberry Pi 5, 8 GB | 1 | ₹7,500–9,000 | Runs the actual ZeroDrift pipeline. Proving the software runs on embedded hardware is a real pitch asset. |
| Pi 5 active cooler | 1 | ₹600–900 | It throttles without one under sustained vision load. |
| microSD 64 GB A2, or NVMe + HAT | 1 | ₹800–3,500 | |
| Pi Camera FPC cable for Pi 5, 300–500 mm | 1 | ₹250–500 | Pi 5 uses the narrow 22-pin connector — the Pi 4 cable does not fit. |
| Arduino Nano | 1 | ₹250–400 | Motion controller. Separate from the beacon's. |
| 12 V 5 A DC PSU | 1 | ₹450–700 | Motor supply. |
| 5 V 5 A buck converter | 1 | ₹200–400 | Pi supply, from the 12 V rail. |
| 100 µF 25 V electrolytic capacitor | 2 | ₹10 | **Across VMOT on each driver. The datasheet requires it. Omitting it destroys drivers on power-up.** |
| Dupont wires, screw terminals, heat-shrink, JST | 1 set | ₹400–700 | |
| M3 screw/nut/standoff assortment | 1 set | ₹300–500 | |
| Emergency cutoff switch, 12 V rated | 1 | ₹100–200 | Kills motor power without killing the Pi. |

### 2.4 Beacon and decoy

| Item | Qty | Est. unit | Notes |
|---|---|---|---|
| Arduino Nano | 1 | ₹250–400 | Beacon's own. |
| 650 nm LED, 3 W, with heatsink/star | 1 | ₹150–300 | Must match the camera's bandpass filter. |
| Constant-current LED driver or power MOSFET + resistor | 1 | ₹80–200 | A 3 W LED will not run from a digital pin. |
| Diffuser (ping-pong ball or opal acrylic) | 1 | ₹40 | Makes it a point source from any angle. |
| Li-ion pack or 9 V + regulator | 1 | ₹300–600 | |
| Enclosure, switch, tripod thread | 1 | ₹200–400 | |
| **Decoy**: bright white LED, resistor, cell, switch | 1 | ₹100–200 | Steady, no chip, deliberately *brighter* than the beacon. Exists so the rejection claim is demonstrable, not asserted. |

### 2.5 Totals

| Subsystem | Range |
|---|---|
| Head (optics) | ₹8,750–13,900 |
| Gimbal (motion + structure) | ₹5,400–8,900 |
| Base (compute + power) | ₹11,300–17,200 |
| Beacon + decoy | ₹1,120–2,140 |
| **Total** | **₹26,600–42,100** |

Two honest notes. The camera and the Pi are over half of it — if that
is too much, the fallback is a UVC camera module with an M12 12 mm lens
(₹2,500–4,500) driven from the laptop, which costs roughly ₹20,000 less
and loses the global shutter and the self-contained story, but keeps
every other property including the dot-tracking loop. And the filter is
the highest value-per-rupee item in the entire list; do not cut it.

---
## 3. Build order

Each stage ends in something testable. Do not proceed past a stage that
does not pass its check — that is how the Mk1/Mk2 protocol mismatch
survived three weeks undetected.

**Stage 1 — Beacon and decoy.** No moving parts. Flash the beacon, and
verify the blink rate with a phone slow-motion capture or a scope before
believing the number printed on it. *Check: beacon measured at 4.00 ±
0.05 Hz.*

**Stage 2 — Camera and filter, on the bench, not yet mounted.** Pi +
camera + lens + filter, pointed at the beacon across the room. Lock
exposure and gain manually; auto-exposure hunts on every blink and will
ruin detection. *Check: the pipeline scores the beacon's 4 Hz blink and
rejects the decoy, at your intended demo range, under your demo
lighting.*

**Stage 3 — One axis, open loop.** Pan motor, TMC2209, belt, Nano.
Command ±45° and confirm it goes there and comes back. *Check: `!`
self-test completes; commanded degrees match a protractor.*

**Stage 4 — Encoders.** AS5600s on both rear shafts through the mux.
*Check: `?` returns `src=E`, and the encoder reading matches the
commanded angle after a move to within 0.05°.*

**Stage 5 — Both axes, structure, cable loom.** Service loop for the
camera ribbon; confirm full travel does not strain it. *Check: ±90° pan
and −30°/+45° tilt with no cable tension, no skipped steps.*

**Stage 6 — Boresight and the dot loop.** Laser on at 7 Hz. Confirm the
camera sees both the dot and the beacon and can tell them apart by
modulation. *Check: `boresight` reports a stable dot-to-beacon pixel
vector.*

**Stage 7 — Full acquisition.** Scan, identify, slew, close on the dot.
*Check: the laser lands on the beacon, from a cold start, repeatably,
with the decoy lit throughout and never chased.*

---
## 4. Search: the cost of a narrow lens

A 12 mm lens sees 22°×16°. Covering a 90°×40° volume takes 24 tiles at
20% overlap, and a 4 Hz blink needs at least two full periods — 0.5 s —
to identify, so budget ~0.4 s per tile once settled. That is roughly
**10 seconds for a full cold search**.

That is not a defect to hide; it is the coarse-acquisition problem the
problem statement is about, made real. A wide-angle camera would make
acquisition trivial and the demo meaningless. If 10 s is too slow to
hold a judge's attention, narrow the *scanned volume* (the beacon's
rough bearing is known in any real deployment) rather than widening the
lens — and say exactly that, because it is what a real terminal does
with ephemeris.

---
## 5. Safety

- 5 mW, Class 3R, 650 nm. Never at eyes or faces. The head moves on its
  own, so soft-limit both axes in firmware and keep the laser off during
  any scan that sweeps toward standing people.
- Kill switch on the 12 V motor rail, reachable without leaning into the
  gimbal's travel.
- Steppers warm up under stall. Do not leave the rig powered and jammed.

---
## 6. Wiring — how the parts actually connect

Three power domains, one ground. Getting this wrong is the most
expensive mistake available in this build.

```
  12 V 5 A PSU ──┬── kill switch ──┬── TMC2209 #1 VMOT ──┬─ 100 µF ─┐
                 │                 │                      │          │
                 │                 └── TMC2209 #2 VMOT ──┬┴─ 100 µF ─┤
                 │                                        │          │
                 └── 5 V buck ── Raspberry Pi 5           │          │
                                                          │          │
   ALL GROUNDS TIE TOGETHER AT ONE POINT ─────────────────┴──────────┘
        Pi GND · Nano GND · both driver GNDs · PSU GND
```

**The 100 µF capacitors are not optional.** Both the A4988 and TMC2209
datasheets require bulk capacitance across VMOT. Without it, the
inductive kick when the motor supply connects will destroy the driver —
this is the single most common way people kill these boards, and it
happens on the *first* power-up, before you have tested anything.

**Never power a motor from the Nano's 5 V pin.** It sources a few
hundred milliamps; a NEMA17 wants an amp or more per phase.

### Nano ↔ drivers

| Nano pin | To | Note |
|---|---|---|
| D2 | TMC2209 #1 STEP | Pan |
| D3 | TMC2209 #1 DIR | |
| D4 | TMC2209 #2 STEP | Tilt |
| D5 | TMC2209 #2 DIR | |
| D7 | Laser module TTL input | Modulated at 7 Hz in firmware |
| D8 | Vibration injector, **through a 2N2222 + flyback diode** | Never straight off a pin |
| A4 | TCA9548A SDA | |
| A5 | TCA9548A SCL | |
| 5 V | TMC2209 VDD (logic), TCA9548A VCC | Logic only, not motor power |

Both drivers' EN pins tie LOW (always enabled). Set MS1/MS2 for 1/32
microstepping — **check your board's silkscreen**, the truth table
differs between vendors, and getting it wrong scales every angle you
command.

### Encoders

| TCA9548A channel | Device |
|---|---|
| SD0 / SC0 | AS5600, pan, on the motor's rear shaft |
| SD1 / SC1 | AS5600, tilt, on the motor's rear shaft |

The multiplexer exists because both AS5600s are hard-wired to I²C
address 0x36 and cannot share a bus. The diametric magnet glues to the
**rear** shaft end, centred, 0.5–3 mm from the chip face. This is the
reason the motors must be dual-shaft — there is no way to retrofit it if
you order single-shaft motors.

### Head

The camera's CSI ribbon and the laser's two wires run from the head,
through the tilt axis, through the pan axis, to the base. Leave a
**service loop** at each axis — enough slack for full travel with the
cable never in tension — and secure it so it cannot foul the belts.
A ribbon that tugs at the end of travel will either pull the head off
boresight or tear its connector, and both failures look like a software
problem.

### Pi ↔ Nano

One USB cable. The Pi runs the vision pipeline and sends `P <pan>
<tilt>` in degrees; the Nano does motion and nothing else. The split
exists because Linux cannot emit step pulses with reliable microsecond
timing — jitter there *is* a skipped step.

---
## 7. Calibration, in order

Each step depends on the one before it. None of these numbers comes from
a datasheet; every one is measured.

**7.1 Encoder datum.** Point the head at a reference mark, send `Z`.
Everything downstream is relative to this.

**7.2 Steps per degree — verify, don't assume.** Command `P 45 0`,
measure the actual rotation with a protractor or a distant wall mark.
If it disagrees with 45°, your microstepping jumpers do not match
`MICROSTEPS` in the firmware. Fix the firmware, not the host.

**7.3 Plate scale, px per radian.** With the beacon in view, command a
known move and measure how far the spot travelled in the image.
`hil/calibrate.py` does this for both axes. This number feeds
`DotClosedLoop`, and it is measured, never taken from the lens's stated
focal length.

**7.4 Camera roll.** The same experiment yields it: command a pure pan
and see whether the spot moves along a pure image row. If it does not,
the camera is rotated relative to the gimbal axes, and the angle goes
into `DotClosedLoop(camera_roll_rad=...)` — otherwise pan corrections
leak into tilt and the loop spirals instead of converging.

**7.5 Frequency plan.** Run `check_frequency_plan(4.0, 7.0, fps,
window)` at your actual frame rate. A plan that aliases gives you a loop
that looks like it is running and is in fact scoring noise.

**7.6 Exposure.** Pin exposure and gain manually so the beacon is bright
but not saturated. Auto-exposure hunts on every blink — that is the
signal, and letting the camera chase it destroys it.

**No boresight offset is measured, ever.** That is the entire point of
§0: the loop closes on the dot, so there is no offset to calibrate and
nothing to drift.
