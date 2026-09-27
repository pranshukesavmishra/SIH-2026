#!/usr/bin/env bash
# Compile + upload a sketch to an Arduino Nano with arduino-cli, then show its serial output.
#
#   tools/rig/flash.sh beacon     # tools/rig/beacon_firmware.ino  (LED on D9, 4 Hz)
#   tools/rig/flash.sh pintest    # tools/rig/pin_test/pin_test.ino (all of D2-D13 blink, 1 Hz)
#   tools/rig/flash.sh rig        # tools/rig/rig_firmware_v2.ino  (MK2 gimbal)
#   tools/rig/flash.sh beacon /dev/cu.usbserial-1420   # pick the port yourself
#
# Clone Nanos (USB-C, CH340 chip) usually need the "old bootloader" setting; the script
# tries that first and falls back to the new one. Monitor runs for 8 s (MONITOR_SECS).
set -euo pipefail
cd "$(dirname "$0")"

command -v arduino-cli >/dev/null || { echo "arduino-cli missing: brew install arduino-cli"; exit 1; }
if ! arduino-cli core list | grep -q '^arduino:avr'; then
  arduino-cli core update-index && arduino-cli core install arduino:avr
fi

case "${1:-beacon}" in
  beacon)  src=beacon_firmware.ino ;;
  pintest) src=pin_test/pin_test.ino ;;
  rig)     src=rig_firmware_v2.ino
           arduino-cli lib list | grep -q AccelStepper || arduino-cli lib install AccelStepper
           arduino-cli lib list | grep -q '^Servo' || arduino-cli lib install Servo ;;
  *) echo "usage: $0 beacon|pintest|rig [port]"; exit 1 ;;
esac

# arduino-cli wants the sketch in a folder of the same name: stage a copy.
name=$(basename "$src" .ino)
stage=$(mktemp -d)/"$name"; mkdir -p "$stage"; cp "$src" "$stage/$name.ino"

port="${2:-}"
if [ -z "$port" ]; then
  port=$(arduino-cli board list | awk '/usbserial|wchusbserial|ttyUSB|ttyACM/ {print $1; exit}')
fi
[ -n "$port" ] || { echo "No Nano port found. Plug it in; on a Mac a CH340 Nano needs the WCH CH34x driver."; arduino-cli board list; exit 1; }
echo "Port: $port   Sketch: $src"

ok=""
for fqbn in arduino:avr:nano:cpu=atmega328old arduino:avr:nano:cpu=atmega328; do
  echo "== compile + upload as $fqbn"
  if arduino-cli compile --fqbn "$fqbn" "$stage" && arduino-cli upload -p "$port" --fqbn "$fqbn" "$stage"; then
    ok=$fqbn; break
  fi
done
[ -n "$ok" ] || { echo "Upload failed with both bootloaders. Check the port and cable (some USB-C cables are charge-only)."; exit 1; }
echo "Uploaded OK ($ok). Serial output for ${MONITOR_SECS:-8} s:"

# The upload resets the board; read what it prints on boot.
arduino-cli monitor -p "$port" -c baudrate=115200 --quiet & mon=$!
sleep "${MONITOR_SECS:-8}"; kill "$mon" 2>/dev/null || true
