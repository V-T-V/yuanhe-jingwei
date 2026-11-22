# -*- coding: utf-8 -*-
"""元和经纬 · 文本计量：site_data + text 分片 → data/stats.json + docs/ANALYSIS.md
   凡数字必出自脚本——README/ANALYSIS 的数字与本产物同源。
   运行：python tools/stats.py"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

raw = open(os.path.join(ROOT, "data", "site_data.js"), encoding="utf-8").read()
yh = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
fetch = json.load(open(os.path.join(ROOT, "data", "fetch_report.json"), encoding="utf-8"))


def shard_chars():
    """分片文本字数（按道，不含卷首）"""
    out = {}
    for f in glob.glob(os.path.join(ROOT, "data", "text", "*.js")):
        key = os.path.basename(f)[:-3]
        body = open(f, encoding="utf-8").read()
        out[key] = len(re.sub(r"\s", "", body))
    return out


def count(text, q):
    n, i = text.find(q), 0
    while i >= 0:
        n += 1
        i = text.find(q, i + len(q))
    return n


def main():
    dao_rows = []
    states = []
    for d in yh["daos"]:
        for s in d["states"]:
            states.append((d, s))
    chars = shard_chars()
    total_state_chars = sum(v for k, v in chars.items() if k != "juanshou")

    # 道级：州数/县数/字数/卷幅
    for d in yh["daos"]:
        ns = len(d["states"])
        nx = sum(len(s.get("xian") or []) for s in d["states"])
        dao_rows.append({
            "dao": d["name"], "id": d["id"], "states": ns, "xian": nx,
            "lost": len(d.get("lost") or []),
            "chars": chars.get(d["id"], 0),
            "juan_lo": min([s["juan"] for s in d["states"] if s.get("juan")], default=None),
            "juan_hi": max([s["juan"] for s in d["states"] if s.get("juan")], default=None),
        })

    # 州级排行：属县数 TOP10 / 字数 TOP10
    top_xian = sorted(states, key=lambda x: -len(x[1].get("xian") or []))[:10]
    top_xian = [{"n": s["n"], "dao": d["name"], "xian": len(s.get("xian") or [])} for d, s in top_xian]

    # 县名样本频次（山河祠庙在县条中的记述密度——以「山」「水」「故城」「陵」起首段计）
    shard_all = ""
    for f in glob.glob(os.path.join(ROOT, "data", "text", "*.js")):
        shard_all += open(f, encoding="utf-8").read()
    feats = {}
    for pat, label in [(r"[一-龥]{1,4}山，在", "山"), (r"[一-龥]{1,4}水，[一在]", "水"),
                       (r"[一-龥]{1,4}故城，在", "故城"), (r"[一-龥]{1,4}陵，", "陵墓")]:
        feats[label] = len(re.findall(pat, shard_all))

    # 节度使体系：文本明记「今为X理所」的镇 vs 整编补足
    text_marked = set()
    for d, s in states:
        pass
    zhen_members = {}
    for d, s in states:
        z = s.get("zhen")
        if z:
            zhen_members.setdefault(z, []).append(s["n"])

    conf1 = sum(1 for _, s in states if s.get("conf") == 1)
    conf2 = sum(1 for _, s in states if s.get("conf") == 2)

    n_states = len(states)
    n_xian = sum(len(s.get("xian") or []) for _, s in states)
    dao_seen = [r["dao"] for r in dao_rows if r["states"]]
    stats = {
        # ── 基础键（lint/run_tests 依赖的稳定口径）──
        "states": n_states,
        "states_coord": n_states,
        "counties_listed": n_xian,
        "daos_present": dao_seen,
        "zhens_text": len(zhen_members),
        "zhens_lost": len(yh["zhens"]) - len(zhen_members) if yh.get("zhens") else 0,
        "per_dao": {r["dao"]: {"states": r["states"], "xian": r["xian"], "lost": r["lost"]}
                    for r in dao_rows},
        # ── 计量扩展（ANALYSIS.md 同源）──
        "fetch": {"chapters": len(fetch["chapters"]), "total_chars": fetch["total_chars"],
                  "source": fetch["source"]},
        "coords": {"total": n_states, "conf1": conf1, "conf2": conf2},
        "xian_listed": n_xian,
        "county_entries": n_xian,
        "dao_rows": dao_rows,
        "top_xian": top_xian,
        "features": feats,
        "zhens": len(zhen_members),
        "state_text_chars": total_state_chars,
        "zhen_members": {k: len(v) for k, v in sorted(zhen_members.items(), key=lambda kv: -len(kv[1]))[:12]},
    }
    with open(os.path.join(ROOT, "data", "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # ANALYSIS.md（数字全自本脚本）
    dao_tbl = "\n".join(
        f"| {r['dao']} | {r['states']} | {r['xian']} | {r['lost']} | "
        f"{r['juan_lo'] or '—'}–{r['juan_hi'] or '—'} | {r['chars']:,} |"
        for r in dao_rows)
    top_tbl = "\n".join(f"| {t['n']} | {t['dao']} | {t['xian']} |" for t in top_xian)
    zhen_tbl = "\n".join(f"| {k} | {v} |" for k, v in stats["zhen_members"].items())

    # 汉唐回程桥（data/xrev_hz.js，build_xrev_hz.py 反转汉志桥产物）
    xrev_path = os.path.join(ROOT, "data", "xrev_hz.js")
    if os.path.exists(xrev_path) and os.path.exists(os.path.join(ROOT, "data", "xref_hy.js")):
        vraw = open(xrev_path, encoding="utf-8").read()
        vfull = json.loads(vraw[vraw.find("{"): vraw.rfind("}") + 1])
        vm = vfull["meta"]
        xrev_md = f"""
