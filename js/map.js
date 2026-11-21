/* ═══════════ 元和经纬 · 地图（道晕 / 州印 / 附郭县点） ═══════════ */

/* var（非 const）：map 挂到 window，测试页可直取 */
var map = L.map("map", {zoomControl: true, minZoom: 4, maxZoom: 12,
  attributionControl: false, maxBounds: [[17, 88], [46, 136]], maxBoundsViscosity: .6});
map.fitBounds([[30, 100], [41, 122]]);

/* 底图：Esri 地形（绢面滤镜见 css） */
var tileLayer = null, tileErrs = 0;
function setBasemap(){
  if (window.__NOTILES__) return;   /* 测试密封：断言页不拉外网瓦片 */
  tileErrs = 0;
  tileLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
    {maxZoom: 12, maxNativeZoom: 8});
  tileLayer.addTo(map);
  tileLayer.on("tileerror", ()=>{
    tileErrs++;
    if (tileErrs === 3){
      map.removeLayer(tileLayer);
      const n = document.createElement("div");
      n.style.cssText = "position:absolute;left:50%;top:12px;transform:translateX(-50%);z-index:500;" +
        "background:rgba(246,239,220,.95);border:1px solid #8b765a;padding:4px 14px;" +
        "font:11px KaiTi,serif;letter-spacing:3px;color:#8a7f68;pointer-events:none";
      n.textContent = "底图离线 · 标记与数据不受影响";
      document.getElementById("map").appendChild(n);
    }
  });
}
setBasemap();

/* 图层 */
const stateLayer = L.layerGroup().addTo(map);   // 州治印章（常驻）
const fgxLayer = L.layerGroup();                // 附郭县点（zoom≥6 挂载）
const hullLayer = L.layerGroup().addTo(map);    // 道晕（凸包示意）
const stateMarkers = {};                        // daoId -> [markers]
var selDao = null;                              // 当前选中道（var：跨脚本无 TDZ）

/* 州印大小：随属县数缩放（6~17px） */
function sealSize(u){
  return 6 + Math.min((u.xian || []).length || 3, 26) * 0.42;
}

function stateTip(dao, u, permanent){
  const dir = ["right", "left", "bottom", "right"][u._i % 4];
  const off = {right: [sealSize(u) / 2 + 6, 0], left: [-(sealSize(u) / 2 + 6), 0],
               bottom: [0, sealSize(u) / 2 + 4], top: [0, -(sealSize(u) / 2 + 4)]}[dir];
  if (permanent){
    return {content: u.n, opts: {permanent: true, direction: dir, offset: off, className: "fulab"}};
  }
  return {content:
    `<b style="font-family:KaiTi,serif;font-size:14px;letter-spacing:2px">${u.n}</b><br>` +
    `<span style="font-size:10px;letter-spacing:1px;color:#57503f">${dao.name}${u.zhen ? " · " + u.zhen : ""}</span><br>` +
    `<span style="font-size:10px;letter-spacing:1px;color:${u.lost ? "#8a7f68" : "#554e3d"}">` +
    (u.lost ? "卷佚 · 有目无文" : (u.now ? "今 " + u.now : "") +
      ((u.xian || []).length ? " · 管" + u.xian.length + "县" : "")) + "</span>",
    opts: {direction: "top", offset: [0, -6], opacity: .95, className: "ftip"}};
}

