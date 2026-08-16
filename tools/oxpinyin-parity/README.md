# oxpinyin parity tools (W8 experiment)

These tools stay inside the fork branch. They drive the real fork engine
through the session IBus daemon; the oxpinyin checkout is only built and read,
never modified by these scripts.

- `ibus-drive.py` — sends the fixed W8 key sequence through
  `IBus.InputContext.process_key_event_async` and records commit, preedit,
  auxiliary and lookup-table signals as JSONL.
- `run-parity.sh` — runs the same installed fork binary twice with isolated
  `XDG_CACHE_HOME` directories: once native (oxpinyin-capi) and once with
  `LD_PRELOAD` of the pinned C++ libpinyin 2.11.91 oracle. The system data
  directory is `/tmp/oxpinyin-dual-data`, which contains both C++ tables and
  oxpinyin redb tables (see `docs/oxpinyin-switch.md`).
- `compare-streams.py` — the acceptance gate. `IDENTICAL` or
  `TIE-ORDER-ONLY` pass; any other event difference fails.
- `run-smoke.sh` — runs the parity gate, then asserts the committed text is
  `你好 / 你好 / 北京 / nihao` and the nihao candidate page is sane.

The parity gate expects the experiment install's
`share/ibus-libpinyin/network.txt` to be empty. The stock file feeds the
C++ oracle six extra network candidates for initial `n`; oxpinyin imports
network phrases into the user store but does not surface them in candidate
lists yet. Emptying only the `/tmp` dev install file keeps the comparison
on the implemented candidate surface.

The GSettings profile used by both sides is written by `run-parity.sh`:
sort candidate option 2 (`SORT_WITHOUT_SENTENCE_CANDIDATE |
SORT_WITHOUT_LONGER_CANDIDATE | SORT_BY_PHRASE_LENGTH |
SORT_BY_PINYIN_LENGTH | SORT_BY_FREQUENCY`), correction/fuzzy/dynamic-adjust
off, incomplete pinyin on. This is the subset of the fork option mask that
oxpinyin-capi decodes at this stage.
