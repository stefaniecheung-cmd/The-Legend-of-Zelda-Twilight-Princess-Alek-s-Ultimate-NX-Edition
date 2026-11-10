# 更新摘要 · Dusklight v1.1.3-cn（Switch 简体中文界面）

| | |
|---|---|
| 上游 | [Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition](https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition) `main`，基线版本 **1.1.3**（合并上游 tag `v1.1.3`） |
| 发布 tag | `v1.1.3-cn`（annotated tag，指向发布时的 `main`） |
| 产物 | `dusklight-1.1.3-cn.nro`，108,041,097 字节（103.0 MiB） |
| SHA256 | `e702c03c7f8519e36f1d52b1a5017a103c54fcfddc81fb2487c046b9d3fd9c8b` |
| 构建 | GitHub Actions run `42860215054`（success），`devkitpro/devkita64` 容器 |

> 这是上游的个人汉化分支，不是官方版本。只汉化**移植层界面**，游戏内剧情对话、道具名等原版游戏资源不在范围内。

---

## 一、这一版做了什么

1. **对齐上游 1.1.3。** 合并上游 `v1.1.2` 与 `v1.1.3` 两个版本：
   - **Kakariko 的 Malo Mart 不再崩溃**（卡卡利科村商店加载即崩，来自反编译代码与编译器行为的差异，上游 issue #14）；
   - **铁靴能正常脱下了**（铁靴装在 Twilit Essentials 的 Z 键时会"脱了又穿"，灯笼与油瓶同理）；
   - **Twilit Essentials 3.0.2 可以加载**；从 HOME 菜单关闭游戏后更新也能正常安装；
   - **设置 → Graphics 新增 Disable Water Refraction**（关闭水面折射效果，节省 GPU）；
   - 自更新与模组加载器的多处加固（详见上游两个版本的 Release Notes）。
2. **修复 v1.1.1-cn 的一个汉化回归：233 个 `[TOKEN]` 界面串会直接显示原文。** v1.1.1-cn 重构汉化管线时，把词表重建为"整句英文键"，但源码里还有 233 个以 `"[TOKEN]"` 形式书写的界面串（存档管理器的按钮与提示、模组浏览器、手柄配置页、图形调谐器等），引擎按裸 token 名查词典，而词典里没有这批词条——上一版这些位置显示的是 `[CREATE_BACKUP]` 这类原始 token。本版从 v1.1.1-cn 重构前的 token 词表回收了全部 233 条翻译（含中文），并新增 `ci/i18n/tokens.json` 让 `build-i18n.py` 自动并入词表，`en.xml` 同步收录英文原文（英文界面也不再显示裸 token）。
3. **补齐上游新增与此前遗漏的界面文案 6 条**：Disable Water Refraction 及其说明、Swing Direction Animations 说明、LiveSplit 连接说明、卡带模组加载说明、手柄自定义按键绑定说明。
4. **修复抽取工具对 `\xNN` 转义的处理**：`"\xE2\x86\x90 Return"` 之前会被抽成乱码键，`← 返回` 词条有从词表里丢失的风险；现在会正确还原为 UTF-8。
5. **确认两个内置模组包与上游 v1.1.3 逐字节一致**（上游 v1.1.3 Release 直接发布了 `dev.aleks2.cross_save.dusk`，SHA256 与本仓库打包的完全相同），无需替换。

## 二、汉化方案：不动一处 UI 调用点

RmlUi 渲染每个字符串时会调用 `SystemInterface::TranslateString`，aurora 图形层实现了这个接口但一直原样返回。在那一层挂一个全局回调即可覆盖全部界面文字：

```
RmlUi 渲染文本 → TranslateString → 拿整句英文查 res/i18n/zh-cn.xml
                                 → 查到就换，查不到原样返回英文
                                 → 含 [TOKEN] 时按裸 token 名查同一本词典
```

- 键就是**英文原文整句**，精确匹配（另支持 `标题\n详情` 的首行匹配）。
- 查不到只回落英文，不会空白、不会崩；上游改文案或加新界面也不会编译失败，**不会与上游代码冲突**。
- aurora 侧的 `TranslateString` override 由 `ci/patches/aurora-translate-callback.py` 在 CMake 配置期自动注入，26 行纯增量、幂等。
- 引擎做了 XML 实体解码，含 `&`、`'` 的词条也能命中。