function buildStates(){
  stateLayer.clearLayers(); fgxLayer.clearLayers(); hullLayer.clearLayers();
  for (const id in stateMarkers) delete stateMarkers[id];
  YH.daos.forEach(dao => {
    stateMarkers[dao.id] = [];
    dao.states.forEach((u, i) => {
      if (!u.c) return;
      u._i = i;
      const size = sealSize(u);
      const ic = L.divIcon({className: "", iconSize: [size, size],
        html: `<div class="zseal" style="--pc:${dao.color};width:${size}px;height:${size}px" title="${u.n}"></div>`});
      const m = L.marker(u.c, {icon: ic}).addTo(stateLayer);
      m._dao = dao; m._u = u;
      const tip = stateTip(dao, u, false);
      m.bindTooltip(tip.content, tip.opts);
      m.on("click", ()=>{ openState(dao, u); });
      m.on("mouseover", ()=>{ const el = m.getElement() && m.getElement().querySelector(".zseal"); el && el.classList.add("hot"); });
      m.on("mouseout", ()=>{ const el = m.getElement() && m.getElement().querySelector(".zseal"); el && el.classList.remove("hot"); });
      stateMarkers[dao.id].push(m);
      /* 附郭县微点（zoom≥6 展开；坐标=州城，元和志体例附郭与州同治） */
      if (u.fg){
        const xi = L.divIcon({className: "", iconSize: [7, 7],
          html: `<div class="xseal fg-x" style="--pc:${dao.color}" title="${u.fg}"></div>`});
        const xm = L.marker([u.c[0] + 0.035, u.c[1] + 0.045], {icon: xi, zIndexOffset: -200}).addTo(fgxLayer);
        xm._dao = dao; xm._u = u;
        xm.bindTooltip(`<b style="font-family:KaiTi,serif;font-size:13px">${u.fg}</b><br>` +
          `<span style="font-size:10px;letter-spacing:1px;color:#b03a25">附郭 · 与${u.n}同治</span>`,
          {direction: "top", offset: [0, -4], opacity: .95, className: "ftip"});
        xm.on("click", ()=>{ openState(dao, u); });
        stateMarkers[dao.id].push(xm);
      }
    });
    /* 缺卷州份：灰虚圈（有目无文） */
    (dao.lost || []).forEach(l => {
      if (!l.c) return;
      const ic = L.divIcon({className: "", iconSize: [10, 10],
        html: `<div class="zseal lostmark" title="${l.n}"></div>`});
      const m = L.marker(l.c, {icon: ic}).addTo(stateLayer);
      m._dao = dao;
      m.bindTooltip(`<b style="font-family:KaiTi,serif;font-size:13px">${l.n}</b><br>` +
        `<span style="font-size:10px;color:#8a7f68">${l.note || "卷佚"} · 有目无文</span>`,
        {direction: "top", offset: [0, -4], opacity: .9, className: "ftip"});
    });
  });
  applyZoomGates();
  applyDaoDim();
}

/* 凸包（Andrew 单调链）：道晕为治所凸包示意，非考证边界 */
function convexHull(points){
  const pts = [...points].sort((a, b)=>a[0]-b[0]||a[1]-b[1]);
  const cross = (o,a,b)=>(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]);
  const lower = [], upper = [];
  for(const p of pts){
    while(lower.length>=2 && cross(lower[lower.length-2], lower[lower.length-1], p) <= 0) lower.pop();
    lower.push(p);
  }
  for(let i=pts.length-1; i>=0; i--){
    const p = pts[i];
    while(upper.length>=2 && cross(upper[upper.length-2], upper[upper.length-1], p) <= 0) upper.pop();
    upper.push(p);
  }
  lower.pop(); upper.pop();
  return lower.concat(upper);
}
function hullLatLngs(points, pad){
  const hull = convexHull(points);
  if (hull.length < 3) return null;
  const n = hull.length;
  const cLat = hull.reduce((s,p)=>s+p[0],0)/n, cLng = hull.reduce((s,p)=>s+p[1],0)/n;
  return hull.map(p=>[cLat+(p[0]-cLat)*pad, cLng+(p[1]-cLng)*pad]);
}

