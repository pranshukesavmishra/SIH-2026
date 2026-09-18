# Host ↔ motion controller protocol — v3

**One definition, two implementations.** `tools/rig/rig_firmware_v2.ino`
and `src/fsoc_pat/hil/rig.py` must both match this file. If you change
the wire format, change this file first and bump `PROTOCOL` in both.

## Why this document exists

Between 27 August and 14 September, three sessions wrote three layers of
this system, each against its own idea of the wire format:

| Layer | Sent / expected | Units |
|---|---|---|
| `hil/rig.py` | `P 12.345 6.789` | degrees, float |
| `rig_firmware.ino` (Mk1) | `P12 T6` | servo degrees, int |
| `rig_firmware_v2.ino` (Mk2 draft) | `P12 T6` | **motor steps**, int |
| `rig_track.py` | `P12 T6`, and `L1` **with no newline** | servo degrees |

None of them could drive any of the others. `hil/rig.py` sending
`P 12.345 6.789` to the Mk2 draft would parse as 12 motor steps — a
silent factor-of-4.4 error — then query a status endpoint that did not
exist, spin for its whole timeout, and report that the gimbal had not
moved. To a person watching, that is indistinguishable from "the tracker
just never locks."

Nobody caught it because the layers were never run against each other on
real hardware. That is the failure this file is here to prevent.

## Rules

1. **The wire is degrees.** Always, both directions, floating point.
2. **The firmware owns all mechanical constants** — microstepping, belt
   ratio, steps per degree, soft limits. Change the mechanics, change the
   firmware, reflash. The host is never recompiled and never told.
3. **Every message ends with `\n`.** A command without one leaves the
   firmware holding a partial line, which then consumes the front of the
   next command and silently drops it.
4. **Lines beginning `#` are human-readable log output.** Hosts ignore them.
5. **Unknown commands are ignored silently.** A newer host must not jam an
   older firmware.

## Commands — host to controller

| Command | Meaning |
|---|---|
| `P <pan> <tilt>` | Coarse absolute target, degrees. Either field may be omitted. Clamped to soft limits. |
| `p <pan> <tilt>` | Fine-stage offset, degrees. Accepted and ignored unless the firmware was built with `FINE_STAGE 1`. |
| `L0` | Laser off |
| `L1` | Laser on, steady |
| `L<hz>` | Laser **modulated** at `<hz>`, e.g. `L7.0` |
| `V0` / `V1` | Vibration injector off / on |
| `C` | Centre both stages |
| `Z` | Declare the current position to be (0, 0) |
| `?` | Status query |
| `!` | Self-test — exercises every actuator in a diagnosable order |

`L0` and `L1` are special-cased; any other argument to `L` is read as a
frequency. So `L1` is steady-on, not 1 Hz — use `L1.0` if you ever
genuinely want 1 Hz.

### Why the laser is modulated

So the camera can identify the terminal's own dot by frequency, exactly
as it identifies the beacon. Beacon at 4 Hz, laser at 7 Hz, both in one
image, and the fine loop closes on the pixel vector between them. That
cancels parallax, boresight error, mount flex and range outright instead
of modelling them. See `docs/TERMINAL_MK3.md` §0 and
`src/fsoc_pat/hil/boresight.py`.

## Replies — controller to host

```
S <pan> <tilt> <src> <moving>
```

| Field | Meaning |
|---|---|
| `pan`, `tilt` | Degrees, 3 decimal places |
| `src` | `E` = measured by the encoders. `C` = commanded position only. |
| `moving` | `1` while either axis is still slewing, else `0` |

**`src` is not decoration.** The encoders are read only while both
steppers are at rest: an I²C transaction takes about a millisecond, and
at speed that is long enough to disturb the step timing and cause the
very skipped step the encoders exist to detect. So during a slew you get
`C`, and on arrival you get `E` — which is exactly the check that
matters, "did the motor actually reach where it was told," at no cost in
step fidelity.

A host that treats `C` as a measurement is fooling itself. Check the flag.

## Startup handshake

Call `check_protocol()` before every run. It sends one `?` and confirms
something answers. It costs a single round trip and converts this
system's worst failure mode — a silent wire-format mismatch — into one
line at startup.

```python
gimbal = SerialGimbal(port)
if not gimbal.check_protocol():
    raise SystemExit("controller did not answer a status query: "
                     "wrong firmware, wrong port, or wrong baud rate")
```
