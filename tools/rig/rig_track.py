"""
ZeroDrift mini-rig: physically point a laser at a blinking phone flashlight.

The webcam finds the beacon by its ~4 Hz blink (same identity principle as
the full simulator), and two SG90 servos steer the laser toward it with a
simple proportional loop — a real, physical coarse-alignment demo.

    pip install opencv-python numpy pyserial
    python tools/rig/rig_track.py                            # auto-detects the Arduino port
    python tools/rig/rig_track.py --port COM5                # or force a specific one

Keys:  arrows = manual trim   c = centre   l = laser toggle   q = quit
Safety: 5 mW class laser — never point at eyes; tape a paper target
behind the phone; keep the soft limits in the firmware.
"""
import argparse
import collections
import pathlib
import sys
import time
import traceback

import cv2
import numpy as np
import serial
from serial.tools import list_ports


def find_arduino_port():
    """Best-guess the Arduino's port so this can run with zero arguments
    (needed to double-click the packaged .exe with no console to pass
    --port into)."""
    ports = list(list_ports.comports())
    likely = [p for p in ports if any(k in (p.description or "") for k in
              ("Arduino", "CH340", "FTDI", "USB Serial", "USB-SERIAL"))]
    candidates = likely or [p for p in ports if "Bluetooth" not in (p.description or "")]
    return candidates[0].device if candidates else None


