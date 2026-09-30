// I2C stand-in: a TCA9548A at 0x70 and one AS5600 (0x36) on each enabled
// channel. The test decides what angle each sensor reads through rawFor().
#pragma once
#include <cstdint>

class FakeWire {
 public:
  bool muxPresent = true;
  bool sensorOn[8] = {false};
  int (*rawFor)(int channel) = nullptr;
  int channel = -1, addr = 0, reg = -1;
  int pending[2] = {0, 0}, left = 0;
  long transactions = 0;

  void begin() {}
  void setClock(long) {}
  void beginTransmission(int a) { addr = a; reg = -1; }
  void write(int v) {
    if (addr == 0x70) { channel = -1; for (int i = 0; i < 8; i++) if (v == (1 << i)) channel = i; }
    else reg = v;
  }
  int endTransmission(bool = true) {
    transactions++;
    if (addr == 0x70) return muxPresent ? 0 : 2;
    if (addr == 0x36) return (muxPresent && channel >= 0 && sensorOn[channel]) ? 0 : 2;
    return 2;
  }
  int requestFrom(uint8_t a, uint8_t n) {
    if (a != 0x36 || !muxPresent || channel < 0 || !sensorOn[channel] || reg != 0x0C) return 0;
    int raw = rawFor ? rawFor(channel) : 0;
    pending[0] = (raw >> 8) & 0x0F; pending[1] = raw & 0xFF; left = n;
    return n;
  }
  int read() { if (left <= 0) return -1; return pending[2 - left--]; }
};
extern FakeWire Wire;
