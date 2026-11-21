# -*- coding: utf-8 -*-
"""元和经纬 Lint——确定性检查（继承四站会战禁止清单）
   python tools/lint.py  →  0 = 全过 / 1 = 有违规"""
import glob
import io
import json
import os
import re
import subprocess
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
fails = []


def check(ok, msg):
    if ok:
        print(f"  ✓ {msg}")
    else:
        fails.append(msg)
        print(f"  ✗ {msg}")


print("═══ 元和经纬 Lint · 禁止清单→确定性 ═══")

# ── 1. 版本一致性（?v= 全站同号，glob 不用手列清单）──
print("── 1. 版本一致性")
idx = open("index.html", encoding="utf-8").read()
sw = open("sw.js", encoding="utf-8").read()
m = re.search(r"\?v=(\w+)", idx)
idx_v = m.group(1) if m else "?"
m2 = re.search(r'VERSION = "v(\w+)"', sw)
sw_v = m2.group(1) if m2 else "?"
check(idx_v == sw_v, f"index ?v={idx_v} == sw VERSION v{sw_v}")
all_v = set(re.findall(r"\?v=(\w+)", idx))
check(len(all_v) <= 1, f"index.html 版本唯一（实得 {all_v}）")
for f in ["tests/*.html"]:
    for g in glob.glob(f):
        c = open(g, encoding="utf-8").read()
        bad = set(re.findall(r"\?v=(\w+)", c)) - {idx_v}
        check(not bad, f"{g} 版本对齐（杂散 {bad if bad else '无'}）")

# ── 2. 目录结构 ──
print("── 2. 目录结构")
check(not glob.glob("test_*.html"), "根目录无残留测试页")
for d in ["js", "css", "data", "tools", "tests", "vendor", "data/text"]:
    check(os.path.isdir(d), f"{d}/ 目录存在")
check(os.path.exists("js/ftworker.js"), "Worker 在 js/")

# ── 3. 数据完整性 ──
print("── 3. 数据完整性")
raw = open("data/site_data.js", encoding="utf-8").read()
sd = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
n_states = sum(len(d["states"]) for d in sd["daos"])
n_coord = sum(1 for d in sd["daos"] for s in d["states"] if s.get("c"))
n_xian = sum(len(s.get("xian") or []) for d in sd["daos"] for s in d["states"])
check(len(sd["daos"]) == 10, f"十道齐全（实得 {len(sd['daos'])}）")
check(n_states >= 90, f"州条目 ≥90（实得 {n_states}）")
check(n_coord == n_states, f"州治坐标全覆盖（{n_coord}/{n_states}）")
check(n_xian >= 400, f"县名录 ≥400（实得 {n_xian}）")
no_zhen = [s["n"] for d in sd["daos"] for s in d["states"] if not s.get("zhen")]
check(not no_zhen, f"州皆有镇属（缺 {no_zhen[:5] if no_zhen else '无'}）")
check("缺卷" in json.dumps(sd["meta"], ensure_ascii=False), "meta 含缺卷注记")
stats = json.load(open("data/stats.json", encoding="utf-8"))
check(stats["states"] == n_states, f"stats.json 州数与 site_data 一致（{stats['states']}=={n_states}）")
check(stats["counties_listed"] == n_xian, f"stats.json 县数一致（{stats['counties_listed']}=={n_xian}）")

# ── 4. 坐标域（中国境内）──
print("── 4. 坐标域")
bad_coord = [s["n"] for d in sd["daos"] for s in d["states"]
             if s.get("c") and not (18 < s["c"][0] < 46 and 88 < s["c"][1] < 136)]
check(not bad_coord, f"坐标皆在中国域内（违 {bad_coord[:5] if bad_coord else '无'}）")

# ── 5. 全文分片 ──
print("── 5. 全文分片")
shards = glob.glob("data/text/*.js")
check(len(shards) >= 8, f"全文分片 ≥8（实得 {len(shards)}）")
check(os.path.exists("data/text/juanshou.js"), "卷首分片存在")
frag = open(shards[0], encoding="utf-8").read() if shards else ""
check("YHTEXT" in frag, "分片写入 YHTEXT 全局")

# ── 6. 闭包安全（let 闭包量不经 window 赋值；__NOTILES__ 测试旗读取豁免）──
print("── 6. 闭包安全")
wlet = []
for f in glob.glob("js/*.js"):
    c = open(f, encoding="utf-8").read()
    wlet += [f"{f}:{mm}" for mm in re.findall(r"window\.(_\w+)\s*=[^=]", c)]
check(not wlet, f"无 window._闭包量赋值（违 {wlet[:3] if wlet else '无'}）")

# ── 7. SW 缓存清单 ──
print("── 7. SW 覆盖")
shell_files = re.findall(r'"(\./[^"]+)"', sw)
check(len(shell_files) >= 18, f"SW SHELL ≥18 文件（实得 {len(shell_files)}）")

# ── 8. JS 语法 ──
print("── 8. JS 语法")
bad_js = []
for f in sorted(glob.glob("js/*.js")):
    r2 = subprocess.run(["node", "--check", f], capture_output=True, timeout=20)
    if r2.returncode:
        bad_js.append(f)
check(not bad_js, f"js/*.js 语法（坏 {bad_js}）")

