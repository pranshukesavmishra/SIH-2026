"""
The live loop: the simulation's algorithms, a real camera, real servos.

    python -m fsoc_pat.hil.live

With no flags at all it auto-detects the Arduino's serial port and a
working camera, and runs with sane default calibration if
hardware/calibration.yaml hasn't been produced yet by hil.calibrate --
this is meant to be the "plug it in and run it" console, not a tool that
needs a calibration ritual before anyone can see anything move.

Builds a CoarseAlignmentTracker from a scenario config whose camera/gimbal
sections have been overwritten with the CALIBRATED (or default) numbers,
then feeds it LiveFrame objects instead of simulated ones. The tracker
cannot tell the difference -- which is the entire demonstration.

Keys in the live window:  q = quit   c = re-centre   l = laser toggle
"""
from __future__ import annotations

import argparse
import os
import time

import numpy as np
import yaml

from ..config import SimConfig
from ..metrics import build_report
from ..pipeline import CoarseAlignmentTracker
from .rig import LiveFrame, SerialGimbal, UsbCamera, find_camera, find_serial_port

DEFAULT_CALIBRATION = {
    "px_per_rad_pan": None,      # None -> derive from --fov-deg default below
    "px_per_rad_tilt": None,
    "command_latency_ms": 150.0,  # conservative; real rigs measure faster
    "exposure": None,
}
DEFAULT_FOV_DEG = 60.0          # typical laptop/webcam horizontal FOV


def _resolve_port(explicit: str | None) -> str:
    if explicit:
        return explicit
    found = find_serial_port()
    if found is None:
        raise SystemExit(
            "no serial port found automatically -- is the rig plugged in? "
            "pass --port explicitly (see `ls /dev/cu.*` on macOS or Device "
            "Manager on Windows) if auto-detect keeps missing it."
        )
    print(f"auto-detected serial port: {found}")
    return found


def _resolve_camera(explicit: int | None) -> int:
    if explicit is not None:
        return explicit
    found = find_camera()
    if found is None:
        raise SystemExit(
            "no working camera found automatically -- check camera "
            "permissions for this app/terminal (macOS: System Settings -> "
            "Privacy & Security -> Camera), or pass --camera explicitly."
        )
    print(f"auto-detected camera index: {found}")
    return found


