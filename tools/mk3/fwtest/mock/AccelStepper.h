// AccelStepper stand-in: one step per run() call toward the target, and it
// logs the fastest speed it was asked for so the test can check the limits.
#pragma once

class AccelStepper {
 public:
  enum { DRIVER = 1 };
  long pos = 0, target = 0;
  float maxSpeed = 1, accel = 1;
  long steps = 0;
  AccelStepper(int, int, int) {}
  void setMaxSpeed(float s) { maxSpeed = s; }
  void setAcceleration(float a) { accel = a; }
  void moveTo(long t) { target = t; }
  long distanceToGo() const { return target - pos; }
  long currentPosition() const { return pos; }
  void setCurrentPosition(long p) { pos = target = p; }
  bool run() {
    if (pos == target) return false;
    pos += pos < target ? 1 : -1; steps++;
    return true;
  }
};
