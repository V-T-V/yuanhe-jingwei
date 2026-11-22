/* ═══════════ 元和经纬 · 深链（#dao=guannei&zhou=华州 / #dao=guannei&zhen=京畿观察使 / #search=…） ═══════════
   加载链最末：app.js 已完成 buildStates/railYutu 初始化。 */

(function deeplink(){
  const q = new URLSearchParams(location.hash.replace(/^#/, ""));
  if (![...q.keys()].length) return;
  dismissBoot();
  if (q.get("search")){
    setTimeout(()=>{
      const si = document.getElementById("search");
      si.value = q.get("search");
      si.dispatchEvent(new Event("input"));
      si.focus();
    }, 700);
    return;
  }
  if (q.get("xref")){
    const lv = q.get("xref") === "han" ? "han" : "song";
    setTimeout(()=>openXref(lv), 400);
    return;
  }
  /* 镇视角：#zhen=<镇名>（与 #dao=/#zhou= 同套写回）；州链优先于镇链 */
  if (q.get("zhen") && !q.get("zhou") && typeof ZHEN_GROUPS !== "undefined"){
    if (openZhenView(q.get("zhen"))) return;
  }
  if (q.get("dao")){
    const dao = YH.daos.find(x=>x.id === q.get("dao"));
    if (!dao) return;
    selectDao(dao.id);
    openDao(dao);
    if (q.get("zhou")){
      const u = dao.states.find(x=>x.n === q.get("zhou"));
      if (u) setTimeout(()=>openState(dao, u), 600);
    } else if (q.get("zhen")){
      /* 州+镇并存而州无此名：仍展开镇纲目 */
      railOpenZhen = q.get("zhen");
      railYutu();
    }
  }
})();
