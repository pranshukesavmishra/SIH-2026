# Host ↔ motion controller protocol

**One definition, three implementations**, and a test that holds them
together: `tools/rig/rig_firmware_v2.ino` (the sketch),
`src/fsoc_pat/hil/mk2.py` (the Mk2 driver) and `src/fsoc_pat/hil/rig.py`
(the Mk1 servo path, which speaks its own older dialect and is documented
at the bottom). `tests/test_protocol_contract.py` drives the real driver
in dry-run mode and parses what it emits against the sketch's grammar —
so if either side moves, CI says so instead of the rig doing it.

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

1. **The wire is motor steps**, integer, for the coarse stage. Not
   degrees. An earlier revision of this document specified degrees and
   the sketch was rewritten to match it — which would have broken
   `hil/mk2.py`, a tested driver with a safety envelope, in favour of an
   untested sketch. The sketch was moved back. Between a tested host and
   an untested sketch, the sketch moves.
2. **The host owns the steps-per-radian scale**, in
   `mk2.py: DEFAULT_STEPS_PER_RAD = 200 * 16 / 2π`. The firmware's
   `MICROSTEPS` must agree with it; a test asserts that, because a
   disagreement silently scales every angle and the rig points
   consistently wrong with nothing in any log.
3. **Every message ends with `\n`.** A command without one leaves the
   firmware holding a partial line, which then consumes the front of the
   next command and silently drops it.
4. **Lines beginning `#` are human-readable log output.** Hosts ignore them.
5. **Unknown commands are ignored silently.** A newer host must not jam an
   older firmware.

## Commands — host to controller

| Command | Meaning |
|---|---|
| `P<int> T<int>` | Coarse absolute target, **motor steps** from centre. `T` may be omitted. Clamped to soft limits in the firmware as a backstop; `mk2.py` also clamps host-side. |
| `T<int>` | Tilt alone |
| `p<int> t<int>` | Fine-stage absolute angle, **servo degrees** (20–160 / 40–140). Accepted and ignored unless built with `FINE_STAGE 1`. |
| `t<int>` | Fine tilt alone |
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
S <panSteps> <tiltSteps> <src> <moving>
```

| Field | Meaning |
|---|---|
| `panSteps`, `tiltSteps` | Motor steps — the same unit as the wire, so the host never holds two scales at once. The encoders measure degrees physically; the conversion happens in the firmware, where the mechanical constants already live. |
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
gimbal = Mk2Gimbal(port)
# ... and if the sketch is built with the encoder block, "?" answers.
```

Note that `hil/mk2.py` does not yet issue `?`; its `reported_pointing()`
returns the commanded position. The `?` reply is additive and exists for
when the AS5600s are fitted — wiring it in is the obvious next step once
the encoders are on real shafts.

---
## Appendix — the Mk1 dialect

`src/fsoc_pat/hil/rig.py` drives the older servo rig
(`tools/rig/rig_firmware.ino`) and speaks a different, simpler dialect:
`P<deg> T<deg>` in **servo degrees centred on 90**, `L0`/`L1`, no status
query at all (`reported_pointing()` returns the last commanded value,
which is honest — servos have no feedback to report). It is not the same
protocol and should not be made to look like one. It stays because it
drives hardware that exists and works.
