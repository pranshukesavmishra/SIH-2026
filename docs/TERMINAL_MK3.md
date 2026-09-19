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
            │    USB webcam, UVC, housing removed     │
            │    red filter over the lens             │
            │    650 nm laser, modulated at 7 Hz      │
            │    ~20 mm between optical axes          │
            └───────────────────┬─────────────────────┘
                     USB + laser │ wire, service loop at each axis
            ┌───────────────────┴─────────────────────┐
            │  GIMBAL                                 │
            │    TILT: NEMA17 1.8° + AS5600           │
            │    PAN : NEMA17 1.8° + AS5600           │
            └───────────────────┬─────────────────────┘
                                │
            ┌───────────────────┴─────────────────────┐
            │  BASE                                   │
            │    Arduino Nano      — motion, real-time│
            │    2× A4988          — 1/16 microstep   │
            │    TCA9548A          — encoder mux      │
            │   12 V Li-ion pack (motor rail only)    │
            └───────────────────┬─────────────────────┘
                     USB ×2     │
            ┌───────────────────┴─────────────────────┐
            │  LAPTOP — vision + the ZeroDrift pipeline│
            └─────────────────────────────────────────┘
```

Tier B moves the pipeline onto a Raspberry Pi in the base and makes the
whole thing self-contained. The architecture does not change; only where
the vision runs.

**Why a separate motion controller.** Neither Linux nor Windows is a
real-time OS. Neither can emit step pulses with reliable microsecond
timing, and jitter there *is* a skipped step — exactly the failure the
encoders exist to catch. So the Nano does motion and nothing else, the
host does vision and the pipeline, and they speak over USB serial. This
is how real pointing systems are built, and it is a good answer when a
judge asks why the architecture is split. It is also why moving the
pipeline to a Pi later changes nothing: the Nano is on the other side of
that boundary either way.

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

| Stage | Tier A (built) | Tier B (+belt) |
|---|---|---|
| Step size | 1.8° ÷ 16 = 0.1125° = **1.96 mrad** | 0.0375° = **0.65 mrad** |
| AS5600, 12-bit | 0.0879° = **1.53 mrad** | 0.0293° = **0.51 mrad** |
| Camera — UVC webcam, 640 px across ~48° | ~0.075°/px = **~1.3 mrad/px** | same |
| *(if an M12 12 mm board camera is used instead)* | *0.0172°/px = 0.30 mrad/px* | *same* |
| Centroid, ~1/5 px on a clean spot | ~0.06 mrad | same |

**The camera is still not the limit — but with a webcam it is closer
than it looks.** Raw pixel pitch on a consumer webcam (~1.3 mrad/px) is
the same order as the encoder's 1.53 mrad, so the "camera is free"
argument does *not* survive on raw pixels alone. It survives on
centroiding: at ~1/5 px the camera contributes ~0.26 mrad, back below
the mechanism. That is a real dependency on the sub-pixel estimator
rather than on optics, and it is worth saying out loud instead of
quoting a lens number we no longer buy.

Both rows above are nominal. **The number that matters is measured, not
derived** — §7.3 obtains plate scale from a commanded move, never from
a lens's stated focal length, precisely because cheap webcams do not
publish honest FOV figures. That is worth
mechanism, a better sensor buys nothing. Money goes into the belt, or
nowhere.

Tier A lands at roughly **1.5–2 mrad, encoder-verified**. That is a real
measured number, twice as good as the Mk2 design it replaces, and honest.
It is *not* the simulator's microradian figure, and `docs/defence_brief.md`
already takes the position that saying so plainly reads as rigour rather
than weakness.

---
## 2. Bill of materials

**Two tiers. Build Tier A.** It is the student build, ~₹6,100, and it
gives up nothing that this design's argument rests on. Tier B is what
you would add if money appeared; it is listed so you know exactly what
you are trading, and so nobody can claim you did not consider it.

### What the budget does NOT touch

Every idea that makes this project worth winning with costs nothing:

- **The dot-closed loop.** Beacon 4 Hz, laser 7 Hz, error measured
  between them. That is software, and it is the whole intellectual
  contribution of the physical build. Free.
- **Modulation as identity.** Beacon vs decoy vs our own dot, separated
  by frequency, not brightness. Free.
- **Closed-loop position feedback.** Two AS5600s and a multiplexer:
  ₹697 total. This is what makes "accurate" a measurement instead of an
  adjective. Never cut it.
- **The camera riding on the gimbal.** An architectural choice, not a
  price point.

What money buys is margin, not capability. Say exactly that if a judge
asks why the rig is cheap.

### Tier A — the build. ₹6,345.

> **This table is generated from `docs/data/bom_tier_a.json`**, which is
> also what `docs/submission/ZeroDrift_Mk3_Build_Guide.pdf` is built from,
> and `tests/test_bom_consistency.py` fails if they drift apart. It is
> written this way because they *did* drift: a hand-maintained version of
> this table summed to ₹5,944 while claiming ₹6,124, and the row it was
> missing was the diametric magnets — the one part whose absence stops the
> build dead. Do not hand-edit the table below; edit the JSON.

✅ = verified against a live Amazon.in listing in the September pricing
pass. `~` = market-range planning figure, not yet confirmed — check before
ordering, and say which is which if a judge asks what the rig cost.

| Item | Qty | Unit | Total | Price basis |
|---|---|---|---|---|
| **A. Motion — the gimbal** | | | | |
| NEMA17 stepper motor, 1.8°/step, 4.2 kg-cm | 2 | ₹749 | **₹1,498** | ✅ verified |
| A4988 stepper driver module | 2 | ₹170 | **₹340** | ✅ verified |
| NEMA17 L-bracket (pan + tilt) | 2 | ₹127 | **₹254** | ✅ verified |
| 100 µF 25 V electrolytic capacitor | 2 | ₹10 | **₹20** | ~ estimate |
| **B. Feedback — what makes “accurate” a measurement** | | | | |
| AS5600 magnetic encoder module | 2 | ₹249 | **₹498** | ✅ verified |
| Diametric magnet, 6 × 2.5 mm | 2 | ₹90 | **₹180** | ~ estimate |
| TCA9548A I²C multiplexer | 1 | ₹199 | **₹199** | ✅ verified |
| **C. Head — camera and laser, one enclosure** | | | | |
| USB webcam, UVC, 640x480+ — housing removed before mounting | 1 | ₹800 | **₹800** | ✅ verified |
| Red filter — gel sheet or red acrylic offcut | 1 | ₹100 | **₹100** | ~ estimate |
| KY-008 laser module | — | — | **₹0** | reuse Mk1 |
| ABS project box, head enclosure | 1 | ₹115 | **₹115** | ~ estimate |
| **D. Control and power** | | | | |
| Arduino Nano — tracker | — | — | **₹0** | reuse Mk1 |
| Arduino Nano — beacon | 1 | ₹225 | **₹225** | ~ estimate |
| 12 V Li-ion pack, 3S (or 3x18650 + holder) | 1 | ₹650 | **₹650** | ~ estimate |
| 3S 12.6 V balance charger — NOT a single-cell charger | 1 | ₹250 | **₹250** | ~ estimate |
| DC barrel jack to screw-terminal adapter | 1 | ₹30 | **₹30** | ~ estimate |
| SPST toggle switch — motor rail kill switch | 1 | ₹25 | **₹25** | ~ estimate |
| Breadboard, 830 point (drivers + Nano + mux) | 1 | ₹90 | **₹90** | ~ estimate |
| USB cables for the two Nanos — check each port before buying | 2 | ₹99 | **₹198** | ~ estimate |
| Acrylic sheet 3 mm, 6″×6″ (pack of 2) | 1 | ₹199 | **₹199** | ✅ verified |
| **E. Disturbance injector — robustness shown, not claimed** | | | | |
| Vibration motor, 3 V DC | 1 | ₹20 | **₹20** | ✅ verified |
| Transistor + diode + resistor combo kit | 1 | ₹105 | **₹105** | ✅ verified |
| **F. Beacon — the target** | | | | |
| High-brightness RED LED, 10 mm, 650 nm | 1 | ₹22 | **₹22** | ~ estimate |
| 2N2222 transistor + 220 Ω + 1 kΩ | 1 | ₹20 | **₹20** | ~ estimate |
| Ping-pong ball (diffuser) | 1 | ₹129 | **₹129** | ✅ verified |
| USB power bank (any, 5V) — beacon supply | — | — | **₹0** | reuse Mk1 |
| SPST toggle switch | 1 | ₹25 | **₹25** | ~ estimate |
| ABS project box | 1 | ₹115 | **₹115** | ~ estimate |
| **G. Decoy — the control** | | | | |
| High-brightness WHITE LED (brighter than beacon) | 1 | ₹22 | **₹22** | ~ estimate |
| 68 Ω resistor | 1 | ₹5 | **₹5** | ~ estimate |
| 3×AA battery holder + 3 AA cells — decoy supply | 1 | ₹90 | **₹90** | ~ estimate |
| Switch + scrap housing | 1 | ₹35 | **₹35** | ~ estimate |
| **H. Consumables** | | | | |
| Dupont jumper wires — M-M, M-F, F-F | 1 | ₹150 | **₹150** | ~ estimate |
| M3 screws, nuts, standoffs assortment | 1 | ₹150 | **₹150** | ~ estimate |
| Heat-shrink, solder, hot-glue sticks | 1 | ₹150 | **₹150** | ~ estimate |
| **TOTAL** | | | **₹6,709** | |

**Resolution you actually get:** 1.8° ÷ 16 microsteps = 0.1125°/step =
**1.96 mrad**, with the AS5600 measuring true position to 0.088° = 1.53
mrad. Roughly **1.5–2 mrad, encoder-verified.**

Without the head (source the camera later): **₹4,730**.

### The one thing to get right when ordering motors

The AS5600 needs a magnet rotating coaxially in front of it. Two ways:

- **Dual-shaft NEMA17** (~₹850–1,200 each if you can find one): magnet
  glues to the rear shaft, sensor on a bracket behind the motor. Clean,
  compact, no flex path. Costs about ₹250 more per motor.
- **Single-shaft** (the ₹749 verified ones): magnet goes on top of the
  rotating platform, on the axis of rotation, with the AS5600 on a small
  fixed arm overhanging it. Works, reads the output directly, and costs
  nothing extra — but keep that arm short and stiff, because any flex in
  it reads as pointing error that is not really there.

Either is fine. Decide by what is actually in stock at a sane price, not
by the datasheet.

### Tier B — what money would buy, and what it is worth

| Upgrade | Cost | What it actually buys |
|---|---|---|
| GT2 3:1 belt reduction (pulleys, belt, 608ZZ bearings, 8 mm shaft) | +₹1,740 | **The best rupee-for-accuracy item that exists here.** 1.96 → 0.65 mrad/step, and it divides the motor's *own* ±5%-of-a-full-step error by three, which microstepping cannot do. If you can raise the budget by one item, raise it by this one. |
| TMC2209 instead of A4988 | +₹560–1,860 | 1/32 microstepping, quiet, and StallGuard as a second stall signal. You already have encoders, so this is comfort, not capability. |
| 0.9°/step motors | +₹700–1,000 | Halves step size again. Only worth it after the belt. |
| Raspberry Pi 5 + camera + on-board pipeline | +₹18,000 | Makes it self-contained rather than USB-tethered to a laptop. A presentation asset, not a performance one. |
| True 650 nm bandpass filter | +₹1,400–2,900 | Better ambient rejection than a gel. Marginal once the modulation gate is doing its job. |
| Global-shutter camera | +₹4,000–5,500 | **Less than I first claimed.** Rolling-shutter readout is 10–30 ms against a 250 ms blink period, and the fine loop measures at rest, so the smear I warned about is small. Nice to have; not load-bearing. |

### On the laptop

Tier A runs the pipeline on your laptop, with one USB cable to the
camera and one to the Nano. The camera still rides on the gimbal — that
was your requirement and it is met. What you give up is only the
*self-contained* story, and PS26169 is a Software-category problem, so
the software running on a laptop is the deliverable, not an apology.

## 2.5 The model

`docs/cad/` holds a parametric model of this build — every BOM item at
its real size, placed. `renders/04_exploded_labelled.png` is the
assembly in the same order as §3's stages, numbered and labelled.

Drawing it caught things the parts list alone did not: the 830-point
breadboard is 165 mm and the 6″ acrylic plate is 152.4 mm, so the
breadboard **does not fit on the base plate** and belongs on the bench
beside the rig (better practice regardless — §2E vibrates that plate on
purpose). A 32 mm webcam PCB also does not fit a 30 mm box, so the head
is 72 × 46 × 42.

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

**Stage 3 — One axis, open loop.** Pan motor, A4988, Nano.
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

A 12 mm M12 lens sees 22°×16°; the UVC webcam Tier A actually specifies sees roughly 48°×36°, which cuts a 90°×40° volume from 24 tiles to about 4 — the one place the cheaper camera is strictly better. At 22°×16° it takes 24 tiles at
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
- Kill switch on the motor rail, reachable without leaning into the
  gimbal's travel.
- The laser rides on a head that moves under software control. Keep it
  off (`L0`) during any scan whose sweep crosses standing people, and
  only enable it once the head is settled and pointing at the beacon
  board.
- Steppers warm up under stall. Do not leave the rig powered and jammed.

---
## 6. Wiring — how the parts actually connect

Three power domains, one ground. Getting this wrong is the most
expensive mistake available in this build.

**The terminal runs from the laptop and one battery, with no wall
socket.** That is a
stage requirement, not a preference, and it constrains exactly one
thing. The laptop's USB runs both Nanos, the camera, the laser, the two
encoders and the vibration motor without complaint — all of that is
logic-level and draws well under an amp in total. The steppers are the
exception: the A4988 needs 8–35 V on VMOT and USB delivers 5 V, so no
amount of wiring makes a stepper run off the laptop. A 12 V Li-ion
battery pack supplies that rail, and only that rail.

The battery is a plain 12 V Li-ion pack with a DC barrel output -- the
same connector the mains adapter used, so nothing else in the wiring
changes. A USB-PD trigger module was considered and rejected: it depends
on the power bank you happen to own supporting PD, and 12 V is not even
a guaranteed PD voltage (the standard's fixed steps are 5/9/15/20 V).
For a demo that cannot be debugged on stage, a supply that needs to
negotiate with unverified hardware is not a supply.

**Set the A4988 Vref to about 0.5-0.6 V** (~0.6 A/phase) before
attaching a motor. The pair then draws under 1 A, so a 3000 mAh pack
runs roughly three hours, and the drivers stay cool.

```
  12 V Li-ion pack ══ barrel jack ════┬── kill switch ──┬── A4988 #1 VMOT ──┬─ 100 µF ─┐
   (motor rail only)                   │                 │                    │          │
                                       │                 └── A4988 #2 VMOT ──┬┴─ 100 µF ─┤
  LAPTOP USB ══ Nano ══ 5 V logic ═════╪═══ camera · laser · AS5600 ×2 ·      │          │
                                       │    TCA9548A · vibration motor        │          │
   ALL GROUNDS TIE TOGETHER AT ONE POINT ─────────────────────────────────────┴──────────┘
        Nano GND · both driver GNDs · battery GND
        (the laptop's ground arrives through the Nano's USB — do not
         also bond it to the motor supply, or you build a ground loop)
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
| D2 | A4988 #1 STEP | Pan |
| D3 | A4988 #1 DIR | |
| D4 | A4988 #2 STEP | Tilt |
| D5 | A4988 #2 DIR | |
| D7 | Laser module TTL input | Modulated at 7 Hz in firmware |
| D8 | Vibration injector base, **through a 1kΩ base resistor into a 2N2222** | Never straight off a pin |
| A4 | TCA9548A SDA | |
| A5 | TCA9548A SCL | |
| 5 V | A4988 VDD (logic), TCA9548A VCC | Logic only, not motor power |

