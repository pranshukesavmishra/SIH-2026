# Plan Urena — run the MK3 firmware in Chrome (Wokwi)

Free, no install. It runs the real `sketch.ino` (a copy of `tools/rig/rig_firmware_v3.ino`)
on a simulated Arduino UNO (same pins as the CNC Shield V3) with two A4988 drivers and two NEMA17 motors.
The red LED is the laser (D12), the yellow LED is the vibration motor (D13).

## Steps

1. Open **https://wokwi.com/projects/new/arduino-uno** in Chrome.
2. `sketch.ino` tab: select all, paste this folder's `sketch.ino`.
3. `diagram.json` tab: select all, paste this folder's `diagram.json`.
4. Library Manager (the book icon) → **+** → add **AccelStepper**.
   (Or: the ▾ next to the tabs → *New file* → `libraries.txt`, paste `AccelStepper`.)
5. Press the green ▶. The serial monitor at the bottom prints
   `# ZeroDrift Mk2 ready, encoders=no, belts=4:4`
   (`encoders=no` is normal: Wokwi has no AS5600 part.)
6. Click in the serial monitor and type these, pressing Enter after each:

| Type | What you should see |
|---|---|
| `P3556 T-711` | Pan motor turns +400°, tilt motor −80°. That is the belt: the motor turns 4× the gimbal, so this is 100° pan, −20° tilt. |
| `?` | `S 3556 -711 C 0` |
| `P999999` | Pan stops at 5333 steps = 150°. The limit works. |
| `L7.0` | Red LED blinks 7 times a second. |
| `L0` | LED off. |
| `C` | Both motors go back to 0. |
| `!` | Self-test: LED, blink, pan +10° and back, yellow LED. |

If a wire shows as not connected after pasting (Wokwi sometimes renames a pin), drag
it again from the UNO pin to the driver pin shown in the table below.

| UNO pin | CNC shield name | Goes to |
|---|---|---|
| D2 / D5 | X.STEP / X.DIR | Pan A4988 STEP / DIR |
| D3 / D6 | Y.STEP / Y.DIR | Tilt A4988 STEP / DIR |
| D8 | EN | ENABLE on both drivers |
| D12 | SpnEn | laser |
| D13 | SpnDir | vibration motor |
| 5V | — | VDD, MS1, MS2, MS3 (1/16 step) on both drivers |

(On the real CNC shield all of this is already wired on the board. You only set the
three jumpers under each driver.)

## The deeper test (on a PC)

`bash tools/mk3/fwtest/run.sh` compiles the same firmware with fake motors, fake
AS5600 sensors and a fake clock, then runs 42 checks for each board (UNO + CNC shield, and a hand-wired Nano): limits, belt maths, both
encoders across the full ±150° pan including the sensor's 0/360 seam, a slipped belt,
the laser frequency, junk input and the self-test (including a sensor mounted upside
down). Needs only `g++`.
