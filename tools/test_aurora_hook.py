"""Validate cmake/AuroraI18nHook.cmake against a pristine copy of extern/aurora.

This parses the real anchors out of the .cmake file (rather than a duplicated
list) and replays the same literal replacement CMake would do, so a typo in an
anchor or a non-idempotent patch shows up before the user configures.

Usage: python tools/test_aurora_hook.py <aurora-source-dir> [--work <tmp>]
"""

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "cmake" / "AuroraI18nHook.cmake"

BRACKET = re.compile(r"\[==\[(.*?)\]==\]", re.S)
SET_F = re.compile(r'set\(_f "\$\{_dusk_aurora\}/([^"]+)"\)')
REPLACE_CALL = re.compile(r"_dusk_i18n_replace\(\"\$\{_f\}\"\s*(\[==\[.*?\]==\])\s*(\[==\[.*?\]==\])\s*\)", re.S)


def parse_patches():
    text = SCRIPT.read_text(encoding="utf-8")
    patches = []
    current = None
    # Walk the file in order, remembering the most recent `set(_f ...)`.
    events = []
    for m in SET_F.finditer(text):
        events.append((m.start(), "file", m.group(1)))
    for m in REPLACE_CALL.finditer(text):
        args = BRACKET.findall(m.group(0))
        events.append((m.start(), "replace", (args[0], args[1])))
    events.sort()
    for _, kind, payload in events:
        if kind == "file":
            current = payload
        else:
            patches.append((current, payload[0], payload[1]))
    return patches


def apply(path, old, new):
    src = path.read_text(encoding="utf-8")
    first = src.find(old)
    if first < 0:
        return "anchor not found"
    if src.find(old, first + 1) >= 0:
        return "anchor not unique"
    path.write_text(src.replace(old, new, 1), encoding="utf-8")
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    source = Path(sys.argv[1])
    work = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "_hooktest"

    if work.exists():
        shutil.rmtree(work)
    tree = work / "extern" / "aurora"
    for rel in {"lib/rmlui/SystemInterface_Aurora.h", "lib/rmlui/SystemInterface_Aurora.cpp",
                "include/aurora/rmlui.hpp", "lib/rmlui.cpp"}:
        dst = tree / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(source / rel, dst)

    patches = parse_patches()
    expected_files = {p[0] for p in patches}
    print(f"parsed {len(patches)} replacement(s) across {len(expected_files)} file(s)")
    if expected_files != {"lib/rmlui/SystemInterface_Aurora.h", "lib/rmlui/SystemInterface_Aurora.cpp",
                          "include/aurora/rmlui.hpp", "lib/rmlui.cpp"}:
        print("FAIL: unexpected file set", sorted(expected_files))
        return 1

    failures = []
    for rel, old, new in patches:
        err = apply(tree / rel, old, new)
        if err:
            failures.append(f"{rel}: {err}")

    if failures:
        print("FAIL - anchors do not match the pristine tree:")
        for f in failures:
            print("  !", f)
        return 1

    # Second configure: the .cmake skips any file carrying the marker. Simulate
    # exactly that guard, then assert nothing would be written again.
    for rel in expected_files:
        body = (tree / rel).read_text(encoding="utf-8")
        if "dusk-i18n" not in body:
            print(f"FAIL: {rel} has no dusk-i18n marker; the idempotency guard cannot skip it")
            return 1

    repatched = []
    for rel, old, new in patches:
        body = (tree / rel).read_text(encoding="utf-8")
        if "dusk-i18n" in body:
            continue  # guard skips this file, as on a second cmake run
        repatched.append(rel)
    if repatched:
        print("FAIL: second configure would patch again:", repatched)
        return 1

    print("OK: all anchors matched exactly once, all files carry the marker, second run is a no-op")
    print(f"patched tree: {tree}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
