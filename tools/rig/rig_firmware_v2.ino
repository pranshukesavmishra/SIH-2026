/*
 * ZeroDrift Mini-Rig Mk2 — tracker firmware.
 * Arduino Nano/Uno + 2x TMC2209 + 2x NEMA17 (dual-shaft) + 2x AS5600
 *                   (via TCA9548A) + laser + vibration injector.
 *
 * Libraries (Arduino Library Manager): AccelStepper, Wire.
 * (Servo.h is only needed if you set FINE_STAGE to 1 — see below.)
 *
 * NO SERVOS in the default build. The Mk1 rig stripped two of them, and a
 * hobby servo's backlash is larger than the pointing error this rig is
 * supposed to measure. Resolution now comes from microstepping and an
 * optional belt reduction, both of which have no gear teeth to shear.
 *
 * ---------------------------------------------------------------------
 * PROTOCOL v3 — see docs/HARDWARE_PROTOCOL.md. Read that before editing.
 *
 * THE WIRE IS DEGREES. Always. The host never sends motor steps, never
 * needs to know the microstepping setting, and never needs recompiling
 * when the mechanics change. This firmware owns every unit conversion.
 * Earlier drafts took steps on the wire while the host sent degrees,
 * which moved the rig by a silent factor of ~4.4 and is why this file
 * was rewritten.
 *
 *   P <pan> <tilt>   coarse absolute target, degrees, float
 *   p <pan> <tilt>   fine-stage offset, degrees — only if FINE_STAGE=1
 *   L0               laser off
 *   L1               laser on, steady
 *   L<hz>            laser MODULATED at <hz>, e.g. L7.0
 *
 *   The laser is modulated so the camera can tell the laser's own dot
 *   apart from the beacon by frequency, exactly the way the beacon is
 *   told apart from the decoy. Beacon 4 Hz, laser 7 Hz: two sources,
 *   two signatures, one image. That is what lets the fine loop close on
 *   the dot-to-beacon pixel error and cancel parallax outright, instead
 *   of modelling it. See docs/TERMINAL_MK3.md section 0.
 *   V0 | V1          vibration injector off / on
 *   C                centre both stages and re-zero the encoder datum
 *   Z                zero: call the current position 0,0
 *   ?                status query -> "S <pan> <tilt> <src> <moving>"
 *   !                self-test (see selftest(), for bring-up)
 *
 * Every command is newline-terminated. Replies are newline-terminated.
 * ---------------------------------------------------------------------
 *
 * Encoder policy, stated plainly: the AS5600s are read only while both
 * steppers are at rest. An I2C transaction takes roughly a millisecond,
 * and at speed that is long enough to disturb AccelStepper's timing and
 * cause the very skipped step the encoders exist to catch. So during a
 * slew the status reply carries the commanded position (src=C), and on
 * arrival it carries the measured one (src=E). That is exactly the check
 * that matters -- "did the motor actually get where it was told" -- and
 * it costs nothing in step fidelity.
 */

#include <AccelStepper.h>
#include <Wire.h>
#if FINE_STAGE
#include <Servo.h>
#endif

// ---- Pin map — verify against your actual wiring before first power-on ----
const int PAN_STEP_PIN  = 2,  PAN_DIR_PIN  = 3;
const int TILT_STEP_PIN = 4,  TILT_DIR_PIN = 5;
const int FINE_PAN_PIN  = 9,  FINE_TILT_PIN = 10;
const int LASER_PIN     = 7;
const int VIBRATION_PIN = 8;
// A4 = SDA, A5 = SCL on a Nano/Uno — wired to the TCA9548A.

// ---- Fine stage: OFF by default. See the header. ------------------------
#define FINE_STAGE 0

// ---- Mechanics ----------------------------------------------------------
// 200 full steps/rev (1.8 deg/step) x 32 microsteps = 6400 steps/rev.
// On a TMC2209 in standalone (non-UART) mode, 1/32 is MS1=LOW, MS2=LOW...
// CHECK YOUR BOARD'S SILKSCREEN: the MS1/MS2 truth table differs between
// vendors and getting it wrong scales every angle you command.
// Whatever you set the jumpers to, set MICROSTEPS to match and reflash.
const float STEPS_PER_REV = 200.0;
const float MICROSTEPS    = 32.0;
const float STEPS_PER_DEG = (STEPS_PER_REV * MICROSTEPS) / 360.0;   // 17.778

