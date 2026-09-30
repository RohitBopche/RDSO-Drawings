#!/usr/bin/env node
/* Offline search from the command line.
 *   node scripts/search_cli.js "how is casual renewal of a fractured rail carried out"
 *   node scripts/search_cli.js --batch eval/questions.jsonl > results.json   (used by eval_retrieval.py)
 */
'use strict';
const fs = require('fs');
const path = require('path');
require('../data/search/search_index.js');
const S = require('../lib/rdso_search.js');
const opts = process.env.RDSO_SEARCH_OPTS ? JSON.parse(process.env.RDSO_SEARCH_OPTS) : {};
const engine = S.create(globalThis.RDSO_SEARCH_INDEX, opts);
const args = process.argv.slice(2);
if (args[0] === '--batch') {
  const rows = fs.readFileSync(path.resolve(args[1]), 'utf8').split('\n').filter(Boolean).map(JSON.parse);
  const out = rows.map(r => {
    const res = engine.search(r.question, { k: 10 });
    return { id: r.id, topScore: res.topScore, coverage: res.coverage, coverage3: res.coverage3, identifierHit: res.identifierHit, results: res.results.map(x => ({ clause: x.clause, passage: x.passage, score: x.score })) };
  });
  process.stdout.write(JSON.stringify(out));
} else {
  const res = engine.search(args.join(' '), { k: 5 });
  console.log(`terms: ${res.terms.join(' ')}  +${res.expanded.join(' ')}  manuals: ${res.manuals.join(',') || '-'}  paras: ${res.paras.join(',') || '-'}`);
  console.log(`top score ${res.topScore.toFixed(2)}  evidence coverage ${(res.coverage * 100).toFixed(0)}%  identifier hit: ${res.identifierHit}`);
  res.results.forEach((x, i) => console.log(`${i + 1}. [${x.score.toFixed(2)}] ${x.clause}  p.${x.page}  ${x.title.slice(0, 70)}\n     ${x.text.replace(/\s+/g, ' ').slice(0, 160)}`));
}
