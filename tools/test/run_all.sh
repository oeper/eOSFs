#!/usr/bin/env bash
# Build eOS.pmp (sprite edition) and run every headless suite against it.
#   EOS_PEN=1 tools/test/run_all.sh   also builds + tests the legacy pen edition (eOS-pen.pmp, not shipped)
# Needs `npm install` in tools/test once, python3 + fonttools.  Screenshots land in $EOS_OUT (default /tmp/eos-test).
set -euo pipefail
cd "$(dirname "$0")"
python3 ../build_os.py ../../eOS.pmp
python3 ../lint_pmp.py ../../eOS.pmp
targets=(../../eOS.pmp)
if [ "${EOS_PEN:-0}" = 1 ]; then python3 ../build_pen.py ../../eOS-pen.pmp; targets+=(../../eOS-pen.pmp); fi
for pmp in "${targets[@]}"; do
  for t in interact visual persist robust gesture nav timebase anim; do
    echo "== $(basename "$pmp") $t"; node "$t.js" "$pmp" | tee "/tmp/eos-$t.log" | grep -E "FAIL|ALL OK|FAILED" || true
    grep -q "ALL OK" "/tmp/eos-$t.log" || { echo "$t failed on $pmp"; exit 1; }
  done
done
