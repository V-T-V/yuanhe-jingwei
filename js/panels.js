/* ═══════════ 元和经纬 · 卷宗面板（总叙 / 道 / 州 / 关于） ═══════════ */

const panel = document.getElementById("panel"),
      pbody = document.getElementById("pbody"),
      vname = document.getElementById("vname"),
      vseal = document.getElementById("vseal");
function showPanel(){ panel.classList.add("open"); document.body.classList.remove("nopanel"); }
function hidePanel(){ panel.classList.remove("open"); document.body.classList.add("nopanel"); }
document.getElementById("pclose").onclick = ()=>{ hidePanel(); if (selDao) selectDao(null); };
function vset(name, seal){ vname.textContent = name; vseal.textContent = seal || "元和"; }

/* 全局统计（自解析数据实时计算） */
const ST = (()=>{
  const nD = YH.daos.filter(d=>d.states.length).length;
  let nS = 0, nX = 0, nC = 0, nLost = 0;
  YH.daos.forEach(d=>{
    nS += d.states.length;
    nLost += (d.lost || []).length;
    d.states.forEach(u=>{ nX += (u.xian || []).length;
      if (u.c) nC++; });
  });
  const zhenSet = new Set();
  YH.daos.forEach(d=>d.states.forEach(u=>{ if (u.zhen) zhenSet.add(u.zhen); }));
  return {d: nD, s: nS, x: nX, c: nC, lost: nLost, z: zhenSet.size};
})();

/* ── 总叙（首屏面板） ── */
function openIntro(){
  vset("元和经纬", "总叙");
  pbody.innerHTML = `
    <div class="p-kicker">元和郡县图志 · 唐 · 李吉甫 · 元和八年（813）成书</div>
    <div class="quote" style="text-align:center;font-size:15.5px;line-height:2.3;padding:22px 12px">
      起京兆府，尽陇右道<br>凡四十七镇，成四十卷</div>
    <div class="p-cap">十道纲</div>
    <ul class="ful" id="daolist">
      ${YH.daos.map(d=>`<li data-id="${d.id}">
        <span class="dot" style="width:9px;height:9px;flex:none;box-shadow:inset 0 0 0 1.5px ${d.color};background:${d.states.length ? d.color : "transparent"}"></span>
        <span class="fn">${d.name}</span>
        <span class="fnow">${d.states.length ? "卷" + (d.states[0].juan || "？") + "起" : "整道卷佚"}</span>
        <span class="fct">${d.states.length}州</span><span class="arrow">➤</span></li>`).join("")}
    </ul>
    <div class="stat-strip">
      <div class="st"><b>${ST.d}</b><span>道（有文）</span></div>
      <div class="st"><b>${ST.s}</b><span>州府</span></div>
      <div class="st"><b>${ST.z}</b><span>镇（文本所及）</span></div>
      <div class="st"><b>${ST.x}</b><span>县（名录）</span></div>
      <div class="st"><b>${ST.c}</b><span>州治坐标</span></div>
      <div class="st"><b>${ST.lost}</b><span>卷佚州份</span></div>
    </div>
    <div class="p-cap">卷首文献</div>
    <div class="chips" id="jschips">
      ${JUANSHOU.map((t,i)=>`<span class="chip jschip" data-i="${i}">${t}</span>`).join("")}
    </div>
    <div class="p-cap">使用</div>
    <div class="hint">左列纲目按「道—镇—州」分镇而读，点道名观其治所晕罩（非考证边界），点州名入详情（沿革 · 八到 · 贡赋 · 辖县 · 阅原卷全文）。州印大小随属县数；zoom≥6 附郭县点显现，zoom≥7 州名常显。顶栏检索州县名（回车直达首条），「在全书原文中检索」遍检全书。底栏 ⚑ 漫游随机入州，☾ 夜读。深链自动写回地址栏。</div>`;
  pbody.querySelectorAll("#daolist li").forEach(li=>li.onclick=()=>{
    selectDao(li.dataset.id);
    openDao(YH.daos.find(d=>d.id === li.dataset.id));
  });
  pbody.querySelectorAll(".jschip").forEach(c=>c.onclick=()=>openJuanshou(+c.dataset.i));
  showPanel();
}