// Belt reduction, motor turns per output turn. 1.0 = direct drive.
// With a GT2 20T pulley on the motor and 60T on the output stage, set 3.0:
// it divides the commanded step size AND the motor's own inherent
// positioning error by three, which is why it is worth the build effort.
// This lives here, not on the host — the host is not allowed to know about
// mechanics. Change the pulleys, change this number, reflash, done.
const float PAN_GEAR_RATIO  = 1.0;
const float TILT_GEAR_RATIO = 1.0;

// ---- Soft limits, degrees. These protect the wiring loom, not the motor. --
const float PAN_MIN_DEG  = -90.0, PAN_MAX_DEG  =  90.0;
const float TILT_MIN_DEG = -30.0, TILT_MAX_DEG =  45.0;
#if FINE_STAGE
const int   FINE_CENTRE_US = 90;           // servo degrees at mechanical centre
const float FINE_RANGE_DEG = 30.0;         // +/- offset the fine stage may take
#endif

// ---- I2C addresses ------------------------------------------------------
const uint8_t TCA_ADDR      = 0x70;
const uint8_t AS5600_ADDR   = 0x36;
const uint8_t AS5600_RAWANG = 0x0C;        // 12-bit raw angle, high byte first
const uint8_t PAN_CHANNEL   = 0;
const uint8_t TILT_CHANNEL  = 1;

AccelStepper panStepper(AccelStepper::DRIVER, PAN_STEP_PIN, PAN_DIR_PIN);
AccelStepper tiltStepper(AccelStepper::DRIVER, TILT_STEP_PIN, TILT_DIR_PIN);
#if FINE_STAGE
Servo finePan, fineTilt;
#endif

// Laser modulation. Referenced against micros(), never delay() — the
// frequency has to actually be the number we claim, for the same reason
// the beacon's does.
float         laserHz          = 0.0;      // 0 = not modulating
bool          laserSteady      = false;
bool          laserPhaseOn     = false;
unsigned long laserHalfPeriodUs = 0;
unsigned long laserLastToggleUs = 0;

bool  encodersPresent = false;
long  panTurns = 0,  tiltTurns = 0;        // wrap accumulator, in whole turns
int   panLastRaw = 0, tiltLastRaw = 0;
float panZeroDeg = 0.0, tiltZeroDeg = 0.0; // datum set by C / Z

// ------------------------------------------------------------------------
void tcaSelect(uint8_t channel) {
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

// Raw 0..4095 from the AS5600 on the given mux channel; -1 if it did not answer.
int readRaw(uint8_t channel) {
  tcaSelect(channel);
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(AS5600_RAWANG);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom((uint8_t)AS5600_ADDR, (uint8_t)2) != 2) return -1;
  int hi = Wire.read(), lo = Wire.read();
  return ((hi << 8) | lo) & 0x0FFF;
}

// Continuous angle in degrees, unwrapped across the 0/4095 seam so a pan
// sweep through the encoder's zero does not read as a 360-degree jump.
float readAngleDeg(uint8_t channel, int &lastRaw, long &turns) {
  int raw = readRaw(channel);
  if (raw < 0) return NAN;
  int delta = raw - lastRaw;
  if (delta >  2048) turns--;              // wrapped backwards through zero
  if (delta < -2048) turns++;              // wrapped forwards through zero
  lastRaw = raw;
  return (turns * 4096.0 + raw) * (360.0 / 4096.0);
}

