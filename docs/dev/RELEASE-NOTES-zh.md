# 更新摘要 · Dusklight v1.1.1-cn（Switch 简体中文界面）

| | |
|---|---|
| 上游 | [Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition](https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition) `main`，基线版本 **1.1.1** |
| 构建基线 | `5e174a84`（含内置模组包；其后的文档与 CI 提交不改动产物） |
| 发布 tag | `v1.1.1-cn`（annotated tag，指向发布时的 `main`） |
| 产物 | `dusklight-1.1.1-cn.nro`，108,021,081 字节（103.0 MiB） |
| SHA256 | `1c386627ca71aadcdb914fa4e189d6ddf0a77b4ef8bac834608ac17bd88e161f` |
| 构建 | GitHub Actions run `42227654038`（success），`devkitpro/devkita64` 容器 |

> 这是上游的个人汉化分支，不是官方版本。只汉化**移植层界面**，游戏内剧情对话、道具名等原版游戏资源不在范围内。

---

## 一、这一版做了什么

1. **界面默认简体中文。** 主菜单、设置页及各项说明、存档对话框、模组加载与更新提示、崩溃报告、按键绑定名，全部译入。设置里可切回 English。
2. **补上中文字形。** 打包 HarmonyOS Sans 系列三款字体，原版字体没有汉字。
3. **把 Switch 构建跑通并搬进 CI。** 上游需要的 `libvulkan.a` 没有公开的 Horizon 预编译版，另建 `stefaniecheung-cmd/mesa-switch` 编出 Mesa 26.2.4 Horizon SDK（release `sdk-26.2.4`，48.3 MB / 93 文件），CI 公开下载，不依赖 token。
4. **补齐两个内置模组包。** `randomizer.dusk` 与 `dev.aleks2.cross_save.dusk` 来自上游 v1.1.1 Release NRO 的 RomFS，按原样放进 `platforms/switch/mod-packages/`，由 `ALEKS2_BUNDLED_MOD_PACKAGES` 打进 `romfs:/res/mods/`。干净源码构建默认没有这两个包（它们不在 git 里）。

## 二、汉化方案：不动一处 UI 调用点

RmlUi 渲染每个字符串时会调用 `SystemInterface::TranslateString`，aurora 图形层实现了这个接口但一直原样返回。在那一层挂一个全局回调即可覆盖全部界面文字：

```
RmlUi 渲染文本 → TranslateString → 拿整句英文查 res/i18n/zh-cn.xml
                                 → 查到就换，查不到原样返回英文
```

- 键就是**英文原文整句**，精确匹配（另支持 `标题\n详情` 的首行匹配）。
- 查不到只回落英文，不会空白、不会崩；上游改文案或加新界面也不会编译失败，**不会与上游代码冲突**。
- aurora 侧的 `TranslateString` override 由 `ci/patches/aurora-translate-callback.py` 在 CMake 配置期自动注入，26 行纯增量、幂等。
- 引擎做了 XML 实体解码，含 `&`、`'` 的词条也能命中。

### 覆盖率

| 口径 | 数量 |
|---|---|
| 抽取到的源串 / `zh-cn.xml` 条目 | 1586 |
| `ci/i18n/zh-cn.json` 中的译文映射 | 1388 |
| XML 中真正换成中文（值 ≠ 键） | **1379（86.9%）** |
| 保持英文 | 207 |

207 条里，198 条是逐条审过、有意不译的，理由与清单写在 `ci/i18n/not-translated.txt`：

| 类别 | 数量 | 原因 |
|---|---|---|
| HTTP/WebSocket 协议字段名与常量 | 27 | 翻了会坏协议或坏格式串 |
| 运行时拼接的句子片段 | 28 | 回调收到的是拼好的整句，字面量永远匹配不到 |
| ELF / TLS 加载器内部诊断 | 143 | 只进日志，不进界面 |

剩下 9 条本身就是英文专名（`GameCube`、`Wii`、`Vulkan`、`WebGPU`、`R + Start` 等），译文与原文相同。

## 三、改动清单

汉化本体 18 个文本文件，加字体二进制、两个模组包、构建 workflow、README 与文档。