/* ── 道面板 ── */
function openDao(dao){
  vset(dao.name, "道");
  const rows = dao.states.map(u=>`
    <li data-n="${u.n}">
      <span class="fn">${u.n}</span>
      <span class="fnow">${u.now ? "今" + u.now : ""}</span>
      <span class="fct">${(u.xian || []).length ? u.xian.length + "县" : ""}</span>
      <span class="arrow">➤</span></li>`).join("");
  const lostRows = (dao.lost || []).map(l=>`
    <li class="lostrow" data-n="${l.n}">
      <span class="fn" style="color:var(--ink-faint)">${l.n}</span>
      <span class="fnow">${l.note || "卷佚"}</span>
      <span class="fct">有目无文</span></li>`).join("");
  pbody.innerHTML = `
    <div class="p-kicker">${dao.states.length ? "卷" + (dao.states[0].juan || "？") + " — 卷" + (dao.states[dao.states.length-1].juan || "？") : "卷佚"}</div>
    <div class="p-ju">${dao.name}</div>
    <div class="stat-strip" style="margin:0 0 12px">
      <div class="st"><b>${dao.states.length}</b><span>州府有文</span></div>
      <div class="st"><b>${(dao.lost || []).length}</b><span>州份卷佚</span></div>
      <div class="st"><b>${dao.states.reduce((s,u)=>s+(u.xian||[]).length, 0)}</b><span>县（名录）</span></div>
    </div>
    <div class="p-cap">州府</div>
    <ul class="ful">${rows}</ul>
    ${lostRows ? `<div class="p-cap">卷佚州份（灰显）</div><ul class="ful">${lostRows}</ul>` : ""}
    ${dao.states.length ? `<div class="readrow"><button class="readfull" data-daoft="1">阅${dao.name}诸州全文 ➤</button></div>` : ""}`;
  pbody.querySelectorAll(".ful li[data-n]").forEach(li=>li.onclick=()=>{
    const u = dao.states.find(x=>x.n === li.dataset.n);
    if (u) openState(dao, u);
  });
  const fb = pbody.querySelector("[data-daoft]");
  if (fb) fb.onclick = ()=>openDaoText(dao);
  selectDao(dao.id);
  syncHash("dao=" + dao.id);
  showPanel();
}

