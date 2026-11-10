# 内置模组包（Switch）

这两个 `.dusk` 是上游 `Alexgg1014/...` **v1.1.1 Release 的 `dusklight.nro` 里 RomFS 的原样提取**，未做任何修改。上游 v1.1.3 Release 单独发布的 `dev.aleks2.cross_save.dusk` 已核对与本目录逐字节一致（SHA256 相同，2026-11 核对），故无需替换；上游 Release 不单独提供 `randomizer.dusk`，但上游把两个包都打进了 NRO 的 `romfs:/res/mods/`。

| 文件 | 大小（字节） | SHA256 |
|---|---:|---|
| `randomizer.dusk` | 6,483,388 | `4ed580714ed5b22a64fda7c6049d8d28e6d3d962c817a46cbd1b27c9702ad11c` |
| `dev.aleks2.cross_save.dusk` | 2,574,119 | `dd9fa48c4593b0a46e950dd80d33619dd105d1d6a79e8a37203b6e8c8ae7b63e` |

两者都是 ZIP：`randomizer.dusk` 内含 `lib/switch-arm64/mod.so`、`mod.json` 与贴图资源；`dev.aleks2.cross_save.dusk` 只有 PC/Android 的原生库，按上游设计，内置模组的原生代码由 NRO 提供，包里主要给 `mod.json` 和资源。

## 怎么进 NRO

`platforms/switch/CMakeLists.txt` 的 `ALEKS2_BUNDLED_MOD_PACKAGES` 是一个分号分隔的路径列表，CMake 会按**文件名**把每个包拷进 `romfs:/res/mods/`。CI 在 `.github/workflows/build-switch.yml` 的 Configure 步把本目录两个文件的绝对路径传进去，并在 Configure 前打印 SHA256、在打包后检查 NRO 里确实出现了这两个文件名。

## 对齐上游时

上游升版本后，从新 Release 的 NRO RomFS 里提取同名文件替换这里，更新上表哈希，并同步 `docs/dev/RELEASE-NOTES-zh.md` 里的产物大小与校验值。不要用 PC 版 `.dusk` 顶替 `randomizer.dusk`：Switch 包里的 `lib/switch-arm64/mod.so` 是必需的。

## 这里没有着色器缓存

`initial_dawn_cache.db`（71.5 MiB）和 `initial_dksh_cache.bin`（13.6 MiB）不属于本目录。上游也是用 `-DALEKS2_DAWN_CACHE_SEED` / `-DALEKS2_DKSH_CACHE` 从外部传入的，注释明确写了「not kept in git」，必须在真机上用 `tools/make-shader-seed.py` 采集，且带驱动标识——换驱动就会被忽略。本分支使用自建 Mesa 26.2.4 Horizon，与上游 26.2.3 不同，因此交给首次启动的「Preparing shaders」自行编译并落盘缓存。
