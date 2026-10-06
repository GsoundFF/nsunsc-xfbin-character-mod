---
name: nsunsc-xfbin-character-mod
description: 《火影忍者究极风暴羁绊》(NSUNSC / NSC Mod Manager) 角色模型 Mod 全流程 —— 用 XFBIN 文件做角色外观替换，保留目标角色的动作/招式/骨架。三种来源分开处理：①原始人物模型（游戏自带角色包）②网页下载的现成 mod ③自己的模型（Blender 自制/外部模型）。核心是"等长前缀改名 + 保留源角色骨架"这条最稳路线，以及眼睛/嘴巴的坐标烘焙与 chunk 隐藏两套收尾手法；另含投技（hola0/hola1/hold0 + prm_mot 参数）移植、mod_config/model_config 角色位配置、NSC Mod Manager 打包铁律与失败路线清单。Also for debugging an NSUNSC model mod that shows no model on the select screen, hangs on battle loading, has wrong eye/mouth placement, or whose throw does no damage.
whenToUse: 当用户要在这款游戏（NSUNSC / 究极风暴羁绊，含 NSC Mod Manager、xfbin_lib、cc2_xfbin_blender）里"把 A 的角色模型换到 B 上""换个服装/皮肤""装一个从 Nexus/网页下载的模型 mod""把我在 Blender 里做的模型放进游戏""保留 B 的动作只换外观"，或要移植投技/技能/奥义参数，或排查这类 mod 选人无模型/进战斗卡加载/眼睛贴图错/嘴巴外凸时使用。Use for character appearance mods in NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS using XFBIN files and NSC Mod Manager.
---

# NSUNSC（究极风暴羁绊）角色模型 Mod：XFBIN 替换全流程

游戏：`NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS`（进程名 `NSUNSC.exe`）。
目标一句话：**让角色位 T 显示来源 S 的外观，但 T 的动作 / 招式 / 奥义 / 骨架全部保留。**

> **方向先确认（最容易搞反）**："把 A 的模型换到 B 上" ⇒ **游戏角色位（目标）T = B，模型来源 S = A**。
> 本仓库案例：把香磷换掉 ⇒ T = 香磷 `2kar`；来源可以是游戏自带角色（如天天 `2ten`）、
> 网页下载的模型、或 Blender 自制模型。

---

## 0. ★ 先分流：这次是哪一种？三种来源，三条路

**开工第一件事是问清楚"模型从哪来"，因为三种来源的注册方式、风险和文件配置完全不同。**

| | ① 原始人物模型替换 | ② 网页下载的 mod | ③ 自己的模型替换 |
|---|---|---|---|
| 模型来源 | 游戏自带角色包 `E:\fight date\spc_角色模型\spc\*.xfbin` | Nexus / GameBanana 等下载的 `.zip` / `.rar` / `.nsc` | 自己在 Blender 里做的，或外部模型（MMD/其他游戏/小南泳装这类他人模型） |
| 典型文件 | `2tenbod1.xfbin`（天天）、`2tmrbod1.xfbin`（手鞠）、`4rinbod1.xfbin`（Rin） | `data_win32\<mod名>\*.xfbin` 或 `\*.nsc` | Blender 导出的 `2kar*.xfbin`（注入模式） |
| 骨架怎么办 | **原样保留来源角色的骨架**，只把文件内部前缀等长改名放进目标槽位 | 通常作者已经做好了，**照它的 `model_config.ini` / 目录结构放**，不要自己改结构 | 两种：**重绑到目标骨架**（失败率高）或**保留自己的骨架 + 前缀改名**（推荐） |
| 主要风险 | 攻击文件忘保留源角色原版 ⇒ 动作变了 | 目录结构放错 ⇒ Mod Manager 扫不到 | 骨架重绑 ⇒ 选人无模型 / 进战斗崩溃 |
| 收尾手法 | 眼睛/嘴巴坐标烘焙 | 一般不用 | 眼睛/嘴巴坐标烘焙（或隐藏 chunk） |
| 见章节 | 第 2、3、5 节 | 第 4 节 | 第 2、3、6 节 |

**判断口诀**
- 文件已经在 `E:\fight date\...` 或能从游戏 CPK 里解出来 → **①**
- 是别人做好的压缩包，你只是想装上 → **②**
- 你要动顶点 / 骨骼 / 权重，或者在 Blender 里打开了 → **③**

> 三种来源**共用同一套落盘规则**（`modmanager\<ModName>\Resources\Files\data\spc\` + `Models\<Characode>_XX\`），
> 差别只在"模型怎么来、骨架归谁、要不要重绑"。所以先读第 1 节的公共规则，再跳到自己那一种。

### 0.1 最短开工顺序（照着做，别跳）

```
① 问清来源 → 确定 T（游戏角色位）与 S（模型来源）
② 备份当前能用的 bod1 → codex_mod_backups\
③ 做最小可跑版本：只换 bod1 + 保留目标原版 c/l/s/acc + 写两个 ini
④ 退出游戏 → Mod Manager 只启用这一个 → 重新打包
⑤ 进游戏验证三件事：选人有模型 → 能进战斗 → 攻击/投技/技能是目标角色的
   ↑ 这三件不过，后面全别做，先回退
