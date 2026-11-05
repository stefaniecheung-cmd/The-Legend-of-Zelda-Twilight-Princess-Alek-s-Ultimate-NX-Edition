#!/usr/bin/env python3
"""Add an RmlUi translate callback to aurora, so the UI can be localised.

RmlUi routes every string it renders through
``SystemInterface::TranslateString``. aurora never overrode it, so the base
class returns the string unchanged and there is nowhere to hook a dictionary
in. This patch adds the override, parks a ``std::function`` on the system
interface, and exposes ``aurora::rmlui::set_translate_callback``.

It is a pure addition: with no callback installed ``translated = input`` and
behaviour is byte-identical to before.

Applied as a post-checkout patch rather than a fork, the same way
``abseil_newlib.py`` is, so the aurora gitlink stays pinned. Idempotent: a
cache-restored tree is patched once and the second run is a no-op.

Usage: python ci/patches/aurora-translate-callback.py extern/aurora
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "SetTranslateCallback"

HPP_ANCHOR = "float get_ui_scale() noexcept;\n"
HPP_INSERT = """void set_translate_callback(
    std::function<int(Rml::String&, const Rml::String&)> callback) noexcept;
"""

RMLUI_ANCHOR = """void set_input_type(InputType type) noexcept {
  auto* systemInterface = static_cast<SystemInterface_Aurora*>(Backend::GetSystemInterface());
  if (systemInterface != nullptr) {
    systemInterface->SetInputType(type);
  }
}
"""
RMLUI_INSERT = """
void set_translate_callback(
    std::function<int(Rml::String&, const Rml::String&)> callback) noexcept {
  auto* systemInterface = static_cast<SystemInterface_Aurora*>(Backend::GetSystemInterface());
  if (systemInterface != nullptr) {
    systemInterface->SetTranslateCallback(std::move(callback));
  }
}
"""

SI_H_MSG_ANCHOR = "  bool LogMessage(Rml::Log::Type type, const Rml::String& message) override;\n"
SI_H_MSG_INSERT = "  int TranslateString(Rml::String& translated, const Rml::String& input) override;\n"

SI_H_API_ANCHOR = "  void SetInputType(InputType type) noexcept;\n"
SI_H_API_INSERT = (
    "  void SetTranslateCallback(std::function<int(Rml::String&, const Rml::String&)> callback) noexcept;\n"
)

SI_H_MEMBER_ANCHOR = "  bool mHasActiveTextInputType = false;\n"
SI_H_MEMBER_INSERT = "  std::function<int(Rml::String&, const Rml::String&)> mTranslateCallback;\n"

SI_CPP_ANCHOR = "} // namespace aurora::rmlui\n"
SI_CPP_INSERT = """
int SystemInterface_Aurora::TranslateString(Rml::String& translated, const Rml::String& input) {
  if (!mTranslateCallback) {
    translated = input;
    return 0;
  }
  return mTranslateCallback(translated, input);
}

void SystemInterface_Aurora::SetTranslateCallback(
    std::function<int(Rml::String&, const Rml::String&)> callback) noexcept {
  mTranslateCallback = std::move(callback);
}

} // namespace aurora::rmlui
"""


def _insert_after(text: str, anchor: str, addition: str, label: str) -> tuple[str, str]:
    """Insert ``addition`` directly after ``anchor``; no-op when already present."""
    if addition.strip() in text:
        return text, f"{label}: already present"
    index = text.find(anchor)
    if index < 0:
        raise SystemExit(f"aurora-translate-callback: anchor not found in {label}: {anchor!r}")
    end = index + len(anchor)
    return text[:end] + addition + text[end:], f"{label}: inserted"


def patch_hpp(root: Path) -> str:
    path = root / "include/aurora/rmlui.hpp"
    text = path.read_text(encoding="utf-8")
    text, status = _insert_after(text, HPP_ANCHOR, HPP_INSERT, "rmlui.hpp")
    if status.endswith("inserted"):
        path.write_text(text, encoding="utf-8")
    return status


def patch_rmlui_cpp(root: Path) -> str:
    path = root / "lib/rmlui.cpp"
    text = path.read_text(encoding="utf-8")
    text, status = _insert_after(text, RMLUI_ANCHOR, RMLUI_INSERT, "lib/rmlui.cpp")
    if status.endswith("inserted"):
        path.write_text(text, encoding="utf-8")
    return status


def patch_system_interface_h(root: Path) -> str:
    path = root / "lib/rmlui/SystemInterface_Aurora.h"
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return "SystemInterface_Aurora.h: already present"
    text, _ = _insert_after(text, SI_H_MSG_ANCHOR, SI_H_MSG_INSERT, "SystemInterface_Aurora.h")
    text, _ = _insert_after(text, SI_H_API_ANCHOR, SI_H_API_INSERT, "SystemInterface_Aurora.h")
    text, _ = _insert_after(text, SI_H_MEMBER_ANCHOR, SI_H_MEMBER_INSERT, "SystemInterface_Aurora.h")
    path.write_text(text, encoding="utf-8")
    return "SystemInterface_Aurora.h: inserted"


def patch_system_interface_cpp(root: Path) -> str:
    path = root / "lib/rmlui/SystemInterface_Aurora.cpp"
    text = path.read_text(encoding="utf-8")
    if "SystemInterface_Aurora::TranslateString" in text:
        return "SystemInterface_Aurora.cpp: already present"
    index = text.rfind(SI_CPP_ANCHOR)
    if index < 0:
        raise SystemExit("aurora-translate-callback: namespace close not found in SystemInterface_Aurora.cpp")
    text = text[:index] + SI_CPP_INSERT.lstrip("\n") + text[index + len(SI_CPP_ANCHOR):]
    path.write_text(text, encoding="utf-8")
    return "SystemInterface_Aurora.cpp: inserted"


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    if not (root / "lib/rmlui.cpp").is_file():
        print(f"aurora-translate-callback: {root} does not look like an aurora checkout", file=sys.stderr)
        return 1

    for step in (patch_hpp, patch_rmlui_cpp, patch_system_interface_h, patch_system_interface_cpp):
        print(step(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
