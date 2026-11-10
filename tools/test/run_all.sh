#!/usr/bin/env bash
# Build eOS.pmp and run every headless test.  Usage: tools/test/run_all.sh   (needs `npm install` in tools/test once,
# plus python3 + fonttools for the build).  Screenshots land in $EOS_OUT (default /tmp/eos-test).
set -euo pipefail
cd "$(dirname "$0")"
python3 ../build_os.py "${EOS_PMP:-../../eOS.pmp}"
for t in interact visual persist robust gesture; do
  echo "== $t"; node "$t.js" "${EOS_PMP:-../../eOS.pmp}" | tee /tmp/eos-$t.log | grep -E "FAIL|ALL OK|FAILED" || true
  grep -q "ALL OK" /tmp/eos-$t.log || { echo "$t failed"; exit 1; }
done
