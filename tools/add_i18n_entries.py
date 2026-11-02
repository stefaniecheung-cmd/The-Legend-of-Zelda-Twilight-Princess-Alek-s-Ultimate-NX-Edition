#!/usr/bin/env python3
"""Batch-insert i18n entries into all four dictionaries (en/zh-cn/fr/ja).

Input: a TSV file (UTF-8). Each non-empty line:
    KEY<TAB>EN<TAB>ZH

- en.xml   : value = EN
- zh-cn.xml: value = ZH
- fr.xml   : value = EN (fallback so no literal [KEY] leaks)
- ja.xml   : value = EN (fallback)

Entries are inserted before </localization>. If a key already exists its
value is replaced. XML entities in EN/ZH are escaped (& < > " ').

Usage:
    python tools/add_i18n_entries.py path/to/entries.tsv
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N_DIR = os.path.join(ROOT, "res", "i18n")

LANGS = {
    "en": "en",
    "zh-cn": "zh-cn",
    "fr": "fr",
    "ja": "ja",
}


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def update_file(lang: str, entries: list[tuple[str, str]], dry: bool = False) -> str:
    path = os.path.join(I18N_DIR, f"{lang}.xml")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    existing: dict[str, str] = {}
    cursor = 0
    while True:
        open_tag = content.find("<entry", cursor)
        if open_tag == -1:
            break
        key_attr = content.find('key="', open_tag)
        key_begin = key_attr + 5
        key_end = content.find('"', key_begin)
        key = content[key_begin:key_end]
        tag_end = content.find(">", key_end)
        entry_close = content.find("</entry>", tag_end + 1)
        val_begin = tag_end + 1
        val = content[val_begin:entry_close]
        existing[key] = (val_begin, entry_close)  # not used for replace, simplified below
        cursor = entry_close + 8

    # Remove any existing entries for the keys we are (re)inserting.
    keys_to_replace = {k for k, _ in entries}
    cursor = 0
    while True:
        open_tag = content.find("<entry", cursor)
        if open_tag == -1:
            break
        key_attr = content.find('key="', open_tag)
        if key_attr == -1 or key_attr > open_tag + 20:
            cursor = open_tag + 6
            continue
        key_begin = key_attr + 5
        key_end = content.find('"', key_begin)
        key = content[key_begin:key_end]
        tag_end = content.find(">", key_end)
        entry_close = content.find("</entry>", tag_end + 1)
        if key in keys_to_replace:
            # also strip a trailing newline kept before the tag if present
            start = open_tag
            while start > 0 and content[start - 1] in ("\n", " "):
                start -= 1
            content = content[:start] + content[entry_close + 8:]
            cursor = start
        else:
            cursor = entry_close + 8

    # Build replacement blocks
    new_blocks = []
    for key, value in entries:
        new_blocks.append(f'  <entry key="{key}">{escape(value)}</entry>')

    block_text = "\n".join(new_blocks) + "\n"

    if "</localization>" in content:
        insert_at = content.rfind("</localization>")
        content = content[:insert_at] + block_text + content[insert_at:]
    else:
        content = content.rstrip() + "\n" + block_text + "</localization>\n"

    if not dry:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return path


def main():
    if len(sys.argv) < 2:
        print("usage: add_i18n_entries.py entries.tsv")
        sys.exit(1)
    tsv_path = sys.argv[1]
    entries: list[tuple[str, str, str]] = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                # allow KEY<TAB>ZH with english fallback = key
                if len(parts) == 2:
                    parts = [parts[0], parts[0], parts[1]]
                else:
                    print(f"SKIP malformed: {line!r}")
                    continue
            key, en, zh = parts[0], parts[1], parts[2]
            if not key:
                continue
            entries.append((key, en, zh))

    if not entries:
        print("No entries to add.")
        return

    for lang, _ in LANGS.items():
        # en -> en value; fr/ja -> en fallback; zh-cn -> zh value
        lang_entries = []
        for key, en, zh in entries:
            val = en if lang in ("en", "fr", "ja") else zh
            lang_entries.append((key, val))
        update_file(lang, lang_entries)
        print(f"updated {lang}.xml ({len(lang_entries)} entries)")


if __name__ == "__main__":
    main()
