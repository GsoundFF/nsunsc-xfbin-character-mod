# ② 网页下载的现成 mod —— 安装、判别、排错

下载来的东西分三种命运：**能直接启用的 mod、只能当素材的散件、根本不该碰的东西**。以下全部来自本机实勘，
`<游戏目录>` = `E:\SteamLibrary\steamapps\common\NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS`；
命令块在 **Windows PowerShell 5.1** 下实跑通过（用 `Get-Content -Encoding Byte`；**不要**改成 `-AsByteStream`，5.1 不认）。

## 0. 本机实勘坐标（先认路）

| 角色 | 真实路径 | 实勘事实 |
|---|---|---|
| 下载存档区 | `<游戏目录>\data_win32\` | 实测 **17 个目录 + 8 个压缩包/`.nsc`**（§1） |
| Mod 仓库 | `<游戏目录>\modmanager\` | **25 个顶层目录**（3 个是空占位；`Anko`/`Shizune Mod`/`Tenten School Model for Ino 02` 把 mod 又套了一层同名目录；`Tenten Normal Model for Karin 00` 里有两份 `mod_config.ini`），共 **464** 个文件 |
| 打包产物（根目录） | `<游戏目录>\data_win32_modmanager.cpk` | ★ **本机当前不存在**（§7） |
| 打包产物（生效副本） | `<游戏目录>\moddingapi\mods\base_game\data_win32_modmanager.cpk` | 140,200,592 字节，2026-09-19 23:09:55，旁边有 8 字节 `.info` |
| Mod Manager | `...\net9.0-windows10.0.26100.0\NSC_ModManager.exe` | V1.6.5.1；UTF16 字符串含 `\modmanager\`、`\mod_config.ini`、`model_config.ini`、`data_win32_modmanager` |
| 游戏本体 CPK | `...\data\launch\*.cpk`、`...\data\sim\data2.cpk` | `data1.cpk` 5,579,935,756 字节 |
| ModdingAPI | `<游戏目录>\moddingapi\` | **另一套系统**（§6.3） |
| 管理器记住的游戏根 | `%LOCALAPPDATA%\TheLeonX\NSC_ModManager_Url_*\1.6.5.1\user.config` | `RootGameFolder` = 本机游戏根（另有 1 份残留配置指向 `F:\naruto\...`） |

## 1. 包形态判别

### 1.1 四种形态一张表

| 形态 | 头 8 字节 | 本机真实实例 | 内部结构 | 你该做什么 |
|---|---|---|---|---|
| `.nsc`（=ZIP） | `50 4B 03 04 14 00 00 00` | `data_win32\静音\Shizune Mod.nsc` | **有顶层目录** `Shizune Mod/...` | 解压 → 把 `Shizune Mod` 整个放进 `modmanager\` |
| `.nsc`（无顶层） | `50 4B 03 04 0A 00 00 00` | `<游戏目录>\NUNSC-SCHOOL-GAUKEN-PACK.nsc` | **无公共顶层**，根即 `Resources/`、`Models/`、`mod_config.ini` | 解压时**自己先建一层目录**，否则文件散落到 `modmanager\` 根部 |
| `.zip` | `50 4B 03 04` | `Shizune Moveset Mod-714-V-1-0-1725713562.zip`、`Shizune Moveset Mod Update-924-V1-1-1739108967.zip`、`红豆.zip`、`流血特效.zip`、`Additional Shaders-101-1-3-1727120363.zip` | 三种都有（含"里面还有 `.nsc`"） | **先列条目再决定** |
| `.rar`（**全是 RAR5**） | `52 61 72 21 1A 07 01 00` | `泳装多有也.rar`、`火辣香磷.rar`、`香磷泳衣.rar` | 裸 xfbin，或自带 `data_win32/spc/` 路径 | 本机**没装 7z/WinRAR**，用系统自带 `tar.exe` 列 |
| 裸 `.xfbin` 散件 | 非 PK/Rar 头 | `data_win32\小南泳装\2knnbod1.xfbin`、`data_win32\校服红\Kurenai Normal\9krnbod1.xfbin` | 单个模型文件 | **不是 mod**，是素材（§4） |

### 1.2 判别命令（可直接复制）

```powershell
function Get-PackKind { param([string]$Path)
  $b = Get-Content -LiteralPath $Path -Encoding Byte -TotalCount 8 -ErrorAction Stop
  $hex = ($b | ForEach-Object { $_.ToString('X2') }) -join ' '
  switch -Regex ($hex) {
    '^50 4B 03 04'          { 'ZIP (含 .nsc)' }
    '^52 61 72 21 1A 07 01' { 'RAR5' }
    '^52 61 72 21 1A 07 00' { 'RAR4' }
    '^37 7A BC AF 27 1C'    { '7z' }
    default                 { '其他 / 裸文件' }
  }
}
Get-ChildItem '<游戏目录>\data_win32' -File |
  Where-Object { $_.Extension -in '.nsc','.zip','.rar' } |
  ForEach-Object { "{0,-10} {1}" -f (Get-PackKind $_.FullName), $_.Name }
