#!/usr/bin/env node
/* Build data/search/search_index.js from data/search/passages.jsonl (written by build_search_index.py).
 * Tokenisation comes from lib/rdso_search.js so index and queries always agree. */
'use strict';
const fs = require('fs');
const path = require('path');
const S = require('../lib/rdso_search.js');
const root = path.resolve(__dirname, '..');
const passages = fs.readFileSync(path.join(root, 'data/search/passages.jsonl'), 'utf8').split('\n').filter(Boolean).map(JSON.parse);
const synCfg = JSON.parse(fs.readFileSync(path.join(root, 'data/search/synonyms.json'), 'utf8'));

const docs = [], postings = {};
let totalLen = 0;
passages.forEach((p, di) => {
  const body = S.analyze(p.text), title = S.analyze(p.title);
  const tf = {};
  body.forEach(t => { (tf[t] = tf[t] || [0, 0])[0]++; });
  title.forEach(t => { (tf[t] = tf[t] || [0, 0])[1]++; });
  Object.keys(tf).sort().forEach(t => { (postings[t] = postings[t] || []).push(di, tf[t][0], tf[t][1]); });
  docs.push({ id: p.id, clause: p.clause, alias: p.alias, doc: p.doc, chapter: p.chapter, para: p.para, title: p.title,
              page: p.page, type: p.type, len: body.length + title.length, text: p.text });
  totalLen += body.length + title.length;
});
const df = {};
Object.keys(postings).forEach(t => { df[t] = postings[t].length / 3; });

// synonym rules: [keyTerms, addTerms] for every ordered pair in a group (phrase or abbreviation triggers)
const synonyms = [];
synCfg.groups.forEach(g => {
  const an = g.map(x => S.analyze(x));
  an.forEach((k, i) => an.forEach((a, j) => { if (i !== j && k.length && a.length) synonyms.push([k, a]); }));
});
const sortedPostings = {};
Object.keys(postings).sort().forEach(t => { sortedPostings[t] = postings[t]; });
const index = { meta: { version: 1, docs: docs.length, avgLen: totalLen / docs.length, terms: Object.keys(postings).length },
                docs, postings: sortedPostings, df, synonyms };
const out = path.join(root, 'data/search/search_index.js');
fs.writeFileSync(out, '(typeof window!=="undefined"?window:globalThis).RDSO_SEARCH_INDEX=' + JSON.stringify(index) + ';\n');
console.log(`indexed ${docs.length} passages, ${index.meta.terms} terms, avgLen ${index.meta.avgLen.toFixed(1)}, ${(fs.statSync(out).size / 1048576).toFixed(2)} MB`);
