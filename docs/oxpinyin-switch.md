# oxpinyin backend switch — Phase 0 characterization (STOPPED)

Status: **STOP after Phase 0**. The fork's live call surface contains one
symbol, `pinyin_get_parsed_input_length`, that oxpinyin-capi does not
implement. Per the W8 roadmap, a non-empty gap list is a maintainer
decision: closing it means either a local oxpinyin patch or a fork-side
shim, both of which need sign-off before any link swap.

## Source identity

- Fork checkout: `shenghaoc/ibus-libpinyin`, branch
  `feat/oxpinyin-backend`, created from
  `fix-556-keep-period-in-pinyin-text` at commit
  `5b8ae81` (`FORK_BASE_REF` = `fix-556-keep-period-in-pinyin-text`).
- oxpinyin checkout (read-only input): `/tmp/oxpinyin`, `main` at commit
  `0d2385e` (`chore(rename): rename workspace crates to oxpinyin-* package
  names`). The parent directory of the fork is mounted read-only in this
  workspace, so the read-only sibling clone was placed in `/tmp/oxpinyin`.
- oxpinyin reference document: `docs/findings/abi-subset.md`, which
  characterizes ibus-libpinyin **tag 1.16.5**. This fork has since moved;
  the delta matters and is shown below.

## Method

- Every `.cc`/`.h` file under `src/` was searched for `pinyin_[A-Za-z0-9_]+`.
- Identifiers that are fork-local functions/variables were removed
  (`pinyin_accelerator_name`, `ibus_pinyin_engine_*`, `pinyin_text`,
  `pinyin_options`, `pinyin_cursor`).
- Function call sites were separated from declarations/type uses.
- Call sites were walked through the preprocessor stack so `#if 0` blocks
  are listed as dead code rather than live calls.
- The implemented set was taken from the declarations in
  `crates/oxpinyin-capi/pinyin.h` and the corresponding
  `#[unsafe(no_mangle)] pub extern "C" fn` exports; both contain exactly
  50 symbols and agree with each other.

## 1. Live call surface: 51 symbols

50 of the 51 live symbols are implemented by oxpinyin-capi. The one gap is
`pinyin_get_parsed_input_length` at
`src/PYPLibPinyinCandidates.cc:151`, introduced by upstream commit
`2c5baa9` ("Fix LibPinyinCandidates::selectCandidate method"), which
changed the full-selection test from `lookup_cursor ==
m_editor->m_text.length()` to `lookup_cursor ==
pinyin_get_parsed_input_length(instance)`. oxpinyin's ABI-subset document
was frozen at tag 1.16.5, before that commit, and explicitly listed the
symbol as "not called anywhere in ibus-libpinyin".

Legend: `OK` = called + implemented, `GAP` = called + not implemented.

