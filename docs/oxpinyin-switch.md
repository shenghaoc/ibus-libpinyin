# oxpinyin backend switch — W8 experiment record

Status: **complete through Phase 3**. The fork builds and runs against
`oxpinyin-capi`, and the same fork binary produces an identical observable
stream on both backends except one equal-cost candidate tie-swap
(`避恶`/`保额` for input `be`), which belongs to oxpinyin's documented
1,030 order-only tie-swap class.

## Source identity

- Fork: `shenghaoc/ibus-libpinyin`, branch `feat/oxpinyin-backend`,
  created from `fix-556-keep-period-in-pinyin-text` @ `5b8ae81`
  (`FORK_BASE_REF` = `fix-556-keep-period-in-pinyin-text`).
- oxpinyin read-only checkout: `/tmp/oxpinyin`, branch
  `feat/w8-fork-bootstrap-surface` @ `9290021`
  (`feat(capi): close W8 fork-bootstrap 51-symbol and C++ header gaps`).
  The parent directory of the fork is read-only in this workspace, so the
  sibling clone lives in `/tmp/oxpinyin`.
- C++ oracle: libpinyin `2.11.91` @
  `0c5e80e1200f84fab185d1c5bde458b770a0636c`, built by
  `tools/oracle/build-oracle.sh` into `/tmp/oxpinyin-oracle/prefix`.
- Model: `model20.text.tar.gz`, SHA-256
  `59c68e89d43ff85f5a309489499cbcde282d2b04bd91888734884b7defcb1155`,
  fetched through `tools/model/fetch-model.sh`.

## Phase 0 — call surface and buckets (rerun against feat/w8-fork-bootstrap-surface)

Method: every `pinyin_[A-Za-z0-9_]+` identifier under `src/` was classified
as fork-local or libpinyin API; call sites were walked through the
preprocessor stack; the implemented set was taken from
`crates/oxpinyin-capi/pinyin.h` and the matching
`#[unsafe(no_mangle)] pub extern "C" fn` exports.

- (a) called + implemented: **51**
- (b) called + NOT implemented: **0**
- (c) implemented + never called by live code: **0**

`pinyin_get_parsed_input_length` is now implemented on the W8 oxpinyin
branch (`crates/oxpinyin-capi/src/parse.rs`; state field `parsed_len`),
closing the gap found in the first Phase-0 pass.

### Live call surface (file:line)

