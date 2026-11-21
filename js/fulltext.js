/* ═══════════ 元和经纬 · 全书全文检索（懒加载分片 + Worker 扫描） ═══════════ */

const FT_KEYS = YH.daos.filter(d=>d.states.length).map(d=>d.id).concat(["juanshou"]);
let _ftWorker = null, _ftDocs = null;

function ftProgress(onDone){
  /* 载全部分片 → docs 列表（道内逐州成篇） */
  let pending = FT_KEYS.slice();
  const step = ()=>{
    if (!pending.length){ onDone(); return; }
    const k = pending.shift();
    loadTextFile(k, ()=>step());
  };
  step();
}

function ftCollectDocs(){
  const docs = [];
  FT_KEYS.forEach(k=>{
    const bag = YHTEXT[k];
    if (!bag) return;
    if (k === "juanshou"){
      Object.keys(bag).forEach(t=>docs.push({key: "juanshou", title: t,
        kicker: "元和郡县图志 · 卷首", text: bag[t]}));
      return;
    }
    const dao = YH.daos.find(d=>d.id === k);
    Object.keys(bag).forEach(st=>{
      if (st === "__dao__") return;
      const u = dao.states.find(x=>x.n === st);
      docs.push({key: k, title: st,
        kicker: "元和郡县图志 · " + dao.name + (u && u.juan ? " · 卷" + u.juan : ""),
        zhou: st, text: bag[st]});
    });
  });
  return docs;
}

function ftRun(q){
  vset("全书检索", "全文");
  pbody.innerHTML = `
    <div class="p-kicker">全书全文检索 · 「${escT(q)}」</div>
    <div class="hint" id="ftprog">正在加载全书原文分片…（首查约数秒，此后缓存）</div>
    <div id="ftresults"></div>`;
  showPanel();
  ftProgress(()=>{
    _ftDocs = ftCollectDocs();
    const prog = document.getElementById("ftprog");
    if (prog) prog.textContent = `全书 ${_ftDocs.length} 篇已就绪，Worker 扫描中…`;
    if (!_ftWorker){
      try{
        _ftWorker = new Worker("js/ftworker.js");
      }catch(e){
        _ftWorker = null;
      }
    }
    const render = results=>{
      if (prog) prog.textContent = results.length
        ? `「${escT(q)}」全书命中 ${results.length} 篇（按命中数排序）`
        : `「${escT(q)}」全书未见`;
      const box = document.getElementById("ftresults");
      if (!box) return;
      box.innerHTML = results.map((r, i)=>
        `<div class="ftrow" data-i="${i}">
          <div class="fth">${r.title} <span style="font-size:10px;color:var(--cinnabar-d)">${r.n}处</span>
            <span style="font-size:10px;color:var(--ink-faint);margin-left:6px">${r.kicker}</span></div>
          <div class="ftsnip">${r.snip}</div></div>`).join("");
      box.querySelectorAll(".ftrow").forEach(el=>{
        el.onclick = ()=>{
          const r = results[+el.dataset.i];
          if (r.key === "juanshou"){
            renderText._q = q;
            openJuanshou(JUANSHOU.indexOf(r.title));
          } else {
            const dao = YH.daos.find(d=>d.id === r.key);
            const u = dao && dao.states.find(x=>x.n === r.title);
            if (u) openStateText(dao, u, q);
          }
        };
      });
    };
    if (_ftWorker){
      _ftWorker.onmessage = e=>{ if (e.data.q === q) render(e.data.results); };
      _ftWorker.postMessage({q: q, docs: _ftDocs});
    } else {
      /* Worker 不可用（file:// 等）——主线程同核扫描 */
      const results = _ftDocs.map(d=>({key: d.key, title: d.title, kicker: d.kicker,
        n: countHits(d.text, q), snip: ftSnippet(d.text, q)}))
        .filter(r=>r.n > 0).sort((a, b)=>b.n - a.n).slice(0, 60);
      render(results);
    }
  });
}