def _load_calibration(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            calib = yaml.safe_load(fh)
        print(f"calibration: loaded from {path}")
        return calib
    print(f"calibration: {path} not found -- using rough defaults "
          f"(FOV {DEFAULT_FOV_DEG:.0f} deg, {DEFAULT_CALIBRATION['command_latency_ms']:.0f} ms "
          f"latency). Run `python -m fsoc_pat.hil.calibrate` later for real accuracy.")
    return dict(DEFAULT_CALIBRATION)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None, help="omit to auto-detect")
    parser.add_argument("--camera", type=int, default=None, help="omit to auto-detect")
    parser.add_argument("--calibration", default="hardware/calibration.yaml")
    parser.add_argument("--duration", type=float, default=300.0)
    parser.add_argument("--blink-hz", type=float, default=4.0)
    parser.add_argument("--fov-deg", type=float, default=None,
                        help="override; else derived from calibration or default")
    parser.add_argument("--exposure", type=float, default=None,
                        help="manual exposure to lock (overrides calibration file); "
                             "use this for dim rooms so auto-exposure doesn't hunt "
                             "on every beacon blink")
    parser.add_argument("--no-window", action="store_true",
                        help="headless: skip the live cv2 display")
    parser.add_argument("--cfar-k", type=float, default=8.0,
                        help="detection threshold (std devs above background). "
                             "Default is stricter than the simulator's 5.0 -- "
                             "the CFAR detector was only ever tuned against clean "
                             "synthetic frames in the test suite, and a real webcam "
                             "sensor's noise floor is coarser, so a low threshold "
                             "here means the tracker chases noise around the frame "
                             "when no beacon is present. Raise further if it still "
                             "grabs onto false targets; lower if it's missing a "
                             "real, dim beacon.")
    parser.add_argument("--lock-frames", type=int, default=8,
                        help="consecutive good frames required before committing "
                             "to TRACK (and firing the laser). Higher = slower to "
                             "lock but far less prone to locking onto a one-frame "
                             "noise spike; default raised from the simulator's 5.")
    args = parser.parse_args(argv)

    port = _resolve_port(args.port)
    camera_index = _resolve_camera(args.camera)
    calib = _load_calibration(args.calibration)

    cfg = SimConfig()
    cfg.name = "live"
    px_per_rad = calib.get("px_per_rad_pan")
    if args.fov_deg:
        cfg.camera.fov_deg = args.fov_deg
    elif px_per_rad:
        cfg.camera.fov_deg = float(np.degrees(cfg.camera.width / px_per_rad))
    else:
        cfg.camera.fov_deg = DEFAULT_FOV_DEG
    cfg.gimbal.command_latency_ms = calib.get("command_latency_ms") or 150.0
    cfg.gimbal.max_rate_deg_s = 45.0
    cfg.beacons[0].blink_hz = args.blink_hz
    cfg.turbulence.enabled = False          # the real air provides its own
    cfg.vibration.enabled = False

    exposure = args.exposure if args.exposure is not None else calib.get("exposure")

    gimbal = SerialGimbal(port)
    camera = UsbCamera(camera_index, exposure=exposure)
    tracker = CoarseAlignmentTracker(cfg, fou_radius_deg=8.0,
                                     search_centre=(0.0, 0.0),
                                     cfar_k=args.cfar_k, lock_frames=args.lock_frames)

    show_window = not args.no_window
    cv2 = None
    if show_window:
        try:
            import cv2 as _cv2
            cv2 = _cv2
        except ImportError:
            print("opencv not available for display -- continuing headless")
            show_window = False

    print(f"live: FOV {cfg.camera.fov_deg:.1f} deg, "
          f"latency {cfg.gimbal.command_latency_ms:.0f} ms, "
          f"beacon {args.blink_hz} Hz, exposure {exposure} -- "
          f"tracking for {args.duration:.0f} s (q to quit)")
    gimbal.centre()
    time.sleep(1.5)

    # Hardware safety limiter -- independent of whatever the tracker's own
    # search/estimator logic decides, so a bad estimate (or a search pattern
    # tuned for the simulator's assumed frame timing, not this webcam's
    # actual, variable capture rate) can never slam the servo hard or fast.
    # The tilt servo has already failed once from being driven into a bind;
    # this makes that class of failure physically impossible from software.
    SAFETY_MAX_STEP_DEG = 4.0        # max degrees moved per actual command
    SAFETY_MIN_INTERVAL_S = 0.12     # >= ~8 Hz cap on commands sent to the wire
    last_sent_pan, last_sent_tilt = 90.0, 90.0
    last_sent_time = 0.0

    index = 0
    laser_on = False
    t0 = time.perf_counter()
    try:
        while time.perf_counter() - t0 < args.duration:
            image = camera.read()
            if image is None:
                continue
            pointing = gimbal.reported_pointing()
            frame = LiveFrame(index=index, time_s=time.perf_counter() - t0,
                              image=image, pointing_true=pointing,
                              pointing_reported=pointing)
            az, el = tracker.update(frame)

            now = time.perf_counter()
            want_pan = 90.0 + np.degrees(az - gimbal.offset[0]) * gimbal.scale[0]
            want_tilt = 90.0 + np.degrees(el - gimbal.offset[1]) * gimbal.scale[1]
            if now - last_sent_time >= SAFETY_MIN_INTERVAL_S:
                step_pan = float(np.clip(want_pan - last_sent_pan,
                                         -SAFETY_MAX_STEP_DEG, SAFETY_MAX_STEP_DEG))
                step_tilt = float(np.clip(want_tilt - last_sent_tilt,
                                          -SAFETY_MAX_STEP_DEG, SAFETY_MAX_STEP_DEG))
                if abs(step_pan) > 0.3 or abs(step_tilt) > 0.3:
                    last_sent_pan += step_pan
                    last_sent_tilt += step_tilt
                    gimbal.raw_command(last_sent_pan, last_sent_tilt)
                    last_sent_time = now

            telem = tracker.telemetry[-1]
            # Only trust a sustained TRACK, not a transient ACQUIRE/COAST
            # flicker, before lighting up the laser -- avoids it firing on
            # noise the detector briefly mistook for the beacon.
            want_laser = telem.state.value == "TRACK"
            if want_laser != laser_on:
                gimbal.laser(want_laser)
                laser_on = want_laser

            if show_window:
                disp = (image >> 4).astype(np.uint8)
                disp = cv2.cvtColor(disp, cv2.COLOR_GRAY2BGR)
                col = (80, 220, 120) if telem.locked else (60, 60, 230)
                cv2.putText(disp,
                            f"{telem.state.value:9} det {telem.n_detections}  "
                            f"laser {'ON' if laser_on else 'off'}  "
                            f"t={telem.time_s:5.1f}s",
                            (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col, 2)
                cv2.imshow("ZeroDrift live console", disp)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    gimbal.centre()
                    last_sent_pan, last_sent_tilt = 90.0, 90.0
                    last_sent_time = now
                elif key == ord('l'):
                    laser_on = not laser_on
                    gimbal.laser(laser_on)

            index += 1
            if index % 30 == 0:
                print(f"  t={telem.time_s:5.1f}s {telem.state.value:9} "
                      f"det {telem.n_detections}", flush=True)
    finally:
        gimbal.laser(False)
        gimbal.centre()
        camera.release()
        if show_window:
            cv2.destroyAllWindows()

    report = build_report(tracker.telemetry, "live", 30.0,
                          wall_time_s=time.perf_counter() - t0)
    print(report.to_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