| Bucket | Symbol | Call sites (file:line) |
|---|---|---|
| OK | `pinyin_init` | `src/PYLibPinyin.cc:69` (pinyin), `:127` (chewing/bopomofo) |
| OK | `pinyin_fini` | `src/PYLibPinyin.cc:51,54` |
| OK | `pinyin_alloc_instance` | `src/PYLibPinyin.cc:107,165` |
| OK | `pinyin_free_instance` | `src/PYLibPinyin.cc:113,171` |
| OK | `pinyin_set_options` | `src/PYLibPinyin.cc:197,211` |
| OK | `pinyin_set_double_pinyin_scheme` | `src/PYLibPinyin.cc:193` |
| OK | `pinyin_set_zhuyin_scheme` | `src/PYLibPinyin.cc:208` |
| OK | `pinyin_load_addon_phrase_library` | `src/PYLibPinyin.cc:91,149` |
| OK | `pinyin_save` | `src/PYLibPinyin.cc:275,427,429` |
| OK | `pinyin_parse_more_full_pinyins` | `src/PYPFullPinyinEditor.cc:98,104`, `src/PYLibPinyin.cc:401` (cloud) |
| OK | `pinyin_parse_more_double_pinyins` | `src/PYPDoublePinyinEditor.cc:117,123` |
| OK | `pinyin_parse_more_chewings` | `src/PYPBopomofoEditor.cc:305,311` |
| OK | `pinyin_in_chewing_keyboard` | `src/PYPBopomofoEditor.cc:180,330,384` |
| OK | `pinyin_guess_sentence` | `src/PYPFullPinyinEditor.cc:99,105`, `src/PYPDoublePinyinEditor.cc:118,124`, `src/PYPBopomofoEditor.cc:306,312`, `src/PYPLibPinyinCandidates.cc:149` |
| OK | `pinyin_guess_candidates` | `src/PYPPhoneticEditor.cc:373` |
| OK | `pinyin_guess_predicted_candidates_with_punctuations` | `src/PYPSuggestionEditor.cc:277` |
| OK | `pinyin_reset` | `src/PYPPhoneticEditor.cc:351` |
| OK | `pinyin_get_n_candidate` | `src/PYPLibPinyinCandidates.cc:37,97`, `src/PYPSuggestionCandidates.cc:34,80`, `src/PYPPinyinEditor.cc:342`, `src/PYPBopomofoEditor.cc:358` |
| OK | `pinyin_get_candidate` | `src/PYPLibPinyinCandidates.cc:41,105,190`, `src/PYPSuggestionCandidates.cc:38,86`, `src/PYPPinyinEditor.cc:361`, `src/PYPBopomofoEditor.cc:371` |
| OK | `pinyin_get_candidate_type` | `src/PYPLibPinyinCandidates.cc:44`, `src/PYPSuggestionCandidates.cc:41`, `src/PYPPinyinEditor.cc:362`, `src/PYPBopomofoEditor.cc:372` |
| OK | `pinyin_get_candidate_string` | `src/PYPLibPinyinCandidates.cc:47`, `src/PYPSuggestionCandidates.cc:58` |
| OK | `pinyin_get_candidate_nbest_index` | `src/PYPLibPinyinCandidates.cc:114` |
| OK | `pinyin_is_user_candidate` | `src/PYPLibPinyinCandidates.cc:59,68,191` |
| OK | `pinyin_remove_user_candidate` | `src/PYPLibPinyinCandidates.cc:192` |
| OK | `pinyin_choose_candidate` | `src/PYPLibPinyinCandidates.cc:111,131,139,146` |
| OK | `pinyin_choose_predicted_candidate` | `src/PYPSuggestionCandidates.cc:87` |
| OK | `pinyin_train` | `src/PYPLibPinyinCandidates.cc:116,154` |
| GAP | `pinyin_get_parsed_input_length` | `src/PYPLibPinyinCandidates.cc:151` |
| OK | `pinyin_get_sentence` | `src/PYPLibPinyinCandidates.cc:118,152`, `src/PYPPinyinEditor.cc:366`, `src/PYPBopomofoEditor.cc:376` |
| OK | `pinyin_get_character_offset` | `src/PYPPinyinEditor.cc:379`, `src/PYPBopomofoEditor.cc:404` |
| OK | `pinyin_get_pinyin_key_rest` | `src/PYPLibPinyinCandidates.cc:165` |
| OK | `pinyin_get_pinyin_key_rest_positions` | `src/PYPLibPinyinCandidates.cc:168` |
| OK | `pinyin_get_pinyin_offset` | `src/PYPPhoneticEditor.cc:393,672,686` |
| OK | `pinyin_get_left_pinyin_offset` | `src/PYPPhoneticEditor.cc:676` |
| OK | `pinyin_get_right_pinyin_offset` | `src/PYPPhoneticEditor.cc:690` |
| OK | `pinyin_get_full_pinyin_auxiliary_text` | `src/PYPFullPinyinEditor.cc:128`, `src/PYPCloudCandidates.cc:704` |
| OK | `pinyin_get_double_pinyin_auxiliary_text` | `src/PYPDoublePinyinEditor.cc:151` |
| OK | `pinyin_get_chewing_auxiliary_text` | `src/PYPBopomofoEditor.cc:425` |
| OK | `pinyin_mask_out` | `src/PYLibPinyin.cc:363,366,369,477` |
| OK | `pinyin_remember_user_input` | `src/PYLibPinyin.cc:389,402` |
| OK | `pinyin_begin_add_phrases` | `src/PYLibPinyin.cc:237,540` |
| OK | `pinyin_iterator_add_phrase` | `src/PYLibPinyin.cc:267,570` |
| OK | `pinyin_end_add_phrases` | `src/PYLibPinyin.cc:272,576` |
| OK | `pinyin_begin_get_phrases` | `src/PYLibPinyin.cc:282` |
| OK | `pinyin_iterator_has_next_phrase` | `src/PYLibPinyin.cc:289` |
| OK | `pinyin_iterator_get_next_phrase` | `src/PYLibPinyin.cc:293` |
| OK | `pinyin_end_get_phrases` | `src/PYLibPinyin.cc:303` |
| OK | `pinyin_begin_get_bigram_phrases` | `src/PYLibPinyin.cc:310` |
| OK | `pinyin_bigram_iterator_has_next_phrase` | `src/PYLibPinyin.cc:317` |
| OK | `pinyin_bigram_iterator_get_next_phrase` | `src/PYLibPinyin.cc:321` |
| OK | `pinyin_end_get_bigram_phrases` | `src/PYLibPinyin.cc:331` |

