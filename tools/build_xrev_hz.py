# -*- coding: utf-8 -*-
"""元和经纬 × 汉志经纬 · 汉唐回程桥（v7）
   读 D:\\W_A_W\\HSDZ\\data\\xref_yh.js（第七站汉唐桥产物）+ HSDZ site_data
   （**HSDZ 只读，绝不写入**），从唐州视角反转重组 → data/xrev_hz.js：
     每唐州 → 汉郡对应（四档：同名同城 / 承名〔同城承名·承名同地〕/ 迁治 / 无对应）；
     样例对读（汉志句 × 元和句，采汉志桥已节引的 hq/tq）；
     ↗汉志深链 ../HSDZ/#bu=<部域id>&jun=<郡名>——格式按 HSDZ js/modes.js 实测
     （任务书猜的 #dao= 不符，报备），逐条对 HSDZ site_data 校验存在，对不上即红。
   四朝同地彩蛋（汉→唐→宋→明 跨链卡）：脚本逐站对 HSDZ/本站/TPHY/HHH 四站
   site_data 校验存在，并核宋站与本站唐宋桥（xref_hy.js）匹配一致。
   运行：python tools/build_xrev_hz.py"""
import io
import json
import os
import sys
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HSDZ = os.path.join(os.path.dirname(ROOT), "HSDZ")
TPHY = os.path.join(os.path.dirname(ROOT), "TPHY")
HHH = os.path.join(os.path.dirname(ROOT), "HHH")


def load_js(path):
    raw = open(path, encoding="utf-8").read()
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])


def badge_family(kind):
    if kind == "同名同城":
        return "同名同城"
    if kind == "同名迁治":
        return "迁治"
    return "承名"


# 四朝同地彩蛋（人工挑硬例——汉唐段取自 HSDZ 桥、唐宋段须与本站 xref_hy 匹配一致、
# 明段对 HHH site_data 校验；全链同今地）
ERAS = [
    {"title": "京兆 · 长安", "now": "陕西西安", "stops": [
        {"dyn": "汉", "n": "京兆尹", "site": "汉志经纬", "bu": "sili", "jun": "京兆尹"},
        {"dyn": "唐", "n": "京兆府", "site": "元和经纬（本站）"},
        {"dyn": "宋", "n": "雍州", "site": "寰宇经纬", "sid": "guanxi"},
        {"dyn": "明", "n": "西安府", "site": "方舆经纬", "pid": "shanxix", "fu": "西安府"}]},
    {"title": "河南 · 洛阳", "now": "河南洛阳", "stops": [
        {"dyn": "汉", "n": "河南郡", "site": "汉志经纬", "bu": "sili", "jun": "河南郡"},
        {"dyn": "唐", "n": "河南府", "site": "元和经纬（本站）"},
        {"dyn": "宋", "n": "河南府", "site": "寰宇经纬", "sid": "henan"},
        {"dyn": "明", "n": "河南府", "site": "方舆经纬", "pid": "henan", "fu": "河南府"}]},
    {"title": "蜀 · 成都", "now": "四川成都", "stops": [
        {"dyn": "汉", "n": "蜀郡", "site": "汉志经纬", "bu": "yi", "jun": "蜀郡"},
        {"dyn": "唐", "n": "成都府", "site": "元和经纬（本站）"},
        {"dyn": "宋", "n": "益州", "site": "寰宇经纬", "sid": "jiannanxi"},
        {"dyn": "明", "n": "成都府", "site": "方舆经纬", "pid": "sichuan", "fu": "成都府"}]},
]


