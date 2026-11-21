/* ═══════════ 元和经纬 · 三维形胜（MapLibre 真地形） ═══════════
   州治圆点立于山川：大小随属县数，色随道；沿革文柱立文量大州（yt≥1200 字，57 州）。
   柱高 = log(条目文量) 映射 0.4–5.0 km（示意尺度，非实测）；文量不满阈值者不立柱——
   卷帙残佚之实，不以矮柱充数。沙箱无 WebGL 时 window.YH3D 钩直验数据与交互。 */

var map3d = null;

(function(){
  /* ── 沿革文柱（数据与交互逻辑独立于地图——无 WebGL 亦可验） ── */
  const YT_MIN = 1200;      /* 文柱门槛：条目文量字数（分布实测：中位 768 / 最大 10,162，57 州入柱） */
  const H_LO = 400, H_HI = 5000;   /* 柱高区间（m，log 示意尺度） */

  function ring(lng, lat, r){
    const pts = [];
    for (let i = 0; i <= 6; i++){
      const a = Math.PI * 2 * i / 6;
      pts.push([lng + r * Math.cos(a), lat + r * Math.sin(a) * .82]);
    }
    return [[pts]];
  }
  function pillarStates(){
    const out = [];
    (window.YH ? YH.daos : []).forEach(d => d.states.forEach(u => {
      if (u.c && (u.yt || 0) >= YT_MIN) out.push([d, u]);
    }));
    return out;
  }
  function pillarGeo(){
    const zs = pillarStates();
    const lo = Math.log(YT_MIN);
    const hi = Math.log(Math.max.apply(null, zs.map(p => p[1].yt)));
    return {type: "FeatureCollection", features: zs.map(([d, u]) => {
      const h = Math.round(H_LO + (H_HI - H_LO) * (hi > lo ? (Math.log(u.yt) - lo) / (hi - lo) : .5));
      return {type: "Feature",
        geometry: {type: "Polygon", coordinates: ring(u.c[1], u.c[0], .055)},
        properties: {n: u.n, dao: d.name, daoId: d.id, now: u.now || "", zhen: u.zhen || "",
          juan: u.juan || "", yan: u.yan || "", yt: u.yt, h: h, lng: u.c[1], lat: u.c[0]}};
    })};
  }

  /* 柱卡（DOM 直写——无地图亦可用）：文量/柱高依据 + 沿革节引 + ⟩ 入 2D 州卡 */
  let pillarOn = true;
  function openPillar(p){
    const card = document.getElementById("pillarcard");
    if (!card) return false;
    card.innerHTML =
      `<h3>${p.n}</h3>` +
      `<div class="m">${p.dao}${p.zhen ? " · " + p.zhen : ""}${p.juan ? " · 卷" + p.juan : ""} · 今${p.now || "?"}</div>` +
      `<div class="m">文柱 ${(p.h / 1000).toFixed(1)} km —— 条目文量 ${p.yt} 字（log 示意尺度，非实测）</div>` +
      `<div class="x">${(p.yan || "").slice(0, 120)}……</div>` +
      `<a class="go2d" href="index.html#dao=${p.daoId}&zhou=${encodeURIComponent(p.n)}">⟩ 入 2D 州卡</a>`;
    card.style.display = "block";
    if (map3d && p.lng != null){
      try{ map3d.flyTo({center: [p.lng, p.lat], zoom: Math.max(map3d.getZoom(), 6.2), duration: 1.2}); }catch(e){}
    }
    return true;
  }
  function setPillarOn(on){
    pillarOn = !!on;
    if (map3d && map3d.getLayer("yh-pillar")){
      try{ map3d.setLayoutProperty("yh-pillar", "visibility", pillarOn ? "visible" : "none"); }catch(e){}
    }
    const b = document.getElementById("pillbtn");
    if (b) b.textContent = pillarOn ? "◧ 文柱 ✓" : "◧ 文柱";
    return pillarOn;
  }

  const el = document.getElementById("map3d");
  const noMap = (msg) => {
    if (el) el.innerHTML =
      `<div style='padding:40px;font:14px KaiTi,serif;letter-spacing:2px'>${msg}` +
      `——<a href='index.html' style='color:#b03a25'>回二维舆图</a></div>`;
  };
  const mapOk = !!window.maplibregl && maplibregl.supported && maplibregl.supported();

  if (!window.maplibregl){
    noMap("三维组件未载入（vendor/maplibre-gl.js）");
  } else if (!mapOk){
    noMap("此环境不支持 WebGL");
  }

  /* 文柱开关（无地图环境亦渲染按钮，交互可验） */
  const vhost = document.getElementById("views3d");
  if (vhost){
    const btn = document.createElement("button");
    btn.id = "pillbtn";
    btn.textContent = "◧ 文柱 ✓";
    btn.title = "沿革文柱：条目文量 ≥" + YT_MIN + " 字的 " + pillarStates().length +
      " 州立柱，柱高随文量（log 示意尺度）；不满阈值者不立柱（卷帙残佚之实）";
    btn.onclick = () => setPillarOn(!pillarOn);
    vhost.appendChild(btn);
  }

  /* 沙箱/冒烟钩（无 WebGL 或无头环境：数据与卡逻辑仍可验，不假绿） */
  window.YH3D = {
    mapOk: mapOk, YT_MIN: YT_MIN, pillarGeo: pillarGeo, openPillar: openPillar,
    setPillarOn: setPillarOn, isPillarOn: () => pillarOn,
    pillarCount: () => (map3d && map3d.getSource("pillars")
      ? map3d.getSource("pillars")._data.features.length : pillarGeo().features.length),
  };

  if (!mapOk) return;

  maplibregl.accessToken = "";
  map3d = new maplibregl.Map({
    container: "map3d",
    style: {
      version: 8,
      sources: {
        img: {
          type: "raster",
          tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
          tileSize: 256, maxzoom: 12,
          attribution: "Esri"
        },
        dem: {
          type: "raster-dem",
          tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
          encoding: "terrarium", tileSize: 256, maxzoom: 13
        }
      },
      layers: [
        {id: "bg", type: "background", paint: {"background-color": "#e8dcb9"}},
        {id: "img", type: "raster", source: "img", paint: {"raster-saturation": -0.4, "raster-brightness": 0.95}}
      ]
    },
    center: [108, 35], zoom: 3.6, pitch: 42, bearing: -18,
    maxBounds: [[80, 15], [140, 48]],
    attributionControl: false, antialias: true
  });
  map3d.addControl(new maplibregl.NavigationControl({visualizePitch: true}), "top-right");
  map3d.on("load", () => {
    map3d.setTerrain({source: "dem", exaggeration: 1.35});
    /* 州点：GeoJSON 由 site_data 生成 */
    const feats = [];
    YH.daos.forEach(d => {
      d.states.forEach(u => {
        if (!u.c) return;
        feats.push({type: "Feature",
          geometry: {type: "Point", coordinates: [u.c[1], u.c[0]]},
          properties: {n: u.n, dao: d.name, color: d.color,
            xian: (u.xian || []).length, now: u.now || "", zhen: u.zhen || ""}});
      });
    });
    map3d.addSource("states", {type: "geojson", data: {type: "FeatureCollection", features: feats}});
    map3d.addLayer({
      id: "states-halo", type: "circle", source: "states",
      paint: {"circle-radius": ["interpolate", ["linear"], ["get", "xian"], 0, 5, 26, 16],
              "circle-color": ["get", "color"], "circle-opacity": 0.18}
    });
    map3d.addLayer({
      id: "states-dot", type: "circle", source: "states",
      paint: {"circle-radius": ["interpolate", ["linear"], ["get", "xian"], 0, 3.5, 26, 10],
              "circle-color": ["get", "color"],
              "circle-stroke-width": 1.2, "circle-stroke-color": "#f6efdc"}
    });
    /* 沿革文柱（六棱 fill-extrusion，青绿系随高渐深）——插于 states-halo 之前，州点覆于柱顶 */
    map3d.addSource("pillars", {type: "geojson", data: pillarGeo()});
    map3d.addLayer({
      id: "yh-pillar", type: "fill-extrusion", source: "pillars",
      paint: {
        "fill-extrusion-height": ["get", "h"],
        "fill-extrusion-base": 0,
        "fill-extrusion-opacity": .58,
        "fill-extrusion-color": ["interpolate", ["linear"], ["get", "h"],
          400, "#9db8a5", 2200, "#4a8a78", 5000, "#1f4d5c"],
      }
    }, "states-halo");
    map3d.on("click", "yh-pillar", e => openPillar(e.features[0].properties));
    map3d.on("mouseenter", "yh-pillar", () => { map3d.getCanvas().style.cursor = "pointer"; });
    map3d.on("mouseleave", "yh-pillar", () => { map3d.getCanvas().style.cursor = ""; });
    const popup = new maplibregl.Popup({closeButton: false, maxWidth: "240px"});
    map3d.on("click", "states-dot", e => {
      const p = e.features[0].properties;
      popup.setLngLat(e.lngLat)
        .setHTML(`<div style="font:15px KaiTi,serif;letter-spacing:2px;color:#2d2820">${p.n}</div>` +
          `<div style="font:11px FangSong,serif;color:#554e3d">${p.dao}${p.zhen ? " · " + p.zhen : ""}</div>` +
          `<div style="font:11px FangSong,serif;color:#554e3d">${p.now ? "今 " + p.now : ""} · 管${p.xian}县</div>` +
          `<a href="index.html#dao=${(YH.daos.find(d => d.name === p.dao) || {id: ""}).id}&zhou=${encodeURIComponent(p.n)}" ` +
          `style="font:11px FangSong,serif;color:#b03a25">➤ 入 2D 详卷</a>`)
        .addTo(map3d);
    });
    map3d.on("mouseenter", "states-dot", () => { map3d.getCanvas().style.cursor = "pointer"; });
    map3d.on("mouseleave", "states-dot", () => { map3d.getCanvas().style.cursor = ""; });

    const b = document.getElementById("boot3d");
    if (b) b.classList.add("gone");
  });

  /* 开场长镜：自西域掠至关中（拖动即断） */
  let _intro = true;
  map3d.on("load", () => {
    if (!_intro) return;
    map3d.flyTo({center: [108.5, 34.4], zoom: 5.4, pitch: 52, duration: 6500,
      curve: 1.6, essential: false});
  });
  map3d.on("dragstart", ()=>{ _intro = false; });

  /* 底栏返回 */
  const bk = document.getElementById("back2d");
  if (bk) bk.onclick = ()=>{ location.href = "index.html"; };
})();