```

实跑：`data_win32\` 下 8 个 `.zip`/`.nsc` **全部判定为 ZIP**，3 个 `.rar` **全部为 RAR5**。

### 1.3 列条目（解压前必做）

```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem           # ZIP / .nsc
$z = [System.IO.Compression.ZipFile]::OpenRead('<路径>\红豆.zip')
$z.Entries | ForEach-Object { "{0,12}  {1}" -f $_.Length, $_.FullName }
$z.Dispose()
& tar -tf '<游戏目录>\data_win32\泳装多有也.rar'                   # RAR5（bsdtar 能读）
```

**实勘条目 = 判形的全部依据：**

| 包 | 条目 |
|---|---|
| `静音\Shizune Mod.nsc` | `Shizune Mod/mod_config.ini`(204)、`mod_icon.png`、`Resources/CPKs/1szn.cpk`(14496)、`Resources/Files/data/spc/1sznbod1.xfbin`(1753374)、`Characters/1szn/character_config.ini`(47)、…100+ 条 |
| `红豆\Anko Mitarashi (Support) Mod.nsc` | `Anko Mitarashi (Support) Mod/mod_config.ini`(232)、`Resources/CPKs/anko.cpk`、`Resources/Files/data/spc/ankobod1.xfbin`、`.../spc/ankobod1out.obj` |
| `NUNSC-SCHOOL-GAUKEN-PACK.nsc` | **150 条、无公共顶层**：`Resources/Files/data/spc/dhbgbod1.xfbin`、`Models/2kar_02/model_config.ini`、`mod_config.ini`、`mod_icon.png` |
| 两个 `Shizune Moveset Mod*.zip` | `-714-V-1-0-…`：8 条 = `Shizune/Shizune Mod (NSC Mod Manager)/Shizune Mod.nsc`(18680941) + `Shizune/Shizune Skin Mod/Jonin/1sznbod1.xfbin`(1434034) + `.../Swimsuit/1znbod1.xfbin`(2325584)；`Update-924-V1-1-…`：**1 条** `Shizune Mod.nsc`(18841643) —— 覆盖式更新 |
| `红豆.zip` | **1 条**：`Anko Mitarashi (Support) Mod.nsc`(16871034) |
| `流血特效.zip` / `Additional Shaders-101-1-3-…zip` | `data_win32/spc/damageeff.bin.xfbin`(7024)、`data_win32/spc/effectprm.bin.xfbin`(78392) ／ `data/system/nuccMaterial_dx11.nsh`(1879632) —— 一个 shader，**既不是 mod 目录也不是 xfbin** |
| 三个 `.rar` | `泳装多有也`：4 个 `5tyv/5tyybod1*.xfbin` + `Always awakening/` 下 2 个；`火辣香磷`：`2karbod1.xfbin`/`_col2`/`_dmg01`；`香磷泳衣`：`data_win32/spc/2karbod1.xfbin`、`…2karbod1_dmg01.xfbin`（**自带游戏目录路径**） |

### 1.4 版本混淆陷阱（本机真实案例）

`静音\` 下两个同名 `.nsc`，**字节数不同 = 版本不同**：`Shizune\Shizune Mod (NSC Mod Manager)\Shizune Mod.nsc`
= **18,680,941**（本体 zip，V1.0）；`静音\Shizune Mod.nsc` = **18,841,643**（Update zip，V1.1，与
`Shizune Moveset Mod Update-924...zip` 内条目字节数一致）。⇒ 装了本体又装更新包时**后放的赢**，别两个都塞进去。

## 2. 「哪一层才是 mod 根」

### 2.1 判定规则（按优先级）

1. **必要条件**：那一层有 `Resources\Files\data\`。角色替换类通常是 `Resources\Files\data\spc\`；**例外**：
   `modmanager\No Combo Damage Scaling` 用的是 `Resources\Files\data\system\ccAdjustParam.xfbin`
   ⇒ 判据写 `Resources\Files\data\`，不要写死 `...\data\spc\`。
2. **强证据**：同层有 `mod_config.ini`（含 `[ModManager]` + `ModName=`）；**加分项**：`Models\<Characode>_XX\model_config.ini`、`mod_icon.png`、`Resources\CPKs\*.cpk`。
3. **不要再套一层**：多套一层同名目录 ⇒ 同名重复条目（§2.3）。

### 2.2 定位脚本

```powershell
function Test-ModRoot { param([string]$Path)
  [pscustomobject]@{
    HasResources = Test-Path (Join-Path $Path 'Resources\Files\data')
    Config = Test-Path (Join-Path $Path 'mod_config.ini')
    Models = Test-Path (Join-Path $Path 'Models')
    Xfbin  = @(Get-ChildItem -LiteralPath $Path -Recurse -Filter *.xfbin -EA SilentlyContinue).Count
    Dir    = $Path } }
