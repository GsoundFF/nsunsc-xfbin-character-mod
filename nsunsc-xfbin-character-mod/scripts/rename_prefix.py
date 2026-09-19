#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""等长前缀改名：把游戏自带角色 / 外部模型的文件换到目标角色槽位。

这是 NSUNSC（究极风暴羁绊）模型替换里最稳的一步：XFBIN 的名字表是变长字符串表，
只要来源前缀与目标前缀**字节长度相同**（都是 4 字符），替换后所有字符串长度、
表偏移与索引全部不变，因此是安全的字节级操作。

用法
----
    # 只预览（默认），打印替换处数与校验结果
    python rename_prefix.py --src 2tmrbod1.xfbin --src-code 2tmr --dst-code 2kar

    # 真的写出
    python rename_prefix.py --src 2tmrbod1.xfbin --src-code 2tmr --dst-code 2kar \
        --out "<游戏目录>\\modmanager\\Temari Outfit for Karin\\Resources\\Files\\data\\spc\\2karbod1.xfbin" --write

    # 连同目标角色的原版攻击文件一起放进槽位（推荐的一步到位）
    python rename_prefix.py --src ...\\2tmrbod1.xfbin --src-code 2tmr --dst-code 2kar \
        --out ...\\2karbod1.xfbin --write \
        --keep-attack "E:\\fight date\\spc_角色模型\\spc" --keep-code 2kar

校验
----
  1) 来源/目标前缀长度必须相等；
  2) 输出长度必须等于输入长度；
  3) 归一化（两边前缀都换成占位符）后两文件必须逐字节相同；
  4) 可选：用 xfbin_lib 回读，确认骨架名无来源前缀残留。

退出码 0 = 全部校验通过。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from hashlib import md5

# Windows 控制台默认可能是 GBK，中文输出会 UnicodeEncodeError —— 强制 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")   # type: ignore[attr-defined]
except Exception:  # noqa: BLE001
    pass

ATTACK_SUFFIXES = (
    "bod1c.xfbin",        # 普通攻击 / 连段
    "bod1l.xfbin",        # 投技
    "bod1s.xfbin",        # 技能
    "bod1acc.bin.xfbin",  # 配件参数
)


def find_xfbin_lib(game_dir: str | None) -> str | None:
    """尝试定位 xfbin_lib（只用于可选的回读校验）。"""
    candidates = []
    if game_dir:
        candidates.append(os.path.join(
            game_dir, "codex_blender_addon", "addons", "XFBINImporter42", "xfbin_lib"))
    if os.environ.get("XFBIN_LIB"):
        candidates.insert(0, os.environ["XFBIN_LIB"])
    for c in candidates:
        if os.path.isdir(c):
            return os.path.abspath(c)
    return None


def byte_diff_report(src: bytes, out: bytes, src_code: bytes, dst_code: bytes) -> None:
    """逐字节校验：归一化后必须完全一致。"""
    if len(src) != len(out):
        raise AssertionError(f"输出长度 {len(out)} != 输入长度 {len(src)}")

    norm_src = src.replace(src_code, b"\x00" * len(src_code))
    norm_out = out.replace(dst_code, b"\x00" * len(dst_code))
    if norm_src != norm_out:
        diffs = [i for i, (a, b) in enumerate(zip(norm_src, norm_out)) if a != b]
        raise AssertionError(
            f"改名字符串之外仍有 {len(diffs)} 处字节差异（前 10 个偏移: {diffs[:10]}）——"
            " 这不是纯改名，停下来检查")
    print("[OK] 归一化后逐字节一致（差异仅来自前缀改名）")


