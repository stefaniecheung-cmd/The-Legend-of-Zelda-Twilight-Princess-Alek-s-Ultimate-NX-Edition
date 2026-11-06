# 更新摘要 · Dusklight v1.1.1-cn（Switch 简体中文界面）

| | |
|---|---|
| 上游 | [Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition](https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition) `main`，基线版本 **1.1.1** |
| 本分支 | `stefaniecheung-cmd/...` 的 `main` @ `593ce04a` |
| 发布 tag | `v1.1.1-cn` |
| 产物 | `dusklight-1.1.1-cn.nro`，98,963,453 字节（94.4 MiB） |
| SHA256 | `7ff5f620beee34aef563a9e3fff9b37b341b7179cc7ab6fd57047f47da250e17` |
| 构建 | GitHub Actions run `42207198181`（success），`devkitpro/devkita64` 容器 |

> 这是上游的个人汉化分支，不是官方版本。只汉化**移植层界面**，游戏内剧情对话、道具名等原版游戏资源不在范围内。

---

## 一、这一版做了什么

1. **界面默认简体中文。** 主菜单、设置页及各项说明、存档对话框、模组加载与更新提示、崩溃报告、按键绑定名，全部译入。设置里可切回 English。
2. **补上中文字形。** 打包 HarmonyOS Sans Regular（7.9 MB），原版字体没有汉字。
3. **把 Switch 构建跑通并搬进 CI。** 上游需要的 `libvulkan.a` 没有公开的 Horizon 预编译版，另建 `stefaniecheung-cmd/mesa-switch` 编出 Mesa 26.2.4 Horizon SDK（release `sdk-26.2.4`，48.3 MB / 93 文件），CI 公开下载，不依赖 token。

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

汉化本体 18 个文本文件，加 1 个字体二进制、1 个构建 workflow、README 与两份文档。

| 类别 | 文件 |
|---|---|
| 查表引擎（新增） | `src/dusk/ui/i18n.cpp`、`src/dusk/ui/i18n.hpp` |
| 注入点（新增） | `ci/patches/aurora-translate-callback.py` |
| 词表 | `res/i18n/zh-cn.xml`、`res/i18n/en.xml`（恒等映射兜底） |
| 词表源数据与工具 | `ci/i18n/{zh-cn,source-strings,extra-seed}.json`、`ci/i18n/not-translated.txt`、`tools/build-i18n.py`、`tools/extract-ui-strings.py` |
| 语言设置 | `src/dusk/settings.h`、`src/dusk/settings.cpp`（`ui.language`，默认 `zh-cn`）、`src/dusk/ui/settings.cpp`（下拉选择） |
| 启动接线 | `src/dusk/ui/ui.cpp`（初始化 + 注册回调）、`files.cmake`、`CMakeLists.txt` |
| 字体（新增，二进制） | `res/HarmonyOS_Sans_Regular.ttf` |
| 构建 | `.github/workflows/build-switch.yml` |
| 文档 | `docs/dev/i18n.md`、`docs/dev/i18n-zh.md`、`docs/dev/RELEASE-NOTES-zh.md`、README 顶部中文版说明 |

`ci/patches/aurora-translate-callback.py` 作用于子模块 `extern/aurora`（本分支用的是 `Alexgg1014/aurora-aleks-nx`），不打补丁就只会显示英文。

## 四、安装与校验

1. 把 `dusklight-1.1.1-cn.nro` 放到 SD 卡 `/switch/` 目录，从相册（hbmenu）启动。
2. 默认就是简体中文；想回英文进设置 → 界面语言 → English。
3. 存档与设置沿用上游路径，替换 NRO 不会丢。

产物校验（本机已做）：NRO0 魔数在偏移 16；菜单串 `v1.1.1-cn`、NACP `1.1.1-cn`、数字版本 `1.1.1.0`；包内含 `zh-cn.xml`、HarmonyOS 字体与中文词条。

## 五、已知限制

- **只汉化移植层 UI，不含游戏本体文本。** 剧情对话、道具名、游戏内菜单文字来自原版资源。
- **未在真机全面验证。** 编译期与包内容已校验，中文断行、字体渲染的实机表现待测。
- 207 条保持英文，其中 198 条是有意为之，原因见上。
- 词表与英文原文强耦合：上游改写某句提示时，那句会静默回落英文。每次同步上游后跑一次 `tools/extract-ui-strings.py` 重新比对。
- 仅面向 Switch；PC 版（AppImage）是另一条线。

## 六、维护与对齐上游

完整流程见 **[i18n-zh.md](i18n-zh.md)**：加词改词、aurora 升级后补丁锚点怎么调、版本号怎么跟上游走、rebase 时 7 个可能冲突的文件怎么处理、本地构建三要素。

简要步骤：

```bash
git remote add upstream https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition.git
git fetch upstream main && git rebase upstream/main
python tools/extract-ui-strings.py          # 找新出现的英文串
python tools/build-i18n.py ci/i18n/source-strings.json ci/i18n/zh-cn.json res/i18n
```

上游升版本时，把 workflow 里的 `-DDUSK_APP_VERSION_OVERRIDE=v1.1.1-cn`、产物名与 artifact 名一起改成新版本（规则见 `cmake/DuskAppVersion.cmake`）。

## 七、提交链

| 提交 | 内容 |
|---|---|
| `ab30befe` | i18n 引擎、词表、字体、设置项、CI |
| `6dfcf7e3` | `settings.cpp` 的 Switch 声明移到 `__SWITCH__` 块内 |
| `f2f40295` | `libvulkan.a` 重建索引、开启运行时模组加载器 |
| `bd187046` | ranlib 改从 devkitA64 的 `tools/bin` 解析 |
| `687cbf57` | 默认界面语言改为 `zh-cn` |
| `593ce04a` | 版本号固定为 `v1.1.1-cn` |
| 文档提交 | 维护指南、本摘要、README 中文版入口 |

---

代码与词表公开，欢迎提 issue 指正译文。
