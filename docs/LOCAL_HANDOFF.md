# Handoff to the local Claude Code session (Mac)

Written 27 Sept 2026 at the end of a long cloud session. The cloud session could
not touch the hardware; this one can. Read this whole file before doing anything.

## Who you are working with

Aryan (team leader, ZeroDrift, SIH26169). MacBook Air, zsh. Wants **simple English,
short step-by-step answers**, and an **image** when it is about wiring or building.
When he says "stop, only do X", do only X.

## Where we stopped: the beacon LED does not blink

The beacon = a second Arduino Nano + one red LED that blinks at 4 Hz
(`tools/rig/beacon_firmware.ino`, LED on **D9**).

| Checked | Result |
|---|---|
| LED + 220 Ω resistor, fed from the Nano's **5V** pin | **Glows.** LED, resistor and legs are fine. |
| Same LED on **D9** | **Dark.** |
| Wiring | User says D9 → 220 Ω → LED long leg, LED short leg → GND (the GND next to D2) is correct. |
| Code upload | **Never confirmed.** No "Done uploading" and no serial check yet. Most likely cause. |
| Board | Clone Nano, **USB-C**, reset button, almost certainly a **CH340** USB chip. |

Wiring picture: `tools/rig/beacon_wiring.png`.

### What to do next, yourself

1. Tools: `brew --version`, `arduino-cli version`. If arduino-cli is missing, ask, then `brew install arduino-cli`.
2. `arduino-cli board list`. No `/dev/cu.usbserial-*` or `/dev/cu.wchusbserial-*` port means the
   **CH340 driver** is missing. The user has to install WCH's CH34x macOS driver and allow it in
   System Settings → Privacy & Security; you cannot click that for him. Also try another cable:
   some USB-C cables only charge.
3. `tools/rig/flash.sh pintest`. It uploads a sketch that blinks D2–D13 together at 1 Hz and prints
   HIGH/LOW. Ask him: does the Nano's small **L** LED blink? Does **his** LED blink?
   - L blinks and his LED blinks → uploads work, the wire is on a digital pin. Go to step 4.
   - L blinks, his LED dark → the wire is not on a D pin or the contact is loose.
   - Upload fails on both bootloaders → driver, port or cable.
4. `tools/rig/flash.sh beacon`. Serial must print `ZeroDrift beacon ready  F4.00 B255 M1`, and the LED
   blinks 4 times a second.
   - If pintest blinked his LED but beacon doesn't: the wire is on a neighbour pin, or D9 is damaged.
     Move the wire to **D10** and set `LED_PIN = 10` (PWM pins are 3, 5, 6, 9, 10, 11). If he keeps
     D10, update the wiring comment in the .ino and `tools/rig/beacon_wiring.png`.
5. `flash.sh` holds the port only while monitoring (8 s). Anything else holding the port (Arduino
   IDE Serial Monitor) makes the upload fail. Close it first.

**`tools/rig/flash.sh` has not been run yet**, because the cloud machine could not download
arduino-cli. Expect to fix small things in it on first use.

Power note: the Nano + one LED draws ~25–40 mA. Some power banks switch off at that load after
about 30 s. If the beacon dies on the power bank, use a phone charger or a bank with a low-current mode.

## The rest of the hardware (for reference)

- **MK2 rig** (`tools/rig/rig_firmware_v2.ino`, flash with `tools/rig/flash.sh rig`, needs
  AccelStepper + Servo libraries; the script installs them).
  - Pins: pan STEP/DIR D2/D3, tilt D4/D5, laser KY-008 S → D7.
  - Sensors: TCA9548A on A4/A5; AS5600 pan on channel 0; tilt sensor optional.
  - A4988 drivers: 1/16 step, Vref 0.55 V, 100 µF on VMOT.
  - Soft limits: pan ±90°, tilt ±18°.
- **Decoy**: 3×AA → switch → 100 Ω (220 Ω if too bright) → LED. Steady, no code.
- **Laptop connections**: USB 1 = rig Nano, USB 2 = webcam. Wall → extension board →
  12 V adapter (motors only) + laptop charger. Beacon and decoy have their own power.
- **Build pages (hidden)**: `docs/build.html`, `preview.html`, `assembly.html`,
  `headbox.html`, `wiring.html`, `wiring3d.html`, `targets.html`. They must stay noindex
  (`docs/_headers` + meta tag) and **must never be linked from public pages**.

## Submission work that was paused (do not start it without asking)

The user stopped this work to build the beacon.

- **Deadline:** `docs/WINNING_PLAN.md` says 30 Sept 2026. Get it confirmed with the college SPOC.
- **Deck:** `docs/submission/ZeroDrift_SIH26169.pptx` has **8 slides**; the rule is max 6
  including the title.
  - Slide 7 is the template's own instruction slide (delete it).
  - Slide 8 is the compliance table (fold into slide 3 or drop it).
  - Slide 1 **Team ID is blank ("—")**.
- **Demo video:** required. It must **not be AI-generated**, and the voice must be team members'.
  Not recorded yet. The user asked for a shot list + script; not written yet.
  - Lead with the software (the PS is Software category).
  - Then the real MK2 rig as proof.
  - Numbers only from the canonical table in `docs/PROJECT_STATE.md` §2.
- **User manual:** `docs/user_manual.md` exists (~960 words). The PS names a User Manual as a
  deliverable, so it is worth expanding with screenshots into a PDF.
- **Links:** deck slide 6 has GitHub + `zerodrift-fsoc-pat.netlify.app`. Add the video link once
  uploaded.
