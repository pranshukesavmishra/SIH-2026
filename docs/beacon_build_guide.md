# ZeroDrift Beacon Unit — Build Guide

> Companion to `docs/rig_mk2_build_guide.md`. That document builds the
> **tracker** (camera + laser + pan-tilt). This one builds the **target**
> it tracks. Same rule as the tracker: not in the pitch deck, this is a
> Grand-Finale table demo, no deadline pressure.

---
## 0. Why build a dedicated beacon at all

Mk1's beacon was "hold up a phone running a strobe app." That's fine for
a first demo, but it quietly undercuts your own pitch: the whole
identification principle is a **hard gate on an exact modulation
frequency** (`tools/webcam_beacon_demo.py` defaults to 4.0 Hz, matching
the simulator). A phone's strobe app runs on a general-purpose OS —
its actual blink timing drifts with scheduler jitter, frame:frame. If
your beacon's own frequency isn't precise, you can't claim you're
testing precise frequency discrimination.

An Arduino's blink loop, timed off its onboard crystal, is accurate to
tens of parts-per-million — several orders of magnitude tighter than a
phone app needs to be for this to matter. **This is the difference
between "a light that blinks about 4 times a second" and "a
metrologically known 4.000 Hz reference."**

Two units, built together:

| Unit | Role | Complexity |
|---|---|---|
| **Beacon** | The real target — precise, adjustable frequency and brightness, portable | Arduino-driven |
| **Decoy** | A steady, non-blinking bright light — physically proves the rejection, side by side with the beacon in the same frame | No microcontroller — just an LED and a switch |

Running both simultaneously, in the same camera frame, is the actual
test your software claims to pass. Switching one light between modes
sequentially is a weaker demo than two lights disagreeing at the same
time.

---
## 1. Beacon unit

### 1.1 What it does

An Arduino Nano drives a diffused high-brightness LED, blinking at a
commanded frequency and brightness, battery-powered so it can sit
across the room independent of a laptop.

```
Serial command, matches the tracker rig's protocol style, 115200 baud:
  F<hz>       set blink frequency, e.g. F4.0 (default on boot: 4.0)
  B<0-255>    set brightness (PWM duty — simulates the simulator's
              0.4-2.5x brightness sweep)
  M0          steady-on (no blink) — for a controlled A/B test against
              the separate decoy unit, or to sanity-check the camera sees it
  M1          blinking mode (default)
```

Frequency is timed with `micros()` against the Nano's crystal, not
`delay()` — see the firmware for why that distinction matters (`delay()`
drifts under interrupt load; a `micros()`-referenced toggle doesn't).

### 1.2 Component list

| # | Item | Qty | ~Price | Notes |
|---|---|---|---|---|
| 1 | Arduino Nano | 1 | ₹200–250 | A second unit — do not borrow the tracker's |
| 2 | High-brightness LED, 10mm, white or red (3000+ mcd) | 1 | ₹15–30 | Search "10mm high brightness LED 3000mcd" |
| 3 | 2N2222 NPN transistor | 1 | ₹10 | Same part as the rig's vibration driver — buy the combo kit once, use across both builds |
| 4 | 220Ω resistor | 1 | ₹5 | Current-limit for the LED |
| 5 | 1kΩ resistor | 1 | ₹5 | Transistor base |
| 6 | Ping-pong ball (or frosted acrylic dome) | 1 | ₹20–40 | **Diffuser** — turns a directional LED into an approximately isotropic point source, so the beacon reads correctly off-axis, not just dead-ahead |
| 7 | 9V battery + clip, or 2×AA holder | 1 | ₹80–150 | Portable power — the whole point is it doesn't need a laptop nearby |
| 8 | SPST toggle switch | 1 | ₹20–30 | On/off without unplugging the battery |
| 9 | Small ABS project box | 1 | ₹80–150 | Same item as the tracker's camera+laser head — buy two identical boxes in one order |

**Total: ≈ ₹435–670**

### 1.3 Assembly

1. Drill a hole in the enclosure lid sized for the LED; push-fit the LED
   through so its dome sits flush.
2. Cut the ping-pong ball roughly in half, sand the inside lightly
   (increases diffusion), and cap it over the LED — hot-glue at the rim.
3. Wire: Nano `D9` (PWM-capable) → 1kΩ → transistor base. Transistor
   collector → LED anode → 220Ω → battery `+`. LED cathode → transistor
   emitter → battery `−` / Nano `GND` (common ground, same rule as the
   tracker's vibration driver).
4. Switch goes in-line on the battery `+` lead, not through the Nano —
   it should kill power to everything, including the Nano itself, so the
   unit truly has an "off."
5. Flash `tools/rig/beacon_firmware.ino`. Test with the switch on:
   confirm a visible blink, then confirm `F2.0` and `F8.0` over Serial
   Monitor actually change the rate before sealing the box.

---
## 2. Decoy unit — the control

### 2.1 Why it exists

Your entire pitch line is "brightness is not identity — modulation is."
A single beacon proves you can detect a blink. It does not, by itself,
prove you *reject* something that's merely bright. The decoy sitting
next to it, steady-on, in the same frame, is what makes that claim
demonstrable rather than asserted.

### 2.2 Component list

| # | Item | Qty | ~Price | Notes |
|---|---|---|---|---|
| 1 | High-brightness LED — **brighter than the beacon's**, different color helpful for you to tell them apart (not for the camera, which only cares about modulation) | 1 | ₹15–30 | Deliberately outshine the beacon — that's the point being proven |
| 2 | 150Ω resistor | 1 | ₹5 | Slightly lower value than the beacon's — drives more current, brighter |
| 3 | CR2032 coin cell + holder, or 2×AA pack | 1 | ₹40–80 | |
| 4 | SPST switch or slide switch | 1 | ₹20–30 | |
| 5 | Small housing — reuse a spare project box, or even a bottle cap + tape for this one, it's genuinely just an LED | 1 | ₹0–40 | No enclosure precision needed — it never moves during a demo |

**Total: ≈ ₹80–185**

No microcontroller, no firmware — wire the LED, resistor, switch and
battery in series. It is deliberately the simplest thing in the entire
build, because its only job is to sit there, be bright, and not blink.

---
## 3. Running the beacon + decoy demo

1. Place the beacon and decoy roughly the same distance from the
   tracker rig, close enough together to both sit inside the camera's
   field of view at once (this is the point — the software has to pick
   the right one from the same frame, not from separate trials).
2. Power both on. Decoy: switch on, done. Beacon: switch on, boots to
   `F4.0 M1` by default.
3. Run `tools/rig/rig_track.py` (or the Mk2 firmware once built) —
   confirm the tracker locks the blinking one and ignores the brighter
   steady one.
4. For the "break it" moment in Q&A: change the beacon's frequency live
   (`F7.0` over Serial) and show the tracker either re-locking at the new
   rate (if your matching window is wide) or losing lock and re-searching
   (if it's tuned tight to 4 Hz) — either outcome is a real, honest answer
   to "what if the frequency isn't exactly 4?", which is a question a
   sharp judge will ask.

---
## 4. Firmware

See `tools/rig/beacon_firmware.ino` — drafted, not yet bench-tested,
same caveat as the tracker firmware: verify the pin wiring against your
actual build before trusting it, and confirm the measured blink rate
with a phone's slow-motion camera or an oscilloscope if you have access
to one before calling the frequency "precise" in front of a judge.

---
## 5. Safety

LEDs here are ordinary indicator-class parts, not lasers — no eye
hazard at normal viewing distance. Standard precaution only: don't stare
directly into a high-brightness LED at close range for an extended
period, same as you wouldn't with a bicycle light.
