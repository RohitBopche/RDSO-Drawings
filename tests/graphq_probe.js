// Relationship queries for tests/test_graphq.py: traces for every paragraph with links, paths for sampled pairs, all drawing numbers.
const path = require('path'), root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js')), G = require(path.join(root, 'lib/rdso_graphq.js'));
['search_index', 'crossrefs', 'drawing_cites'].forEach(f => require(path.join(root, 'data/search', f + '.js')));
const e = S.create(globalThis.RDSO_SEARCH_INDEX);
const g = G.create({ xrefs: globalThis.RDSO_CROSSREFS, clauseText: id => e.clauseText(id), drawingCites: globalThis.RDSO_DRAWING_CITES });
const ids = Object.keys(globalThis.RDSO_CROSSREFS.out).filter(i => i.startsWith('CLAUSE:')).sort();
const out = { traces: {}, paths: [], drawings: {} };
ids.forEach(id => { ['in', 'out'].forEach(d => { const t = g.trace(id, d, 2, 1000); out.traces[id + '|' + d] = { total: t.total, first: t.levels[0] ? t.levels[0].map(x => ({ id: x.id, raw: x.link.raw, quote: x.link.quote, at: x.link.at, back: x.link.back })) : [] }; }); });
const sample = ids.filter((_, i) => i % 7 === 0).slice(0, 40);
sample.forEach((a, i) => { const b = sample[(i * 5 + 3) % sample.length]; const p = g.path(a, b, 6); out.paths.push({ a, b, length: p ? p.length : null, hops: p ? p.hops.map(h => ({ from: h.from, to: h.to, quote: h.quote, at: h.at, raw: h.raw })) : null }); });
Object.keys(globalThis.RDSO_DRAWING_CITES).forEach(n => { out.drawings[n] = g.drawingCites(n).map(r => ({ clause: r.clause, raw: r.raw, quote: r.quote })); });
console.log(JSON.stringify(out));