# ── 9. 危险 API 禁用 ──
print("── 9. 危险 API")
DANGEROUS = [
    (r'map\.fire\("click"', "map.fire 委托分发不可靠"),
    (r'innerHTML\.indexOf\("mode=', "innerHTML.indexOf 验证（& 序列化）"),
    (r'git mv -q', "git mv -q 不存在"),
]
for pat, msg in DANGEROUS:
    hits = []
    for f in glob.glob("js/*.js") + glob.glob("tests/*.html") + glob.glob("tools/*.py"):
        if "lint.py" in f:
            continue
        c = open(f, encoding="utf-8").read()
        if re.search(pat, c):
            hits.append(f)
    check(not hits, f"API 禁用：{msg}（违 {hits[:3] if hits else '无'}）")

# ── 10. Worker 无 DOM ──
print("── 10. 架构约束")
w = open("js/ftworker.js", encoding="utf-8").read()
dom_refs = re.findall(r"(?:document|window)\.", w)
check(len(dom_refs) == 0, f"Worker 不引用 DOM（实得 {len(dom_refs)} 处）")

# 脚本 defer 顺序
scripts = re.findall(r'<script src="js/(\w+)\.js', idx)
expected_order = ["config", "map", "panels", "rail", "search", "reader",
                  "ft_core", "fulltext", "app", "modes"]
actual_order = [s for s in scripts if s in expected_order]
check(actual_order == expected_order[:len(actual_order)],
      f"脚本 defer 顺序符合依赖链（{actual_order}）")

# ── 11. 吞错禁用（or True / || true / || exit 0）──
print("── 11. 吞错禁用")
PY_OT = re.compile(r"\bor\s+True\b")
SW1 = "||" + " true"
SW2 = "||" + " exit 0"
py_swallow = []
for f in sorted(glob.glob("tools/*.py")) + ["run_tests.py", "build_data.py"]:
    if not os.path.exists(f):
        continue
    for i, line in enumerate(open(f, encoding="utf-8"), 1):
        code = line.split("#")[0]
        if PY_OT.search(code) or SW1 in code or SW2 in code:
            py_swallow.append(f"{f}:{i}")
check(not py_swallow, f"py 工具无恒真吞错兜底（违 {py_swallow[:3] if py_swallow else '无'}）")

# ── 12. subprocess 显式编码 ──
print("── 12. subprocess 编码")
bare_sub = []
for f in ["run_tests.py"] + sorted(glob.glob("tools/*.py")):
    for i, line in enumerate(open(f, encoding="utf-8"), 1):
        if "text=True" in line and "encoding" not in line:
            bare_sub.append(f"{f}:{i}")
check(not bare_sub, f"text=True 同行须显式 encoding（违 {bare_sub}）")

# ── 13. Python 工具可编译 ──
print("── 13. 工具编译")
import py_compile
import tempfile as _tf
broken_py = []
for f in sorted(glob.glob("tools/*.py")) + ["run_tests.py"]:
    try:
        py_compile.compile(f, doraise=True,
                           cfile=os.path.join(_tf.gettempdir(), "yh_lint.pyc"))
    except Exception as e:
        broken_py.append(f"{f}: {str(e)[:60]}")
check(not broken_py, f"工具脚本可编译（实得 {broken_py}）")

# ── 14. 互查桥数据完整性（TPHY 只读产物） ──
print("── 14. 互查桥")
xref_path = "data/xref_hy.js"
check(os.path.exists(xref_path), "data/xref_hy.js 存在（python tools/build_xref_hy.py）")
if os.path.exists(xref_path):
    xraw = open(xref_path, encoding="utf-8").read()
    xref = json.loads(xraw[xraw.find("{"): xraw.rfind("}") + 1])
    xm = xref["meta"]
    n_rows = len(xref["rows"])
    check(xm["tang_states"] == n_states and n_rows == n_states,
          f"桥行数 == 州数（{n_rows}=={n_states}）")
    n_m = sum(1 for r in xref["rows"] if r["m"])
    check(xm["matched"] == n_m and xm["matched"] + xm["unmatched"] == n_rows,
          f"桥计数自洽（得对应 {xm['matched']} + 无对应 {xm['unmatched']} == {n_rows}）")
    tphy_write = [ln for ln in open("tools/build_xref_hy.py", encoding="utf-8").read().splitlines()
                  if 'TPHY' in ln and ('"w"' in ln or "'w'" in ln or '"a"' in ln or "'a'" in ln)]
    check(not tphy_write, f"build_xref_hy.py 不写 TPHY（违 {tphy_write[:1] if tphy_write else '无'}）")

# ── 15. 论文 PDF 同步哨兵（ANALYSIS.md 改动必须重排 PDF） ──
print("── 15. 论文 PDF 哨兵")
pdf_path = "docs/元和经纬-数字人文.pdf"
md_path = "docs/ANALYSIS.md"
check(os.path.exists(pdf_path), "docs/元和经纬-数字人文.pdf 存在（python tools/build_paper_pdf.py）")
if os.path.exists(pdf_path) and os.path.exists(md_path):
    mt, pt = os.path.getmtime(md_path), os.path.getmtime(pdf_path)
    if mt > pt + 60:
        import time
        check(False, f"ANALYSIS.md（{time.strftime('%m-%d %H:%M', time.localtime(mt))}）"
                     f"新于 PDF（{time.strftime('%m-%d %H:%M', time.localtime(pt))}）——请重跑 tools/build_paper_pdf.py")
    else:
        check(True, "ANALYSIS.md ↔ 论文 PDF 同步")

print()
if fails:
    for f_ in fails:
        print(f"✗ {f_}")
    print(f"Lint：{len(fails)} 项违规")
    sys.exit(1)
print("Lint：全过 ✓")
