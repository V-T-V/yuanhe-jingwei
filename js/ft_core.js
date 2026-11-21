/* ═══════════ 元和经纬 · 全文检索公共纯核 ═══════════
   主线程（fulltext.js）与 Worker（ftworker.js importScripts）共用。
   约束：本文件禁止任何 document/window 引用——只做无 DOM 纯计算。 */

function countHits(text, q){
  var n = 0, i = text.indexOf(q);
  while (i >= 0){ n++; i = text.indexOf(q, i + q.length); }
  return n;
}
function ftSnippet(text, q){
  var i = text.indexOf(q);
  if (i < 0) return null;
  var a = Math.max(0, i - 18), b = Math.min(text.length, i + q.length + 18);
  var seg = text.slice(a, b).replace(/\s+/g, "");
  var esc = function(s){ return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };
  var qi = seg.indexOf(q);
  return (a > 0 ? "…" : "") + esc(seg.slice(0, qi)) +
    "<b>" + esc(q) + "</b>" + esc(seg.slice(qi + q.length)) + (b < text.length ? "…" : "");
}
