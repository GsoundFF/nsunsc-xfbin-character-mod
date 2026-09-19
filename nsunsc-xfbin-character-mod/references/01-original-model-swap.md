# ① 原始人物模型替换（游戏自带角色 → 目标角色位）

**把游戏自带角色 S 的模型换到角色位 T 上，T 的动作 / 招式 / 奥义全部保留。**

这是三种来源里**最稳、最推荐先做**的一种，也是另外两种（网页下载、自制模型）的技术基础。
核心手法只有一句：**整文件字节级等长前缀改名 + 只把 `bod1` 放进目标槽位 + 攻击文件用目标角色原版。**

> **方向先确认**：把天天换到香磷上 ⇒ **T（游戏角色位）= 香磷 `2kar`，S（模型来源）= 天天 `2ten`**。
> 改的是香磷槽位里的文件，模型字节取自天天。

---

## 1. 素材从哪来

游戏自带角色模型包（未打包的原始文件）：

```
E:\fight date\spc_角色模型\spc\
   2tenbod1.xfbin      # 天天（普通）
   2tmrbod1.xfbin      # 手鞠
   4rinbod1.xfbin      # Rin
   2karprm.bin.xfbin   # 香磷参数（原版，用作基底）
   2karbod1c.xfbin     # 香磷普通攻击（原版）
   2karbod1l.xfbin     # 香磷投技（原版）
   2karbod1s.xfbin     # 香磷技能（原版）
   2karbod1acc.bin.xfbin  # 香磷配件参数（原版）
   ...
```

游戏本体里的同名前缀文件（`<游戏目录>\data\launch\*.cpk` 内）可作对照，
`codex_tmp_original_2karbod1.xfbin` 这类是**调试用的原版副本**，保留它们以便随时回退。

> **基线校验习惯**：动手前先算 md5 对照。例如 `2karbod1l.xfbin` 与游戏原版一致时
> md5 = `179429361fd155707b46d88eafe77791` —— 确认你拿到的是**未改过的原版**，
> 否则后面所有"改了没生效"的判断都会失真。

---

## 2. ★ 角色代码识别（禁止靠猜）

角色代码是**文件名的前 4 字符**，同一个角色常有多套代码（不同服装/形态）：

