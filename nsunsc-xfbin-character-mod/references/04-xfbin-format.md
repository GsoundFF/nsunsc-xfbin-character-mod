# XFBIN / NUCC 文件格式与在本作里的用法

本文所有字段与偏移都用 `xfin_lib`（`codex_blender_addon\addons\XFBINImporter42\xfbin_lib`）
的 `br_xfbin.py` / `br_nucc.py` 源码与真实文件实测核对过。

---

## 1. 文件头（28 字节）

| 偏移 | 类型 | 字段 | 实测值 / 说明 |
|---|---|---|---|
| 0x00 | char[4] | `magic` | 必须是 `NUCC`。若是 `CPK ` ⇒ 这个文件是 **CPK 压缩过的**，需先解 CPK。 |
| 0x04 | u32 | `nuccId` | 本作 `0x79` |
| 0x08 | u64 | padding | 固定 0（8 字节） |
| 0x10 | u32 | `chunkTableSize` | 块表大小（**不含** references 部分） |
| 0x14 | u32 | `minPageSize` | 通常 3 |
| 0x18 | u16 | `nuccId2` | 本作 `0x79` |
| 0x1A | u16 | `unk` | 0 |

实测 `2karbod1.xfbin`（3588242 字节）前 16 字节：
`4E 55 43 43 00 00 00 79 00 00 00 00 00 00 00 00` → `NUCC` + `0x79` + 8 字节零。

> 读取时 `read_xfbin` 会校验 magic，不是 `NUCC` 直接抛异常。
> 遇到 `Invalid magic. XFBIN file is possibly CPK compressed.` 说明你拿到的是 CPK 内的压缩件。

---

## 2. 块表（Chunk Table）

紧跟文件头。全部整数都是**大端**，字符串是 **cp932** 编码。

```
u32 chunkTypeCount ; u32 chunkTypeSize     # 类型名表（"Model" / "Anm" / "Texture" ...）
u32 filePathCount  ; u32 filePathSize
u32 chunkNameCount ; u32 chunkNameSize     # ★ 名字表（"2kar00t0 body" / "2karhola0" ...）
u32 chunkMapCount  ; u32 chunkMapSize
u32 chunkMapIndicesCount
u32 chunkMapReferencesCount
── 然后是各字符串区（依次 type / filePath / name），末尾 4 字节对齐 ──
── 然后 chunkMap 数组：每个 12 字节 = 3 个 u32 索引（typeIndex, filePathIndex, nameIndex） ──
── 然后 references 数组：每个 8 字节 = (chunkNameIndex, chunkMapIndex) ──
── 然后 chunkMapIndices：u32 × chunkMapIndicesCount ──
```

**为什么"等长前缀改名"是安全的**：名字在名字表里是**以 `\0` 结尾的变长字符串**，
当把 `2ten` 换成 `2kar`（同为 4 字节）时，所有字符串长度不变 ⇒
`chunkNameSize`、各表偏移、所有索引**全部不用改**。这就是必须**等长**的原因。

**为什么"整体重写文件"是危险的**：`BrXfbin.__br_write__` 会**重建整个块表**——
它用 `IterativeDict` **按写入顺序重新分配索引**，而不是沿用原索引。
所以整体 `write_xfbin_to_path` 出来的文件**大小和字节布局都会变**（非逐字节保真），
对 `bod1l` 这类含复杂模型/动画块的文件尤其危险。

> **结论**：能只做动画页替换就只做动画页替换；能字节级等长替换就字节级替换。
> 只有确实需要重建结构时（如 Blender 注入导出）才整体重写，并且必须回读验证。

---

## 3. 页（Page）与块（Chunk）

文件 = 一串**页**；每页 = 若干块 + 结尾一个 `NuccChunkPage`（`pageSize` / `referenceSize` 在这里）。

**块的二进制头（12 字节）**：

| 偏移 | 类型 | 字段 |
|---|---|---|
| 0x00 | u32 | `size`（payload 字节数） |
| 0x04 | u32 | `chunkMapIndex`（本页内的局部索引） |
| 0x08 | u16 | `nuccId`（写出时固定 0x79，读入时用于影响部分块的解析） |
| 0x0A | u16 | `unk`（部分动画块非 0） |

紧跟 `size` 字节的 payload。

**块类型名**（字符串形式，见 `chunkTypes` 表）：

