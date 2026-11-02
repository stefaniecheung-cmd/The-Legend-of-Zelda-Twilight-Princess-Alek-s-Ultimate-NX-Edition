# 汉化 + 双端构建流程（Switch NRO / SteamOS）

这份文档回答两件事：**汉化怎么在 Alexgg1014 的基座上落地**，以及**怎么从同一棵代码树产出 `.nro` 和 SteamOS 可执行文件**。

结论先说：两端共用同一份汉化层，不需要分叉。汉化只挂在 RmlUi 的 `SystemInterface::TranslateString` 上，和平台后端无关；差异只在构建工具链和 `res/` 的打包方式。

---

## 阶段 0：一次性准备

```sh
git clone -b cn-switch https://github.com/<你的fork>/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition.git
cd The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition
git submodule update --init --recursive
```

汉化层需要的三样东西都在树里，没有外部依赖：

| 件 | 位置 | 说明 |
|---|---|---|
| 翻译器 | `src/dusk/ui/i18n.{hpp,cpp}` | 自包含，只依赖 aurora/borealis/dusk/io |
| 词典 | `res/i18n/{en,zh-cn,fr,ja}.xml` | `[TOKEN]` → 译文 |
| 中文字体 | `res/HarmonyOS_Sans*.ttf` | 作为 **fallback face** 加载，拉丁字形仍走 Fira Sans |
| aurora 钩子 | `cmake/AuroraI18nHook.cmake` | configure 时自动给 `extern/aurora` 打补丁，`.gitmodules` 保持上游原样 |

---

## 阶段 1：汉化本体（可增量做，不影响构建）

一屏一屏推进，每屏三步：

```sh
# 1. 只替换词典里已有译文的字符串（复用优先）
python tools/auto_tokenize.py src/dusk/ui/<screen>.cpp --report unmatched.tsv
python tools/auto_tokenize.py src/dusk/ui/<screen>.cpp --apply

# 2. 剩下没有译文的，写进 TSV：KEY<TAB>English<TAB>中文
python tools/add_i18n_entries.py my_tokens.tsv

# 3. 门禁（缺 key、重复 key、会破坏 RmlUi 解析的值，全部拦下）
python tools/check_i18n_tokens.py
```

三条硬规则（踩到会**静默**出错，不会报编译错误）：

1. token 内不能有 `{}` —— `fmt::format` 先格式化后翻译，参数会被丢掉。
2. 译文值不能含 `{` `}` 或裸 `<` —— 发生替换后 RmlUi 会把结果当 RML 重新解析。
3. 只有**文本节点**会被翻译；属性值（`title="[X]"`）要走 `i18n::tr()`。

进度：`prelaunch`、`settings`、`mod_browser`、`saves_window`、`mods_window`、`controller_config`、`logs_window`、`graphics_tuner`、`ui` 已完成；`editor.cpp`（可复用命中 373 处）和 `touch_controls*`、`online_mods`、`mod_updates`、`overlay`、`color_input`、`warp`、`list`、`window` 待做。

---

## 阶段 2：先做 SteamOS（建议顺序，见文末）

桌面端编译依赖少、迭代快，是验证汉化最快的方式，不需要 devkitPro。

SteamOS 的根文件系统是只读的，别去 `steamos-readonly disable`，用容器：

```sh
distrobox create --name dusk-build --image archlinux:latest
distrobox enter dusk-build
```

容器内（SteamOS 本身就是 Arch 系，包名一致）：

```sh
sudo pacman -S --needed alsa-lib base-devel clang cmake freetype2 libpulse \
  libxrandr lld llvm ninja python python-markupsafe vulkan-headers \
  libxi libxcursor libxinerama libxss libxtst libpng curl git

cmake --preset linux-default-relwithdebinfo
cmake --build --preset linux-default-relwithdebinfo
```

产物：`build/linux-default-relwithdebinfo/dusklight`（`res/` 与 `mods/` 会一起放在旁边）。

运行：

```sh
./build/linux-default-relwithdebinfo/dusklight --dvd /path/to/game.iso
```

> 游戏本体不参与构建，运行时才读镜像。汉化验收在这一步就能看完：主菜单 → 设置 → 模组浏览器 → 存档管理。

如要打成 AppImage 分发给别人，仓库自带 `ci/build-appimage.sh`。

---

## 阶段 3：Switch NRO

### 依赖（缺一不可）