| 代码 | 角色 | 确认程度 |
|---|---|---|
| `2kar` | 香磷（本作主力实验角色位，普通服装） | 实测（本项目全部案例） |
| `2ten` | 天天（普通） | 实测（天天一般服装替换香磷） |
| `2tmr` | 手鞠（一般服装） | 实测（手鞠替换香磷，247 处改名） |
| `4rin` | Rin | 实测（Rin 投技移植源） |
| `1ino` | 井野（小井野） | 实测（井野投技源） |
| `2ino` | 井野 02 角色位 | 实测（校服天天替换井野02） |
| `dtng` | 校服天天（学园装） | 实测（作为 `BaseModel` 使用） |
| `2knn` | 小南（泳装） | 实测（泳装小南替换香磷，219 骨） |
| `2mkg` | 详见 `data_win32\spc\2mkgbod1.xfbin` | 待确认 |
| `1szn` / `9krn` / `3ksn` / `5tyy` / `8ksn` / `2hnt` / `6hnt` / `oksn` | 详见 `data_win32\spc\` 与 `codex_tmp\` 下的文件 | 待确认 |

**识别纪律**
- **不要靠文件名字面猜**。把候选角色的 `body` 贴图**渲染成 PNG，让用户肉眼确认**是谁
  （模型可能没有视觉能力，这一步必须由人确认）。
- 本作一个角色有多套代码，尾字母/数字常表示配色或服装，**只做一套 ≠ 全做了**。
- 需要确认"某个代码是哪套服装"时，用 `NscToolbox`/`xfbin_lib` 读它的 `Coord` 骨骼
  或纹理页做对照。

---

## 3. 三条必须同时满足的规则

### 规则一：模型文件走"等长前缀改名"，骨架保留来源角色的

```
2tenbod1.xfbin  ──[把内部所有 2ten 换成 2kar]──▶  2karbod1.xfbin（放进香磷槽位）
```

- 骨架（`Coord` 块）**是来源角色自己的**，骨骼顺序/命名都不动；
- 动作之所以还是香磷的：动画轨道按**骨骼名**匹配，
  香磷与来源的**核心骨架同名**（`pelvis / spine / neck / head / upperarm / forearm /
  hand / thigh / leg / foot / toe0 …`），引擎自然把香磷动画套上来；
- 来源**独有**的骨骼（如手鞠 200 骨 vs 香磷 227 骨）不会被驱动，
  **结果是"那部分不动"而不是崩溃**（这是可接受的，比重绑骨架安全得多）。

**各角色骨骼数（实测，用 `scripts/dump_xfbin.py` 可自行核对）**：

| 代码 | 角色 | `Coord` 骨骼数 |
|---|---|---|
| `2ten` | 天天（普通） | **192**（模型 14 个、clump 分组 3 个） |
| `2tmr` | 手鞠 | **200**（模型 13 个） |
| `2knn` | 小南（泳装） | **219** |
| `2kar` | 香磷（目标角色位） | **227** |

⇒ **骨骼数不同完全不是障碍。** 天天 192 根做 `2ten`→`2kar` 改名后，
骨骼数 / 模型数 / 分组数与源文件**完全一致**（改名只动字符串，不动结构）。
手鞠 200 根保留自己的骨架即成功。香磷多出来的骨骼不被驱动，只是"不摆"。

**为什么必须等长**：XFBIN 的名字表是变长字符串表，
`2ten → 2kar` 都是 4 字节 ⇒ 所有字符串长度、表偏移、索引全部不变（详见
`04-xfbin-format.md` 第 2 节）。**改成不等长会破坏整个名字表。**

### 规则二：攻击文件必须用**目标角色原版**

```
Resources\Files\data\spc\
   2karbod1.xfbin          ← 来源模型的改名版（唯一替换的模型文件）
   2karbod1c.xfbin         ← 香磷原版（普通攻击/连段）  ★
   2karbod1l.xfbin         ← 香磷原版（投技）          ★
   2karbod1s.xfbin         ← 香磷原版（技能）          ★
   2karbod1acc.bin.xfbin   ← 香磷原版（配件参数）      ★
```

漏了这四行 ⇒ **普通攻击/投技/技能会变成来源角色自己的**，用户会立刻发现"动作不对"。

### 规则三：`mod_config.ini` + `model_config.ini` 用目标代码

```ini
# modmanager\<ModName>\mod_config.ini
[ModManager]
ModName=Temari Outfit for Karin
Description=Replaces Karin normal costume with Temari's normal outfit (2tmr bod1, prefix-renamed to 2kar, Temari skeleton kept). Karin attack files (2karbod1c/l/s) preserved. NOTE: conflicts with other mods that replace 2karbod1.xfbin - enable only one.
Author=<你>
LastUpdate=09.08.2026
Version=2.1.1
EnableMod=true
```

```ini
# modmanager\<ModName>\Models\2kar_00\model_config.ini   （2kar_01 同样一份）
[ModManager]
Characode=2kar
BaseModel=2kar
AwakeModel=
```

`Models\2kar_XX\data\spc\playerSettingParam.bin.xfbin` 直接从**已成功的同类 mod**
（本项目用 `Tenten Normal Model for Karin 00`）整个复制即可。

---

## 4. 完整构建流程（照抄）

```powershell
# 0. 备份当前能用的模型
$G = "E:\SteamLibrary\steamapps\common\NARUTO X BORUTO Ultimate Ninja STORM CONNECTIONS"
$bk = "$G\codex_mod_backups\2karbod1_before_<来源>_$(Get-Date -Format yyyyMMdd_HHmmss)"
New-Item -ItemType Directory -Force -Path $bk | Out-Null
Copy-Item "$G\modmanager\<目标Mod>\Resources\Files\data\spc\2karbod1.xfbin" $bk\
```

```python
# 1. 字节级等长前缀改名
SRC_CODE, DST_CODE = b"2tmr", b"2kar"
assert len(SRC_CODE) == len(DST_CODE), "必须等长！"
raw = open(r"E:\fight date\spc_角色模型\spc\2tmrbod1.xfbin", "rb").read()
print("source size:", len(raw), "count:", raw.count(SRC_CODE))
out = raw.replace(SRC_CODE, DST_CODE)
assert len(out) == len(raw), "长度必须不变"
assert out.count(SRC_CODE) == 0
open(r"<...>\Resources\Files\data\spc\2karbod1.xfbin", "wb").write(out)
print("written:", len(out))
```

```python
# 2. 回读校验（用 xfbin_lib）
import sys
sys.path.insert(0, r"<游戏目录>\codex_blender_addon\addons\XFBINImporter42\xfbin_lib")
from xfbin import read_xfbin
from xfbin.structure.nucc import NuccChunkClump, NuccChunkMaterial, NuccChunkTexture

