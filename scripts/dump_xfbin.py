#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打印 XFBIN 的结构：页 / 块 / 骨架 / 贴图 / 材质 / 参数块大小字段。

用途
----
* 定位模型页与动画页（移植投技时要找 hola0/hola1/hold0 所在的页）；
* dump 骨架（`Coord`）骨骼名，用于比对两个角色的核心骨骼是否同名；
* 检查 `prm_*` 参数块的大小字段是否满足 `u16@2 == len-4`（写错会卡加载）；
* 检查文件名前缀残留。

用法
----
    python dump_xfbin.py <文件.xfbin> [--bones] [--params] [--names 2kar]

xfbin_lib 定位优先级：--xfbin-lib > 环境变量 XFBIN_LIB > --game-dir 下的默认位置。
"""

from __future__ import annotations

import argparse
import os
import re
import struct
import sys

# Windows 控制台默认可能是 GBK，中文/符号输出会 UnicodeEncodeError —— 强制 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass


def find_lib(args) -> str | None:
    cands = []
    if args.xfbin_lib:
        cands.append(args.xfbin_lib)
    if os.environ.get("XFBIN_LIB"):
        cands.append(os.environ["XFBIN_LIB"])
    if args.game_dir:
        cands.append(os.path.join(args.game_dir, "codex_blender_addon", "addons",
                                  "XFBINImporter42", "xfbin_lib"))
    for c in cands:
        if c and os.path.isdir(c):
            return os.path.abspath(c)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="dump XFBIN 结构")
    ap.add_argument("path", help="xfbin 文件路径")
    ap.add_argument("--xfbin-lib", help="xfbin_lib 目录")
    ap.add_argument("--game-dir", help="游戏根目录（用于自动定位 xfbin_lib）")
    ap.add_argument("--bones", action="store_true", help="dump 全部骨骼名")
    ap.add_argument("--params", action="store_true", help="检查参数块大小字段")
    ap.add_argument("--names", default=None, help="统计该前缀出现次数（如 2kar）")
    ap.add_argument("--raw", action="store_true", help="只用原始字节扫描（不需要 xfbin_lib）")
    args = ap.parse_args()

    if not os.path.isfile(args.path):
        print(f"[FATAL] 文件不存在: {args.path}", file=sys.stderr)
        return 2

    lib = find_lib(args)

    # ---------- 原始字节信息（总能给出） ----------
    raw = open(args.path, "rb").read()
    print(f"# 文件: {args.path}")
    print(f"# 大小: {len(raw)}")
    print(f"# magic: {raw[:4]!r}"
          + ("（NUCC/XFBIN）" if raw[:4] == b"NUCC" else
             "（注意：不是 NUCC，可能是 CPK 压缩件）"))
    if args.names:
        code = args.names.encode("ascii", "ignore")
        print(f"# '{args.names}' 出现 {raw.count(code)} 次")

    if args.raw or not lib:
        if not lib:
            print("# 未找到 xfbin_lib，仅给出原始字节信息（--xfbin-lib / --game-dir / $XFBIN_LIB）")
        hits = sorted({m.decode("ascii", "ignore")
                       for m in re.findall(rb"[0-9a-z]{4}hola[0-9]", raw)})
        if hits:
            print(f"# 投技动画名（原始扫描）: {hits}")
        return 0

    sys.path.insert(0, lib)
    from xfbin import read_xfbin
    from xfbin.structure.nucc import (
        NuccChunkClump, NuccChunkMaterial, NuccChunkTexture,
    )

    xf = read_xfbin(args.path)
    print(f"# pages: {len(xf.pages)}")

    binary_chunks: list[tuple[str, bytes]] = []
    for i, page in enumerate(xf.pages):
        kinds = []
        for c in page.chunks:
            tname = type(c).__name__
            short = tname.replace("NuccChunk", "")
            nm = getattr(c, "name", "") or ""
            kinds.append(f"{short}:{nm}" if nm else short)
            if tname == "NuccChunkBinary" and nm:
                binary_chunks.append((nm, bytes(c.data)))
        print(f"[page {i:>3}] {len(page.chunks)} chunks | " + ", ".join(kinds))

    # ---------- 骨架 ----------
    all_bones: list[str] = []
    for page in xf.pages:
        for cl in page.get_chunks_by_type(NuccChunkClump):
            bones = [c.name for c in cl.coord_chunks]
            all_bones.extend(bones)
            print(f"\n[clump] bones={len(bones)} models={len(cl.model_chunks)} "
                  f"groups={len(cl.model_groups)}")
            print(f"[clump] models: {[m.name for m in cl.model_chunks]}")
            for g in cl.model_groups:
                names = [getattr(m, "name", m) for m in g.model_chunks]
                print(f"[clump] group(flag0={getattr(g, 'flag0', '?')}) "
                      f"{len(names)} models: {names}")
    if all_bones:
        prefixes = sorted({b.split("0", 1)[0] for b in all_bones if b})
        print(f"[bones] 共 {len(all_bones)} 根；前缀集合: {prefixes}")
        print(f"[bones] 前 8 根: {all_bones[:8]}")
        if args.bones:
            for b in all_bones:
                print(f"    {b}")

    # ---------- 贴图 / 材质 ----------
    print()
    for page in xf.pages:
        for t in page.get_chunks_by_type(NuccChunkTexture):
            print(f"[tex] {t.name}  path={t.filePath}")
        for m in page.get_chunks_by_type(NuccChunkMaterial):
            groups = getattr(m, "texture_groups", [])
            refs = [t.name for g in groups for t in g.texture_chunks]
            size = getattr(m, "size", None)
            print(f"[mat] {m.name}  贴图槽组数={len(groups)}  refs={refs}"
                  + (f"  size={size}" if size is not None else ""))

    # ---------- 参数块大小字段 ----------
    if args.params or binary_chunks:
        print()
        bad = 0
        for name, data in binary_chunks:
            if len(data) < 6:
                continue
            field = struct.unpack_from(">H", data, 2)[0]
            entries = struct.unpack_from("<I", data, 52)[0] if len(data) >= 56 else None
            ok = (field == len(data) - 4)
            if not ok:
                bad += 1
            print(f"[prm] {name:<22} len={len(data):<8} u16@2={field:<8} "
                  f"len-4={len(data) - 4:<8} {'OK' if ok else '★ 不一致！'} "
                  + (f"entries@{52}={entries}" if entries is not None else ""))
        if bad:
            print(f"[prm] ★ 有 {bad} 个块的大小字段 != len-4：改过内容后必须重算，"
                  " 否则可能导致选人无模型 / 进战斗卡加载（见 prm_mot_size_fix.py）")
        else:
            print("[prm] 全部参数块的 u16@2 == len-4  ✅")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
