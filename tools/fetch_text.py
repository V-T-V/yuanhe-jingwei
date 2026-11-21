# -*- coding: utf-8 -*-
"""元和经纬 · 文本抓取（识典古籍 · 四库全书本《元和郡县志》SK0967）

数据源: https://www.shidianguji.com/book/SK0967 （字节跳动识典古籍，SSR 直出）
选源说明: 本环境无法直连维基文库（TLS 阻断）与 ctext（403）；国学导航未收此书。
         识典古籍为四库全书本整理，页面服务端渲染，结构干净。
编码教训: 响应偶发以错误 charset 解释（UTF-8 页被当 GBK 解出「鍘?鏈」乱码）——
         一律 r.content 显式 UTF-8 解码 + 正文标记校验，坏则重抓。
反爬教训: 连抓 ~74 页后偶返回 JS 挑战页（无 <article>）——指数退避重试即恢复。
输出:   data_raw/sdgj/NNN.html  原始页面（不进 git）
        data/vol/NNN.txt       每章纯净 UTF-8 文本（标题行 + 段落）
        data/fetch_report.json 抓取盘点
用法:   python tools/fetch_text.py          # 断点续抓（已存且校验通过跳过）
        python tools/fetch_text.py --force # 全部重抓
"""
import json
import os
import re
import sys
import time

import requests

BASE = "https://www.shidianguji.com"
START = "/book/SK0967/chapter/1jzvm9hx6x1ju"   # 提要（第一章）
HEADERS = {
    "User-Agent": "YHJZ-DH-site-builder/0.1 (digital humanities research; "
                  "static site for Yuanhe Junxian Tuzhi; polite crawl, >=1s/page)",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data_raw", "sdgj")
VOL_DIR = os.path.join(ROOT, "data", "vol")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(VOL_DIR, exist_ok=True)

# 本机注册表残留死代理（127.0.0.1:58319）→ trust_env=False 直连
SESSION = requests.Session()
SESSION.trust_env = False
SESSION.headers.update(HEADERS)

# 乱码特征字：UTF-8 页被按 GBK 解释后的典型产物（正常古籍文本不含）
MOJI_MARK = re.compile(r"[锛鍘鏈鍏鍥鍚]")


def parse_chapter(html: str):
    """SSR 解析：article 内 h2=章题，p=段落；footer 内 下一篇 链接。"""
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.S)
    if not m:
        return None, [], None
    art = m.group(1)
    hs = re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", art, re.S)
    title = ""
    for h in hs[1:]:  # h[0] 是书名「元和郡县志」
        t = re.sub(r"<[^>]+>", "", h).strip()
        if t:
            title = t
            break
    paras = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", art, re.S):
        t = re.sub(r"<[^>]+>", "", p)
        t = t.replace("\u3000", "").replace("\xa0", "").strip()
        if t:
            paras.append(t)
    nm = re.search(r'next-button.*?href="(/book/SK0967/chapter/[^"]+)"[^>]*title="([^"]*)"',
                   html, re.S)
    nxt = nm.group(1) if nm else None
    return title, paras, nxt


def valid_body(paras):
    """正文校验：非空、含足量汉字、无乱码特征字（挑战页/乱码页不过）。"""
    body = "".join(paras)
    cjk = len(re.findall(r"[一-鿿]", body))
    return bool(body) and cjk >= 6 and not MOJI_MARK.search(body)


def repair_mojibake(html):
    """逆解码修复：CDN 偶发把 UTF-8 页按 GBK 解释后再度以 UTF-8 送出。
       特征字（锛/鍘/鏈…）出现时，尝试把正文文本 gbk 回编码再 utf-8 解码。"""
    if not re.search(r"[锛鍘鏈閬鍏鍥鍚]", html):
        return html

    def fix(m):
        t = m.group(1)
        if not re.search(r"[锛鍘鏈閬鍏鍥鍚]", t):
            return m.group(0)
        try:
            fixed = t.encode("gbk", errors="ignore").decode("utf-8", errors="ignore")
            return ">" + fixed + "<"
        except Exception:
            return m.group(0)

    return re.sub(r">([^<>]{20,})<", fix, html)