| 类型 | 作用 | 本作典型名字 |
|---|---|---|
| `Null` | 页起始占位（每页第一个块） | 空 |
| `Page` | 页结尾标记 | `Page0` |
| `Texture` | `NUT`（`NTP3`）贴图 | `2karbody` / `2karbody_lod1` / `2kareye` |
| `Dynamics` | 物理/摆动 | `2karbod1` |
| `Model` | `NUD`（`NDP3`）网格 | `2kar00t0 body` / `kao` / `kami` / `eye_l` / `eye_r` / `upper teeth` / `lower teeth` / `tongue` / `megane` / `udeanml` … 及各自 `_lod1` |
| `Coord` | 骨架（骨骼坐标） | `2kar00t0 trall`（根）、`2kar00t0` |
| `Material` | 材质（贴图槽在这里） | `2kareye_l` / `2kareye_r` … |
| `Anm` | 动画页 | `2karhola0` / `2karhola1` / `2karhold0` … |
| `Camera` | 摄像机轨道 | `camera01` / `camera001` |
| `LightDirc` | 方向光 | `fdirect001` |
| `Binary` | 原始二进制块（参数块都是这种） | `2karprm_mot` / `2karprm_awa` … |

---

## 4. `2karbod1.xfbin` 的真实结构（实测）

```
size = 3588242 字节，共 5 页

page 0: Textures  2karbody
page 1: Textures  2karbody_lod1
page 2: Textures  2kareye
page 3: Dynamics  2karbod1
page 4: Model/Coord 主体
        Model 2kar_udeanml, 2kar_udeanmr
        Model 2kar00t0 upper teeth / tongue / lower teeth / megane
        Model 2kar00t0 eye_r / eye_l / kao / kami
        Model 2kar_asianimel / 2kar_asianimer
        Model 2kar00t0 body
        Model 2kar00t0 megane_lod1 / eye_l_lod1 / eye_r_lod1 / kami_lod1 / kao_lod1 / body_lod1
        Coord 2kar00t0 trall
        Coord 2kar00t0
```

**要点**
- `body` / `kao`（脸）/ `kami`（头发）**各有 lod1 副本** ⇒ 外观修改通常要**两套都改**。
- `eye_l` / `eye_r` 与 `eye_l_lod1` / `eye_r_lod1` 是**无蒙皮权重的刚性网格**，见 SKILL 第 5.3 节。
- `megane`（眼镜）存在但通常为空模型。

### 动作文件 `2karbod1l.xfbin`（投技）

```
共 39 页，每页 = Null + [Camera/LightDirc] + Anm + Page
动画名实例：2karhola0 / 2karhola1 / 2karhold0（被投反应用通用骨骼 1cmn00t0）
带附属块的页：
  page 9  → camera01
  page 13 → camera01
  page 16 → camera01
  page 32 → camera001 + fdirect001 (LightDirc)   ← 投出特写，必须一起搬
```

> 移植投技时**只搬整页**（含附属 `Camera` / `LightDirc`），引用名等长改名，
> 页内块顺序不动。见 SKILL 第 6 节。

---

## 5. `NUD`（`NDP3`）与 `NUT`（`NTP3`）

- `Model` 块的 payload 是 `NUD`，magic `NDP3`（`br_nud.py` 会校验）。
- `Texture` 块的 payload 是 `NUT`，magic `NTP3`。
- **顶点坐标是整数**：`i16`，单位取决于模型（手鞠/香磷体系里 NUD 坐标 ≈ 厘米，
  即 Blender 米制 ×100）。做坐标烘焙时按整数写回。
- 刚性网格的坐标语义随角色不同（"骨骼在原点、世界位置写在顶点里" vs
  "骨骼在头部、顶点只是局部小偏移"）——见 SKILL 第 5.3 节。

---

## 6. 参数（prm）块：`prm_mot` 与大小字段铁律

`2karprm.bin.xfbin` 里全是 `Binary` 块，实测各块：

| 块名 | 块长 | 字段 @2 | `len-4` |
|---|---|---|---|
| `2karprm_awa` | 2412 | 2408 | 2408 |
| `2karprm_etc` | 676 | 672 | 672 |
| `2karprm_hit` | 560 | 556 | 556 |
| `2karprm_load` | 2248 | 2244 | 2244 |
| `2karprm_mot` | 40352 | **40348** | 40348 |
| `2karprm_skl` | 3340 | 3336 | 3336 |
| `2karprm_sklslot` | 3745 | **3741** | 3741 |
| `2karprm_spl` | 9580 | 9576 | 9576 |

### ★ 铁律

```
块头部 offset 2..4  (u16, 大端)  ==  块数据长度 - 4
```