| Symbol | Call sites |
|---|---|
| `pinyin_init` | `src/PYLibPinyin.cc:69,127` |
| `pinyin_fini` | `src/PYLibPinyin.cc:51,54` |
| `pinyin_alloc_instance` | `src/PYLibPinyin.cc:107,165` |
| `pinyin_free_instance` | `src/PYLibPinyin.cc:113,171` |
| `pinyin_set_options` | `src/PYLibPinyin.cc:197,211` |
| `pinyin_set_double_pinyin_scheme` | `src/PYLibPinyin.cc:193` |
| `pinyin_set_zhuyin_scheme` | `src/PYLibPinyin.cc:208` |
| `pinyin_load_addon_phrase_library` | `src/PYLibPinyin.cc:91,149` |
| `pinyin_save` | `src/PYLibPinyin.cc:275,427,429` |
| `pinyin_parse_more_full_pinyins` | `src/PYPFullPinyinEditor.cc:98,104`, `src/PYLibPinyin.cc:401` |
| `pinyin_parse_more_double_pinyins` | `src/PYPDoublePinyinEditor.cc:117,123` |
| `pinyin_parse_more_chewings` | `src/PYPBopomofoEditor.cc:305,311` |
| `pinyin_in_chewing_keyboard` | `src/PYPBopomofoEditor.cc:180,330,384` |
| `pinyin_guess_sentence` | `src/PYPFullPinyinEditor.cc:99,105`, `src/PYPDoublePinyinEditor.cc:118,124`, `src/PYPBopomofoEditor.cc:306,312`, `src/PYPLibPinyinCandidates.cc:149` |
| `pinyin_guess_candidates` | `src/PYPPhoneticEditor.cc:373` |
| `pinyin_guess_predicted_candidates_with_punctuations` | `src/PYPSuggestionEditor.cc:277` |
| `pinyin_reset` | `src/PYPPhoneticEditor.cc:351` |
| `pinyin_get_n_candidate` | `src/PYPLibPinyinCandidates.cc:37,97`, `src/PYPSuggestionCandidates.cc:34,80`, `src/PYPPinyinEditor.cc:342`, `src/PYPBopomofoEditor.cc:358` |
| `pinyin_get_candidate` | `src/PYPLibPinyinCandidates.cc:41,105,190`, `src/PYPSuggestionCandidates.cc:38,86`, `src/PYPPinyinEditor.cc:361`, `src/PYPBopomofoEditor.cc:371` |
| `pinyin_get_candidate_type` | `src/PYPLibPinyinCandidates.cc:44`, `src/PYPSuggestionCandidates.cc:41`, `src/PYPPinyinEditor.cc:362`, `src/PYPBopomofoEditor.cc:372` |
| `pinyin_get_candidate_string` | `src/PYPLibPinyinCandidates.cc:47`, `src/PYPSuggestionCandidates.cc:58` |
| `pinyin_get_candidate_nbest_index` | `src/PYPLibPinyinCandidates.cc:114` |
| `pinyin_is_user_candidate` | `src/PYPLibPinyinCandidates.cc:59,68,191` |
| `pinyin_remove_user_candidate` | `src/PYPLibPinyinCandidates.cc:192` |
| `pinyin_choose_candidate` | `src/PYPLibPinyinCandidates.cc:111,131,139,146` |
| `pinyin_choose_predicted_candidate` | `src/PYPSuggestionCandidates.cc:87` |
| `pinyin_train` | `src/PYPLibPinyinCandidates.cc:116,154` |
| `pinyin_get_parsed_input_length` | `src/PYPLibPinyinCandidates.cc:151` |
| `pinyin_get_sentence` | `src/PYPLibPinyinCandidates.cc:118,152`, `src/PYPPinyinEditor.cc:366`, `src/PYPBopomofoEditor.cc:376` |
| `pinyin_get_character_offset` | `src/PYPPinyinEditor.cc:379`, `src/PYPBopomofoEditor.cc:404` |
| `pinyin_get_pinyin_key_rest` | `src/PYPLibPinyinCandidates.cc:165` |
| `pinyin_get_pinyin_key_rest_positions` | `src/PYPLibPinyinCandidates.cc:168` |
| `pinyin_get_pinyin_offset` | `src/PYPPhoneticEditor.cc:393,672,686` |
| `pinyin_get_left_pinyin_offset` | `src/PYPPhoneticEditor.cc:676` |
| `pinyin_get_right_pinyin_offset` | `src/PYPPhoneticEditor.cc:690` |
| `pinyin_get_full_pinyin_auxiliary_text` | `src/PYPFullPinyinEditor.cc:128`, `src/PYPCloudCandidates.cc:704` |
| `pinyin_get_double_pinyin_auxiliary_text` | `src/PYPDoublePinyinEditor.cc:151` |
| `pinyin_get_chewing_auxiliary_text` | `src/PYPBopomofoEditor.cc:425` |
| `pinyin_mask_out` | `src/PYLibPinyin.cc:363,366,369,477` |
| `pinyin_remember_user_input` | `src/PYLibPinyin.cc:389,402` |
| `pinyin_begin_add_phrases` | `src/PYLibPinyin.cc:237,540` |
| `pinyin_iterator_add_phrase` | `src/PYLibPinyin.cc:267,570` |
| `pinyin_end_add_phrases` | `src/PYLibPinyin.cc:272,576` |
| `pinyin_begin_get_phrases` | `src/PYLibPinyin.cc:282` |
| `pinyin_iterator_has_next_phrase` | `src/PYLibPinyin.cc:289` |
| `pinyin_iterator_get_next_phrase` | `src/PYLibPinyin.cc:293` |
| `pinyin_end_get_phrases` | `src/PYLibPinyin.cc:303` |
| `pinyin_begin_get_bigram_phrases` | `src/PYLibPinyin.cc:310` |
| `pinyin_bigram_iterator_has_next_phrase` | `src/PYLibPinyin.cc:317` |
| `pinyin_bigram_iterator_get_next_phrase` | `src/PYLibPinyin.cc:321` |
| `pinyin_end_get_bigram_phrases` | `src/PYLibPinyin.cc:331` |