def try_readback(path: str, lib: str | None) -> None:
    """可选：用 xfbin_lib 回读，打印骨架/贴图/材质摘要。"""
    if not lib:
        print("[skip] 未找到 xfbin_lib，跳过回读校验（设置 --xfbin-lib 可启用）")
        return
    sys.path.insert(0, lib)
    try:
        from xfbin import read_xfbin
        from xfbin.structure.nucc import (
            NuccChunkClump, NuccChunkMaterial, NuccChunkTexture,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[skip] 导入 xfbin_lib 失败: {exc}")
        return

    xf = read_xfbin(path)
    print(f"[readback] pages = {len(xf.pages)}")
    for page in xf.pages:
        for cl in page.get_chunks_by_type(NuccChunkClump):
            bones = [c.name for c in cl.coord_chunks]
            print(f"[readback] CLUMP bones={len(bones)} models={len(cl.model_chunks)} "
                  f"groups={len(cl.model_groups)}")
            print(f"[readback]   first bones: {bones[:5]}")
            print(f"[readback]   models: {[m.name for m in cl.model_chunks]}")
        for t in page.get_chunks_by_type(NuccChunkTexture):
            print(f"[readback]   TEX {t.name} (path={t.filePath})")
        for m in page.get_chunks_by_type(NuccChunkMaterial):
            refs = [t.name for g in m.texture_groups for t in g.texture_chunks]
            print(f"[readback]   MAT {m.name} -> {refs}")


def copy_attack_files(src_dir: str, dst_spc: str, keep_code: str) -> None:
    """把目标角色的原版攻击文件复制进槽位（保证动作不变）。"""
    os.makedirs(dst_spc, exist_ok=True)
    for suffix in ATTACK_SUFFIXES:
        name = f"{keep_code}{suffix}"
        s = os.path.join(src_dir, name)
        if not os.path.isfile(s):
            print(f"[warn] 找不到目标角色原版攻击文件: {s}（跳过）")
            continue
        d = os.path.join(dst_spc, name)
        shutil.copyfile(s, d)
        same = md5(open(s, "rb").read()).hexdigest() == md5(open(d, "rb").read()).hexdigest()
        print(f"[attack] copied {name}  identical={same}")


def main() -> int:
    ap = argparse.ArgumentParser(description="XFBIN 等长前缀改名（NSUNSC 模型替换）")
    ap.add_argument("--src", required=True, help="来源模型文件（如 2tmrbod1.xfbin）")
    ap.add_argument("--src-code", required=True, help="来源角色前缀（4 字符，如 2tmr）")
    ap.add_argument("--dst-code", required=True, help="目标角色前缀（4 字符，如 2kar）")
    ap.add_argument("--out", help="输出文件路径（不给则只预览）")
    ap.add_argument("--write", action="store_true", help="真的写出文件（默认只预览）")
    ap.add_argument("--game-dir", help="游戏根目录（用于自动定位 xfbin_lib）")
    ap.add_argument("--xfbin-lib", help="xfbin_lib 目录（显式指定）")
    ap.add_argument("--keep-attack", help="目标角色原版攻击文件所在目录（如 E:\\fight date\\spc_角色模型\\spc）")
    ap.add_argument("--keep-code", help="目标角色代码，用于 --keep-attack（默认取 --dst-code）")
    args = ap.parse_args()

    src_code = args.src_code.encode("ascii")
    dst_code = args.dst_code.encode("ascii")

    if len(src_code) != len(dst_code):
        print(f"[FATAL] 前缀长度不等: {args.src_code}={len(src_code)} vs "
              f"{args.dst_code}={len(dst_code)} —— 会破坏名字表，必须等长", file=sys.stderr)
        return 2
    if not os.path.isfile(args.src):
        print(f"[FATAL] 来源文件不存在: {args.src}", file=sys.stderr)
        return 2

    raw = open(args.src, "rb").read()
    if not raw.startswith(b"NUCC"):
        print(f"[FATAL] {args.src} 不是 NUCC/XFBIN（magic={raw[:4]!r}）；"
              " 若是 'CPK ' 说明它是 CPK 压缩件，需先解包", file=sys.stderr)
        return 2

    count = raw.count(src_code)
    print(f"[src] {args.src}")
    print(f"[src] size = {len(raw)}  '{args.src_code}' 出现 {count} 次")
    if count == 0:
        print(f"[FATAL] 文件里没有 '{args.src_code}'，前缀给错了？", file=sys.stderr)
        return 2

    out = raw.replace(src_code, dst_code)
    print(f"[rename] '{args.src_code}' -> '{args.dst_code}'，替换 {count} 处")
    print(f"[rename] 输出长度 {len(out)}（输入 {len(raw)}）")
    byte_diff_report(raw, out, src_code, dst_code)

    if out.count(src_code):
        print(f"[FATAL] 改后仍有 {out.count(src_code)} 处残留", file=sys.stderr)
        return 2
    print(f"[rename] 无 '{args.src_code}' 残留")

    if not (args.write and args.out):
        print("[dry-run] 未写出。加 --out <路径> --write 才会写文件。")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    if os.path.isfile(args.out):
        bak = args.out + ".bak"
        shutil.copyfile(args.out, bak)
        print(f"[backup] 原文件已备份到 {bak}")
    with open(args.out, "wb") as fh:
        fh.write(out)
    print(f"[write] {args.out}  ({len(out)} 字节)")

    lib = args.xfbin_lib or find_xfbin_lib(args.game_dir)
    try_readback(args.out, lib)

    if args.keep_attack:
        copy_attack_files(args.keep_attack, os.path.dirname(os.path.abspath(args.out)),
                          args.keep_code or args.dst_code)

    print("[done] 记住：退出游戏 → Mod Manager 只启用本 mod → 重新打包 → 进游戏验证")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
