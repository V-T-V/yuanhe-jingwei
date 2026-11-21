/* ═══════════ 元和经纬 · 全文检索 Worker（纯数据，无 DOM） ═══════════ */
importScripts("ft_core.js");

self.onmessage = function(e){
  var q = e.data.q;
  var docs = e.data.docs;   // [{key, title, kicker, text}]
  var out = [];
  for (var i = 0; i < docs.length; i++){
    var d = docs[i];
    var n = countHits(d.text, q);
    if (n > 0){
      out.push({key: d.key, title: d.title, kicker: d.kicker, n: n,
                snip: ftSnippet(d.text, q)});
    }
  }
  out.sort(function(a, b){ return b.n - a.n; });
  self.postMessage({q: q, results: out.slice(0, 60)});
};
