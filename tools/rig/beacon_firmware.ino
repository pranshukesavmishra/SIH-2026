// ZeroDrift Beacon Unit firmware — DRAFT, not yet bench-tested.
// Verify wiring and measured blink rate (phone slow-mo or a scope) before
// calling the frequency "precise" in front of a judge.
//
// Companion to rig_firmware_v2.ino (the tracker) — this is the target it
// tracks. Runs standalone on its own Nano, its own battery; no wired
// connection to the tracker at demo time. Serial is for bench setup only.
//
// Serial protocol @ 115200 baud, newline-terminated commands:
//   F<float>   set blink frequency in Hz, e.g. F4.0 (boot default: 4.0)
//   B<0-255>   set brightness (PWM duty cycle at the LED's ON phase)
//   M0         steady-on (no blink) — for A/B comparison against the
//              separate decoy unit
//   M1         blinking mode (boot default)
//
// Timing note: the blink is referenced against micros(), not delay() or a
// counted loop — delay()-based timing drifts under any interrupt load
// (Serial RX included), and the entire point of building this instead of
// using a phone app is that the frequency should actually be the number
// printed on it.

const int LED_PIN = 9;   // PWM-capable pin, drives the transistor base

float blinkHz = 4.0;
uint8_t brightness = 255;
bool blinkMode = true;

unsigned long halfPeriodUs = 125000;   // recomputed whenever blinkHz changes
unsigned long lastToggleUs = 0;
bool ledOn = false;

void recomputePeriod() {
  if (blinkHz <= 0.01) blinkHz = 0.01;   // guard against div-by-zero from bad input
  halfPeriodUs = (unsigned long)(500000.0 / blinkHz);   // half of 1e6/Hz
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  recomputePeriod();
  lastToggleUs = micros();
}

void loop() {
  static char buf[24];
  static int n = 0;

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || n >= 23) {
      buf[n] = 0;
      n = 0;
      handleLine(buf);
    } else {
      buf[n++] = c;
    }
  }

  if (!blinkMode) {
    analogWrite(LED_PIN, brightness);   // steady-on at the set brightness
    return;
  }

  unsigned long now = micros();
  if (now - lastToggleUs >= halfPeriodUs) {
    lastToggleUs = now;
    ledOn = !ledOn;
    analogWrite(LED_PIN, ledOn ? brightness : 0);
  }
}

void handleLine(const char *line) {
  if (line[0] == 'F') {
    float hz = atof(line + 1);
    if (hz > 0) {
      blinkHz = hz;
      recomputePeriod();
    }
  } else if (line[0] == 'B') {
    int v = atoi(line + 1);
    brightness = (uint8_t)constrain(v, 0, 255);
  } else if (line[0] == 'M') {
    blinkMode = (line[1] != '0');
    if (!blinkMode) analogWrite(LED_PIN, brightness);
  }
}
