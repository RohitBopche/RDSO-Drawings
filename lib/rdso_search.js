/* RDSO offline search engine (P5.1).
 *
 * One implementation for the browser and for Node (eval harness, CLI): BM25F over passages with
 * a Porter stemmer, railway abbreviation expansion, identifier (paragraph number) matching,
 * manual-name scoping, bigram re-ranking and an evidence-coverage score used to refuse
 * out-of-scope questions. No network, no dependencies.
 *
 *   const engine = RDSOSearch.create(indexObject);
 *   engine.search("How is casual renewal of a fractured rail carried out?", {k: 10, manual: "IRPWM"})
 */
(function (root) {
  'use strict';

  var STOP = new Set(('a an the of in on at for to is are was were be been being by with and or how what which who whom whose ' +
    'when where why does do did can could should shall must may might will would from that this these those it its as any all ' +
    'into between during after before over under than then there their they them he she his her we our you your i me my not no ' +
    'if but so such out also about tell give show list explain describe please mention state per via').split(' '));

  // ---- Porter stemmer (standard algorithm) -------------------------------------------------
  var step2 = { ational: 'ate', tional: 'tion', enci: 'ence', anci: 'ance', izer: 'ize', bli: 'ble', alli: 'al', entli: 'ent', eli: 'e', ousli: 'ous', ization: 'ize', ation: 'ate', ator: 'ate', alism: 'al', iveness: 'ive', fulness: 'ful', ousness: 'ous', aliti: 'al', iviti: 'ive', biliti: 'ble', logi: 'log' };
  var step3 = { icate: 'ic', ative: '', alize: 'al', iciti: 'ic', ical: 'ic', ful: '', ness: '' };
  var c = '[^aeiou]', v = '[aeiouy]', C = c + '[^aeiouy]*', V = v + '[aeiou]*';
  var mgr0 = new RegExp('^(' + C + ')?' + V + C);
  var meq1 = new RegExp('^(' + C + ')?' + V + C + '(' + V + ')?$');
  var mgr1 = new RegExp('^(' + C + ')?' + V + C + V + C);
  var sv = new RegExp('^(' + C + ')?' + v);

  function stem(w) {
    var stem_, suffix, re, re2, re3, re4;
    if (w.length < 3) return w;
    var firstch = w.substr(0, 1);
    if (firstch === 'y') w = firstch.toUpperCase() + w.substr(1);
    re = /^(.+?)(ss|i)es$/; re2 = /^(.+?)([^s])s$/;
    if (re.test(w)) w = w.replace(re, '$1$2'); else if (re2.test(w)) w = w.replace(re2, '$1$2');
    re = /^(.+?)eed$/; re2 = /^(.+?)(ed|ing)$/;
    if (re.test(w)) { var fp = re.exec(w); re = mgr0; if (re.test(fp[1])) w = w.slice(0, -1); }
    else if (re2.test(w)) {
      var fp2 = re2.exec(w); stem_ = fp2[1]; re2 = sv;
      if (re2.test(stem_)) {
        w = stem_; re2 = /(at|bl|iz)$/; re3 = /([^aeiouylsz])\1$/; re4 = new RegExp('^' + C + v + '[^aeiouwxy]$');
        if (re2.test(w)) w += 'e'; else if (re3.test(w)) w = w.slice(0, -1); else if (re4.test(w)) w += 'e';
      }
    }
    re = /^(.+?)y$/;
    if (re.test(w)) { var fp3 = re.exec(w); stem_ = fp3[1]; re = sv; if (re.test(stem_)) w = stem_ + 'i'; }
    re = /^(.+?)(ational|tional|enci|anci|izer|bli|alli|entli|eli|ousli|ization|ation|ator|alism|iveness|fulness|ousness|aliti|iviti|biliti|logi)$/;
    if (re.test(w)) { var fp4 = re.exec(w); stem_ = fp4[1]; suffix = fp4[2]; if (mgr0.test(stem_)) w = stem_ + step2[suffix]; }
    re = /^(.+?)(icate|ative|alize|iciti|ical|ful|ness)$/;
    if (re.test(w)) { var fp5 = re.exec(w); stem_ = fp5[1]; suffix = fp5[2]; if (mgr0.test(stem_)) w = stem_ + step3[suffix]; }
    re = /^(.+?)(al|ance|ence|er|ic|able|ible|ant|ement|ment|ent|ou|ism|ate|iti|ous|ive|ize)$/; re2 = /^(.+?)(s|t)(ion)$/;
    if (re.test(w)) { var fp6 = re.exec(w); stem_ = fp6[1]; if (mgr1.test(stem_)) w = stem_; }
    else if (re2.test(w)) { var fp7 = re2.exec(w); stem_ = fp7[1] + fp7[2]; if (mgr1.test(stem_)) w = stem_; }
    re = /^(.+?)e$/;
    if (re.test(w)) { var fp8 = re.exec(w); stem_ = fp8[1]; re = mgr1; re2 = meq1; re3 = new RegExp('^' + C + v + '[^aeiouwxy]$'); if (re.test(stem_) || (re2.test(stem_) && !re3.test(stem_))) w = stem_; }
    re = /ll$/; re2 = mgr1; if (re.test(w) && re2.test(w)) w = w.slice(0, -1);
    if (firstch === 'y') w = firstch.toLowerCase() + w.substr(1);
    return w;
  }

  // ---- tokenizer -------------------------------------------------------------------------
  var UNITS = 'kg|mm|cm|km|kmph|kn|mhz|hz|kv|amps?|volts?|litres?|liters?|tonnes?|gmt|hp|rpm|mpa|db';
  function normalizeText(s) {
    s = String(s).toLowerCase().replace(/[‐-―−]/g, '-').replace(/[‘’]/g, "'").replace(/°/g, ' deg ');
    s = s.replace(/\b1\s*(?:in|:)\s*(\d+(?:\.\d+)?)/g, '1in$1');                 // "1 in 12", "1:12"
    s = s.replace(new RegExp('\\b(\\d+(?:\\.\\d+)?)\\s*(' + UNITS + ')\\b', 'g'), '$1$2');  // "60 kg" -> "60kg"
    s = s.replace(/\b(kmph|km\/h|kmh)\b/g, 'kmph');
    return s;
  }
  function rawTokens(s) {
    s = normalizeText(s);
    var out = [], m, re = /[a-z0-9]+(?:[.\/][a-z0-9]+)*/g;
    while ((m = re.exec(s))) {
      var t = m[0];
      out.push(t);
      if (/[.\/]/.test(t) && !/^\d+(?:\.\d+)+$/.test(t)) t.split(/[.\/]/).forEach(function (p) { if (p) out.push(p); });
    }
    return out;
  }
  function termOf(t) {
    if (/^\d/.test(t)) return t;
    return t.length > 3 ? stem(t) : t;
  }
  function analyze(s, keepStop) {
    var out = [], toks = rawTokens(s);
    for (var i = 0; i < toks.length; i++) {
      var t = toks[i];
      if (!keepStop && STOP.has(t)) continue;
      out.push(termOf(t));
    }
    return out;
  }

  // ---- engine ----------------------------------------------------------------------------
  var MANUAL_WORDS = {
    IRPWM: ['irpwm', 'permanent way manual', 'indian railways permanent way manual'],
    TMM: ['tmm', 'track machine manual', 'track machines manual'],
    STMM: ['stmm', 'small track machine', 'small track machines manual'],
    USFD: ['usfd manual', 'usfd'],
    AT_WELD: ['at weld manual', 'at welding manual', 'thermit welding manual', 'aluminothermic welding manual', 'at weld'],
    FBW: ['fbw', 'flash butt welding manual']
  };

  function create(index, opts) {
    opts = opts || {};
    var k1 = opts.k1 || 1.0, b = opts.b || 0.75, titleW = opts.titleWeight || 3;
    var bigramW = opts.bigram == null ? 0.5 : opts.bigram, synW = opts.syn == null ? 0.35 : opts.syn, topicW = opts.topic == null ? 1.3 : opts.topic, primaryW = opts.primary == null ? 1.15 : opts.primary, aggW = opts.agg == null ? 0 : opts.agg, tableW = opts.table == null ? 0.9 : opts.table, formW = opts.form == null ? 0.7 : opts.form;
    var docs = index.docs, N = docs.length, post = index.postings, syn = index.synonyms || [];
    var avgLen = index.meta.avgLen;
    var df = index.df;
    var maxIdf = Math.log(1 + (N - 0.5) / 1.5);
    function idf(t) { var d = df[t]; return d ? Math.log(1 + (N - d + 0.5) / (d + 0.5)) : maxIdf; }
    function getSeq(d) { return d._seq || (d._seq = analyze(d.title + ' ' + d.text).join(' ')); }
    function getTerms(d) { if (!d._terms) { d._terms = {}; analyze(d.title + ' ' + d.text).forEach(function (t) { d._terms[t] = 1; }); } return d._terms; }
    var byPara = {};
    docs.forEach(function (d, i) { var key = d.alias + '|' + d.para.toLowerCase(); (byPara[key] = byPara[key] || []).push(i); });
    var aliases = Object.keys(MANUAL_WORDS);

    var manualPhrases = [];
    aliases.forEach(function (a) { MANUAL_WORDS[a].forEach(function (w) { manualPhrases.push([a, w]); }); });
    manualPhrases.sort(function (x, y) { return y[1].length - x[1].length; });
    function detectManuals(q) {
      var lq = ' ' + normalizeText(q) + ' ', found = [];
      manualPhrases.forEach(function (pw) {
        var re = new RegExp('([^a-z])' + pw[1].replace(/ /g, '\\s+') + '(?=[^a-z])');
        if (re.test(lq)) { if (found.indexOf(pw[0]) < 0) found.push(pw[0]); lq = lq.replace(re, '$1 '); }  // blank out: "small track machines manual" must not also hit TMM
      });
      return found;
    }
    var TOPIC = { FBW: ['flash butt'], AT_WELD: ['thermit', 'alumino thermic', 'aluminothermic', 'at weld'],
                  USFD: ['ultrasonic', 'usfd', 'probe', 'flaw detect'], STMM: ['small track machine'],
                  TMM: ['tamping', 'track machine', 'stabiliser', 'stabilizer', 'ballast regulating', 'ballast cleaning'] };
    function topicManuals(q) {
      var lq = normalizeText(q), out = [];
      Object.keys(TOPIC).forEach(function (a) { if (TOPIC[a].some(function (w) { return lq.indexOf(w) >= 0; })) out.push(a); });
      return out;
    }
    function detectParas(q) {
      var lq = normalizeText(q), out = [], m;
      var re = /\b(?:para(?:graph)?s?|clause|item|sec(?:tion)?)\.?\s*(?:no\.?)?\s*(\d+(?:\.\d+)*[a-z]?)(?:\s*(?:,|and|&)\s*(\d+(?:\.\d+)*[a-z]?))*/g;
      while ((m = re.exec(lq))) { out.push(m[1]); if (m[2]) out.push(m[2]); }
      // "IRPWM 429", "IRPWM 2024 225", "permanent way manual 328": a manual name, an optional year, then the number
      var names = manualPhrases.map(function (pw) { return pw[1].replace(/ /g, '\\s+'); }).join('|');
      var re2 = new RegExp('(?:' + names + ')\\s+(?:(?:19|20)\\d\\d\\s+)?(\\d+(?:\\.\\d+)*[a-z]?)\\b', 'g');
      while ((m = re2.exec(lq))) out.push(m[1]);
      return out.filter(function (x, i, a) { return a.indexOf(x) === i; });
    }

    function containsSeq(terms, key) {
      for (var i = 0; i + key.length <= terms.length; i++) {
        var ok = true;
        for (var j = 0; j < key.length; j++) if (terms[i + j] !== key[j]) { ok = false; break; }
        if (ok) return true;
      }
      return false;
    }
    var synAlts = {};      // single-word trigger -> alternatives (each a list of words that must all occur)
    syn.forEach(function (rule) { if (rule[0].length === 1) (synAlts[rule[0][0]] = synAlts[rule[0][0]] || []).push(rule[1]); });
    function expand(terms) {
      var extra = {};
      syn.forEach(function (rule) {
        if (containsSeq(terms, rule[0])) rule[1].forEach(function (s) { if (terms.indexOf(s) < 0) extra[s] = 1; });
      });
      return Object.keys(extra);
    }

    function search(query, o) {
      o = o || {};
      var k = o.k || 10;
      var qTerms = analyze(query).filter(function (t, i, a) { return a.indexOf(t) === i; });
      var manuals = o.manual ? [o.manual] : detectManuals(query);
      var topics = topicW !== 1 ? topicManuals(query) : [];
      var paras = detectParas(query);
      var extraTerms = expand(qTerms);
      var scores = new Float64Array(N), hit = new Float64Array(N);
      function accumulate(term, weight) {
        var p = post[term]; if (!p) return;
        var w = idf(term) * weight;
        for (var j = 0; j < p.length; j += 3) {
          var di = p[j], tfb = p[j + 1], tft = p[j + 2];
          var tf = tfb + titleW * tft;
          var len = docs[di].len;
          var norm = k1 * (1 - b + b * len / avgLen);
          scores[di] += w * (tf * (k1 + 1)) / (tf + norm);
        }
      }
      qTerms.forEach(function (t) { accumulate(t, 1); });
      extraTerms.forEach(function (t) { accumulate(t, synW); });

      // query bigrams for phrase re-ranking
      var qSeq = analyze(query);
      var bigrams = [];
      for (var i = 0; i + 1 < qSeq.length; i++) bigrams.push(qSeq[i] + ' ' + qSeq[i + 1]);

      var cand = [];
      for (var d = 0; d < N; d++) if (scores[d] > 0 && (!(o.strict && manuals.length) || manuals.indexOf(docs[d].alias) >= 0)) cand.push(d);   // strict: only the named manual(s)
      cand.sort(function (a, c2) { return scores[c2] - scores[a]; });
      cand = cand.slice(0, 200);

      // identifier matches are candidates even if the words do not overlap
      var idDocs = {};
      paras.forEach(function (p) {
        (manuals.length ? manuals : aliases).forEach(function (a) {
          (byPara[a + '|' + p] || []).forEach(function (di) { idDocs[di] = manuals.length ? 2 : 1; if (cand.indexOf(di) < 0) cand.push(di); });
        });
      });

      var top = 0;
      var results = cand.map(function (di) {
        var d0 = docs[di], s = scores[di];
        if (manuals.length && manuals.indexOf(d0.alias) < 0) s *= 0.55;      // named manual scopes the answer
        if (bigrams.length) {
          var seq = getSeq(d0), n = 0;
          bigrams.forEach(function (bg) { if (seq.indexOf(bg) >= 0) n++; });
          s *= 1 + bigramW * n / bigrams.length;
        }
        if (topics.length && topics.indexOf(d0.alias) >= 0 && !manuals.length) s *= topicW;
        else if (!topics.length && !manuals.length && d0.alias === 'IRPWM') s *= primaryW;   // the permanent way manual is the default authority
        if (d0.kind === 'table') s *= d0.form ? tableW * formW : tableW;                                  // structured table rows: helpful for values, noisy otherwise
        if (idDocs[di] === 1) s += 6;                                         // paragraph number named without a manual
        return { di: di, score: s };
      });
      // manual and paragraph both named: that paragraph leads every other passage
      var adjTop = 0;
      results.forEach(function (x) { if (!idDocs[x.di] && x.score > adjTop) adjTop = x.score; });
      results.forEach(function (x) { if (idDocs[x.di] === 2) x.score = Math.max(x.score, adjTop) + 5; });
      results.sort(function (a, c2) { return c2.score - a.score; });
      top = results.length ? results[0].score : 0;

      // clause-level score: best passage plus a fraction of its runner-up passage (a clause that answers in two places)
      if (aggW) {
        var runner = {};
        results.forEach(function (x) { var c2 = docs[x.di].clause; if (runner[c2] === undefined) runner[c2] = -1; else if (runner[c2] === -1) runner[c2] = x.score; });
        results.forEach(function (x) { var rr = runner[docs[x.di].clause]; if (rr > 0 && x.score >= rr) x.score += aggW * rr; });
        results.sort(function (a, c2) { return c2.score - a.score; });
      }
      // best passage per clause
      var seen = {}, out = [];
      for (var r = 0; r < results.length && out.length < k; r++) {
        var dd = docs[results[r].di];
        if (seen[dd.clause]) continue;
        seen[dd.clause] = 1;
        out.push({ clause: dd.clause, passage: dd.id, score: results[r].score, alias: dd.alias, doc: dd.doc, para: dd.para,
                   title: dd.title, chapter: dd.chapter, page: dd.page, type: dd.type, kind: dd.kind, tableId: dd.tableId, form: !!dd.form, text: dd.text, matched: matchedTerms(qTerms, dd) });
      }

      // Evidence coverage: idf mass of query terms present in the best passage / idf mass of all query terms.
      // coverage3 pools the top three passages (a question can be answered across neighbouring passages).
      // A question word counts as covered when the passage has it OR has what the synonym rules say it stands for
      // ("aluminothermic" is covered by "alumino-thermic" or "thermit"): the manuals do not use one spelling.
      function cover(docIdxs) {
        var present = {};
        docIdxs.forEach(function (di) { var t = getTerms(docs[di]); Object.keys(t).forEach(function (k2) { present[k2] = 1; }); });
        var tot = 0, got = 0;
        qTerms.forEach(function (t) {
          var w = idf(t); tot += w;
          if (present[t] || (synAlts[t] || []).some(function (alt) { return alt.every(function (a) { return present[a]; }); })) got += w;
        });
        return tot ? got / tot : 0;
      }
      var coverage = 0, coverage3 = 0;
      if (out.length && qTerms.length) {
        coverage = cover([results[0].di]);
        coverage3 = cover(results.slice(0, 3).map(function (r2) { return r2.di; }));
      }
      var identifierHit = !!(results.length && idDocs[results[0].di]);
      return { query: query, terms: qTerms, identifierHit: identifierHit, expanded: extraTerms, manuals: manuals, paras: paras, results: out, topScore: top, coverage: coverage, coverage3: coverage3 };
    }

    function matchedTerms(qTerms, d) {
      var present = getTerms(d);
      return qTerms.filter(function (t) { return present[t]; });
    }

    // ---- extractive answer: the sentences of the best passage that carry the question's terms ----------
    var VALUE_Q = /\b(how (?:many|much|long|far|often|frequently)|maximum|minimum|limit|range|permissible|distance|interval|frequency|speed|depth|width|length|tolerance)\b/i;
    function splitSentences(text) {
      var out = [], lineRe = /[^\n]+/g, lm;
      while ((lm = lineRe.exec(text))) {
        var line = lm[0], base = lm.index, last = 0, sm, re = /(?<=[.!?;])\s+(?=[A-Z(\d])/g;
        while ((sm = re.exec(line))) { out.push({ start: base + last, end: base + sm.index }); last = sm.index + sm[0].length; }
        out.push({ start: base + last, end: base + line.length });
      }
      // glue fragments shorter than 25 characters to the next sentence ("(a)", "Note -")
      var merged = [];
      for (var i = 0; i < out.length; i++) {
        var cur = out[i];
        while (cur.end - cur.start < 25 && i + 1 < out.length) { cur = { start: cur.start, end: out[++i].end }; }
        merged.push(cur);
      }
      return merged.map(function (m) { return { start: m.start, end: m.end, text: text.slice(m.start, m.end) }; });
    }
    function extractSentences(query, text, max) {
      max = max || 3;
      var qTerms = analyze(query).filter(function (t, i, a) { return a.indexOf(t) === i; });
      var extra = expand(qTerms), wantsValue = VALUE_Q.test(query);
      var qBigrams = [], qs = analyze(query);
      for (var i = 0; i + 1 < qs.length; i++) qBigrams.push(qs[i] + ' ' + qs[i + 1]);
      var sents = splitSentences(text).map(function (s) {
        var toks = analyze(s.text), set = {};
        toks.forEach(function (t) { set[t] = 1; });
        var score = 0;
        qTerms.forEach(function (t) { if (set[t]) score += idf(t); });
        extra.forEach(function (t) { if (set[t]) score += 0.35 * idf(t); });
        var seq = toks.join(' ');
        qBigrams.forEach(function (bg) { if (seq.indexOf(bg) >= 0) score += 0.6 * maxIdf; });
        if (wantsValue && /\d\s*(mm|cm|m|km|kmph|kg|t|%|days?|months?|years?|hours?|minutes?|degrees?|deg)\b/i.test(s.text)) score += 0.8 * maxIdf;
        s.score = score;
        return s;
      });
      var best = Math.max.apply(null, sents.map(function (s) { return s.score; }).concat([0]));
      if (best <= 0) return [];
      var picked = sents.filter(function (s) { return s.score >= 0.45 * best; })
        .sort(function (a, b) { return b.score - a.score; }).slice(0, max)
        .sort(function (a, b) { return a.start - b.start; });
      return picked;
    }

    /* A table passage is one row per line, each cell already prefixed by its column header: answer with the rows
       that match the question, whole, instead of cutting the text into sentences. */
    function extractRows(query, text, max) {
      var qTerms = analyze(query).filter(function (t, i, a) { return a.indexOf(t) === i; });
      var extra = expand(qTerms), off = 0;
      var rows = text.split('\n').map(function (line) {
        var r = { start: off, end: off + line.length, text: line, score: 0 };
        off += line.length + 1;
        var set = {};
        analyze(line).forEach(function (t) { set[t] = 1; });
        qTerms.forEach(function (t) { if (set[t]) r.score += idf(t); });
        extra.forEach(function (t) { if (set[t]) r.score += 0.35 * idf(t); });
        return r;
      }).filter(function (r) { return r.text.trim(); });
      var best = Math.max.apply(null, rows.map(function (r) { return r.score; }).concat([0]));
      if (best <= 0) return [];
      return rows.filter(function (r) { return r.score >= 0.6 * best; })
        .sort(function (a, b) { return b.score - a.score; }).slice(0, max || 3)
        .sort(function (a, b) { return a.start - b.start; });
    }

    var refuseBelow = opts.refuseBelow == null ? 0.66 : opts.refuseBelow;
    /* One call for the UI and tests: an answer with cited sentences, or an explicit refusal. */
    function answer(query, o) {
      var res = search(query, o);
      var top = res.results[0];
      var supported = !!top && (res.coverage >= refuseBelow || res.identifierHit);
      if (!supported) return { status: 'no_evidence', query: query, coverage: res.coverage, results: [], search: res };
      var second = res.results[1];
      var margin = second && second.score > 0 ? top.score / second.score : 9;
      var confidence = res.identifierHit || (res.coverage >= 0.85 && margin >= 1.15) ? 'high' : (res.coverage >= 0.75 ? 'medium' : 'low');
      return { status: 'answer', query: query, confidence: confidence, coverage: res.coverage, margin: margin,
               sentences: top.kind === 'table' ? extractRows(query, top.text, 3) : extractSentences(query, top.text, 3), best: top, related: res.results.slice(1, 5), search: res };
    }

    return { search: search, answer: answer, extractSentences: extractSentences, extractRows: extractRows, analyze: analyze, size: N, refuseBelow: refuseBelow };
  }

  var api = { create: create, analyze: analyze, stem: stem, normalizeText: normalizeText, STOP: STOP };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RDSOSearch = api;
})(typeof window !== 'undefined' ? window : globalThis);
