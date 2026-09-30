// Runs the real rig_firmware_v3.ino on a PC with fake hardware and checks
// what it does. Build and run:  bash tools/mk3/fwtest/run.sh
// Each scenario runs in its own process, which is a clean "power-on".
#include "Arduino.h"
#include "Wire.h"
#include "AccelStepper.h"
#include <sys/wait.h>
#include <unistd.h>
#include <functional>

namespace sim {
uint64_t nowUs = 0;
std::vector<PinEvent> pinLog;
int pinMode_[32], pinVal[32];
}
FakeSerial Serial;
FakeWire Wire;

// Arduino IDE writes these prototypes for you; g++ needs them spelled out.
void handleLine(char *line);
void serviceLaser();
void zeroHere();
void reportStatus();
void selftest();
float commandedPan();
float commandedTilt();

#include "../../rig/rig_firmware_v3.ino"

// ---- fake encoders: each sensor reads the OUTPUT shaft angle ------------
static int   encOffset[2] = {0, 0};     // raw counts at power-on
static float encSlipDeg[2] = {0, 0};    // real OUTPUT angle minus commanded (skipped steps), degrees
static int   encSign[2] = {1, 1};       // -1 = sensor mounted the other way round
static int rawFor(int ch) {
  const AccelStepper &m = ch == 0 ? panStepper : tiltStepper;
  float gear = ch == 0 ? PAN_GEAR_RATIO : TILT_GEAR_RATIO;
  float ratio = ch == 0 ? PAN_ENC_RATIO : TILT_ENC_RATIO;      // pan sensor sits on the motor shaft
  double deg = (m.currentPosition() / (STEPS_PER_DEG * gear) + encSlipDeg[ch]) * ratio;
  long c = encOffset[ch] + encSign[ch] * lround(deg * 4096.0 / 360.0);
  return (int)(((c % 4096) + 4096) % 4096);
}

// ---- helpers ------------------------------------------------------------
static int fails = 0, checks = 0;
static void check(bool ok, const std::string &what) {
  checks++;
  if (!ok) fails++;
  printf("  %s %s\n", ok ? "ok  " : "FAIL", what.c_str());
}
static std::string lastLine() {
  std::string o = Serial.out;
  while (!o.empty() && (o.back() == '\n' || o.back() == '\r')) o.pop_back();
  size_t i = o.rfind('\n');
  return i == std::string::npos ? o : o.substr(i + 1);
}
static void send(const std::string &cmd) { Serial.feed(cmd + "\n"); loop(); }
static void settle(long maxLoops = 2000000) {
  loop();
  for (long i = 0; i < maxLoops && moving(); i++) loop();
}
static bool status(long &p, long &t, char &src, int &mv) {
  send("?");
  return sscanf(lastLine().c_str(), "S %ld %ld %c %d", &p, &t, &src, &mv) == 4;
}
static void boot(bool panSensor, bool tiltSensor) {
  Wire.sensorOn[0] = panSensor; Wire.sensorOn[1] = tiltSensor; Wire.rawFor = rawFor;
  setup();
}

// ---- scenarios ------------------------------------------------------------
static void s_boot_plain() {
  boot(false, false);
  check(Serial.out.rfind("# ZeroDrift Mk2 ready, encoders=no, belts=4:4", 0) == 0,
        "banner starts with '# ZeroDrift Mk2' (the Live page looks for this): " + lastLine());
  check(sim::pinMode_[ENABLE_PIN] == OUTPUT && sim::pinVal[ENABLE_PIN] == LOW, "EN pin D" + std::to_string(ENABLE_PIN) + " is an output and LOW (drivers on)");
  check(sim::pinVal[LASER_PIN] == LOW, "laser starts OFF");
  check(sim::pinVal[VIBRATION_PIN] == LOW, "vibration motor starts OFF");
  long p, t; char c; int m;
  bool got = status(p, t, c, m);
  check(got && p == 0 && t == 0 && c == 'C' && m == 0, "'?' at rest -> S 0 0 C 0: " + lastLine());
  check(panStepper.maxSpeed <= 2000 && tiltStepper.maxSpeed <= 2000, "speed capped at 2000 steps/s per axis");
}

