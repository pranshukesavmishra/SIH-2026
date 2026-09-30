#!/usr/bin/env bash
# Plan Urena: compile the MK3 firmware for a PC with fake hardware and run the checks,
# once for each board (UNO + CNC Shield V3, and a hand-wired Nano).
set -e
cd "$(dirname "$0")"
for board in 1 0; do
  echo "=== BOARD_CNC_SHIELD=$board ==="
  g++ -std=c++17 -O1 -Wall -Wno-unused-variable -DBOARD_CNC_SHIELD=$board -Imock -o /tmp/zd_fwtest test_fw.cpp
  /tmp/zd_fwtest
done