| 类别 | 文件 |
|---|---|
| 查表引擎（新增） | `src/dusk/ui/i18n.cpp`、`src/dusk/ui/i18n.hpp` |
| 注入点（新增） | `ci/patches/aurora-translate-callback.py` |
| 词表 | `res/i18n/zh-cn.xml`、`res/i18n/en.xml`（恒等映射兜底） |
| 词表源数据与工具 | `ci/i18n/{zh-cn,source-strings,extra-seed}.json`、`ci/i18n/not-translated.txt`、`tools/build-i18n.py`、`tools/extract-ui-strings.py` |
| 语言设置 | `src/dusk/settings.h`、`src/dusk/settings.cpp`（`ui.language`，默认 `zh-cn`）、`src/dusk/ui/settings.cpp`（下拉选择） |
| 启动接线 | `src/dusk/ui/ui.cpp`（初始化 + 注册回调）、`files.cmake`、`CMakeLists.txt` |
| 字体（新增，二进制） | `res/HarmonyOS_Sans_Regular.ttf` 等三款 |
| 内置模组包（新增，二进制） | `platforms/switch/mod-packages/{randomizer,dev.aleks2.cross_save}.dusk`、`README.md` |
| 构建 | `.github/workflows/build-switch.yml` |
| 文档 | `docs/dev/i18n.md`、`docs/dev/i18n-zh.md`、`docs/dev/RELEASE-NOTES-zh.md`、README 顶部中文版说明 |

`ci/patches/aurora-translate-callback.py` 作用于子模块 `extern/aurora`（本分支用的是 `Alexgg1014/aurora-aleks-nx`），不打补丁就只会显示英文。

## 四、安装与校验

### NRO 本体

1. 把 `dusklight-1.1.1-cn.nro` 放到 **`sdmc:/switch/dusklight/`**（不是 `/switch/` 根下）。游戏盘镜像放同目录或 `sdmc:/switch/dusklight/discs/`。
2. **在 HOME 菜单按住 R 启动任意游戏做 title takeover**，从列表里选本程序。**不要从相册 / hbmenu 启动**——applet 模式内存不足，程序会打印提示后直接退出（上游 `docs/user/install.md`）。
3. 默认就是简体中文；想回英文进设置 → 界面语言 → English。存档与设置沿用上游路径，替换 NRO 不会丢。
4. 首次启动会显示 **Preparing shaders**（见下），属正常现象，可以等它跑完或点 Skip。

### 两个内置模组：两条路，效果相同

Release 的 Assets 里除了 NRO，还单独提供 `randomizer.dusk`（6,483,388 字节，SHA256 `4ed58071…`）与 `dev.aleks2.cross_save.dusk`（2,574,119 字节，SHA256 `dd9fa48c…`），均为上游 v1.1.1 原包逐字节一致。

| | 做法 | 适用 |
|---|---|---|
| A（开箱即用） | 什么都不做，两个包已由 `ALEKS2_BUNDLED_MOD_PACKAGES` 打进 `romfs:/res/mods/` | 新装、或愿意重新下载 NRO |
| B（更快） | 把两个 `.dusk` 拷到 **`sdmc:/switch/dusklight/mods/`** 后重启，无需重下 100 MB 的 NRO | 已经装了旧 NRO、或想要更小体积的 NRO |

方式 B 是上游官方支持的手工安装方式（`docs/user/mods.md` 原文：「copy `.dusk` packages to `sdmc:/switch/dusklight/mods/`」）。源码里 `mods_init(dusk::ConfigPath / "mods")` 把这张卡上的目录设为**第一搜索目录**，`romfs:/res/mods` 排在其后；按 `mod.json` 的 id 去重时，低优先级的那份会被 `shadowed by higher-priority duplicate` 跳过，所以**两份共存不会重复加载，SD 卡那份生效**。模组默认 `ConfigVar<bool>(..., true)` 自动启用。

两点注意：

- 卡上若还留着 beta 期的旧 `randomizer.dusk`，先删掉；旧包会挡住新包。上游 `hardware_findings.inc` 把本版 `randomizer.dusk` 的 SHA256（`4ed580714ed5b22a64fda7c6049d8d28e6d3d962c817a46cbd1b27c9702ad11c`）标为 `Tested`，beta 包会被拒绝。
- 若模组显示 refused / 未激活，进设置 → 诊断 → **Native Mods (H37)** 把模式设为 **Execute**（全新安装默认即为 Execute）。`randomizer.dusk` 带 `lib/switch-arm64/mod.so`，`dev.aleks2.cross_save.dusk` 没有 Switch 库、走 `lib/linux-aarch64` 兼容模式，两者都由本 NRO 的运行时加载器加载。

产物校验（本机已做）：NRO0 魔数在偏移 16；菜单串 `v1.1.1-cn`、NACP `1.1.1-cn`、数字版本 `1.1.1.0`；RomFS 共 56 个文件，内含 `//res/mods/randomizer.dusk`（6,483,388）、`//res/mods/dev.aleks2.cross_save.dusk`（2,574,119）、四份 i18n 词表、三款 HarmonyOS 字体与中文词条。代码段与补模组前的 NRO 完全一致（61,820,928 字节），差异只来自 RomFS 多出的 8.6 MiB 模组包。

## 五、已知限制