def main():
    xh = load_js(os.path.join(HSDZ, "data", "xref_yh.js"))     # 汉志桥（只读）
    hz = load_js(os.path.join(HSDZ, "data", "site_data.js"))   # 汉志站数据（只读）
    yh = load_js(os.path.join(ROOT, "data", "site_data.js"))   # 本站
    xy = load_js(os.path.join(ROOT, "data", "xref_hy.js"))     # 本站唐宋桥（宋段一致性）

    # 部域名 → id；汉郡存在性索引（部域下按 n/raw 双口径）
    bu_id = {b["name"]: b["id"] for b in hz["bu"]}
    bu_juns = {b["name"]: {s["n"] for s in b.get("states") or []} |
                      {s.get("raw") for s in b.get("states") or [] if s.get("raw")} for b in hz["bu"]}

    tang_states = [(d, s) for d in yh["daos"] for s in d["states"]]
    tang_index = {s["n"]: (d, s) for d, s in tang_states}

    # ── 反转：唐州 → 汉郡（多对一容错：一唐州可承两汉郡之名实）──
    by_tang = {}
    link_errors = []
    for r in xh["rows"]:
        m = r.get("m")
        if not m:
            continue
        buid = bu_id.get(r["bu"])
        if not buid or (r["n"] not in bu_juns.get(r["bu"], set())):
            link_errors.append(f"汉郡 {r['n']} 不在 {r['bu']}（深链无法落点）")
        if m["n"] not in tang_index:
            link_errors.append(f"唐州 {m['n']} 不在本站（汉志桥数据过期？）")
        by_tang.setdefault(m["n"], []).append({
            "n": r["n"], "bu": r["bu"], "buId": buid or "", "now": r.get("now") or "",
            "kind": m["kind"], "fam": badge_family(m["kind"]),
            "dao": m.get("dao") or "", "ju": r.get("ju") or "",
        })

    rows = []
    for d, s in tang_states:
        han = by_tang.get(s["n"])
        rows.append({"n": s["n"], "dao": d["name"], "zhen": s.get("zhen") or "",
                     "now": s.get("now") or "",
                     "han": sorted(han, key=lambda h: h["n"]) if han else None})

    # 深链（实测格式：HSDZ modes.js 用 #bu=<id>&jun=<名>，jun 按 n/raw 双口径匹配）
    def hsdz_link(h):
        return "../HSDZ/#bu=" + (h["buId"] or "?") + "&jun=" + quote(h["n"])

    by_dao = []
    for d in yh["daos"]:
        rs = [r for r in rows if r["dao"] == d["name"]]
        fams = {}
        for r in rs:
            if r["han"]:
                for h in r["han"]:
                    fams[h["fam"]] = fams.get(h["fam"], 0) + 1
        by_dao.append({"dao": d["name"], "id": d["id"], "total": len(rs),
                       "withHan": sum(1 for r in rs if r["han"]),
                       "pairs": sum(len(r["han"]) for r in rs if r["han"]), **fams})

    matched_pairs = sum(len(r["han"]) for r in rows if r["han"])
    tang_with = sum(1 for r in rows if r["han"])
    meta = {
        "han_juns": xh["meta"]["han_juns"],
        "tang_states": len(rows),
        "matched_pairs": matched_pairs,
        "tang_with_han": tang_with,
        "tang_without_han": len(rows) - tang_with,
        "same_name": sum(1 for r in rows if r["han"] for h in r["han"] if h["fam"] == "同名同城"),
        "chengming": sum(1 for r in rows if r["han"] for h in r["han"] if h["fam"] == "承名"),
        "qianyi": sum(1 for r in rows if r["han"] for h in r["han"] if h["fam"] == "迁治"),
        "han_side_unmatched": xh["meta"]["unmatched"],
        "deeplink_format": "../HSDZ/#bu=<部域id>&jun=<郡名>（实测 HSDZ js/modes.js，任务书所猜 #dao= 不符）",
        "source": "HSDZ/data/xref_yh.js + site_data.js（皆只读）；反转视角重组成因同源",
    }

    # 样例对读：采汉志桥 samples（汉志句 × 元和句，唐站逐条校验在本站）
    samples = []
    for s in xh.get("samples", []):
        if s["tn"] in tang_index:
            h0 = by_tang.get(s["tn"], [{}])[0]
            samples.append({"hn": s["hn"], "hq": s["hq"], "tn": s["tn"], "tq": s["tq"],
                            "kind": s["kind"], "fam": badge_family(s["kind"]),
                            "buId": h0.get("buId") or "", "tid": s.get("tid") or ""})

    # ── 四朝同地彩蛋：逐站校验存在 + 唐宋段与本站桥一致 ──
    song_zhou = load_js(os.path.join(TPHY, "data", "site_data.js"))["zhou"]   # 只读
    ming_fu = load_js(os.path.join(HHH, "data", "site_data.js"))["provinces"]  # 只读
    our_song = {r["n"]: r["m"]["n"] for r in xy["rows"] if r["m"]}             # 唐→宋
    era_errors = []
    for e in ERAS:
        tang_name = next(st["n"] for st in e["stops"] if st["dyn"] == "唐")
        if tang_name not in tang_index:
            era_errors.append(f"{e['title']}: 唐站 {tang_name} 不在本站")
        for st in e["stops"]:
            if st["dyn"] == "汉":
                juns = bu_juns.get(next(b["name"] for b in hz["bu"] if b["id"] == st["bu"]), set())
                if st["jun"] not in juns:
                    era_errors.append(f"{e['title']}: 汉站 {st['jun']} 不在部域 {st['bu']}")
                # 汉唐段还须是汉志桥的实际匹配（防凭空拼链）
                if not any(r["n"] == st["jun"] and r.get("m") and r["m"]["n"] == tang_name
                           for r in xh["rows"]):
                    era_errors.append(f"{e['title']}: 汉唐段 {st['jun']}→{tang_name} 非桥上实配")
            elif st["dyn"] == "宋":
                if not any(z["n"] == st["n"] for z in song_zhou):
                    era_errors.append(f"{e['title']}: 宋站 {st['n']} 不在寰宇数据")
                if our_song.get(tang_name) != st["n"]:
                    era_errors.append(f"{e['title']}: 唐宋段 {tang_name}→{st['n']} 与本站唐宋桥不符")
            elif st["dyn"] == "明":
                if not any(u["n"] == st["fu"] for p in ming_fu if p["id"] == st["pid"] for u in p["fu"]):
                    era_errors.append(f"{e['title']}: 明站 {st['fu']} 不在方舆数据")
    if era_errors or link_errors:
        for msg in (link_errors + era_errors)[:10]:
            print("✗", msg)
        sys.exit(1)

    # 组装彩蛋卡（href 逐站生成：汉 ../HSDZ、唐本站、宋 ../TPHY、明 ../HHH）
    eras = []
    for e in ERAS:
        stops = []
        for st in e["stops"]:
            if st["dyn"] == "汉":
                stops.append({"dyn": "汉", "n": st["n"], "site": st["site"], "ext": True,
                              "href": "../HSDZ/#bu=" + st["bu"] + "&jun=" + quote(st["jun"])})
            elif st["dyn"] == "唐":
                did = tang_index[st["n"]][0]["id"]
                stops.append({"dyn": "唐", "n": st["n"], "site": st["site"], "ext": False,
                              "href": "#dao=" + did + "&zhou=" + st["n"]})
            elif st["dyn"] == "宋":
                stops.append({"dyn": "宋", "n": st["n"], "site": st["site"], "ext": True,
                              "href": "../TPHY/#dao=" + st["sid"] + "&zhou=" + quote(st["n"])})
            else:
                stops.append({"dyn": "明", "n": st["n"], "site": st["site"], "ext": True,
                              "href": "../HHH/#mode=舆图&p=" + st["pid"] + "&fu=" + quote(st["fu"])})
        eras.append({"title": e["title"], "now": e["now"], "stops": stops})

    out = {"meta": meta, "byDao": by_dao, "rows": rows, "samples": samples, "eras": eras}
    with open(os.path.join(ROOT, "data", "xrev_hz.js"), "w", encoding="utf-8") as f:
        f.write("/* 元和经纬 · 汉唐回程桥（build_xrev_hz.py 生成，勿手改；HSDZ 只读） */\n")
        f.write("var YHXREV = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("汉唐回程桥：唐 %d 州 ↔ 汉志 %d 郡：得对应 %d 对（同名同城 %d · 承名 %d · 迁治 %d）"
          "｜唐州无汉对应 %d（汉志侧 51 郡无唐对应之外的新出）｜深链校验 %d 条全过｜四朝彩蛋 %d 例"
          % (len(rows), meta["han_juns"], matched_pairs, meta["same_name"], meta["chengming"],
             meta["qianyi"], meta["tang_without_han"],
             sum(len(r["han"]) for r in rows if r["han"]), len(eras)))


if __name__ == "__main__":
    main()
