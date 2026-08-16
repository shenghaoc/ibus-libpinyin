#!/usr/bin/env python3
"""Deterministic IBus driver for the oxpinyin fork-backend experiment.

The fork has no test harness that types into a real engine; this drives the
debug engine over the session IBus daemon exactly the way a desktop client
does (DBus ProcessKeyEvent plus the standard engine signals).  Output is one
JSON object per line, which makes the two backend runs byte-comparable.

Usage:
  ibus-drive.py --engine libpinyin-debug --out capture.jsonl

The engine process must already be running and registered with IBus.  The
caller is responsible for GSETTINGS_SCHEMA_DIR, XDG_CACHE_HOME and the
keyfile GSettings profile; run-parity.sh does that.
"""

import argparse
import json
import sys

import gi

gi.require_version("IBus", "1.0")
from gi.repository import GLib, IBus  # noqa: E402


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="libpinyin-debug")
    parser.add_argument("--out", required=True)
    parser.add_argument("--step-ms", type=int, default=250)
    return parser.parse_args(argv)


def text_of(value):
    return value.get_text() if value is not None else ""


def main(argv):
    args = parse_args(argv)

    bus = IBus.Bus()
    bus.set_global_engine(args.engine)
    context = bus.create_input_context("oxpinyin-parity-driver")
    context.set_capabilities(
        IBus.Capabilite.PREEDIT_TEXT
        | IBus.Capabilite.AUXILIARY_TEXT
        | IBus.Capabilite.LOOKUP_TABLE
        | IBus.Capabilite.FOCUS
        | IBus.Capabilite.SURROUNDING_TEXT
    )

    events = []
    logging_enabled = False

    def log(event):
        if logging_enabled:
            events.append(event)

    context.connect(
        "commit-text",
        lambda _context, text: log({"event": "commit", "text": text_of(text)}),
    )
    context.connect(
        "update-preedit-text",
        lambda _context, text, cursor, visible: log(
            {
                "event": "preedit",
                "text": text_of(text),
                "cursor": cursor,
                "visible": bool(visible),
            }
        ),
    )
    context.connect(
        "update-auxiliary-text",
        lambda _context, text, visible: log(
            {"event": "aux", "text": text_of(text), "visible": bool(visible)}
        ),
    )

    def lookup_cb(_context, table, visible):
        total = table.get_number_of_candidates()
        candidates = []
        for index in range(min(total, 12)):
            candidate = table.get_candidate(index)
            candidates.append(candidate.get_text() if candidate is not None else None)
        log(
            {
                "event": "lookup",
                "candidates": candidates,
                "cursor": table.get_cursor_pos(),
                "page_size": table.get_page_size(),
                "total": total,
                "visible": bool(visible),
            }
        )

    context.connect("update-lookup-table", lookup_cb)
    context.focus_in()

    # The W8 smoke/parity sequence:
    #   nihao -> space selects/commits 你好 (NBEST/normal path)
    #   nihao again -> label 1 commits 你好 (repeat/training path)
    #   beijing -> label 3 commits 北京 (multi-word selection; first page is
    #              ["beijing", "⬆", "北京", ...], so label 3 is index 2)
    #   nihao -> Return commits raw pinyin (raw-commit path)
    sequence = []
    sequence += [(ord(ch), "type:" + ch) for ch in "nihao"]
    sequence.append((IBus.KEY_space, "select:space"))
    sequence += [(ord(ch), "type:" + ch + ":repeat") for ch in "nihao"]
    sequence.append((IBus.KEY_1, "select:label-1"))
    sequence += [(ord(ch), "type:" + ch) for ch in "beijing"]
    sequence.append((IBus.KEY_3, "select:label-3"))

    # zh-class incomplete-initial coverage for the pin re-freeze evidence:
    # zhongguo plus z / c / s single initials.  Escape after each keeps the
    # composition boundaries identical on both backends.
    sequence += [(ord(ch), "type:" + ch + ":zh-class") for ch in "zhongguo"]
    sequence.append((IBus.KEY_Escape, "reset:zhongguo"))
    for initial in ("z", "c", "s"):
        sequence.append((ord(initial), "type:" + initial + ":zh-class"))
        sequence.append((IBus.KEY_Escape, "reset:initial-" + initial))

    sequence.append((IBus.KEY_BackSpace, "lifecycle:backspace-empty"))
    sequence.append((IBus.KEY_Left, "lifecycle:left-empty"))
    sequence.append((IBus.KEY_Right, "lifecycle:right-empty"))
    sequence += [(ord(ch), "type:" + ch) for ch in "nihao"]
    sequence.append((IBus.KEY_Return, "commit:return-raw"))

    index = 0
    loop = GLib.MainLoop()

    def step():
        nonlocal index, logging_enabled
        if index == 0:
            logging_enabled = True
            log({"event": "focus-in"})
        if index < len(sequence):
            keyval, note = sequence[index]
            index += 1
            log({"event": "key", "keyval": int(keyval), "note": note})
            context.process_key_event_async(keyval, 0, 0, -1, None, lambda *_: None)
            return True

        context.focus_out()
        log({"event": "focus-out"})
        context.reset()
        log({"event": "reset"})

        def finish():
            loop.quit()

        GLib.timeout_add(300, finish)
        return False

    GLib.timeout_add(args.step_ms, step)
    GLib.timeout_add(12000, loop.quit)
    loop.run()

    with open(args.out, "w", encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    print(f"events={len(events)} written={args.out}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1:])
