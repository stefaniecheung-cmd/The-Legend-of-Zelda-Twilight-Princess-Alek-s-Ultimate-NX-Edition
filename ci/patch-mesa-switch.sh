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
# This pins the target the wrapper already knows about and makes the wrapper
# install that target's std on first use: the base image only ships rust-src.
set -eu

root="${1:-mesa-switch}"
wrapper="$root/rustc-switch-wrapper.sh"
if [ ! -f "$wrapper" ]; then
    echo "no rustc wrapper at $wrapper" >&2
    exit 1
fi

python3 - "$wrapper" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

default_old = "RUST_TARGET=${MESA_SWITCH_RUST_TARGET:-}"
default_new = "RUST_TARGET=${MESA_SWITCH_RUST_TARGET:-aarch64-unknown-linux-gnu}"
if default_old not in text:
    sys.exit("rustc wrapper default target line not found")
text = text.replace(default_old, default_new, 1)

exec_old = '    exec "$RUSTC_BIN" --target="$RUST_TARGET" "$@"'
ensure = '''    # The base image ships rust-src but no std for this target, so rustc would
    # stop with "can't find crate for `core`". Install it once per container.
    marker="/tmp/.mesa-switch-rust-target-$(echo "$RUST_TARGET" | tr / _)"
    if [ ! -f "$marker" ]; then
        "$(dirname "$RUSTC_BIN")/rustup" target add "$RUST_TARGET" >/dev/null 2>&1 || true
        : > "$marker"
    fi
'''
if exec_old not in text:
    sys.exit("rustc wrapper exec line not found")
text = text.replace(exec_old, ensure + exec_old, 1)

path.write_text(text)
print("patched", path)
PY

grep -n 'RUST_TARGET=' "$wrapper" | head -3
# The insert reads `.../rustup" target add ...`, so match on the stable part.
grep -n 'target add' "$wrapper"
