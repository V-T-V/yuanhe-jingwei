/* ═══════════ 元和经纬 · 深链（#dao=guannei&zhou=华州 / #search=…） ═══════════
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
  if (q.get("dao")){
    const dao = YH.daos.find(x=>x.id === q.get("dao"));
    if (!dao) return;
    selectDao(dao.id);
    openDao(dao);
    if (q.get("zhou")){
      const u = dao.states.find(x=>x.n === q.get("zhou"));
      if (u) setTimeout(()=>openState(dao, u), 600);
    }
  }
})();