### 覆盖率（v1.1.3-cn）

| 口径 | 数量 |
|---|---|
| 抽取到的源串 / `zh-cn.xml` 整句条目 | 1449 |
| `[TOKEN]` 词条（`ci/i18n/tokens.json`，en/zh-cn 各一份） | 233，**全部有中文** |
| 整句中真正换成中文（值 ≠ 键） | **1222（84.3%）** |
| 保持英文的整句 | 227 |

整句 + token 合计：**1455 / 1682（86.5%）**。227 条整句保持英文，全部逐条审过、理由见 `ci/i18n/not-translated.txt`（协议字段名、运行时拼接片段、加载器日志诊断、RML 模板抽取碎片、英文专名）。

## 三、改动清单（相对 v1.1.1-cn）

| 类别 | 文件 |
|---|---|
| 上游同步 | 合并 `v1.1.2` + `v1.1.3`（23 个文件，含 `self_update`、`settings.cpp` 等；冲突 3 处已按"保留汉化 token 化、其余取上游"解决） |
| token 词表（新增） | `ci/i18n/tokens.json`（233 条，从 v1.1.1-cn 重构前的 token 词典回收） |
| 词表生成 | `tools/build-i18n.py`（并入 `tokens.json`）、`tools/extract-ui-strings.py`（`\xNN` 按 UTF-8 还原） |
| 词表 | `res/i18n/zh-cn.xml`、`res/i18n/en.xml`（重建：1449 整句 + 233 token） |
| 词表源数据 | `ci/i18n/zh-cn.json`（+6 条）、`ci/i18n/source-strings.json`（重新抽取）、`ci/i18n/not-translated.txt`（+29 条已审不译项） |
| 版本号 | `.github/workflows/build-switch.yml`（`-DDUSK_APP_VERSION_OVERRIDE=v1.1.3-cn`、产物与 artifact 名） |
| 文档 | 本摘要、`docs/dev/i18n-zh.md`（token 词条机制与新版数字）、README 中文版说明 |

## 四、安装与校验

### NRO 本体

1. 把 `dusklight-1.1.3-cn.nro` 放到 **`sdmc:/switch/dusklight/`**（不是 `/switch/` 根下）。游戏盘镜像放同目录或 `sdmc:/switch/dusklight/discs/`。
2. **在 HOME 菜单按住 R 启动任意游戏做 title takeover**，从列表里选本程序。**不要从相册 / hbmenu 启动**——applet 模式内存不足，程序会打印提示后直接退出（上游 `docs/user/install.md`）。
3. 默认就是简体中文；想回英文进设置 → 界面语言 → English。存档与设置沿用上游路径，替换 NRO 不会丢。
4. 首次启动会显示 **Preparing shaders**，属正常现象，可以等它跑完或点 Skip。

### 两个内置模组：两条路，效果相同

Release 的 Assets 里除了 NRO，还单独提供 `randomizer.dusk`（6,483,388 字节，SHA256 `4ed58071…`）与 `dev.aleks2.cross_save.dusk`（2,574,119 字节，SHA256 `dd9fa48c…`），与上游 v1.1.1 / v1.1.3 发布的原包逐字节一致。

| | 做法 | 适用 |
|---|---|---|
| A（开箱即用） | 什么都不做，两个包已由 `ALEKS2_BUNDLED_MOD_PACKAGES` 打进 `romfs:/res/mods/` | 新装、或愿意重新下载 NRO |
| B（更快） | 把两个 `.dusk` 拷到 **`sdmc:/switch/dusklight/mods/`** 后重启，无需重下 NRO | 已经装了旧 NRO、或想要更小体积的 NRO |

两点注意：

- 卡上若还留着 beta 期的旧 `randomizer.dusk`，先删掉；旧包会挡住新包。
- 若模组显示 refused / 未激活，进设置 → 诊断 → **Native Mods (H37)** 把模式设为 **Execute**（全新安装默认即为 Execute）。

