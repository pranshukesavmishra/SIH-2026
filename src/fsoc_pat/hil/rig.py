"""
Drivers for the physical rig, behind the same contracts as the simulation.

The design rule for this package: the detector, tracker, estimator and
controller must not know whether they are running against the simulator or
against a webcam and two servos. Everything hardware-specific lives here, and
everything here presents interfaces the virtual counterparts already defined.
That is the transfer claim -- "the identical code drives real optics" -- and
it is enforced by construction, not by a diagram.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class LiveFrame:
    """Duck-typed stand-in for simulator.Frame: same fields the tracker reads."""
    index: int
    time_s: float
    image: np.ndarray
    pointing_true: Tuple[float, float]        # best knowledge = reported
    pointing_reported: Tuple[float, float]
    dropped: bool = False
    targets: List = field(default_factory=list)
    glint: Optional[tuple] = None

    @property
    def primary(self):
        return None                            # no ground truth in the real world


class SerialGimbal:
    """
    The pan-tilt stage, presenting the virtual Gimbal's command surface.

    Angles are radians at this interface, exactly as in the simulation;
    degrees exist only on the wire. The firmware owns every mechanical
    constant -- microstepping, belt ratio, steps per degree -- so nothing
    here changes when the mechanics do.

    Speaks PROTOCOL v3 (docs/HARDWARE_PROTOCOL.md). Earlier revisions of
    this class sent degrees to a firmware that parsed motor steps, and
    queried a status endpoint that did not exist. Both are fixed here,
    and `check_protocol()` exists so that a mismatch is caught in one
    line at startup instead of presenting as a tracker that mysteriously
    never locks.
    """

    #: Bump whenever the wire format changes incompatibly.
    PROTOCOL = 3

    def __init__(self, port: str, baud: int = 115200,
                 scale: Tuple[float, float] = (1.0, 1.0),
                 offset_rad: Tuple[float, float] = (0.0, 0.0),
                 status_timeout_s: float = 0.05):
        import serial                                    # pyserial
        self.ser = serial.Serial(port, baud, timeout=0.02)
        time.sleep(2.0)                                  # board resets on open
        self.scale = scale
        self.offset = offset_rad
        self.status_timeout_s = status_timeout_s
        self.az = 0.0
        self.el = 0.0
        self.encoder_backed = False       # was the last reading measured?
        self.moving = False
        self.stale_reads = 0              # queries that got no answer

    # -- outbound ---------------------------------------------------------

    def _send(self, line: str) -> None:
        # Every command is newline-terminated. A missing newline leaves the
        # firmware holding a partial line, which then eats the front of the
        # next command -- silently dropping a pointing update.
        self.ser.write((line + "\n").encode())

    def command(self, az: float, el: float) -> None:
        pan = np.degrees((az - self.offset[0]) * self.scale[0])
        tilt = np.degrees((el - self.offset[1]) * self.scale[1])
        self._send(f"P {pan:.3f} {tilt:.3f}")

    def laser(self, mode) -> None:
        """
        False/0 -> off, True -> steady on, a number -> modulate at that Hz.

        Modulating matters: the camera identifies the laser's own dot by
        its frequency, the same way it identifies the beacon. That is what
        lets the fine loop close on the dot-to-beacon error and cancel
        parallax instead of modelling it.
        """
        if mode is False or mode == 0:
            self._send("L0")
        elif mode is True:
            self._send("L1")
        else:
            self._send(f"L{float(mode):.2f}")

    def vibration(self, on: bool) -> None:
        self._send("V1" if on else "V0")

    def centre(self) -> None:
        self._send("C")

    def zero(self) -> None:
        """Declare the current physical position to be (0, 0)."""
        self._send("Z")

    # -- inbound ----------------------------------------------------------

    def reported_pointing(self) -> Tuple[float, float]:
        """
        Where the stage actually is, in radians.

        Encoder reading when the stage is at rest and the encoders
        answered; commanded position otherwise. Which one you got is in
        `encoder_backed`. On no reply the previous value is returned and
        `stale_reads` increments -- a climbing `stale_reads` means the
        firmware is not answering, not that the rig is holding still.
        """
        self._send("?")
        deadline = time.time() + self.status_timeout_s
        while time.time() < deadline:
            raw = self.ser.readline().decode(errors="ignore").strip()
            if not raw or raw.startswith("#"):
                continue                                  # firmware log line
            if not raw.startswith("S "):
                continue
            parts = raw.split()
            if len(parts) < 3:
                continue
            try:
                pan_deg, tilt_deg = float(parts[1]), float(parts[2])
            except ValueError:
                continue
            self.encoder_backed = len(parts) > 3 and parts[3] == "E"
            self.moving = len(parts) > 4 and parts[4] == "1"
            self.az = np.radians(pan_deg) / self.scale[0] + self.offset[0]
            self.el = np.radians(tilt_deg) / self.scale[1] + self.offset[1]
            return self.az, self.el
        self.stale_reads += 1
        return self.az, self.el

    def check_protocol(self) -> bool:
        """
        Confirm the firmware answers a status query before the run starts.

        Cheap, and it turns this rig's worst failure mode -- software and
        firmware disagreeing about the wire format, which looks exactly
        like "the tracker just never locks" -- into one line at startup.
        """
        before = self.stale_reads
        self.reported_pointing()
        return self.stale_reads == before


class PiGlobalShutterCamera:
    """
    The Mk3 head camera: Raspberry Pi Global Shutter (IMX296), C-mount.

    Global shutter is a nice-to-have here, not a requirement -- an earlier
    revision of this docstring overstated it. A rolling shutter exposes
    rows at different instants, but its readout is 10-30 ms against a
    250 ms blink period, and the fine loop measures when the head is at
    rest, so the smear is small. `UsbCamera` below is the Tier A path and
    is fully adequate; this class exists for the Raspberry Pi build.

    Exposure and gain are pinned manually for the same reason auto-exposure
    is banned on the USB path: the loop hunts on every beacon blink.
    """

    def __init__(self, exposure_us: int = 4000, gain: float = 1.0,
                 width: int = 1456, height: int = 1088):
        from picamera2 import Picamera2                   # Pi only
        self.cam = Picamera2()
        cfg = self.cam.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"})
        self.cam.configure(cfg)
        self.cam.set_controls({
            "AeEnable": False,
            "AwbEnable": False,
            "ExposureTime": int(exposure_us),
            "AnalogueGain": float(gain),
        })
        self.cam.start()
        time.sleep(0.5)                                   # let controls settle

    def read(self) -> Optional[np.ndarray]:
        frame = self.cam.capture_array()
        if frame is None:
            return None
        # Luminance, then scale 8-bit up to the 12-bit range the pipeline
        # was built against, so every threshold carries over unchanged.
        gray = frame[..., :3].mean(axis=2)
        return (gray.astype(np.uint16) << 4)

    def release(self) -> None:
        self.cam.stop()


class UsbCamera:
    """A UVC camera with manual exposure, delivering grayscale frames."""

    def __init__(self, index: int = 0, width: int = 640, height: int = 480,
                 exposure: Optional[float] = None, gain: Optional[float] = None):
        import cv2
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if exposure is not None:
            # Auto-exposure hunts on every beacon blink; manual is mandatory.
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # V4L2: manual
            self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
        if gain is not None:
            self.cap.set(cv2.CAP_PROP_GAIN, gain)
        self._cv2 = cv2

    def read(self) -> Optional[np.ndarray]:
        ok, frame = self.cap.read()
        if not ok:
            return None
        gray = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2GRAY)
        # The pipeline was built against 12-bit frames; scale 8-bit up so
        # every threshold and normalisation carries over unchanged.
        return (gray.astype(np.uint16) << 4)

    def release(self) -> None:
        self.cap.release()
