# oxpinyin backend switch — W8 experiment record

Status: **revalidated against clean oxpinyin `main` after PR stack #80–#87
was merged**. The fork builds and runs against `oxpinyin-capi` with zero
local oxpinyin patches. The extended parity sequence produces the same
observable stream on both backends except one equal-cost candidate tie-swap
(`避恶`/`保额` for input `be`): verdict **TIE-ORDER-ONLY**.

## Source identity

- Fork: `shenghaoc/ibus-libpinyin`, branch `feat/oxpinyin-backend`,
  created from `fix-556-keep-period-in-pinyin-text` @ `5b8ae81`
  (`FORK_BASE_REF` = `fix-556-keep-period-in-pinyin-text`).
- oxpinyin read-only checkout: `/tmp/oxpinyin`, branch `main` @
  `3ec6172b73e7158c0f9555e48cd71d7dcf00b576`
  (`refactor: stack-review cleanups that do not change merge-time behavior`);
  `git -C /tmp/oxpinyin status --porcelain` is empty (clean, no local
  patches). The parent directory of the fork is read-only in this
  workspace, so the sibling clone lives in `/tmp/oxpinyin`.
- C++ oracle: libpinyin `2.11.91` @
  `0c5e80e1200f84fab185d1c5bde458b770a0636c`, built by
  `tools/oracle/build-oracle.sh` into `/tmp/oxpinyin-oracle/prefix`.
- Model: `model20.text.tar.gz`, SHA-256
  `59c68e89d43ff85f5a309489499cbcde282d2b04bd91888734884b7defcb1155`,
  fetched through `tools/model/fetch-model.sh`.

## Revalidation against merged oxpinyin main (PR stack #80–#87)

Method: same experiment shape as Phase 1–3, but the oxpinyin checkout is
clean `main` @ `3ec6172b73e7158c0f9555e48cd71d7dcf00b576` with no local
patches, and `/tmp/oxpinyin-dual-data` was regenerated from a clean-main
`oxpinyin-migrate export` plus the pinned model `interpolation2.text`.

Main-state checks all pass:

- `pinyin_get_parsed_input_length` is exported in
  `crates/oxpinyin-capi/pinyin.h` and implemented.
- `PINYIN_CAPI_ALLOW_FLAT_UNIGRAMS` is gone from the tree.
- `oxpinyin_init_for_fixtures` exists in `context.rs` but is **not** in
  `pinyin.h`.
- `MAX_CANDIDATES` is absent from `crates/oxpinyin-engine/src/session.rs`.

Build/link/symbol result:

- `cargo build --release -p oxpinyin-capi` completes.
- The fork was rebuilt and reinstalled exactly as Phase 1
  (`--with-oxpinyin-capi=/tmp/oxpinyin`,
  `--with-oxpinyin-capi-datadir=/tmp/oxpinyin-dual-data`,
  `--prefix=/tmp/ibus-libpinyin-dev`, `--disable-libnotify`,
  `--disable-opencc`, `--disable-lua-extension`); the make log has no
  compiler warnings/errors.
- `ldd /tmp/ibus-libpinyin-dev/libexec/ibus-engine-libpinyin` resolves
  `libpinyin_capi.so` to the rebuilt
  `/tmp/oxpinyin/target/release/libpinyin_capi.so`; `readelf -d` shows it
  as `DT_NEEDED` with the `/tmp/oxpinyin/target/release` RPATH.
- `nm -D --undefined-only` on the engine reports exactly **51**
  undefined `pinyin_*` symbols; `ldd -r` reports no unresolved
  `pinyin_*` symbol. The 51 references are the same live call surface as
  the Phase 0 table below.

Smoke/parity result:

- `tools/oxpinyin-parity/run-smoke.sh` passes: commits are exactly
  `你好 / 你好 / 北京 / nihao` and the candidate-page sanity assertions hold.
- `tools/oxpinyin-parity/run-parity.sh` (extended sequence with the
  `zhongguo` plus `z`/`c`/`s` zh-class inputs) captures 128 events per
  side. `compare-streams.py` verdict: **TIE-ORDER-ONLY**. The sole lookup
  difference is the equal-cost `be` swap:
  oracle `…, 避恶, 保额, …` vs oxpinyin `…, 保额, 避恶, …`.

Interpolation2 / fail-closed `pinyin_init`:

- `/tmp/oxpinyin-dual-data` does supply `interpolation2.text` (symlink to
  the verified model20 extraction), so the fork's data-path config is
  correct and public `pinyin_init` succeeds.
- A direct C probe confirmed the new fail-closed behavior: the same redb
  tables without `interpolation2.text` make public `pinyin_init` return
  NULL, while `oxpinyin_init_for_fixtures` is the explicit fixture-only
  path. This is the intended #84 behavior, not a fork regression.

Save/train cycle:

