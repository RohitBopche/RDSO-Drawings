/* Relationship questions over the paragraph graph, answered from the manuals' own cross-references.
 *   trace(id, 'out'|'in')   what a paragraph refers to / what refers to it, a few steps deep
 *   path(a, b)              the shortest chain of references between two paragraphs, with the sentence that makes each link
 *   drawingCites(number)    the paragraphs that cite a drawing number
 * Every link carries the sentence of the source paragraph that contains the reference, cut verbatim from the paragraph text.
 * One module for the browser and Node; it takes its data as arguments and holds none of its own. */
(function (root) {
  'use strict';
  function plain(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }

  function create(ctx) {
    var xrefs = ctx.xrefs || { out: {}, in: {} }, text = ctx.clauseText, cites = ctx.drawingCites || {};
    var fwd = {}, back = {};      // clause -> { target: [edge] }
    Object.keys(xrefs.out).forEach(function (src) {
      xrefs.out[src].forEach(function (e) {
        if (e[2] !== 'RESOLVED' || e[6] == null) return;
        (e[3] || []).forEach(function (t) {
          if (t === src || t.indexOf('CLAUSE:') !== 0) return;
          // "(Back to Para N)" printed in src is a note that N refers to src, so the edge runs from N to src; the sentence still sits in src
          var edge = e[8] ? { from: t, to: src, at: src, raw: e[0], start: e[6], end: e[7], back: true } : { from: src, to: t, at: src, raw: e[0], start: e[6], end: e[7], back: false };
          ((fwd[edge.from] = fwd[edge.from] || {})[edge.to] = fwd[edge.from][edge.to] || []).push(edge);
          ((back[edge.to] = back[edge.to] || {})[edge.from] = back[edge.to][edge.from] || []).push(edge);
        });
      });
    });

    /* the sentence of the source paragraph that holds the reference (verbatim words, spaces collapsed), cut to about 300 characters */
    function quote(edge) {
      var t = text(edge.at) || '', a = edge.start, b = edge.end, lo = 0, hi = t.length, m, re = /[.;:?!]\s+(?=[A-Z(\d])/g;
      while ((m = re.exec(t))) { if (m.index + 1 <= a) lo = m.index + m[0].length; else if (m.index >= b) { hi = m.index + 1; break; } }
      var s = plain(t.slice(lo, hi));
      if (s.length > 300) { var ref = plain(t.slice(a, b)), at = Math.max(0, s.indexOf(ref)), from = Math.max(0, at - 120); s = (from ? '…' : '') + s.slice(from, from + 300).replace(/\s+\S*$/, ''); }
      return s.replace(/^…/, '');
    }
    function first(list) { return list[0]; }
    function link(edge, dir) { return { from: edge.from, to: edge.to, at: edge.at, back: edge.back, dir: dir, raw: plain(edge.raw), quote: quote(edge) }; }

    function trace(id, dir, maxDepth, maxNodes) {
      var g = dir === 'in' ? back : fwd, seen = {}, levels = [], frontier = [id]; seen[id] = 1; maxDepth = maxDepth || 2; maxNodes = maxNodes || 40;
      var total = 0;
      for (var d = 1; d <= maxDepth && frontier.length; d++) {
        var next = [], level = [];
        frontier.forEach(function (c) {
          Object.keys(g[c] || {}).sort().forEach(function (o) {
            if (seen[o]) return; seen[o] = 1; total++;
            if (total <= maxNodes) { var edge = first(g[c][o]); level.push({ id: o, via: c, depth: d, link: link(edge, dir === 'in' ? 'in' : 'out') }); }
            next.push(o);
          });
        });
        if (level.length) levels.push(level);
        frontier = next;
      }
      return { root: id, dir: dir, levels: levels, total: total, shown: Math.min(total, maxNodes) };
    }

    function neighbours(c) {
      var o = [];
      Object.keys(fwd[c] || {}).forEach(function (t) { o.push([t, first(fwd[c][t]), 'out']); });
      Object.keys(back[c] || {}).forEach(function (s) { o.push([s, first(back[c][s]), 'in']); });
      return o.sort(function (x, y) { return x[0] < y[0] ? -1 : x[0] > y[0] ? 1 : 0; });
    }
    function path(a, b, maxDepth) {
      if (a === b) return { hops: [], length: 0 };
      maxDepth = maxDepth || 6;
      var prev = {}, frontier = [a], seen = {}; seen[a] = 1;
      for (var d = 0; d < maxDepth && frontier.length; d++) {
        var next = [];
        for (var i = 0; i < frontier.length; i++) {
          var c = frontier[i], ns = neighbours(c);
          for (var j = 0; j < ns.length; j++) {
            var o = ns[j][0]; if (seen[o]) continue; seen[o] = 1; prev[o] = [c, ns[j][1], ns[j][2]];
            if (o === b) { var hops = [], cur = b; while (cur !== a) { var p = prev[cur]; hops.unshift(link(p[1], p[2])); cur = p[0]; } return { hops: hops, length: hops.length }; }
            next.push(o);
          }
        }
        frontier = next;
      }
      return null;
    }

    function drawingKey(s) { var m = /(\d{3,5})/.exec(String(s || '')); return m ? m[1] : null; }
    function drawingCites(number) {
      var k = drawingKey(number), rows = cites[k] || [];
      return rows.map(function (r) { var edge = { from: r[0], to: null, at: r[0], raw: '', start: r[1], end: r[2] }; edge.raw = plain((text(r[0]) || '').slice(r[1], r[2])); return { clause: r[0], raw: edge.raw, held: !!r[3], quote: quote(edge) }; });
    }
    function quoteSpan(clause, start, end) { return quote({ at: clause, start: start, end: end }); }
    return { quoteSpan: quoteSpan, trace: trace, path: path, drawingCites: drawingCites, drawingKey: drawingKey, degree: function (id) { return { out: Object.keys(fwd[id] || {}).length, in: Object.keys(back[id] || {}).length }; } };
  }
  var api = { create: create };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RDSOGraphQ = api;
})(typeof window !== 'undefined' ? window : globalThis);
