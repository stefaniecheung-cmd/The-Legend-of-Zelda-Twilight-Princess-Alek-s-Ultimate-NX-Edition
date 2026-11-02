# aleks2-cn: RmlUi text-translation hook for the aurora submodule.
#
# RmlUi hands every text node to Rml::SystemInterface::TranslateString before
# instancing it (Source/Core/Factory.cpp: InstanceElementText). aurora owns the
# concrete SystemInterface implementation but upstream exposes no way to
# intercept that call, so the four files below get a minimal callback added.
#
# The edit happens here, at configure time, instead of in a forked submodule or
# a repointed .gitmodules entry: a plain `git submodule update` keeps working and
# the patch is re-applied on the next configure if the submodule is reset.
# The edit is idempotent: each file is skipped once it carries the "dusk-i18n"
# marker, so reconfiguring does not rewrite sources or trigger rebuilds.
#
# It is deliberately non-fatal. If aurora's sources drift and an anchor stops
# matching, we warn and leave DUSK_I18N_AURORA_HOOK unset; ui.cpp then skips the
# callback registration and the UI stays English instead of the build breaking
# on a missing symbol.

set(DUSK_I18N_AURORA_HOOK OFF)

set(_dusk_aurora "${CMAKE_CURRENT_LIST_DIR}/../extern/aurora")

if (NOT EXISTS "${_dusk_aurora}/lib/rmlui/SystemInterface_Aurora.h")
    message(STATUS "dusk i18n: extern/aurora is not populated; skipping translate hook "
                   "(run: git submodule update --init --recursive)")
    return()
endif ()

set(_dusk_i18n_failed "")
set(_dusk_i18n_patched 0)

# Applies one literal replacement, matching the file's own line endings, and
# requires the anchor to be unique so a divergent tree cannot be half-patched.
function(_dusk_i18n_replace path old new)
    file(READ "${path}" _src)

    # Rebuild the anchor with the line ending this checkout actually uses
    # (core.autocrlf on Windows turns the submodule into CRLF).
    if (_src MATCHES "\r\n")
        set(_nl "\r\n")
    else ()
        set(_nl "\n")
    endif ()
    string(REPLACE "\n" "${_nl}" _old "${old}")
    string(REPLACE "\n" "${_nl}" _new "${new}")

    get_filename_component(_name "${path}" NAME)

    string(FIND "${_src}" "${_old}" _first)
    if (_first EQUAL -1)
        set(_dusk_i18n_failed "${_dusk_i18n_failed}\n  - anchor not found in ${_name}" PARENT_SCOPE)
        return()
    endif ()

    string(FIND "${_src}" "${_old}" _second REVERSE)
    if (NOT _second EQUAL _first)
        set(_dusk_i18n_failed "${_dusk_i18n_failed}\n  - anchor is not unique in ${_name}" PARENT_SCOPE)
        return()
    endif ()

    string(REPLACE "${_old}" "${_new}" _out "${_src}")
    file(WRITE "${path}" "${_out}")
endfunction()

# Skips a file that already carries the marker. Sets _dusk_needs_patch.
macro(_dusk_i18n_begin path)
    set(_dusk_needs_patch TRUE)
    if (EXISTS "${path}")
        file(READ "${path}" _dusk_marker_probe)
        if (_dusk_marker_probe MATCHES "dusk-i18n")
            set(_dusk_needs_patch FALSE)
        endif ()
    else ()
        set(_dusk_i18n_failed "${_dusk_i18n_failed}\n  - missing file: ${path}")
    endif ()
endmacro()

# --- 1/4: declare the override + setter on the aurora SystemInterface ---------
set(_f "${_dusk_aurora}/lib/rmlui/SystemInterface_Aurora.h")
_dusk_i18n_begin("${_f}")
if (_dusk_needs_patch)
    math(EXPR _dusk_i18n_patched "${_dusk_i18n_patched} + 1")
    _dusk_i18n_replace("${_f}"
        [==[  ~SystemInterface_Aurora() override = default;
  bool LogMessage(Rml::Log::Type type, const Rml::String& message) override;]==]
        [==[  ~SystemInterface_Aurora() override = default;

  // dusk-i18n: RmlUi calls this for every text node before instancing it.
  int TranslateString(Rml::String& translated, const Rml::String& input) override;
  void SetTranslateCallback(std::function<int(Rml::String&, const Rml::String&)> callback);

  bool LogMessage(Rml::Log::Type type, const Rml::String& message) override;]==]
    )
    _dusk_i18n_replace("${_f}"
        [==[private:
  InputType mTextInputType = InputType::Text;]==]
        [==[private:
  // dusk-i18n
  std::function<int(Rml::String&, const Rml::String&)> mTranslateCallback;

  InputType mTextInputType = InputType::Text;]==]
    )
