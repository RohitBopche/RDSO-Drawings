// Node harness for tests/test_chat.py: runs scripted dialogues and the grounding sweep, prints one JSON document.
const path = require('path');
const root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js')), C = require(path.join(root, 'lib/rdso_chat.js'));
require(path.join(root, 'data/search/search_index.js')); require(path.join(root, 'data/search/clause_extras.js')); require(path.join(root, 'data/search/crossrefs.js'));
const engine = S.create(globalThis.RDSO_SEARCH_INDEX);
const mk = () => C.create(engine, { extras: globalThis.RDSO_CLAUSE_EXTRAS, xrefs: globalThis.RDSO_CROSSREFS });
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
  r.points.forEach(p => check(p, 'point')); (r.alsoSee || []).forEach(p => check(p, 'also'));
  if (!r.primary || !r.primary.page) out.grounding.violations.push({ q: q.question, text: 'missing citation' });
});
console.log(JSON.stringify(out));
