# Handoff: make the MK2 motors run (local Mac session)

Written 28 Sept 2026. Read `CLAUDE.md` and `docs/LOCAL_HANDOFF.md` first (user, tone, tools).

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
7. Then the live page: CONNECT RIG → TEST MOTION.

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