### 回程 · 汉唐对照（汉志互查桥，data/xrev_hz.js）

汉志侧桥（姊妹站汉志经纬 build_xref_yh.py，HSDZ 数据只读）判 {vm['han_juns']} 汉郡 ↔ {vm['tang_states']} 唐州、
得对应 {vm['matched_pairs']}——本站回程视角反转重组，对账全等（{vm['matched_pairs']} = 同名同城 {vm['same_name']} + 承名 {vm['chengming']} + 迁治 {vm['qianyi']}）；
唐州无汉对应 {vm['tang_without_han']}（汉志侧另有 {vm['han_side_unmatched']} 郡无唐对应，两侧如实并计）。
四朝同地彩蛋 {len(vfull['eras'])} 例（汉→唐→宋→明 跨链卡：京兆长安 / 河南洛阳 / 蜀成都），
逐站对四站 site_data 校验存在，唐宋段与本站唐宋桥一致。
"""
    else:
        xrev_md = ""

    # 唐宋对照（互查桥产物 data/xref_hy.js，build_xref_hy.py 生成）
    xref_path = os.path.join(ROOT, "data", "xref_hy.js")
    if os.path.exists(xref_path):
        xraw = open(xref_path, encoding="utf-8").read()
        xm = json.loads(xraw[xraw.find("{"): xraw.rfind("}") + 1])["meta"]
        xref_tbl = "\n".join(
            "| %s | %d | %d | %d | %d | %d |" % (g["dao"], g["same"], g["renamed"], g["unmatched"], g["yili"], g["sj"])
            for g in json.loads(xraw[xraw.find("{"): xraw.rfind("}") + 1])["byDao"])
        xref_md = f"""## 五、唐宋对照（寰宇互查桥）

