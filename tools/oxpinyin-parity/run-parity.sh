#!/usr/bin/env bash
set -euo pipefail

# W8 parity: run the same fork binary twice, native oxpinyin-capi and
# LD_PRELOAD pinned C++ libpinyin 2.11.91, drive the same IBus key sequence,
# and compare the observable stream.
#
# Requirements:
#   - the fork is installed at IBUS_LIBPINYIN_ENGINE (user-local prefix only)
#   - oxpinyin-capi and the pinned oracle were built (OXPINYIN_ORACLE_SO)
#   - /tmp/oxpinyin-dual-data contains C++ data + oxpinyin redb tables +
#     interpolation2.text (see docs/oxpinyin-switch.md)
#   - the session IBus daemon is running and `ibus address` works

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
WORK=${OXPINYIN_PARITY_WORK:-/tmp/oxpinyin-parity-run}
ENGINE=${IBUS_LIBPINYIN_ENGINE:-/tmp/ibus-libpinyin-dev/libexec/ibus-engine-libpinyin}
ORACLE_SO=${OXPINYIN_ORACLE_SO:-/tmp/oxpinyin-oracle/prefix/lib/libpinyin.so}
DATA_DIR=${OXPINYIN_PARITY_DATA:-/tmp/oxpinyin-dual-data}
SCHEMA_DIR=${OXPINYIN_PARITY_SCHEMA_DIR:-/tmp/ibus-libpinyin-dev/share/glib-2.0/schemas}

command -v ibus >/dev/null 2>&1 || { echo 'ibus command not found' >&2; exit 2; }
test -x "$ENGINE" || { echo "engine not found: $ENGINE" >&2; exit 2; }
test -f "$ORACLE_SO" || { echo "oracle .so not found: $ORACLE_SO" >&2; exit 2; }
test -f "$DATA_DIR/pinyin_index.redb" || { echo "redb data not found under $DATA_DIR" >&2; exit 2; }
test -f "$DATA_DIR/table.conf" || { echo "C++ table.conf not found under $DATA_DIR" >&2; exit 2; }
test -f "$DATA_DIR/interpolation2.text" || { echo "interpolation2.text not found under $DATA_DIR" >&2; exit 2; }

rm -rf "$WORK"
mkdir -p "$WORK/config/glib-2.0/settings"
cat >"$WORK/config/glib-2.0/settings/keyfile" <<'EOF'
[com/github/libpinyin/ibus-libpinyin/libpinyin]
sort-candidate-option=2
dynamic-adjust=false
correct-pinyin=false
fuzzy-pinyin=false
incomplete-pinyin=true
emoji-candidate=true
english-candidate=true
suggestion-candidate=false
EOF

export GSETTINGS_BACKEND=keyfile
export GSETTINGS_SCHEMA_DIR="$SCHEMA_DIR"
export XDG_CONFIG_HOME="$WORK/config"
export IBUS_ADDRESS=${IBUS_ADDRESS:-$(ibus address)}

run_side() {
    local name=$1 preload=$2
    local cache="$WORK/cache-$name"
    local out="$WORK/$name.jsonl"
    local log="$WORK/$name.engine.log"

    rm -rf "$cache"
    mkdir -p "$cache"

    # Keep the run self-contained; this only kills the experiment's own
    # debug-engine processes (the installed system ibus-engine-libpinyin is
    # never touched).
    pkill -f "$ENGINE" 2>/dev/null || true
    sleep 2

    env \
        XDG_CACHE_HOME="$cache" \
        LD_PRELOAD="$preload" \
        "$ENGINE" >"$log" 2>&1 &
    local pid=$!
    trap 'kill "$pid" 2>/dev/null || true' RETURN EXIT
    sleep 2

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "FAIL: $name engine exited during startup" >&2
        cat "$log" >&2
        exit 1
    fi

    python3 "$SCRIPT_DIR/ibus-drive.py" --engine libpinyin-debug --out "$out"

    # Driver completed and engine stayed alive: smoke/parity pass.
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    trap - RETURN EXIT
    echo "$name: captured $out"
}

run_side oracle "$ORACLE_SO"
run_side oxpinyin ""

python3 "$SCRIPT_DIR/compare-streams.py" \
    "$WORK/oracle.jsonl" "$WORK/oxpinyin.jsonl"
echo "captures: $WORK/{oracle,oxpinyin}.jsonl"
