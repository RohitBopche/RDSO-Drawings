// Recall of the retrieval engine on the 20 real questions (expected paragraph per question). Prints one JSON document.
const path = require('path'), fs = require('fs'), root = path.resolve(__dirname, '..');
const S = require(path.join(root, 'lib/rdso_search.js'));
require(path.join(root, 'data/search/search_index.js'));
const e = S.create(globalThis.RDSO_SEARCH_INDEX);
const qs = fs.readFileSync(path.join(root, 'eval/real_questions_irpwm.jsonl'), 'utf8').trim().split('\n').map(l => JSON.parse(l));
let r1 = 0, r5 = 0; const misses = [];
qs.forEach(q => { const para = q.expected_para.replace('IRPWM Para ', ''), rows = e.search(q.question, { k: 10 }).results, i = rows.findIndex(r => r.alias === 'IRPWM' && r.para === para);
  if (i === 0) r1++; if (i >= 0 && i < 5) r5++; else misses.push(q.id); });
console.log(JSON.stringify({ n: qs.length, r1, r5, misses }));
