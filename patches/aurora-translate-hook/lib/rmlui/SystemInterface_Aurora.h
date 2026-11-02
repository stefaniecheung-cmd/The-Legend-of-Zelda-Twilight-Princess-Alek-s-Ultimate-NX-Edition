#pragma once

#include <aurora/rmlui.hpp>
#include <RmlUi_Platform_SDL.h>

namespace aurora::rmlui {

class SystemInterface_Aurora : public SystemInterface_SDL {
public:
  SystemInterface_Aurora();
  ~SystemInterface_Aurora() override = default;

  // dusk-i18n: RmlUi calls this for every text node before instancing it.
  int TranslateString(Rml::String& translated, const Rml::String& input) override;
  void SetTranslateCallback(std::function<int(Rml::String&, const Rml::String&)> callback);

  bool LogMessage(Rml::Log::Type type, const Rml::String& message) override;
  void ActivateKeyboard(Rml::Vector2f caret_position, float line_height) override;
  void DeactivateKeyboard() override;

  // Custom API
  void SetInputType(InputType type) noexcept;

private:
  // dusk-i18n
  std::function<int(Rml::String&, const Rml::String&)> mTranslateCallback;

  InputType mTextInputType = InputType::Text;
  InputType mActiveTextInputType = InputType::Text;
  bool mHasActiveTextInputType = false;
};

} // namespace aurora::rmlui
