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

/* ═══════════ 历代对照 · 互查桥（唐宋 data/xref_hy.js · 汉唐回程 data/xrev_hz.js） ═══════════ */
function xrefLink(m){
  return "../TPHY/#dao=" + m.id + "&zhou=" + encodeURIComponent(m.n);
}
let xlevel = "song";
function openXref(level){
  if (level) xlevel = level;
  if (xlevel === "han") return openXrev();
  vset("历代对照", "桥");
  const M = YHXREF.meta;
  const badges = m => {
    let b = "";
    if (m.kind === "同治异名") b += `<span class="xb xb-r">改名</span>`;
    if (m.sj) b += `<span class="xb xb-s">${m.sj}</span>`;
    if (m.yili) b += `<span class="xb xb-y">异隶</span>`;
    return b;
  };
  /* 按道分组的对照表 */
  const groups = YHXREF.byDao.map(g=>{
    const rows = YHXREF.rows.filter(r=>r.dao === g.dao).map(r=>{
      if (r.m){
        return `<li data-dao="${g.id}" data-zhou="${r.n}">
          <span class="fn">${r.n}</span>
          <span class="fnow">${r.now ? "今" + r.now : ""}</span>
          <span class="fct">${r.m.n}${badges(r.m)}</span>
          <a class="xgo" href="${xrefLink(r.m)}" target="_blank" rel="noopener" title="于寰宇经纬开此条">↗</a></li>`;
      }
      return `<li class="lostrow">
          <span class="fn" style="color:var(--ink-faint)">${r.n}</span>
          <span class="fnow">${r.why}</span></li>`;
    }).join("");
    const head = g.dao === "淮南道" ? `${g.dao}（唐整道卷佚，桥无所出）`
      : `${g.dao} <span style="color:var(--ink-faint)">·同名 ${g.same} ·改名 ${g.renamed} ·无对应 ${g.unmatched}${g.yili ? " ·异隶 " + g.yili : ""}${g.sj ? " ·升降 " + g.sj : ""}</span>`;
    return `<div class="p-cap" style="margin-top:10px">${head}</div><ul class="ful">${rows}</ul>`;
  }).join("");
  /* 样例：元和原文句 × 寰宇对应条目 */
  const samples = YHXREF.samples.map((s,i)=>`
    <div class="xsamp">
      <div class="xs-head"><b>唐 · ${s.tn}</b>${s.kind === "同治异名" ? '<span class="xb xb-r">改名</span>' : ""}${s.sj ? `<span class="xb xb-s">${s.sj}</span>` : ""}${s.yili ? '<span class="xb xb-y">异隶</span>' : ""}</div>
      <div class="xs-q">「${s.tq}」<span class="xs-src">——元和郡县图志</span></div>
      <div class="xs-head" style="margin-top:6px"><b>宋 · ${s.sn}</b>
        <a class="xgo" href="../TPHY/#dao=${s.sid}&zhou=${encodeURIComponent(s.sn)}" target="_blank" rel="noopener">↗寰宇</a></div>
      <div class="xs-q">「${s.sq}」<span class="xs-src">——太平寰宇记</span></div>
    </div>`).join("");
  pbody.innerHTML = `
    <div class="p-kicker">元和（唐·813）× 寰宇（宋·977）州府对照 · 凡计数出自 tools/build_xref_hy.py</div>
    <div class="tabbar-x">
      <button class="tbx on">唐→宋（${M.matched}/${M.tang_states}）</button>
      <button class="tbx" data-x="han">汉→唐（${YHXREV.meta.matched_pairs}/${YHXREV.meta.han_juns}）</button>
    </div>
    <div class="stat-strip" style="margin:2px 0 10px">
      <div class="st"><b>${M.tang_states}</b><span>唐州府</span></div>
      <div class="st"><b>${M.matched}</b><span>得宋对应</span></div>
      <div class="st"><b>${M.same_name}</b><span>同名</span></div>
      <div class="st"><b>${M.renamed}</b><span>同治异名</span></div>
      <div class="st"><b>${M.yili}</b><span>同州异隶</span></div>
      <div class="st"><b>${M.unmatched}</b><span>无对应</span></div>
    </div>
    <div class="p-cap">样例 · 元和原文 × 寰宇条目</div>
    ${samples}
    <div class="hint">同名=去府/州/军/监尾后同名且地理今名相合；同治异名=治所同今地而名异（唐宋间升降改置，如京兆府↔雍州、汴州↔開封府、恒州↔鎮州）。异隶三源并注：唐方镇移隶回流（濠/安/黄/蕲）、宋分道改制（渝/成）、寰宇站个别道标出入（信/昌，地理今名俱合）。同名异地（唐渭州≠宋渭州、河北景州≠岭南景州）与寰宇佚卷（江南西道卷113–119）所失诸州，如实计「无对应」，不以似是者充数。</div>
    <div class="p-cap">全表 · 按唐道分组</div>
    ${groups}
    <div class="hint">↗ 于姊妹站「寰宇经纬」打开对应条目（相对路径 ../TPHY/——需父目录同根服务，见 README）。宋侧另有 ${M.song_new} 条（军监新置、四夷、唐佚之州）无唐州对应，不计入唐侧。</div>`;
  bindXrefTabs();
  pbody.querySelectorAll(".ful li[data-zhou]").forEach(li=>li.onclick=()=>{
    const dao = YH.daos.find(d=>d.id === li.dataset.dao);
    const u = dao && dao.states.find(x=>x.n === li.dataset.zhou);
    if (u) openState(dao, u);
  });
  pbody.querySelectorAll("a.xgo").forEach(a=>a.onclick=e=>e.stopPropagation());
  showPanel();
}

