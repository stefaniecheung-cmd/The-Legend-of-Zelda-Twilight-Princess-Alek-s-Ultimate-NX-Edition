# 简体中文汉化维护指南

这份文档给以后接手的人看：汉化是怎么接进引擎的、怎么加词改词、上游更新时怎么对齐。
本版的改动摘要与发布信息见 [RELEASE-NOTES-zh.md](RELEASE-NOTES-zh.md)。

## 一、结构：三层，互不侵入

```
res/i18n/zh-cn.xml          ← 词表（键 = 英文原文，值 = 中文）
        ↑ 生成
ci/i18n/zh-cn.json          ← 词表的源数据，日常只改这个
ci/i18n/source-strings.json ← 从源码抽出来的英文全集，只读

src/dusk/ui/i18n.cpp/.hpp   ← 查表引擎，提供 i18n::translate()
        ↑ 注册
src/dusk/ui/ui.cpp          ← 启动时 i18n::initialize() + set_translate_callback(i18n::translate)

extern/aurora/lib/rmlui/SystemInterface_Aurora.cpp
                            ← TranslateString() override，由补丁脚本自动注入
```

关键设计：**没有改任何一处 UI 调用点**。RmlUi 渲染文本时走 `TranslateString`，我们把整句英文丢进词表查，查到就换掉，查不到原样返回。因此：

- 某句没译 → 显示英文，不会空白，不会崩
- 上游改了源码文案 → 那句自动变回英文（因为键对不上），不会编译失败
- 上游新增界面 → 新文案自动是英文，等你补词

`res/i18n/en.xml` 是恒等映射（键 = 值），给没翻译的条目兜底。默认语言在 `src/dusk/settings.cpp` 里写死为 `zh-cn`，设置页可以切回 `en`。

## 二、加词改词

```bash
# 1. 改 ci/i18n/zh-cn.json，键是英文原文，值是中文
# 2. 重新生成 XML
python tools/build-i18n.py ci/i18n/source-strings.json ci/i18n/zh-cn.json res/i18n
# 3. 想看源码里有哪些英文还没进词表
python tools/extract-ui-strings.py
```

`build-i18n.py` 不会拒绝任何缺失：没译的键会用英文原文作为值写进 XML。
生成的 XML 里含 `&`、`'` 这类字符时会被转义；引擎读回时做实体解码，否则带 `&` 的词条会匹配不上（第一版踩过这个坑）。

### [TOKEN] 词条

源码里还有一类 UI 串写作 `"[TOKEN]"`（拼接句、参数化句），引擎会把方括号里的裸 token 名丢进同一本词典查。这部分词条来自 `ci/i18n/tokens.json`（每条 `{token: {en, zh}}`，从 v1.1.1-cn 重构前的 token 词表回收），`build-i18n.py` 会自动把它们并入两份 XML：

- `en.xml`：`TOKEN → 英文原文`（英文界面不显示裸 token）；
- `zh-cn.xml`：`TOKEN → 中文`（没有中文时回落英文）。

源码里新增 `[TOKEN]` 时，把它连同英文原文加进 `tokens.json` 即可；`tools/check_i18n_tokens.py` 会核对源码里的 token 是否都有词条。v1.1.1-cn 发布时这 233 个 token 没进词典，界面会直接显示 `[XXX]`，v1.1.3-cn 已修复。

### 词表数字怎么读（v1.1.3-cn）

| 口径 | 数量 |
|---|---|
| `source-strings.json` 抽出的源串 / XML 整句条目 | 1449 |
| `zh-cn.json` 里的译文映射 | 1394 |
| 整句中真正换成中文（值 ≠ 键） | **1222（84.3%）** |
| `[TOKEN]` 词条（en/zh-cn 各一份） | 233，全部有中文 |
| 保持英文的整句 | 227 |

227 = `not-translated.txt` 里逐条审过的 227 条（含 20 条 RML 模板碎片与 8 条加载器诊断的抽取噪音、9 条英文专名）。

