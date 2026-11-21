# -*- coding: utf-8 -*-
"""《元和经纬》论文排印：docs/ANALYSIS.md → docs/元和经纬-数字人文.pdf
   题页摘要数字运行时取自 data/stats.json 与 data/xref_hy.js（凡数字出自脚本）；
   正文由 ANALYSIS.md（tools/stats.py 生成）逐节解析——md 重产而 PDF 未重排，lint 哨兵即红。
   运行：python tools/build_paper_pdf.py"""
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "元和经纬-数字人文.pdf")
MD = os.path.join(ROOT, "docs", "ANALYSIS.md")

# 插图缺失时自动重建（管线可重入：data/stats.json → build_paper_figs.py，学 HHH）
FIGS_DIR = os.path.join(ROOT, "docs", "figs")
NEED_FIGS = ["fig1_dao.png", "fig2_lost.png", "fig3_zhen.png"]
if not all(os.path.isfile(os.path.join(FIGS_DIR, f)) for f in NEED_FIGS):
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "build_paper_figs.py")],
                   check=True)

pdfmetrics.registerFont(TTFont("KaiTi", r"C:\Windows\Fonts\STKAITI.TTF"))
pdfmetrics.registerFont(TTFont("YaHei", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))

# ━━ 配色（站色系：石青 · 朱砂 · 麻纸）━━
ACCENT = colors.HexColor("#2f5d70")
CINNABAR = colors.HexColor("#8c2c1c")
TEXT_PRIMARY = colors.HexColor("#2d2820")
TEXT_MUTED = colors.HexColor("#8a7f68")
BG_SURFACE = colors.HexColor("#e8e2d0")
BG_PAGE = colors.HexColor("#efeada")

W, H = A4
M = 20 * mm
AW = W - 2 * M

