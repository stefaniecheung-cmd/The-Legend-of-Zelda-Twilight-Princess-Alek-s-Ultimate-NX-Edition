#!/usr/bin/env python3
"""
Auto-replace hardcoded English UI strings in Dusklight C++ sources with [TOKEN]
placeholders, based on res/i18n/en.xml. Only replaces full string-literal matches
of UI display text; leaves code identifiers, paths and log messages alone.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN_XML = ROOT / "res" / "i18n" / "en.xml"
UI_DIRS = [
    ROOT / "src" / "dusk" / "ui",
]

def load_en_map():
    tree = ET.parse(EN_XML)
    root = tree.getroot()
    # map: english_text -> TOKEN (longest first to avoid partial matches)
    m = {}
    for entry in root.findall("entry"):
        key = entry.get("key")
        text = (entry.text or "").strip()
        # skip empty, markup-only, or already-token-like
        if not text or text.startswith("[") or "<" in text:
            continue
        m[text] = key
    # sort by length descending so longer phrases win
    return dict(sorted(m.items(), key=lambda kv: len(kv[0]), reverse=True))

# C++ string literal: "..." with escaped chars
STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')

def replacer_factory(emap):
    # Precompile: for each file, find string literals and look up exact match
    def replace_in_file(path: Path):
        text = path.read_text(encoding="utf-8")
        hits = []
        def sub(match):
            raw = match.group(1)
            # unescape common sequences for matching
            decoded = raw.replace("\\n", "\n").replace("\\\"", '"').replace("\\\\", "\\")
            decoded = decoded.strip()
            if decoded in emap:
                # already a token? skip
                if raw.startswith("["):
                    return match.group(0)
                hits.append((decoded, emap[decoded]))
                return f'"[{emap[decoded]}]"'
            return match.group(0)
        new_text = STRING_RE.sub(sub, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
        return hits
    return replace_in_file

def main():
    emap = load_en_map()
    print(f"Loaded {len(emap)} English strings from en.xml")
    replace = replacer_factory(emap)
    total = 0
    per_file = {}
    for d in UI_DIRS:
        for f in sorted(d.glob("*.cpp")):
            hits = replace(f)
            if hits:
                per_file[f.name] = len(hits)
                total += len(hits)
    print(f"\nReplaced {total} string literals across {len(per_file)} files:")
    for name, count in sorted(per_file.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count} replacements")

if __name__ == "__main__":
    main()