def show_message(text, seconds=6):
    """Only way to tell the operator something's wrong when there's no
    console attached (a double-clicked, --noconsole packaged .exe)."""
    img = np.zeros((260, 700, 3), dtype=np.uint8)
    for i, line in enumerate(text.split("\n")):
        cv2.putText(img, line, (20, 40 + i*32), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (70, 70, 235), 2, cv2.LINE_AA)
    cv2.imshow("ZeroDrift mini-rig", img)
    cv2.waitKey(int(seconds * 1000))
    cv2.destroyAllWindows()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None,
                    help="Arduino serial port; auto-detected if omitted")
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--blink", type=float, default=4.0)
    ap.add_argument("--gain", type=float, default=0.02,
                    help="servo degrees per pixel of error (start small)")
    ap.add_argument("--min-bright", type=int, default=200,
                    help="reject a candidate spot unless its raw pixel value "
                         "(0-255) is at least this bright; raise this if "
                         "skin/fingers/mouth get picked up instead of the "
                         "phone's LED flash, lower it if the LED never "
                         "registers as bright enough in a dim room")
    ap.add_argument("--history", type=int, default=48,
                    help="frames of brightness history required before a spot "
                         "can be scored; lower = locks faster but less sure, "
                         "higher = slower but more certain")
    ap.add_argument("--lock-threshold", type=float, default=0.32,
                    help="minimum blink-match score (0-1) to call something LOCKED")
    ap.add_argument("--match-radius", type=int, default=70,
                    help="max pixel distance for a new bright peak to count as "
                         "the same physical spot as an existing candidate; "
                         "raise this if a shaky hand keeps losing the lock "
                         "(it restarts history from zero every time identity "
                         "is lost)")
    ap.add_argument("--max-candidates", type=int, default=8,
                    help="distinct bright spots tracked per frame, at most; "
                         "raise this if the real beacon keeps getting crowded "
                         "out by other bright things in frame")
    ap.add_argument("--peak-contrast", type=int, default=45,
                    help="minimum local-contrast value for a spot to be "
                         "considered a candidate at all; lower this if the "
                         "LED is dim relative to a bright background")
    ap.add_argument("--velocity-gain", type=float, default=0.75,
                    help="how fast the motion estimate adapts to a change in "
                         "speed/direction (0-1); raise this if fast motion "
                         "still loses lock, lower it if the lock jitters when "
                         "the beacon is nearly still")
    ap.add_argument("--patch-radius", type=int, default=9,
                    help="half-width in px of the brightness-sampling patch "
                         "around each tracked spot; a bit larger tolerates "
                         "small prediction error during fast motion")
    args = ap.parse_args()

    port = args.port or find_arduino_port()
    if not port:
        show_message("No Arduino found.\nCheck the USB cable, then relaunch.")
        return 1
    try:
        ard = serial.Serial(port, 115200, timeout=0.01)
    except serial.SerialException as e:
        show_message(f"Could not open {port}:\n{e}\n"
                      "Check the cable / that nothing else has it open.")
        return 1
    time.sleep(2.0)                      # Nano resets on connect
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        show_message("No camera found.\nCheck it's connected and not in use "
                      "by another app.")
        return 1

    N = args.history         # brightness-history length used for the blink FFT
    NMS_RADIUS = 30          # px to suppress around a picked peak (avoid re-picking it)
    STALE_FRAMES = 90        # drop a candidate if nothing has re-lit it in this many frames
    candidates = []          # [{"pos", "hist", "times", "last_peak"}, ...]
    frame_idx = 0
    pan_deg, tilt_deg = 90.0, 90.0
    laser = False

    def send():
        ard.write(f"P{int(pan_deg)} T{int(tilt_deg)}\n".encode())

    def blink_score(hist, times):
        if len(hist) < N or times[-1] <= times[0]:
            return 0.0
        fps = (N-1) / (times[-1]-times[0])
        sig = np.array(hist) - np.mean(hist)
        k_bin = args.blink / fps * N
        w = np.exp(-2j*np.pi*k_bin*np.arange(N)/N)
        return min(1.0, 2.0*abs(np.dot(sig, w))**2 /
                   ((float(np.dot(sig, sig))+1e-9)*N/2))

    def draw_hud(frame, beacon, score, n_candidates, pan_deg, tilt_deg, laser, fps):
        H, W = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (W, 60), (25, 25, 25), -1)
        cv2.rectangle(overlay, (0, H-30), (W, H), (25, 25, 25), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        cv2.putText(frame, "ZERODRIFT  |  SIH26169 coarse-alignment demo",
                    (14, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (170, 170, 170), 1, cv2.LINE_AA)

        status_col = (80, 220, 120) if beacon else (70, 110, 230)
        cv2.putText(frame, "LOCKED" if beacon else "SEARCHING",
                    (14, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_col, 2, cv2.LINE_AA)

        detail = (f"blink {score:.2f}   targets {n_candidates}   "
                  f"pan {pan_deg:.0f} deg   tilt {tilt_deg:.0f} deg   "
                  f"laser {'ON' if laser else 'off'}   {fps:.0f} fps")
        cv2.putText(frame, detail, (155, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (225, 225, 225), 1, cv2.LINE_AA)

        dot_col = (0, 0, 255) if laser else (80, 80, 80)
        cv2.circle(frame, (W-22, 20), 8, dot_col, -1)
        cv2.circle(frame, (W-22, 20), 8, (200, 200, 200), 1)

        cx, cy = W // 2, H // 2
        cv2.line(frame, (cx-12, cy), (cx+12, cy), (110, 110, 110), 1)
        cv2.line(frame, (cx, cy-12), (cx, cy+12), (110, 110, 110), 1)

        cv2.putText(frame, "q quit   c centre   l laser   arrow keys trim",
                    (14, H-10), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 160), 1, cv2.LINE_AA)

    fps_ema, last_tick = 0.0, time.time()

    send()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        H, W = frame.shape[:2]
        frame_idx += 1
        now = time.time()
        dt = now - last_tick
        last_tick = now
        if dt > 0:
            fps_ema = 1.0/dt if fps_ema == 0 else 0.9*fps_ema + 0.1*(1.0/dt)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
        blur = cv2.GaussianBlur(tophat, (9, 9), 0)

        # Predict: coast every candidate forward by its last known velocity
        # before looking for it again, so a fast-moving light is searched for
        # where it's headed, not where it used to be.
        for c in candidates:
            vx, vy = c["vel"]
            c["pos"] = (c["pos"][0] + vx, c["pos"][1] + vy)

        # Find every distinct bright-enough spot this frame (not just the single
        # brightest) so a finger/mouth that's merely bright can't hide the real
        # blinking LED, or get selected over it.
        work = blur.copy()
        peaks = []
        for _ in range(args.max_candidates):
            _, mx, _, loc = cv2.minMaxLoc(work)
            if mx <= args.peak_contrast:
                break
            if int(gray[loc[1], loc[0]]) >= args.min_bright:
                peaks.append(loc)
            cv2.circle(work, loc, NMS_RADIUS, 0, -1)

        # Match each peak to the candidate already tracking that physical spot
        # (using its predicted position), or start a new candidate for it. On a
        # match, correct position to the real detection and update the
        # velocity estimate from the prediction error (a simple alpha-beta
        # tracker) so it keeps anticipating motion, not just reacting to it.
        matched = set()
        for loc in peaks:
            best_i, best_d = None, args.match_radius
            for i, c in enumerate(candidates):
                if i in matched:
                    continue
                d = np.hypot(loc[0]-c["pos"][0], loc[1]-c["pos"][1])
                if d < best_d:
                    best_i, best_d = i, d
            if best_i is None:
                candidates.append({"pos": loc, "vel": (0.0, 0.0),
                                    "hist": collections.deque(maxlen=N),
                                    "times": collections.deque(maxlen=N), "last_peak": frame_idx})
                matched.add(len(candidates) - 1)
            else:
                c = candidates[best_i]
                dx, dy = loc[0]-c["pos"][0], loc[1]-c["pos"][1]  # prediction error
                vx, vy = c["vel"]
                vx = float(np.clip(vx + args.velocity_gain*dx, -250, 250))
                vy = float(np.clip(vy + args.velocity_gain*dy, -250, 250))
                c["vel"] = (vx, vy)
                c["pos"] = loc
                c["last_peak"] = frame_idx
                matched.add(best_i)

        # Sample brightness at every tracked spot every frame — including the
        # OFF half of a blink cycle, where it won't show up as a peak at all.
        r = args.patch_radius
        for c in candidates:
            x, y = int(round(c["pos"][0])), int(round(c["pos"][1]))
            patch = gray[max(0, y-r):y+r+1, max(0, x-r):x+r+1]
            c["hist"].append(float(patch.mean()) if patch.size else 0.0)
            c["times"].append(time.time())

        # Forget spots nothing has re-lit in a while (a hand that moved on, etc).
        candidates = [c for c in candidates if frame_idx - c["last_peak"] <= STALE_FRAMES]

        # Identity is the ~4 Hz modulation, not brightness: score every
        # candidate and steer only toward whichever one is actually blinking.
        best, score = None, 0.0
        for c in candidates:
            s = blink_score(c["hist"], c["times"])
            if s > score:
                best, score = c, s
        beacon = best is not None and score > args.lock_threshold

        if beacon:
            # Steer toward where the beacon will be by the time this command
            # takes effect, not where it was this frame — plain proportional
            # control on the current position always lags a moving target,
            # more so the faster it moves. This is the same reason the real
            # engine's Smith predictor steers off a model prediction instead
            # of the raw measurement.
            px = best["pos"][0] + args.lead * best["vel"][0]
            py = best["pos"][1] + args.lead * best["vel"][1]
            ex, ey = px-W/2, py-H/2
            pan_deg = float(np.clip(pan_deg - args.gain*ex, 20, 160))
            tilt_deg = float(np.clip(tilt_deg + args.gain*ey, 40, 140))
            send()
            if not laser:
                laser = True; ard.write(b"L1")
        elif laser:
            laser = False; ard.write(b"L0")

        # Only ever mark the beacon itself — every other bright spot (eyes,
        # fingers, mouth, room lights) is tracked internally to keep it from
        # stealing the lock, but it's not the operator's business and stays
        # off the screen so the display isn't cluttered with distractions.
        if beacon:
            bx, by = int(round(best["pos"][0])), int(round(best["pos"][1]))
            cv2.circle(frame, (bx, by), 18, (80, 220, 120), 2)
            cv2.circle(frame, (bx, by), 26, (80, 220, 120), 1)
        draw_hud(frame, beacon, score, len(candidates), pan_deg, tilt_deg, laser, fps_ema)
        cv2.imshow("ZeroDrift mini-rig", frame)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        elif k == ord('c'):
            pan_deg = tilt_deg = 90.0; send()
        elif k == ord('l'):
            laser = not laser; ard.write(b"L1" if laser else b"L0")
        elif k == 81: pan_deg = max(20, pan_deg-2); send()    # left
        elif k == 83: pan_deg = min(160, pan_deg+2); send()   # right
        elif k == 82: tilt_deg = max(40, tilt_deg-2); send()  # up
        elif k == 84: tilt_deg = min(140, tilt_deg+2); send() # down

    ard.write(b"L0"); cap.release(); cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        # No console when double-clicked as a packaged .exe -- leave a trail
        # instead of just silently vanishing.
        base = pathlib.Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
        with open(base / "rig_debug.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            traceback.print_exc(file=f)
        try:
            show_message("Something went wrong.\nSee rig_debug.log next to "
                          "this program for details.", seconds=8)
        except Exception:
            pass
        code = 1
    raise SystemExit(code)
