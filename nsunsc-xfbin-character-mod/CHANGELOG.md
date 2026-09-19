# Changelog

All notable changes to this skill are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-08-15

Initial release, distilled from the NSUNSC (究极风暴羁绊) model-mod debug records:
Rin throw port, Ino throw port, 泳装小南→香磷, 天天→香磷, 手鞠→香磷, 校服天天→井野02,
Blender XFBIN 导出流程。

### Added
- `SKILL.md` — 主入口。**开工第一步按"模型从哪来"分流**为三种来源：
  ① 原始人物模型（游戏自带）、② 网页下载的 mod、③ 自己的模型（Blender / 外部）。
  含公共落盘规则、Mod Manager 铁律、稳定路线、Blender 规范、
  眼睛/嘴巴收尾、投技移植、`Characode`/`BaseModel` 配置规则、验证清单、排错速查。
- `references/01-original-model-swap.md` — 等长前缀改名路线（含角色代码表、逐字节校验、
  完整构建脚本、可选处理项、已知边界）。
- `references/02-web-download-mods.md` — 下载包的形态判别（`.nsc` 实为 ZIP / zip / rar / 裸 .xfbin）、
  mod 根目录判定、冲突检测、安全提示。
- `references/03-own-model-blender.md` — 三条子路线（保留骨架改名 / 重绑骨架 / 改顶点）、
  Blender 4.2 注入导出设置与常见错误、刚性网格坐标烘焙、轴向陷阱、
  材质贴图槽数量与像素格式两种眼睛根因。
- `references/04-xfbin-format.md` — NUCC 头（28 字节字段表）、块表结构、
  为什么等长替换安全 / 为什么整体重写危险、页与块布局、`2karbod1` 与 `2karbod1l`
  的真实结构、`prm_mot` 大小字段铁律、名字表残留的正确理解。
- `references/05-troubleshooting.md` — 失败路线全集 + 症状→怀疑→动作速查表 + 调试纪律。
- `scripts/rename_prefix.py` — 等长前缀改名，默认 dry-run，
  校验：前缀等长 / 长度不变 / 归一化后逐字节一致 / 无残留 / 可选 xfbin_lib 回读。
- `scripts/dump_xfbin.py` — 页/块/骨架/贴图/材质 dump + `prm_*` 大小字段体检。
- `scripts/prm_mot_size_fix.py` — `u16@2 = len-4` 重算 + 投技三个参数条目移植
  （块内等长改名、条目数不变、写前复核、写后回读）。

### Verified
- `rename_prefix.py`：对 `2tmrbod1.xfbin` → `2kar` 复现 247 处等长替换，
  归一化后逐字节一致、长度不变、无残留；对 `2tenbod1.xfbin` → `2kar` 端到端跑通，
  改名后骨骼数（192）/ 模型数（14）/ 分组数（3）与源文件完全一致，
  攻击文件 `c/l/s/acc` 四个 md5 与目标原版相同。
- `prm_mot_size_fix.py --port-throw`：从香磷原版 prm + Rin 原版 prm 出发，
  产物与项目里已验证可用的成品 **md5 逐字节一致**
  （`0E47D3C286FD6844C5122E802A6D497A`）。
- `dump_xfbin.py`：正确报出 `2karprm_*` 全部 8 个参数块的
  `u16@2 == len-4`（含 `mot` 40352→40348、`sklslot` 3745→3741）；
  并实测确认手鞠原版 `2tmreye_l` 材质是 **1 组贴图槽**、香磷原版与重建后的 mod 都是 **2 组**。
- 各角色骨骼数实测：天天 192 / 手鞠 200 / 小南泳装 219 / 香磷 227。
- 冲突检测复现：`modmanager` 下 **293 条覆盖记录 → 243 个不同游戏文件**，
  `data/spc/2karbod1.xfbin` 被 **15 个 mod** 同时覆盖。

### Corrected during review
- **Mod Manager 打包产物路径**：实测在
  `<游戏目录>\moddingapi\mods\base_game\data_win32_modmanager.cpk`（140200592 字节），
  **不在游戏根目录**；根目录同名文件是否存在取决于 ModdingAPI 是否在场。文档已改为"两个路径都查"。
- **源前缀残留的判定分文件**：`prm_mot` 必须 0 残留；`bod1l` **允许**残留
  （实测 Rin 版 11 处 `4rin`、Ino 版 11 处 `1ino`，都在动画块内嵌的源路径字符串里）。
  原先把"无残留"写成通用规则，已修正为只看页面/块名/引用表。
- **F3 与 F1 的自相矛盾**已消除：优先等长改名，重绑骨架只在核心骨骼不同构时才考虑，
  且必须先做最小可测版本。

### Notes
- 本仓库仅含文档与脚本，**不含任何游戏资源**。
- 关键结论均来自实测失败与成功记录；不确定处已标注"待确认"
  （如 CPK 写盘位置的裁决规则、双 mod 覆盖顺序、Mod Manager 递归扫描深度上限）。
