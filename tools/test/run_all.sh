#!/usr/bin/env bash
# Build both editions and run every headless suite against each.
#   eOS.pmp          pen edition      (one sprite, pen stamps)
#   eOS-sprites.pmp  sprite edition   (apps are sprites, every UI element is a clone, text by Iris Text)
# Needs `npm install` in tools/test once, python3 + fonttools.  Screenshots land in $EOS_OUT (default /tmp/eos-test).
set -euo pipefail
cd "$(dirname "$0")"
python3 ../build_os.py ../../eOS.pmp
python3 ../build_sprites.py ../../eOS-sprites.pmp
for pmp in ../../eOS.pmp ../../eOS-sprites.pmp; do
  for t in interact visual persist robust gesture nav timebase; do
    echo "== $(basename $pmp) $t"; node "$t.js" "$pmp" | tee /tmp/eos-$t.log | grep -E "FAIL|ALL OK|FAILED" || true
    grep -q "ALL OK" /tmp/eos-$t.log || { echo "$t failed on $pmp"; exit 1; }
  done
done
