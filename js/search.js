/* ═══════════ 元和经纬 · 检索（道·镇·州·县） ═══════════ */

const IDX = (()=>{
  const a = [];
  YH.daos.forEach(d=>{
    if (d.states.length) a.push({t: d.name, k: "道", ctx: d.states.length + "州", dao: d.id});
    d.states.forEach(u=>{
      a.push({t: u.n, k: "州", ctx: d.name + (u.zhen ? " · " + u.zhen : ""), dao: d.id, zhou: u.n});
      (u.xian || []).forEach(x=>{
        a.push({t: x, k: "县", ctx: d.name + " · " + u.n, dao: d.id, zhou: u.n});
      });
    });
  });
  YH.zhens.forEach(z=>{
    if (z.states && z.states.length)
      a.push({t: z.n, k: "镇", ctx: z.dao || ""});
  });
  return a;
})();

const sinput = document.getElementById("search"), sres = document.getElementById("sresults");

function searchHits(q){
  return IDX.filter(x=>x.t.includes(q))
    .sort((a, b)=>(a.t === q ? -1 : 0) - (b.t === q ? -1 : 0) ||
                   a.t.indexOf(q) - b.t.indexOf(q) || a.t.length - b.t.length)
    .slice(0, 14);
}
function renderHits(hits, q){
  const escQ = q.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const ftRow = `<div class="sr ftall" id="ftall">📖 在全书原文中检索「${escQ}」…</div>`;
  if (!hits.length){
    sres.innerHTML = `<div class="none">名录未见「${escQ}」</div>` + ftRow;
  } else {
    sres.innerHTML = hits.map((h, i)=>
      `<div class="sr" data-i="${i}"><span class="tag t${h.k}">${h.k}</span>` +
      `<span>${h.t}</span><span class="ctx">${h.ctx}</span></div>`).join("") + ftRow;
    sres.querySelectorAll(".sr[data-i]").forEach(el=>
      el.onclick = ()=>goHit(hits[+el.dataset.i]));
  }
  sres.classList.add("open");
  const fa = sres.querySelector("#ftall");
  if (fa) fa.onclick = ()=>ftRun(q);
}
function goHit(h){
  sinput.value = h.t;
  sres.classList.remove("open");
  if (h.k === "道"){
    selectDao(h.dao);
    openDao(YH.daos.find(d=>d.id === h.dao));
  } else if (h.k === "州" || (h.k === "县" && h.zhou && revealState(h.dao, h.zhou))){
    if (h.k === "州") revealState(h.dao, h.zhou);
  } else if (h.k === "镇"){
    railOpenZhen = h.t;
    if (typeof railYutu === "function") railYutu();
  } else {
    /* 县：州未见（卷佚州份等）——检索面板提示 */
    const dao = YH.daos.find(d=>d.id === h.dao);
    if (dao) openDao(dao);
  }
}

/* 输入防抖：IME 组合期不逐键重建 */
let _sT = null;
sinput.addEventListener("input", ()=>{
  const q = sinput.value.trim();
  if (!q){ clearTimeout(_sT); sres.classList.remove("open"); return; }
  clearTimeout(_sT);
  _sT = setTimeout(()=>renderHits(searchHits(q), q), 110);
});
/* 回车直达第一条 */
sinput.addEventListener("keydown", e=>{
  if (e.key !== "Enter") return;
  const q = sinput.value.trim();
  if (!q) return;
  const hits = searchHits(q);
  if (hits.length) goHit(hits[0]);
});
document.addEventListener("click", e=>{
  if (!e.target.closest("#searchwrap")) sres.classList.remove("open");
});