Counts: (a) called + implemented = **50**; (b) called + NOT implemented =
**1** (`pinyin_get_parsed_input_length`); (c) implemented + never called by
live code = **0** (the 50-symbol bootstrap is exactly covered by the
fork's live set, minus the one gap).

### Conditionally-compiled sites

- **Cloud input** (`ENABLE_CLOUD_INPUT_MODE`, configure option
  `--enable-cloud-input-mode`, default off): `PYPCloudCandidates.cc` is
  added to the build only under `if ENABLE_CLOUD_INPUT_MODE` in
  `src/Makefile.am` and included only under `#ifdef
  ENABLE_CLOUD_INPUT_MODE` in `src/PYPPhoneticEditor.h:46`. Its only
  libpinyin call is `pinyin_get_full_pinyin_auxiliary_text` at
  `src/PYPCloudCandidates.cc:704`. No other libpinyin call is cloud-gated.
- **Lua extension** (`IBUS_BUILD_LUA_EXTENSION`, `--disable-lua-extension`,
  default enabled when Lua is available): the Lua plugin files,
  `PYExtEditor.cc`, `PYPLuaTriggerCandidates.cc`, and
  `PYPLuaConverterCandidates.cc` make **no direct `pinyin_*` calls**. The
  suggestion editor that calls
  `pinyin_guess_predicted_candidates_with_punctuations` is compiled
  unconditionally (`src/Makefile.am` always lists
  `PYPSuggestionEditor.cc`); only the Lua-trigger/converter candidate
  providers attached to it are ifdef-gated.
- **English input** (`IBUS_BUILD_ENGLISH_INPUT_MODE`, default enabled):
  `PYEnglishDatabase.cc`, `PYEnglishEditor.cc`, and
  `PYPEnglishCandidates.cc` make **no direct `pinyin_*` calls**.
- **Table input** (`IBUS_BUILD_TABLE_INPUT_MODE`, default enabled):
  `PYTableDatabase.cc` and `PYTableEditor.cc` make **no direct
  `pinyin_*` calls**.
- All pinyin/chewing editor call sites in `PYPPhoneticEditor.cc`,
  `PYPPinyinEditor.cc`, `PYPFullPinyinEditor.cc`,
  `PYPDoublePinyinEditor.cc`, `PYPBopomofoEditor.cc`,
  `PYPLibPinyinCandidates.cc`, and `PYPSuggestionCandidates.cc` are
  otherwise unconditional.

### Dead code (`#if 0`) for completeness

These are **not** part of the live call surface, and are listed so later
phases do not re-count them:

| Dead symbol | Call sites | In oxpinyin-capi? |
|---|---|---|
| `pinyin_get_n_candidate` | `src/PYPPhoneticEditor.cc:490` | yes |
| `pinyin_get_candidate` | `src/PYPPhoneticEditor.cc:498` | yes |
| `pinyin_get_candidate_type` | `src/PYPPhoneticEditor.cc:501` | yes |
| `pinyin_choose_candidate` | `src/PYPPhoneticEditor.cc:505,512` | yes |
| `pinyin_get_candidate_nbest_index` | `src/PYPPhoneticEditor.cc:507` | yes |
| `pinyin_guess_sentence` | `src/PYPPhoneticEditor.cc:515` | yes |
| `pinyin_get_pinyin_key_rest` | `src/PYPPhoneticEditor.cc:523` | yes |
| `pinyin_get_pinyin_key_rest_positions` | `src/PYPPhoneticEditor.cc:526` | yes |
| `pinyin_get_n_pinyin` | `src/PYPPinyinEditor.cc:399` | no (not a `libpinyin.ver` export either) |
| `pinyin_get_pinyin_key` | `src/PYPPinyinEditor.cc:406` | no |
| `pinyin_get_pinyin_string` | `src/PYPPinyinEditor.cc:409` | no |

The first block is the old `PhoneticEditor::selectCandidate` under `#if 0`
at `src/PYPPhoneticEditor.cc:485`; the second is the old
`PinyinEditor::updateAuxiliaryText` under `#if 0` at
`src/PYPPinyinEditor.cc:385`. The live selection path is
`LibPinyinCandidates::selectCandidate` in `PYPLibPinyinCandidates.cc`.

## 2. Gap analysis

- Gap symbol: `pinyin_get_parsed_input_length`.
- C++ signature: `size_t pinyin_get_parsed_input_length(pinyin_instance_t *instance);`
- Fork call site: `src/PYPLibPinyinCandidates.cc:151`
  (`LibPinyinCandidates::selectCandidate`), live and unconditional.
- oxpinyin-capi header (`crates/oxpinyin-capi/pinyin.h`) declares the
  bootstrap 50 and does **not** declare this symbol. The Rust sources have
  no `#[unsafe(no_mangle)]` export for it. The only mentions inside
  oxpinyin are oracle FFI, graph comments, fixtures, and the ABI-subset
  doc; none are part of `oxpinyin-capi`.
- Origin: `git show 2c5baa9` changes
  `if (lookup_cursor == m_editor->m_text.length())` to
  `if (lookup_cursor == pinyin_get_parsed_input_length (instance))`.
  oxpinyin's `docs/findings/abi-subset.md` (tag 1.16.5) listed this symbol
  in the 29 out-of-subset exports, so the 50-symbol bootstrap contract no
  longer matches this fork's live source.

## 3. Non-symbol surface

### Header include path

The fork includes only `<pinyin.h>` from libpinyin:

- `src/PYConfig.h:30`
- `src/PYPConfig.h:32`
- `src/PYLibPinyin.cc:25`
- `src/PYPCloudCandidates.cc:31`
- `src/PYPConfig.cc:24`
- `src/PYPLibPinyinCandidates.cc:23`
- `src/PYPPhoneticEditor.h:28`
- `src/PYPSuggestionCandidates.cc:23`
- `src/PYPSuggestionEditor.h:25`

No other libpinyin install header is included. The include directory comes
from `@LIBPINYIN_CFLAGS@` (pkg-config). oxpinyin does not install a header;
its C header is checked in at
`<oxpinyin>/crates/oxpinyin-capi/pinyin.h`, so the Phase 1 experiment
would point `-I` there (or copy it into the fork).

Header compatibility findings that Phase 1 would have to resolve (these
are non-symbol compile-surface items, recorded now so they are not
discovered mid-link):

1. oxpinyin's `pinyin.h` has **no `extern "C"` guard**, but the fork is
   C++ (`AC_PROG_CXX`, `.cc` sources). Included directly, the declarations
   would get C++ linkage and the Rust `pinyin_*` symbols would not link.
   A fork-side compatibility header or an oxpinyin header patch is needed.
2. The fork's live code uses `PinyinKeyPos` at
   `src/PYPLibPinyinCandidates.cc:164` (dead code also uses `PinyinKey` at
   `src/PYPPinyinEditor.cc:405`). C++ libpinyin's `pinyin.h` aliases these
   as `typedef ChewingKey PinyinKey; typedef ChewingKeyRest PinyinKeyPos;`.
   oxpinyin's header declares `ChewingKey`/`ChewingKeyRest` but not those
   two aliases.
3. The fork uses libpinyin option constants and phrase-index macros that
   oxpinyin's header does not define:
   `PINYIN_INCOMPLETE`, `ZHUYIN_INCOMPLETE`, `PINYIN_CORRECT_ALL`,
   `PINYIN_CORRECT_*`, `PINYIN_AMB_*`, `USE_TONE`, `USE_DIVIDED_TABLE`,
   `USE_RESPLIT_TABLE`, `DYNAMIC_ADJUST`, `DOUBLE_PINYIN_DEFAULT`,
   `ZHUYIN_DEFAULT`, `PHRASE_INDEX_LIBRARY_MASK`,
   `PHRASE_INDEX_MAKE_TOKEN`, `USER_DICTIONARY`, `ADDON_DICTIONARY`,
   `NETWORK_DICTIONARY`, and `null_token`. See `src/PYPConfig.cc`,
   `src/PYLibPinyin.cc`, and `src/PYConfig.h`.
4. oxpinyin's header uses `uint32_t`/`uint8_t`/`size_t` and defines
   `guint`/`gchar` itself, which is enough for those types; enum
   discriminants used by the fork match. Function signatures that take an
   enum in C++ libpinyin take a plain `int` in oxpinyin for scheme setters;
   enum-to-`int` conversion is legal C++, so that part is fine.

### pkg-config probe and link line

- `configure.ac:69-71`: `PKG_CHECK_MODULES(LIBPINYIN, [libpinyin >= 2.9.92],
  [enable_libpinyin=yes])`.
- `configure.ac:73`: `LIBPINYIN_DATADIR=$PKG_CONFIG
  --variable=pkgdatadir libpinyin`, substituted into the source as
  `-DLIBPINYIN_DATADIR="@LIBPINYIN_DATADIR@/data"` at
  `src/Makefile.am:174`.
- `src/Makefile.am:148`: `@LIBPINYIN_CFLAGS@` is in
  `ibus_engine_libpinyin_CXXFLAGS`.
- `src/Makefile.am:169`: `@LIBPINYIN_LIBS@` is in
  `ibus_engine_libpinyin_LDADD`. The C++ install observed in this
  workspace supplies `-L.../libpinyin/lib64 -lpinyin -lglib-2.0`.
- There is **no CMake build** in this fork (`configure.ac`/automake only),
  so the Phase 1 build-system change is autotools-only.
- oxpinyin has no `pinyin.pc` and cargo does not install one. Phase 1
  would either write `oxpinyin-patches/pinyin.pc` into the fork branch or
  set `LIBPINYIN_CFLAGS`/`LIBPINYIN_LIBS` explicitly for configure.
- Link target for oxpinyin: `cargo build --release -p oxpinyin-capi`
  produces `<oxpinyin>/target/release/libpinyin_capi.so`; the link line
  would use `-L<oxpinyin>/target/release -lpinyin_capi`.

### Runtime data expectations

Fork side (`src/PYLibPinyin.cc:69,127`):
- System dir argument is `LIBPINYIN_DATADIR`, computed as
  `pkgdatadir(libpinyin) + "/data"`.
- User dirs are `$XDG_CACHE_HOME/ibus/libpinyin` and
  `$XDG_CACHE_HOME/ibus/libbopomofo`, created mode 0700.
- C++ libpinyin expects `table.conf`, the system `.bin` indexes, and
  `bigram.db` in the system dir; the workspace's pinned C++ install uses
  Tkrzw-format files under
  `/home/sheng/.local/opt/libpinyin/lib64/libpinyin/data`.

oxpinyin-capi side (`crates/oxpinyin-capi/src/state.rs:137-156`):
- `pinyin_init(systemdir, userdir)` opens `pinyin_index.redb`,
  `phrase_index.redb`, and `bigram.redb` from `systemdir`.
- `table.conf` is optional and only overrides the pinned λ (`0.312699`);
  absence is accepted.
- User state is one file, `user_store.redb`, in `userdir` (redb; training
  commits are durable before `pinyin_save`).
- The fetched pinned model cache
  (`tools/model/fetch-model.sh`, default `<oxpinyin>/target/model20/extracted`)
  is **raw input** (`interpolation2.text` + `.table` files); it is not
  directly readable by `oxpinyin-capi`. The deployable system dir is the
  `oxpinyin-migrate export` output containing the three `.redb` files.
- `pinyin_load_addon_phrase_library` is a documented provisional no-op
  (always `false`) in oxpinyin-capi; the fork ignores the return value, so
  addon dictionaries would silently be absent.

### GSettings schema

- Installed by `data/Makefile.am` via `GLIB_GSETTINGS`:
  `data/com.github.libpinyin.ibus-libpinyin.gschema.xml`.
- Two schema IDs are used by the engine:
  `com.github.libpinyin.ibus-libpinyin.libpinyin`
  (`src/PYPConfig.cc`, PinyinConfig) and
  `com.github.libpinyin.ibus-libpinyin.libbopomofo`
  (`src/PYPConfig.cc`, BopomofoConfig).
- A user-local Phase 2 run needs the schema compiled and visible, e.g.
  `glib-compile-schemas $HOME/.local/share/glib-2.0/schemas` and
  `GSETTINGS_SCHEMA_DIR` set, regardless of the backend library.

## Decision record

- Gap bucket (b) is non-empty: `pinyin_get_parsed_input_length`
  (`src/PYPLibPinyinCandidates.cc:151`) is called but not implemented by
  oxpinyin-capi.
- Action: **STOP after Phase 0**; do not patch oxpinyin locally, do not
  modify the fork build, do not build/link/smoke, do not run parity.
- Implementations for later decision: (i) add the symbol to
  oxpinyin-capi as a local patch + patch file under `oxpinyin-patches/`,
  (ii) a fork-side compatibility shim, or (iii) maintain the call-surface
  delta another way chosen by the maintainer.
