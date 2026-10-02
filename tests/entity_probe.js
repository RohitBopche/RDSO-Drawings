// Prints, as JSON, how the chat answers a few concept questions and that ordinary questions are not taken over by the concept layer.
const path = require('path'), root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js')), C = require(path.join(root, 'lib/rdso_chat.js')), G = require(path.join(root, 'lib/rdso_graphq.js')), EN = require(path.join(root, 'lib/rdso_entities.js'));
['search_index', 'clause_extras', 'crossrefs', 'tables', 'editions', 'drawing_cites', 'entities'].forEach(f => require(path.join(root, 'data/search', f + '.js')));
const engine = S.create(globalThis.RDSO_SEARCH_INDEX);
const graph = G.create({ xrefs: globalThis.RDSO_CROSSREFS, clauseText: id => engine.clauseText(id), drawingCites: globalThis.RDSO_DRAWING_CITES });
const entities = EN.create(globalThis.RDSO_ENTITIES);
const ask = q => C.create(engine, { extras: globalThis.RDSO_CLAUSE_EXTRAS, xrefs: globalThis.RDSO_CROSSREFS, tables: globalThis.RDSO_TABLES, editions: globalThis.RDSO_EDITIONS, entities, graph }).ask(q);
const out = {};
for (const q of process.argv.slice(2)) { const r = ask(q); out[q] = { kind: r.kind, mode: r.mode || null, concept: r.concept || null, rows: (r.rows || []).map(x => ({ label: x.raw, clause: x.cite && x.cite.clause, quote: x.quote })), text: r.text || null }; }
out.find = { 'the PWI': (entities.find('the PWI') || {}).id, 'LWR buckling': (entities.find('LWR buckling') || {}).id, 'hello': entities.find('hello') };
console.log(JSON.stringify(out));
