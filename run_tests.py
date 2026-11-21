# -*- coding: utf-8 -*-
"""元和经纬 · 一键回归：python run_tests.py
  1) lint（确定性禁止清单）
  2) 数据断言（≥10 项，Python 侧直查产物）
  3) 无头浏览器断言页（TESTLOG 协议）
  退出码 0=全绿 / 1=有失败。本地服务：python -m http.server 9600"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

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


def A(name, ok, detail=""):
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

PAGES = ["tests/test_auto.html", "tests/test_ft.html"]
for page in PAGES:
    prof = tempfile.mkdtemp(prefix="yhtest_")
    r = subprocess.run(
        [EDGE, "--headless=new", "--disable-gpu", "--no-first-run",
         "--user-data-dir=" + prof, "--virtual-time-budget=18000",
         "--dump-dom", BASE + page],
        capture_output=True, timeout=240)
    html = r.stdout.decode("utf-8", errors="replace")
    m = re.search(r'id="testlog"[^>]*>([^<]*)<', html)
    if not m or "TESTLOG" not in (m.group(1) or ""):
        fails.append((page, ["脚本未产出 TESTLOG"]))
        print(f"✗ {page} 无日志产出")
        continue
    lines = [l.strip() for l in m.group(1).splitlines()
             if l.strip() and l.strip() not in ("TESTLOG", "ENDLOG")]
    bad = [l for l in lines if "FAIL" in l]
    print(("✓" if not bad else "✗") + f" {page} {len(lines)} 项断言")
    for l in bad:
        fails.append((page, [l]))
        print("    FAIL  " + l)

print()
if fails:
    print(f"回归未过：{sum(len(f[1]) for f in fails)} 个失败项")
    sys.exit(1)
print(f"回归通过：lint + 15 数据断言 + {len(PAGES)} 断言页全绿")
