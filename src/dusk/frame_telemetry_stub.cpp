// PC builds link d_map.cpp and settings.cpp, which both read
// dusk::frame_telemetry::lab(). The real implementation is Switch-only
// (its svc* calls and the g_dusk* knob externs sit outside any __SWITCH__
// guard, so it never compiled off the console -- which is why the upstream
// PC link stopped at "undefined symbol: dusk::frame_telemetry::lab()").
// Non-console builds get a default-off stub instead; the defaults match
// perf::LabOptions' own initializers, so minimap_pan and hud_fast behave
// exactly as they do at console defaults. On the console this file expands
// to nothing: frame_telemetry.cpp provides the real thing.
#ifndef __SWITCH__

#include "dusk/frame_telemetry.hpp"

namespace dusk::frame_telemetry {

const perf::LabOptions& lab() {
    static const perf::LabOptions options;
    return options;
}

}  // namespace dusk::frame_telemetry

#endif  // !__SWITCH__