float clampf(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

bool moving() {
  return panStepper.distanceToGo() != 0 || tiltStepper.distanceToGo() != 0;
}

// ------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);                   // fast mode: shortens the stall

  // Conservative speeds. A NEMA17 on an A4988 at 12V will happily be
  // commanded faster than it can actually accelerate a loaded gimbal, and
  // a skipped step is worse than a slow slew.
  // At 1/32 microstepping a degree costs 17.8 steps, so the step RATE has
  // to rise to keep the same slew speed in degrees. 2400 steps/s = 135 deg/s
  // direct-drive, which is brisk but well inside what a NEMA17 will hold.
  // An Arduino Nano tops out around 4000 steps/s across both axes; if you
  // add the belt reduction, raise these or accept a 3x slower slew.
  panStepper.setMaxSpeed(2400);
  panStepper.setAcceleration(1200);
  tiltStepper.setMaxSpeed(2400);
  tiltStepper.setAcceleration(1200);

#if FINE_STAGE
  finePan.attach(FINE_PAN_PIN);
  fineTilt.attach(FINE_TILT_PIN);
  finePan.write(FINE_CENTRE_US);
  fineTilt.write(FINE_CENTRE_US);
#endif

  pinMode(LASER_PIN, OUTPUT);     digitalWrite(LASER_PIN, LOW);
  pinMode(VIBRATION_PIN, OUTPUT); digitalWrite(VIBRATION_PIN, LOW);

  // Probe the encoders once. If they are absent the rig still runs fully
  // open-loop and says so in every status reply, rather than pretending.
  panLastRaw  = readRaw(PAN_CHANNEL);
  tiltLastRaw = readRaw(TILT_CHANNEL);
  encodersPresent = (panLastRaw >= 0 && tiltLastRaw >= 0);
  if (panLastRaw  < 0) panLastRaw  = 0;
  if (tiltLastRaw < 0) tiltLastRaw = 0;

  Serial.print(F("# ZeroDrift Mk2 ready, encoders="));
  Serial.println(encodersPresent ? F("yes") : F("no"));
}

void loop() {
  static char buf[32];
  static int  n = 0;

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n' || n >= 31) { buf[n] = 0; n = 0; handleLine(buf); }
    else buf[n++] = c;
  }

  panStepper.run();
  tiltStepper.run();
  serviceLaser();
}

void serviceLaser() {
  if (laserHz <= 0.0) return;              // off or steady: nothing to do
  unsigned long now = micros();
  if (now - laserLastToggleUs >= laserHalfPeriodUs) {
    laserLastToggleUs = now;
    laserPhaseOn = !laserPhaseOn;
    digitalWrite(LASER_PIN, laserPhaseOn ? HIGH : LOW);
  }
}

// ------------------------------------------------------------------------
void handleLine(char *line) {
  switch (line[0]) {

    case 'P': {                            // coarse absolute, degrees
      float pan, tilt;
      int got = sscanf(line + 1, "%f %f", &pan, &tilt);
      if (got >= 1) {
        pan = clampf(pan, PAN_MIN_DEG, PAN_MAX_DEG);
        panStepper.moveTo((long)lround(pan * STEPS_PER_DEG * PAN_GEAR_RATIO));
      }
      if (got == 2) {
        tilt = clampf(tilt, TILT_MIN_DEG, TILT_MAX_DEG);
        tiltStepper.moveTo((long)lround(tilt * STEPS_PER_DEG * TILT_GEAR_RATIO));
      }
      break;
    }

    case 'p': {                            // fine offset, degrees
#if FINE_STAGE
      float pan, tilt;
      int got = sscanf(line + 1, "%f %f", &pan, &tilt);
      if (got >= 1)
        finePan.write(FINE_CENTRE_US + (int)lround(
            clampf(pan, -FINE_RANGE_DEG, FINE_RANGE_DEG)));
      if (got == 2)
        fineTilt.write(FINE_CENTRE_US + (int)lround(
            clampf(tilt, -FINE_RANGE_DEG, FINE_RANGE_DEG)));
#endif
      break;                               // no fine stage: accept and ignore
    }

    case 'L': {
      // "L0" off, "L1" steady on, anything else a modulation frequency.
      if (line[1] == '0' && line[2] == 0) {
        laserHz = 0.0; laserSteady = false;
        digitalWrite(LASER_PIN, LOW);
      } else if (line[1] == '1' && line[2] == 0) {
        laserHz = 0.0; laserSteady = true;
        digitalWrite(LASER_PIN, HIGH);
      } else {
        float hz = atof(line + 1);
        if (hz > 0.2) {                    // below this the dot reads as steady
          laserHz = hz;
          laserSteady = false;
          laserHalfPeriodUs = (unsigned long)(500000.0 / hz);
          laserLastToggleUs = micros();
          laserPhaseOn = true;
          digitalWrite(LASER_PIN, HIGH);
        }
      }
      break;
    }
    case 'V': digitalWrite(VIBRATION_PIN, line[1] == '1' ? HIGH : LOW); break;

    case 'C':                              // centre everything, re-datum
      panStepper.moveTo(0);
      tiltStepper.moveTo(0);
#if FINE_STAGE
      finePan.write(FINE_CENTRE_US);
      fineTilt.write(FINE_CENTRE_US);
#endif
      break;

    case 'Z': zeroHere(); break;
    case '?': reportStatus(); break;
    case '!': selftest(); break;

    default: break;                        // unknown: stay silent, keep moving
  }
}