**The vibration motor's own supply was left unstated here in an earlier
revision** — worth calling out because the obvious wrong answer, wiring
it to the motor rail sitting right there on the same board, overdrives a
motor rated 3 V by more than 4×. Run its positive lead from the **Nano's
own 5 V pin**, through a **27 Ω series resistor**, into the motor, with
the 2N2222's collector on the motor's negative lead and its emitter to
ground (flyback diode across the motor, cathode to the 5 V side). At
27 Ω the motor sees close to its rated 3 V and draws roughly 75 mA —
small enough that it doesn't compete with the Nano's own 500 mA USB budget alongside everything else on it. Both the base resistor and the 27 Ω motor resistor come out of the assortment kit already on the list (§2E) — it's a mixed-value pack, not a single part, so there's nothing new to buy.

Both drivers' EN pins tie LOW (always enabled). Tie MS1/MS2/MS3 HIGH for
1/16 microstepping — **check your board's silkscreen**, the truth table
differs between vendors, and getting it wrong scales every angle you
command. Set `MICROSTEPS` in the firmware to match.

Set each A4988's current limit with its trimpot before attaching any
motor: Vref ≈ I × 8 × Rsense. Running a NEMA17 at full chip current with
no heatsink is how these boards die second-most often, after the missing
VMOT capacitor.