/* 道晕开关（全部道 / 仅选中道） */
var hullsOn = false;
function drawHulls(){
  hullLayer.clearLayers();
  if (!hullsOn && !selDao) return;
  YH.daos.forEach(dao => {
    if (selDao && dao.id !== selDao) return;
    const pts = dao.states.filter(u=>u.c).map(u=>u.c);
    if (pts.length < 3) return;
    const hull = hullLatLngs(pts, 1.16);
    if (!hull) return;
    L.polygon(hull, {color: dao.color, weight: 2.2, dashArray: "7 6", opacity: .8,
      fillColor: dao.color, fillOpacity: .10, lineCap: "round", interactive: false}).addTo(hullLayer);
    /* 道名标签：晕重心 */
    const lat = hull.reduce((s,p)=>s+p[0],0)/hull.length;
    const lng = hull.reduce((s,p)=>s+p[1],0)/hull.length;
    L.marker([lat, lng], {icon: L.divIcon({className: "", iconSize: [80, 20],
      html: `<div class="dao-lab">${dao.name}</div>`}), interactive: false,
      zIndexOffset: -600}).addTo(hullLayer);
  });
}

/* 缩放分级：附郭县点 zoom≥6 */
function applyZoomGates(){
  const z = map.getZoom();
  if (z >= 6) map.addLayer(fgxLayer); else map.removeLayer(fgxLayer);
  /* zoom≥7：州名常显（同道相邻错向避让） */
  Object.values(stateMarkers).flat().forEach(m => {
    if (!m._u || !m._dao) return;
    m.unbindTooltip();
    const tip = stateTip(m._dao, m._u, z >= 7);
    m.bindTooltip(tip.content, tip.opts);
  });
  applyDaoDim();
}
map.on("zoomend", applyZoomGates);

/* 道选淡出：非选中道的印/点加 .dim */
function applyDaoDim(){
  for (const id in stateMarkers){
    stateMarkers[id].forEach(m => {
      const el = m.getElement && m.getElement();
      if (!el) return;
      const f = el.querySelector(".zseal");
      if (f) f.classList.toggle("dim", !!selDao && id !== selDao);
      const x = el.querySelector(".xseal");
      if (x) x.classList.toggle("dim", !!selDao && id !== selDao);
    });
  }
}

/* 容器未完成布局（尺寸 0）时飞行动画会 NaN——就绪前延迟重试 */
function safeFly(bounds, opts){
  if (map.getSize().x > 40){
    try{ map.flyToBounds(bounds, opts); }
    catch(e){ map.fitBounds(bounds); }
  } else {
    setTimeout(()=>safeFly(bounds, opts), 250);
  }
}
function safeFlyTo(center, zoom, opts){
  if (map.getSize().x > 40){
    try{ map.flyTo(center, zoom, opts); }
    catch(e){ map.setView(center, zoom); }
  } else {
    setTimeout(()=>safeFlyTo(center, zoom, opts), 250);
  }
}

/* 道选择 */
function selectDao(id){
  selDao = id;
  document.body.classList.toggle("seldao", !!id);
  applyDaoDim();
  drawHulls();
  setHullBtn();
  if (typeof highlightRail === "function") highlightRail(id);
  if (id){
    const dao = YH.daos.find(d=>d.id === id);
    if (dao){
      const pts = dao.states.filter(u=>u.c).map(u=>u.c);
      if (pts.length){
        safeFly(L.latLngBounds(pts).pad(.22), {duration: 1.1});
      }
      syncHash("dao=" + id);
    }
  } else {
    syncHash(null);
  }
}

/* 道晕按钮 */
function setHullBtn(){
  const b = document.getElementById("hullbtn");
  if (b) b.classList.toggle("on", hullsOn);
}

/* 舆图：点空白取消道选 */
map.on("click", ()=>{ if (selDao) selectDao(null); });

/* 检索定位州：飞至 + 脉冲环 */
function revealState(daoId, name){
  const dao = YH.daos.find(d=>d.id === daoId);
  if (!dao) return false;
  const u = dao.states.find(x=>x.n === name);
  if (!u || !u.c) return false;
  selectDao(daoId);
  openState(dao, u);
  setTimeout(()=>{
    safeFlyTo(u.c, 7, {duration: 1});
    const ring = L.circleMarker(u.c, {radius: 14, weight: 2.2, color: "#b03a25",
      opacity: .9, fill: false, className: "evring"}).addTo(map);
    setTimeout(()=>map.removeLayer(ring), 3200);
  }, 420);
  return true;
}
