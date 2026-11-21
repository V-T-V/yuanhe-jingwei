# -*- coding: utf-8 -*-
"""元和经纬 · 古今对照导出（P2）：227 州治 + 1,081 县名录 → CSV（带 BOM）/ KML / GeoJSON
   字段与前端「⤓ 导出」按钮同口径（js/panels.js exportRows）——两处数字互证。
   坐标为整编今地（src:derived，非考古定位），置信分确/推，导出中逐行注明。
   运行：python tools/export_data.py → docs/export/"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "export")
os.makedirs(OUT, exist_ok=True)

raw = open(os.path.join(ROOT, "data", "site_data.js"), encoding="utf-8").read()
yh = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])

BOM = "\ufeff"


def main():
    # ── 州表（227 行）──
    zhou_rows = [["道", "镇", "州府", "类", "治所今地", "纬度", "经度", "src", "置信", "卷", "管县数", "坐标注记"]]
    feats, pins = [], []
    for d in yh["daos"]:
        for u in d["states"]:
            conf = "推" if u.get("conf") == 2 else "确"
            zhou_rows.append([
                d["name"], u.get("zhen") or "", u["n"],
                "府" if u["n"].endswith("府") else "州",
                u.get("now") or "",
                (u.get("c") or ["", ""])[0], (u.get("c") or ["", ""])[1],
                u.get("src") or "derived", conf, u.get("juan") or "",
                len(u.get("xian") or []),
                "整编今地坐标（非考古定位）",
            ])
            if u.get("c"):
                feats.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [u["c"][1], u["c"][0]]},
                    "properties": {"名": u["n"], "类": "府" if u["n"].endswith("府") else "州",
                                   "道": d["name"], "镇": u.get("zhen") or "", "今地": u.get("now") or "",
                                   "src": u.get("src") or "derived", "置信": conf,
                                   "卷": u.get("juan") or "", "管县": len(u.get("xian") or []),
                                   "坐标注记": "整编今地坐标（非考古定位）"},
                })
                pins.append(
                    "<Placemark><name>%s</name><description>%s%s 今%s（src:derived 置信%s）</description>"
                    "<Point><coordinates>%s,%s,0</coordinates></Point></Placemark>"
                    % (u["n"], d["name"], (" · " + u["zhen"]) if u.get("zhen") else "",
                       u.get("now") or "", conf, u["c"][1], u["c"][0]))

    # ── 县表（1,081 行：附郭与州同治，余县但存名录）──
    xian_rows = [["道", "州", "县", "附郭/属县", "附注"]]
    for d in yh["daos"]:
        for u in d["states"]:
            for i, x in enumerate(u.get("xian") or []):
                xian_rows.append([
                    d["name"], u["n"], x,
                    "附郭" if i == 0 else "属县",
                    ("与州治同治（%s）" % (u.get("now") or "")) if i == 0 else "名录存真，治所未定位",
                ])

    # ── 落盘 ──
    def w(name, text):
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print("  ✓", name)

    w("元和经纬-州治对照.csv", BOM + "\n".join(",".join(str(c) for c in r) for r in zhou_rows) + "\n")
    w("元和经纬-县名录.csv", BOM + "\n".join(",".join(str(c) for c in r) for r in xian_rows) + "\n")
    w("元和经纬-州治点位.kml",
      '<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
      "<name>元和经纬·州治点位（整编今地坐标）</name>" + "".join(pins) + "</Document></kml>\n")
    w("元和经纬-州治点位.geojson", json.dumps({"type": "FeatureCollection", "features": feats},
                                            ensure_ascii=False, indent=1) + "\n")
    print("导出完成：州 %d 行（表头外 %d 数据行）· 县 %d 行（表头外 %d）· KML/GeoJSON 点位 %d"
          % (len(zhou_rows), len(zhou_rows) - 1, len(xian_rows), len(xian_rows) - 1, len(feats)))


if __name__ == "__main__":
    main()
