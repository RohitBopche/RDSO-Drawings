// Per-manual retrieval probe for scripts/pilot_checklist.py: identifier lookup, natural-language recall, refusal. Prints one JSON document.
const path = require('path'), fs = require('fs'), root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js'));
require(path.join(root, 'data/search/search_index.js'));
const engine = S.create(globalThis.RDSO_SEARCH_INDEX);
const ALIAS = { IRPWM: 1, TMM: 1, STMM: 1, USFD: 1, AT_WELD: 1, FBW: 1 };
const clauses = {};
globalThis.RDSO_SEARCH_INDEX.docs.forEach(d => { if (d.type === 'CLAUSE' && !d.kind && ALIAS[d.alias]) clauses[d.clause] = { alias: d.alias, para: d.para }; });
const out = {};
Object.keys(ALIAS).forEach(a => { out[a] = { clauses: 0, ident_n: 0, ident_ok: 0, nl_n: 0, nl_r5: 0, oos_n: 0, oos_refused: 0 }; });
// identifier lookup on every 3rd clause: "<ALIAS> Para <n>" must put that clause first
const ids = Object.keys(clauses).sort();
ids.forEach((id, i) => { const c = clauses[id], o = out[c.alias]; o.clauses++; if (i % 3) return; o.ident_n++;
  const r = engine.search(c.alias.replace('_', ' ') + ' para ' + c.para, { k: 3 }); if (r.results[0] && r.results[0].clause === id) o.ident_ok++; });
// natural-language questions of the evaluation sets, by the manual of their gold clause
fs.readFileSync(path.join(root, 'eval/questions.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l)).forEach(q => {
  if (q.expect !== 'answer' || !['nl', 'blind', 'blind_table', 'kw_auto'].includes(q.category)) return;
  const m = /^CLAUSE:([A-Z_]+):/.exec(q.gold[0] || ''); if (!m || !out[m[1]]) return; const o = out[m[1]]; o.nl_n++;
  const r = engine.search(q.question, { k: 5 }); if (r.results.slice(0, 5).some(x => q.gold.includes(x.clause))) o.nl_r5++; });
// off-topic questions, scoped to each manual with strict scope: every one must be refused
const OFF = ['What is the recipe for butter chicken?', 'Who won the cricket world cup in 2011?', 'How do I fix a memory leak in a Python program?', 'What is the exchange rate of the US dollar to the rupee?'];
Object.keys(ALIAS).forEach(a => OFF.forEach(q => { const o = out[a]; o.oos_n++; if (engine.answer(q, { k: 8, manual: a, strict: true }).status === 'no_evidence') o.oos_refused++; }));
console.log(JSON.stringify(out));