### Encoders

| TCA9548A channel | Device |
|---|---|
| SD0 / SC0 | AS5600, pan, on the motor's rear shaft |
| SD1 / SC1 | AS5600, tilt, on the motor's rear shaft |

The multiplexer exists because both AS5600s are hard-wired to I²C
address 0x36 and cannot share a bus.

Magnet mounting depends on which motor you bought (§2 covers both):

- **Dual-shaft NEMA17**: magnet glues to the **rear** shaft end,
  centred, 0.5–3 mm from the chip face. Sensor sits on a bracket
  directly behind the motor.
- **Single-shaft NEMA17 — the ₹749 verified item, and what Tier A
  actually specifies**: there is no rear shaft to use. The magnet
  glues instead to the **top face of the rotating platform**, on the
  axis of rotation, and the AS5600 sits on a short, stiff arm
  overhanging it from a fixed point on the frame. "Short and stiff" is
  load-bearing advice, not a preference: any flex in that arm reads
  back as pointing error that is not really there, which is exactly
  the class of error this whole design exists to eliminate (§0).

An earlier revision of this section said the motors "must be
dual-shaft," which was wrong and contradicted §2's own BOM. Tier A's
verified line is single-shaft; that is the motor most builders will
actually have.

### Head

**The camera-to-tilt-shaft standoff must be metal.** An M3 brass
standoff out of the assortment already on the list is correct; a
3D-printed one is not, and the difference is not marginal. For the
42 mm span this build uses, carrying roughly 80 g of head:

| Standoff material | Static droop | Natural frequency |
|---|---|---|
| Steel | 54 µrad (0.5 px) | 404 Hz |
| Aluminium / brass | 158 µrad (1.4 px) | 237 Hz |
| **PLA, 3D-printed** | **3,109 µrad (28.5 px)** | **53 Hz** |

53 Hz sits on top of the 47 Hz platform mode this build's own benchmark
scenario injects. A printed standoff is therefore a resonator tuned to
the disturbance we are trying to reject — it manufactures the
flex-reads-as-pointing-error failure §0 is built to avoid. The CAD model
in `docs/cad/` carries the same warning, because the obvious thing to do
with an STL is print all of it.


The camera's USB cable and the laser's two wires run from the head,
through the tilt axis, through the pan axis, to the base. Leave a
**service loop** at each axis — enough slack for full travel with the
cable never in tension — and secure it so it cannot foul the belts.
A cable that tugs at the end of travel will either pull the head off
boresight or tear its connector, and both failures look like a software
problem. USB cable is stiffer than a ribbon — give it more slack than
feels necessary.

### Host ↔ Nano

One USB cable. The host runs the vision pipeline and sends
`P <pan> <tilt>` in degrees; the Nano does motion and nothing else.

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
