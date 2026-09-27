// Pin test: blinks the Nano's own "L" LED and every pin D2-D12 together, once a second,
// and prints which cycle it is on. If the external LED blinks with this sketch, the
// upload works and the wire is on a digital pin. See docs/LOCAL_HANDOFF.md.
void setup() {
  for (int p = 2; p <= 13; p++) pinMode(p, OUTPUT);
  Serial.begin(115200);
  Serial.println("pin_test ready: D2-D13 blink at 1 Hz");
}

void loop() {
  for (int p = 2; p <= 13; p++) digitalWrite(p, HIGH);
  Serial.println("HIGH");
  delay(500);
  for (int p = 2; p <= 13; p++) digitalWrite(p, LOW);
  Serial.println("LOW");
  delay(500);
}
