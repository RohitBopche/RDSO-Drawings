// Citation verifier: every piece of text the chat shows must be a verbatim part of what it cites. Run over every evaluation question, the
// real questions and the probe. Prints one JSON document: counts and every violation.
const path = require('path'), fs = require('fs'), root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js')), C = require(path.join(root, 'lib/rdso_chat.js'));
['search_index', 'clause_extras', 'crossrefs', 'tables', 'editions', 'drawing_cites'].forEach(f => require(path.join(root, 'data/search', f + '.js')));
const engine = S.create(globalThis.RDSO_SEARCH_INDEX);
const norm = t => String(t).replace(/\s+/g, ' ').replace(/…$/, '').replace(/\s*\.\.\.$/, '').trim();
const docsByClause = {};
globalThis.RDSO_SEARCH_INDEX.docs.forEach(d => { (docsByClause[d.clause] = docsByClause[d.clause] || []).push(norm(d.text)); });
const clauseHay = id => (docsByClause[id] || []).join(' ');
const cellsOf = id => { const T = globalThis.RDSO_TABLES[id]; return T ? new Set([].concat(T.h, ...T.r).map(c => norm((c || '').replace(/\n/g, '; ')))) : null; };
const G = require(path.join(root, 'lib/rdso_graphq.js'));
const graph = G.create({ xrefs: globalThis.RDSO_CROSSREFS, clauseText: id => engine.clauseText(id), drawingCites: globalThis.RDSO_DRAWING_CITES });
const lines = f => fs.readFileSync(path.join(root, f), 'utf8').trim().split('\n').map(l => JSON.parse(l));
const questions = lines('eval/questions.jsonl').map(q => q.question).concat(lines('eval/real_questions_irpwm.jsonl').map(q => q.question),
  JSON.parse(fs.readFileSync(path.join(root, 'eval/chat_probe.json'), 'utf8')).items.map(i => i.q));
const out = { questions: questions.length, answers: 0, refused: 0, fragments: 0, violations: [] };
const check = (q, what, text, clause) => { out.fragments++; const hay = clauseHay(clause), t = norm(text);
  if (!clause || !hay) out.violations.push({ q, what, text: t.slice(0, 80), why: 'no cited paragraph' });
  else if (!hay.includes(t)) out.violations.push({ q, what, text: t.slice(0, 100), why: 'not in the cited paragraph' }); };
questions.forEach(q => {
  const r = C.create(engine, { extras: globalThis.RDSO_CLAUSE_EXTRAS, xrefs: globalThis.RDSO_CROSSREFS, tables: globalThis.RDSO_TABLES, editions: globalThis.RDSO_EDITIONS, graph }).ask(q);
  if (r.kind !== 'answer') { out.refused++; return; }
  out.answers++;
  if (!r.primary || !r.primary.page || !r.primary.label) out.violations.push({ q, what: 'citation', why: 'missing label or page' });
  if (r.table) { // rows come from the stored table that the primary paragraph owns or is
    const cells = cellsOf(r.table.id); r.table.rows.forEach(w => w.cells.forEach(c => { out.fragments++; if (cells && c && !cells.has(norm(c))) out.violations.push({ q, what: 'table cell', text: norm(c).slice(0, 80), why: 'not in the stored table' }); }));
  } else (r.points || []).forEach(p => check(q, 'point', p.text, p.cite && p.cite.clause));
  (r.ownedTables || []).forEach(t => { const cells = cellsOf(t.id); t.rows.forEach(w => w.cells.forEach(c => { out.fragments++; if (cells && c && !cells.has(norm(c))) out.violations.push({ q, what: 'owned table cell', text: norm(c).slice(0, 80), why: 'not in the stored table' }); })); });
  (r.alsoSee || []).forEach(p => check(q, 'also relevant', p.text, p.cite && p.cite.clause));
  // edition line and correction-slip marks: the edition must be the registry's, every mark must be printed in the cited paragraph
  if (!r.edition) out.violations.push({ q, what: 'edition', why: 'answer without an edition line' });
  (r.amendments || []).forEach(a => { out.fragments++; const [kind, n] = a.split(' '); if (!new RegExp('\\(\\s*' + kind + '\\s*[-\u2013]\\s*' + n + '\\s*\\)').test(clauseHay(r.primary.clause))) out.violations.push({ q, what: 'amendment', text: a, why: 'mark not printed in the cited paragraph' }); });
});
// relationship answers: every quoted sentence is a verbatim part of the paragraph that prints the reference
out.relations = 0;
const relIds = Object.keys(globalThis.RDSO_CROSSREFS.out).filter(i => /^CLAUSE:(IRPWM|TMM|STMM|USFD|AT_WELD|FBW):/.test(i)).sort().filter((_, i) => i % 5 === 0).slice(0, 60);
relIds.forEach(id => { const m = /^CLAUSE:([^:]+):CH_\d+:PARA_(.+)$/.exec(id), label = m[1].replace('_', ' ') + ' Para ' + m[2].replace(/_/g, '.');
  ['What refers to ' + label + '?', 'What does ' + label + ' refer to?', 'Which figures does ' + label + ' mention?'].forEach(q => {
    const r = require(path.join(root, 'lib/rdso_chat.js')).create(engine, { extras: globalThis.RDSO_CLAUSE_EXTRAS, xrefs: globalThis.RDSO_CROSSREFS, tables: globalThis.RDSO_TABLES, editions: globalThis.RDSO_EDITIONS, graph }).ask(q);
    if (r.kind !== 'relation') { if (r.kind !== 'clarify' && !/figures/.test(q)) out.violations.push({ q, what: 'relation', why: 'not understood as a relationship question: ' + r.kind }); return; }
    out.relations++; (r.rows || []).forEach(x => { const at = x.at || x.cite; out.fragments++; check(q, 'relation quote', String(x.quote).replace(/^…/, ''), at && at.clause); }); }); });
if (process.env.RDSO_SEED_BAD) { check('seeded', 'seeded', 'The maximum permissible speed on every curve is 999 Kmph.', 'CLAUSE:IRPWM:CH_06:PARA_616'); check('seeded', 'seeded', 'Casual rail renewal shall be done for replacement of defective rail', 'CLAUSE:IRPWM:CH_06:PARA_616'); }   // self-test: a fabricated sentence must be caught, a real one not
console.log(JSON.stringify(out));