xf = read_xfbin(out_model)
print("pages:", len(xf.pages))
for page in xf.pages:
    for cl in page.get_chunks_by_type(NuccChunkClump):
        bones = [c.name for c in cl.coord_chunks]
        bad = [b for b in bones if not b.startswith("2kar")]      # ★ 不应有残留
        print(f"CLUMP bones={len(bones)} models={len(cl.model_chunks)} "
              f"groups={len(cl.model_groups)} non-2kar={len(bad)}")
        print("  first bones:", bones[:5])
        print("  models:", [m.name for m in cl.model_chunks])
    for t in page.get_chunks_by_type(NuccChunkTexture):
        print("  TEX", t.name, t.filePath)
    for m in page.get_chunks_by_type(NuccChunkMaterial):
        print("  MAT", m.name, [t.name for g in m.texture_groups for t in g.texture_chunks])
```

```python
# 3. 复制目标角色原版攻击文件
import shutil, os, hashlib
for f in ["2karbod1c.xfbin", "2karbod1l.xfbin", "2karbod1s.xfbin", "2karbod1acc.bin.xfbin"]:
    src = os.path.join(r"E:\fight date\spc_角色模型\spc", f)
    dst = os.path.join(spc_dir, f)
    shutil.copyfile(src, dst)
    a = hashlib.md5(open(src, "rb").read()).hexdigest()
    b = hashlib.md5(open(dst, "rb").read()).hexdigest()
    print(f, "identical:", a == b)        # ★ 必须 True
```

```python
# 4. Models 配置（从已成功的同类 mod 复制，最省事最不易错）
for slot in ["2kar_00", "2kar_01"]:
    shutil.copyfile(rf"{REF_MOD}\Models\{slot}\model_config.ini",
                    rf"{MOD}\Models\{slot}\model_config.ini")
    shutil.copyfile(rf"{REF_MOD}\Models\{slot}\data\spc\playerSettingParam.bin.xfbin",
                    rf"{MOD}\Models\{slot}\data\spc\playerSettingParam.bin.xfbin")
```

> 现成模板：`codex_tmp\hnt_build\build_tmr_prefix.py`（手鞠版）、
> `codex_tmp\verify_tmr_prefix.py`（校验版）。本 skill 的 `scripts/rename_prefix.py`
> 是这两者的通用化版本。

---

## 5. 可选处理项

| 项目 | 文件 | 不做的后果 | 做法 |
|---|---|---|---|
| 破衣状态 | `2karbod1_dmg01.xfbin` | **回退目标角色原版破损模型**（不崩，只是破衣时外观退回） | 同样等长改名 |
| 配色变体 | `2karbod1_col2.xfbin` / `_col3.xfbin` | 某配色还是原角色 | 同样处理 |
| 第二角色位 | `Models\2kar_01\` | 第 2 套衣服没变 | 复制同样的配置 |
| 眼睛/嘴巴 | 模型内部网格 | 眼睛无贴图 / 位置错 / 嘴巴外凸 | 见 SKILL 第 5 节 |

---

## 6. ★ 逐字节校验（必做，别只看游戏里"看起来对"）

游戏里看起来正常，不代表文件干净——**残留的错误会在用户换一套衣服时才暴露**。校验内容：

```python
# 6.1 与来源对比：除改名字符串外应逐字节相同
src = open(src_path, "rb").read()
out = open(out_path, "rb").read()
assert len(src) == len(out)
# 把两边的角色前缀都归一化后应完全相等
assert src.replace(SRC_CODE, b"####") == out.replace(DST_CODE, b"####")

