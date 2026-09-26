# MK2 — the weekend build (for Monday's submission)

> **The step-by-step build guide is `docs/build.html`** (on the site: *MK2 BUILD
> GUIDE* under the MK1/MK2 comparison), also as
> `docs/submission/ZeroDrift_MK2_Build_Guide.pdf`, with the 3D assembly at
> `docs/assembly.html`. Every wire, command and check is there. This file is
> the reasoning behind it.

**Verdict on the "AI Laser Turret v1.3" design (diaawastaken, Instagram):**
it is the same machine as our MK2 — two NEMA17s, the camera and the laser
on one plate riding the tilt axis — plus a GT2 belt reduction on both axes
and fully 3D‑printed structure. That is exactly our **Tier B** in
`docs/TERMINAL_MK3.md`. The design is right; copying it *literally* by
Monday is not, because it needs ~20–30 h of 3D printing, belt tensioning
and a second round of fixing prints. **Take its three ideas, not its
parts.** All three work with what we already have plus ~₹700 from Amar
Robotics / a hardware shop, and all three plug into our software unchanged.

| Idea from that turret | Why it matters | How we do it without a printer |
|---|---|---|
| **Camera + laser on one rigid plate on the tilt axis** | The camera sees its own laser dot → our dot‑to‑beacon loop cancels parallax and mount error | 3 mm acrylic (in hand) or 2 mm aluminium plate, bolted to the tilt shaft with a **5 mm flange coupling** |
| **Pan load on a bearing, not on the motor shaft** | No wobble, no friction, no skipped steps | Our head is light (~0.4 kg on the pan shaft), well inside a NEMA17's own bearings, so the platform goes straight on a **5 mm flange coupling**. A **100 mm lazy‑Susan bearing** is the fallback only if the platform wobbles |
| **Balanced head** | Tilt motor holds position with almost no current; no sag, no drift | Put the plate's centre of mass on the tilt axis (move camera/laser until the head stays wherever you leave it with the motor off) |
| *(Belt reduction 3:1)* | 3× finer and 3× more accurate | **Optional, only if pulleys are in stock.** Software already supports it: set **MK2 DRIVE** on the Live page and `*_GEAR_RATIO` in firmware |

---
## 1. Buy today (Amar Robotics / hardware shop)

Already in hand (per `ZeroDrift_StillToBuy.pdf`): 2× NEMA17, 2× A4988,
2× L‑bracket, capacitors, Nano, KY‑008 laser, 3S pack + charger, acrylic,
wires, screws. You now have the USB webcam.

| # | Item | Qty | ~₹ | Why | Check at the counter |
|---|---|---|---|---|---|
| 1 | AS5600 magnetic encoder module | 2 | 500 | Closed loop — "accurate" becomes a measurement | 11×11 mm board, "AS5600" on the chip |
| 2 | Diametric magnet 6×2.5 mm | 2 | 180 | The AS5600 reads nothing without it | Must be **diametric**, not axial (usually sold with the AS5600) |
| 3 | TCA9548A I²C multiplexer | 1 | 200 | Both AS5600s have the same address | 8‑channel, TCA/PCA9548A |
| 4 | **5 mm rigid flange coupling** (shaft → plate) | 2 | 200–300 | Bolts plates straight to the motor shafts, no play | Bore **5 mm** (NEMA17 shaft), with grub screws |
| 5 | *Optional:* lazy‑Susan turntable bearing, 100 mm | 1 | 150–300 | Only if the platform wobbles on the flange coupling | Smooth, no grit |
| 6 | M4×12 bolts + nuts | 8 | 40 | Bearing to base and platform | — |
| 7 | Red gel sheet / red acrylic scrap (or any sunglasses lens) | 1 | 50–100 | Over the camera: bright room goes dark, beacon stays bright | Hold it to your phone camera — the room should look dim |
| — | *Optional belt kit:* GT2 20T pulley 5 mm bore ×2, GT2 60T pulley ×2, GT2 closed belts (length to fit), 608ZZ ×4 | — | ~1,700 | 3:1 reduction (Tier B) | Only if in stock **and** someone can drill/cut the mounts today |

**Total for items 1–7: ~₹1,300–1,600.**

---
## 2. Build — one day

Follow `docs/build.html` sections 4–8 in order (mechanics → wiring → firmware
→ first power‑on). Every step there ends in a check. Soft limits are
**pan ±90°, tilt ±18°** (the CAD clearance check has the head touching the
platform at +21° tilt); firmware, `mk2.py` and the Live page all clamp to them.

---
## 3. Connect to the website (zerodrift-fsoc-pat.netlify.app/live)

1. Chrome/Edge. **START CAMERA**, then **MK2 CAMERA (USB)** — the view
   switches to the gimbal's camera (labelled *MK2 CAM*).
2. **CONNECT RIG** → pick the Nano's port. It auto‑detects MK2.
   In the RIG card set **MK2 DRIVE** to match the firmware
   (Direct drive, or 3:1 if belted).
3. **TEST MOTION** — pan right, tilt up, laser blinks. If an axis goes
   the wrong way tick **INVERT**; wrong axis → **SWAP**.
4. Beacon on (4 Hz). It locks, the head turns to centre it.
   Turn the laser on, click **SET AIM** and click the laser dot in the
   video — from then on the rig drives the beacon onto the dot.
5. Set **BEACON RATE** to the beacon's actual rate — the tracker now
   locks **only** that rate (±10 %); a 3 Hz or 5 Hz light is ignored.

---
## 4. Honest numbers to quote

Direct drive, 1/16 step: **0.11° (1.96 mrad) per step**, AS5600 reading
**0.088° (1.5 mrad)** — "~1.5–2 mrad, encoder‑verified". With a 3:1 belt:
**0.65 mrad/step**. Measure it (TERMINAL_MK3 §7.2) before saying it.

## 5. What can go wrong (and the fix)

| Symptom | Cause | Fix |
|---|---|---|
| Motor buzzes, doesn't turn | Vref too low / coil pair swapped | Vref 0.55 V; swap one coil's two wires |
| Head sags or drifts after moves | Unbalanced head | Move camera/laser until it balances |
| Loses position on fast moves | Too much acceleration for the load | Lower `setAcceleration` in firmware; balance the head |
| Won't lock in a bright room | Camera exposure | Red filter / sunglasses lens over the camera |
| Locks, but the wrong way round | Axis direction | **INVERT** / **SWAP** in the RIG card |
