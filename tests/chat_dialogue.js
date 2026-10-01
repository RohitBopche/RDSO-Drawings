// Node harness for tests/test_chat.py: runs scripted dialogues and the grounding sweep, prints one JSON document.
const path = require('path');
const root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js')), C = require(path.join(root, 'lib/rdso_chat.js'));
require(path.join(root, 'data/search/search_index.js')); require(path.join(root, 'data/search/clause_extras.js')); require(path.join(root, 'data/search/crossrefs.js')); require(path.join(root, 'data/search/tables.js'));
const engine = S.create(globalThis.RDSO_SEARCH_INDEX);
const mk = () => C.create(engine, { extras: globalThis.RDSO_CLAUSE_EXTRAS, xrefs: globalThis.RDSO_CROSSREFS, tables: globalThis.RDSO_TABLES });
const norm = t => String(t).replace(/\s+/g, ' ').replace(/…$/, '').trim();
const out = { scenarios: {}, grounding: { checked: 0, violations: [] } };

function run(name, qs) { const c = mk(); out.scenarios[name] = qs.map(q => { const r = c.ask(q); return { q, kind: r.kind, confidence: r.confidence || null, interpreted: r.interpreted || null,
  primary: r.primary ? { label: r.primary.label, alias: r.primary.alias, para: r.primary.para } : null, points: (r.points || []).length, text: r.text || null,
  options: (r.options || []).length, nearest: (r.nearest || []).length, followups: (r.followups || []).length }; }); }
run('greet', ['hello', 'what can you do']);
run('renewal', ['How is casual renewal of a defective or fractured rail carried out?', 'what about the source', 'show me more', 'what else']);
run('wear', ['What does Para 429 of IRPWM say?', 'and what is the wear limit?']);
run('oos', ['What is the recipe for butter chicken?']);
run('fresh_after_other_manual', ['What does Para 13.1 of USFD say?', 'what is the tolerance in gauge']);
run('reset', ['What does Para 429 of IRPWM say?', 'start over', 'more']);
run('no_context', ['more']);

// Grounding: every sentence the assistant shows must be a piece of the cited passage (or of the second passage for "also relevant").
const fs = require('fs');
const qs = fs.readFileSync(path.join(root, 'eval/questions.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l)).filter(q => q.category !== 'oos' && q.category !== 'blind_oos');
const pick = qs.filter((_, i) => i % 3 === 0).slice(0, 120);
const docsByClause = {};
globalThis.RDSO_SEARCH_INDEX.docs.forEach(d => { (docsByClause[d.clause] = docsByClause[d.clause] || []).push(d.text); });
pick.forEach(q => {
  const c = mk(), r = c.ask(q.question);
  if (r.kind !== 'answer') return;
  const check = (p, label) => {
    out.grounding.checked++;
    const hay = (docsByClause[p.cite.clause] || []).map(norm).join(' ');
    if (!hay.includes(norm(p.text).replace(/\s*\.\.\.$/, '')) && !p.cite.clause) out.grounding.violations.push({ q: q.question, text: p.text });
    else if (!hay.includes(norm(p.text))) out.grounding.violations.push({ q: q.question, label, text: p.text.slice(0, 120) });
  };
  r.points.forEach(p => { check(p, 'point'); if (p.text.split(' ').length < 4 && !/^(Para|\d)/.test(p.text)) out.grounding.violations.push({ q: q.question, label: 'stub', text: p.text }); }); (r.alsoSee || []).forEach(p => check(p, 'also'));
  if (!r.primary || !r.primary.page) out.grounding.violations.push({ q: q.question, text: 'missing citation' });
});
out.probe = JSON.parse(fs.readFileSync(path.join(root, 'eval/chat_probe.json'), 'utf8')).items.map(it => {
  const r = mk().ask(it.q), text = (r.points || []).map(p => p.text).join(' ');
  const fail = [];
  if (r.kind !== it.kind) fail.push('kind ' + r.kind);
  if (it.primary && (!r.primary || r.primary.label !== it.primary)) fail.push('primary ' + (r.primary && r.primary.label));
  if (it.primary_in && (!r.primary || !it.primary_in.includes(r.primary.label))) fail.push('primary ' + (r.primary && r.primary.label));
  if (it.alias && (!r.primary || r.primary.alias !== it.alias)) fail.push('alias ' + (r.primary && r.primary.alias));
  if (it.text_regex && !new RegExp(it.text_regex, 'i').test(text + ' ' + (r.primary ? r.primary.text : ''))) fail.push('text');
  return { q: it.q, fail };
});
{ const r = mk().ask('what is the speed of utility track vehicle');
  out.table = r.table ? { columns: r.table.columns, rows: r.table.rows.map(w => w.cells), hit: r.table.rows.map(w => w.hit), page: r.table.page } : null; }
{ // every cell shown comes from the stored table
  const bad = []; let n = 0;
  qs.filter(q => q.category === 'blind_table').concat(pick.slice(0, 60), [{ question: 'what is the speed of utility track vehicle' }, { question: 'standard height of new 60 kg rail' }]).forEach(q => { const r0 = mk().ask(q.question); const r = r0.table ? r0 : (r0.ownedTable ? Object.assign({}, r0, { table: r0.ownedTable }) : r0); if (r.kind !== 'answer' || !r.table) return; n++;
    const T = globalThis.RDSO_TABLES[r.table.id], flat = T.r.map(row => row.map(c => (c || '').replace(/\n/g, '; ')));
    r.table.rows.forEach(w => { if (!flat.some(row => w.cells.every(c => row.includes(c)))) bad.push({ q: q.question, cells: w.cells.slice(0, 3) }); }); });
  out.tablecheck = { tables_shown: n, bad };
}
console.log(JSON.stringify(out));
