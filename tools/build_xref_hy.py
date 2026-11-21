# -*- coding: utf-8 -*-
"""元和经纬 × 寰宇经纬 · 唐宋互查桥（P2）
   读 D:\\W_A_W\\TPHY\\data\\site_data.js（**TPHY 只读，绝不写入**），
   唐州（元和 227 州府）↔ 宋府州军监（寰宇 361 条）匹配：
     一档 同名（繁简归一 + 去府/州/军/监尾）：同名州府；
     二档 同治异名（治所今名对齐 + 坐标 ≤0.25°）：改名/升降（州→府/军/监）如实分档；
     同州异隶（唐道 ↔ 宋道隶属不同，含淮南移隶回流）单独标记；匹配不上如实计数。
   产 data/xref_hy.js（前端「唐宋对照」页签）；深链 ../TPHY/#dao=<id>&zhou=<名>。
   运行：python tools/build_xref_hy.py"""
import io
import json
import math
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPHY = os.path.join(os.path.dirname(ROOT), "TPHY", "data", "site_data.js")

# ── 繁→简 + 异体归一（仅覆盖两站名表所需字；乾/驩 等专名用字不误映射）──
T2S = {
    "㑹": "会", "䝉": "蒙", "䖍": "虔", "劍": "剑", "卭": "邛", "寕": "宁", "寧": "宁",
    "峩": "峨", "峯": "峰", "嶲": "巂", "嶺": "岭", "廣": "广", "廬": "庐", "復": "复",
    "懐": "怀", "懷": "怀", "揚": "扬", "撫": "抚", "晉": "晋", "東": "东", "榮": "荣",
    "樂": "乐", "橫": "横", "歸": "归", "涇": "泾", "涼": "凉", "湯": "汤", "滄": "沧",
    "漢": "汉", "漣": "涟", "潤": "润", "潯": "浔", "澤": "泽", "濟": "济", "濰": "潍",
    "濱": "滨", "瀘": "泸", "營": "营", "環": "环", "瓊": "琼", "當": "当", "疊": "叠",
    "監": "监", "祿": "禄", "簡": "简", "籐": "藤", "籠": "笼", "絳": "绛", "綏": "绥",
    "維": "维", "綿": "绵", "義": "义", "興": "兴", "萬": "万", "薊": "蓟", "蘄": "蕲",
    "蘇": "苏", "蘭": "兰", "處": "处", "衛": "卫", "覊": "羁", "許": "许", "貝": "贝",
    "貴": "贵", "費": "费", "賀": "贺", "資": "资", "賓": "宾", "趙": "赵", "軍": "军",
    "逺": "远", "遠": "远", "遼": "辽", "鄧": "邓", "鄭": "郑", "鎮": "镇", "長": "长",
    "開": "开", "閬": "阆", "關": "关", "陜": "陕", "陝": "陕", "陸": "陆", "陽": "阳",
    "隨": "随", "隴": "陇", "雲": "云", "靈": "灵", "順": "顺", "領": "领", "頴": "颍",
    "潁": "颍", "饒": "饶", "髙": "高", "鬱": "郁", "鮮": "鲜", "鳯": "凤", "鳳": "凤",
    "鹵": "卤", "鹽": "盐", "齊": "齐", "龍": "龙", "龔": "龚", "媯": "妫", "嵐": "岚",
    "夾": "夹", "麗": "丽", "濤": "涛", "淶": "涞", "灤": "滦", "燿": "耀", "壽": "寿",
    "處": "处", "邊": "边", "銅": "铜", "銀": "银", "鐵": "铁", "鳴": "鸣", "鞏": "巩",
    "澮": "浍", "華": "华", "肅": "肃", "慶": "庆", "豐": "丰", "愛": "爱",
    "緜": "绵", "𤓰": "瓜", "𡊮": "袁", "𤣥": "玄", "儀": "仪", "憲": "宪",
    "涼": "凉", "壽": "寿", "萊": "莱", "郟": "郏", "澂": "澄",
    "勝": "胜", "單": "单", "國": "国", "夀": "寿", "峽": "峡", "帶": "带",
    "師": "师", "昇": "升", "欽": "钦", "竇": "窦", "達": "达", "鄆": "郓",
    "階": "阶", "宷": "审", "宻": "密", "陳": "陈",
}