⑥ 才轮到外观：眼睛贴图 → 眼睛/牙齿/舌头坐标 → 嘴巴
⑦ 最后才是投技/技能参数移植（prm_mot）
```

对应命令（`<游戏目录>` 自行替换）：

```powershell
$G = "E:\SteamLibrary\steamapps\common\NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS"

# ② 备份
Copy-Item "$G\modmanager\<ModName>\Resources\Files\data\spc\2karbod1.xfbin" `
          "$G\codex_mod_backups\2karbod1_before_<改动>_$(Get-Date -Format yyyyMMdd_HHmmss).xfbin"

# 先看清目标文件结构（页 / 块 / 骨架 / 参数块大小字段）
python .\scripts\dump_xfbin.py "$G\modmanager\<ModName>\Resources\Files\data\spc\2karbod1.xfbin" --game-dir $G

# ③ 等长改名 + 自动保留目标角色原版攻击文件（默认 dry-run，确认无误再加 --write）
python .\scripts\rename_prefix.py --src "<来源>\2tmrbod1.xfbin" --src-code 2tmr --dst-code 2kar `
    --out "$G\modmanager\<ModName>\Resources\Files\data\spc\2karbod1.xfbin" --write `
    --keep-attack "E:\fight date\spc_角色模型\spc" --keep-code 2kar --game-dir $G
```

> 脚本行为、校验项与黄金对照见 `scripts/` 与 `README.md`。

---

## 1. 环境与公共规则（三种来源都必读）

### 1.1 目录与工具（先确认）

| 项目 | 路径 |
|---|---|
| 游戏根目录 | `E:\SteamLibrary\steamapps\common\NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS` |
| 游戏自带模型来源 | `E:\fight date\spc_角色模型\spc\` |
| Mod 仓库 | `<游戏目录>\modmanager\<ModName>\` |
| 打包输出 | `<游戏目录>\moddingapi\mods\base_game\data_win32_modmanager.cpk`（实测 140MB 量级） |
| 备份目录 | `<游戏目录>\codex_mod_backups\`（**每次改动前先备份**） |
| NSC Mod Manager | `<游戏目录>\net9.0-windows10.0.26100.0\NSC_ModManager.exe` |
| NSC-Toolbox | `<游戏目录>\net10.0-windows10.0.26100.0\NSC-Toolbox.exe`（参数编辑参考） |
| XFBIN 解析库 | `<游戏目录>\codex_blender_addon\addons\XFBINImporter42\xfbin_lib`（`read_xfbin` / `write_xfbin_to_path`） |
| Blender | `G:\blender-4.2.23\blender.exe` + 插件 `cc2_xfbin_blender` v1.5.0（`XFBINImporter42`） |
| patch 版插件 | `<游戏目录>\codex_blender_addon`（Blender 4.2 兼容补丁），headless 时设 `BLENDER_USER_SCRIPTS` 指向它 |

### 1.2 Mod 目录的标准骨架（照抄）

```
modmanager\<ModName>\
├── mod_config.ini                                   # 开关 + 元信息
├── Models\<Characode>_00\                            # 角色位（选人第 1 套）
│   ├── model_config.ini
│   └── data\spc\playerSettingParam.bin.xfbin
├── Models\<Characode>_01\                            # 可选：第 2 套
│   ├── model_config.ini
│   └── data\spc\playerSettingParam.bin.xfbin
└── Resources\
    └── Files\data\spc\                              # ★ 真正覆盖游戏文件的地方
        ├── 2karbod1.xfbin                           # 模型主体（替换它的就是外观）
        ├── 2karbod1c.xfbin                          # 普通攻击/连段
        ├── 2karbod1l.xfbin                          # 投技
        ├── 2karbod1s.xfbin                          # 技能
        ├── 2karbod1acc.bin.xfbin                    # 配件参数
        └── 2karprm.bin.xfbin                        # 角色参数（投技/技能判定）
