#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重算 prm 参数块的大小字段（防"选人无模型 / 进战斗卡加载"）+ 可选移植投技参数条目。

两个功能
--------
1. **--fix-size**（最常用）
   把文件里所有 `prm_*` Binary 块的头部 `u16 @ offset 2`（大端）重算为 `len(块数据) - 4`。
   这是本项目最容易写错、也最难从现象反推的字段：写错 ⇒ 游戏解析 prm 越界 ⇒
   **选人界面模型消失 / 进战斗一直卡加载**。
   实测规律对全部参数块成立（2karprm_mot 40352 → 40348 等）。

2. **--port-throw**
   把**来源角色**的投技三个参数条目
   （`PL_ANM_THROW_BEGIN` / `PL_ANM_THROW_SUCCESS_ATTACKER` / `PL_ANM_THROW_SUCCESS_VICTIM`）
   移植到**目标角色**的 `prm_mot` 里，块内引用名做等长前缀替换。
   条目在 `prm_mot` 里**顺序存放、内嵌名字、没有偏移表**，引擎线性扫描匹配，
   所以整体替换这几个条目是安全的（条目数必须保持不变）。

   只换动画不换参数的症状：**投技动画放完了还没出伤害、也没有打飞特效。**

用法
----
    # 1) 只修大小字段
    python prm_mot_size_fix.py --prm 2karprm.bin.xfbin --out fixed.xfbin --fix-size --write

    # 2) 移植投技参数（Rin 4rin -> 香磷 2kar）
    python prm_mot_size_fix.py \
        --prm 2karprm.bin.xfbin --src-prm 4rinprm.bin.xfbin \
        --prm-name 2karprm_mot --src-prm-name 4rinprm_mot \
        --src-code 4rin --dst-code 2kar \
        --port-throw --fix-size --out 2karprm.bin.xfbin --write

    # 3) 只校验（不写）
    python prm_mot_size_fix.py --prm <文件> --fix-size

退出码 0 = 全部校验通过。
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import sys

# Windows 控制台默认可能是 GBK，中文输出会 UnicodeEncodeError —— 强制 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass

THROW_KEYS = (b"PL_ANM_THROW_BEGIN",
              b"PL_ANM_THROW_SUCCESS_ATTACKER",
              b"PL_ANM_THROW_SUCCESS_VICTIM")
THROW_END = b"PL_ANM_AWAKE_S"      # 第三个条目的边界（下一条）

MOT_ENTRY_COUNT_OFFSET = 52        # u32 小端：条目数
SIZE_FIELD_OFFSET = 2              # u16 大端：块长度 - 4


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


def load_lib(lib: str):
    sys.path.insert(0, lib)
    from xfbin import read_xfbin, write_xfbin_to_path       # type: ignore
    return read_xfbin, write_xfbin_to_path


def find_binary(xf, name: str):
    for page in xf.pages:
        for c in page.chunks:
            if type(c).__name__ == "NuccChunkBinary" and getattr(c, "name", "") == name:
                return c
    return None


def list_binaries(xf):
    out = []
    for page in xf.pages:
        for c in page.chunks:
            if type(c).__name__ == "NuccChunkBinary":
                out.append((getattr(c, "name", ""), len(bytes(c.data or b""))))
    return out


def report_size_fields(data: bytes, label: str) -> tuple[int, int]:
    """返回 (ok 数, bad 数)。"""
    ok = bad = 0
    field = struct.unpack_from(">H", data, SIZE_FIELD_OFFSET)[0]
    if field == len(data) - 4:
        ok += 1
        print(f"[size] {label:<24} len={len(data):<8} u16@2={field:<8} OK")
    else:
        bad += 1
        print(f"[size] {label:<24} len={len(data):<8} u16@2={field:<8} "
              f"应为 {len(data) - 4}  ★ 需修正")
    return ok, bad


def fix_size_field(data: bytearray) -> bytes:
    struct.pack_into(">H", data, SIZE_FIELD_OFFSET, len(data) - 4)
    return bytes(data)