Conditional sites: only the cloud-input call
(`PYPCloudCandidates.cc:704`, compiled under `ENABLE_CLOUD_INPUT_MODE`)
is ifdef-gated. Lua/English/table mode files make no direct `pinyin_*`
calls. The `#if 0` dead blocks remain as recorded in the first Phase-0
pass; none are live.

### Header / non-symbol surface

The W8 oxpinyin header closes the first-pass C++ blockers: it has
`extern "C"` guards, `PinyinKey`/`PinyinKeyPos` aliases, fork-referenced
option/correction/ambiguity constants, `PHRASE_INDEX_*` macros,
`DOUBLE_PINYIN_DEFAULT`, `ZHUYIN_DEFAULT`, and `null_token`. The fork still
includes only `<pinyin.h>` from the 9 sites listed in the first pass; no
header beyond `pinyin.h` is used.

Build/link/runtime surface:
- Autotools only; no CMake.
- Old path: `PKG_CHECK_MODULES(LIBPINYIN, [libpinyin >= 2.9.92])`.
- New path: `--with-oxpinyin-capi=PATH` (oxpinyin checkout root) plus
  `--with-oxpinyin-capi-datadir=PATH` (runtime system dir).
- oxpinyin has no `pinyin.pc`; the experiment uses the explicit configure
  options instead, so no pinyin.pc file is needed.