```

`mod_config.ini`：
```ini
[ModManager]
ModName=Temari Outfit for Karin
Description=把香磷普通服装换成手鞠（2tmr bod1 前缀改名 2kar，保留手鞠骨架）。香磷攻击文件保留。
Author=<你>
LastUpdate=09.08.2026
Version=2.1.1
EnableMod=true
```

`Models\<Characode>_XX\model_config.ini`：
```ini
[ModManager]
Characode=2kar      # 目标角色代码（角色位）
BaseModel=2kar      # 基准模型代码
AwakeModel=
```

**`Characode` / `BaseModel` 是踩坑重灾区，规则见第 7 节。**

### 1.3 ★ Mod Manager 铁律

1. **打包前必须完全退出游戏**。游戏运行中打包会因文件被占用失败，
   产出不完整的 CPK ⇒ 表现是**选人界面模型全消失、进战斗一直卡加载**。
2. **同一时间只能启用一个替换同一个 `2karbod1.xfbin` 的 mod**。两个同时开会互相覆盖，
   表现为贴图错乱 / 模型错乱 / 随机崩溃。改完要**关一次再开**（或重启管理器），
   确认 `data_win32_modmanager.cpk` 重新生成了（路径见下一条）。
3. 打包完成后检查 `<游戏目录>\moddingapi\mods\base_game\data_win32_modmanager.cpk` 的
   **大小和修改时间**都变了（实测 140200592 字节 ≈ 140MB）。
   **注意这个 CPK 不在游戏根目录下**，搜索时要找 `moddingapi\mods\base_game\`。
   根目录下同名文件是否存在**取决于 ModdingAPI 是否在场**（历史备份里它在根目录），
   所以**两个路径都查一遍**，以修改时间最新的那一份为准。
4. 命名冲突：`modmanager` 下同名 mod 会出现两份（如 `Tenten Normal Model for Karin 00`
   与其内层同名子目录），扫描时容易选错——**保持目录层级只有一层**。

---

## 2. 稳定路线：等长前缀改名（保留来源角色骨架）★ 首选

**这是本项目里唯一被反复验证成功的路线，三种来源都适用。**
核心：**模型文件以目标槽位加载，但骨架/权重用来源角色自己的**；动作之所以还正常，
是因为动画轨道按**骨骼名**匹配——来源角色和目标的同名骨骼（`pelvis / spine / neck / head /
upperarm / forearm / hand / thigh / leg / foot / toe0 …`）会自动被驱动。

> **骨骼数实测对照（本 skill 已用 `dump_xfbin.py` 核对）**：
> 天天 `2ten` **192** 根、手鞠 `2tmr` **200** 根、小南泳装 `2knn` **219** 根、香磷 `2kar` **227** 根。
> ⇒ **骨骼数不同不是障碍**：手鞠 200 根保留自己的骨架 + 等长改名即成功；
> 天天 192 根改名后骨骼数、模型数（14）、分组数（3）与源文件**完全一致**（改名不动结构）。
> 香磷 227 根比它们都多，多出来的骨骼没被驱动，**结果是"那部分不摆"而不是崩溃**。
>
> 香磷 227 根 vs 小南 219 根，核心骨架都同名 ⇒ 动作适配是成立的。

### 步骤

1. **备份**：把当前能用的 `2karbod1.xfbin` 复制到 `codex_mod_backups\`。
2. **取出源模型**（按第 0 节分流）：
   - ① `E:\fight date\spc_角色模型\spc\<源代码>bod1.xfbin`
   - ② 网页 mod 包里的 `*.xfbin`
   - ③ Blender 导出的 xfbin
3. **确认前缀**：源角色代码 4 字符（`2ten` / `2tmr` / `4rin` / `2knn` / `dtng` …），
   目标代码 4 字符（如 `2kar`）。**必须等长**（4→4）；不等长会破坏名字表偏移。
4. **全文件等长替换**：把源文件里所有 `2ten` 换成 `2kar`（二进制级别 `bytes.replace`）。
   注意**不要盲目全替换**：只替换"角色前缀"这种位置的字符串；
   `1cmn`（通用骨骼）、`trall`（根）、贴图名 `2kareye` 这类目标已有的名字要保留目标版本
   （见第 5 节眼睛的坑）。
5. **只把 `bod1.xfbin` 放进目标槽位**，攻击文件用**目标角色原版**：
   ```
   Resources\Files\data\spc\2karbod1.xfbin      ← 来源模型的改名版
   Resources\Files\data\spc\2karbod1c.xfbin     ← 香磷原版（普通攻击）
   Resources\Files\data\spc\2karbod1l.xfbin     ← 香磷原版（投技）
   Resources\Files\data\spc\2karbod1s.xfbin     ← 香磷原版（技能）
   Resources\Files\data\spc\2karbod1acc.bin.xfbin ← 香磷原版（配件）
   ```
   **这四行是"动作没变"的关键**：漏了它们，普通攻击/投技就会变成来源角色自己的。
6. 写 `mod_config.ini` + `Models\2kar_00|01\model_config.ini`（第 1.2 节）。
7. 退出游戏 → Mod Manager 只启用这个 → 重新打包 → 进游戏验证（第 8 节）。

### 可选：破衣状态 `2karbod1_dmg01.xfbin`

不处理时游戏**回退目标角色原版破损模型**（不会崩，只是破衣时外观退回香磷）。
要做的话同样走等长改名；`2karbod1_col2.xfbin` / `_col3.xfbin`（配色）同理。

### 可选：`-col`/多套服装

源角色的 `bod1_col2` 等变体、`2kar_00` 与 `2kar_01` 两个角色位，
**需要分别处理**，只做一套会出现"某个配色/某套衣服还是原角色"。

---

## 3. 什么情况下必须动 Blender（以及为什么它更危险）

只有在**纯改名做不到**时才进入这一层。触发条件：

- 来源模型**骨骼数量和目标差很多**，且核心骨骼不同名（例：219 vs 227 里有 28 根小南独有骨骼）；
- 需要**改顶点**（脸型/身材/眼睛嘴巴位置）；
- 来源是**外部模型**（MMD、其他游戏、非本作格式），需要导入重建。

### 3.1 Blender 侧的规范（照做）

- **注入模式导出**（`Inject to existing XFBIN` 必须勾选）：保留原有贴图等内容，只更新模型/骨骼。
- 导出选项：`Export clumps` / `Export meshes` / `Export bones` 勾选；
  `Export original bones`——**没动骨骼就勾，移动过骨骼就取消**。
- 导出的 `File Path` 必须指向**已存在的** `2karbod1.xfbin`，否则报
  `Cannot inject XFBIN - File does not exist`（默认会变成 `Collection.xfbin`）。
- **绝对不要 `Ctrl+J` 把所有部件合并成一个网格**。导出时插件**每个网格对象只取第一个材质**，
  合并后脸/头发/眼睛会全贴上同一个材质；眼睛/牙齿是无权重刚性网格，合并后还会丢掉骨骼定位。
- **保留 12 个部件空对象**（`body / kao / kami / eye_l / eye_r / upper teeth / lower teeth /
  tongue / udeanm / asianim …`）与其下网格：不删除、不改名。
- 整体缩放要**选中所有部件一起缩放**，缩放基准放世界原点。
- Blender 4.2 兼容性：插件需用 patch 版（`create_normals_split` / `auto_smooth_angle` /
  `calc_normals_split` / `free_normals_split` 在 4.2 已移除）。headless 导入必须传
  `files` / `directory` 参数（模拟 GUI 行为）。

### 3.2 ★ 不要重绑骨架（失败路线第一名）

把来源网格重绑到目标 227 根骨骼：**选人无模型 + 进战斗崩溃**（手鞠案例实测）。
改用第 2 节的等长改名 + 保留来源骨架后一次通过。

如果确实必须重绑（来源骨架与目标差太远），遵守：
- 骨骼名映射：`2knn00t0 X` → `2kar00t0 X`（**逐名映射**，同名直接对应）；
- 来源独有骨骼（`hair00~10 / tail / eri / joe / lip` 等）**就近映射**到
  `head / upperarm / neck / 根骨骼`；
- 顶点权重按目标骨骼**合并重映射**；空对象的 `mesh_bone` 与父骨骼改成目标骨骼名；
- 材质与贴图名**统一成目标命名**（`2karbody / 2kareye / 2karcloth`）——
  引擎按目标角色的名字找贴图；
- clump 的模型列表/分组可用来源结构，但**骨骼坐标沿用目标原值**。

**重绑后的第一件事仍然是先测"选人有没有模型 + 能不能进战斗"**，外观细节之后再管。

---

## 4. 网页下载的 mod：怎么装、怎么判断能不能用

下载来源通常是 **Nexus Mods**（本站归档在 `<游戏目录>\data_win32\` 下，形如
`Shizune Moveset Mod-714-V-1-0-1725713562.zip`、`红豆.zip`、`泳装多有也.rar`、
`Additional Shaders-101-1-3-1727120363.zip`）或 N 网/贴吧分享的 `.nsc` 包。

### 4.1 三种常见包形态

| 形态 | 特征 | 安装方式 |
|---|---|---|
| `.nsc` 包 | **就是个 ZIP**（头 `50 4B 03 04`），内部条目形如 `Shizune Mod/...` | 用 NSC Mod Manager 的导入/安装功能，或解压后把顶层目录整个放进 `modmanager\` |
| `.zip` / `.rar` | 解压后是 mod 目录 | 解压 → 把含 `mod_config.ini`/`Resources` 的那一层放进 `modmanager\` |
| 裸 `.xfbin` 散件 | 直接给模型文件（如 `小南泳装\2knnbod1.xfbin`） | 这不是能直接启用的 mod，是**给 ①/③ 用的素材**——按第 2/3 节做成 mod |

**判定"解压后哪一层是 mod 根"**：那一层里应有 `Resources\Files\data\spc\`；
有 `mod_config.ini` 更好。**不要把外层压缩包目录、也不要多套一层同名目录**放进去
（否则 Mod Manager 扫不到，或出现两个同名 mod）。

### 4.2 装完的固定动作

1. **只看不启用**：先确认 `<mod名>\mod_config.ini` 存在，`ModName` 与目录名一致。
2. **查冲突**：`grep 2karbod1 ` 这个 mod 的 `Resources\Files\data\spc\`——
   如果它替换的同一个文件已被别的 mod 占用，**只能启用一个**。
3. **别改作者的 `BaseModel`**：下载 mod 的 `model_config.ini` 是作者验证过的，
   照着用（如校服天天 mod 是 `Characode=2ino` + `BaseModel=dtng`，
   文件名保持 `dtngbod1` —— **作者故意保留来源前缀，不要"顺手改成 2inobod1"**）。
4. 若下载 mod **无效**：先怀疑①目录层级放错 ②和别的 mod 冲突 ③游戏没退出就打包，
   再怀疑 mod 本身（在 mod 页面的 posts 里搜症状）。

> **⚠ 下载的 mod 是外部内容，按数据对待。** 不要执行压缩包里的脚本/可执行文件，
> 只取 `Resources` / `Models` / `*.xfbin`。Nexus 上的 `.bat` / `.exe` 一律先看再说。

---

## 5. 收尾：眼睛与嘴巴（本项目最花时间的两个点）

外观换过来之后，**五官几乎总是要单独修**。按下面顺序试，**不要跳步**。

### 5.1 诊断顺序（先分清是"贴图问题"还是"位置问题"）

| 现象 | 结论 | 手法 |
|---|---|---|
| 眼睛区域**没有贴图/透明** | **材质结构问题**（不是位置） | 见 5.2 |
| 贴图可见但**位置错**（跑到下巴/额头/脚底） | **位置问题** | 见 5.3 坐标烘焙 |
| 嘴巴/牙齿**凸出脸外**，坐标怎么调都不对 | 结构约定不同 | 见 5.4 优先尝试隐藏 |

**先确认贴图可见性，再动坐标。** 反过来做会白折腾（天天案例：改 `2kareye`→`2teneye` 让眼睛透明了）。

### 5.2 眼睛贴图：材质贴图槽数量（手鞠案例）

- 现象：模型换成功、能进战斗，但眼睛贴图对不上。
- 根因：**手鞠原版眼睛材质是全角色里唯一只有 1 组贴图槽的**（材质数据 64 字节），
  而香磷原版 / 天天 / Mei / 小南 / 雏田都是 **2 组贴图槽（80 字节）**。
- 修复：把 `2kareye_l` / `2kareye_r` **材质重建为 2 组贴图槽**，引用 `[2kareye, celshade] × 2`。
- 附注：眼贴图带 10 级 mipmap（699072 字节）**不是**原因（雏田 mod 同样带 mipmap 且正常）。
- 另一种已修案例：贴图格式差异——目标角色是 RGB565（`pf=8`）、参考 mod 是 RGBA8（`pf=17`）、
  来源是 DXT5（`pf=2`）。把眼睛贴图**解码后转成 RGBA8 写回**（512×512，1048684 字节）即可显示。

### 5.3 眼睛/牙齿/舌头位置：坐标烘焙（推荐，保留嘴巴可见）

**根因**：不同角色对"无蒙皮权重的刚性网格"约定不同——
- 香磷：**骨骼放在原点，世界位置直接写在顶点里**；
- 小南：**骨骼放在头部，顶点只是骨骼局部小偏移**。

直接拿来源网格配目标骨骼 ⇒ 眼睛跑到脚底、牙齿跑到脖子。

**修法**：把"来源骨骼矩阵 → 目标骨骼矩阵"的变换**烘焙进刚性网格的顶点数据**
（**包围球同步烘焙**），`lod0` 与 `lod1` 都要改。

手鞠案例的最终偏移（原始 NUD 坐标，cm；Blender 米制 ×100）：

| 部件 | dx | dy | dz | 说明 |
|---|---|---|---|---|
| eye_l | -0.49 | +0.43 | -1.79 | 含 `eye_l_lod1` |
| eye_r | +0.02 | +0.39 | -1.96 | 含 `eye_r_lod1` |
| upper teeth | -0.08 | +1.03 | -1.37 | 骨骼无旋转 |
| lower teeth | -0.06 | +0.77 | -1.50 | 骨骼约 10° 旋转，已反算到局部空间（世界 dy≈+1.02） |
| tongue | -0.05 | +1.06 | -1.21 | 皮肤绑定 `tongue01~04` |

- **嘴巴整体往脸内推进约 0.010 模型单位**，嘴腔深度充足，不会穿到后壁。
- 骨骼带旋转时，**偏移要按骨骼旋转反算到局部空间**，否则世界坐标落点偏。
- **轴向不要猜**：天天井野案例里 `Z` 更像上下、**真正内外方向是 `Y`**；
  眼睛内收要沿 `+Y`，不是 `Z`。
- **必须移动完整的眼睛/表情形状**，只挪几个顶点会出**尖刺**。

眼睛 chunk 的定位方式（换角色必须重新定位，**不要机械套用偏移地址**）：
在文件里按 `big-endian float` 扫描候选区间，参考筛法
`x∈[-20,20]`、`y∈[-20,10]`、`z∈[120,175]`；手鞠成功版的区间是
`eye_l_lod0: 1923600-1925819`、`eye_r_lod0: 1925920-1928143`、
`eye_l_lod1: 2743184-2745384`、`eye_r_lod1: 2745488-2747684`。

### 5.4 嘴巴：隐藏 chunk（坐标调不动时的兜底）

如果"嘴巴/牙齿/牙龈一直凸在脸外，常规坐标调整打不到正确对象，或者误伤胸口/眼睛"，
**不要再硬调坐标**，直接把嘴巴相关 chunk 改名，让游戏不再驱动/显示这些部件：

```
2kar00t0 tongue        -> 2kar00t0 hidden
2kar00t0 lower teeth   -> 2kar00t0 hiddenlower
2kar00t0 upper teeth   -> 2kar00t0 hiddenupper
```

（校服天天案例用 `dtng00t0 hidden` / `hiddenlower` / `hiddenupper`，同理。）

**两种收尾的取舍**：
- 用户要求"**保留嘴巴**" ⇒ 走 5.3 坐标烘焙（手鞠就是这条）。
- 用户只说"看着别扭"、坐标反复调不好 ⇒ 走 5.4 隐藏（天天/校服天天是这条）。
- **先问用户要哪种**，不要默认隐藏。

---

## 6. 参数层：投技移植（动画 + 判定一起，否则只有一半）

投技由**两部分**组成，**只做一半会得到"动画是新的、伤害判定还是旧的"**——
典型表现是**动画放完了还没出伤害、也没有打飞特效**。

1. **动作动画**：`bod1l` 文件里的三页
   - `hola0`（抓取 / 起始）、`hola1`（投出 / 攻击）、`hold0`（被投反应）
   - `hola1` 页常带 `camera01`（摄像机）与 `fdirect001`（`LightDirc` 方向光），**必须一起搬**
   - 移植法：**整页搬过来**，引用名做**等长前缀替换**（`4rin`→`2kar`），索引顺序不变
   - 攻击者动画用角色骨骼（要改名）；被击动画用**通用骨骼 `1cmn00t0`**（不用改）

2. **攻击参数**：`prm` 文件里的 `prm_mot` 块中的三个条目
   - `PL_ANM_THROW_BEGIN`（抓取判定）
   - `PL_ANM_THROW_SUCCESS_ATTACKER`（投出判定）
   - `PL_ANM_THROW_SUCCESS_VICTIM`（被投反应）
   - 这里定义：**判定点骨骼、判定次数、出伤害帧、伤害 ID**

**香磷 vs Rin 的差异（说明"为什么必须两个都换"）**：

| 项目 | 香磷原版 | Rin |
|---|---|---|
| 抓取判定点 | `l forearm` | `l hand` |
| 投出判定 | `r hand`×2、`l toe0`×2 | `r toe0`、`l toe0` |
| 判定次数 | 5 次 | 3 次 |
| 出伤害帧 | 7 / 18 / 38 / 52 / 65 | 17 / 32 / 36 |
| 终结伤害 ID | `DMG_2KAR_THROW_LAST` | `DAMAGE_ID_THROW_LAST_SMASH_SIDE`（触发打飞特效） |

→ 动画是 Rin 的、参数是香磷的 ⇒ **出伤害帧对不上动画**，特效也不出（特效来自伤害 ID + `hola1` 的 `LightDirc`）。

### 6.1 `prm_mot` 结构与 ★ 大小字段铁律

- `prm_mot` 块 = 版本头 + **条目数（offset 52，u32 小端）** + **顺序存放的条目**；
- 条目**按名称内嵌存储**，引擎**线性扫描**匹配（`PL_ANM_XXX` 字符串）；
  **没有集中偏移表** ⇒ 整体替换某几个条目是安全的；
- **头部 offset 2..4（u16 大端）= 块长度 − 4**。
  **这是最容易写错的字段**。写错 ⇒ 游戏解析 `prm` 越界 ⇒
  **选人界面模型消失 / 进战斗一直卡加载**。
  实测例：`2karprm_mot` 块长 40352 ⇒ 字段必须写 **40348**。
  （同文件所有块都遵守这个规律：`awa` 2412→2408、`etc` 676→672、`sklslot` 3745→3741…）

### 6.2 移植流程（照抄）

```python
# 源：4rinprm.bin.xfbin（Rin）；目标：2karprm.bin.xfbin（香磷）
# 1) 用 xfbin_lib 读两边的 NuccChunkBinary 块：4rinprm_mot / 2karprm_mot
# 2) 定位三个投技条目的边界（到下一个 PL_ANM_XXX，即 PL_ANM_AWAKE_S 为止）
def spans(data):
    return ((data.find(b"PL_ANM_THROW_BEGIN"),          data.find(b"PL_ANM_THROW_SUCCESS_ATTACKER")),
            (data.find(b"PL_ANM_THROW_SUCCESS_ATTACKER"), data.find(b"PL_ANM_THROW_SUCCESS_VICTIM")),
            (data.find(b"PL_ANM_THROW_SUCCESS_VICTIM"),  data.find(b"PL_ANM_AWAKE_S")))
