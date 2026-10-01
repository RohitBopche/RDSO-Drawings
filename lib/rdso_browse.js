/* Data model for browsing the manuals: manual -> chapter -> paragraph, with the paragraph's full text, built from the search index
 * (one passage per chunk of a clause; the index already holds every clause of the six manuals). One module for the browser and Node. */
(function (root) {
  'use strict';
  var NAMES = { IRPWM: 'Indian Railways Permanent Way Manual', TMM: 'Track Machine Manual', STMM: 'Small Track Machines Manual',
                USFD: 'Ultrasonic Flaw Detection of Rails Manual', AT_WELD: 'Alumino-Thermic Welding Manual', FBW: 'Flash Butt Welding Manual' };
  var DECIMAL = { AT_WELD: 1, FBW: 1, USFD: 1 };

  function paraKey(p) { return String(p).split('.').map(function (x) { var n = parseInt(x, 10); return isNaN(n) ? 0 : n; }); }
  function cmpPara(a, b) {
    var x = paraKey(a), y = paraKey(b);
    for (var i = 0; i < Math.max(x.length, y.length); i++) { var d = (x[i] || 0) - (y[i] || 0); if (d) return d; }
    return String(a).localeCompare(String(b));
  }

  function build(index) {
    var byId = {}, order = [];
    var annexParts = {}, annexOrder = [];
    index.docs.forEach(function (d) {
      if (d.type === 'CLAUSE' && d.kind === 'annexure' && NAMES[d.alias]) {     // annexure and appendix units (coverage layer)
        var a = annexParts[d.clause];
        if (!a) { var cm = /Chapter\s+(\d+)/.exec(d.chapter || ''); a = annexParts[d.clause] = { id: d.clause, alias: d.alias, annex: true, label: d.para, para: d.para, chapterNum: cm ? parseInt(cm[1], 10) : 0, chapter: d.chapter || '', title: String(d.title || '').replace(d.para, '').split(' Chapter ')[0].trim(), page: d.page, parts: [] }; annexOrder.push(a); }
        a.parts.push([d.id, d.text]); return;
      }
      if (d.type !== 'CLAUSE' || d.kind || !NAMES[d.alias]) return;
      var c = byId[d.clause];
      if (!c) {
        var m = /^CLAUSE:[^:]+:CH_(\d+):/.exec(d.clause);
        c = byId[d.clause] = { id: d.clause, alias: d.alias, para: d.para, chapterNum: m ? parseInt(m[1], 10) : 0, chapter: d.chapter || '',
                               title: String(d.title || '').split(' Chapter ')[0].trim(), page: d.page, parts: [] };
        order.push(c);
      }
      c.parts.push([d.id, d.text]);
    });
    order.forEach(function (c) {
      c.parts.sort(function (a, b) { return parseInt(a[0].split('#')[1], 10) - parseInt(b[0].split('#')[1], 10); });
      c.text = c.parts.map(function (p) { return p[1]; }).join('\n'); delete c.parts;
    });
    annexOrder.forEach(function (a) {
      a.parts.sort(function (x, y) { return parseInt(x[0].split('#')[1], 10) - parseInt(y[0].split('#')[1], 10); });
      a.text = a.parts.map(function (p) { return p[1]; }).join('\n'); delete a.parts; byId[a.id] = a;
    });
    var manuals = Object.keys(NAMES).map(function (alias) {
      var chapters = {};
      order.filter(function (c) { return c.alias === alias; }).forEach(function (c) {
        var ch = chapters[c.chapterNum] = chapters[c.chapterNum] || { num: c.chapterNum, title: c.chapter.replace(/^Chapter\s+\d+\s*[—-]\s*/, ''), clauses: [] };
        ch.clauses.push(c);
      });
      var list = Object.keys(chapters).map(function (k) { return chapters[k]; }).sort(function (a, b) { return a.num - b.num; });
      list.forEach(function (ch) { ch.clauses.sort(function (a, b) { return cmpPara(a.para, b.para); }); });
      var annexes = annexOrder.filter(function (a) { return a.alias === alias; }).sort(function (x, y) { return x.page - y.page; });
      annexes.forEach(function (a, i) { a.prev = i ? annexes[i - 1].id : null; a.next = i + 1 < annexes.length ? annexes[i + 1].id : null; });
      return { alias: alias, name: NAMES[alias], decimal: !!DECIMAL[alias], chapters: list, annexes: annexes, count: list.reduce(function (n, ch) { return n + ch.clauses.length; }, 0), annexCount: annexes.length };
    });
    // neighbours within a manual, in reading order
    manuals.forEach(function (m) {
      var flat = [];
      m.chapters.forEach(function (ch) { ch.clauses.forEach(function (c) { flat.push(c); }); });
      flat.forEach(function (c, i) { c.prev = i ? flat[i - 1].id : null; c.next = i + 1 < flat.length ? flat[i + 1].id : null; });
    });
    return { manuals: manuals, byId: byId, names: NAMES };
  }

  /* decimal manuals: 13.1.1's parent is 13.1 */
  function parentPara(alias, para) { return DECIMAL[alias] && String(para).indexOf('.') > 0 ? String(para).replace(/\.[^.]+$/, '') : null; }
  function find(model, text) {
    var q = String(text || '').toLowerCase().trim();
    if (!q) return [];
    var out = [];
    Object.keys(model.byId).forEach(function (id) {
      var c = model.byId[id], hay = (c.alias + ' ' + c.para + ' ' + c.title).toLowerCase();
      if (hay.indexOf(q) >= 0) out.push(c);
    });
    return out.slice(0, 60);
  }
  var api = { build: build, cmpPara: cmpPara, parentPara: parentPara, find: find, NAMES: NAMES };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RDSOBrowse = api;
})(typeof window !== 'undefined' ? window : globalThis);
