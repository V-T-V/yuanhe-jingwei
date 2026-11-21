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
    railOpenZhen = railOpenZhen === el.dataset.zhen ? null : el.dataset.zhen;
    railYutu();
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
