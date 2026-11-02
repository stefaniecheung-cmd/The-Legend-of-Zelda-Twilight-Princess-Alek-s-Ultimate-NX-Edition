#!/usr/bin/env python3
"""Tokenize user-visible display strings in settings.cpp.

Each entry: original English literal (exactly as it appears, WITH quotes in the
source) -> (KEY, ZH). We replace the quoted literal `"EN"` with `"[KEY]"` everywhere
it appears. Replacement is global per literal; counts are reported so the operator
can sanity-check that no internal/config string was hit.

Idempotent: if a literal is already tokenized it won't match.
"""
import sys
from pathlib import Path

SRC = Path("src/dusk/ui/settings.cpp")

# EN literal -> (KEY, ZH). Only user-visible display strings.
TOKENS = {
    # .title (pane / group / modal titles)
    "Data Folder Not Changed": ("DATA_FOLDER_NOT_CHANGED", "数据文件夹未更改"),
    "Internal Resolution": ("INTERNAL_RESOLUTION", "内部分辨率"),
    "Shadow Resolution": ("SHADOW_RESOLUTION", "阴影分辨率"),
    "Output Resampling": ("OUTPUT_RESAMPLING", "输出重采样"),
    "Bloom": ("BLOOM", "泛光"),
    "Bloom Brightness": ("BLOOM_BRIGHTNESS", "泛光亮度"),
    "Depth of Field": ("DEPTH_OF_FIELD", "景深"),
    "Enable Texture Replacements": ("ENABLE_TEXTURE_REPLACEMENTS", "启用纹理替换"),
    "Restart by hand": ("RESTART_BY_HAND", "请手动重启"),
    "Benchmark not started": ("BENCHMARK_NOT_STARTED", "基准测试未启动"),
    "Profile matrix not started": ("PROFILE_MATRIX_NOT_STARTED", "性能矩阵未启动"),
    "Shader preparation not started": ("SHADER_PREP_NOT_STARTED", "着色器准备未启动"),
    "Performance tour not started": ("PERF_TOUR_NOT_STARTED", "性能巡览未启动"),
    "Check tour not started": ("CHECK_TOUR_NOT_STARTED", "检查巡览未启动"),
    "Trailer takes not started": ("TRAILER_NOT_STARTED", "预告片镜头未启动"),
    "DRS stress not started": ("DRS_STRESS_NOT_STARTED", "动态分辨率压力测试未启动"),
    "Warming every shader": ("WARMING_SHADERS", "正在预热所有着色器"),
    # .text (buttons / labels)
    "Reset to Default": ("RESET_TO_DEFAULT", "恢复默认"),
    "Restart now": ("RESTART_NOW", "立即重启"),
    "Check now": ("CHECK_NOW", "立即检查"),
    "Download and install": ("DOWNLOAD_AND_INSTALL", "下载并安装"),
    "Next Start Without Mods": ("NEXT_START_NO_MODS", "下次启动禁用模组"),
    "Executable Memory": ("EXECUTABLE_MEMORY", "可执行内存"),
    "Patch Own Code": ("PATCH_OWN_CODE", "修补自身代码"),
    "Run Benchmark": ("RUN_BENCHMARK", "运行基准测试"),
    "Run Profile Matrix": ("RUN_PROFILE_MATRIX", "运行性能矩阵"),
    "Prepare Shaders": ("PREPARE_SHADERS", "准备着色器"),
    "Run Performance Tour": ("RUN_PERF_TOUR", "运行性能巡览"),
    "Run Check Tour": ("RUN_CHECK_TOUR", "运行检查巡览"),
    "Play trailer takes": ("PLAY_TRAILER", "播放预告片镜头"),
    "Run DRS Stress": ("RUN_DRS_STRESS", "运行动态分辨率压力测试"),
    "Warm All Shaders": ("WARM_ALL_SHADERS", "预热所有着色器"),
    "Configure Inputs": ("CONFIGURE_INPUTS", "配置输入"),
    "Customize Layout": ("CUSTOMIZE_LAYOUT", "自定义布局"),
    "Recenter Motion Sensors": ("RECENTER_SENSORS", "校准运动传感器"),
    "Achievements": ("ACHIEVEMENTS", "成就"),
    "Missing Device": ("MISSING_DEVICE", "缺少设备"),
    # display-name returns (.getValue / display_name functions)
    "Auto": ("BACKEND_AUTO", "自动"),
    "(none)": ("NONE", "(无)"),
    "Unknown": ("UNKNOWN", "未知"),
    "Auto (only when the GPU is tight)": ("AUTO_TIGHT", "仅在 GPU 紧张时自动"),
    # global on/off/normal (display only)
    "Off": ("OFF", "关闭"),
    "On": ("ON", "开启"),
    "Normal": ("DUAL_LAYOUT_NORMAL", "常规"),
    # constexpr enum-name arrays (dropdown option labels)
    "Card Image": ("CARD_IMAGE", "存储卡镜像"),
    "GCI Folder": ("GCI_FOLDER", "GCI 文件夹"),
    "Top Left": ("FPS_CORNER_TL", "左上"),
    "Top Right": ("FPS_CORNER_TR", "右上"),
    "Bottom Left": ("FPS_CORNER_BL", "左下"),
    "Bottom Right": ("FPS_CORNER_BR", "右下"),
    "Companion Screen": ("FPS_CORNER_COMPANION", "副屏"),
    "Wii U Style": ("DUAL_HUD_WIIU", "Wii U 风格"),
    "3DS Style": ("DUAL_HUD_3DS", "3DS 风格"),
    "Flip Grip": ("DUAL_LAYOUT_FLIP", "翻转握持"),
}

text = SRC.read_text(encoding="utf-8")
total_replaced = 0
for en, (key, zh) in TOKENS.items():
    literal = f'"{en}"'
    token = f'"[{key}]"'
    count = text.count(literal)
    if count == 0:
        print(f"WARN 0x {en!r} -> not found (already tokenized or renamed?)")
        continue
    text = text.replace(literal, token)
    total_replaced += count
    print(f"OK   {count}x {en!r} -> [{key}]")

SRC.write_text(text, encoding="utf-8")
print(f"# replaced {total_replaced} literals across {len(TOKENS)} keys")

# Emit dict TSV for add_i18n_entries.py (KEY <TAB> EN <TAB> ZH)
with open("settings_tokens.tsv", "w", encoding="utf-8") as f:
    for en, (key, zh) in TOKENS.items():
        f.write(f"{key}\t{en}\t{zh}\n")
print("# wrote settings_tokens.tsv")
