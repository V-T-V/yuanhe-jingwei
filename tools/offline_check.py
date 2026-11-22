# -*- coding: utf-8 -*-
"""元和经纬 · 离线验证：python tools/offline_check.py

「首访后经 Service Worker 离线可用」三验（承旗舰方舆经纬 tools/offline_check.py 范式；
CDP over websocket 以 stdlib 自实现，零第三方依赖，本地 / CI 同口径）：
  ① SW 在位且接管：轮询 navigator.serviceWorker.controller 非空（install→activate→claim 实证）；
  ② 断网重载首屏：Network.emulateNetworkConditions 离线 → Page.reload——舆图容器 ·
     十道纲目 · 底栏账字 · 双样式表 · 数据全局量到位，并驱动纲目首条 → 面板开；
  ③ 数据层离线可得：断网态 fetch data/ 产物 200 且命中 SW CacheStorage（SHELL 预存）；
     全文分片懒存——仅暖存并验首片（data/text/j01.js；全书 40 片不要求全缓，范围如实注明）。
任一验失败即非零退出。证据截图落 docs/evidence/offline-index.png。
前置：python -m http.server 9600（YH_BASE 可覆盖）；本地需 Edge/Chrome（YH_BROWSER 可指定）。
"""
import base64
import io
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request as ur

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get("YH_BASE", "http://127.0.0.1:9600/")
PORT = int(os.environ.get("YH_CDP", "9361"))

CANDS = [
    os.environ.get("YH_BROWSER", ""),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
]
BROWSER = next((c for c in CANDS if c and os.path.exists(c)), None)

V = "5"                                     # 与 sw.js VERSION 同步（lint 校验）；本站 data 产物引用不带 ?v
CORE_DATA = ["data/site_data.js", "data/xref_hy.js"]
FIRST_SHARD = "data/text/guannei.js"        # 全书 10 片懒存（关内/河南/…按道分片），本验范围=首片
READ_DATA = None                             # 面板驱动（openDao）不触懒载——道卡数据随 site_data 预存
WARM_URLS = [u for u in (FIRST_SHARD, READ_DATA) if u]
SHARD_NOTE = ("data/text 共 10 片懒存（按道分片，首开后离线）；本验范围=首片 guannei 暖存后断网重取，不求全缓")
RAIL_SEL = "#raillist .ri-dao"              # 十道纲目行（道晕开关之外十条道）
RAIL_MIN = 10
GLOBAL = "YH"                               # 数据层全局量（site_data.js 顶层 var）


class CDP:
    """极简 CDP 客户端：/json 建页 + RFC6455 文本帧（stdlib 自实现，零依赖）。"""

    def __init__(self, ws_url):
        u = urllib.parse.urlsplit(ws_url)
        self.sock = socket.create_connection((u.hostname, u.port), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET {u.path}{'?' + u.query if u.query else ''} HTTP/1.1\r\n"
            f"Host: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("CDP 握手失败")
            buf += chunk
        head, _, rest = buf.partition(b"\r\n\r\n")
        if " 101 " not in head.decode("latin-1").split("\r\n")[0]:
            raise ConnectionError("CDP 握手非 101")
        self.buf = rest
        self._id = 0

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("CDP 连接断开")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _frame(self, op, payload=b""):
        m = os.urandom(4)
        h = bytes([0x80 | op])
        n = len(payload)
        if n < 126:
            h += bytes([0x80 | n])
        elif n < 65536:
            h += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            h += bytes([0x80 | 127]) + struct.pack(">Q", n)
        self.sock.sendall(h + m + bytes(b ^ m[i % 4] for i, b in enumerate(payload)))

    def recv(self):
        frags = []
        while True:
            b1, b2 = self._read(2)
            fin, op = b1 >> 7, b1 & 0xF
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read(8))[0]
            pl = self._read(ln)
            if op == 9:                       # ping → pong
                self._frame(10, pl)
                continue
            if op == 8:
                raise ConnectionError("CDP 关闭帧")
            frags.append(pl)
            if fin:
                return b"".join(frags).decode("utf-8", "replace")

    def cmd(self, method, params=None):
        self._id += 1
        self._frame(1, json.dumps(
            {"id": self._id, "method": method, "params": params or {}}).encode())
        while True:
            r = json.loads(self.recv())
            if r.get("id") == self._id:
                if "error" in r:
                    raise RuntimeError(f"CDP {method}: {r['error']}")
                return r.get("result", {})

    def ev(self, expr, await_promise=False):
        r = self.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                          "awaitPromise": await_promise})
        return r.get("result", {}).get("value")

    def evx(self, expr, await_promise=False):
        """严格求值：表达式抛错时返回 {'__exc': 描述}，不与正常值混淆。"""
        r = self.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                          "awaitPromise": await_promise})
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            return {"__exc": (d.get("exception", {}).get("description")
                              or d.get("text") or "")[:160]}
        return r.get("result", {}).get("value")