static void s_limits() {
  boot(false, false);
  long panMax = lround(150 * 3200 / 360.0 * 4), tiltMax = lround(40 * 3200 / 360.0 * 4);
  check(PAN_MAX_STEPS == panMax && TILT_MAX_STEPS == tiltMax,
        "limits = pan 150 deg (" + std::to_string(PAN_MAX_STEPS) + " steps), tilt 40 deg (" + std::to_string(TILT_MAX_STEPS) + " steps)");
  send("P999999 T-999999"); settle();
  long p, t; char c; int m;
  status(p, t, c, m);
  check(p == PAN_MAX_STEPS && t == -TILT_MAX_STEPS, "huge move is clamped to the limits: " + lastLine());
  send("P-999999 T999999"); settle(); status(p, t, c, m);
  check(p == -PAN_MAX_STEPS && t == TILT_MAX_STEPS, "clamped the other way too: " + lastLine());
  send("T500"); settle(); status(p, t, c, m);
  check(p == -PAN_MAX_STEPS && t == 500, "'T500' moves tilt only: " + lastLine());
  send("P1234"); settle(); status(p, t, c, m);
  check(p == 1234 && t == 500, "'P1234' with no T leaves tilt alone: " + lastLine());
  send("C"); settle(); status(p, t, c, m);
  check(p == 0 && t == 0, "'C' goes back to 0,0: " + lastLine());
  send("P3556 T-711"); settle(); status(p, t, c, m);
  check(p == 3556 && t == -711, "100 deg pan = 3556 steps, -20 deg tilt = -711 steps (4:1 belts)");
}

static void s_moving() {
  boot(false, false);
  send("P2000 T300");
  for (int i = 0; i < 50; i++) loop();
  long p, t; char c; int m;
  status(p, t, c, m);
  check(c == 'C' && m == 1 && p > 0 && p < 2000, "while moving: commanded position, moving=1: " + lastLine());
  long i2cBefore = Wire.transactions;
  send("?");
  check(Wire.transactions == i2cBefore, "no I2C traffic while motors move (keeps steps smooth)");
}

static void s_encoders_wrap() {
  encOffset[0] = 4000; encOffset[1] = 60;            // magnets glued at random angles
  boot(true, true);
  check(lastLine() == "# ZeroDrift Mk2 ready, encoders=yes, belts=4:4", "banner reports both encoders: " + lastLine());
  long p, t; char c; int m;
  status(p, t, c, m);
  check(c == 'E' && labs(p) <= 4 && labs(t) <= 4, "power-on reads 0,0 from the sensors: " + lastLine());
  // +150 then -150: a 300-degree swing between two reads, through the sensor's seam
  send("P" + std::to_string(PAN_MAX_STEPS)); settle(); status(p, t, c, m);
  check(c == 'E' && labs(p - PAN_MAX_STEPS) <= 4, "+150 deg measured right: " + lastLine());
  send("P" + std::to_string(-PAN_MAX_STEPS) + " T-1400"); settle(); status(p, t, c, m);
  check(c == 'E' && labs(p + PAN_MAX_STEPS) <= 4 && labs(t + 1400) <= 4, "300 deg swing to -150 deg measured right (old code was 360 deg off): " + lastLine());
  for (int k = 0; k < 40; k++) {                     // random-ish targets
    long tp = ((k * 7919L) % (2 * PAN_MAX_STEPS)) - PAN_MAX_STEPS, tt = ((k * 104729L) % (2 * TILT_MAX_STEPS)) - TILT_MAX_STEPS;
    send("P" + std::to_string(tp) + " T" + std::to_string(tt)); settle(); status(p, t, c, m);
    if (labs(p - tp) > 4 || labs(t - tt) > 4) { check(false, "random target " + std::to_string(k) + ": " + lastLine()); return; }
  }
  check(true, "40 random moves across the full range all measured within 4 steps (0.11 deg)");
  check(PAN_ENC_RATIO == 4.0 && TILT_ENC_RATIO == 1.0, "pan sensor reads the motor (4 turns per pan turn), tilt sensor reads the pulley");
  // skipped steps: pan lost 3 degrees, tilt lost 2
  send("P0 T0"); settle();
  encSlipDeg[0] = -3.0; encSlipDeg[1] = 2.0;
  status(p, t, c, m);
  check(labs(p - lround(-3.0 * STEPS_PER_DEG * 4)) <= 4 && labs(t - lround(2.0 * STEPS_PER_DEG * 4)) <= 4,
        "skipped steps show up in the reply (pan -3 deg, tilt +2 deg): " + lastLine());
  encSlipDeg[0] = encSlipDeg[1] = 0;
  send("P500 T100"); settle(); send("Z"); status(p, t, c, m);
  check(labs(p) <= 4 && labs(t) <= 4, "'Z' makes here the new 0,0: " + lastLine());
  send("P-800"); settle(); status(p, t, c, m);
  check(labs(p + 800) <= 4, "moves after Z are measured from the new datum: " + lastLine());
}

static void s_pan_only() {
  encOffset[0] = 10;
  boot(true, false);
  check(lastLine() == "# ZeroDrift Mk2 ready, encoders=pan, belts=4:4", "pan sensor only: " + lastLine());
  long p, t; char c; int m;
  send("P-2000 T333"); settle(); status(p, t, c, m);
  check(c == 'E' && labs(p + 2000) <= 4 && t == 333, "pan measured, tilt commanded: " + lastLine());
}

