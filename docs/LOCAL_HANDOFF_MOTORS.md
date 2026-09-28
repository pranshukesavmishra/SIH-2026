# Handoff: make the MK2 motors run + first live tracking test (local session)

Written 28 Sept 2026, updated same day once hardware moved to Aryan's **Windows PC**.
Read `CLAUDE.md` and `docs/LOCAL_HANDOFF.md` first (user, tone, tools). Commands below
give the Mac (`brew`, zsh) form first, Windows (PowerShell / Git Bash) form second —
check `arduino-cli version` / `echo $OS` or just ask Aryan which machine he's on before
running anything.

## Windows setup (if this is the Windows PC)
- Arduino CLI: easiest is the **Arduino IDE** installer (arduino.cc/en/software) — it can
  install boards/libraries with a GUI, and Aryan can watch it happen. `arduino-cli` alone
  also works: `winget install ArduinoSDA.arduino-cli` (or download the .zip and put
  `arduino-cli.exe` on PATH).
- `tools/rig/flash.sh` is a **bash script** — on Windows run it from **Git Bash** (installed
  with Git for Windows), not PowerShell/cmd directly. If Git Bash isn't installed, either
  install it, or drive `arduino-cli compile` / `arduino-cli upload` by hand with the same
  flags as in the script, or just use the Arduino IDE's own Upload button after opening
  `tools/rig/rig_firmware_v2.ino` and installing the **AccelStepper** and **Servo** libraries
  via Library Manager, board = "Arduino Nano", processor = **ATmega328P** (try "(Old
  Bootloader)" too if upload fails), port = whatever `COM#` shows up in Device Manager
  once the Nano is plugged in (CH340 driver may be needed for a clone Nano).
- Serial monitor from Git Bash: `arduino-cli monitor -p COM# -c baudrate=115200`.

## Where we are
- Aryan has wired the rig breadboard himself: Nano, 2× A4988 (red boards), TCA9548A mux,
  12 V adapter → 3-leg DC jack → toggle switch → TOP red rail. **His column layout is his own**,
  not `docs/wiring_plan.js`. Do not assume hole numbers; ask for a top-down photo if needed.
- 12 V chain: jack thin pin (+) → switch MIDDLE; switch outer → TOP red rail; jack round pin (−) → TOP blue rail.
- **AS5600 not wired yet.** Its header pins probably need soldering. Firmware runs fine without it
  (reports encoders=no / pan-only). Motors first, sensor later.

## Goal of this session
Motors turn on command from the laptop. Nothing else.

## Steps (do them in order, confirm each with Aryan)
1. **Wiring check with photos + multimeter, power OFF.** Per driver:
   VMOT→TOP red (+12 V), GND beside it→GND, VDD→5 V (NEVER 12 V), other GND→GND,
   EN→GND, MS1/MS2/MS3→5 V, RST↔SLP jumpered, STEP/DIR: pan D2/D3, tilt D4/D5.
   Blue rails joined; red rails NOT joined (beep test TOP red↔BOTTOM red = no beep).
   100 µF across VMOT/GND, stripe to GND. Heat sink on each A4988 chip, clear of the pot.
2. **Motor coil pairs:** multimeter Ω, pair = ~2–4 Ω. Pair 1 → 2B/2A, pair 2 → 1A/1B.
   Never plug/unplug a motor with 12 V on.
3. **Vref:** USB only, 12 V OFF. Black probe GND, red probe on the pot's metal top → 0.55 V. Both drivers.
4. **Flash:** `tools/rig/flash.sh rig` (installs AccelStepper). Serial 115200, newline endings.
5. **Power up:** USB in, then switch 12 V ON. Shafts should go stiff; nothing hot.
6. **Move** (serial monitor, e.g. `arduino-cli monitor -p <port> -c baudrate=115200`):
   `?` status · `!` self-test · `P200 T0` pan +200 steps · `P0 T0` back · `P0 T100` tilt ·
   `C` return to datum · `Z` zero here · `L1`/`L0` laser.
   200 steps = 22.5° at 1/16 microstep (8.889 steps/deg). Soft limits pan ±90°, tilt ±18°.
7. **Then the live page: CONNECT RIG → TEST MOTION.** No Python and no local server needed
   for this — `docs/live.html` does the webcam capture and the tracking math in the
   **browser** itself, and talks to the Nano straight from the page over the **Web Serial
   API**. That only works in **Chrome or Edge** (not Firefox/Safari), and only on a secure
   (https) or localhost page — the deployed site `https://zerodrift-fsoc-pat.netlify.app/live.html`
   already qualifies, so Aryan can just open that URL on the Windows PC, plug in the Nano,
   click **CONNECT RIG**, pick the Nano's port from the browser's own picker, allow the
   camera, then **TEST MOTION**. Pick **MK2** rig mode. Point the webcam at the beacon LED
   (blinking 4 Hz) to see it lock and track for real.
   - The separate Python engine (`pip install -e ".[gui,dev]"`, `python -m fsoc_pat.gui.app`)
     is for offline simulation/tests only — it is **not** part of this live hardware path.

## Troubleshooting
| Symptom | Likely cause |
|---|---|
| Motor buzzes, no turn | coil pair split across 1x/2x; re-pair |
| No holding torque | no 12 V at VMOT, EN not GND, RST↔SLP missing |
| Wrong direction | fine; or swap the two wires of ONE pair |
| Moves 16× too far/short | MS1-3 not all at 5 V |
| Driver hot / cuts out | Vref too high, heat sink missing |
| Upload fails | close other serial monitors; CH340 driver; try another cable |

## AS5600 (later, separate step)
Solder the header (short end into the board). Wire: mux VIN→5 V, GND→GND, SDA→A4, SCL→A5,
A0/A1/A2→GND; mux SD0/SC0 → AS5600 SDA/SCL; AS5600 VCC→5 V, GND→GND, DIR→GND.
Magnet 1–2 mm above the chip, centred. Firmware then reports `encoders=pan`.

## Rules
Power on: USB then 12 V. Off: 12 V then USB. Stop with the switch at any sign of heat or smell.