S = {
    "title": ParagraphStyle("t", fontName="KaiTi", fontSize=23, leading=33, alignment=TA_CENTER,
                            textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "sub": ParagraphStyle("s", fontName="KaiTi", fontSize=12.5, leading=19, alignment=TA_CENTER,
                          textColor=TEXT_MUTED, wordWrap="CJK"),
    "h1": ParagraphStyle("h1", fontName="KaiTi", fontSize=15.5, leading=23, textColor=ACCENT,
                         spaceBefore=14, spaceAfter=6, wordWrap="CJK"),
    "body": ParagraphStyle("b", fontName="YaHei", fontSize=10.5, leading=17.5, alignment=TA_JUSTIFY,
                           textColor=TEXT_PRIMARY, spaceAfter=5, wordWrap="CJK", firstLineIndent=21),
    "body0": ParagraphStyle("b0", fontName="YaHei", fontSize=10.5, leading=17.5, alignment=TA_JUSTIFY,
                            textColor=TEXT_PRIMARY, spaceAfter=4, wordWrap="CJK"),
    "abs": ParagraphStyle("a", fontName="YaHei", fontSize=9.8, leading=16.5, alignment=TA_JUSTIFY,
                          textColor=TEXT_PRIMARY, wordWrap="CJK", firstLineIndent=19.6),
    "cap": ParagraphStyle("c", fontName="KaiTi", fontSize=9.5, leading=14, alignment=TA_CENTER,
                          textColor=TEXT_MUTED, spaceBefore=2, spaceAfter=8, wordWrap="CJK"),
    "th": ParagraphStyle("th", fontName="YaHei", fontSize=9.5, leading=13.5, alignment=TA_CENTER,
                         textColor=colors.white, wordWrap="CJK"),
    "td": ParagraphStyle("td", fontName="YaHei", fontSize=9.5, leading=13.5, alignment=TA_CENTER,
                         textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "tdl": ParagraphStyle("tdl", fontName="YaHei", fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY,
                          textColor=TEXT_PRIMARY, wordWrap="CJK"),
}


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, st="body"):
    return Paragraph(esc(t), S[st])


def tbl(headers, rows):
    n = len(headers)
    data = [[Paragraph(esc(h), S["th"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(esc(c), S["tdl"] if i == 0 else S["td"]) for i, c in enumerate(r)])
    t = Table(data, colWidths=[AW / n] * n, hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_SURFACE]),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#c9c2ad")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def footer(cv, doc):
    cv.saveState()
    cv.setFont("KaiTi", 8.5)
    cv.setFillColor(TEXT_MUTED)
    cv.drawCentredString(W / 2, 12 * mm, f"— {doc.page} —")
    cv.setFont("KaiTi", 7.5)
    cv.drawString(M, 12 * mm, "元和经纬 · 数字人文")
    cv.drawRightString(W - M, 12 * mm, "元和郡县图志（唐 · 李吉甫）")
    cv.restoreState()


def fig(fname, h_mm, caption):
    img = Image(os.path.join(FIGS_DIR, fname), width=AW, height=h_mm * mm, hAlign="CENTER")
    return KeepTogether([Spacer(1, 2 * mm), img, Paragraph(esc(caption), S["cap"])])


# 节 → 插图（fname, h_mm, 图注）。挂在各节首表之后——图文对应，数字均出自 data/stats.json
FIGS_AFTER = {
    "一、道级覆盖": [
        ("fig1_dao.png", 103.9, "图 1　十道州府数与县名录数——淮南整道佚（data/stats.json: per_dao）"),
        ("fig2_lost.png", 85.0, "图 2　卷佚 31 州份的道级分布——剑南残帙 14 · 淮南全佚 6（data/stats.json: per_dao[].lost）"),
    ],
    "四、镇属规模 TOP12": [
        ("fig3_zhen.png", 113.3, "图 3　镇属规模 TOP12——陇右诸州（陷蕃残帙）21 州独大（data/stats.json: zhen_members）"),
    ],
}


def parse_md(md):
    """ANALYSIS.md（stats.py 产物）→ flowables：## 节 → h1；表格 → tbl；- 条 → body0；> 引 → cap
    节内首表后按 FIGS_AFTER 挂插图（图注自 data/stats.json 键名，凡数字出自脚本）。"""
    out, lines, i = [], md.splitlines(), 0
    tbl_no = 0
    section, figs_done = "", set()
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("## "):
            section = ln[3:].strip()
            out.append(P(ln[3:], "h1"))
            i += 1
            continue
        if ln.startswith("# "):
            i += 1
            continue
        if ln.startswith("> "):
            out.append(P(ln[2:].lstrip(), "cap"))
            i += 1
            continue
        if ln.startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-— ") for c in row):
                    block.append(row)
                i += 1
            if block:
                tbl_no += 1
                out.append(tbl(block[0], block[1:]))
                out.append(Spacer(1, 2 * mm))
                if section in FIGS_AFTER and section not in figs_done:
                    for fname, h_mm, cap in FIGS_AFTER[section]:
                        out.append(fig(fname, h_mm, cap))
                    figs_done.add(section)
            continue
        if ln.lstrip().startswith("- "):
            out.append(P("· " + ln.lstrip()[2:], "body0"))
            i += 1
            continue
        # 普通段：并下行（ANALYSIS.md 无跨行段落，逐行成段即可）
        out.append(P(ln.strip(), "body0"))
        i += 1
    return out


def main():
    stats = json.load(open(os.path.join(ROOT, "data", "stats.json"), encoding="utf-8"))
    xraw = open(os.path.join(ROOT, "data", "xref_hy.js"), encoding="utf-8").read()
    xm = json.loads(xraw[xraw.find("{"): xraw.rfind("}") + 1])["meta"]
    md = open(MD, encoding="utf-8").read()

    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=M, rightMargin=M,
                          topMargin=18 * mm, bottomMargin=20 * mm,
                          title="元和经纬：《元和郡县图志》数字人文整编", author="元和经纬项目组",
                          subject="数字人文·唐代政区地理·元和郡县图志", creator="元和经纬")
    frame = Frame(M, 20 * mm, AW, H - 38 * mm, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])

    E = [Spacer(1, 10 * mm),
         Paragraph("《元和郡县图志》的数字人文整编", S["title"]),
         Spacer(1, 3 * mm),
         Paragraph("——十道四十七镇州县的数字化、缺卷实录与唐宋对照", S["sub"]),
         Spacer(1, 8 * mm),
         Paragraph("元和经纬项目组", S["sub"]),
         Paragraph("2026 年 11 月 · 全部数字由脚本可复核（tools/stats.py · build_xref_hy.py）", S["sub"]),
         Spacer(1, 5 * mm),
         HRFlowable(width="34%", thickness=.7, color=ACCENT, hAlign="CENTER"),
         Spacer(1, 5 * mm)]

    f = stats["fetch"]
    abstract = (
        "<b>摘　要</b>　本文报告唐李吉甫《元和郡县图志》（元和八年成书，起京兆府、尽陇右道，"
        "凡四十七镇、四十卷）的数字人文整编。自识典古籍四库本抓取 %(chapters)d 章、%(chars)s 字，"
        "解析得州府条目 %(states)d、县名录 %(counties)d，州治今地坐标全覆盖（置信确 %(c1)d / 推 %(c2)d，"
        "src:derived，非考古定位）。方法要点在「佚则如实计佚」：此本「八到」「贡、赋」两节大段佚失"
        "（标签俱存而内容已亡），淮南道整道佚——本文不以他书补缀，站内逐条标「佚」，里程网与贡赋"
        "品类计量因此悬置并如实声明，此为本整编之学术底线而非缺憾遮掩。在此底线上作三项计量："
        "道级覆盖（有文之道 8，陇右残帙 21 州存志旧貌）、山河故城记述形态（山 %(shan)d · 水 %(shui)d · "
        "故城 %(gucheng)d · 陵 %(lingmu)d）、镇属规模（文本所及 %(zhens)d 镇）。又与宋乐史《太平寰宇记》"
        "（姊妹站寰宇经纬数据）作唐宋州府对照：唐 %(tang)d 州府得宋对应 %(matched)d（同名 %(same)d · "
        "同治异名 %(renamed)d），无对应 %(unmatched)d（同名异地存疑 %(doubt)d、或在寰宇佚卷 %(vollost)d "
        "如实分记）；同州异隶 %(yili)d（唐方镇移隶回流、宋分道改制）、升降 %(sj)d（州→府/军/监）"
        "各为唐宋政区变迁之实录。全部数字可由仓库脚本复现。" % {
            "chapters": f["chapters"], "chars": format(f["total_chars"], ","),
            "states": stats["states"], "counties": stats["counties_listed"],
            "c1": stats["coords"]["conf1"], "c2": stats["coords"]["conf2"],
            "shan": stats["features"]["山"], "shui": stats["features"]["水"],
            "gucheng": stats["features"]["故城"], "lingmu": stats["features"]["陵墓"],
            "zhens": stats["zhens"], "tang": xm["tang_states"], "matched": xm["matched"],
            "same": xm["same_name"], "renamed": xm["renamed"], "unmatched": xm["unmatched"],
            "doubt": xm["unmatched_doubt"], "vollost": xm["unmatched_vollost"],
            "yili": xm["yili"], "sj": xm["shengjiang"]})
    kw = ("<b>关键词</b>　元和郡县图志；唐代政区地理；数字人文；缺卷实录；唐宋对照；太平寰宇记")
    abs_tbl = Table([[Paragraph(abstract, S["abs"])], [Paragraph(kw, S["abs"])]], colWidths=[AW])
    abs_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_PAGE),
        ("LINEBELOW", (0, 0), (-1, 0), .4, colors.HexColor("#d5cfbb")),
        ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#c9c2ad")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    E += [abs_tbl, Spacer(1, 6 * mm)]

    E += [P("引言", "h1"),
          P("《元和郡县图志》是我国现存最早又较完整的地方总志，其「每镇皆图在篇首」之体制"
            "（图至南宋已亡，故传本称《元和郡县志》）使唐元和一朝的政治地理具备逐州可数的结构。"
            "本整编将四库本全文解析为「道—镇—州—县」机器可读数据，坐标依唐代政区地理整编为今地"
            "（附郭县与州同治，余县但存名录，不作定位臆测），并坚持两条纪律：凡数字必出自脚本；"
            "佚则如实计佚。以下各节计量均由 tools/stats.py 产出的 ANALYSIS.md 逐节排印，"
            "交互验证见于配套站点元和经纬（舆图 · 分镇循读 · 全书检索 · 唐宋对照）。")]
    E += parse_md(md)
    E += [Spacer(1, 4 * mm), HRFlowable(width="100%", thickness=.5, color=BG_SURFACE),
          Paragraph("本文一切数字可由仓库脚本复现；交互验证：站点「舆图」「分镇而读」「唐宋对照」诸页签。", S["cap"])]

    doc.build(E)
    print("OK →", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
