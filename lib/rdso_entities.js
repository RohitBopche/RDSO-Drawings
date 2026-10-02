/* Concept questions over the entity layer (data/search/entities.js, built by scripts/build_entities.py).
 *   find(text)         the concept a question names (longest alias wins), or null
 *   where(id)          how often and in which manuals a concept is named, with a few paragraphs
 *   related(id, n)     concepts named in the same sentence as this one, in several paragraphs, most specific first
 *   parts(id)          curated sub-types and parts of a concept
 *   limits(id, q)      measured values printed in a sentence that names the concept
 * Every row points at a place in a paragraph (source id and character span); the chat quotes the sentence from the paragraph text.
 * One module for the browser and Node; it takes its data as an argument. */
(function (root) {
  'use strict';
  function csAlias(a) { return /[A-Z]{2}/.test(a) || a === 'P.Way' || a === 'P-Way' || a === 'P&C'; }
  function esc(a) { return a.replace(/[.*+?^${}()|[\]\\\/]/g, '\\$&').replace(/ /g, '\\s+'); }

  function create(data) {
    var C = data.c, S = data.s, ids = Object.keys(C).sort(), tax = data.tax || [];
    var owner = {}, groups = { cs: [], ci: [] };
    ids.forEach(function (id) { C[id].a.forEach(function (a) { var cs = csAlias(a); owner[cs ? a : a.toLowerCase()] = id; groups[cs ? 'cs' : 'ci'].push(a); }); });
    function mk(list, flags) { list.sort(function (x, y) { return y.length - x.length || (x < y ? -1 : 1); }); return list.length ? new RegExp('(?<![A-Za-z0-9])(' + list.map(esc).join('|') + ')(?:s|es)?(?![A-Za-z0-9])', flags) : null; }
    var reCs = mk(groups.cs, 'g'), reCi = mk(groups.ci, 'gi');

    function find(text) {
      var best = null;
      [[reCs, true], [reCi, false]].forEach(function (p) {
        if (!p[0]) return; p[0].lastIndex = 0; var m;
        while ((m = p[0].exec(text))) {
          var key = p[1] ? m[1] : m[1].replace(/\s+/g, ' ').toLowerCase(), id = owner[key];
          if (id && (!best || m[1].length > best.alias.length)) best = { id: id, alias: m[1], label: C[id].l };
        }
      });
      return best;
    }
    function where(id) {
      var c = C[id]; if (!c) return null;
      var occ = data.occ[id] || [];
      return { id: id, label: c.l, mentions: c.n, paragraphs: c.p, byManual: c.m, places: occ.map(function (o) { return { source: S[o[0]], start: o[1], end: o[2] }; }) };
    }
    function related(id, n) {
      var rows = [];
      (data.rel || []).forEach(function (r) {
        var other = r[0] === id ? r[1] : r[1] === id ? r[0] : null; if (!other) return;
        var support = r[2], pa = r[3], pb = r[4], lift = support / Math.sqrt(pa * pb);   // shared sentences relative to how often each is named at all
        rows.push({ id: other, label: C[other].l, support: support, lift: lift, example: { source: S[r[5][0][0]], start: r[5][0][1], end: r[5][0][2] } });
      });
      rows.sort(function (a, b) { return b.lift - a.lift || b.support - a.support || (a.id < b.id ? -1 : 1); });
      return { total: rows.length, rows: rows.slice(0, n || 8) };
    }
    function parts(id) {
      var kids = { PART_OF: [], IS_A: [] };
      tax.forEach(function (t) { if (t[2] === id) kids[t[0]].push(t[1]); });
      var up = tax.filter(function (t) { return t[1] === id; }).map(function (t) { return { type: t[0], id: t[2], label: C[t[2]].l }; });
      function row(k) { var o = (data.occ[k] || [])[0]; return { id: k, label: C[k].l, mentions: C[k].n, example: o ? { source: S[o[0]], start: o[1], end: o[2] } : null }; }
      return { parts: kids.PART_OF.sort().map(row), kinds: kids.IS_A.sort().map(row), up: up };
    }
    function limits(id, filter) {
      var rows = (data.limits[id] || []).map(function (l) { return { source: S[l[0]], start: l[1], end: l[2], raw: l[3], quantity: l[4], lo: l[5], hi: l[6], unit: l[7] }; });
      if (filter) rows = rows.filter(function (r) { return r.quantity === filter; });
      var q = {}; rows.forEach(function (r) { q[r.quantity || 'value'] = (q[r.quantity || 'value'] || 0) + 1; });
      return { total: rows.length, quantities: q, rows: rows };
    }
    return { find: find, where: where, related: related, parts: parts, limits: limits, get: function (id) { return C[id] || null; }, ids: function () { return ids.slice(); } };
  }
  var api = { create: create };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RDSOEntities = api;
})(typeof window !== 'undefined' ? window : globalThis);
