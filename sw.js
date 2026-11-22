/* ═══════════ 元和经纬 · Service Worker ═══════════
   三级缓存：SHELL 外壳预存 · TEXTS 全文懒存 · TILES 瓦片限额存
   VERSION 与 index.html 的 ?v 同步。 */

const VERSION = "v5";
const SHELL = "yh-" + VERSION + "-shell";
const TEXTS = "yh-" + VERSION + "-texts";
const TILES = "yh-" + VERSION + "-tiles";
const TILE_CAP = 1200;
const SHELL_FILES = [
  "./", "./index.html", "./3d.html", "./manifest.json",
  "./css/main.css?v=5",
  "./vendor/leaflet.js", "./vendor/leaflet.css",
  "./vendor/maplibre-gl.js", "./vendor/maplibre-gl.css",
  "./data/site_data.js",
  "./data/xref_hy.js",
  "./icons/icon-192.png", "./icons/icon-512.png", "./icons/icon-maskable-512.png",
  "./js/config.js?v=5", "./js/map.js?v=5", "./js/panels.js?v=5",
  "./js/rail.js?v=5", "./js/search.js?v=5", "./js/reader.js?v=5",
  "./js/ft_core.js?v=5", "./js/fulltext.js?v=5",
  "./js/app.js?v=5", "./js/modes.js?v=5",
  "./js/ftworker.js", "./js/map3d.js?v=5",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => ![SHELL, TEXTS, TILES].includes(k))
        .map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

let tilePuts = 0;
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  /* 页面导航：网络优先；仅 index 响应入壳（任意导航都 put 会把 3d.html 塞进
     "./index.html" 键——离线打开首页被调包，离线三验实证）；离线先回本页缓存再回外壳 */
  if (req.mode === "navigate") {
    const isIndex = /\/(index\.html)?$/.test(url.pathname);
    e.respondWith(
      fetch(req).then(r => {
        if (isIndex) {
          const cp = r.clone();
          caches.open(SHELL).then(c => c.put("./index.html", cp));
        }
        return r;
      }).catch(() =>
        caches.match(req, { ignoreSearch: true })
          .then(r => r || caches.match("./index.html", { ignoreSearch: true }))
          .then(r => r || Response.error()))
    );
    return;
  }

  /* 瓦片：stale-while-revalidate + 限额 */
  const isTile = url.hostname === "server.arcgisonline.com";
  if (isTile) {
    e.respondWith((async () => {
      const cache = await caches.open(TILES);
      const hit = await cache.match(req);
      const fresh = fetch(req).then(r => {
        if (r.ok) {
          tilePuts++;
          cache.put(req, r.clone()).then(async () => {
            if (tilePuts % 100 === 0) {
              const keys = await cache.keys();
              if (keys.length > TILE_CAP) await caches.delete(TILES);
            }
          });
        }
        return r;
      }).catch(() => null);
      return hit || (await fresh) || Response.error();
    })());
    return;
  }

  /* 同源资源：缓存优先，未命中网络回填 */
  if (url.origin === self.location.origin) {
    e.respondWith((async () => {
      const cacheName = url.pathname.includes("/data/text/") ? TEXTS : SHELL;
      const cache = await caches.open(cacheName);
      const hit = await cache.match(req, { ignoreSearch: true });
      if (hit) return hit;
      try {
        const r = await fetch(req);
        if (r.ok && (url.pathname.startsWith("/js/") || url.pathname.startsWith("/css/") ||
                     url.pathname.startsWith("/data/") || url.pathname.startsWith("/vendor/") ||
                     url.pathname.startsWith("/icons/"))) {
          cache.put(req, r.clone());
        }
        return r;
      } catch (err) {
        return Response.error();
      }
    })());
  }
});
