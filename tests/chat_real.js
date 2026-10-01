// Runs the user-supplied real questions through the chat and prints the reply kind and cited paragraph for each.
const path = require('path'), root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js')), C = require(path.join(root, 'lib/rdso_chat.js'));
['search_index', 'clause_extras', 'crossrefs', 'tables'].forEach(f => require(path.join(root, 'data/search', f + '.js')));
const e = S.create(globalThis.RDSO_SEARCH_INDEX);
const qs = require('fs').readFileSync(path.join(root, 'eval/real_questions_irpwm.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l));
console.log(JSON.stringify(qs.map(q => { const r = C.create(e, { extras: globalThis.RDSO_CLAUSE_EXTRAS, xrefs: globalThis.RDSO_CROSSREFS, tables: globalThis.RDSO_TABLES }).ask(q.question);
  const shown = r.kind === 'answer' ? (r.points || []).map(p => p.text).join(' ') + ' ' + (r.table ? r.table.rows.map(w => w.cells.join(' ')).join(' ') : '') + ' ' + (r.ownedTable ? r.ownedTable.rows.map(w => w.cells.join(' ')).join(' ') : '') : '';
  return { id: q.id, kind: r.kind, label: r.primary ? r.primary.label : null, grade: q.graded_2026_10_01, expected: q.expected_para, facts: q.key_facts.filter(k => shown.toLowerCase().includes(k.toLowerCase())).length, total: q.key_facts.length }; })));