function bindXrefTabs(){
  pbody.querySelectorAll(".tabbar-x .tbx").forEach(b=>b.onclick=()=>{
    if (b.dataset.x) openXref(b.dataset.x);
  });
}

/* ── 汉唐回程（data/xrev_hz.js，build_xrev_hz.py 反转汉志桥；HSDZ 只读） ── */
function openXrev(){
  vset("历代对照", "桥");
  const M = YHXREV.meta;
  const famBadge = h =>
    h.fam === "同名同城" ? '<span class="xb xb-s">同名同城</span>'
    : h.fam === "迁治" ? '<span class="xb xb-r">迁治</span>'
    : '<span class="xb xb-y">承名</span>';
  const groups = YHXREV.byDao.map(g=>{
    const rows = YHXREV.rows.filter(r=>r.dao === g.dao).map(r=>{
      if (r.han && r.han.length){
        const hans = r.han.map(h=>
          `<a class="xgo" style="margin-left:0" href="../HSDZ/#bu=${h.buId}&jun=${encodeURIComponent(h.n)}" target="_blank" rel="noopener" title="于汉志经纬开此郡">${h.n}</a>${famBadge(h)}`).join(" · ");
        return `<li data-dao="${g.id}" data-zhou="${r.n}">
          <span class="fn">${r.n}</span>
          <span class="fnow">${r.now ? "今" + r.now : ""}</span>
          <span class="fct">${hans}</span></li>`;
      }
      return `<li class="lostrow">
          <span class="fn" style="color:var(--ink-faint)">${r.n}</span>
          <span class="fnow">汉志无同城对应（如实计）</span></li>`;
    }).join("");
    const head = g.dao === "淮南道" ? `${g.dao}（唐整道卷佚，桥无所出）`
      : `${g.dao} <span style="color:var(--ink-faint)">·得汉郡 ${g.withHan}${g["同名同城"] ? " ·同名同城 " + g["同名同城"] : ""}${g["承名"] ? " ·承名 " + g["承名"] : ""}${g["迁治"] ? " ·迁治 " + g["迁治"] : ""} ·无对应 ${g.total - g.withHan}</span>`;
    return `<div class="p-cap" style="margin-top:10px">${head}</div><ul class="ful">${rows}</ul>`;
  }).join("");
  const samples = YHXREV.samples.map(s=>`
    <div class="xsamp">
      <div class="xs-head"><b>汉 · ${s.hn}</b>${s.fam === "同名同城" ? '<span class="xb xb-s">同名同城</span>' : s.fam === "迁治" ? '<span class="xb xb-r">迁治</span>' : '<span class="xb xb-y">承名</span>'}
        <a class="xgo" href="../HSDZ/#bu=${s.buId}&jun=${encodeURIComponent(s.hn)}" target="_blank" rel="noopener">↗汉志</a></div>
      <div class="xs-q">「${s.hq}」<span class="xs-src">——汉书地理志</span></div>
      <div class="xs-head" style="margin-top:6px"><b>唐 · ${s.tn}</b></div>
      <div class="xs-q">「${s.tq}」<span class="xs-src">——元和郡县图志</span></div>
    </div>`).join("");
  const eras = YHXREV.eras.map(e=>`
    <div class="eracard">
      <div class="xs-head"><b>${e.title}</b> <span style="font-size:10.5px;color:var(--ink-faint)">今${e.now} · 四朝同地，一站一点到明</span></div>
      <div class="erastops">${e.stops.map(st=>
        `<a class="estop" href="${st.href}" ${st.ext ? 'target="_blank" rel="noopener"' : ""}><b>${st.dyn}</b>${st.n}<small>${st.site}</small></a>`).join('<span class="eraarrow">→</span>')}</div>
    </div>`).join("");
  pbody.innerHTML = `
    <div class="p-kicker">汉志（汉书地理志）× 元和（唐·813）郡州对照 · 回程桥，凡计数出自 tools/build_xrev_hz.py（对汉志侧 52 全等）</div>
    <div class="tabbar-x">
      <button class="tbx" data-x="song">唐→宋（${YHXREF.meta.matched}/${YHXREF.meta.tang_states}）</button>
      <button class="tbx on">汉→唐（${M.matched_pairs}/${M.han_juns}）</button>
    </div>
    <div class="stat-strip" style="margin:2px 0 10px">
      <div class="st"><b>${M.han_juns}</b><span>汉郡（汉志侧）</span></div>
      <div class="st"><b>${M.tang_states}</b><span>唐州府</span></div>
      <div class="st"><b>${M.matched_pairs}</b><span>得汉郡对应</span></div>
      <div class="st"><b>${M.same_name}</b><span>同名同城</span></div>
      <div class="st"><b>${M.chengming}</b><span>承名</span></div>
      <div class="st"><b>${M.qianyi}</b><span>迁治</span></div>
    </div>
    <div class="p-cap">四朝同地 · 汉唐宋明一路点到底（彩蛋）</div>
    ${eras}
    <div class="p-cap">样例 · 汉志句 × 元和句</div>
    ${samples}
    <div class="hint">回程视角：汉志侧桥（HSDZ build_xref_yh.py 判 103 汉郡 ↔ 227 唐州，得对应 52）自唐州反转重组——同名同城（如京兆尹→京兆府）、承名（唐州承汉郡之名而治同城/同地，如蜀郡→成都府、弘農郡→虢州）、迁治各为一档；唐州无汉对应 ${M.tang_without_han}（汉志侧另有 51 郡无唐对应，两侧如实并计）。汉志为前汉书地理志郡国世界，↗ 深链 ../HSDZ/#bu=&lt;部域id&gt;&amp;jun=&lt;郡名&gt;（实测其前端格式，逐条对 site_data 校验存在）。</div>
    <div class="p-cap">全表 · 按唐道分组</div>
    ${groups}
    <div class="hint">↗郡名 于「汉志经纬」开对应郡卡（相对路径 ../HSDZ/，父目录同根服务）。唐行点击回本站州卡。</div>`;
  bindXrefTabs();
  pbody.querySelectorAll(".ful li[data-zhou]").forEach(li=>li.onclick=()=>{
    const dao = YH.daos.find(d=>d.id === li.dataset.dao);
    const u = dao && dao.states.find(x=>x.n === li.dataset.zhou);
    if (u) openState(dao, u);
  });
  pbody.querySelectorAll("a.xgo").forEach(a=>a.onclick=e=>e.stopPropagation());
  /* 彩蛋唐站内链：不走 hash 导航（深链 IIFE 不重跑），直接开州卡 */
  pbody.querySelectorAll("a.estop:not([target])").forEach(a=>a.onclick=e=>{
    e.preventDefault();
    e.stopPropagation();
    const q = new URLSearchParams(a.getAttribute("href").replace(/^#/, ""));
    const dao = YH.daos.find(d=>d.id === q.get("dao"));
    const u = dao && dao.states.find(x=>x.n === q.get("zhou"));
    if (u) openState(dao, u);
  });
  showPanel();
}

/* ═══════════ 州县导出（与 tools/export_data.py 同口径：CSV BOM / KML / GeoJSON） ═══════════ */
function exportRows(){
  /* 州表：道/镇/州府/类/治所今地(依据)/纬/经/src/置信/卷/管县/坐标注记 */
  const zhou = [];
  YH.daos.forEach(d=>d.states.forEach(u=>{
    zhou.push([d.name, u.zhen || "", u.n, u.n.endsWith("府") ? "府" : "州",
      u.now || "", (u.c ? u.c[0] : ""), (u.c ? u.c[1] : ""), u.src || "derived",
      u.conf === 2 ? "推" : "确", u.juan || "", (u.xian || []).length,
      "整编今地坐标（非考古定位）"]);
  }));
  const xian = [];
  YH.daos.forEach(d=>d.states.forEach(u=>(u.xian || []).forEach((x, i)=>{
    xian.push([d.name, u.n, x, i === 0 ? "附郭" : "属县",
      i === 0 ? "与州治同治（" + (u.now || "") + "）" : "名录存真，治所未定位"]);
  })));
  return {zhou, xian};
}
function dlBlob(content, mime, fname){
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([content], {type: mime}));
  a.download = fname;
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href), 3000);
}
function csvOf(rows){
  const NL = String.fromCharCode(10), BOM = String.fromCharCode(0xFEFF);
  return BOM + rows.map(r=>r.join(",")).join(NL);
}
function openExport(){
  vset("导出", "集");
  const E = exportRows();
  const M = YHXREF ? YHXREF.meta.matched : "";
  pbody.innerHTML = `
    <div class="p-kicker">古今对照导出 · 与 tools/export_data.py 同口径（${E.zhou.length} 州 / ${E.xian.length} 县）</div>
    <div class="readrow" style="flex-direction:column;align-items:stretch;gap:8px">
      <button class="readfull" id="ex-zcsv">⤓ 州治对照 CSV（${E.zhou.length} 行 · 带 BOM）</button>
      <button class="readfull" id="ex-xcsv">⤓ 县名录 CSV（${E.xian.length} 行 · 带 BOM）</button>
      <button class="readfull" id="ex-kml">⤓ 州治点位 KML（Google Earth）</button>
      <button class="readfull" id="ex-geo">⤓ 州治点位 GeoJSON</button>
    </div>
    <div class="p-cap">字段口径</div>
    <div class="hint">州表：道、镇、州府、类（府/州）、治所今地（即今名依据）、纬度、经度、src、置信（确/推）、卷、管县数、坐标注记。县表：道、州、县、附郭/属县、附注。坐标为依唐代政区地理整编之今地（src:derived，非考古定位），附郭县与州同治，余县但存名录不做定位臆测——导出中如实注明。唐宋对照另见「唐宋」页签（匹配 ${M} 州）。</div>`;
  pbody.querySelector("#ex-zcsv").onclick = ()=>{
    const {zhou} = exportRows();
    zhou.unshift(["道","镇","州府","类","治所今地","纬度","经度","src","置信","卷","管县数","坐标注记"]);
    dlBlob(csvOf(zhou), "text/csv;charset=utf-8", "元和经纬-州治对照.csv");
  };
  pbody.querySelector("#ex-xcsv").onclick = ()=>{
    const {xian} = exportRows();
    xian.unshift(["道","州","县","附郭/属县","附注"]);
    dlBlob(csvOf(xian), "text/csv;charset=utf-8", "元和经纬-县名录.csv");
  };
  pbody.querySelector("#ex-kml").onclick = ()=>{
    let pins = "";
    YH.daos.forEach(d=>d.states.forEach(u=>{
      if (!u.c) return;
      pins += `<Placemark><name>${u.n}</name><description>${d.name}${u.zhen ? " · " + u.zhen : ""}${u.now ? " 今" + u.now : ""}（src:derived 置信${u.conf === 2 ? "推" : "确"}）</description><Point><coordinates>${u.c[1]},${u.c[0]},0</coordinates></Point></Placemark>`;
    }));
    const kml = `<?xml version="1.0" encoding="UTF-8"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>元和经纬·州治点位（整编今地坐标）</name>${pins}</Document></kml>`;
    dlBlob(kml, "application/vnd.google-earth.kml+xml", "元和经纬-州治点位.kml");
  };
  pbody.querySelector("#ex-geo").onclick = ()=>{
    const feats = [];
    YH.daos.forEach(d=>d.states.forEach(u=>{
      if (!u.c) return;
      feats.push({type: "Feature", geometry: {type: "Point", coordinates: [u.c[1], u.c[0]]},
        properties: {名: u.n, 类: u.n.endsWith("府") ? "府" : "州", 道: d.name, 镇: u.zhen || "",
          今地: u.now || "", src: u.src || "derived", 置信: u.conf === 2 ? "推" : "确",
          卷: u.juan || "", 管县: (u.xian || []).length, 坐标注记: "整编今地坐标（非考古定位）"}});
    }));
    dlBlob(JSON.stringify({type: "FeatureCollection", features: feats}), "application/geo+json", "元和经纬-州治点位.geojson");
  };
  showPanel();
}