def throw_spans(data: bytes) -> list[tuple[int, int]]:
    """定位三个投技条目的 (start, end)。"""
    starts = [data.find(k) for k in THROW_KEYS]
    end = data.find(THROW_END)
    if any(s < 0 for s in starts) or end < 0:
        raise ValueError(
            f"定位失败：{dict(zip([k.decode() for k in THROW_KEYS], starts))}, "
            f"{THROW_END.decode()}={end}")
    order = sorted(starts)
    if order != starts:
        raise ValueError(f"投技条目顺序异常: {starts}")
    return [(starts[0], starts[1]), (starts[1], starts[2]), (starts[2], end)]


def port_throw(dst_mot: bytearray, src_mot: bytes,
               src_code: bytes, dst_code: bytes) -> tuple[bytearray, list[int]]:
    if len(src_code) != len(dst_code):
        raise ValueError(f"前缀长度不等: {src_code!r} vs {dst_code!r}（必须等长）")

    dst_spans = throw_spans(bytes(dst_mot))
    src_spans = throw_spans(src_mot)
    print(f"[port] 目标条目区间: {dst_spans}")
    print(f"[port] 来源条目区间: {src_spans}")

    # 从后往前替换，避免前面的长度变化影响后面的偏移
    counts = []
    for (ds, de), (ss, se) in sorted(zip(dst_spans, src_spans), reverse=True):
        block = src_mot[ss:se]
        n = block.count(src_code)
        counts.append(n)
        block = block.replace(src_code, dst_code)
        if len(block) != se - ss:
            raise AssertionError("改名后长度变化——前缀必须等长")
        if block.find(src_code) >= 0:
            raise AssertionError(f"块内仍有 {src_code!r} 残留")
        dst_mot[ds:de] = block
        print(f"[port] 替换条目 [{ds}:{de}] ({de - ds} 字节)，改名 {n} 处")
    return dst_mot, counts