**规律对全部参数块一致成立**（连 3745 这种非 4 对齐、2412 这种都成立）。
改完 `prm_mot` 内容后**必须重算这个字段**：

```python
import struct
struct.pack_into(">H", mot, 2, len(mot) - 4)
```

写错的后果：游戏解析 `prm` 时越界 ⇒ **选人界面模型消失 / 进战斗一直卡加载**。
这一条是本项目里最容易写错、也最难从现象反推的字段。

### `prm_mot` 条目布局

```
[版本头]
offset 52 : u32 (小端) 条目数      # 2kar 实测 91
然后：条目顺序存放，每条内嵌名字字符串
```

- 条目**没有集中偏移表**，引擎**线性扫描**名字匹配（`PL_ANM_XXX`）。
- ⇒ 替换其中几个条目（保持条目数不变）是安全的。
- 已知条目名（投技相关）：
  `PL_ANM_THROW_BEGIN` / `PL_ANM_THROW_SUCCESS_ATTACKER` /
  `PL_ANM_THROW_SUCCESS_VICTIM`；其后是 `PL_ANM_AWAKE_S`（用来切条目边界）。
- 条目里引用的动画名形如 `2karhola0`，判定点骨骼形如 `2kar00t0 l forearm`。

---

## 7. 名字表与"残留名字"的正确理解

**名字表里会有你不再使用、但依然存在的字符串。** 这不一定是 bug：

- `2karbod1l.xfbin`（Rin 投技版）里同时存在 `2karhola0`/`2karhola1`/`2karhold0`
  **与** `4rinhola0`/`4rinhola1`/`4rinhold0`。
- 原因是投技页是从 Rin 的文件里整页搬来的，**Rin 的名字被登记进了本文件的名字表**，
  但实际被引用的动画块名已经改成 `2kar*`。

**判定"改名是否真的生效"要看引用（块名 / references），不要简单地 grep 字符串。**
校验的正确姿势：
1. 枚举实际的 `Anm` 块名 → 应为 `2karhola0` 等；
2. 用 `xfin_lib` 重读输出，逐条对比动画条目（骨骼名改名后、`entry_format`、
   各曲线关键帧数量）与来源一致；
3. 确认页面引用里没有来源角色前缀（如 `ino`）；
4. `camera01` 这类通用名保持原名。

---

## 8. 常用操作片段

```python
import sys, struct
sys.path.insert(0, r"<游戏目录>\codex_blender_addon\addons\XFBINImporter42\xfbin_lib")
from xfbin import read_xfbin, write_xfbin_to_path

# 8.1 列出结构
xf = read_xfbin(r"<...>\2karbod1.xfbin")
for i, page in enumerate(xf.pages):
    print(i, [(type(c).__name__, getattr(c, "name", "")) for c in page.chunks])

# 8.2 取出参数块（Binary）
def get_binary(xf, name):
    for page in xf.pages:
        for c in page.chunks:
            if type(c).__name__ == "NuccChunkBinary" and c.name == name:
                return bytearray(c.data)
    raise KeyError(name)

# 8.3 写回参数块（注意 data 用 bytearray）
def set_binary(path, name, payload):
    xf = read_xfbin(path)
    for page in xf.pages:
        for c in page.chunks:
            if type(c).__name__ == "NuccChunkBinary" and c.name == name:
                c.data = bytearray(payload)
                write_xfbin_to_path(xf, path)
                return
    raise KeyError(name)
```

**等长前缀改名（字节级，最稳）**：

```python
data = open(src, "rb").read()
n = data.count(b"2ten")
assert n > 0
assert len(b"2ten") == len(b"2kar")          # ★ 必须等长
out = data.replace(b"2ten", b"2kar")
assert len(out) == len(data)                  # ★ 长度必须不变
open(dst, "wb").write(out)
print("替换处数:", n)                          # 手鞠案例 = 247
```

---

## 9. 检查清单（改完 XFBIN 后）

- [ ] `NUCC` magic 仍在，文件能被 `read_xfbin` 无异常读出；
- [ ] 页数、每页块数与顺序与原文件一致（只做内容替换时）；
- [ ] 名字表字符串长度未变（等长替换）、`chunkNameSize` 未变；
- [ ] 参数块 `offset 2..4 == len-4`，条目数不变；
- [ ] 重读输出再验一遍（不要只看内存对象）；
- [ ] `body` / `kao` / `kami` 的 **lod1 副本**也处理了（如果这次动的是它们）；
- [ ] 备份文件已存在 `codex_mod_backups\`。
