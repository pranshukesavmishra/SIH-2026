# ZeroDrift Physical System — Master Bill of Materials

*The single combined parts list across every physical subsystem: the
Mk2 tracker (camera + laser + pan-tilt) and the new Beacon + Decoy
units. Tracker prices are real, screenshot-verified Amazon.in prices
from a live pricing pass — not estimates. Beacon/decoy prices are
estimates (not yet price-checked) and are marked as such.*

Not in the pitch deck, same reasoning as always: the PS is
Software category, validated without hardware. This is the Grand
Finale table demo, if shortlisted (Dec 2026) — no deadline pressure.

---
## Tracker — Mk2 (camera, laser, pan-tilt, closed-loop)

Real prices, verified against live Amazon.in listings.

| Item | Qty | Unit (real) | Line total |
|---|---|---|---|
| NEMA17 stepper motor (bare, 4.2kg-cm) | 2 | ₹749 | ₹1,498 |
| A4988 stepper driver | 2 | ₹170 | ₹340 |
| AS5600 magnetic encoder | 2 | ₹249 | ₹498 |
| TCA9548A I²C multiplexer | 1 | ₹199 | ₹199 |
| NEMA17 single-axis L-bracket ×2 (DIY pan+tilt) | 2 | ₹127 | ₹254 |
| MG90S metal-gear micro servo (2-pack) | 1 | ₹399 | ₹399 |
| 12V 2A DC power adapter | 1 | ₹279 | ₹279 |
| Acrylic sheet 3mm, 6″×6″ (pack of 2) | 1 | ₹199 | ₹199 |
| Mini vibration motor, 3V DC | 1 | ₹20 | ₹20 |
| Transistor+diode+resistor combo kit | 1 | ₹105 | ₹105 |
| KY-008 laser module | — | ₹0 | reuse from Mk1 |
| Small ABS project box (camera+laser head) | 1 | ₹80–150 est. | ₹80–150 |
| Matte black spray paint (optional) | 1 | ₹219 | ₹219 |
| **Tracker subtotal** | | | **₹4,190–4,410 core, +₹219 if painted** |

*(Webcam and tripod excluded — team is sourcing those separately.)*

---
## Beacon unit (the precise, Arduino-driven target)

Estimates — not yet price-checked live. Treat as planning numbers.

| Item | Qty | Unit (est.) | Line total |
|---|---|---|---|
| Arduino Nano (dedicated — do not share with the tracker) | 1 | ₹200–250 | ₹200–250 |
| High-brightness 10mm LED | 1 | ₹15–30 | ₹15–30 |
| 2N2222 NPN transistor | 1 | ₹10 | ₹10 |
| 220Ω + 1kΩ resistor | 2 | ₹5 | ₹10 |
| Ping-pong ball (diffuser) | 1 | ₹20–40 | ₹20–40 |
| 9V battery + clip (or 2×AA holder) | 1 | ₹80–150 | ₹80–150 |
| SPST toggle switch | 1 | ₹20–30 | ₹20–30 |
| Small ABS project box | 1 | ₹80–150 | ₹80–150 |
| **Beacon subtotal** | | | **₹435–670** |

## Decoy unit (the control — proves the rejection)

| Item | Qty | Unit (est.) | Line total |
|---|---|---|---|
| High-brightness LED (brighter than the beacon's) | 1 | ₹15–30 | ₹15–30 |
| 150Ω resistor | 1 | ₹5 | ₹5 |
| CR2032 + holder (or 2×AA pack) | 1 | ₹40–80 | ₹40–80 |
| Switch | 1 | ₹20–30 | ₹20–30 |
| Housing (reuse scrap / bottle cap) | 1 | ₹0–40 | ₹0–40 |
| **Decoy subtotal** | | | **₹80–185** |

---
## Grand total — entire physical system

| Subsystem | Range |
|---|---|
| Tracker (core, unpainted) | ₹4,190–4,410 |
| Tracker (painted) | +₹219 |
| Beacon | ₹435–670 |
| Decoy | ₹80–185 |
| **Everything, all-in** | **≈ ₹4,705–5,485** |

If you already own a hot glue gun and pick a black enclosure box for
the tracker's camera+laser head (saves the ₹219 paint), realistic
total lands closer to **₹4,700–5,050**.

---
## What's real vs estimated — be straight about this with judges

If asked "how much did the physical rig cost," the honest answer is:
tracker pricing was checked against live listings and is solid; beacon
and decoy pricing is a planning estimate from component-class market
ranges, not yet verified against live listings the way the tracker
was. Say so if asked — it's a small, cheap subsystem, and volunteering
the distinction is more credible than presenting both as equally
verified.

## Build order

1. **Decoy first** — 10 minutes, no firmware, immediately useful even
   before the beacon exists (any steady light works as a placeholder
   decoy for early tracker testing).
2. **Beacon second** — needs firmware flashed and a bench check of the
   actual blink rate before trusting it.
3. **Tracker Mk2** — per the phased order already in
   `docs/rig_mk2_build_guide.md` (ground-truth logger → coarse stage +
   encoders → base → fine stage → disturbance injector).
4. **Combined test** — beacon + decoy both in frame, tracker locks the
   correct one. This is the actual demo, not any one piece alone.