endif ()

# --- 2/4: implement them ------------------------------------------------------
set(_f "${_dusk_aurora}/lib/rmlui/SystemInterface_Aurora.cpp")
_dusk_i18n_begin("${_f}")
if (_dusk_needs_patch)
    math(EXPR _dusk_i18n_patched "${_dusk_i18n_patched} + 1")
    _dusk_i18n_replace("${_f}"
        [==[} // namespace aurora::rmlui]==]
        [==[
// dusk-i18n: translation callback plumbing (see cmake/AuroraI18nHook.cmake).
void SystemInterface_Aurora::SetTranslateCallback(
    std::function<int(Rml::String&, const Rml::String&)> callback) {
  mTranslateCallback = std::move(callback);
}

// dusk-i18n: same contract as Rml::SystemInterface::TranslateString -- fill
// `translated` and return the number of substitutions made.
int SystemInterface_Aurora::TranslateString(Rml::String& translated, const Rml::String& input) {
  if (mTranslateCallback) {
    return mTranslateCallback(translated, input);
  }

  translated = input;
  return 0;
}
} // namespace aurora::rmlui]==]
    )
endif ()

# --- 3/4: public entry point --------------------------------------------------
set(_f "${_dusk_aurora}/include/aurora/rmlui.hpp")
_dusk_i18n_begin("${_f}")
if (_dusk_needs_patch)
    math(EXPR _dusk_i18n_patched "${_dusk_i18n_patched} + 1")
    _dusk_i18n_replace("${_f}"
        [==[void set_input_type(InputType type) noexcept;]==]
        [==[void set_input_type(InputType type) noexcept;

// dusk-i18n: callback receives the raw text and fills `translated`. Returning a
// non-zero count tells RmlUi the text is now RML and it re-parses it, so
// translations must not contain '<'.
void set_translate_callback(std::function<int(Rml::String&, const Rml::String&)> callback) noexcept;
]==]
    )
endif ()

# --- 4/4: forward it to the live system interface -----------------------------
set(_f "${_dusk_aurora}/lib/rmlui.cpp")
_dusk_i18n_begin("${_f}")
if (_dusk_needs_patch)
    math(EXPR _dusk_i18n_patched "${_dusk_i18n_patched} + 1")
    _dusk_i18n_replace("${_f}"
        [==[void set_input_type(InputType type) noexcept {
  auto* systemInterface = static_cast<SystemInterface_Aurora*>(Backend::GetSystemInterface());
  if (systemInterface != nullptr) {
    systemInterface->SetInputType(type);
  }
}]==]
        [==[void set_input_type(InputType type) noexcept {
  auto* systemInterface = static_cast<SystemInterface_Aurora*>(Backend::GetSystemInterface());
  if (systemInterface != nullptr) {
    systemInterface->SetInputType(type);
  }
}

// dusk-i18n: route RmlUi text through the callback registered by the game.
void set_translate_callback(std::function<int(Rml::String&, const Rml::String&)> callback) noexcept {
  auto* systemInterface = static_cast<SystemInterface_Aurora*>(Backend::GetSystemInterface());
  if (systemInterface != nullptr) {
    systemInterface->SetTranslateCallback(std::move(callback));
  }
}]==]
    )
endif ()

if (_dusk_i18n_failed STREQUAL "")
    set(DUSK_I18N_AURORA_HOOK ON)
    if (_dusk_i18n_patched GREATER 0)
        message(STATUS "dusk i18n: patched ${_dusk_i18n_patched} aurora file(s) with the translate hook")
    else ()
        message(STATUS "dusk i18n: aurora translate hook already in place")
    endif ()
else ()
    message(WARNING
        "dusk i18n: could not patch extern/aurora -- the UI stays English.\n"
        "Apply patches/aurora-translate-hook/ by hand (see its README), or reset the "
        "submodule to the pinned commit and reconfigure. Unmatched anchors:${_dusk_i18n_failed}")
endif ()