Get-ChildItem '<你刚解压到的目录>' -Directory -Recurse |
  Where-Object { Test-Path (Join-Path $_.FullName 'Resources') } |
  ForEach-Object { Test-ModRoot $_.FullName } | Format-Table -AutoSize
```

### 2.3 实测：Mod Manager **递归**扫描，但嵌套带来歧义

本机 25 个顶层目录里有 4 个把 `mod_config.ini` 埋在**一层同名子目录**里，全部能被扫到：
`Anko Mitarashi (Support) Mod\...\`（EnableMod=false）、`Shizune Mod\...\`（false）、
**`Tenten School Model for Ino 02\...\`（EnableMod=★true —— 递归确实生效，且这正是调试记录里确认"成功"的那个 mod）**、
`Tenten Normal Model for Karin 00\`（**两层都有** ⇒ 反例，见下）。

**反例（要避免）—— `modmanager\Tenten Normal Model for Karin 00\`：**

```
Tenten Normal Model for Karin 00\
├── mod_config.ini                    # ModName=Tenten Normal Model for Karin 00
├── Models\2kar_00|2kar_01\{model_config.ini, data\spc\playerSettingParam.bin.xfbin}
├── Resources\Files\data\spc\2karbod1.xfbin (+ _col2/_col3/_dmg01/acc/c/l/s)
└── Tenten Normal Model for Karin 00\ # ★ 内层副本，ModName 一模一样
    ├── mod_config.ini                # ModName 也是 Tenten Normal Model for Karin 00
    └── Models\2kar_00\{model_config.ini, data\spc\playerSettingParam.bin.xfbin}