### 故意不译的条目

`ci/i18n/not-translated.txt` 逐条记录了不译的原因：

| 类别 | 数量 | 为什么 |
|---|---|---|
| 协议字段名 | 27 | `Content-Length`、`Sec-WebSocket-Key` 这类 HTTP/WebSocket 头，翻了会坏协议 |
| 拼接片段 | 28 | 运行时拼好的整句才会进回调，这些字面量永远匹配不到 |
| 加载器内部诊断 | 143 | ELF 表、重定位、TLS 相关，只写日志，不进界面 |

补词之前先看这份清单，避免白做功。

## 三、对齐上游更新

这是最需要小心的一步。上游是 `Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition`。

```bash
git remote add upstream https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition.git
git fetch upstream main
git rebase upstream/main        # 或者 merge，看你的习惯
```

同步完必做两件事：

1. 跑 `python tools/extract-ui-strings.py`，把新出现的英文串与 `ci/i18n/source-strings.json` 比对，补进 `zh-cn.json` 后重建 XML。
2. 用 `-DDUSK_APP_VERSION_OVERRIDE=v<上游版本>-cn` 重新构建，别把版本号留在旧值。

### 冲突面有多大

汉化本体改了 18 个文本文件（见 [更新摘要](RELEASE-NOTES-zh.md) 第三节清单），另加字体二进制、`platforms/switch/mod-packages/` 下两个上游 `.dusk` 模组包、构建 workflow，以及 README 和文档。其中大部分是**纯新增**（词表、引擎、工具、补丁脚本、字体、模组包、文档），rebase 时零冲突。真正可能撞的只有 7 个：

| 文件 | 改了什么 | 冲突处理 |
|---|---|---|
| `CMakeLists.txt` | 配置期调用补丁脚本那段 | 保留上游，重新插入 aurora 补丁调用块 |
| `files.cmake` | 列表里加 `src/dusk/ui/i18n.cpp` | 直接加回去 |
| `src/dusk/settings.h` | 加 `ConfigVar<std::string> language` | 直接加回去 |
| `src/dusk/settings.cpp` | 注册 `ui.language`，默认 `zh-cn` | 直接加回去 |
| `src/dusk/ui/settings.cpp` | 设置页「界面语言」下拉 | 直接加回去 |
| `src/dusk/ui/ui.cpp` | 两行：`i18n::initialize()` + 挂回调 | 直接加回去 |
| `README.md` | 顶部中文版说明块 | 重新贴回去，下载链接的 tag 换成新版本 |

### 上游换了 aurora 版本时

`ci/patches/aurora-translate-callback.py` 是按文本锚点往 aurora 里插代码的，改 4 个文件、26 行纯增量、可重复执行。如果 aurora 改了你锚定的那几行，configure 会以 `FATAL_ERROR` 停下，日志写着 `i18n: ci/patches/aurora-translate-callback.py failed`。

处理办法：打开脚本，看它 `ANCHORS` 里对不上的那条，按新代码调整锚点文本，然后单独跑一次验证：

```bash
python ci/patches/aurora-translate-callback.py extern/aurora
python ci/patches/aurora-translate-callback.py extern/aurora   # 第二遍应该全是 already present
```

第二遍能幂等退出，才算改对。注意 `extern/aurora` 是子模块，升级后别忘了重新打补丁；CI 的 configure 步会自动跑，本地手动构建要自己跑一次。

### 上游升版本号时

版本号不在源码里写死，由 configure 参数决定，见 `.github/workflows/build-switch.yml` 的 Configure 步：

```bash
-DDUSK_APP_VERSION_OVERRIDE=v1.1.3-cn
```

上游出 1.2.0 就改成 `v1.2.0-cn`。规则在 `cmake/DuskAppVersion.cmake`：必须是 `vX.Y.Z` 或 `vX.Y.Z-后缀`，后缀只允许字母数字和点。菜单显示 `v1.2.0-cn`，NACP 显示 `1.2.0-cn`（上限 15 字符），数字版本 `1.2.0.0`。
产物文件名 `dusklight-<版本>-cn.nro` 与 artifact 名也在同一个 workflow 里，改版本时一起改，别只改一半。

