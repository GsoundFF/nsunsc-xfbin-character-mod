# nsunsc-xfbin-character-mod

《火影忍者究极风暴羁绊》(NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS / `NSUNSC`)
**角色模型 Mod 制作与排错**的 AI agent skill。

用 XFBIN 文件把角色 S 的外观换到角色位 T 上，**T 的动作 / 招式 / 奥义全部保留**。
覆盖三种模型来源，并明确区分它们各自的做法与风险。

---

## 这个 skill 解决什么

| 你想做的事 | 对应章节 |
|---|---|
| 把游戏自带角色（天天/手鞠/Rin/小南/天天校服…）的模型换到别的角色位 | ① `references/01-original-model-swap.md` |
| 装一个从 Nexus / 网页下载的现成 mod | ② `references/02-web-download-mods.md` |
| 把自己在 Blender 做的模型 / 外部模型放进游戏 | ③ `references/03-own-model-blender.md` |
| 改投技（换动画 + 换判定参数 / 伤害 / 特效） | `SKILL.md` 第 6 节 |
| 眼睛没贴图 / 眼睛跑到下巴 / 嘴巴外凸 | `SKILL.md` 第 5 节 |
| 选人界面没模型 / 进战斗卡加载 / 闪退 | `SKILL.md` 第 9 节 + `references/05-troubleshooting.md` |

---

## 三种来源的区别（一句话版）

| | ① 原始人物模型 | ② 网页下载 mod | ③ 自己的模型 |
|---|---|---|---|
| 模型从哪来 | 游戏自带角色包 `E:\fight date\spc_角色模型\spc` | 别人做好的 `.nsc` / `.zip` / `.rar` | Blender 自制或外部模型（MMD 等） |
| 骨架 | **保留来源角色骨架**，只做等长改名 | 照作者配置，**不要动** | 优先保留自己骨架 + 等长改名；重绑是最后手段 |
| 主要风险 | 忘保留目标角色原版攻击文件 ⇒ 动作变了 | 目录层级放错 / mod 冲突 ⇒ 扫不到 | 重绑骨架 ⇒ 选人无模型 + 进战斗崩溃 |
| 收尾 | 眼睛/嘴巴坐标烘焙 | 一般不用 | 眼睛/嘴巴坐标烘焙（或隐藏 chunk） |

---

## 核心结论（这个 skill 最想传达的）

1. **最稳的路线是"等长前缀改名 + 保留来源角色骨架"**：
   `2tenbod1.xfbin` 内部所有 `2ten` → `2kar`，放进香磷槽位，骨架用天天自己的。
   动作仍然正常，因为动画轨道按**骨骼名**匹配，两角色核心骨架同名。
   > 实测：手鞠 247 处等长替换后选人正常、进战斗正常、动作仍是香磷的。

2. **攻击文件必须用目标角色原版**（`bod1c` / `bod1l` / `bod1s` / `bod1acc`），
   否则普通攻击和投技会变成来源角色自己的。

3. **不要重绑骨架**（除非核心骨骼不同名）。把外部网格重绑到目标 227 根骨骼
   ⇒ **选人界面无模型 + 进战斗崩溃**（实测）。

4. **`prm` 参数块头部 `u16 @ offset 2` 必须等于 `块长度 - 4`**。
   写错 ⇒ 游戏解析越界 ⇒ **选人界面模型消失、进战斗一直卡加载**。
   这是本项目最容易写错、最难从现象反推的字段。

5. **投技 = 动画页 + `prm_mot` 参数，两块都要换**。
   只换动画 ⇒ **动画放完了还没出伤害、也没有打飞特效**。

6. **Mod Manager 打包前必须完全退出游戏**，且**同一时间只能启用一个**
   替换同一个 `2karbod1.xfbin` 的 mod。

7. **先保证"选人显示 + 能进战斗"，再处理动作归属，最后才是外观微调。**
   任何导致消失/卡加载/崩溃的改法**一律先回退**。

---

## 安装

### 作为 DSH / Claude Code 风格的 skill

把本目录复制到 skills 根目录：

```powershell
# DeepSeek Harness
Copy-Item -Recurse .\nsunsc-xfbin-character-mod "$env:USERPROFILE\.dsh\skills\"

# 或 Codex
Copy-Item -Recurse .\nsunsc-xfbin-character-mod "$env:USERPROFILE\.codex\skills\"
```

目录名必须与 `SKILL.md` frontmatter 里的 `name` 一致（`nsunsc-xfbin-character-mod`）。