产物校验：菜单串 `v1.1.3-cn`、NACP `1.1.3-cn`、数字版本 `1.1.3.0`；RomFS 内含 `//res/mods/randomizer.dusk`（6,483,388）、`//res/mods/dev.aleks2.cross_save.dusk`（2,574,119）、四份 i18n 词表（en/zh-cn 各 1682 条目）、三款 HarmonyOS 字体与中文词条。

## 五、已知限制

- **只汉化移植层 UI，不含游戏本体文本。** 剧情对话、道具名、游戏内菜单文字来自原版资源。
- **首次启动要自己编译着色器。** 上游 Release 打包了两份预编译着色器缓存，本分支**故意不打**（它们必须在真机上为确切的驱动采集；本分支用 Mesa 26.2.4 Horizon）。首次预热数分钟，界面有进度和 Skip。
- **未在真机全面验证。** 编译期与包内容已校验，中文断行、字体渲染、首次预热的实际表现待测。
- 227 条整句保持英文，全部逐条审过、有意为之，原因见 `ci/i18n/not-translated.txt`。
- 词表与英文原文强耦合：上游改写某句提示时，那句会静默回落英文。每次同步上游后跑一次 `tools/extract-ui-strings.py` 重新比对，并跑 `tools/check_i18n_tokens.py` 核对 token 词条。
- 仅面向 Switch；PC 版（AppImage）是另一条线。

## 六、维护与对齐上游

完整流程见 **[i18n-zh.md](i18n-zh.md)**：加词改词、token 词条怎么补、aurora 升级后补丁锚点怎么调、版本号怎么跟上游走、rebase 时可能冲突的文件怎么处理、本地构建三要素。

简要步骤：

```bash
git remote add upstream https://github.com/Alexgg1014/The-Legend-of-Zelda-Twilight-Princess-Alek-s-Ultimate-NX-Edition.git
git fetch upstream main && git merge upstream/v<新版本>
python tools/extract-ui-strings.py          # 找新出现的英文串
python tools/build-i18n.py ci/i18n/source-strings.json ci/i18n/zh-cn.json res/i18n
python tools/check_i18n_tokens.py           # 核对 [TOKEN] 词条
```

上游升版本时，把 workflow 里的 `-DDUSK_APP_VERSION_OVERRIDE=v1.1.3-cn`、产物名与 artifact 名一起改成新版本（规则见 `cmake/DuskAppVersion.cmake`）；同时核对新 Release 的两个 `.dusk` 是否有更新（哈希比对），替换 `platforms/switch/mod-packages/` 并更新该目录 README 里的哈希。别用 PC 版包顶替 `randomizer.dusk`，Switch 包里的 `lib/switch-arm64/mod.so` 是必需的。

## 七、为什么比上游 Release 的 NRO 小

上游 v1.1.3 的 `dusklight.nro` 是 170.7 MiB（178,989,461 字节），本分支 103.0 MiB。**不是编译裁剪，也不是压缩差异**，而是上游在发布时额外传入了四个不在 git 里的二进制：

| 文件 | 大小 | 本分支 |
|---|---:|---|
| `initial_dawn_cache.db` | 71.5 MiB | 不打（留给真机生成） |
| `initial_dksh_cache.bin` | 13.6 MiB | 不打（留给真机生成） |
| `res/mods/randomizer.dusk` | 6.2 MiB | **已打进** |
| `res/mods/dev.aleks2.cross_save.dusk` | 2.5 MiB | **已打进** |

本分支则多出三款 HarmonyOS 中文字体（19.7 MiB）、四份 i18n 词表与少量模组资源。

## 八、提交链（v1.1.3-cn）

| 提交 | 内容 |
|---|---|
| `652af97` | 合并上游 v1.1.3（含 v1.1.2） |
| `6ad63b2` | token 词条回收（`ci/i18n/tokens.json`）、build-i18n 并入 token、抽取工具 `\xNN` 修复、6 条新译文、词表重建、版本号 `v1.1.3-cn` |
| 文档提交 | 本摘要回填最终产物数字（run `42860215054`，42 分钟构建完成） |

---

代码与词表公开，欢迎提 issue 指正译文。
