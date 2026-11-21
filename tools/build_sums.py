# -*- coding: utf-8 -*-
"""元和经纬 · 学术账目生成器（SHA256SUMS）

范围（构建产物级）：
  data/ 全目录（管线产物层 js/json/txt/html）
  index.html · sw.js · manifest.json（发版门面）
  docs/*.pdf（论文 PDF）· docs/export/（州县导出件）
不含：data_raw/（原始抓取）· vendor/ · tests/ · tools/ 源码 · js/css 手写前端。

纪律（HHH CRLF 教训，decisions.tsv 在案）：
  1) 账本本身必须纯 LF——open(..., "w", newline="\n") 写出，零例外；
  2) 指纹口径「行尾无关」——文本按 CRLF→LF 归一后哈希（库内归一字节即 LF，
     本机 autocrlf 工作区得 CRLF 亦不炸），二进制（含 b"\\x00"，如 PDF）按原字节。
     这样账本在 Windows/Linux 任意 checkout 下都成立。
幂等：内容不变则不落盘（字节级不变）。

用法：
  python tools/build_sums.py           生成/更新仓库根 SHA256SUMS
  python tools/build_sums.py --check   只对账不落盘，过期即退出码 1
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "SHA256SUMS")
ROOT_FILES = ("index.html", "sw.js", "manifest.json")
EXPORT_DIRS = ("docs/export",)


def collect():
    """应入账的相对路径集合（/ 分隔）。"""
    rels = set()

    def walk(top):
        for dp, _, fns in os.walk(os.path.join(ROOT, top)):
            for fn in fns:
                rels.add(os.path.relpath(os.path.join(dp, fn), ROOT).replace("\\", "/"))

    walk("data")                                    # 产物层全目录
    for rel in ROOT_FILES:                          # 发版门面
        if os.path.isfile(os.path.join(ROOT, rel)):
            rels.add(rel)
    docs = os.path.join(ROOT, "docs")               # 论文 PDF
    rels.update(os.path.relpath(os.path.join(docs, fn), ROOT).replace("\\", "/")
                for fn in os.listdir(docs) if fn.endswith(".pdf"))
    for d in EXPORT_DIRS:                           # 导出件
        if os.path.isdir(os.path.join(ROOT, d)):
            walk(d)
    return sorted(rels)


def sha256(rel):
    """行尾无关指纹：文本 CRLF→LF 归一后哈希（= 库内归一字节），二进制原字节。"""
    blob = open(os.path.join(ROOT, rel), "rb").read()
    if b"\x00" in blob:                       # 二进制（PDF/PNG 等）——原字节
        pass
    else:
        blob = blob.replace(b"\r\n", b"\n")   # 文本归一：本机 CRLF / 库内 LF 同指纹
    return hashlib.sha256(blob).hexdigest()


def build_lines():
    """sha256sum 格式账目行：<sha256>␣␣<相对路径>。"""
    return [f"{sha256(rel)}  {rel}" for rel in collect()]


def main(argv):
    lines = build_lines()
    want = "\n".join(lines) + "\n"
    have = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if "--check" in argv:
        if have != want:
            print(f"✗ SHA256SUMS 过期（应 {len(lines)} 行）——重跑 python tools/build_sums.py")
            return 1
        print(f"✓ SHA256SUMS 就绪：{len(lines)} 行（LF）")
        return 0
    if have == want:
        print(f"SHA256SUMS 已是最新：{len(lines)} 行（字节不变）")
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:   # LF 铁律
        fh.write(want)
    print(f"SHA256SUMS 写出：{len(lines)} 行（LF）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