# 3) 取 4rin 的三个条目块，块内所有 b"4rin" 等长替换为 b"2kar"（4→4，禁止改变长度）
# 4) 用它们替换 2karprm_mot 里对应的三个条目
# 5) 重算大小字段：struct.pack_into(">H", mot, 2, len(mot) - 4)
# 6) 写回 modmanager\<ModName>\Resources\Files\data\spc\2karprm.bin.xfbin
```

**用 `port_throw_prm_rin.py`（`codex_tmp\hnt_build\`）作为可运行模板。**

### 6.3 校验（必做）

- `prm` **条目数不变**（香磷保持 91）；
- 三个投技条目**改名后与源角色逐字节相等**；
- 除投技区域和大小字段外，`prm_mot` 其余字节与原版**完全一致**；
- 其他参数块（`awa` / `etc` / `hit` / `load` / `skl` / `sklslot` / `spl`）**逐字节不变**；
- **`prm_mot` 里无源角色前缀残留**（实测 `4rin` = 0 处）；
  ⚠️ **但 `bod1l` 里有残留是正常的**：Rin 版 `2karbod1l.xfbin` 实测含 **11 处 `4rin`**
  （Ino 版含 11 处 `1ino`），位于**动画块内嵌的源文件路径字符串**
  （形如 `c\4rin\anm\4rinbod1l\4rinhola0.max`），运行时无害。
  ⇒ **判定 `bod1l` 改干净与否，看页面 / 块名 / 引用表，不要用全文 `count`**
  （`2karhola0`/`2karhola1` 才是被引用的块名）；
- `bod1l` 的 `hola0`/`hola1`/`hold0` 三页齐全，`hola1` 带 `camera` 与 `LightDirc`；
- **重读输出再验一遍**，别只看内存里的结果。

### 6.4 只换动画不换参数（合法的半成品）

如果用户只要"动作像"，可以只做动画页替换——但要**明确告知**：
判定点（`2kar00t0 l forearm`）与伤害 ID（`DMG_2KAR_THROW_LAST`）仍是目标角色的。
另外：**源角色独有骨骼**（井野的 `hair00~10 / tail / eri / joe / lip`）在目标骨架上不存在，
**动画轨道会被引擎忽略**（身体/四肢/头部动作完整）。
被投动画 `hold0` 是通用骨架，对任何角色都有效（井野版 66 帧 vs 香磷版 52 帧）。

---

## 7. `Characode` / `BaseModel` / 文件名的配置规则（踩坑集合）

**一句话：`Characode` 是"你要占据哪个角色位"，`BaseModel` 与模型文件名是"这套模型按谁的名字加载"。**

| 场景 | Characode | BaseModel | 模型文件名 | 为什么 |
|---|---|---|---|---|
| 来源是本作角色、改名进目标槽位（①/③推荐） | 目标（`2kar`） | 目标（`2kar`） | 目标（`2karbod1`） | 走第 2 节路线 |
| 来源保留自己前缀（如校服天天进井野 02） | 目标（`2ino`） | **来源（`dtng`）** | **来源（`dtngbod1`）** | 强行改名成 `2inobod1` ⇒ **选人无模型 + 战斗无限加载** |
| 网页下载的 mod | 照作者 | 照作者 | 照作者 | 作者验证过，别动 |

**绝对不要做的事**
- ✘ `BaseModel=2ten`（来源代码）而文件已改名——**容易选人消失 + 卡加载**；
- ✘ 全局把 `2kar00t0` → `2ten00t0`——骨骼前缀错乱 ⇒ 五官飘到脸外/下巴下方、选人消失；
- ✘ 把 `dtngbod1` 改成 `2inobod1`——同第一条；
- ✘ 把 `dtngbody1`/`2` 统一替换成 `dtngbody4`——**大面积黑块**（头发到手臂）+ 进游戏闪黑；
- ✘ 用 Character Roster Editor 把来源做成新角色、动作挂目标——**选人无模型、进战斗卡加载/闪退**；
- ✘ 改低层骨架/骨骼表做微调——人物姿态会变；
- ✘ 同时启用两个替换同一个 `bod1` 的 mod。

**改完配置的固定动作**：退出游戏 → Mod Manager 里把该 mod **关一次再开**（重新生成
`data_win32_modmanager.cpk`）→ 进游戏选目标服装。
**"模型消失 / 无限加载"优先查文件名与角色位配置，不要先动材质。**

---

## 8. 验证清单（每次都要过）

**构建侧**
- [ ] 等长替换：替换处数量可枚举、长度未变（手鞠案例 247 处）；
- [ ] 逐字节核对：贴图数据、骨骼（coord）数据与原版**一致**；除预期改动外无差异；
- [ ] `prm_mot` 大小字段 = 块长 − 4；条目数不变；其他参数块逐字节不变；
- [ ] 无来源角色前缀残留；
- [ ] Blender 重新导入：身体/脸网格不变，眼睛/牙齿/舌头按预期偏移；
- [ ] 备份文件在 `codex_mod_backups\`。

**游戏侧**
- [ ] 选人界面**能显示模型**；
- [ ] **能进入战斗**（不卡加载）；
- [ ] 普通攻击 / 投技 / 技能 / 奥义 **是目标角色的动作**（不是来源角色的）；
- [ ] 眼睛贴图显示正常、位置在眼眶内、不透明到背景板；
- [ ] 嘴巴：要么在嘴里且说话动画正常，要么已确认按用户要求隐藏；
- [ ] 技能/奥义的特效归属正确（若移植了 `spl`/`skill` 相关文件）。

---

## 9. 排错速查

| 症状 | 首要怀疑 | 动作 |
|---|---|---|
| 选人界面**模型消失** | `BaseModel` 写成了来源代码 / 文件名与角色位不匹配 / `prm_mot` 大小字段写错 / CPK 打包不完整 | 先回退配置；再查角色位三件套；再验 `prm_mot` 的 `len-4`；**不要先动材质**（F4/F5/F26/F32） |
| 进战斗**一直卡加载** | 同上 + 来源被做成了新角色位 / 冲突 mod | 退出游戏重新打包；只启用一个 mod（F2/F33） |
| **进战斗闪退** | 骨架重绑路线 / 材质 parent-material 指错 | 回退到等长改名路线（F1） |
| 能进但**外观没变** | 改错文件 / 选错角色位看效果 / 方向搞反（T/S 反了） | 确认 `Resources\Files\data\spc\` 下文件名 = 目标槽位 |
| **动作变了**（攻击变成来源角色的） | 漏保留目标的 `bod1c` / `bod1l` / `bod1s` | 补回目标原版这四个文件 |
| **普通攻击失效 / 脸型被拉大** | 直接套用了来源骨骼、且两骨架不同构 | 回退；优先等长改名（F3） |
| **眼睛透明/没有贴图** | 材质贴图槽数量（1 组 vs 2 组）或贴图格式（DXT5/RGB565/RGBA8）或贴图名与材质引用不一致 | 见 5.2（F12/F16/F17） |
| **眼睛/牙齿位置错**（下巴/脚底/脖子） | 刚性网格的骨骼约定不同，未做坐标烘焙 | 见 5.3，注意**包围球同步烘焙** + `lod0/lod1` 都改（F23） |
| **五官整体飘到脸外/下巴下方** | 骨骼/节点前缀被批量改坏 | 恢复原名前缀，只改必要位置（F6） |
| **嘴巴外凸** | 坐标调整打到错的对象 | 见 5.4；**先问用户要不要保留嘴巴**（F21） |
| **嘴收不进去（穿到口腔后壁）** | 沿 Y 推过头了 | 嘴部沿 Y 往脸内累计约 +0.010 模型单位即可（F24） |
| 眼睛出现**尖刺/突刺** | 只移动了局部顶点 | 移动完整形状，不要逐点扫（F20） |
| 大面积**黑块** | 贴图名/材质引用被批量替换坏（如 body1/2→body4） | 回退，只改必要名字（F11） |
| **投技动画放完没伤害/无特效** | 只换了动画页，没换 `prm_mot`；或 `hola1` 页漏搬 `camera01`/`LightDirc` | 见第 6 节，两块一起做（F25/F28） |
| 投技**动画对但打得不对**（判定点/次数错） | 判定点骨骼在目标骨架上不存在 | 换相近骨骼名，或改用目标角色原版判定 |
| **被投动画失效** | 把通用骨架 `1cmn00t0` 也改了名 | 通用骨骼不改名（F29） |
| 某个配色/某套衣服还是原角色 | 只做了 `2kar_00`，漏了 `_01` / `_col2` / `_col3` / `_dmg01` | 分别处理（F8） |
| 改了没生效（打包成功） | Mod Manager 没重新打包 / mod 没重新启用 | 关一次再开，确认 CPK 大小与时间变了（F9） |
| 自我怀疑"移植没改干净"（因为 grep 到来源前缀） | `bod1l` **允许**残留源路径字符串（实测 11 处） | 看页面/块名/引用表；只有 `prm_mot` 必须 0 残留（F31） |

> 更完整的 **36 条失败路线（F1–F36）+ 22 行症状速查表**见
> `references/05-troubleshooting.md`；上表括号里的编号就是它的条目号。
>
> **F33（多 mod 抢同一文件）的实测样本，注意它分两个层次**：
> 本机当前启用态是 3 个 mod，其中 `School Gauken Pack`（`NUNSC-SCHOOL-GAUKEN-PACK`）与
> `Tenten Models for Ino Moveset`（`Tenten School Model for Ino 02\...`）**同时覆盖**
> `data/spc/dtngbod1.xfbin` / `_col2` / `_col3` / `acc` **共 4 个文件**。
> 但它**不是要修的问题**——两者都是"校服天天"模型（一个挂香磷家族位，
> 一个用 `Characode=2ino` 挂井野 02），用途不重叠，且这正是该项目已验证可用的启用组合。
> ⇒ **判据不是"有没有重叠"，而是"重叠的两个 mod 是否服务于同一个角色位、
> 以及你是否能接受其中一个不生效"。** 真正必须拆开的是
> `data/spc/2karbod1.xfbin` 被 **15 个 mod** 抢的那种（同一角色位、不同外观）。

---

## 10. 参考文档

- `references/01-original-model-swap.md` —— ①原始人物模型替换详解（等长改名实现、逐字节校验脚本）
- `references/02-web-download-mods.md` —— ②网页下载 mod 的安装与判别（`.nsc`/zip/rar/散件）
- `references/03-own-model-blender.md` —— ③自己的模型替换（Blender 注入导出、骨架重绑与坐标烘焙）
- `references/04-xfbin-format.md` —— XFBIN/NUCC 结构、chunk 类型、命名表与偏移、`prm_mot` 字段
- `references/05-troubleshooting.md` —— 失败路线全集 + 逐条症状排查表
- `scripts/rename_prefix.py` —— 等长前缀改名 + 逐字节校验
- `scripts/dump_xfbin.py` —— 打印 XFBIN 的 page/chunk 结构（定位模型与动画页）
- `scripts/prm_mot_size_fix.py` —— 重算并写回 `prm_mot` 大小字段（防卡加载）

## 心法

> **动作稳定性的优先级高于外观微调。**
> **任何导致"选人消失 / 进战斗卡加载 / 崩溃"的改法一律先回退，再去调外观。**
> 最稳的组合始终是：**模型文件保留来源骨架 + 只做等长前缀改名 + 攻击文件用目标原版**；
> Blender 重绑骨架是最后手段，不是第一步。