- **只汉化移植层 UI，不含游戏本体文本。** 剧情对话、道具名、游戏内菜单文字来自原版资源。
- **首次启动要自己编译着色器。** 上游 Release 的 NRO 里打包了 `initial_dawn_cache.db`（71.5 MiB）与 `initial_dksh_cache.bin`（13.6 MiB）两份预编译缓存，本分支**故意不打**。原因见下节：它们必须在真机上为确切的驱动采集，Aurora 会忽略驱动不匹配的种子，而本分支用的是 Mesa 26.2.4 Horizon（上游 26.2.3）。启动后 Aurora 会把 `romfs:/initial_pipeline_cache.db.zst` 里的管线清单在后台编译一遍，首次在 Tegra X1 上是数分钟，界面有进度和 Skip；跑完写 `cache/shader_prep_done.txt` 标记，之后基本全是缓存命中。想省掉这一步，可在真机上用 `platforms/switch/tools/make-shader-seed.py` 采集后，通过 `-DALEKS2_DAWN_CACHE_SEED` / `-DALEKS2_DKSH_CACHE` 重编。
- **未在真机全面验证。** 编译期与包内容已校验，中文断行、字体渲染、首次预热的实际表现待测。
- 207 条保持英文，其中 198 条是有意为之，原因见上。
- 词表与英文原文强耦合：上游改写某句提示时，那句会静默回落英文。每次同步上游后跑一次 `tools/extract-ui-strings.py` 重新比对。
- 仅面向 Switch；PC 版（AppImage）是另一条线。

## 六、维护与对齐上游

完整流程见 **[i18n-zh.md](i18n-zh.md)**：加词改词、aurora 升级后补丁锚点怎么调、版本号怎么跟上游走、rebase 时可能冲突的文件怎么处理、本地构建三要素。

简要步骤：

```bash
git remote add upstream https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition.git
git fetch upstream main && git rebase upstream/main
python tools/extract-ui-strings.py          # 找新出现的英文串
python tools/build-i18n.py ci/i18n/source-strings.json ci/i18n/zh-cn.json res/i18n
```

上游升版本时，把 workflow 里的 `-DDUSK_APP_VERSION_OVERRIDE=v1.1.1-cn`、产物名与 artifact 名一起改成新版本（规则见 `cmake/DuskAppVersion.cmake`）；同时从新 Release NRO 的 RomFS 里重新提取两个 `.dusk`，替换 `platforms/switch/mod-packages/` 并更新该目录 README 里的哈希。别用 PC 版包顶替 `randomizer.dusk`，Switch 包里的 `lib/switch-arm64/mod.so` 是必需的。

## 七、为什么比上游 Release 的 NRO 小

上游 v1.1.1 的 `dusklight.nro` 是 170.7 MiB，本分支 103.0 MiB。**不是编译裁剪，也不是压缩差异**，而是上游在发布时额外传入了四个不在 git 里的二进制：

| 文件 | 大小 | 本分支 |
|---|---:|---|
| `initial_dawn_cache.db` | 71.5 MiB | 不打（留给真机生成） |
| `initial_dksh_cache.bin` | 13.6 MiB | 不打（留给真机生成） |
| `res/mods/randomizer.dusk` | 6.2 MiB | **已打进** |
| `res/mods/dev.aleks2.cross_save.dusk` | 2.5 MiB | **已打进** |

本分支则多出三款 HarmonyOS 中文字体（19.7 MiB）、四份 i18n 词表（0.5 MiB）与少量模组资源。代码段两边只差约 4.3 MiB，来自 Mesa 版本（26.2.3 / 26.2.4）与构建预设不同，没有发现调试符号被裁掉的迹象。两个 NRO 的 RomFS 清单可用 `aleks-local/nro/{ours,upstream}-romfs.txt` 对照。

## 八、提交链

| 提交 | 内容 |
|---|---|
| `ab30befe` | i18n 引擎、词表、字体、设置项、CI |
| `6dfcf7e3` | `settings.cpp` 的 Switch 声明移到 `__SWITCH__` 块内 |
| `f2f40295` | `libvulkan.a` 重建索引、开启运行时模组加载器 |
| `bd187046` | ranlib 改从 devkitA64 的 `tools/bin` 解析 |
| `687cbf57` | 默认界面语言改为 `zh-cn` |
| `593ce04a` | 版本号固定为 `v1.1.1-cn` |
| `c8c137ae` / `db2ce630` | 维护指南、更新摘要、README 中文版入口 |
| `5e174a84` | 内置两个 `.dusk` 模组包，CI 传入 `ALEKS2_BUNDLED_MOD_PACKAGES`（run `42227654038` 由此构建出最终 NRO） |
| `623451dc` | 与本分支无关的 CI 导出 workflow，不改动产物 |
| 文档提交 | 更新摘要、维护指南、README 中文版入口随最终产物数字更新 |

---

代码与词表公开，欢迎提 issue 指正译文。