static double laserHzMeasured(uint64_t fromUs) {
  std::vector<uint64_t> rise;
  for (auto &e : sim::pinLog) if (e.pin == LASER_PIN && e.val == HIGH && e.t > fromUs) rise.push_back(e.t);
  if (rise.size() < 3) return 0;
  return (rise.size() - 1) / ((rise.back() - rise.front()) / 1e6);
}

static void s_laser() {
  boot(false, false);
  send("L1");
  check(sim::pinVal[LASER_PIN] == HIGH, "'L1' laser steady ON");
  send("L0");
  check(sim::pinVal[LASER_PIN] == LOW, "'L0' laser OFF");
  uint64_t t0 = sim::nowUs;
  send("L7.0");
  while (sim::nowUs - t0 < 3000000) loop();         // 3 s of loop()
  double hz = laserHzMeasured(t0);
  char b[80]; snprintf(b, sizeof b, "'L7.0' blinks at %.3f Hz (want 7.000 +/- 0.05)", hz);
  check(fabs(hz - 7.0) < 0.05, b);
  t0 = sim::nowUs;
  send("L4.5");
  while (sim::nowUs - t0 < 3000000) loop();
  hz = laserHzMeasured(t0);
  snprintf(b, sizeof b, "'L4.5' blinks at %.3f Hz", hz);
  check(fabs(hz - 4.5) < 0.05, b);
  send("L0");
  size_t n = sim::pinLog.size();
  for (int i = 0; i < 20000; i++) loop();
  check(sim::pinVal[LASER_PIN] == LOW && sim::pinLog.size() == n, "'L0' stops the blinking and stays off");
  send("L0.1");
  check(sim::pinVal[LASER_PIN] == LOW, "'L0.1' (too slow) is ignored");
  send("V1"); check(sim::pinVal[VIBRATION_PIN] == HIGH, "'V1' vibration on");
  send("V0"); check(sim::pinVal[VIBRATION_PIN] == LOW, "'V0' vibration off");
}

static void s_garbage() {
  boot(false, false);
  send("hello");
  send("P");
  send("Pabc Txyz");
  send("PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP");
  send("");
  send("\r");
  long p, t; char c; int m;
  settle();
  bool got = status(p, t, c, m);
  check(got && p == 0 && t == 0, "junk and over-long lines: no crash, no move: " + lastLine());
  Serial.feed("P100 T");  loop();                   // command split across two USB packets
  Serial.feed("50\r\n"); settle();
  status(p, t, c, m);
  check(p == 100 && t == 50, "a command split across two reads still works (with CRLF): " + lastLine());
}

static void s_selftest(int sign) {
  encOffset[0] = 2048; encSign[0] = sign;
  boot(true, true);
  Serial.out.clear();
  send("!");
  printf("%s", Serial.out.c_str());
  check(Serial.out.find("# selftest done") != std::string::npos, "self-test runs to the end");
  if (sign > 0)
    check(Serial.out.find("# encoder saw 10.0") != std::string::npos || Serial.out.find("# encoder saw 9.9") != std::string::npos,
          "self-test: encoder sees the +10 deg move");
  else
    check(Serial.out.find("direction reversed") != std::string::npos, "self-test spots a sensor mounted the other way round");
  check(panStepper.currentPosition() == 0, "self-test returns pan to where it started");
}

int main() {
  std::vector<std::pair<const char *, std::function<void()>>> S = {
      {"power-on", s_boot_plain}, {"limits and moves", s_limits}, {"status while moving", s_moving},
      {"encoders, full range", s_encoders_wrap}, {"pan encoder only", s_pan_only}, {"laser and vibration", s_laser},
      {"bad input", s_garbage}, {"self-test", [] { s_selftest(1); }}, {"self-test, reversed sensor", [] { s_selftest(-1); }}};
  int total = 0, bad = 0;
  for (auto &s : S) {
    printf("\n[%s]\n", s.first);
    fflush(stdout);
    int fd[2];
    if (pipe(fd) != 0) return 2;
    pid_t pid = fork();
    if (pid == 0) {
      close(fd[0]);
      s.second();
      fflush(stdout);
      int r[2] = {checks, fails};
      if (write(fd[1], r, sizeof r) != sizeof r) _exit(3);
      _exit(0);
    }
    close(fd[1]);
    int r[2] = {0, 1}, st = 0;
    if (read(fd[0], r, sizeof r) != sizeof r) printf("  FAIL scenario crashed\n");
    waitpid(pid, &st, 0);
    total += r[0]; bad += r[1];
  }
  printf("\n%d checks, %d failed\n", total, bad);
  return bad ? 1 : 0;
}