- With `LIBPINYIN_SAVE_TIMEOUT_SECONDS=5` and the save-cycle GSettings
  profile using `sort-candidate-option=1` (sentence candidates enabled; the
  parity profile's option 2 deliberately excludes NBEST/sentence
  candidates and therefore never reaches `pinyin_train`), selecting `nihao`
  with Space runs the full NBEST train path. An LD_PRELOAD call trace
  recorded `pinyin_train -> 1` followed by the timer-driven
  `pinyin_save -> 1`; `user_store.redb` compacted from **1,056,768 bytes
  to 32,768 bytes**, proving train -> modified -> timeout -> `pinyin_save`.

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
user store compacted from 1,056,768 bytes to 20,480 bytes in the original
patched run (the clean-main revalidation above observes 32,768 bytes),
proving the train -> modified -> timeout -> `pinyin_save` cycle.

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

### oxpinyin-patches/ disposition (deleted after merge)

The six experiment `.patch` files were deleted from the fork branch in
commit `fbd1b97` (`chore: remove oxpinyin-patches superseded by merged
oxpinyin PR stack`); the files remain recoverable from git history. All six
changes are merged or superseded on oxpinyin main:

| Patch | Upstream disposition |
|---|---|
| `01-capi-decode-pinyin-incomplete-option.patch` | Merged as PR **#83** (`feat/capi-decode-incomplete-option`). |
| `02-capi-load-interpolation2-real-unigrams.patch` | Merged as PR **#84** (`feat/capi-interpolation2-unigrams`); public `pinyin_init` is now fail-closed and requires `interpolation2.text`. |
| `03-capi-full-pinyin-auxiliary-text-format.patch` | Merged as PR **#86** (`feat/capi-full-aux-text`). |
| `04-engine-raise-max-candidates-to-4096.patch` | Merged as PR **#87** (`fix/engine-remove-candidate-cap`); the cap constant is gone from `session.rs`. |
| `05-capi-filter-ng-only-tokens-at-abi-boundary.patch` | **Superseded** by PR **#85** (`fix/core-incomplete-phonetic-initial`), the core phonetic-initial fix. |
| `06-bisect-guard-nbest-accessor.patch` | Merged as PR **#82** (`fix/bisect-nbest-guard`). |

The other two commits in the PR stack are foundation already in main:
PR **#80** (`fix/shared-fewest-keys-walk`) and PR **#81**
(`feat/w8-fork-bootstrap-surface`, including the exported
`pinyin_get_parsed_input_length`).

### Minimal changes list (fork branch)

1. `configure.ac` + `src/Makefile.am`: explicit oxpinyin-capi link/data
   options.
2. `src/PYLibPinyin.h`: use `<pinyin.h>` instead of conflicting forward
   typedefs.
3. `src/PYLibPinyin.{h,cc}`: save-timeout test hook
   (`LIBPINYIN_SAVE_TIMEOUT_SECONDS`, default 300) so the headless harness
   can prove the save/train cycle without a five-minute wait.
4. `tools/oxpinyin-parity/`: capture/comparison/smoke/parity scripts.
5. `oxpinyin-patches/`: deleted after the upstream PR stack landed
   (see disposition above).
6. `docs/oxpinyin-switch.md`: this record.

### Findings / current known gaps after revalidation

The former patch-05 incomplete-key finding is closed: PR **#85** fixes
phonetic-initial expansion in oxpinyin core, so the C ABI boundary shim is
no longer needed.

Still open on oxpinyin main as of the revalidation:

- Imported network/user dictionary phrases do not yet surface in oxpinyin
  candidate lists. The parity gate therefore still uses an emptied
  `/tmp/ibus-libpinyin-dev/share/ibus-libpinyin/network.txt` so both
  backends start from the same dictionary state.
- Correction, fuzzy, and dynamic-adjust option bits are still not decoded
  by oxpinyin-engine; the parity profile keeps them off.
- Prediction APIs (`pinyin_guess_predicted_candidates_with_punctuations`,
  `pinyin_choose_predicted_candidate`) remain no-op/false; the suggestion
  editor path is not exercised by the parity sequence.
- Double-pinyin and chewing auxiliary text remain provisional (preedit
  text rather than C++-formatted key text).
- `pinyin_load_addon_phrase_library` remains a provisional no-op, so addon
  dictionaries still silently do not load.

## Verification

- oxpinyin checkout is clean `main` @
  `3ec6172b73e7158c0f9555e48cd71d7dcf00b576`: `git -C /tmp/oxpinyin status
  --porcelain` is empty, so none of the six experiment patches remain
  applied.
- `oxpinyin-patches/` was deleted from the fork branch in commit
  `fbd1b97`; the `.patch` files remain recoverable from git history.
- No `gh pr create` or any other PR command was run, and nothing was
  pushed to the oxpinyin remote.
- Fork branch `feat/oxpinyin-backend` is pushed to
  `origin` (`shenghaoc/ibus-libpinyin`); the pushed tip SHA is recorded in
  the revalidation report that accompanies this branch.