def reap(proc, port):
    """收尸（承旗舰教训 9）：terminate 只杀主进程，须平台级清无头残留，防尸体吃 CPU 假超时。"""
    if proc is not None:
        try:
            proc.terminate()
        except OSError:
            pass
    if sys.platform == "win32":
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | "
                        "Where-Object {$_.CommandLine -like '*headless*'} | "
                        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"],
                       capture_output=True, timeout=30)
    else:
        subprocess.run(["pkill", "-f", "remote-debugging-port=%d" % port],
                       capture_output=True, timeout=15)


def ready(c):
    """真页就绪：complete + 舆图容器 + 纲目行到位。"""
    return c.ev("document.readyState==='complete'"
                " && !!(document.getElementById('map')||{}).classList"
                " && document.getElementById('map').classList.contains('leaflet-container')"
                f" && document.querySelectorAll('{RAIL_SEL}').length>0")


def main():
    if not BROWSER:
        print("✗ 未找到浏览器（YH_BROWSER 可指定）")
        sys.exit(2)
    prof = tempfile.mkdtemp(prefix="yhoff_")
    proc = subprocess.Popen(
        [BROWSER, "--headless=new", "--disable-gpu", "--no-first-run",
         f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    steps = {}
    sws = []                      # SW 目标会话（断网须连它——页面会话的仿真管不到 SW 自身 fetch）

    def mark(name, ok, detail=""):
        steps[name] = {"ok": bool(ok), **({"detail": detail} if detail else {})}
        print(f"  {'✓' if ok else '✗'} {name}" + (f"  {detail}" if detail else ""))

    t0 = time.time()
    try:
        base = f"http://127.0.0.1:{PORT}"
        for _ in range(150):
            try:
                ur.urlopen(base + "/json/version", timeout=1).read()
                break
            except Exception:
                time.sleep(.2)
        else:
            print("✗ CDP 30s 未就绪")
            sys.exit(2)
        req = ur.Request(base + "/json/new?" + urllib.parse.quote(BASE + "index.html", safe=""),
                         method="PUT")
        tab = json.loads(ur.urlopen(req, timeout=5).read())
        c = CDP(tab["webSocketDebuggerUrl"])
        c.cmd("Page.enable")
        c.cmd("Runtime.enable")
        c.cmd("Network.enable")

        # ① SW 在位且接管（真信号轮询，不 sleep 猜）
        controlled = False
        for _ in range(60):
            if c.ev("document.readyState==='complete'"
                    " && !!navigator.serviceWorker.controller") and ready(c):
                controlled = True
                break
            time.sleep(.5)
        regs = c.ev("navigator.serviceWorker.getRegistrations().then(a=>a.length)",
                    await_promise=True)
        if not controlled:
            why = "sw.js 从未注册——页面无 registration" if not regs else "注册未接管（controller 空）"
            mark("①sw-controlled", False, f"registrations={regs}；{why}")
            print(json.dumps({"ok": False, "secs": round(time.time() - t0, 1),
                              "steps": steps}, ensure_ascii=False, indent=1))
            sys.exit(1)
        mark("①sw-controlled", True, f"registrations={regs}")

        # 暖存懒载资源（在线态经 SW 拦截入 TEXTS；body 须读尽——tee 未消费会压住缓存写入）
        warm = c.evx(
            "(async()=>{const out={};for(const u of " + json.dumps(WARM_URLS) + "){"
            "const r=await fetch(u);await r.text();"
            "for(let i=0;i<40 && !(await caches.match(u));i++)"
            "await new Promise(s=>setTimeout(s,500));"
            "out[u]={status:r.status,cache:!!(await caches.match(u))};}return out;})()",
            await_promise=True) or {}
        warm_ok = (not warm.get("__exc") and len(warm) == len(WARM_URLS)
                   and all(v.get("status") == 200 and v.get("cache")
                           for k, v in warm.items() if k != "__exc"))
        mark("warm-lazy-data", warm_ok,
             "；".join(f"{k.split('/')[-1]}={v.get('status')}/{'+缓存' if v.get('cache') else '未缓存'}"
                       for k, v in warm.items() if k != "__exc")
             + (f"；{warm.get('__exc')}" if "__exc" in warm else ""))

        # ② 断网重载（关键：SW 自身的 fetch 不受页面会话仿真约束——须同源 service_worker
        #    目标逐一挂上离线，否则网络优先型 SW 仍偷偷连本地服务，断网即成假象）
        origin = urllib.parse.urlsplit(BASE)._replace(path="", query="", fragment="").geturl()
        for t in json.loads(ur.urlopen(base + "/json", timeout=5).read()):
            if t.get("type") == "service_worker" and t.get("url", "").startswith(origin):
                try:
                    s = CDP(t["webSocketDebuggerUrl"])
                    s.cmd("Network.enable")
                    sws.append(s)
                except Exception:
                    pass
        offs = [c] + sws
        netoff = all(s.cmd("Network.emulateNetworkConditions",
                           {"offline": True, "latency": 0,
                            "downloadThroughput": 0, "uploadThroughput": 0}) == {}
                     for s in offs)
        mark("②network-off", netoff, f"页面 + {len(sws)} 个 SW 目标")
        c.cmd("Page.reload", {"ignoreCache": False})
        reloaded = False
        for _ in range(60):
            if ready(c):
                reloaded = True
                break
            time.sleep(.5)
        mark("②offline-reload", reloaded)

        c.ev("document.querySelector('#boot .go') && document.querySelector('#boot .go').click()")
        time.sleep(1.2)
        n_rail = c.ev(f"document.querySelectorAll('{RAIL_SEL}').length")
        mark("②rail-dom", bool(n_rail and n_rail >= RAIL_MIN),
             f"{RAIL_SEL} = {n_rail}（下界 {RAIL_MIN}）")
        css = c.ev("document.styleSheets.length")
        mark("②css-2sheets", css == 2, f"styleSheets={css}（leaflet+main；缺一=离线样式断供）")
        mark("②data-global", bool(c.ev(f"typeof {GLOBAL}!=='undefined'")),
             f"typeof {GLOBAL} !== 'undefined'")
        stat = (c.ev("(document.getElementById('bookstat')||{}).textContent || ''") or "").strip()
        mark("②fbar-stat", bool(stat), stat[:24])
        c.ev(f"document.querySelector('{RAIL_SEL}') && document.querySelector('{RAIL_SEL}').click()")
        time.sleep(1.5)
        popen = c.ev("document.getElementById('panel').classList.contains('open')")
        vname = (c.ev("(document.getElementById('vname')||{}).textContent || ''") or "").strip()
        mark("②panel-open", bool(popen) and bool(vname), vname[:14])

        # ③ 数据层离线可得（断网态 cache:'reload' 直取——200 只可能来自 SW 缓存，且命中 CacheStorage）
        urls = list(dict.fromkeys(CORE_DATA + WARM_URLS))   # 去重保序（核心表与暖存表可重叠）
        res = c.evx(
            "(async()=>{const out={};for(const u of " + json.dumps(urls) + "){"
            "try{const r=await fetch(u,{cache:'reload'});"
            "out[u]={status:r.status,cache:!!(await caches.match(u))}}"
            "catch(e){out[u]={status:0,cache:false}}}return out;})()",
            await_promise=True) or {}
        bad = [u for u, v in res.items()
               if v.get("status") != 200 or not v.get("cache")]
        mark("③data-offline", len(res) == len(urls) and not bad,
             f"{len(res)}/{len(urls)} 断网 200 且 SW 缓存命中"
             + (f"；失：{bad}" if bad else "")
             + (f"；{res.get('__exc')}" if "__exc" in res else ""))
        mark("③shard-scope", True, SHARD_NOTE)

        shot = c.cmd("Page.captureScreenshot", {"format": "png"})
        os.makedirs(os.path.join(ROOT, "docs", "evidence"), exist_ok=True)
        png = os.path.join(ROOT, "docs", "evidence", "offline-index.png")
        with open(png, "wb") as f:
            f.write(base64.b64decode(shot["data"]))

        ok = all(s["ok"] for s in steps.values())
        print(json.dumps({"ok": ok, "secs": round(time.time() - t0, 1),
                          "steps": steps, "evidence": png}, ensure_ascii=False, indent=1))
        sys.exit(0 if ok else 1)
    finally:
        for s in sws:
            try:
                s.sock.close()
            except OSError:
                pass
        reap(proc, PORT)


if __name__ == "__main__":
    main()
