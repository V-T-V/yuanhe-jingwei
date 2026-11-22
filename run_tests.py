# -*- coding: utf-8 -*-
"""元和经纬 · 一键回归：python run_tests.py
  1) lint（确定性禁止清单）
  2) 数据断言（≥10 项，Python 侧直查产物）
  3) 无头浏览器断言页（TESTLOG 协议）
  退出码 0=全绿 / 1=有失败。本地服务：python -m http.server 9600"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
BASE = os.environ.get("YH_BASE", "http://127.0.0.1:9600/")

fails = []

# ── 1. Lint ──
rl = subprocess.run([sys.executable, "tools/lint.py"], capture_output=True,
                    text=True, encoding="utf-8", errors="replace", timeout=180)
lint_ok = "全过" in rl.stdout
print(rl.stdout.strip().splitlines()[-1] if rl.stdout.strip() else "✗ lint 无输出")
if not lint_ok:
    for b in [l for l in rl.stdout.splitlines() if l.startswith("✗")][:8]:
        print("    " + b)
    fails.append(("lint", ["见上"]))

# ── 2. 数据断言（数字皆出自脚本产物）──
print("── 数据断言")
raw = open("data/site_data.js", encoding="utf-8").read()
sd = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
stats = json.load(open("data/stats.json", encoding="utf-8"))
fetch = json.load(open("data/fetch_report.json", encoding="utf-8"))


A_COUNT = 0


def A(name, ok, detail=""):
    global A_COUNT
    A_COUNT += 1
    mark = "✓" if ok else "✗"
    print(f"  {mark} {name} {detail}")
    if not ok:
        fails.append((name, [detail or "断言失败"]))


states = [s for d in sd["daos"] for s in d["states"]]
n_coord = sum(1 for s in states if s.get("c"))
n_conf1 = sum(1 for s in states if s.get("conf") == 1)
n_xian = sum(len(s.get("xian") or []) for s in states)
n_lost = sum(len(d.get("lost") or []) for d in sd["daos"])
zhens = {s["zhen"] for s in states if s.get("zhen")}

A("A1 十道定义齐全", len(sd["daos"]) == 10, f"{len(sd['daos'])}道")
A("A2 州条目 ≥90", len(states) >= 90, f"{len(states)}州")
A("A3 州治坐标全覆盖", n_coord == len(states), f"{n_coord}/{len(states)}")
A("A4 高置信坐标过半", n_conf1 >= len(states) * 0.5, f"确 {n_conf1}")
A("A5 县名录 ≥400", n_xian >= 400, f"{n_xian}县")
A("A6 卷佚州份 ≥25", n_lost >= 25, f"{n_lost}州份")
A("A7 文本所及镇 ≥30", len(zhens) >= 30, f"{len(zhens)}镇")
A("A8 淮南道标注整道佚", any(d["id"] == "huainan" and len(d.get("lost") or []) >= 5
                            for d in sd["daos"]), "申光蕲黄安移隶已注")
A("A9 meta 缺卷注记", "十九" in sd["meta"]["missing_juan"], sd["meta"]["missing_juan"][:30])
A("A10 stats 与 site_data 同源", stats["states"] == len(states)
  and stats["counties_listed"] == n_xian, f"{stats['states']}州/{stats['counties_listed']}县")
A("A11 抓取语料 ≥15万字", fetch["total_chars"] >= 150000, f"{fetch['total_chars']}字")
A("A12 全文分片 ≥8 且含卷首",
  len([f for f in os.listdir("data/text") if f.endswith(".js")]) >= 8
  and os.path.exists("data/text/juanshou.js"))
A("A13 京兆府条存在且有附郭", any(s["n"] == "京兆府" and s.get("fg") for s in states))
A("A14 八到标签存而文佚如实记",
  any(s.get("badao") for s in states) and any(not s.get("badao") for s in states),
  "标签有/无两态皆见")
A("A15 道晕配色十道齐色", all(d.get("color") for d in sd["daos"]))

# ── P2：互查桥 + 导出 + 论文 ──
xraw = open("data/xref_hy.js", encoding="utf-8").read()
xref = json.loads(xraw[xraw.find("{"): xraw.rfind("}") + 1])
xm = xref["meta"]
A("A16 唐宋互查桥自洽", xm["tang_states"] == len(states)
  and xm["matched"] + xm["unmatched"] == xm["tang_states"]
  and xm["matched"] >= 150 and xm["same_name"] + xm["renamed"] == xm["matched"],
  f"同名 {xm['same_name']} · 异名 {xm['renamed']} · 无对应 {xm['unmatched']}（存疑 {xm['unmatched_doubt']}）· 异隶 {xm['yili']}")
zc = open("docs/export/元和经纬-州治对照.csv", "rb").read()
xc = open("docs/export/元和经纬-县名录.csv", "rb").read()
gj = json.load(open("docs/export/元和经纬-州治点位.geojson", encoding="utf-8"))
km = open("docs/export/元和经纬-州治点位.kml", encoding="utf-8").read()
n_zc = len(zc.decode("utf-8-sig").strip().splitlines()) - 1
n_xc = len(xc.decode("utf-8-sig").strip().splitlines()) - 1
A("A17 导出三格式同口径（CSV 带 BOM）",
  zc[:3] == b"\xef\xbb\xbf" and xc[:3] == b"\xef\xbb\xbf"
  and n_zc == stats["states"] and n_xc == stats["counties_listed"]
  and len(gj["features"]) == stats["states"]
  and km.count("<Placemark>") == stats["states"],
  f"州 {n_zc} 行 · 县 {n_xc} 行 · 点位 {len(gj['features'])}")
A("A18 论文 PDF 在位", os.path.exists("docs/元和经纬-数字人文.pdf")
  and os.path.getsize("docs/元和经纬-数字人文.pdf") > 50000, "元和经纬-数字人文.pdf")

# ── 2b. 账目对账（SHA256SUMS 指纹账本；行尾无关口径，过期即红）──
print("── 账目对账（SHA256SUMS）")
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("build_sums", "tools/build_sums.py")
_bs = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_bs)
_want = _bs.collect()
_has_sums = os.path.exists("SHA256SUMS")
A("A19 账本在库且纯 LF", _has_sums
  and open("SHA256SUMS", "rb").read().count(b"\r") == 0,
  f"{len(open('SHA256SUMS', encoding='utf-8').read().splitlines()) if _has_sums else 0} 行"
  if _has_sums else "缺失——先 python tools/build_sums.py")
_lines = open("SHA256SUMS", encoding="utf-8").read().splitlines() if _has_sums else []
_problems, _seen = [], set()
for _i, _line in enumerate(_lines, 1):
    _parts = _line.split("  ", 1)
    _rel = _parts[1].strip().replace("\\", "/") if len(_parts) == 2 else ""
    if len(_parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", _parts[0]) or not _rel:
        _problems.append(f"第{_i}行格式非法"); continue
    if _rel in _seen:
        _problems.append(f"第{_i}行重复 {_rel}"); continue
    _seen.add(_rel)
    if not os.path.isfile(_rel):
        _problems.append(f"账上文件缺失 {_rel}"); continue
    if _bs.sha256(_rel) != _parts[0]:
        _problems.append(f"指纹不符 {_rel}")
A("A20 逐行指纹与磁盘实测一致", not _problems,
  f"失真 {len(_problems)}：{_problems[:2]}——重跑 python tools/build_sums.py" if _problems
  else f"{len(_lines)} 行全符")
A("A21 行数与生成器一致且产物无缺账",
  len(_lines) == len(_want) and not [r for r in _want if r not in _seen],
  f"账 {len(_lines)} 行 / 生成器 {len(_want)} 行"
  + ("" if len(_lines) == len(_want) else "——重跑 python tools/build_sums.py"))

# ── 2c. 3D 沿革文柱（yt 字段 + 阈值，map3d.js 常量与数据互证）──
m3 = open("js/map3d.js", encoding="utf-8").read()
mm = re.search(r"YT_MIN = (\d+)", m3)
yt_min = int(mm.group(1)) if mm else -1
yts = [s.get("yt") or 0 for d in sd["daos"] for s in d["states"]]
n_pillar = sum(1 for v in yts if v >= yt_min)
A("A22 沿革文柱自洽（yt 阈值与 map3d 同源）",
  yt_min == 1200 and all(isinstance(v, int) and v >= 0 for v in yts)
  and 45 <= n_pillar <= 70 and max(yts) == 10162,
  f"入柱 {n_pillar} 州 · 中位 {sorted(yts)[len(yts) // 2]} 字 · 最大 {max(yts)}（成都府）")

# ── 3. 本地服务健康检查 ──
try:
    urllib.request.urlopen(BASE + "index.html", timeout=3).read()
except Exception as e:
    print(f"✗ 本地服务不可达：{BASE} —— 请先 python -m http.server 9600")
    sys.exit(1)

# ── 4. 无头断言页 ──
CANDS = [
    os.environ.get("YH_BROWSER", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
EDGE = next((c for c in CANDS if c and os.path.exists(c)), None)
if not EDGE:
    print("✗ 未找到浏览器（可用环境变量 YH_BROWSER 指定）")
    sys.exit(1)

PAGES = ["tests/test_auto.html", "tests/test_ft.html", "tests/test_3d.html"]
# 「无日志」= 页面在虚时预算内没跑完（Worker 冷启动竞态，ubuntu Chrome 上偶发）——
# 有界重试+加预算；一旦产出 TESTLOG 且含 FAIL 仍即红，重试只治「没跑」，不吞断言失败
BUDGETS = [18000, 30000, 45000]
for page in PAGES:
    lines = None
    for attempt, budget in enumerate(BUDGETS, 1):
        prof = tempfile.mkdtemp(prefix="yhtest_")
        r = subprocess.run(
            [EDGE, "--headless=new", "--disable-gpu", "--no-first-run",
             "--user-data-dir=" + prof, "--virtual-time-budget=" + str(budget),
             "--dump-dom", BASE + page],
            capture_output=True, timeout=240)
        html = r.stdout.decode("utf-8", errors="replace")
        m = re.search(r'id="testlog"[^>]*>([^<]*)<', html)
        if m and "TESTLOG" in (m.group(1) or ""):
            lines = [l.strip() for l in m.group(1).splitlines()
                     if l.strip() and l.strip() not in ("TESTLOG", "ENDLOG")]
            if attempt > 1:
                print(f"  （第 {attempt} 次跑出日志，预算 {budget}）")
            break
    if lines is None:
        fails.append((page, ["脚本未产出 TESTLOG"]))
        print(f"✗ {page} 无日志产出（{len(BUDGETS)} 次重试后仍无）")
        continue
    bad = [l for l in lines if "FAIL" in l]
    print(("✓" if not bad else "✗") + f" {page} {len(lines)} 项断言")
    for l in bad:
        fails.append((page, [l]))
        print("    FAIL  " + l)

# ── 5. 离线三验（SW 在位 · 断网重载 · 数据层离线可得；audit.yml 亦专步硬跑）──
ro = subprocess.run([sys.executable, "tools/offline_check.py"],
                    capture_output=True, text=True, encoding="utf-8", timeout=300)
print("── 离线三验")
print(ro.stdout.strip())
if ro.returncode != 0:
    fails.append(("offline_check", ["exit %d" % ro.returncode]))

print()
if fails:
    print(f"回归未过：{sum(len(f[1]) for f in fails)} 个失败项")
    sys.exit(1)
print("回归通过：lint + 数据断言（A1–A%d）+ %d 断言页 + 离线三验全绿" % (A_COUNT, len(PAGES)))
