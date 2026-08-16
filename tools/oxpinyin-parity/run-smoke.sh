#!/usr/bin/env bash
set -euo pipefail

# Phase 2 smoke: one native oxpinyin-capi engine, the same scripted sequence
# as run-parity.sh, plus explicit sanity assertions on committed text.

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
WORK=${OXPINYIN_PARITY_WORK:-/tmp/oxpinyin-parity-run}
"$SCRIPT_DIR/run-parity.sh" >"$WORK/smoke.log" 2>&1 &
PARITY_PID=$!
wait "$PARITY_PID"
OUT="$WORK/oxpinyin.jsonl"
test -f "$OUT" || { echo "missing $OUT" >&2; exit 1; }

python3 - "$OUT" <<'PY'
import json, sys
events = [json.loads(line) for line in open(sys.argv[1], encoding='utf-8')]
commits = [e['text'] for e in events if e.get('event') == 'commit']
expected = ['你好', '你好', '北京', 'nihao']
assert commits == expected, f'commits={commits}'
lookup = [e for e in events if e.get('event') == 'lookup']
assert lookup, 'no lookup-table events captured'
nihao = next(e for e in lookup if e.get('total') == 126 and e['candidates'][0] == '你好')
assert nihao['candidates'][1] == '你'
print('smoke: sane candidates, commits:', ' '.join(commits))
PY
echo "smoke PASS"