void zeroHere() {
  panStepper.setCurrentPosition(0);
  tiltStepper.setCurrentPosition(0);
  if (encodersPresent) {
    panTurns = tiltTurns = 0;
    panLastRaw  = max(0, readRaw(PAN_CHANNEL));
    tiltLastRaw = max(0, readRaw(TILT_CHANNEL));
    panZeroDeg  = panLastRaw  * (360.0 / 4096.0);
    tiltZeroDeg = tiltLastRaw * (360.0 / 4096.0);
  }
  Serial.println(F("# zeroed"));
}

void reportStatus() {
  float pan, tilt;
  char src;

  if (encodersPresent && !moving()) {
    float p = readAngleDeg(PAN_CHANNEL,  panLastRaw,  panTurns)  - panZeroDeg;
    float t = readAngleDeg(TILT_CHANNEL, tiltLastRaw, tiltTurns) - tiltZeroDeg;
    if (isnan(p) || isnan(t)) { src = 'C'; pan = commandedPan(); tilt = commandedTilt(); }
    else                      { src = 'E'; pan = p;              tilt = t; }
  } else {
    src = 'C';
    pan = commandedPan();
    tilt = commandedTilt();
  }

  Serial.print(F("S "));
  Serial.print(pan, 3);  Serial.print(' ');
  Serial.print(tilt, 3); Serial.print(' ');
  Serial.print(src);     Serial.print(' ');
  Serial.println(moving() ? '1' : '0');
}

float commandedPan()  { return panStepper.currentPosition()  / (STEPS_PER_DEG * PAN_GEAR_RATIO); }
float commandedTilt() { return tiltStepper.currentPosition() / (STEPS_PER_DEG * TILT_GEAR_RATIO); }

// Bring-up helper: exercises every actuator once, in an order where a
// failure tells you which subsystem is at fault. Run it with '!' the first
// time you power the rig, before running any of the tracking software.
void selftest() {
  Serial.println(F("# selftest: laser steady, then 7 Hz for 2 s"));
  laserHz = 0.0;
  digitalWrite(LASER_PIN, HIGH); delay(400); digitalWrite(LASER_PIN, LOW);
  handleLine((char *)"L7.0");
  unsigned long until = millis() + 2000;
  while (millis() < until) serviceLaser();
  handleLine((char *)"L0");

#if FINE_STAGE
  Serial.println(F("# selftest: fine stage"));
  finePan.write(FINE_CENTRE_US - 20); delay(400);
  finePan.write(FINE_CENTRE_US + 20); delay(400);
  finePan.write(FINE_CENTRE_US);      delay(300);
  fineTilt.write(FINE_CENTRE_US - 15); delay(400);
  fineTilt.write(FINE_CENTRE_US + 15); delay(400);
  fineTilt.write(FINE_CENTRE_US);      delay(300);
#endif

  Serial.println(F("# selftest: coarse pan +10 deg and back"));
  long before = panStepper.currentPosition();
  panStepper.moveTo(before + lround(10.0 * STEPS_PER_DEG));
  while (panStepper.distanceToGo()) panStepper.run();
  delay(200);
  if (encodersPresent) {
    float m = readAngleDeg(PAN_CHANNEL, panLastRaw, panTurns) - panZeroDeg;
    Serial.print(F("# encoder reads ")); Serial.print(m, 2);
    Serial.println(F(" deg (expect ~10.00 from the datum)"));
  } else {
    Serial.println(F("# no encoders: cannot verify the move happened"));
  }
  panStepper.moveTo(before);
  while (panStepper.distanceToGo()) panStepper.run();

  Serial.println(F("# selftest: vibration 600 ms"));
  digitalWrite(VIBRATION_PIN, HIGH); delay(600); digitalWrite(VIBRATION_PIN, LOW);
  Serial.println(F("# selftest done"));
}
