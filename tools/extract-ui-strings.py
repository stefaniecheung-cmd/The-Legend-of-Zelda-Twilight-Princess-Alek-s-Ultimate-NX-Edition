#!/usr/bin/env python3
"""Extract the UI strings this port renders, as dictionary keys.

The port writes UI text as C++ string literals, so the literal *is* the key the
RmlUi translate callback will see at run time. Two things make a naive regex
scan wrong:

  * adjacent literals concatenate at compile time ("a " "b" -> "a b"), and
    almost every long help text is written that way;
  * text can sit across lines, so line-by-line scanning shreds sentences.

So the scanner walks the file, skips comments, and greedily joins runs of
adjacent literals before filtering.

Usage: python tools/extract-ui-strings.py <repo-root> <out.json>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCAN_DIRS = ("src/dusk/ui", "src/dusk/mods")

ESCAPES = {
    "n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\",
    '"': '"', "'": "'", "?": "?", "a": "\a", "b": "\b", "f": "\f", "v": "\v",
}

# Anything that is clearly not interface copy.
REJECT_SUBSTRINGS = (
    "%s", "%d", "{}", "{0}", "{1}", "http://", "https://", "::",
    "sdmc:", "switch/", ".rcss", ".rml", ".ttf", ".png", ".json", ".iso",
    ".rvz", ".wia", ".gcz", "TARGET_PC", "__SWITCH__", "#shader", "#",
)
REJECT_EXACT = {"OK", "Yes", "No", "On", "Off", "Auto", "None", "Custom", "Back", "Cancel"}


def strip_comments(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == '"':
                    j += 1
                    break
                j += 1
            out.append(text[i:j])
            i = j
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def decode(body: str) -> str:
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\" or i + 1 >= len(body):
            out.append(ch)
            i += 1
            continue
        nxt = body[i + 1]
        if nxt == "x":
            j = i + 2
            while j < len(body) and body[j] in "0123456789abcdefABCDEF":
                j += 1
            out.append(chr(int(body[i + 2:j], 16)) if j > i + 2 else "x")
            i = j
            continue
        if nxt == "u":
            j = i + 2
            while j < len(body) and body[j] in "0123456789abcdefABCDEF":
                j += 1
            out.append(chr(int(body[i + 2:j], 16)) if j > i + 2 else "u")
            i = j
            continue
        out.append(ESCAPES.get(nxt, nxt))
        i += 2
    return "".join(out)


STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def literals_in(text: str):
    """Yield joined runs of adjacent string literals."""
    pos = 0
    while True:
        m = STRING_RE.search(text, pos)
        if not m:
            return
        parts = [m.group(1)]
        end = m.end()
        while True:
            j = end
            while j < len(text) and text[j] in " \t\r\n":
                j += 1
            if j >= len(text) or text[j] != '"':
                break
            nxt = STRING_RE.match(text, j)
            if not nxt:
                break
            parts.append(nxt.group(1))
            end = nxt.end()
        yield "".join(decode(p) for p in parts), m.start()
        pos = end


def keep(s: str) -> bool:
    if not (3 <= len(s) <= 400):
        return False
    if s in REJECT_EXACT:
        return False
    if not re.search(r"[A-Za-z]{2}", s):
        return False
    for bad in REJECT_SUBSTRINGS:
        if bad in s:
            return False
    if "/" in s or "\\" in s:
        return False
    if s != s.strip():
        return False
    # Needs a space, or to be a capitalised word that is not an identifier.
    if " " not in s:
        if not s[:1].isupper() or re.fullmatch(r"[A-Za-z0-9_]+", s) and s.islower():
            return False
        if re.fullmatch(r"[A-Z0-9_]+", s):  # CONSTANT
            return False
    if re.fullmatch(r"[a-z][a-z0-9_.]*", s):
        return False
    return True


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    found: dict[str, list[str]] = {}
    for rel in SCAN_DIRS:
        for path in sorted((root / rel).rglob("*.cpp")):
            text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
            for literal, _ in literals_in(text):
                if keep(literal):
                    found.setdefault(literal, []).append(str(path.relative_to(root)))

    ordered = dict(sorted(found.items(), key=lambda kv: (-len(kv[1]), kv[0])))
    out_path.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ordered)} strings -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
