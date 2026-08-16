#!/usr/bin/env python3
"""Compare two ibus-drive.py JSONL streams.

Verdicts:
  IDENTICAL        every event byte-identical after JSON round-trip
  TIE-ORDER-ONLY   every difference is a lookup-table candidate list with the
                   same multiset, same metadata, and only a different order.
                   This is the known equal-cost tie-swap class.
  DIVERGENT        anything else.

Exit status is 0 for IDENTICAL/TIE-ORDER-ONLY and 2 for DIVERGENT.
"""

import argparse
import collections
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def classify(left, right):
    if left == right:
        return "IDENTICAL"

    if len(left) != len(right):
        return "DIVERGENT"

    tie_diffs = []
    for index, (left_event, right_event) in enumerate(zip(left, right)):
        if left_event == right_event:
            continue
        if (
            left_event.get("event") == "lookup"
            and right_event.get("event") == "lookup"
            and {key: value for key, value in left_event.items() if key != "candidates"}
            == {key: value for key, value in right_event.items() if key != "candidates"}
            and collections.Counter(left_event.get("candidates"))
            == collections.Counter(right_event.get("candidates"))
        ):
            tie_diffs.append(
                {
                    "line": index + 1,
                    "note_before": left[index - 1].get("note"),
                    "oracle": left_event.get("candidates"),
                    "oxpinyin": right_event.get("candidates"),
                }
            )
            continue
        print(f"divergent event line {index + 1}:")
        print(f"  oracle  : {left_event}")
        print(f"  oxpinyin: {right_event}")
        return "DIVERGENT"

    if tie_diffs:
        print(f"TIE-ORDER-ONLY: {len(tie_diffs)} lookup table tie-swap(s)")
        for diff in tie_diffs:
            print(
                "  note={} oracle={} oxpinyin={}".format(
                    diff["note_before"], diff["oracle"], diff["oxpinyin"]
                )
            )
        return "TIE-ORDER-ONLY"
    return "DIVERGENT"


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("oracle")
    parser.add_argument("oxpinyin")
    args = parser.parse_args(argv)

    verdict = classify(load(args.oracle), load(args.oxpinyin))
    print(f"verdict: {verdict}")
    return 0 if verdict in ("IDENTICAL", "TIE-ORDER-ONLY") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
