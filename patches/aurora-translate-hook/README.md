# aurora translate hook (manual fallback)

`cmake/AuroraI18nHook.cmake` applies this patch automatically at configure time.
You only need this directory if that step reported a warning — for example when
`extern/aurora` has local edits, or when the aurora submodule was updated and the
anchors in the script no longer match.

## Why the patch exists

RmlUi passes **every text node** through `Rml::SystemInterface::TranslateString`
before instancing it (`Source/Core/Factory.cpp`, `Factory::InstanceElementText`).
That is the only place where a localization layer can intercept text that the UI
builds at run time — including text set with `SetInnerRML` after a document has
loaded.

aurora ships the `SystemInterface` implementation (`SystemInterface_Aurora`,
derived from RmlUi's `SystemInterface_SDL`) but exposes no way to install a
translate callback. These four files add one:

| File | Change |
|---|---|
| `lib/rmlui/SystemInterface_Aurora.h` | declare `TranslateString` override, `SetTranslateCallback`, and the stored `std::function` |
| `lib/rmlui/SystemInterface_Aurora.cpp` | implement both; falls back to "copy input, return 0" when no callback is set |
| `include/aurora/rmlui.hpp` | public `aurora::rmlui::set_translate_callback(...)` |
| `lib/rmlui.cpp` | forward the callback to the live system interface |

The game-side wiring is in `src/dusk/ui/ui.cpp` and is compiled only when
`DUSK_I18N_AURORA_HOOK` is defined, which `cmake/AuroraI18nHook.cmake` sets on
success. If the hook is missing, the build still succeeds and the UI stays
English.

## How to apply by hand

Copy the four files over the submodule, keeping the paths:

```sh
cp -r patches/aurora-translate-hook/lib       extern/aurora/
cp -r patches/aurora-translate-hook/include   extern/aurora/
```

Then reconfigure. The script detects the `dusk-i18n` marker and leaves the files
alone.

## Contract when writing translations

Returning a non-zero substitution count tells RmlUi the result is RML and it
re-parses it as markup. Therefore **translated values must not contain `<`**, and
must not contain `{` / `}` (RmlUi treats those as data expressions).
`tools/check_i18n_tokens.py` enforces both rules.

The patch is against aurora `7bb64f8f807b747e019c074b2a6d7b5e370f2fc1`, which
vendors RmlUi `encounter/RmlUi@f00a0fee` — the revision where
`SystemInterface::TranslateString(String&, const String&)` exists.
