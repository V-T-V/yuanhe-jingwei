# -*- coding: utf-8 -*-
"""元和经纬 · 全文分片管线
data_raw/sdgj/*.html → data/text/<dao_id>.js（懒加载）+ data/text/juanshou.js
  每道一文件: YHTEXT["guannei"] = {"京兆府":"全篇文本", …, "__dao__":"道序全文"}
  卷首一文件: YHTEXT["juanshou"] = {"提要":"…","原序":"…"}
运行：python tools/build_text.py（须在 build_data.py 之后——州名清单同源）
"""
import glob
import importlib.util
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data_raw", "sdgj")
OUT = os.path.join(ROOT, "data", "text")

DAO_ID = {"关内道": "guannei", "河南道": "henan", "河东道": "hedong",
          "河北道": "hebei", "山南道": "shannan", "淮南道": "huainan",
          "江南道": "jiangnan", "剑南道": "jiannan", "岭南道": "lingnan",
          "陇右道": "longyou"}
BOILER = {"钦定四库全书", "唐李吉甫撰"}


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).replace("\u3000", "").replace("\xa0", "").strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    sys_path = os.path.join(ROOT, "tools", "build_data.py")
    spec = importlib.util.spec_from_file_location("bd", sys_path)
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    blocks = bd.parse_blocks()

    # 卷首（提要/原序 = 首两章）
    juanshou = {}
    js_parts = []
    for kind, t, ch in blocks:
        if ch <= 1:
            js_parts.append(t)
    # 提要与原序各成篇（按章切）
    chapters = {}
    for kind, t, ch in blocks:
        chapters.setdefault(ch, []).append(t)
    if 0 in chapters:
        juanshou["提要"] = "\n".join(chapters[0])
    if 1 in chapters:
        juanshou["原序"] = "\n".join(chapters[1])
    with open(os.path.join(OUT, "juanshou.js"), "w", encoding="utf-8") as f:
        f.write("/* 元和经纬 · 卷首（build_text.py 生成） */\n")
        f.write("var YHTEXT = window.YHTEXT || {};\n")
        f.write("YHTEXT[\"juanshou\"] = " + json.dumps(juanshou, ensure_ascii=False) + ";\n")

    # 分道分州
    dao_texts = {}   # dao -> {state: [paras]}
    cur_state, cur_dao = None, None
    ZHOU_RE = bd.ZHOU_RE
    JUAN_RE = bd.JUAN_RE
    INLINE_RE = bd.INLINE_STATE_RE
    for kind, t, ch in blocks:
        if ch <= 1:
            continue
        if JUAN_RE.match(t) or t in BOILER:
            continue
        if t in DAO_ID:
            cur_dao = DAO_ID[t]
            cur_state = "__dao__"
            dao_texts.setdefault(cur_dao, {}).setdefault("__dao__", [])
            dao_texts[cur_dao]["__dao__"].append(t)
            continue
        # 州名块带道修正（陇右残帙等）——与 build_data 同口径
        mz0 = ZHOU_RE.match(t)
        if mz0:
            dao_name2 = bd.DAO_OVERRIDE.get(mz0.group(1))
            if dao_name2 and DAO_ID.get(dao_name2) and DAO_ID[dao_name2] != cur_dao:
                cur_dao = DAO_ID[dao_name2]
                cur_state = None
        m = ZHOU_RE.match(t)
        if m:
            cur_state = m.group(1)
            dao_texts.setdefault(cur_dao, {})[cur_state] = []
            continue
        im = INLINE_RE.match(t)
        if im and t.count("，") <= 12:
            cur_state = im.group(1)
            dao_texts.setdefault(cur_dao, {})[cur_state] = []
        if cur_dao is None:
            continue
        bag = dao_texts.setdefault(cur_dao, {})
        if cur_state:
            bag.setdefault(cur_state, []).append(t)

    total = 0
    for dao, bag in dao_texts.items():
        out = {"__dao__": "\n".join(bag.get("__dao__", []))}
        for st, paras in bag.items():
            if st == "__dao__":
                continue
            out[st] = st + "\n" + "\n".join(paras)
            total += len(re.sub(r"\s", "", out[st]))
        with open(os.path.join(OUT, dao + ".js"), "w", encoding="utf-8") as f:
            f.write("/* 元和经纬 · %s 全文（build_text.py 生成） */\n" % dao)
            f.write("var YHTEXT = window.YHTEXT || {};\n")
            f.write("YHTEXT[%s] = " % json.dumps(dao) + json.dumps(out, ensure_ascii=False) + ";\n")
    print(f"分片 {len(dao_texts)} 道 · 州县全文 {total} 字 → data/text/")


if __name__ == "__main__":
    main()
