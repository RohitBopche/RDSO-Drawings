/* RDSO offline chat (dialogue layer over the retrieval engine).
 *
 * No network, no model: every statement in a reply is a sentence or table row copied from a manual, with its citation, or
 * a value extracted from that provision, or a fixed sentence of the assistant's own (greeting, refusal, clarification).
 * What it adds over a search box: conversation memory (follow-ups such as "what about 60 kg rails?"), clarifying questions
 * when two manuals answer equally well, "more / source / what else" commands, related provisions and cross-references as
 * follow-up suggestions, and an honest refusal with the nearest topics when nothing supports an answer.
 *
 *   const chat = RDSOChat.create(RDSOSearch.create(index), { extras: RDSO_CLAUSE_EXTRAS, xrefs: RDSO_CROSSREFS });
 *   const reply = chat.ask("How is casual renewal of a fractured rail carried out?");
 */
(function (root) {
  'use strict';

  var MANUALS = {
    IRPWM: 'Indian Railways Permanent Way Manual', TMM: 'Track Machine Manual', STMM: 'Small Track Machines Manual',
    USFD: 'Ultrasonic Flaw Detection of Rails Manual', AT_WELD: 'Alumino-Thermic Welding Manual', FBW: 'Flash Butt Welding Manual'
  };
  var EXAMPLES = [
    'How is casual renewal of a fractured rail carried out?',
    'What does Para 429 of IRPWM say?',
    'What is the rail temperature range for destressing LWR?',
    'How often is the track inspected by the PWI?'
  ];
  var UNIT_LABEL = { kmph: 'km/h', degC: '°C', deg: '°', kn: 'kN', mpa: 'MPa', gmt: 'GMT', khz: 'kHz', mhz: 'MHz' };

  function label(r) { return r.alias + ' Para ' + r.para; }
  function plain(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }
  function titleOf(r) { return plain(String(r.title || '').split(' Chapter ')[0]); }

  /* The engine picks sentences by line; manuals hard-wrap lines, so a pick can be half a sentence. Expand each pick to the whole
     sentence of the passage (split after . ; : ? before a capital letter, bracketed number or digit) and drop duplicates. */
  function wholeSentences(passage, picks, max) {
    var flat = passage.replace(/\s+/g, ' '), bounds = [], last = 0, re = /[.;:?!]\s+(?=[A-Z(\d])/g, m;
    var ABBR = /(?:^|[\s(\/])(?:[A-Za-z]|No|Nos|Sr|Jr|Fig|Figs|Dr|Mr|Drg|Rly|Rlys|Dy|Dept|etc|viz|vs|approx|max|min|ref|para|sl|km|dia)$/i;
    while ((m = re.exec(flat))) {
      if (m[0][0] === '.' && ABBR.test(flat.slice(Math.max(0, m.index - 8), m.index))) continue;     // "P.", "Sr.", "Fig." do not end a sentence
      bounds.push([last, m.index + 1]); last = m.index + m[0].length;
    }
    bounds.push([last, flat.length]);
    var words = function (t) { return plain(t).split(' ').slice(0, 4).join(' '); };
    var out = [], seen = {};
    picks.forEach(function (p2) {
      var head = words(p2.text), at = flat.indexOf(head);
      if (at < 0) { out.push(plain(p2.text)); return; }
      for (var i = 0; i < bounds.length; i++) {
        if (at >= bounds[i][0] && at < bounds[i][1] + 1) {
          var sent = flat.slice(bounds[i][0], bounds[i][1]);
          if (/:$/.test(sent) && sent.split(' ').length < 8 && bounds[i + 1]) sent += ' ' + flat.slice(bounds[i + 1][0], bounds[i + 1][1]);   // a heading line carries the sentence after it
          if (!seen[sent]) { seen[sent] = 1; out.push(sent.length > 420 ? sent.slice(0, 417).replace(/\s+\S*$/, '') + '…' : sent); }
          return;
        }
      }
    });
    return out.slice(0, max || 3);
  }

  /* A sentence worth showing as an answer: not a bare heading ("11.4.1 Equipment:"), a list marker, a back-reference or a stub. */
  function informative(t) {
    var x = plain(t);
    var words = x.replace(/^\(?[0-9a-z.]{1,8}\)?\s*/i, '').split(' ').filter(function (w) { return /[A-Za-z]{2,}/.test(w); });
    if (words.length < 5) return false;
    if (/^\(?back to\b/i.test(x) || /^\(?acs\b/i.test(x)) return false;
    if (/:$/.test(x) && words.length < 8) return false;
    return true;
  }

  function fmtValue(v) {
    var cmp = v[0], lo = v[1], hi = v[2], u = UNIT_LABEL[v[3]] || v[3];
    var t = cmp === 'max' ? 'at most ' + hi + ' ' + u : cmp === 'min' ? 'at least ' + lo + ' ' + u :
            cmp === 'range' ? lo + ' to ' + hi + ' ' + u : cmp === 'tolerance' ? lo + ' / +' + hi + ' ' + u : lo + ' ' + u;
    return { quantity: v[4] || null, text: t, quote: v[5], near: v[6] || [] };
  }

  function create(engine, ctx) {
    ctx = ctx || {};
    var tables = ctx.tables || {}, editions = ctx.editions || {};
    var tablesOf = {};      // owner clause -> table ids
    Object.keys(tables).forEach(function (id) { var k = tables[id].k; if (k) (tablesOf[k] = tablesOf[k] || []).push(id); });
    var extras = ctx.extras || {}, xrefs = ctx.xrefs || null;
    var state = { last: null, turns: [], scope: null };
    function scopeOpts(o) { if (state.scope) { o.manual = state.scope; o.strict = true; if (state.chapter) o.chapter = state.chapter; } return o; }

    function cite(r) {
      return { clause: r.clause, label: label(r), alias: r.alias, para: r.para, page: r.page, title: titleOf(r), doc: r.doc, kind: r.kind || null };
    }

    function isFollowUp(text, first) {
      if (!state.last) return false;
      if (first.manuals.length || first.paras.length) return false;       // names its own manual or paragraph: a new question
      var content = engine.analyze(text).length;
      return /^\s*(and|also|but|then|so|what about|how about|what if)\b/i.test(text) ||
             /\b(it|its|that|this|those|these|they|them|there|same|such)\b/i.test(text) || content <= 2;
    }

    function meta(text) {
      var t = plain(text).toLowerCase().replace(/[?.!]+$/, '').replace(/^(and |also |please |can you |could you |what about |how about |show me |show |give me |tell me |let me see )+/, '');
      if (/^(hi|hello|hey|namaste|good (morning|afternoon|evening))\b/.test(plain(text).toLowerCase()) && plain(text).split(' ').length <= 4) return 'greeting';
      if (/^(thanks|thank you|ok thanks|great|got it|okay|ok)$/.test(t)) return 'thanks';
      if (/^(help|what can you do|who are you|what are you|how do you work|what do you know)/.test(t)) return 'help';
      if (/^(clear|reset|start over|new (question|topic|chat))$/.test(t)) return 'reset';
      if (/^(more|more details?|details|full text|(the )?(full )?(text|passage|paragraph)|read (it|the paragraph)|the rest)$/.test(t)) return 'more';
      if (/^((the )?sources?|(the )?page|which page|what page|where (is|was) (this|that|it)( from)?|cite|(the )?citation)$/.test(t)) return 'source';
      if (/^(what else|anything else|related( provisions)?|see also|other (provisions|paragraphs)|more like this)$/.test(t)) return 'related';
      return null;
    }

    function followups(primary, related, xr) {
      var out = [];
      (xr || []).slice(0, 2).forEach(function (r) { out.push('What does ' + r + ' say?'); });
      (related || []).slice(0, 3 - out.length).forEach(function (r) { out.push('What does ' + label(r) + ' say?'); });
      var seen = {};
      return out.filter(function (q) { if (seen[q]) return false; seen[q] = 1; return true; }).slice(0, 3);
    }

    function referencesOf(clauseId) {
      if (!xrefs || !xrefs.out) return [];
      var seen = {}, out = [];
      (xrefs.out[clauseId] || []).forEach(function (r) {
        // r = [raw, kind, status, [targets], ...] : only resolved paragraph references become suggestions
        var tg = Array.isArray(r[3]) ? r[3][0] : r[3];
        if (r[1] === 'para' && r[2] === 'RESOLVED' && tg && !seen[tg] && tg !== clauseId) {
          seen[tg] = 1;
          var m = /^CLAUSE:([^:]+):[^:]+:PARA_(.+)$/.exec(tg);
          if (m) out.push(m[1] + ' Para ' + m[2].replace(/_/g, '.'));
        }
      });
      return out.slice(0, 3);
    }

    /* The matching row(s) of a table with their column headers. Wide tables show only the identifying columns and the columns
       the question's words point at, so "speed of the utility track vehicle" shows the machine name and the speed column. */
    function tableView(query, tableId) {
      var T = tables[tableId];
      if (!T || !T.r.length) return null;
      var qs = engine.analyze(query).filter(function (t, i, a) { return a.indexOf(t) === i; });
      function hits(text) { var set = {}; engine.analyze(text).forEach(function (t) { set[t] = 1; }); return qs.filter(function (t) { return set[t]; }).length; }
      var colScore = T.h.map(hits);
      var rowScore = T.r.map(function (row) { return row.reduce(function (a, c) { return a + hits(c); }, 0); });
      var best = Math.max.apply(null, rowScore.concat([0]));
      var rowIdx = [];
      T.r.forEach(function (_, i) { if (best > 0 && rowScore[i] >= Math.max(1, 0.6 * best)) rowIdx.push(i); });
      if (!rowIdx.length) rowIdx = [0];
      rowIdx = rowIdx.slice(0, 4);
      var cols = T.h.map(function (_, j) { return j; });
      if (cols.length > 6) {
        var keep = { 0: 1 }, count = 1, add = function (j) { if (!keep[j] && count < 6) { keep[j] = 1; count++; } };
        rowIdx.forEach(function (i) { T.r[i].forEach(function (c, j) { if (hits(c) > 0) add(j); }); });                 // cells the question's words point at
        var headHits = 0;
        cols.forEach(function (j) {                                                                                      // columns named by the question, if the row has a value there
          if (colScore[j] > 0 && headHits < 3 && rowIdx.some(function (i) { return (T.r[i][j] || '').trim(); })) { add(j); headHits++; }
        });
        if (count < 3) {                                                                                                  // otherwise the most descriptive column
          var nameCol = -1, bestLen = 0;
          T.h.forEach(function (_, j) { if (j > 0) { var len = rowIdx.reduce(function (a2, i) { return a2 + (T.r[i][j] || '').length; }, 0); if (len > bestLen) { bestLen = len; nameCol = j; } } });
          if (nameCol > 0) add(nameCol);
        }
        cols = cols.filter(function (j) { return keep[j]; });
      }
      return {
        id: tableId, page: T.p, caption: plain(T.c), totalRows: T.n, totalCols: T.h.length, truncatedColumns: cols.length < T.h.length,
        columns: cols.map(function (j) { return plain(T.h[j]); }),
        rows: rowIdx.map(function (i) { return { cells: cols.map(function (j) { return (T.r[i][j] || '').replace(/\n/g, '; '); }), hit: cols.map(function (j) { return hits(T.r[i][j] || '') > 0; }) }; }),
        full: { columns: T.h.map(plain), rows: T.r.slice(0, 60).map(function (r) { return r.map(function (c) { return (c || '').replace(/\n/g, '; '); }); }) }
      };
    }

    /* A paragraph often carries its numbers in a table of its own ("Rail Section / Vertical Wear"): when the answer is a prose passage
       and one of the paragraph's tables matches several of the question's words, its matching rows are shown under their headers. */
    function ownedTableViews(searched, clause) {
      var scored = [];
      (tablesOf[clause] || []).forEach(function (id) {
        var v = tableView(searched, id); if (!v) return;
        var score = v.rows.reduce(function (a, r) { return a + r.hit.filter(Boolean).length; }, 0);
        var qset = {}; engine.analyze(searched).forEach(function (t) { qset[t] = 1; });
        var headTerms = {}; v.columns.forEach(function (c) { engine.analyze(c).forEach(function (t) { if (qset[t]) headTerms[t] = 1; }); });
        score += 2 * Object.keys(headTerms).length;      // words of the question that name the table's columns count double
        if (score >= 2) scored.push({ v: v, score: score });
      });
      scored.sort(function (x, y) { return y.score - x.score; });
      // a two-part question can need two tables ("vertical wear" and "loss of section"): keep those about as good as the best
      return scored.filter(function (x) { return x.score >= 0.6 * scored[0].score; }).slice(0, 2).map(function (x) { return x.v; });
    }

    /* Correction-slip marks the manual itself prints in the paragraph, "(ACS - 7)" or "(CS-3)": the paragraph was amended by that slip. */
    function amendmentsOf(text) {
      var seen = {}, out = [], re = /\(\s*(ACS|CS)\s*[-\u2013]\s*(\d+)\s*\)/g, m;
      while ((m = re.exec(text || ''))) { var k = m[1] + ' ' + m[2]; if (!seen[k]) { seen[k] = 1; out.push(k); } }
      return out;
    }

    var QNUM = /\b(how (?:many|much|long|far|often|frequently)|maximum|minimum|limit|range|permissible|distance|interval|frequency|speed|depth|width|length|tolerance|time|temperature|duration|density|gauge|clearance|spacing|height|size|period|number|value|wear|weight|area|gap|load|deflection)\b/i;
    function pointsOf(best, searched, picked) {
      if (best.kind === 'table') return picked.map(function (s2) { return plain(s2.text); });
      var maxPts = plain(searched).split(' ').length >= 12 ? 6 : 3;      // a long, multi-part question needs more of the passage
      var whole = (QNUM.test(searched) && engine.clauseText && engine.clauseText(best.clause)) || best.text;      // a quantity is often in a later chunk of the paragraph
      if (maxPts > 3) picked = engine.extractSentences(searched, whole, maxPts);
      var all = wholeSentences(whole, picked, maxPts);
      var good = all.filter(informative);
      // The numbers are often in table-like lines inside the passage rather than in a sentence ("Rails 60 kg 90 UTS ..."):
      // for a quantity question, add the passage's best-matching lines that carry a number.
      var NUMBER = /\d\s*(?:mm|cm|m|km|kmph|kg|t|%|days?|months?|years?|hours?|minutes?|seconds?|degrees?|deg|[kM]?Hz|°|˚|kN|MPa|g|per\s+km)(?![a-z])|\d\s*(?:to|-)\s*\d|\b\d{3,}\b/i;
      if (QNUM.test(searched)) {
        var qw = (searched.toLowerCase().match(/[a-z]{3,}/g) || []).filter(function (w) { return !/^(what|which|the|are|and|for|with|from|that|this|does|how|many|much|per|via)$/.test(w); });
        var raw = whole.split('\n').map(plain).filter(Boolean), cand = [];
        var df5 = function (w) { var k = w.slice(0, 5), n = raw.filter(function (l2) { return l2.toLowerCase().indexOf(k) >= 0; }).length; return Math.max(1, n); };      // a word found in many lines names the topic, not a value
        raw.forEach(function (ln, i) {
          if (!NUMBER.test(ln) || ln.split(' ').length < 3) return;
          var pv = i ? raw[i - 1] : '';
          var label = pv && pv.split(' ').length <= 4 && !/\d/.test(pv) ? pv + ' ' : '';      // a short label line above the numbers names them
          var lw = (label + ln).toLowerCase(), ov = qw.reduce(function (a2, w) { return a2 + (lw.indexOf(w.slice(0, 5)) >= 0 ? 1 / df5(w) : 0); }, 0);
          cand.push({ i: i, ov: ov, t: label + ln });
        });
        var lines = cand.sort(function (x, y) { return y.ov - x.ov || x.i - y.i; }).slice(0, maxPts > 3 ? 7 : 4).sort(function (x, y) { return x.i - y.i; }).map(function (c2) { return c2.t; });
        var have = good.join(' ');
        lines = lines.filter(function (t) { return have.indexOf(t) < 0; });
        if (lines.length) return good.concat(lines).slice(0, maxPts + (maxPts > 3 ? 5 : 2));
      }
      if (good.length) return good;
      // every pick was a heading or stub: take the best-scoring informative sentences of the whole passage instead
      var more = wholeSentences(best.text, engine.extractSentences(searched, best.text, 8), 8).filter(informative);
      return (more.length ? more : all).slice(0, maxPts);
    }

    function answerFrom(text, searched, isFollow) {
      var ans = engine.answer(searched, scopeOpts({ k: 8 }));
      if (ans.status !== 'answer') return { ans: ans };
      // Only the six manuals are sources (the index also holds hand-made graph notes), and the first candidate with a sentence
      // worth showing is preferred to a bare heading, so "11.4.1 Equipment:" is not offered as an answer.
      var cands = [ans.best].concat(ans.related).filter(function (r) { return MANUALS[r.alias]; });
      if (!cands.length) return { ans: { status: 'no_evidence', coverage: ans.coverage, results: [], search: ans.search } };
      var best = cands[0], sentences = best === ans.best ? ans.sentences : engine.extractSentences(searched, best.text, 3);
      // For a quantity question a table that scores about as well as the best prose passage is the better answer: its rows hold the numbers.
      if (QNUM.test(searched) && best.kind !== 'table') {
        for (var ti = 1; ti < cands.length && ti < 4; ti++) {
          if (cands[ti].kind === 'table' && cands[ti].score >= 0.9 * best.score && tableView(searched, cands[ti].tableId)) {
            var tv = tableView(searched, cands[ti].tableId);
            if (tv.rows.reduce(function (a, r) { return a + r.hit.filter(Boolean).length; }, 0) >= 2) { best = cands[ti]; sentences = engine.extractRows(searched, best.text, 3); break; }
          }
        }
      }
      // A question for a quantity ("what is the speed of ...", "how long ...") is answered by a candidate that shows a number.
      var wantsNumber = /\b(how (?:many|much|long|far|often|frequently)|maximum|minimum|limit|range|permissible|distance|interval|frequency|speed|depth|width|length|tolerance|time|temperature|duration|density|gauge|clearance|spacing|height|size|period|number|value|wear)\b/i.test(searched);
      var good = function (pts, cand) { return pts.some(informative) && (!wantsNumber || (cand && cand.kind === 'table') || pts.some(function (t) { return /\d\s*(?:mm|cm|m|km|kmph|kg|t|%|days?|months?|years?|hours?|minutes?|seconds?|degrees?|deg|[kM]?Hz|°|˚|kN|MPa|per\s+km)(?![a-z])|\d\s*(?:to|-)\s*\d/i.test(t); })); };
      if (!good(pointsOf(best, searched, sentences), best)) {
        var found = null;
        for (var pass = 0; pass < 2 && !found; pass++) {      // a table that shows the number is preferred to prose that merely contains one
          for (var ci = 1; ci < cands.length && ci < 4 && !found; ci++) {
            if (pass === 0 && cands[ci].kind !== 'table') continue;
            var alt = engine.extractSentences(searched, cands[ci].text, 3);
            if (good(pointsOf(cands[ci], searched, alt), cands[ci])) found = { r: cands[ci], s: alt };
          }
        }
        if (found) { best = found.r; sentences = found.s; }
        if (!pointsOf(best, searched, sentences).some(informative)) {
          for (var cj = 1; cj < cands.length && cj < 4; cj++) {
            var alt2 = engine.extractSentences(searched, cands[cj].text, 3);
            if (pointsOf(cands[cj], searched, alt2).some(informative)) { best = cands[cj]; sentences = alt2; break; }
          }
        }
      }
      var rel = cands.filter(function (r) { return r.clause !== best.clause; });
      var ex = extras[best.clause] || {};
      var reply = {
        kind: 'answer', confidence: ans.confidence, interpreted: isFollow ? searched : null,
        points: pointsOf(best, searched, sentences).map(function (t) { return { text: t, cite: cite(best) }; }),
        primary: Object.assign(cite(best), { text: best.text, isTable: best.kind === 'table' }),
        values: [],
        subparas: (ex.s || []).map(function (s) { return { para: s[0], clause: s[1] }; }),
        drawings: (ex.d || []).map(function (d) { return { number: d[0], file: d[1] }; }),
        lead: ans.confidence === 'low' ? 'I am not sure this answers your question. The closest passage I found:' : null,
        caveat: ans.confidence === 'low' ? 'Low confidence: this may not answer your question. Check the source page, or name the manual or paragraph.' : null,
        table: best.kind === 'table' ? tableView(searched, best.tableId) : null,
        edition: editions[best.alias] ? editions[best.alias].title + ', ' + editions[best.alias].edition : null,
        amendments: amendmentsOf(engine.clauseText ? engine.clauseText(best.clause) : best.text),
        alsoSee: [], related: rel.slice(0, 4).map(cite), followups: [],
        ownedTables: best.kind === 'table' ? [] : ownedTableViews(searched, best.clause)
      };
      // a second provision that is nearly as good is part of the answer (answers often span two paragraphs)
      var second = rel[0];
      if (second && second.score >= 0.85 * best.score && second.clause !== best.clause) {
        var sent = second.kind === 'table' ? engine.extractRows(searched, second.text, 1) : wholeSentences(second.text, engine.extractSentences(searched, second.text, 1), 1);
        var st = sent.length && (sent[0].text ? plain(sent[0].text) : sent[0]);
        if (st && informative(st)) reply.alsoSee.push({ text: st, cite: cite(second) });
      }
      reply.ownedTable = reply.ownedTables[0] || null;
      var shown = reply.points.map(function (p2) { return p2.text; }).join(' ');
      reply.values = (ex.v || []).filter(function (v) { return shown.indexOf(plain(v[5])) >= 0 && !(v[3] === 'kg' && !v[4]); }).slice(0, 4).map(fmtValue);   // only values that sit in a sentence shown above
      reply.followups = followups(best, rel, referencesOf(best.clause));
      reply.ambiguous = !ans.search.identifierHit && ans.confidence !== 'high' && rel[0] && rel[0].alias !== best.alias &&
                        rel[0].score >= 0.95 * best.score && !ans.search.manuals.length;
      return { ans: ans, reply: reply };
    }

    function ask(text) {
      text = plain(text);
      var turn = { user: text };
      state.turns.push(turn);
      var reply = respond(text);
      turn.reply = reply;
      return reply;
    }

    function respond(text) {
      if (!text) return { kind: 'help', text: 'Type a question about the loaded manuals.', examples: EXAMPLES };
      var m = meta(text);
      if (m === 'greeting') return { kind: 'greeting', text: 'Hello. I answer questions from six railway manuals, offline, and I show where every statement comes from.', examples: EXAMPLES };
      if (m === 'thanks') return { kind: 'thanks', text: 'You are welcome. Ask another question whenever you like.' };
      if (m === 'reset') { state.last = null; return { kind: 'reset', text: 'Started a new conversation.' }; }
      if (m === 'help') return { kind: 'help', text: 'I search six manuals (' + Object.keys(MANUALS).map(function (k) { return MANUALS[k] + ' (' + k + ')'; }).join('; ') +
        ') and answer with the exact sentences or table rows, each with its paragraph and page. Name a manual or a paragraph number to narrow a question. I say so when the manuals do not answer it.', examples: EXAMPLES, manuals: MANUALS };
      if (m && !state.last) return { kind: 'no_context', text: 'Ask a question first; then I can show more, the source page, or related provisions.' };
      if (m === 'more') return { kind: 'more', primary: state.last.primary, text: state.last.primary.text };
      if (m === 'source') return { kind: 'source', primary: state.last.primary,
                                   text: 'That answer comes from ' + state.last.primary.label + ', page ' + state.last.primary.page + ' of the ' + (MANUALS[state.last.primary.alias] || state.last.primary.alias) + '.' };
      if (m === 'related') return { kind: 'related_list', related: state.last.related, text: state.last.related.length ? 'Related provisions:' : 'I found no closely related provisions.' };

      var first = engine.search(text, scopeOpts({ k: 4 }));
      var explicit = state.last && !first.manuals.length && !first.paras.length &&
        (/^\s*(and|also|but|then|so|what about|how about|what if)\b/i.test(text) || /\b(it|its|that|this|those|these|they|them|there|same|such)\b/i.test(text));
      var short = state.last && !first.manuals.length && !first.paras.length && engine.analyze(text).length <= 2;
      var usable = state.last && state.last.confidence !== 'low';
      var fresh = answerFrom(text, text, false), follow = false, out = fresh;
      if (usable && (explicit || short)) {
        var joined = answerFrom(text, text + ' ' + state.last.focus, true);
        var freshGood = fresh.reply && fresh.ans.confidence !== 'low' && fresh.ans.coverage >= 0.85;
        if (joined.reply && (explicit || !freshGood) && (!fresh.reply || explicit || joined.ans.coverage > fresh.ans.coverage)) { out = joined; follow = true; }
      }
      if (!out.reply) {
        var near = (out.ans.search && out.ans.search.results || first.results).slice(0, 3).map(cite);
        return { kind: 'no_evidence', coverage: out.ans.coverage,
                 text: 'I could not find this in the loaded manuals: only ' + Math.round(out.ans.coverage * 100) + '% of your key terms occur together in any one passage.' +
                       ' Try naming the manual, a paragraph number or the component.', nearest: near };
      }
      var reply = out.reply;
      if (reply.ambiguous && !follow) {
        var options = [reply.primary].concat(reply.related.filter(function (r) { return r.alias !== reply.primary.alias; }).slice(0, 2));
        var seen = {}, opts = options.filter(function (o) { if (seen[o.alias]) return false; seen[o.alias] = 1; return true; });
        state.pending = { text: text, options: opts };
        return { kind: 'clarify', text: 'More than one manual answers this about equally well. Which do you mean?',
                 options: opts.map(function (o) { return { alias: o.alias, name: MANUALS[o.alias] || o.alias, label: o.label, title: o.title, ask: text + ' in ' + o.alias }; }),
                 fallback: reply };
      }
      state.last = { query: text, confidence: reply.confidence, focus: reply.primary.alias + ' ' + reply.primary.title, primary: reply.primary, related: reply.related };
      return reply;
    }

    return { ask: ask, setScope: function (alias, chapter) { state.scope = MANUALS[alias] ? alias : null; state.chapter = state.scope && chapter ? String(chapter) : null; state.last = null; }, getScope: function () { return state.scope; }, getChapter: function () { return state.chapter || null; }, reset: function () { state.last = null; state.turns = []; }, history: function () { return state.turns.slice(); }, state: state, manuals: MANUALS, examples: EXAMPLES };
  }

  var api = { create: create, MANUALS: MANUALS, EXAMPLES: EXAMPLES };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RDSOChat = api;
})(typeof window !== 'undefined' ? window : globalThis);