- **devkitPro**，含 `devkitA64`、`libnx`、switch portlibs（zlib、zstd、bzip2、xz、freetype、harfbuzz、libpng、curl、expat），环境变量 `DEVKITPRO` 指向安装目录。
- **CMake 3.25+ / Ninja / Python 3 / Git**，并且要用**原生 Windows 的 CMake（MSYS2 那个）**，不能用 devkitPro 自带的 CMake。
- **GNU `patch`**：仓库要在 configure 阶段给 Dawn / Tracy / SDL3 打三个补丁（`cmake/SwitchPatches.cmake`）。
- **Mesa Horizon 驱动**：`danfromtico/mesa-switch` 产出的 `libvulkan.a` + Vulkan 头文件，按 `NAGA_VULKAN_ROOT` 的目录布局放好（`<mesa sdk>/opt/devkitpro/portlibs/switch`）。
- configure 期间要能联网：Dawn、SDL3、Tracy、RmlUi 都是现场拉取。

### 构建

```sh
cmake --preset switch-devkitA64-release \
  -DNAGA_VULKAN_ROOT=<mesa sdk>/opt/devkitpro/portlibs/switch
cmake --build --preset switch-devkitA64-release
```

产物：`dusklight.elf` 和 `dusklight.nro`（`platforms/switch` 的构建输出目录）。

**关于静态 mod**：官方文档的示例会带 `-DALEKS2_STATIC_MODS="template_mod;flow_demo;rollandsprint"`，但 `flow_demo` 在新版工具链上会因 `IMPORT_SERVICE(MessageService, svc_message)` 编译失败。拿不准就先留空（preset 默认就是空），只做汉化验收不需要这些 demo mod。

### 部署到 SD 卡

```
sdmc:/switch/dusklight/dusklight.nro
sdmc:/switch/dusklight/          ← 存档、设置、mods 也在这里
```

启动方式：在 hbmenu 里对任意游戏按住 **R** 点开，选 `dusklight`（title takeover）。

---

## 阶段 4：汉化在 Switch 上的两个差异点

1. **`res/` 会被打进 romfs**（`DUSK_ASSET_DIR="romfs:/"`）。也就是说字体和词典**不需要**放 SD 卡，但它们会算进 NRO 体积：三个 HarmonyOS 字体约 **20.5 MB**。想瘦身就把 `HarmonyOS_Sans_TC_Regular.ttf` 和 `HarmonyOS_Sans_Regular.ttf` 去掉，只留 `SC`（约 8 MB），并同步删掉 `ui.cpp` 里对应的 `load_font` 行。

   注意 `platforms/switch/CMakeLists.txt` 是用 `file(COPY "${CMAKE_SOURCE_DIR}/res" ...)` 在 **configure 阶段**拷进 romfs 的。改完词典或字体后只 `cmake --build` 不会更新，必须重新跑一次 `cmake --preset ...`。
2. **CJK 字形靠 fallback**：`load_font(..., true)` 的第二个参数必须是 true，否则中文会显示成空白方块——不是乱码，是彻底不显示。这条已经在 `ui.cpp` 里接好。

---

## 为什么建议先 SteamOS、后 Switch

| | SteamOS | Switch |
|---|---|---|
| 依赖 | pacman 一套包 | devkitPro + 预编译 mesa 驱动 + 三个补丁 |
| 迭代周期 | 分钟级 | 十几分钟起 |
| 能看到中文吗 | 能，完整 | 能，但要真机 |
| 失败模式 | 编译错误，易定位 | 编译错误 + 驱动/romfs 问题 |

汉化层是平台无关的，所以先在桌面端把「译文对不对、有没有 `[TOKEN]` 漏网、字体渲染正常吗」全部验证完，再去碰 Switch 工具链。Switch 端只剩「romfs 里资源读得到吗」「字体在 720p 下好看吗」两个新变量。

---

## 验收清单（两端通用）

- [ ] 主菜单：设置 / 模组 / 检查更新 / 退出 都是中文
- [ ] 设置：分页标题、开关项、下拉选项、重启提示
- [ ] 模组浏览器：排序项、安装状态徽章、错误提示、分页
- [ ] 存档管理：槽位、复制/删除对话框、文件选择器
- [ ] 手柄设置：分页、按键名表、死区说明
- [ ] 日志页：级别名、复制/清空
- [ ] 全程没有残留 `[TOKEN]`（日志里搜 `[A-Z_]` 也能查）