```

两层 `ModName` 完全相同 ⇒ 列表里出现**两个同名条目**，勾选时无法判断点的是哪一个，两层的 `EnableMod`
各写各的。**处置：把内层多余目录删掉/移出 `modmanager\`，只留一层。**
另有 **3 个空目录**（枚举 0 条目，既无 `mod_config.ini` 也无 `Resources`）：`modmanager\Tenten 02 Model on
Ino 02 Moveset`、`Tenten Normal Model for Ino 00`、`Tenten School Model for Ino 02 - Ino Face` —— 整理残留，
清掉即可，别误判成"装了没生效"。

### 2.4 作者包里的垃圾/备份（会一起进 CPK）

`Shizune Mod` 包内实测存在 `Resources\Files\data\spc\Shizune\1sznbod1.xfbin`、`…\spc\Shizune\2sznbod1.xfbin`、
`…\spc\Shizune1.xfbin`、`data\skill\1szn_x.xfbin.bak`、`data\ui\flash\OTHER\name_l\kokr\nl_szn1.xfbin.bak`、
`Characters\1szn\data\spc\duelPlayerParam.xfbin.backup`；`Anko` 包里还有
`Resources\Files\data\spc\ankobod1out.obj`。**Mod Manager 不做过滤**（实测 CPK 目录表就是扁平的
`data/spc`、`data/spcload`），这些备份/裸编辑产物会照原样打进 `data_win32_modmanager.cpk`。「包里在 `spc\` 下
又套一层人名目录」**不会**让游戏多认一个角色。

## 3. 为什么「网页下载」与「自己做」的注册方式不同

**因为下载 mod 的 `model_config.ini` 不是"描述"而是"绑定"，那个组合被作者验证过。**

### 3.1 真实案例：`Tenten School Model for Ino 02`（校服天天放在井野 02 位）

```
modmanager\Tenten School Model for Ino 02\Tenten School Model for Ino 02\
├── mod_config.ini                  ModName=Tenten Models for Ino Moveset   EnableMod=true
├── Models\2ino_02\model_config.ini Characode=2ino / BaseModel=dtng / AwakeModel=（空）
├── Models\2ino_02\data\{spc\playerSettingParam.bin.xfbin, spc\player_icon.xfbin,
│      spc\costumeBreakColorParam.xfbin, rpg\param\costumeParam.bin.xfbin,
│      ui\max\select\characterSelectParam.xfbin}
└── Resources\Files\data\spc\  dtngbod1.xfbin / dtngbod1_col2 / dtngbod1_col3 / dtngbod1acc.bin.xfbin
```

**模型文件名是 `dtngbod1.xfbin`（天天校服前缀），不是 `2inobod1.xfbin`。** `Characode=2ino` 只说"挂在井野 02
角色位"，`BaseModel=dtng` 说"基准模型用天天校服那套"—— 两者本来就**不该一致**。改名成 `2inobod1` 的实测后果
（源自 `_docx_extract\校服天天替换井野02_调试流程记录.txt`）：

| 改动 | 症状 |
|---|---|
| `dtngbod1.xfbin` → `2inobod1.xfbin` | 切到井野 02 **看不到模型**，进对战**无限加载** |
| `dtngbody1`/`dtngbody2` 统一换成 `dtngbody4` | 头发到手臂**大面积黑块** + 进游戏闪黑 |
| 骨骼/节点前缀 `dtng00t0`/`dtng_` 改成井野编号 | 五官飘到脸外、甚至偏到下巴下方 |
| 用 Character Roster Editor 另造角色位 | 选人无模型、进战斗卡加载/闪退 |

**纪律：下载 mod 的 `Characode` / `BaseModel` / 模型文件名三者照抄，一个字都别动。** "顺手改成目标角色前缀"
是**自己做 mod** 时才做的事（见 `01-original-model-swap.md`），且那时 `BaseModel` 必须与文件名一致。

### 3.2 本机全部 `model_config.ini` 实勘（拿来对照，别凭记忆）

`Characode == BaseModel == 2kar` 的 9 个 mod（同角色换衣服，正常）：`Bachong for Karin`、`Falushan for Karin`、
`Hanabi Replaces Karin`、`Kushina Qipao for Karin`、`Kushina Qipao for Karin with Rin Throw`、
`Konan White Swimsuit for Karin with Sarada Throw`、`Nobara Genin Model for Karin 00`、
`Temari Outfit for Karin`、`Tenten Normal Model for Karin 00`（均有 `Models\2kar_00` + `Models\2kar_01`，`AwakeModel` 全空）。
**跨角色的才是重点：**

| mod → `Models\<X>` | Characode | BaseModel | AwakeModel |
|---|---|---|---|
| `NUNSC-SCHOOL-GAUKEN-PACK` → `2kar_02` | 2kar | **dkrg** | |
| 同上 → `2ten_02` / `2tmr_04` / `6hnb_02` | 2ten / 2tmr / 6hnb | **dtng / dtmg / dhbg** | |
| 同上 → `3who_02` / `4rin_01` / `5tyy_01` | 3who / 4rin / 5tyy | **dwhg / drng / dtyg** | **3tmi / 3isb / 5tyv** |
| `Tenten School Model for Ino 02` → `2ino_02` | 2ino | **dtng** | |

两个可复用结论：① 看到 `2ino`+`dtng` 是正常的，不是笔误；② `Models\<Characode>_XX` 的 `_XX` **可以是
00/01/02/04**，由作者按目标服装槽位决定，**别默认从 00 开始**；`AwakeModel` 是第 3 个可选绑定，留空即不用。

## 4. 「下载素材」vs「下载成品 mod」

| 特征 | 成品 mod | 素材散件 |
|---|---|---|
| 有 `mod_config.ini` / `Resources\Files\data\` | ✅ / ✅ | ❌ / ❌ |
| 形态 | 目录树 | 一堆 `*.xfbin` 平铺 |
| 放进 `modmanager\` | 列表里可勾选 | **不出现**（扫不到），什么都不会发生 |
| 该干什么 | 勾选 → 打包 | 走 `01`/`03` 自己拼一个 mod |

本机 `data_win32\` 全部实勘分类（本节即"同一批下载里怎么分辨"的答案）：

| 目录 | 内容 | 判定 |
|---|---|---|
| `静音\` | `Shizune Mod.nsc`(18841643)；`Shizune\Shizune Mod (NSC Mod Manager)\Shizune Mod.nsc`(18680941)；`Shizune\Shizune Skin Mod\Jonin\1sznbod1.xfbin`(1434034)；`...\Swimsuit\1znbod1.xfbin`(2325584) | 成品包 + 2 个素材 xfbin |
| `红豆\` | `Anko Mitarashi (Support) Mod.nsc`(16871034) | 成品包 |
| `小南泳装\` / `小南泳装 2\` / `小南泳装 白衣\` | `2knnbod1.xfbin`、`2knnbod1_dmg01`、`2knnbod1l`、`2knnspl1`、`2pea2knn_spl1_2knn`、`2knnbod1c` | **素材**（三份 `2knnbod1.xfbin` **同名不同版**，别混用） |
| `校服红\` / `泳装红\` | `Kurenai Normal\{9krnbod1 7186226, _dmg01 3587714}`、`Kurenai Alt\{9krnbod1 7159378, _dmg01}`；`泳装红\9krnbod1.xfbin`(7138678) | 素材；`泳装红` 那份**与 `data_win32\spc\9krnbod1.xfbin` 字节数完全相同 = 重复素材** |
| `静音上忍服\` / `静音泳装\` | `1sznbod1.xfbin`(1434034) ／ `1sznbod1.xfbin`(2325584) | 素材（前者 = `静音\Shizune\...\Jonin\1sznbod1.xfbin` 同体积；zip 里那版叫 `1znbod1.xfbin`，**少一个 s**） |
| `职业雏田\` / `忍者之路雏田\` | `Hinata(Babe)\spc\{6hntbod1, 6hntbod1acc.bin, _col2, _col3}` ／ `2hntbod1.xfbin`(5966145) | 素材：**只有 `spc\` 没有 `Resources\Files\data\spc\`** ⇒ 不是 mod 根（后者与 `data_win32\spc\2hntbod1.xfbin` 同体积） |
| `旗袍玖辛奈\` / `泳装赵美\` / `火辣香磷\` / `香磷泳衣\` | `3ksnbod1,+_col2,3ksvbod1`；`2mkgbod1,+_col2,+_dmg01`；`2karbod1`(6249402)`+_col2+_dmg01`；`2karbod1`(4094662)`+_dmg01` | 素材 |
| `钉宫换鸣妈\` | `Nobara Mod\{Genin\, Jounin\, Finish cuts\, Weapons\, Hud\ui\flash\OTHER\, Raw Models\}` 共 26 文件 | **作者工程目录**（无 `Resources\Files\`、无 `mod_config.ini`）⇒ 素材 |
| `spc\` | `2hntbod1`、`5tyv*`、`5tyy*`、`8ksn*`、`8ksv*`、`9krn*`、`damageeff.bin`、`effectprm.bin` | **散件暂存区**（`damageeff`/`effectprm` 来自 `流血特效.zip`）；无 `Resources\Files\data\` ⇒ **永远不是 mod** |

**记忆锚点**：`小南泳装\2knnbod1.xfbin`、`校服红\Kurenai Normal\9krnbod1.xfbin` 这类"平铺的 `xxxxbod1.xfbin`"**永远是素材**，它是 `01`/`03` 流程里的 `S`（来源模型）。看到下载目录里平铺 `2karbod1.xfbin`，要真正生效必须自己建 `modmanager\<ModName>\Resources\Files\data\spc\2karbod1.xfbin` 并写 `mod_config.ini`。

## 5. 冲突检测

### 5.1 列出「每个 mod 覆盖了哪些游戏文件」+ 检测重复覆盖

```powershell
$mm = '<游戏目录>\modmanager'
$rows = foreach ($mc in Get-ChildItem $mm -Filter 'mod_config.ini' -Recurse -File) {
    $root = $mc.DirectoryName; $res = Join-Path $root 'Resources\Files'
    if (-not (Test-Path $res)) { continue }
    foreach ($f in Get-ChildItem $res -Recurse -File) {
        [pscustomobject]@{ Mod = $root.Substring($mm.Length + 1)
                           GamePath = $f.FullName.Substring($res.Length + 1).Replace('\','/') } } }
$rows | Sort-Object Mod, GamePath | Format-Table -AutoSize             # 全部覆盖关系
$rows | Group-Object GamePath | Where-Object { $_.Count -gt 1 } |      # 只看被抢的
    Sort-Object Count -Descending |
    ForEach-Object { "{0,3}x  {1}" -f $_.Count, $_.Name; $_.Group | ForEach-Object { "        " + $_.Mod } }
```

本机实跑：**293 条覆盖记录 → 243 个不同游戏文件**，重复覆盖（真实输出）：

```
 15x  data/spc/2karbod1.xfbin   (Bachong / Falushan / Hanabi / Hinata Job Outfit / Hinata Road to Ninja
                                 ±Sakura Throw / Konan Swimsuit / Konan White Swimsuit / Kushina Qipao
                                 ±Rin Throw / Mei Swimsuit ±Ino Throw / Nobara Genin / Temari / Tenten Normal)
  9x  2karbod1l.xfbin     8x  2karbod1acc.bin.xfbin     7x  2karbod1s.xfbin     7x  2karbod1c.xfbin
  3x  2karbod1_dmg01.xfbin (Hanabi / Nobara Genin / Tenten Normal)
  2x  2karbod1_col2.xfbin  2x 2karbod1_col3.xfbin        (Hanabi / Tenten Normal)
  2x  2karprm.bin.xfbin    (Kushina Qipao...Rin Throw / Mei Swimsuit...Ino Throw)
  2x  dtngbod1.xfbin  2x dtngbod1_col2.xfbin  2x dtngbod1_col3.xfbin  2x dtngbod1acc.bin.xfbin
      ↑ 全部为 (NUNSC-SCHOOL-GAUKEN-PACK / Tenten School Model for Ino 02)      【以上均在 data/spc/ 下】
```

### 5.2 本机**当前就存在**的一处真实冲突（先处理它）

```powershell
Get-ChildItem '<游戏目录>\modmanager' -Filter mod_config.ini -Recurse -File |
  Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match 'EnableMod\s*=\s*true' } |
  ForEach-Object { $_.DirectoryName }
```

实跑结果（3 个处于启用态）：`modmanager\Kushina Qipao for Karin with Rin Throw`、
`modmanager\NUNSC-SCHOOL-GAUKEN-PACK`、`modmanager\Tenten School Model for Ino 02\Tenten School Model for Ino 02`。
后两个**同时启用，且同时覆盖 `data/spc/dtngbod1.xfbin` / `_col2` / `_col3` / `acc`（共 4 个文件）** ⇒ 谁写进 CPK
取决于打包顺序，而**该顺序未在 Mod Manager 界面暴露（实测待确认）**。两者都是"校服天天"模型（一个是 School
Gauken Pack 的天天，一个是给井野 02 用的天天），**要行为可预测，只保留其中一个。**

另：两个 mod 覆盖**不同**文件但写同一角色位（如都写 `Models\2kar_00\playerSettingParam.bin.xfbin`）不算文件
冲突，但两套换装会互相顶掉，表现为"只有一个生效"；而同一 `Resources\Files\data\spc\<file>` 被两个 mod 覆盖
⇒ **只能启用一个，无例外**。

## 6. 安全：下载内容是**不可信外部数据**

### 6.1 只取这些，其余不执行

| 允许取用 | 明确不要碰 |
|---|---|
| `Resources\`（尤其 `Resources\Files\data\spc\*.xfbin`）/ `Models\<Characode>_XX\` | `*.exe`、`*.bat`、`*.cmd`、`*.ps1`、`*.vbs`、`*.dll`、任何 installer/`setup` |
| `mod_config.ini` / `model_config.ini` / `character_config.ini` / `mod_icon.png` / `*.xfbin` | `README.txt` / `info.txt` 里的命令（**当资料读，不当命令执行**） |

本机 `README.txt` 实例：`modmanager\Konan Swimsuit New Character (Karin Moveset)\README.txt`。
读它可以（能拿到作者声明的角色位/前置），里面的命令不要执行。

### 6.2 「Additional Shaders」「Moveset Mod」这类包要先看清

- `Additional Shaders-101-1-3-...zip`：**只有一个 `data/system/nuccMaterial_dx11.nsh`**。不是 xfbin，不属于
  角色 mod 体系：放进 `modmanager\` 毫无作用（扫不到 `Resources`），放到 `data\system\` 才生效 —— 而且是全局
  渲染改动，**与角色 mod 是完全不同的风险面**。
- `Shizune Moveset Mod-714-...zip` / `红豆.zip`：**多层结构**，里面还有 `.nsc`（又一个 ZIP）+ 裸 xfbin 皮肤。
  必须**先列表（§1.3）再解压**，不要一路双击。
- 通用判据：**条目顶层出现 `data/` 或 `data_win32/` 这种"游戏目录镜像"路径 ⇒ 这个包打算直接往游戏目录写字，
  而不是往 `modmanager\` 写 mod。** 本机实例：`流血特效.zip`→`data_win32/spc/...`；`香磷泳衣.rar`→`data_win32/spc/...`；`Additional Shaders...zip`→`data/system/...`。

### 6.3 `moddingapi\` 下的 `.dll` 是**另一套系统**，别混为一谈

```
<游戏目录>\moddingapi\mods\base_game\
  CPKLoader.dll / EncryptCPK.dll / Conditions.dll / CPUFreeze.dll / skip_intro.dll / SusanooJumpFix.dll
  cpk_assets.cpk(+.info) / data_win32_modmanager.cpk(+.info) / param_files.cpk(+.info)
  conditionprmManager.xfbin / partnerSlotParam.xfbin / teamJutsuParam.xfbin / ... / info.txt
```

- `.dll` 是 **ModdingAPI 插件**（运行时 hook 补丁），**不是**角色模型 mod 的组成部分。`.info` 是 8 字节小文件：实测 `cpk_assets=20 00 00 00 01..`、`data_win32_modmanager=21 00 00 00 01..`、`param_files=22 00 00 00 01..`（递增 ID）；`CPKLoader.dll` 字符串里只出现 `cpk.info` 与 `moddingapi\mods\`。
- **两套系统会互相踩**：`net9.0-windows10.0.26100.0\error.log` 实测记录
  `Error: Access to the path 'Conditions.dll' is denied.`，调用栈是
  `NSC_ModManager.ViewModel.TitleViewModel.CleanGameAssets` —— Mod Manager 的"清理游戏资源"会去删 ModdingAPI
  的 dll，被占用时失败。**不要用 Mod Manager 的清理功能去动 `moddingapi\`。**
- `moddingapi\cpu_freeze.log` 实测：`InitializePlugin called` / `WARNING: patch site bytes unexpected, mod disabled`
  —— 插件因目标字节不匹配被自动禁用。**「插件没生效」和「CPK mod 没生效」是两件事，别互相归因。**

## 7. 安装后的固定验证动作

```powershell
$g = '<游戏目录>'
Get-Process NSUNSC -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime  # 1) 必须先退出（实勘时 pid 23780 在跑）
Get-ChildItem "$g\modmanager" -Filter mod_config.ini -Recurse -File |                          # 2) 启用态
  Where-Object { (Get-Content -LiteralPath $_.FullName -Raw) -match 'EnableMod\s*=\s*true' } |
  ForEach-Object { $_.DirectoryName.Replace("$g\modmanager\", '') }
Get-Item "$g\data_win32_modmanager.cpk",                                                       # 3) 两个位置都看
         "$g\moddingapi\mods\base_game\data_win32_modmanager.cpk" -EA SilentlyContinue |
  Select-Object Length, LastWriteTime, FullName | Format-List
$c = "$g\moddingapi\mods\base_game\data_win32_modmanager.cpk"                                 # 4) 合法 CPK？
((Get-Content -LiteralPath $c -Encoding Byte -TotalCount 4) | ForEach-Object { $_.ToString('X2') }) -join ' '  # 应为 43 50 4B 20
```

| 步骤 | 检查点 | 本机实测基准 |
|---|---|---|
| 1 | 退出游戏（`NSUNSC.exe` 不在进程表） | 运行中打包 ⇒ 文件占用失败 ⇒ 产出不完整 CPK |
| 2 | 列表里**只有该 mod 勾上**（同名条目只能勾一个） | 同名条目来自 §2.3 的嵌套副本 |
| 3 | 关一次再开（或重启管理器）触发重新打包 | `EnableMod` 写回 `true` 才代表状态已落盘 |
| 4 | CPK **大小 + 修改时间**都变了；头是 `43 50 4B 20` | 生效副本 140,200,592 字节 / 2026-09-19 23:09:55 |
| 5 | 根目录那一份**当前不存在** | 历史副本在 `codex_mod_backups\before_patch_data_win32_modmanager_cpk_20260808_184059\data_win32_modmanager.cpk`（120,478,816 字节）+ 8 字节 `.info` |
| 6 | 进游戏：选人**有模型** → **能进战斗**（不卡加载）→ 普攻/投技/技能/奥义是**目标角色**的 | 见 `04` 与 §8 |

> **产物位置**：`data_win32_modmanager.cpk` 本机当前只在 `moddingapi\mods\base_game\` 下，而 2026-08-08 的备份证明它当时位于游戏根目录。**是"Mod Manager 写根目录、ModdingAPI 再接手"还是"ModdingAPI 在场时直接写自己目录"，实测待确认** ⇒ 第 3 步两个路径都查。

## 8. 常见失败与处置

| 症状 | 首要怀疑 | 处置 |
|---|---|---|
| 放进 `modmanager\` 却没出现在列表 | 目录层级多套了一层 / 放到了压缩包外层 / 那层没有 `Resources\Files\data\` | 用 §2.2 找真正的 mod 根，移到 `modmanager\` 直接子级 |
| 列表里出现**两个同名 mod** | 嵌套同名副本（`Tenten Normal Model for Karin 00` 型） | 删掉内层副本，只留一层 |
| 勾了 mod 但外观没变 | 与另一启用中的 mod 抢同一个 `data/spc/<file>`；或勾的是同名条目里的另一个 | 跑 §5.1 冲突表，只留一个启用 |
| 选人**没有模型** / 进战斗**无限加载** | ① 改了作者验证过的模型文件名（`dtngbod1`→`2inobod1` 型）② 改了 `BaseModel` ③ 游戏没退出就打包，CPK 不完整 | 先把 `model_config.ini` 与文件名**原样还原**，退出游戏重打包 |
| 进战斗**闪黑/大面积黑块** | 批量替换了作者的 mesh/骨骼名（`dtngbody1/2`→`dtngbody4`） | 还原包内命名，别动 |
| 装了**毫无反应**也无报错 | 装的是**素材散件**（`小南泳装\2knnbod1.xfbin` 型）或**非角色包**（`Additional Shaders` 的 `.nsh`） | 按 §4 判定；素材要走 `01`/`03` 自己做成 mod |
| 解压报错 / 条目不全 | 下载不完整 | 重新下载；用 §1.3 条目列表核对预期（如 `红豆.zip` 应只有 1 条 16,871,034 字节的 `.nsc`） |
| 效果是**旧版本** | 同名 `.nsc` 两份（18,680,941 / 18,841,643），放的是旧的 | 只留一份，按字节数确认版本 |
| 外观**对不上你以为的角色** | 作者的 `Characode` 与你以为的不同 | 读 `model_config.ini` + `Models\<Characode>_XX` 目录名，别猜（`2ino`/`3who`/`6hnb`/`dwhg` 都是真实槽位） |
| 某配色/破衣状态还是原角色 | 包里只有 `bod1`，没有 `_col2/_col3/_dmg01` | 看该 mod 实际覆盖哪些文件（§5.1），缺的就是会退回原版的部分 |
| `patch site bytes unexpected, mod disabled` ／ `Access to the path 'Conditions.dll' is denied.` | ModdingAPI 插件版本不匹配 ／ 用"清理游戏资源"动过 `moddingapi\` 的 dll | 两者都与角色 mod 无关：查 `moddingapi\*.log`，别改 CPK；别对 `moddingapi\` 做清理（§6.3） |

## 9. 实测待确认（不要当结论用）

1. `data_win32_modmanager.cpk` **写盘位置的裁决规则**（根目录 vs `moddingapi\mods\base_game\`）——两处都查最稳。
2. 同时启用两个覆盖同一文件的 mod 时，**打包覆盖顺序**由什么决定——界面未暴露，故策略是"只启用一个"而非"赌顺序"。
3. Mod Manager 递归扫描的**深度上限**（本机最深只命中 1 层嵌套，更深未测）。
4. `.nsc` 的 `Version`/`LastUpdate` 是否参与去重比较（`Shizune` 一旧一新两包 `Version` 都是 `1.0.0`，无从判断）。
