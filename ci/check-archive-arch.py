#!/usr/bin/env python3
"""Fail if a static archive carries objects built for the wrong machine.

The Switch driver is cross built in a Linux container. When the Rust target is
not pinned, Mesa's Rust crates come out as x86_64 objects and the NRO link
reports "Relocations in generic ELF (EM: 62)" hundreds of times. Catching it
here costs a second; catching it in the NRO job costs a 40 minute round trip.
"""

import struct
import sys

MACHINES = {62: "x86_64", 183: "aarch64", 40: "arm", 3: "i386"}


def members(data):
    """Yield (name, e_machine) for every ELF member of a GNU ar archive."""
    if not data.startswith(b"!<arch>\n"):
        return
    pos = 8
    while pos + 60 <= len(data) and data[pos + 58:pos + 60] == b"`\n":
        try:
            size = int(data[pos + 48:pos + 58].decode().strip())
        except ValueError:
            return
        name = data[pos:pos + 16].decode("utf-8", "replace").strip()
        body = data[pos + 60:pos + 60 + size]
        machine = struct.unpack_from("<H", body, 18)[0] if body[:4] == b"\x7fELF" else None
        yield name, machine
        pos += 60 + size + (size & 1)


def main(path, expected=183):
    with open(path, "rb") as handle:
        data = handle.read()

    counts = {}
    wrong = []
    for name, machine in members(data):
        if machine is None:
            continue
        counts[machine] = counts.get(machine, 0) + 1
        if machine != expected and len(wrong) < 5:
            wrong.append(f"{name} ({MACHINES.get(machine, machine)})")

    total = sum(counts.values())
    summary = ", ".join(f"{MACHINES.get(k, k)}={v}" for k, v in sorted(counts.items()))
    print(f"{path}: {total} ELF members ({summary})")
    if not total:
        print(f"::error::{path} has no ELF members")
        return 1

    bad = total - counts.get(expected, 0)
    if bad:
        print(f"::error::{bad} of {total} members are not {MACHINES[expected]}: " + "; ".join(wrong))
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: check-archive-arch.py <archive>")
    sys.exit(main(sys.argv[1]))