### 依赖（都是可选，但强烈建议）

| 依赖 | 用途 | 获取方式 |
|---|---|---|
| `xfbin_lib` | 解析 / 写出 XFBIN、dump 结构、回读校验 | `cc2_xfbin_blender` 插件自带（`addons\XFBINImporter42\xfbin_lib`） |
| `cc2_xfbin_blender` + Blender 4.2 | 导入 / 导出 XFBIN 模型 | 社区插件；4.2 需打补丁（见 `03-own-model-blender.md`） |
| NSC Mod Manager | 打包 mod 成 `data_win32_modmanager.cpk` | 游戏 mod 工具链（`net9.0-*\NSC_ModManager.exe`） |
| NSC-Toolbox | 参数编辑参考 | `net10.0-*\NSC-Toolbox.exe` |
| Python 3.9+ | 跑 `scripts/` 下的脚本 | 标准库即可 |

`scripts/` 下的脚本会自动从 `--game-dir` / `--xfbin-lib` / 环境变量 `XFBIN_LIB`
定位 `xfbin_lib`；找不到时会降级为纯字节模式（仍能做等长改名与大小字段校验）。

---

## 脚本

```powershell
# 等长前缀改名（默认 dry-run，只预览 + 校验）
python scripts\rename_prefix.py --src 2tmrbod1.xfbin --src-code 2tmr --dst-code 2kar

# 真的写出，并顺带把目标角色原版攻击文件放进槽位
python scripts\rename_prefix.py --src 2tmrbod1.xfbin --src-code 2tmr --dst-code 2kar `
    --out "<Mod>\Resources\Files\data\spc\2karbod1.xfbin" --write `
    --keep-attack "E:\fight date\spc_角色模型\spc" --keep-code 2kar

# dump 结构 / 骨架 / 参数块大小字段
python scripts\dump_xfbin.py <文件.xfbin> --game-dir "<游戏目录>" --params --bones

# 修正 prm 大小字段（防"选人无模型 / 卡加载"）
python scripts\prm_mot_size_fix.py --prm 2karprm.bin.xfbin --game-dir "<游戏目录>" --fix-size --write

# 移植投技参数条目（4rin -> 2kar）
python scripts\prm_mot_size_fix.py --prm 2karprm.bin.xfbin `
    --src-prm 4rinprm.bin.xfbin --prm-name 2karprm_mot --src-prm-name 4rinprm_mot `
    --src-code 4rin --dst-code 2kar --game-dir "<游戏目录>" `
    --port-throw --fix-size --out 2karprm.bin.xfbin --write
```

> `prm_mot_size_fix.py` 的 `--port-throw` 路径已用**黄金对照**验证：
> 从香磷原版 prm + Rin 原版 prm 出发，脚本产物与项目里已验证可用的成品
> **md5 逐字节一致**（`0E47D3C286FD6844C5122E802A6D497A`）。

---

## 目录结构

```
nsunsc-xfbin-character-mod/
├── SKILL.md                          # 主入口：三种来源分流 + 最短开工顺序 + 全流程 + 配置 + 排错速查
├── README.md                         # 本文件
├── CHANGELOG.md
├── LICENSE
├── references/
│   ├── 01-original-model-swap.md     # ① 游戏自带角色模型替换（等长改名 + 逐字节校验）
│   ├── 02-web-download-mods.md       # ② 网页下载 mod 的安装与判别
│   ├── 03-own-model-blender.md       # ③ 自己的模型（Blender 注入导出 / 重绑 / 坐标烘焙）
│   ├── 04-xfbin-format.md            # XFBIN/NUCC 格式、块类型、prm 字段铁律
│   └── 05-troubleshooting.md         # 失败路线全集（F1–F36）+ 症状排查表
└── scripts/
    ├── rename_prefix.py              # 等长前缀改名 + 逐字节校验（dry-run 默认）
    ├── dump_xfbin.py                 # 结构 / 骨架 / 贴图 / 材质 / 参数块 dump
    └── prm_mot_size_fix.py           # prm 大小字段修正 + 投技参数移植
```

---

## 免责声明

本仓库只包含**文档与工具脚本**，不包含任何游戏资源、模型、贴图或游戏本体文件。
使用者需自备正版游戏。所有游戏内资源版权归原作者与发行商所有。
请仅在**单人/离线**场景使用，不要在联机对战中破坏他人体验。

---

## 许可

MIT，见 `LICENSE`。