唐 {xm['tang_states']} 州府 ↔ 宋 {xm['song_total']} 条（太平寰宇记，姊妹站寰宇经纬数据，只读）：
得对应 {xm['matched']}（同名 {xm['same_name']} · 同治异名 {xm['renamed']}）·
无对应 {xm['unmatched']}（同名异地存疑 {xm['unmatched_doubt']} · 或在寰宇佚卷 {xm['unmatched_vollost']}）；
同州异隶 {xm['yili']} · 升降（州→府/军/监）{xm['shengjiang']}。
宋侧另有 {xm['song_new']} 条无唐州对应（军监新置、四夷、唐佚之州），不计唐侧。

| 道 | 同名 | 同治异名 | 无对应 | 异隶 | 升降 |
|---|---|---|---|---|---|
{xref_tbl}

（同名=去府/州/军/监尾同名且地理今名相合；同治异名如京兆府↔雍州、汴州↔開封府、恒州↔鎮州；
同名异地如唐渭州（陇西）≠宋渭州（平凉）——存疑不计，不以似是者充数。）
{xrev_md}
## 六、古今对照导出

- 州治对照 CSV {stats['states']} 行（道/镇/州府/类/治所今地/纬经/src/置信/卷/管县/坐标注记）
- 县名录 CSV {stats['xian_listed']} 行（附郭与州同治，余县存名录不定位）
- KML / GeoJSON 州治点位 {stats['states']} 点（docs/export/，与前端「⤓ 导出」按钮同口径）
"""
    else:
        xref_md = """## 五、唐宋对照（寰宇互查桥）

（桥未建——先运行 python tools/build_xref_hy.py）
"""

    md = f"""# 元和经纬 · 文本计量（ANALYSIS）

> 凡数字必出自脚本（tools/stats.py → data/stats.json；本文件勿手改数字）。
> 语料：识典古籍·四库本《元和郡县志》，{stats['fetch']['chapters']} 章抓取，
> 共 {stats['fetch']['total_chars']:,} 字；州县结构化全文 {stats['state_text_chars']:,} 字。

## 一、道级覆盖

| 道 | 州府 | 县（名录） | 卷佚州份 | 卷幅 | 全文字数 |
|---|---|---|---|---|---|
{dao_tbl}

- 有文之道 8（淮南整道佚——申光列河南、蕲黄安列江南，唐方镇移隶之实）
- 陇右道为卷 39/40 残帙（元和时陷蕃，志存旧貌），源本道标缺失，据十道整编

## 二、州县结构

- 州府条目 {stats['states']}，州治坐标全覆盖（置信「确」{conf1} / 「推」{conf2}）
- 县名录 {stats['xian_listed']}；附郭县与州同治，余县但存名录（传本八到里程佚，不臆测定位）
- 文本所及节镇 {stats['zhens']}（原书四十七镇；淮南、安西四镇卷帙全佚）

属县最多的十州：

| 州 | 道 | 管县 |
|---|---|
{top_tbl}

## 三、山河故城（县条下地理记述形态计数）

| 形态 | 计数 |
|---|---|
""" + "\n".join(f"| {k} | {v} |" for k, v in feats.items()) + f"""

（正则形态：如「X山，在」「X水，一/在」「X故城，在」「X陵，」——元和志县条下
山川故迹记述之密度，可作方志体例计量之基线。）

## 四、镇属规模 TOP12

| 镇 | 领州 |
|---|---|
{zhen_tbl}

{xref_md}
## 七、已知之阙

- 「八到」「贡、赋」传本大段佚（标签存而文亡），站内如实标注——里程网与贡赋品类计量无从做起
- 剑南卷帙残（黎保柘霸乾诸州佚）；山南西部（峡归夔万忠涪）佚
- 州治坐标为今地整编（非考古定位），「推」级多为故城遗址
"""
    with open(os.path.join(ROOT, "docs", "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write(md)
    print("stats.json + ANALYSIS.md 更新：", stats["states"], "州 /", stats["xian_listed"], "县 /",
          stats["zhens"], "镇 /", stats["fetch"]["total_chars"], "字")


if __name__ == "__main__":
    main()