# 6.2 差异位置集合：应只出现在名字表与引用这些名字的地方
diffs = [i for i, (a, b) in enumerate(zip(src, out)) if a != b]
print("diff bytes:", len(diffs), "first/last:", diffs[0], diffs[-1])
```

```python
# 6.3 手鞠案例的正式校验（材质只应有预期的 2 处变化）
#     - 贴图数据、骨骼（coord）数据完全一致
#     - 除两个眼睛材质外，其余材质字节完全一致
# 6.4 Blender 重新导入：身体、脸网格完全不变；眼睛/牙齿/舌头按预期偏移
# 6.5 无来源前缀残留（non-2kar == 0）
```

---

## 7. 游戏内验证清单

- [ ] 选人界面**能显示模型**；
- [ ] **能进入战斗**（不卡加载）；
- [ ] **普通攻击 / 投技 / 技能 / 奥义是目标角色的动作**（不是来源角色的）；
- [ ] 眼睛贴图显示正常、位置在眼眶内；
- [ ] 嘴巴在嘴里（或按用户要求已隐藏）；
- [ ] 破衣时的外观（如果处理了 `_dmg01`）。

**测试前必须**：完全退出游戏 → NSC Mod Manager 里**只启用这一个**替换 `2karbod1.xfbin` 的 mod
→ 重新打包（确认 `data_win32_modmanager.cpk` 大小与时间戳都变了）→ 进游戏。

> Mod Manager 里如果同时启用了基础版（如 `Kushina Qipao for Karin`）与增强版
> （如 `Kushina Qipao for Karin with Rin Throw`），两者都替换同一个 `2karbod1.xfbin`，
> **必须只开一个**，否则文件互相覆盖 ⇒ 贴图/模型错乱。

---

## 8. 复用检查清单（换下一个角色时）

1. 确认方向：**T = 游戏角色位（模型要出现在谁身上），S = 模型来源**；
2. 确认 S 的代码（4 字符）并确认 T 的代码（4 字符），**两者长度必须相等**；
3. 先备份当前可用的 `bod1`；
4. 统计替换处数（记录在案，便于复查）；
5. 复制 T 的原版 `c/l/s/acc` 四个文件；
6. 写 `mod_config.ini` + 两个 `model_config.ini`；
7. 逐字节校验 + `xfbin_lib` 回读校验；
8. 退出游戏 → 只启用本 mod → 重新打包 → 进游戏；
9. 外观细节（眼睛/嘴巴）留到最后处理；
10. **任何导致"选人无模型 / 卡加载 / 崩溃"的改动一律先回退**。

---

## 9. 本路线的已知边界

| 情况 | 表现 | 处理 |
|---|---|---|
| 来源骨骼数 < 目标 | 来源独有部件不会被驱动，可能"少了点摆动" | 可接受；要更精确就得进 Blender（见 `03-own-model-blender.md`） |
| 来源骨架与目标核心骨骼**不同名** | 动作错乱 | 此时等长改名不够，必须走骨骼名映射重绑（风险高） || 来源比目标**大很多** | 文件变大，CPK 变大（本作无硬性容量上限，实测 3.5MB→3.8MB 正常） | 一般无碍；注意 `data_win32_modmanager.cpk` 体积 |
| 需要**换脸型/身材** | 等长改名做不到 | 进 Blender 改顶点 |