/* ── 州面板（详情） ── */
var __curState = null;
function openState(dao, u){
  __curState = { dao: dao.id, n: u.n };
  vset(u.n.replace(/[府州]$/, "").slice(0, 6), dao.name.replace("道", ""));
  vseal.textContent = u.n.endsWith("府") ? "府" : "州";
  const xchips = (u.xian || []).map((x, i)=>
    `<span class="chip${i === 0 ? " fg" : ""}" title="${i === 0 ? "附郭 · 与州同治" : "属县（治所未定位，名录存真）"}">${x}${i === 0 ? " · 附郭" : ""}</span>`).join("");
  pbody.innerHTML = `
    <div class="p-kicker">${dao.name}${u.zhen ? " · " + u.zhen : ""}${u.juan ? " · 卷" + u.juan : ""}</div>
    ${u.now ? `<div class="p-now">治今 ${u.now}${u.conf === 2 ? "（推）" : ""}</div>` : ""}
    <div class="readrow" style="margin:0 0 4px">
      <button class="readfull" data-ft="1">阅原卷全文 ➤</button>
      <button class="star" data-st="1">☆ 书签</button>
    </div>
    ${u.yan ? `<div class="p-cap">沿革（摘）</div><div class="quote">${u.yan}……</div>` : ""}
    <div class="p-cap">八到 · 贡赋</div>
    ${u.badao || u.gongfu
      ? `<div class="lostnote">此本「${u.badao ? "八到" : ""}${u.badao && u.gongfu ? "」「" : ""}${u.gongfu ? "贡、赋" : ""}」标签俱存而内容已佚——宋传本已然，据实标注。</div>`
      : `<div class="lostnote">此本未见「八到」「贡、赋」标签（佚）。</div>`}
    <div class="p-cap">辖县${(u.xian || []).length ? " · 管" + u.xian.length + "县" : ""}</div>
    <div class="chips">${xchips || '<span class="chip small">县名录佚（卷残）</span>'}</div>
    <div class="readrow" style="margin-top:8px">
      <button class="readfull" id="shareZhou" title="复制此景链接">🔗 分享此景</button>
    </div>
    <div class="p-cap">出处 · 定位</div>
    <div class="hint">《元和郡县图志》${dao.name} · ${u.n}条。治所坐标为依唐代政区地理整编之今地（src:derived${u.conf === 2 ? " · 置信度：推" : " · 置信度：确"}），附郭县与州城同治；属县但存名录，未作定位。</div>`;
  const fb = pbody.querySelector("[data-ft]");
  if (fb) fb.onclick = ()=>openStateText(dao, u);
  const sb = pbody.querySelector("[data-st]");
  if (sb) sb.onclick = ()=>{
    const added = BM.toggle(dao, u);
    sb.classList.toggle("on", added);
    sb.textContent = (added ? "★" : "☆") + " 书签";
  };
  const sh = pbody.querySelector("#shareZhou");
  if (sh) sh.onclick = ()=>{
    const url = location.origin + location.pathname +
      "#dao=" + dao.id + "&zhou=" + encodeURIComponent(u.n);
    const ok = ()=>{ sh.textContent = "✓ 已复制"; setTimeout(()=>sh.textContent = "🔗 分享此景", 1600); };
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(ok, ok);
    else {
      const ta = document.createElement("textarea");
      ta.value = url; document.body.appendChild(ta);
      ta.select(); document.execCommand("copy"); ta.remove(); ok();
    }
  };
  if (u.c) safeFlyTo(u.c, 7, {duration: 1.1});
  syncHash("dao=" + dao.id + "&zhou=" + encodeURIComponent(u.n));
  showPanel();
}

/* ── 关于 · 版本与缺卷（如实标注） ── */
function openAbout(){
  vset("关于", "校记");
  pbody.innerHTML = `
    <div class="p-kicker">元和经纬 · 数据与体例</div>
    <div class="stat-strip" style="margin-top:2px">
      <div class="st"><b>${ST.d}</b><span>道（有文）</span></div>
      <div class="st"><b>${ST.s}</b><span>州府</span></div>
      <div class="st"><b>${ST.z}</b><span>镇</span></div>
      <div class="st"><b>${ST.x}</b><span>县</span></div>
      <div class="st"><b>${ST.c}</b><span>州治坐标</span></div>
      <div class="st"><b>${ST.lost}</b><span>卷佚州份</span></div>
    </div>
    <div class="p-cap">源流</div>
    <div class="hint">文本取自识典古籍《钦定四库全书》本《元和郡县志》（SK0967），服务端渲染页逐章抓取解析（tools/fetch_text.py → build_data.py → build_text.py）。全书十道四十七镇，此本实存七道有文；州治今地坐标依唐代政区地理整编（src:derived，置信度分确/推两级），附郭县与州同治，余县但存名录。凡数字（州县数、字数）皆出自脚本（data/stats.json）。</div>
    <div class="p-cap">缺卷与残佚（据四库提要）</div>
    <div class="hint">${MISSING_NOTE}</div>
    <div class="p-cap">体例说明</div>
    <div class="hint">「八到」「贡、赋」原文在传本中大段佚失，遇标签存而文佚者如实标注，不以他书补缀；淮南道整道佚，其申、光列河南道，蕲、黄、安列江南道，均系唐方镇移隶之实录。太原府、邢洺磁等州之道属，四库本重编偶有错标，本站据《唐六典》十道整编并在数据中注明。地图道晕为治所凸包示意，非考证边界。</div>
    <div class="p-cap">已知之阙</div>
    <div class="hint">县治多数未能定位（传本无八到里程可推），图中县点仅附郭；贡赋品类无法统计（原文佚）；剑南道卷帙残甚。静态本地站，无追踪，首访后可离线（Service Worker）。</div>`;
  showPanel();
}
