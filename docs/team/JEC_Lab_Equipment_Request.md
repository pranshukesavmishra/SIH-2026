# Equipment request — JEC IoT & Robotics Lab

**To:** jec.iotroboticslab@gmail.com
(the site's "Contact Lab" button points at `about.html`, where this address is listed)

**Subject:** Equipment request — SIH 2026 team, PS26169 (ISRO) — 4 items

---

Respected Sir/Ma'am,

I am Aryan Singh, team leader of **Team ZeroDrift**, Jabalpur Engineering
College. We are building our entry for **Smart India Hackathon 2026,
problem statement PS26169 (ISRO)** — an AI-based virtual camera tracking
system for coarse alignment of mobile free-space-optical communication
terminals.

We have bought most of the hardware ourselves. Four items remain, and we
are writing to ask whether the lab can issue any of them before we
purchase.

### 1. HD USB WebCam — listed on your equipments page

Your **Sensors & Input Devices** section lists an *HD USB WebCam*. This is
the one item we found that matches our requirement, and we would be
grateful to be issued one.

**One question we must ask before requesting it.** Our design needs the
camera to be **bolted rigidly to a moving pan/tilt head** — the camera
rides the gimbal and is boresighted with a laser, so any movement between
the camera and the mount reads as a pointing error that is not real. To do
that we would need to **remove the plastic housing** and mount the bare
camera board inside our 72 × 46 × 42 mm enclosure.

We understand that may not be permitted for lab property, and we will not
modify anything without explicit permission. Could you please tell us
whether:

- **(a)** we may remove the housing, in which case we would like to request one; or
- **(b)** it must stay intact, in which case we will buy our own and not trouble the lab.

Either answer is genuinely useful to us — we only need to know which.

### 2–4. Three items we could not find listed

These are not on the equipments page, but a webpage is rarely a complete
inventory, so we wanted to ask directly:

| Item | Qty | What it does in our build |
|---|---|---|
| **AS5600 magnetic rotary encoder module** | 2 | Absolute shaft-angle feedback on the pan and tilt axes. This is what lets us *measure* pointing accuracy instead of claiming it. |
| **TCA9548A (or PCA9548A) I²C multiplexer** | 1 | Both AS5600s are hard-wired to I²C address 0x36 and cannot share a bus, so the multiplexer is not optional. |
| **3S 12.6 V Li-ion balance charger** | 1 | Our motor supply is a 3-cell 18650 pack; we demonstrate on stage with no mains adapter. |

**A note on one near-match, so we are not asking for the wrong thing.**
We saw the *Quad Encoder Geared DC Motor (200RPM, 12V DC)* in your Motors &
Actuators section. We do not think it can substitute for the AS5600, for
two reasons: its encoder is **incremental**, so it loses absolute position
on every power cycle, whereas ours must know the shaft angle the instant it
powers up; and it is **integral to a DC gearmotor**, so it cannot be fitted
to the NEMA17 stepper shafts our gimbal uses. We mention this only in case
it looked like an obvious answer to us.

If the lab has any of these three loose in stock we would be glad to be
issued them; if not, no difficulty — we will purchase them.

### What we can offer back

Our full design is open and documented — bill of materials, build guide,
CAD, firmware and test tooling. We would be happy to deposit the completed
terminal, the documentation, or a demonstration session with the lab after
the hackathon, if that is of any use to you.

Thank you for your time and for keeping the lab open to student projects.

With respect,

**Aryan Singh**
Team Leader, Team ZeroDrift
Jabalpur Engineering College
aryansingh882005@gmail.com

---

## Notes for us, not for the email

- **Total at stake: ₹1,747.** Webcam ₹800 (conditional on the housing
  answer), AS5600 ×2 ₹498, TCA9548A ₹199, charger ₹250.
- **Do not wait on this to order the AS5600s** if the build schedule is
  tight. They are the long pole: nothing about closed-loop pointing can be
  tested without them, and a lab reply may take days.
- **If the answer on the housing is (b)**, buy the webcam the same day. A
  camera that is not rigid on the moving head breaks the architecture, and
  ₹800 is the cheapest possible fix for that.
- The lab has **no NEMA17 steppers and no A4988 drivers** either — we
  checked the whole page text, not just the titles. Everything else in our
  build was always going to be ours.