## 四、构建

CI 在 `.github/workflows/build-switch.yml`。push 到 `main` 且改动命中 `src/**`、`res/**`、`cmake/**`、workflow 等路径时自动跑（纯文档改动不会触发），产物是 `dusklight-<版本>-cn.nro`，也可以手动 `workflow_dispatch`。

本地构建要先解决三件事，细节见 [building-switch.md](building-switch.md)：

1. `devkitpro/devkita64` 容器（直接装 devkitPro 会遇到 `pkg.devkitpro.org` 403）
2. Mesa Horizon SDK 的 `libvulkan.a`，解压后必须 `aarch64-none-elf-ranlib -D` 重建索引，否则链接报四千多个 `core::panicking::*` 未定义。SDK 是 `stefaniecheung-cmd/mesa-switch` 的 release `sdk-26.2.4`
3. `-DALEKS2_NATIVE_MOD_LOADER=ON -DALEKS2_SYMBOL_CHECK_STRICT=OFF`，否则缺 `aleks2_live_mod_threads`
4. 想和 Release 一样带上内置模组，`-DALEKS2_BUNDLED_MOD_PACKAGES="<绝对路径>/randomizer.dusk;<绝对路径>/dev.aleks2.cross_save.dusk"`。两个包在 `platforms/switch/mod-packages/`，是从上游 v1.1.1 NRO 的 RomFS 原样提取的，来源与哈希见该目录 README

> **不重编也能装模组**：把这两个 `.dusk` 直接拷到 `sdmc:/switch/dusklight/mods/` 重启即可，上游 `docs/user/mods.md` 就是这么写的。`mods_init()` 把卡上的 `mods/` 设为第一搜索目录，优先级高于 `romfs:/res/mods`；同 id 时低优先级的那份被 `shadowed by higher-priority duplicate` 跳过，两份共存不会重复加载。模组默认自动启用（`ConfigVar<bool>(..., true)`）。Release 里把两个 `.dusk` 也作为独立资产提供，就是为了这条更快的路。若模组显示 refused，检查设置 → 诊断 → **Native Mods (H37)** 是否为 **Execute**。

着色器种子（`ALEKS2_DAWN_CACHE_SEED` / `ALEKS2_DKSH_CACHE`）不要随便塞：它们带驱动标识，换驱动就会被 Aurora 忽略。本分支用自建 Mesa 26.2.4 Horizon，与上游 26.2.3 不同，交给真机首次启动时自己编译并落盘。

## 五、变更记录

| 提交 | 内容 |
|---|---|
| `ab30befe` | i18n 引擎、词表、字体、设置项、CI |
| `6dfcf7e3` | `settings.cpp` 的 Switch 声明移到 `__SWITCH__` 块内 |
| `f2f40295` | `libvulkan.a` 重建索引；开启运行时模组加载器 |
| `bd187046` | ranlib 改从 devkitA64 的 `tools/bin` 解析 |
| `687cbf57` | 默认界面语言改为 `zh-cn` |
| `593ce04a` | 版本号固定为 `v1.1.1-cn` |
| `5e174a84` | 打包两个内置 `.dusk` 模组包，CI 传 `ALEKS2_BUNDLED_MOD_PACKAGES` |
| 发布 | tag `v1.1.1-cn`，Release 附 `dusklight-1.1.1-cn.nro` 与本摘要 |
| `652af97` | 合并上游 v1.1.2 + v1.1.3 |
| `6ad63b2` | 回收 233 条 `[TOKEN]` 词条（v1.1.1-cn 回归修复）、补译 6 条、抽取工具 `\xNN` 修复、版本号 `v1.1.3-cn` |
| 发布 | tag `v1.1.3-cn`，Release 附 `dusklight-1.1.3-cn.nro` 与更新摘要 |
