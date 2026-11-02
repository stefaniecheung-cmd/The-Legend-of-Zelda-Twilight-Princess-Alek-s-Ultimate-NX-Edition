# Launcher localization (zh-cn)

The launcher UI is rendered by RmlUi and every user-visible string is authored as
a `[TOKEN]` placeholder. RmlUi passes each text node to
`Rml::SystemInterface::TranslateString` before instancing it, and that call is
routed into `dusk::ui::i18n`, which looks the token up in `res/i18n/<lang>.xml`.

```
RML text "[SETTINGS]"
   └─ RmlUi Factory::InstanceElementText
        └─ SystemInterface_Aurora::TranslateString   (added by cmake/AuroraI18nHook.cmake)
             └─ aurora::rmlui callback → i18n::translate()
                  └─ res/i18n/zh-cn.xml  →  "设置"
```

## Moving parts

| Piece | Where | Notes |
|---|---|---|
| Translator + parser | `src/dusk/ui/i18n.{hpp,cpp}` | self-contained; needs only aurora/borealis/dusk/io |
| Dictionaries | `res/i18n/{en,zh-cn,fr,ja}.xml` | `<entry key="TOKEN">value</entry>` |
| CJK glyphs | `res/HarmonyOS_Sans*.ttf` | loaded as **fallback** faces, so the Latin UI font keeps its look |
| RmlUi hook | `cmake/AuroraI18nHook.cmake` | patches `extern/aurora` in place at configure time, idempotent |
| Manual fallback for the hook | `patches/aurora-translate-hook/` | only needed if the CMake step warns |
| Wiring | `src/dusk/ui/ui.cpp` | register callback → `i18n::initialize()` → `set_language("zh-cn")` |
| Tokenizers | `tools/*.py` | see below |
| Gate | `tools/check_i18n_tokens.py` | run before every commit |

## Rules that are easy to get wrong

1. **A token must never contain `{}`.** `fmt::format("[TOKEN]", arg)` formats first
   and translates later, so the argument is silently dropped. Translate the words
   only, then append: `fmt::format("{} {}", i18n::tr("[PAGE]"), n)`.
2. **Translated values must not contain `{`, `}`, or a stray `<`.** When a
   substitution happens RmlUi re-parses the result as RML, so braces become data
   expressions and `<` starts a tag. `<br/>` and friends are fine.
3. **Only text nodes are translated.** A token inside an attribute
   (`title="[X]"`, `placeholder="[X]"`) is never seen by the translator; call
   `i18n::tr()` in C++ there instead.
4. **Do not tokenize identifiers.** Search-filter keys, `SetAttribute("id", …)`,
   enum config values (`"auto"`, `"d3d12"`), log messages and `ZoneScoped` labels
   must stay literal. The tokenizers skip these by line marker, but review diffs.
5. **Missing dictionary entry = `[TOKEN]` on screen.** That is deliberate: it is
   obvious in a screenshot, and `check_i18n_tokens.py` fails the build gate first.

## Workflow for a new screen

```sh
# 1. see what the dictionary already covers (reuse before inventing keys)
python tools/auto_tokenize.py src/dusk/ui/<screen>.cpp --report unmatched.tsv
python tools/auto_tokenize.py src/dusk/ui/<screen>.cpp --apply

# 2. translate the leftovers into a TSV:  KEY<TAB>english<TAB>中文
python tools/add_i18n_entries.py my_tokens.tsv

# 3. gate
python tools/check_i18n_tokens.py
```

`apply_*_tokens.py` scripts exist for the screens that needed ordered, verified
replacement with per-string occurrence assertions (`settings.cpp`,
`mod_browser.cpp`). They are replayable: after merging upstream, re-running them
re-applies the tokenization instead of hand-merging 200 string edits.

## Adding a language

1. Add `res/i18n/<tag>.xml` with the same key set (`--sync-languages` in the
   checker copies missing keys from `en.xml`).
2. Add the tag to `i18n::set_language` and, if the script needs different glyphs,
   to `use_harmonyos_font`.
3. Call `i18n::set_language("…")` in `ui.cpp` — currently hard-coded to `zh-cn`
   because this build is Chinese-first. `set_language` falls back to English when
   a dictionary is missing, so a bad tag degrades instead of showing placeholders.

## Known gap

The game language used by the disc (`getSettings().game.language`) is a separate
setting and is untouched by this layer; the launcher UI language has no settings
toggle yet.
