#!/usr/bin/env python3
"""Build res/i18n/{en,zh-cn}.xml from the extracted strings plus a translation map.

en.xml is the identity map: key = the literal this port renders. zh-cn.xml uses
the translation when one exists and falls back to the English string otherwise,
so a partially translated dictionary never blanks out the UI.

Usage: python tools/build-i18n.py <ui_clean.json> <translations.json> <out-dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HEADER = """<?xml version="1.0" encoding="utf-8"?>
<!--
  Interface strings for the Switch port.

  The port renders UI text from C++ string literals and RmlUi hands the
  finished text to TranslateString, so the English literal *is* the key. No
  call site is tokenised, which is what keeps this file independent of
  upstream edits: a string that is not listed here simply stays English.

  {note}
-->
<i18n language="{language}">
"""


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write(path: Path, language: str, entries: list[tuple[str, str]], note: str) -> None:
    lines = [HEADER.format(language=language, note=note)]
    for key, value in entries:
        lines.append(f'  <entry key="{esc(key)}">{esc(value)}</entry>')
    lines.append("</i18n>\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    strings_path, translations_path, out_dir = (Path(a) for a in sys.argv[1:4])

    keys = json.loads(strings_path.read_text(encoding="utf-8"))
    translations = json.loads(translations_path.read_text(encoding="utf-8"))

    # [TOKEN] entries: some call sites render "[TOKEN]" strings (built by
    # concatenation or replaced wholesale); i18n::translate() strips the
    # brackets and looks the bare token up in the same dictionary. tokens.json
    # carries {"token": {"en": ..., "zh": ...}} for every token the source
    # renders; en.xml gets the English text so the English UI never shows a
    # raw "[TOKEN]", zh-cn.xml gets the Chinese when one exists.
    tokens_path = strings_path.parent / "tokens.json"
    token_entries_en: list[tuple[str, str]] = []
    token_entries_zh: list[tuple[str, str]] = []
    if tokens_path.exists():
        tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
        token_entries_en = [(t, v["en"]) for t, v in sorted(tokens.items())]
        token_entries_zh = [(t, v.get("zh") or v["en"]) for t, v in sorted(tokens.items())]

    out_dir.mkdir(parents=True, exist_ok=True)
    ordered = sorted(keys)

    write(
        out_dir / "en.xml",
        "en",
        [(k, k) for k in ordered] + token_entries_en,
        "English is the source language: the keys and the values are the same text.",
    )

    translated = [(k, translations[k]) for k in ordered if k in translations]
    fallback = [k for k in ordered if k not in translations]
    translated_tokens = sum(1 for t, v in token_entries_zh if v != dict(token_entries_en)[t])
    write(
        out_dir / "zh-cn.xml",
        "zh-cn",
        [(k, translations.get(k, k)) for k in ordered] + token_entries_zh,
        f"{len(translated)} of {len(ordered)} strings translated plus "
        f"{translated_tokens}/{len(token_entries_zh)} [TOKEN] entries; the rest fall back to English.",
    )

    print(
        f"en.xml/zh-cn.xml: {len(ordered)} entries + {len(token_entries_en)} tokens, "
        f"{len(translated)} translated, {len(fallback)} fallback"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
