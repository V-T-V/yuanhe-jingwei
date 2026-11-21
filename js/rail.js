/* ═══════════ 元和经纬 · 左列纲目（分镇而读：道—镇—州） ═══════════ */

const rail = document.getElementById("raillist");
const railtitle = document.getElementById("railtitle");
let railOpenZhen = null;

/* 州 → 镇 分组（按道归置，卷序排） */
const ZHEN_GROUPS = (()=>{
  const m = new Map();   // 镇名 -> {key, dao, states:[州名…]}
  YH.daos.forEach(d=>{
    d.states.forEach(u=>{
      const z = u.zhen || "（镇属未详）";
      if (!m.has(z)) m.set(z, {key: z, dao: d, states: []});
      m.get(z).states.push(u.n);
    });
  });
  return m;
})();

function railYutu(){
  const nZhen = ZHEN_GROUPS.size;
  railtitle.innerHTML = `十道四十七镇<small>分镇而读 · 州${ST.s}</small>`;
  let html = "";
  /* 道晕开关 */
  html += `<div class="ri" id="hullbtn" style="border-bottom:1px solid var(--line)">
    <span class="dot" style="box-shadow:inset 0 0 0 1.5px currentColor;color:var(--azur)"></span>
    <span><span class="nm">道晕开关</span><span class="ju">治所凸包示意</span></span></div>`;
  YH.daos.forEach(d=>{
    const zhens = [...ZHEN_GROUPS.values()].filter(g=>g.dao.id === d.id);
    html += `<div class="ri ri-dao" data-dao="${d.id}">
      <span class="dot" style="background:${d.states.length ? d.color : "transparent"};box-shadow:inset 0 0 0 1.5px ${d.color}"></span>
      <span><span class="nm">${d.name}</span><span class="ju">${d.states.length ? d.states.length + "州" + (zhens.length ? " · " + zhens.length + "镇" : "") : "整道卷佚"}</span></span>
      <span class="ct">${d.states.length ? "卷" + (d.states[0].juan || "?") : "—"}</span></div>`;
    zhens.forEach(g=>{
      const open = railOpenZhen === g.key;
      html += `<div class="rsub rzh" data-zhen="${g.key}" data-dao="${d.id}">
        <span style="color:var(--cinnabar-d)">镇</span> ${g.key.replace(/都防御使|节度使|观察使|经略使|防御使/, "")} <span style="color:var(--ink-faint)">(${g.states.length})</span> ${open ? "▾" : "▸"}</div>`;
      if (open){
        g.states.forEach(n=>{
          html += `<div class="rsub" data-dao="${d.id}" data-zhou="${n}">${n}</div>`;
        });
      }
    });
  });
  rail.innerHTML = html;
  rail.querySelectorAll(".ri-dao").forEach(el=>el.onclick=()=>{
    selectDao(el.dataset.dao);
    openDao(YH.daos.find(d=>d.id === el.dataset.dao));
  });
  rail.querySelectorAll(".rzh").forEach(el=>el.onclick=()=>{
    const opening = railOpenZhen !== el.dataset.zhen;
    railOpenZhen = opening ? el.dataset.zhen : null;
    railYutu();
    /* 深链写回：展开镇即入 URL（刷新/分享可复原），收起回落道链 */
    syncHash(opening
      ? "dao=" + el.dataset.dao + "&zhen=" + encodeURIComponent(el.dataset.zhen)
      : "dao=" + el.dataset.dao);
  });
  rail.querySelectorAll(".rsub[data-zhou]").forEach(el=>el.onclick=()=>{
    const dao = YH.daos.find(d=>d.id === el.dataset.dao);
    const u = dao && dao.states.find(x=>x.n === el.dataset.zhou);
    if (u) openState(dao, u);
  });
  const hb = rail.querySelector("#hullbtn");
  if (hb) hb.onclick = ()=>{ hullsOn = !hullsOn; drawHulls(); setHullBtn(); };
  setHullBtn();
  highlightRail(selDao);
}

function highlightRail(daoId){
  rail.querySelectorAll(".ri-dao").forEach(el=>
    el.classList.toggle("on", el.dataset.dao === daoId));
}

/* ═══════════ 镇视角（#zhen=<镇名> 直达：纲目展开 + 州列聚焦 + 写回） ═══════════ */
function openZhenView(key){
  const g = ZHEN_GROUPS.get(key);
  if (!g) return false;
  railOpenZhen = key;
  railYutu();
  selectDao(g.dao.id);                       /* 道高亮/淡出（其 hash 随后覆写为镇链） */
  const members = g.states.map(n=>g.dao.states.find(s=>s.n === n)).filter(Boolean);
  const pts = members.filter(u=>u.c).map(u=>u.c);
  if (pts.length > 1) setTimeout(()=>safeFly(L.latLngBounds(pts).pad(.3), {duration: 1.1}), 350);
  else if (pts.length === 1) setTimeout(()=>safeFlyTo(pts[0], 7, {duration: 1.1}), 350);
  vset(key.replace(/都防御使|节度使|观察使|经略使|防御使/, ""), "镇");
  const nx = members.reduce((s, u)=>s + (u.xian || []).length, 0);
  pbody.innerHTML = `
    <div class="p-kicker">${g.dao.name} · 元和四十七镇体制</div>
    <div class="p-ju" style="font-size:19px">${key}</div>
    <div class="stat-strip" style="margin:0 0 12px">
      <div class="st"><b>${members.length}</b><span>领州</span></div>
      <div class="st"><b>${nx}</b><span>管县（名录）</span></div>
    </div>
    <div class="p-cap">所领州府</div>
    <ul class="ful">${members.map(u=>`
      <li data-n="${u.n}">
        <span class="fn">${u.n}</span>
        <span class="fnow">${u.now ? "今" + u.now : ""}</span>
        <span class="fct">${(u.xian || []).length ? u.xian.length + "县" : ""}</span>
        <span class="arrow">➤</span></li>`).join("")}</ul>
    <div class="hint">镇视角深链：#zhen=${encodeURIComponent(key)}（写回地址栏，刷新/分享可复原）。点州名入其详情（沿革 · 八到/贡赋佚注 · 辖县）。</div>`;
  pbody.querySelectorAll(".ful li[data-n]").forEach(li=>li.onclick=()=>{
    const u = g.dao.states.find(x=>x.n === li.dataset.n);
    if (u) openState(g.dao, u);
  });
  syncHash("dao=" + g.dao.id + "&zhen=" + encodeURIComponent(key));
  showPanel();
  return true;
}
