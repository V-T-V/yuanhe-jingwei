/* ═══════════ 元和经纬 · 三维形胜（MapLibre 真地形） ═══════════
   州治圆点立于山川：大小随属县数，色随道；点击出卡回 2D。 */

var map3d = null;

(function(){
  const el = document.getElementById("map3d");
  if (!window.maplibregl){
    el.innerHTML = "<div style='padding:40px;font:14px KaiTi,serif;letter-spacing:2px'>三维组件未载入（vendor/maplibre-gl.js）</div>";
    return;
  }
  if (!maplibregl.supported || !maplibregl.supported()){
    el.innerHTML = "<div style='padding:40px;font:14px KaiTi,serif;letter-spacing:2px'>此环境不支持 WebGL——请回 <a href='index.html' style='color:#b03a25'>二维舆图</a></div>";
    return;
  }

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
