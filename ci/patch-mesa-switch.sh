#!/bin/bash
# The NVK driver build runs in a Linux container through mesa-switch's
# build-switch.sh, which installs its own rustc wrapper. That wrapper only
# supplies an ELF aarch64 target when it detects the Windows/MSYS host; on
# Linux RUST_TARGET stays empty, rustc compiles for x86_64-unknown-linux-gnu
# and every Mesa Rust crate (libnil's format table, compiler_builtins, ...)
# lands inside libvulkan.a as an EM:62 object. Linking the NRO then stops with
#   "Relocations in generic ELF (EM: 62)"
# for each of the Rust members it needs.
#
# Fix, in two parts:
#   1. Pin the ELF aarch64 target the wrapper injects (and fetch its std once;
#      the base image only ships rust-src).
#   2. Meson's cross build compiles the proc-macro chain (paste, syn, ...) for
#      the BUILD machine, but meson never passes --target itself, so the
#      wrapper cannot tell build-machine from target-machine invocations.
#      Mark every build-machine subproject (native: true or rust.proc_macro)
#      with a --cfg and have the wrapper skip the pin when it sees it.
set -eu

root="${1:-mesa-switch}"
wrapper="$root/rustc-switch-wrapper.sh"
if [ ! -f "$wrapper" ]; then
    echo "no rustc wrapper at $wrapper" >&2
    exit 1
fi

python3 - "$root" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
wrapper = root / "rustc-switch-wrapper.sh"

# --- 1. the rustc wrapper ------------------------------------------------
text = wrapper.read_text()

default_old = "RUST_TARGET=${MESA_SWITCH_RUST_TARGET:-}"
default_new = "RUST_TARGET=${MESA_SWITCH_RUST_TARGET:-aarch64-unknown-linux-gnu}"
if default_old not in text:
    sys.exit("rustc wrapper default target line not found")
text = text.replace(default_old, default_new, 1)

exec_old = 'if [ -n "$RUST_TARGET" ]; then\n    exec "$RUSTC_BIN" --target="$RUST_TARGET" "$@"\nfi'
ensure = '''# The base image ships rust-src but no std for this target, so rustc would
# stop with "can't find crate for `core`". Install it once per container.
marker="/tmp/.mesa-switch-rust-target-$(echo "$RUST_TARGET" | tr / _)"
if [ ! -f "$marker" ]; then
    "$(dirname "$RUSTC_BIN")/rustup" target add "$RUST_TARGET" >/dev/null 2>&1 || true
    : > "$marker"
fi

# Meson compiles the proc-macro chain and every native: true subproject for
# the BUILD machine but never passes --target itself, so the only machine
# signal available is the marker this script injects into those meson.build
# files (and the crate-type of a proc-macro).  Without the skip, build-machine
# crates get aarch64 objects and the host link dies with
#   rust-lld: error: --fix-cortex-a53-843419 is only supported on AArch64
# or, later, with E0461 "couldn't find crate ... with expected target triple".
for arg in "$@"; do
    case "$arg" in
        *proc-macro*|mesa_switch_build_machine) RUST_TARGET= ;;
    esac
done

if [ -n "$RUST_TARGET" ]; then
    exec "$RUSTC_BIN" --target="$RUST_TARGET" "$@"
fi'''
if exec_old not in text:
    sys.exit("rustc wrapper exec block not found")
text = text.replace(exec_old, ensure, 1)

wrapper.write_text(text)
print("patched", wrapper)

# --- 2. mark the build-machine subprojects -------------------------------
marked = 0
for mb in sorted((root / "subprojects" / "packagefiles").glob("*/meson.build")):
    body = mb.read_text()
    if "mesa_switch_build_machine" in body:
        continue
    is_build_machine = ("native : true" in body) or ("rust.proc_macro" in body)
    if not is_build_machine:
        continue
    lines = body.splitlines(keepends=True)
    # insert right after the project() call's closing paren
    for i, line in enumerate(lines[:40]):
        if line.rstrip() == ")":
            lines.insert(
                i + 1,
                # native: true is REQUIRED: meson routes project args per
                # machine, and these native: true targets are BUILD machine
                # targets (they invoke PATH rustc, which is the wrapper, since
                # build-switch.sh puts /usr/local/libexec on PATH).  Without
                # the kwarg the cfg lands in the host-machine bucket and never
                # reaches the command line (verified in the 2026-11-04 run:
                # "marked 18" but zero occurrences of the marker in the log).
                "\nadd_project_arguments('--cfg', 'mesa_switch_build_machine', language: 'rust', native: true)\n",
            )
            break
    else:
        print("SKIP (no project() close found):", mb)
        continue
    mb.write_text("".join(lines))
    marked += 1
    print("marked", mb.relative_to(root))
print("marked", marked, "build-machine subprojects")

# --- 3. mark the MAIN project's build-machine rust targets ---------------
# compiler_proc (src/compiler/rust/meson.build, native: true) is NOT a
# subproject, so step 2 cannot reach it.  Injecting the same cfg into the
# root meson.build (build-machine bucket) covers every native: true rust
# target in the main tree, whatever it is.  add_project_arguments before
# any target is fine, and meson does not require 'rust' to be an enabled
# language at the call site (verified against meson 1.12 source).
root_mb = root / "meson.build"
body = root_mb.read_text()
if "mesa_switch_build_machine" in body:
    print("root meson.build already marked")
else:
    lines = body.splitlines(keepends=True)
    for i, line in enumerate(lines[:60]):
        if line.rstrip() == ")":
            lines.insert(
                i + 1,
                "\n# CI patch: mark build-machine rust compiles for rustc-switch-wrapper.sh\n"
                "add_project_arguments('--cfg', 'mesa_switch_build_machine', language: 'rust', native: true)\n",
            )
            print("marked root meson.build after project() line", i + 1)
            break
    else:
        sys.exit("root meson.build project() close not found")
    root_mb.write_text("".join(lines))
PY

grep -n 'RUST_TARGET=' "$wrapper" | head -3
# The insert reads `.../rustup" target add ...`, so match on the stable part.
grep -n 'target add' "$wrapper"