# 人工整编别名（书证明确而两侧数据键不合者，入档必注明「别名整编」）
ALIAS = {
    "成都府": "益州",   # 寰宇记仍以益州著成都；该条今名坐标俱缺，凭书证合档
}


def norm(s):
    return "".join(T2S.get(ch, ch) for ch in (s or ""))


SUFFIX = "府州軍监军监"


def base_key(name):
    """去 废/新/旧/唐 前缀 + 府/州/军/监 尾的归一键（雍州/雍 同键；兴元府 键=兴元；
    废宥州/新宥州 → 宥）"""
    n = norm(name)
    while n and n[0] in "废新旧唐":
        n = n[1:]
    while n and n[-1] in "府州军监":
        n = n[:-1]
    return n


def kind_of(name):
    n = norm(name)
    for suf, k in [("府", "府"), ("州", "州"), ("军", "军"), ("监", "监")]:
        if n.endswith(suf):
            return k
    return "州"


# ── 唐道 → 宋道 隶属对应（宋分道更细：山南/江南/剑南各分东西）──
DAO_MAP = {
    "关内道": ["關西道"], "河南道": ["河南道"], "河东道": ["河東道"], "河北道": ["河北道"],
    "山南道": ["山南西道", "山南東道"], "淮南道": ["淮南道"],
    "江南道": ["江南東道", "江南西道"], "剑南道": ["劍南西道", "劍南東道"],
    "岭南道": ["嶺南道"], "陇右道": ["隴右道"],
}


def dist_km(a, b):
    """球面距离（km）；缺坐标返回 None"""
    if not a or not b:
        return None
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def now_align(a, b):
    """治所今名对齐（一方含另一方，≥3 字）"""
    a, b = norm(a or ""), norm(b or "")
    if len(a) < 3 or len(b) < 3:
        return False
    return a in b or b in a


def load_js(path):
    raw = open(path, encoding="utf-8").read()
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])