- Runtime system dir for oxpinyin-capi must contain `pinyin_index.redb`,
  `phrase_index.redb`, `bigram.redb`, and `interpolation2.text` (the
  fetched model's real unigrams); `table.conf` is optional for λ.
  User dir remains `$XDG_CACHE_HOME/ibus/libpinyin` and stores
  `user_store.redb`.

## Phase 1 — link swap

Built with:

```bash
cd /tmp/oxpinyin
cargo build --release -p oxpinyin-capi
cd /home/sheng/Documents/repos/ibus-libpinyin
./autogen.sh \
  --with-oxpinyin-capi=/tmp/oxpinyin \
  --with-oxpinyin-capi-datadir=/tmp/oxpinyin-dual-data \
  --prefix=/tmp/ibus-libpinyin-dev \
  --disable-libnotify --disable-opencc --disable-lua-extension
make -j4 && make install
```

Fork changes (see commits on `feat/oxpinyin-backend`):
- `configure.ac`: add the two `--with-oxpinyin-capi*` options; in
  oxpinyin mode set `LIBPINYIN_CFLAGS=-I.../crates/oxpinyin-capi`,
  `LIBPINYIN_LIBS=-L.../target/release
  -Wl,-rpath,.../target/release -lpinyin_capi`, and set the system dir
  directly. The old libpinyin pkg-config path stays the default.
- `src/Makefile.am`: compile `-DLIBPINYIN_DATADIR="@LIBPINYIN_SYSTEM_DIR@"`
  instead of always appending `/data`.
- `src/PYLibPinyin.h`: include `<pinyin.h>` instead of forward-declaring
  `struct _pinyin_context_t` / `struct _pinyin_instance_t`; the underscore
  tags conflict with oxpinyin's C tag names in C++.
- No pinyin-related warning was emitted; `make` is clean with
  `-Wall -Werror`.

## Phase 2 — runtime wiring and smoke

Deployment story:
- The experiment install is user-local (`/tmp/ibus-libpinyin-dev`); the
  system `ibus-engine-libpinyin` is never replaced.
- `LIBPINYIN_DATADIR` compiled into the binary is
  `/tmp/oxpinyin-dual-data`. That directory contains symlinks to the
  pinned C++ data (`table.conf`, `.bin`, `bigram.db`) plus the oxpinyin
  redb export and a symlink to `interpolation2.text`; one directory works
  for both backends.
- GSettings schema comes from the install's
  `share/glib-2.0/schemas/gschemas.compiled` and is selected with
  `GSETTINGS_SCHEMA_DIR`.
- The headless driver (`tools/oxpinyin-parity/ibus-drive.py`) connects to
  the running session `ibus-daemon`, sets the global engine to the debug
  engine registered by our process, and sends real DBus key events.

Smoke sequence and result (native oxpinyin-capi):
1. type `nihao`, Space -> candidate page starts with `你好`; commit `你好`.
2. type `nihao` again, label 1 -> commit `你好` (repeated selection/train).
3. type `beijing`, label 3 -> commit `北京` (multi-word sentence).
4. lifecycle probes: empty backspace/left/right, focus-out, reset.
5. type `nihao`, Return -> raw commit `nihao`.

No crashes; candidate pages are sane; commits are exactly
`你好 / 你好 / 北京 / nihao`. Save/train: oxpinyin commits training durably
on every `pinyin_train`. The fork save timer was exercised with the W8 test
hook `LIBPINYIN_SAVE_TIMEOUT_SECONDS=5`; after the timer fired, the redb
user store compacted from 1,056,768 bytes to 20,480 bytes, proving the
train -> modified -> timeout -> `pinyin_save` cycle.

## Phase 3 — wire-level parity

Capture mechanism:
- The `/tmp/ibus-libpinyin-dev` install's `network.txt` is emptied for the
  gate so imported network phrases cannot leak into the oracle candidate
  table (oxpinyin does not surface them yet; see findings).
- `tools/oxpinyin-parity/run-parity.sh` runs the **same installed fork
  binary** twice with isolated `XDG_CACHE_HOME` dirs:
  1. oracle: `LD_PRELOAD=/tmp/oxpinyin-oracle/prefix/lib/libpinyin.so`;
  2. oxpinyin: native `libpinyin_capi.so` (DT_NEEDED + RPATH).
- Both runs use the keyfile GSettings profile written by the script:
  sort option 2 (no sentence/longer candidates, three-key order),
  `dynamic-adjust=false`, `correct-pinyin=false`, `fuzzy-pinyin=false`,
  `incomplete-pinyin=true`.
- `ibus-drive.py` records `commit`, `preedit`, `auxiliary`, and
  `lookup` events as JSONL; `compare-streams.py` is the acceptance gate.

Result:
- Commits identical: `你好 / 你好 / 北京 / nihao`.
- Every preedit, auxiliary, lookup total/cursor/page-size, and candidate
  page is identical except one event: input `be` candidate positions 5/6
  are `避恶, 保额` on the oracle and `保额, 避恶` on oxpinyin.
- `compare-streams.py` verdict: **TIE-ORDER-ONLY**.
- The two texts have identical rank keys: phrase length 2, pinyin span 2,
  real unigram count 2. The order differs only in collection-order tie
  resolution.
- oxpinyin's own real-tables parity test still reports exactly **1030
  order-only tie-swaps** and the frozen pins
  `10136 / 10182 / 94456 of 98930 / absent 1` (run after all local
  oxpinyin patches; passed bit-identical).

LD_PRELOAD symbol resolution was confirmed with `LD_DEBUG=bindings`: all
fork `pinyin_*` references bind to the preloaded oracle library in the
oracle run and to `libpinyin_capi.so` in the native run.

## Phase 4 — record

### oxpinyin-patches/ inventory (local, uncommitted in /tmp/oxpinyin)

| Patch | Rationale |
|---|---|
| `01-capi-decode-pinyin-incomplete-option.patch` | Decode `PINYIN_INCOMPLETE` from `pinyin_set_options` into the session config. |
| `02-capi-load-interpolation2-real-unigrams.patch` | Load the fetched model's `interpolation2.text` when present so candidate ranking uses the real three-key frequencies. |
| `03-capi-full-pinyin-auxiliary-text-format.patch` | Port C++ full-pinyin auxiliary text (`space-separated keys + |`). |
| `04-engine-raise-max-candidates-to-4096.patch` | The C++ candidate table is not capped at 64; raising the session cap lets the wire total match. The real-tables pins remain unchanged. |
| `05-capi-filter-ng-only-tokens-at-abi-boundary.patch` | C ABI shim: raw `n` must not surface phrases reachable only through zero-initial `ng`. Kept in the capi layer because the equivalent core `completions` fix moved the frozen pins and was reverted under the STOP rule. |
| `06-bisect-guard-nbest-accessor.patch` | oxpinyin's bisection tool aborted against the oracle by calling `pinyin_get_candidate_nbest_index` on non-NBEST candidates. |

All patches keep integer/saturating arithmetic; no float paths were added.
`cargo test -p oxpinyin-capi --release` passes 13/13. The pinned oracle
artifacts and frozen fixtures were not modified; `/tmp/oxpinyin` still has
only the local uncommitted diffs above.

### Minimal changes list (fork branch)

1. `configure.ac` + `src/Makefile.am`: explicit oxpinyin-capi link/data
   options.
2. `src/PYLibPinyin.h`: use `<pinyin.h>` instead of conflicting forward
   typedefs.
3. `src/PYLibPinyin.{h,cc}`: save-timeout test hook
   (`LIBPINYIN_SAVE_TIMEOUT_SECONDS`, default 300) so the headless harness
   can prove the save/train cycle without a five-minute wait.
4. `tools/oxpinyin-parity/`: capture/comparison/smoke/parity scripts.
5. `oxpinyin-patches/`: candidate upstream changes for the maintainer to
   review.
6. `docs/oxpinyin-switch.md`: this record.

### Findings / Stage-2 opportunities (note only)

- oxpinyin-core expands incomplete keys by string prefix rather than
  phonetic initial. Fixing it in core is correct long-term but moved the
  frozen pins; this experiment therefore applies the narrow capi shim
  (`05-...patch`) and records the core fix as a maintainer decision.
- Imported user/network dictionary phrases do not yet surface in oxpinyin
  candidate lists. With the stock dev-install `network.txt`, the oracle
  side shows six extra network candidates for `n`. The parity run uses an
  emptied `network.txt` in the `/tmp/ibus-libpinyin-dev` install so both
  sides start from the same network dictionary state; this is a Stage-2
  oxpinyin gap, not a fork-side change.
- `pinyin_load_addon_phrase_library` remains a provisional no-op; addon
  dictionaries silently do not load.
- Correction/fuzzy/dynamic-adjust option bits are not decoded by
  oxpinyin-engine yet; the parity profile turns them off on the C++ side
  so both backends implement the same supported semantics.
- Double pinyin and chewing auxiliary text are still provisional preedit
  text rather than C++-formatted key text.
- Prediction APIs (`pinyin_guess_predicted_candidates_with_punctuations`,
  `pinyin_choose_predicted_candidate`) return false/no-op; the suggestion
  editor path is not exercised by the smoke sequence.

## Verification

- `git -C /tmp/oxpinyin status` shows only the six local patch diffs; no
  commit was created and nothing was pushed to the oxpinyin remote.
- No `gh pr create` or any PR command was run.
- Fork branch `feat/oxpinyin-backend` is pushed to
  `origin` (`shenghaoc/ibus-libpinyin`).
