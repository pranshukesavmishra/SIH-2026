// Tower build (DRIVE_DIRECT=1): the same firmware, compiled for the direct-drive tower.
// Built and run by run.sh with -DDRIVE_DIRECT=1.
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


#ifndef DRIVE_DIRECT
#error "build this test with -DDRIVE_DIRECT=1"
#endif
static int fails = 0, checks = 0;
static void check(bool ok, const std::string &what) { checks++; if (!ok) fails++; printf("  %s %s\n", ok ? "ok  " : "FAIL", what.c_str()); }
static std::string lastLine() {
  std::string o = Serial.out;
  while (!o.empty() && (o.back() == '\n' || o.back() == '\r')) o.pop_back();
  size_t i = o.rfind('\n');
  return i == std::string::npos ? o : o.substr(i + 1);
}
static void send(const std::string &cmd) { Serial.feed(cmd + "\n"); loop(); }
static void settle(long maxLoops = 2000000) { loop(); for (long i = 0; i < maxLoops && moving(); i++) loop(); }
static bool status(long &p, long &t, char &src, int &mv) { send("?"); return sscanf(lastLine().c_str(), "S %ld %ld %c %d", &p, &t, &src, &mv) == 4; }

int main() {
  Wire.sensorOn[0] = false; Wire.sensorOn[1] = false; Wire.rawFor = nullptr;
  setup();
  check(Serial.out.rfind("# ZeroDrift Mk2 ready, encoders=no, belts=1:1", 0) == 0, "tower banner (Live page still sees Mk2): " + lastLine());
  check(PAN_GEAR_RATIO == 1.0 && TILT_GEAR_RATIO == 1.0, "direct drive: ratio 1:1 on both axes");
  check(PAN_MAX_STEPS == lround(90 * 3200 / 360.0) && TILT_MAX_STEPS == lround(30 * 3200 / 360.0),
        "limits = pan 90 deg (" + std::to_string(PAN_MAX_STEPS) + " steps), tilt 30 deg (" + std::to_string(TILT_MAX_STEPS) + " steps)");
  check(panStepper.maxSpeed <= 1200 && tiltStepper.maxSpeed <= 1200, "speed capped at 1200 steps/s per axis");
  long p, t; char c; int m;
  send("P800 T-267"); settle(); status(p, t, c, m);
  check(p == 800 && t == -267 && c == 'C', "a 90 deg pan and 30 deg tilt is 800 and 267 steps: " + lastLine());
  send("P999999 T999999"); settle(); status(p, t, c, m);
  check(p == PAN_MAX_STEPS && t == TILT_MAX_STEPS, "huge move clamps to 90 / 30 deg: " + lastLine());
  send("C"); settle(); status(p, t, c, m);
  check(p == 0 && t == 0, "'C' returns to 0,0: " + lastLine());
  send("L"); 
  printf("%d checks, %d failed\n", checks, fails);
  return fails ? 1 : 0;
}
