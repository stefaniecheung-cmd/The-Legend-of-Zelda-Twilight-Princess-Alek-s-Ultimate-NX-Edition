#!/usr/bin/env python3
"""Extract candidate user-visible display strings from a dusk UI .cpp file.

Only the unambiguous display contexts are matched:
  - `.title = "..."`            (pane/group/modal titles)
  - `.text  = "..."`           (button/label text via add_button / add_group_button)
  - `push_toast({.title = "..."})`
  - `make_unique<Button>(..., "...")` and `Button(..., "...")`
  - `return "...";` in label/name helper functions

Output: one TSV line per candidate:
    LINE<TAB>KIND<TAB>EN

KIND is one of: title, text, toast, button, return.
We deliberately skip:
  - constexpr enum-name arrays (ambiguous mapping / comparison risk)
  - strings containing { } / \\ . :: (format strings, paths, identifiers)
"""
import sys
import re

PATH = sys.argv[1]

patterns = [
    ("title", re.compile(r'\.title\s*=\s*"([^"{}]*)"')),
    ("text", re.compile(r'\.text\s*=\s*"([^"{}]*)"')),
    ("toast", re.compile(r'push_toast\(\{\s*\.title\s*=\s*"([^"{}]*)"')),
    ("button", re.compile(r'(?:make_unique<Button>|Button)\s*\([^,]+,\s*"([^"{}]*)"')),
]

# return "..."; (label/name helpers)
ret_re = re.compile(r'return\s+"([^"{}]*)"\s*;')

seen = set()
out = []
with open(PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, start=1):
        for kind, pat in patterns:
            m = pat.search(line)
            if m:
                en = m.group(1)
                if not en.strip():
                    continue
                key = (i, kind, en)
                if key in seen:
                    continue
                seen.add(key)
                out.append((i, kind, en))
                break
        else:
            m = ret_re.search(line)
            if m:
                en = m.group(1)
                if not en.strip():
                    continue
                key = (i, "return", en)
                if key in seen:
                    continue
                seen.add(key)
                out.append((i, "return", en))

for i, kind, en in out:
    print(f"{i}\t{kind}\t{en}")
print(f"# total candidates: {len(out)}", file=sys.stderr)