def fetch_one(path):
    """抓单页，返回 utf-8 正确解码的 html；挑战页/网络错指数退避 + 乱码自愈。
       每次重试新建连接（CDN 偶发把 keep-alive 连接钉在坏节点上）。"""
    last_err = None
    for attempt in range(10):
        try:
            s = requests.Session()
            s.trust_env = False
            s.headers.update(HEADERS)
            r = s.get(BASE + path, timeout=45)
            r.raise_for_status()
            html = r.content.decode("utf-8", errors="replace")
            _, paras, _ = parse_chapter(html)
            if paras and not valid_body(paras):
                fixed = repair_mojibake(html)
                _, paras2, _ = parse_chapter(fixed)
                if paras2 and valid_body(paras2):
                    print("  ↻ 乱码页自愈成功（gbk 逆解码）")
                    return fixed
                raise RuntimeError("正文校验不过（疑似乱码页）")
            if not paras and "<article" not in html:
                raise RuntimeError("挑战页/无正文")
            return html
        except Exception as e:
            last_err = e
            wait = min(8 * (attempt + 1), 60)
            print(f"  退避重试 {path[-16:]}: {e}（等 {wait}s）")
            time.sleep(wait)
    raise RuntimeError(f"{path} 抓取失败（8 次退避后）：{last_err}")


def cached_chain():
    """从已存 raw 页恢复抓取链，避免重复请求。"""
    chain = []
    idx = 0
    while True:
        raw = os.path.join(RAW_DIR, f"{idx:03d}.html")
        if not os.path.exists(raw):
            break
        html = open(raw, encoding="utf-8", errors="replace").read()
        t, p, nxt = parse_chapter(html)
        chain.append({"idx": idx, "html": html, "title": t, "paras": p, "url": None, "next": nxt})
        idx += 1
    return chain


def fetch_all(force=False):
    report = []
    # 1) 恢复缓存链
    cached = [] if force else cached_chain()
    path = None
    for c in cached:
        ok = valid_body(c["paras"])
        if ok:
            report.append({"idx": c["idx"], "title": c["title"], "paras": c["paras"],
                           "url": None, "next": c["next"], "cached": True})
            path = c["next"]
        else:
            # 缓存里第一处坏档之后的链不可信（raw 可能也是坏的）——从坏档起重抓
            path = None
            break
    start_idx = len(report)
    if path is None:
        # 无缓存可续或缓存全坏：从头走
        url_by_idx = {}
        path = START
        start_idx = 0
        report = []
    else:
        url_by_idx = {}
    idx = start_idx
    seen = set()
    while path and path not in seen and idx < 260:
        seen.add(path)
        html = fetch_one(path)
        raw_path = os.path.join(RAW_DIR, f"{idx:03d}.html")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(html)
        title, paras, nxt = parse_chapter(html)
        report.append({"idx": idx, "title": title, "paras": paras,
                       "url": path, "next": nxt, "cached": False})
        body_chars = len(re.sub(r"\s", "", "".join(paras)))
        print(f"[抓取] {idx:03d} {title or '(续页)'}  {body_chars} 字  {path[-14:]}")
        path = nxt
        idx += 1
        time.sleep(1.1)   # 礼貌限速（规程 ≥0.5s，识典加严）

    # 2) 落盘 txt + 报告
    total = 0
    chapters_out = []
    for c in report:
        body = (c["title"] + "\n" if c["title"] else "") + "\n".join(c["paras"])
        with open(os.path.join(VOL_DIR, f"{c['idx']:03d}.txt"), "w", encoding="utf-8") as f:
            f.write(body)
        chars = len(re.sub(r"\s", "", body))
        total += chars
        chapters_out.append({"idx": c["idx"], "title": c["title"], "chars": chars,
                             "url": c["url"] or ""})
    out = {"source": "shidianguji.com/book/SK0967（四库全书本）",
           "chapters": chapters_out, "total_chars": total,
           "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(ROOT, "data", "fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n合计 {len(report)} 章 {total} 字 → data/fetch_report.json")


if __name__ == "__main__":
    fetch_all(force="--force" in sys.argv)