def main() -> int:
    ap = argparse.ArgumentParser(description="prm 大小字段修正 / 投技参数移植")
    ap.add_argument("--prm", required=True, help="目标 prm 文件（如 2karprm.bin.xfbin）")
    ap.add_argument("--out", help="输出路径（默认覆盖 --prm，会先自动备份）")
    ap.add_argument("--write", action="store_true", help="真的写出")
    ap.add_argument("--fix-size", action="store_true",
                    help="把所有 prm_* 块的 u16@2 重算为 len-4")
    ap.add_argument("--port-throw", action="store_true", help="移植投技三个参数条目")
    ap.add_argument("--src-prm", help="来源 prm 文件（--port-throw 时必填）")
    ap.add_argument("--prm-name", help="目标 prm_mot 块名（如 2karprm_mot）")
    ap.add_argument("--src-prm-name", help="来源 prm_mot 块名（如 4rinprm_mot）")
    ap.add_argument("--src-code", help="来源角色前缀（如 4rin）")
    ap.add_argument("--dst-code", help="目标角色前缀（如 2kar）")
    ap.add_argument("--game-dir", help="游戏根目录（用于定位 xfbin_lib）")
    ap.add_argument("--xfbin-lib", help="xfbin_lib 目录")
    args = ap.parse_args()

    if not (args.fix_size or args.port_throw):
        ap.error("至少要指定 --fix-size 或 --port-throw 之一")

    lib = find_lib(args)
    if not lib:
        print("[FATAL] 找不到 xfbin_lib：用 --xfbin-lib 或 --game-dir 指定", file=sys.stderr)
        return 2
    read_xfbin, write_xfbin_to_path = load_lib(lib)

    print(f"# xfbin_lib: {lib}")
    print(f"# 目标: {args.prm}")
    xf = read_xfbin(args.prm)
    print(f"# 参数块: {list_binaries(xf)}")

    ok = bad = 0
    for name, _ in list_binaries(xf):
        c = find_binary(xf, name)
        if c is None or not c.data:
            continue
        data = bytes(c.data)
        if len(data) < 6:
            continue
        o, b = report_size_fields(data, name)
        ok += o
        bad += b

    if args.port_throw:
        if not (args.src_prm and args.prm_name and args.src_prm_name
                and args.src_code and args.dst_code):
            print("[FATAL] --port-throw 需要 --src-prm --prm-name --src-prm-name "
                  "--src-code --dst-code", file=sys.stderr)
            return 2

        src_xf = read_xfbin(args.src_prm)
        src_chunk = find_binary(src_xf, args.src_prm_name)
        dst_chunk = find_binary(xf, args.prm_name)
        if src_chunk is None:
            print(f"[FATAL] 来源里找不到块 {args.src_prm_name}；"
                  f" 可用: {list_binaries(src_xf)}", file=sys.stderr)
            return 2
        if dst_chunk is None:
            print(f"[FATAL] 目标里找不到块 {args.prm_name}；"
                  f" 可用: {list_binaries(xf)}", file=sys.stderr)
            return 2

        src_mot = bytes(src_chunk.data)
        dst_mot = bytearray(dst_chunk.data)
        src_count = struct.unpack_from("<I", src_mot, MOT_ENTRY_COUNT_OFFSET)[0]
        dst_count = struct.unpack_from("<I", dst_mot, MOT_ENTRY_COUNT_OFFSET)[0]
        print(f"[port] 条目数: 来源={src_count} 目标={dst_count}")
        if src_count != dst_count and len(src_mot) > 56 and len(dst_mot) > 56:
            print("[warn] 两边条目数不同——本流程只替换投技三项，条目数应保持不变；"
                  " 请确认这对文件是否是同一类角色的 prm")

        dst_mot, counts = port_throw(dst_mot, src_mot,
                                     args.src_code.encode("ascii"),
                                     args.dst_code.encode("ascii"))
        dst_chunk.data = bytearray(dst_mot)
        print(f"[port] 改名处数: {counts}")

    if args.fix_size:
        fixed = 0
        for name, _ in list_binaries(xf):
            c = find_binary(xf, name)
            if c is None or not c.data or len(bytes(c.data)) < 6:
                continue
            data = bytearray(c.data)
            before = struct.unpack_from(">H", data, SIZE_FIELD_OFFSET)[0]
            new = fix_size_field(data)
            after = struct.unpack_from(">H", new, SIZE_FIELD_OFFSET)[0]
            if before != after:
                fixed += 1
                print(f"[fix] {name:<24} {before} -> {after}")
            c.data = bytearray(new)
        print(f"[fix] 修正了 {fixed} 个块的大小字段")

    # ---------- 写前复核 ----------
    print("\n# 写前复核")
    all_ok = True
    for name, _ in list_binaries(xf):
        c = find_binary(xf, name)
        data = bytes(c.data) if c and c.data else b""
        if len(data) < 6:
            continue
        field = struct.unpack_from(">H", data, SIZE_FIELD_OFFSET)[0]
        good = field == len(data) - 4
        all_ok &= good
        print(f"  {name:<24} u16@2={field:<8} len-4={len(data) - 4:<8} "
              + ("OK" if good else "★ 不一致"))
    if args.port_throw:
        dst_chunk = find_binary(xf, args.prm_name)
        dst_mot = bytes(dst_chunk.data)
        dst_count = struct.unpack_from("<I", dst_mot, MOT_ENTRY_COUNT_OFFSET)[0]
        print(f"  条目数 = {dst_count}")
        residues = dst_mot.count(args.src_code.encode("ascii"))
        print(f"  '{args.src_code}' 残留 = {residues}"
              + ("（注意：名字表里可能有来源角色的无害残留，需看引用而非 grep）"
                 if residues else ""))
    if not all_ok:
        print("[FATAL] 仍有大小字段不一致，拒绝写出", file=sys.stderr)
        return 2

    if not args.write:
        print("\n[dry-run] 未写出。加 --write 才会写。")
        return 0

    out = args.out or args.prm
    if os.path.abspath(out) == os.path.abspath(args.prm):
        bak = args.prm + ".bak"
        shutil.copyfile(args.prm, bak)
        print(f"\n[backup] {bak}")
    write_xfbin_to_path(xf, out)
    print(f"[write] {out}")

    # ---------- 回读验证 ----------
    print("\n# 回读验证")
    back = read_xfbin(out)
    for name, _ in list_binaries(back):
        c = find_binary(back, name)
        data = bytes(c.data) if c and c.data else b""
        if len(data) < 6:
            continue
        field = struct.unpack_from(">H", data, SIZE_FIELD_OFFSET)[0]
        good = field == len(data) - 4
        print(f"  {name:<24} u16@2={field:<8} len-4={len(data) - 4:<8} "
              + ("OK" if good else "★ FAIL"))
        if not good:
            return 2
    print("[done] 记住：退出游戏 → 只启用本 mod → 重新打包 → 进游戏测投技")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
