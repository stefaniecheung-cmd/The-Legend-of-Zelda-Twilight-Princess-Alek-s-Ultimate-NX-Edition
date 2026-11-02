#!/usr/bin/env python3
"""Generic i18n tokenizer: reuse existing dictionary entries.

For every double-quoted literal in a source file, if the literal's text
exactly matches a value already present in res/i18n/en.xml, replace it with
"[KEY]". Only existing translations are reused, so nothing needs new wording
and no [KEY] can leak untranslated text.

Safety: lines that look like logs, telemetry scopes, RML class/id names,
search-filter logic keys, includes, or asset paths are skipped entirely.

Usage:
    python tools/auto_tokenize.py src/dusk/ui/foo.cpp            # dry run
    python tools/auto_tokenize.py src/dusk/ui/foo.cpp --apply
    python tools/auto_tokenize.py src/dusk/ui/foo.cpp --report out.tsv
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Substrings that mark a line as "not user-visible text".
SKIP_LINE = (
    "DuskLog",
    "BrowserLog",
    "Log.",
    "ZoneScoped",
    "TracyZone",
    "SetClass",
    "add_class",
    "->class",
    ".classList",
    "#include",
    'SetAttribute("class"',
    'SetAttribute("id"',
    "fmt::format_error",
    "static_assert",
)

# Contexts where a quoted literal is an identifier rather than display text.
SKIP_LINE_MARKERS = (
    ".key = ",
    ".id = ",
    'SetAttribute("id"',
    'set_attribute("id"',
    'SetAttribute("class"',
)

# Literals that are almost certainly identifiers / assets / CSS.
IDENTIFIER_RE = re.compile(
    r"^[a-z0-9_\-./{}.]+$"  # lowercase, dots, dashes -> css class, path, token
)


def load_reverse_map():
    """value -> key, preferring the shortest key for stability."""
    rev = {}
    for e in ET.parse(ROOT / "res/i18n/en.xml").getroot():
        key, val = e.get("key"), e.text or ""
        if not key or not val:
            continue
        if val not in rev or len(key) < len(rev[val]):
            rev[val] = key
    return rev


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = Path(sys.argv[1])
    apply = "--apply" in sys.argv
    report = None
    if "--report" in sys.argv:
        report = Path(sys.argv[sys.argv.index("--report") + 1])

    rev = load_reverse_map()
    lines = target.read_text(encoding="utf-8").split("\n")
    changes, unmatched = [], []

    lit = re.compile(r'"((?:[^"\\]|\\.)*)"')
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if any(mark in line for mark in SKIP_LINE + SKIP_LINE_MARKERS):
            continue
        for m in lit.finditer(line):
            text = m.group(1)
            key = rev.get(text)
            if key:
                changes.append((idx, text, key, line))
            elif (" " in text or text[:1].isupper()) and not IDENTIFIER_RE.match(text):
                unmatched.append((idx, text))

    # apply
    if apply:
        out = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("//") or any(mark in line for mark in SKIP_LINE + SKIP_LINE_MARKERS):
                out.append(line)
                continue

            def sub(m):
                text = m.group(1)
                key = rev.get(text)
                return f'"[{key}]"' if key else m.group(0)

            out.append(lit.sub(sub, line))
        target.write_text("\n".join(out), encoding="utf-8")

    print(f"{target.name}: {len(changes)} reusable match(es), {len(unmatched)} unmatched display-ish string(s)")
    for idx, text, key, line in changes[:400]:
        print(f"  {idx:5d}  [{key}]  <- {text!r}")
    if unmatched:
        print("  --- unmatched (need manual keys) ---")
        seen = set()
        for idx, text in unmatched:
            if text in seen:
                continue
            seen.add(text)
            print(f"  {idx:5d}  {text!r}")
        if report:
            with open(report, "w", encoding="utf-8") as f:
                for idx, text in unmatched:
                    f.write(f"{idx}\t{text}\n")
    if apply:
        print("APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