def main():
    yh = load_js(os.path.join(ROOT, "data", "site_data.js"))
    hy = load_js(TPHY)  # 只读
    song_dao_id = {d["name"]: d["id"] for d in hy["daos"]}

    tang = []   # 唐州
    for d in yh["daos"]:
        for s in d["states"]:
            tang.append({"n": s["n"], "dao": d["name"], "zhen": s.get("zhen") or "",
                         "now": s.get("now") or "", "c": s.get("c")})
    song = []   # 宋府州军监
    for z in hy["zhou"]:
        if z["n"] == "領覊縻州":   # 占位条（领羁縻州），不参与匹配
            continue
        song.append({"n": z["n"], "dao": z["dao"], "id": song_dao_id.get(z["dao"], ""),
                     "now": z.get("now") or "", "c": z.get("c"),
                     "vols": (z.get("vols") or [None])[0], "xc": z.get("xc") or 0})
    for s in song:
        s["key"] = base_key(s["n"])
        s["used"] = False

    rows = []
    # ── 一档：同名（须地理/今名佐证——同名异地不入档，教训：剑南高州非广东高州）──
    for t in tang:
        k = base_key(t["n"])
        cands = [s for s in song if s["key"] == k]
        row = {"n": t["n"], "dao": t["dao"], "zhen": t["zhen"], "now": t["now"], "m": None}
        tn_full = norm(t["n"])

        def qualify(s, _t=t):
            """同名条目入档佐证：今名对齐 / 距离 ≤70 km；
            全名相同而宋条无坐标时，须宋条在唐道对应的宋道内方合档（同名异地防线）"""
            dkm = dist_km(_t["c"], s["c"])
            if now_align(_t["now"], s["now"]):
                return True, dkm
            if dkm is not None and dkm <= 110:   # ≤70 同治；70–110 迁治（注记）
                return True, dkm
            if dkm is None and norm(s["n"]) == norm(_t["n"]) and s["dao"] in DAO_MAP.get(_t["dao"], []):
                return True, None
            return False, dkm

        if cands:
            free = [s for s in cands if not s["used"]]
            pool = free or cands
            scored = sorted(pool, key=lambda s: (norm(s["n"]) != tn_full,
                                                 (qualify(s)[1] if qualify(s)[1] is not None else 9e9)))
            best = scored[0]
            ok, dkm = qualify(best)
            if ok and not best["used"]:
                best["used"] = True
                best["by"] = t["n"]
                row["m"] = {"n": best["n"], "dao": best["dao"], "id": best["id"],
                            "now": best["now"], "ju": best["vols"], "kind": "同名"}
                row.pop("why", None)
                if dkm is not None and 70 < dkm <= 110:
                    row["m"]["note"] = "同名而治所相距 %d km——宋治迁移" % round(dkm)
                elif dkm is not None and dkm > 110:
                    row["m"]["note"] = "今名对齐而宋条坐标相距 %d km——寰宇条坐标疑误，存疑并注" % round(dkm)
                elif dkm is None and not now_align(t["now"], best["now"]) and norm(best["n"]) != tn_full:
                    row["m"]["note"] = "同名，宋条无坐标，凭名合档"
            elif ok and best["used"]:
                row["why"] = "宋志%s一条已合唐%s（同名异地，此条无独对应）" % (best["n"], best.get("by", ""))
            else:
                alt = [s for s in pool if not s["used"] and qualify(s)[0]]
                if alt:
                    b2 = min(alt, key=lambda s: qualify(s)[1] or 9e9)
                    b2["used"] = True
                    b2["by"] = t["n"]
                    row["m"] = {"n": b2["n"], "dao": b2["dao"], "id": b2["id"],
                                "now": b2["now"], "ju": b2["vols"], "kind": "同名"}
                    row.pop("why", None)
                else:
                    row["why"] = "同名异地（宋志另有同名而治所非此，存疑不计）"
        rows.append(row)

    # ── 二档：同治异名（改名/升降；宋条无坐标者凭今名对齐入档并注）──
    for t, row in zip(tang, rows):
        if row["m"]:
            continue
        cands = []
        for s in song:
            if s["used"]:
                continue
            dkm = dist_km(t["c"], s["c"])
            if dkm is not None and dkm <= 28 and now_align(t["now"], s["now"]):
                cands.append((dkm, s))
            elif dkm is None and now_align(t["now"], s["now"]) and s["key"] != base_key(t["n"]) \
                    and s["dao"] in DAO_MAP.get(t["dao"], []):
                cands.append((None, s))
        if cands:
            cands.sort(key=lambda x: (x[0] is None, x[0] or 0))
            dkm, best = cands[0]
            best["used"] = True
            best["by"] = t["n"]
            row["m"] = {"n": best["n"], "dao": best["dao"], "id": best["id"],
                        "now": best["now"], "ju": best["vols"], "kind": "同治异名"}
            row.pop("why", None)
            if dkm is not None:
                row["m"]["note"] = "治所同今地（相距 %d km）而名异——唐宋间升降/改置" % round(dkm)
            else:
                row["m"]["note"] = "宋条无坐标，凭治所今名对齐"

    # ── 三档：人工整编别名（书证明确，入档必注明）──
    for t, row in zip(tang, rows):
        if row["m"] or row["n"] not in ALIAS:
            continue
        s = next((x for x in song if not x["used"] and norm(x["n"]) == ALIAS[row["n"]]), None)
        if s:
            s["used"] = True
            s["by"] = row["n"]
            row["m"] = {"n": s["n"], "dao": s["dao"], "id": s["id"],
                        "now": s["now"], "ju": s["vols"], "kind": "同治异名",
                        "note": "别名整编（%s，书证明确；宋条今名坐标俱缺）" % ALIAS[row["n"]]}
            row.pop("why", None)

    # ── 无对应归因：宋帙卷缺优先注明（按道卷幅范围核佚卷），其余如实 ──
    lost_vols = set((hy.get("stats") or {}).get("vols_lost") or [])
    for t, row in zip(tang, rows):
        if row["m"] or row.get("why"):
            continue
        hit = None
        for sd in DAO_MAP.get(t["dao"], []):
            d = next((x for x in hy["daos"] if x["name"] == sd), None)
            if not d or not d["vols"]:
                continue
            lo, hi = min(d["vols"]), max(d["vols"])
            lv = sorted(v for v in lost_vols if lo <= v <= hi)
            if lv:
                hit = (sd, lv)
        if hit:
            row["why"] = ("寰宇记%s帙有佚卷（卷 %s），或在佚卷中；否则省废/改并——如实计无对应"
                          % (hit[0], "、".join(str(v) for v in hit[1])))
        else:
            row["why"] = "宋志未见同治条目（省废/改并/边外，如实计无对应）"

    # ── 异隶 / 升降标记 ──
    for row in rows:
        m = row["m"]
        if not m:
            continue
        if m["dao"] not in DAO_MAP.get(row["dao"], []):
            m["yili"] = True   # 同州异隶：唐道与宋道隶属不同
        tk, sk = kind_of(row["n"]), kind_of(m["n"])
        if tk != sk:
            m["sj"] = "%s→%s" % (tk, sk)   # 升降：州→府 / 府→州 / 州→军 …

    # ── 样例（元和原文句 × 寰宇条目）──
    prefer = ["京兆府", "兴元府", "河中府", "汴州", "华州", "广州", "凉州",
              "恒州", "渝州", "蕲州", "沧州", "眉州"]
    yh_text = {s["n"]: s for d in yh["daos"] for s in d["states"]}
    hy_zhou = {z["n"]: z for z in hy["zhou"]}
    samples = []
    for name in prefer:
        row = next((r for r in rows if r["n"] == name and r["m"]), None)
        if not row:
            continue
        yan = (yh_text[name].get("yan") or "").strip()
        yz = (hy_zhou[row["m"]["n"]].get("yz") or "").strip()
        samples.append({
            "tn": name, "tq": (yan[:64] + "……") if len(yan) > 64 else yan,
            "sn": row["m"]["n"], "sq": (yz[:64] + "……") if len(yz) > 64 else yz,
            "sid": row["m"]["id"], "kind": row["m"]["kind"],
            "sj": row["m"].get("sj", ""), "yili": bool(row["m"].get("yili")),
        })
        if len(samples) >= 8:
            break

    # ── 计数（凡计数出自脚本）──
    matched = [r for r in rows if r["m"]]
    by_dao = []
    for d in yh["daos"]:
        rs = [r for r in rows if r["dao"] == d["name"]]
        by_dao.append({
            "dao": d["name"], "id": d["id"],
            "total": len(rs),
            "matched": sum(1 for r in rs if r["m"]),
            "same": sum(1 for r in rs if r["m"] and r["m"]["kind"] == "同名"),
            "renamed": sum(1 for r in rs if r["m"] and r["m"]["kind"] == "同治异名"),
            "unmatched": sum(1 for r in rs if not r["m"]),
            "yili": sum(1 for r in rs if r["m"] and r["m"].get("yili")),
            "sj": sum(1 for r in rs if r["m"] and r["m"].get("sj")),
        })
    meta = {
        "tang_states": len(rows),
        "matched": len(matched),
        "same_name": sum(1 for r in matched if r["m"]["kind"] == "同名"),
        "renamed": sum(1 for r in matched if r["m"]["kind"] == "同治异名"),
        "unmatched": sum(1 for r in rows if not r["m"]),
        "unmatched_doubt": sum(1 for r in rows if not r["m"] and "同名异地" in r.get("why", "")),
        "unmatched_vollost": sum(1 for r in rows if not r["m"] and "佚卷" in r.get("why", "")),
        "yili": sum(1 for r in matched if r["m"].get("yili")),
        "shengjiang": sum(1 for r in matched if r["m"].get("sj")),
        "song_total": len(song),
        "song_matched": sum(1 for s in song if s["used"]),
        "song_new": sum(1 for s in song if not s["used"]),
        "source": "TPHY/data/site_data.js（只读 · 太平寰宇记 kanripo/ctext 转录本）",
    }
    out = {"meta": meta, "byDao": by_dao, "rows": rows, "samples": samples}
    with open(os.path.join(ROOT, "data", "xref_hy.js"), "w", encoding="utf-8") as f:
        f.write("/* 元和经纬 · 寰宇互查桥（build_xref_hy.py 生成，勿手改；TPHY 只读） */\n")
        f.write("var YHXREF = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("唐宋对照桥：唐 %d 州府 ↔ 宋 %d 条：同名 %d · 同治异名 %d · 无对应 %d｜异隶 %d · 升降 %d｜宋侧无唐对应 %d"
          % (meta["tang_states"], meta["song_total"], meta["same_name"], meta["renamed"],
             meta["unmatched"], meta["yili"], meta["shengjiang"], meta["song_new"]))
    print("样例：", "、".join(s["tn"] + "↔" + s["sn"] for s in samples))


if __name__ == "__main__":
    main()
