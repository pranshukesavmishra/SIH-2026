// Minimal Arduino stand-in so rig_firmware_v3.ino compiles and runs on a PC.
// Time is simulated: every micros()/millis() call moves the clock a little,
// delay() jumps it, so loops that wait on time still finish.
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <string>
#include <deque>
#include <vector>
#include <algorithm>

using std::isnan;
using std::lround;

typedef uint8_t byte;
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT 0
#define F(s) (s)

template <class A, class B> auto max(A a, B b) -> decltype(a + b) { return a > b ? a : b; }
template <class A, class B> auto min(A a, B b) -> decltype(a + b) { return a < b ? a : b; }
template <class T, class L, class H> T constrain(T v, L lo, H hi) { return v < lo ? lo : (v > hi ? hi : v); }

namespace sim {
extern uint64_t nowUs;
struct PinEvent { int pin; int val; uint64_t t; };
extern std::vector<PinEvent> pinLog;
extern int pinMode_[32], pinVal[32];
}

inline unsigned long micros() { sim::nowUs += 20; return (unsigned long)sim::nowUs; }
inline unsigned long millis() { sim::nowUs += 20; return (unsigned long)(sim::nowUs / 1000); }
inline void delay(unsigned long ms) { sim::nowUs += (uint64_t)ms * 1000; }
inline void pinMode(int p, int m) { sim::pinMode_[p] = m; }
inline void digitalWrite(int p, int v) {
  if (sim::pinVal[p] != v) sim::pinLog.push_back({p, v, sim::nowUs});
  sim::pinVal[p] = v;
}

class FakeSerial {
 public:
  std::deque<char> in;
  std::string out;
  void begin(long) {}
  int available() { return (int)in.size(); }
  int read() { if (in.empty()) return -1; char c = in.front(); in.pop_front(); return c; }
  void feed(const std::string &s) { for (char c : s) in.push_back(c); }
  void print(const char *s) { out += s; }
  void print(char c) { out += c; }
  void print(long v) { out += std::to_string(v); }
  void print(int v) { out += std::to_string(v); }
  void print(double v, int d = 2) { char b[48]; snprintf(b, sizeof b, "%.*f", d, v); out += b; }
  template <class T> void println(T v) { print(v); out += "\r\n"; }
  void println() { out += "\r\n"; }
};
extern FakeSerial Serial;
