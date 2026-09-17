/**
 * Phase 7: Semantic Intelligence – CDP Browser Verification
 * Tests semantic tab rendering, concept neighbors, taxonomy, knowledge gaps, and search expansion chips.
 */
const WebSocket = require('ws');
const http = require('http');

const CHROME_PORT = 9222;
const PAGE_URL = 'file:///F:/git/RDSO-Drawings/index.html';
const results = [];

function log(msg) { console.log(`  [CDP] ${msg}`); }
function pass(name) { results.push({ name, status: 'PASS' }); log(`✅ PASS: ${name}`); }
function fail(name, reason) { results.push({ name, status: 'FAIL', reason }); log(`❌ FAIL: ${name} — ${reason}`); }

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function getWSEndpoint() {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${CHROME_PORT}/json`, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          const targets = JSON.parse(data);
          const page = targets.find(t => t.type === 'page');
          if (page) resolve(page.webSocketDebuggerUrl);
          else reject(new Error('No page target found'));
        } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

async function connectCDP() {
  const wsUrl = await getWSEndpoint();
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let id = 1;
    const pending = new Map();
    ws.on('open', () => resolve({
      send(method, params = {}) {
        return new Promise((res, rej) => {
          const msgId = id++;
          pending.set(msgId, { res, rej });
          ws.send(JSON.stringify({ id: msgId, method, params }));
        });
      },
      close() { ws.close(); }
    }));
    ws.on('message', raw => {
      const msg = JSON.parse(raw);
      if (msg.id && pending.has(msg.id)) {
        const { res, rej } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) rej(msg.error);
        else res(msg.result);
      }
    });
    ws.on('error', reject);
  });
}

async function evaluate(cdp, expression) {
  const r = await cdp.send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: false
  });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}

(async () => {
  log('Connecting to Chrome...');
  const cdp = await connectCDP();

  // Navigate
  await cdp.send('Page.enable');
  await cdp.send('Page.navigate', { url: PAGE_URL });
  await sleep(5000);

  // ─── TEST 1: Semantic drawer tab button exists ───
  try {
    const tabExists = await evaluate(cdp, `!!document.getElementById('drawer-tab-semantic')`);
    if (tabExists) pass('Semantic drawer tab button exists');
    else fail('Semantic drawer tab button exists', 'Button not found');
  } catch (e) { fail('Semantic drawer tab button exists', e.message); }

  // ─── TEST 2: Open drawer and click semantic tab ───
  try {
    await evaluate(cdp, `(function(){ var d = document.getElementById('intelligence-drawer'); if(d) { d.classList.remove('collapsed'); } return true; })()`);
    await sleep(500);
    await evaluate(cdp, `(function(){ switchDrawerTab('semantic'); return true; })()`);
    await sleep(800);
    const paneVisible = await evaluate(cdp, `(function(){ var p = document.getElementById('tab-pane-semantic'); return p ? p.classList.contains('active') : false; })()`);
    if (paneVisible) pass('Semantic tab pane is active after click');
    else fail('Semantic tab pane is active after click', 'Pane not active');
  } catch (e) { fail('Semantic tab pane is active after click', e.message); }

  // ─── TEST 3: Semantic sub-navigation renders with 3 buttons ───
  try {
    const subNavCount = await evaluate(cdp, `document.querySelectorAll('.semantic-subnav-btn').length`);
    if (subNavCount === 3) pass('Semantic sub-navigation has 3 buttons');
    else fail('Semantic sub-navigation has 3 buttons', `Found ${subNavCount}`);
  } catch (e) { fail('Semantic sub-navigation has 3 buttons', e.message); }

  // ─── TEST 4: Concept Proximity Explorer renders neighbors ───
  try {
    const hasNeighborCards = await evaluate(cdp, `document.querySelectorAll('.concept-neighbor-card').length > 0`);
    if (hasNeighborCards) pass('Concept neighbor cards rendered');
    else fail('Concept neighbor cards rendered', 'No neighbor cards found');
  } catch (e) { fail('Concept neighbor cards rendered', e.message); }

  // ─── TEST 5: Similarity percentage shown ───
  try {
    const hasSimilarity = await evaluate(cdp, `(function(){ var cards = document.querySelectorAll('.concept-neighbor-card'); var found = false; cards.forEach(function(c){ if(c.textContent.indexOf('%') >= 0) found = true; }); return found; })()`);
    if (hasSimilarity) pass('Similarity percentage displayed on cards');
    else fail('Similarity percentage displayed on cards', 'No % found');
  } catch (e) { fail('Similarity percentage displayed on cards', e.message); }

  // ─── TEST 6: Taxonomy sub-view renders ───
  try {
    await evaluate(cdp, `(function(){ renderSemanticModule('taxonomy'); return true; })()`);
    await sleep(400);
    const hasTaxonomy = await evaluate(cdp, `(function(){ var m = document.getElementById('semantic-subview-mount'); return m ? m.textContent.indexOf('Railway Engineering Semantic Taxonomy') >= 0 : false; })()`);
    if (hasTaxonomy) pass('Taxonomy sub-view renders correctly');
    else fail('Taxonomy sub-view renders correctly', 'Taxonomy heading not found');
  } catch (e) { fail('Taxonomy sub-view renders correctly', e.message); }

  // ─── TEST 7: Taxonomy shows expansion chips ───
  try {
    const chipCount = await evaluate(cdp, `(function(){ var m = document.getElementById('semantic-subview-mount'); return m ? m.querySelectorAll('.expansion-chip').length : 0; })()`);
    if (chipCount >= 8) pass(`Taxonomy expansion chips present (${chipCount})`);
    else fail('Taxonomy expansion chips present', `Only ${chipCount} chips found`);
  } catch (e) { fail('Taxonomy expansion chips present', e.message); }

  // ─── TEST 8: Knowledge Gaps sub-view renders ───
  try {
    await evaluate(cdp, `(function(){ renderSemanticModule('gaps'); return true; })()`);
    await sleep(400);
    const hasCompleteness = await evaluate(cdp, `(function(){ var m2 = document.getElementById('semantic-subview-mount'); return m2 ? m2.textContent.indexOf('Completeness Index') >= 0 : false; })()`);
    if (hasCompleteness) pass('Knowledge Gaps sub-view renders Completeness Index');
    else fail('Knowledge Gaps sub-view renders Completeness Index', 'Heading not found');
  } catch (e) { fail('Knowledge Gaps sub-view renders Completeness Index', e.message); }

  // ─── TEST 9: Gap breakdown cards present (4 categories) ───
  try {
    const gapCardCount = await evaluate(cdp, `(function(){ var m3 = document.getElementById('semantic-subview-mount'); return m3 ? m3.querySelectorAll('.knowledge-gap-card').length : 0; })()`);
    if (gapCardCount >= 4) pass(`Gap breakdown cards present (${gapCardCount})`);
    else fail('Gap breakdown cards present', `Only ${gapCardCount} found`);
  } catch (e) { fail('Gap breakdown cards present', e.message); }

  // ─── TEST 10: Semantic expansion chips appear in search dropdown ───
  try {
    await evaluate(cdp, `(function(){ var inp = document.getElementById('global-search'); inp.value = 'turnout'; inp.dispatchEvent(new Event('input')); return true; })()`);
    await sleep(600);
    const hasExpansionBar = await evaluate(cdp, `(function(){ var bar = document.querySelector('.semantic-expansion-bar'); return bar ? bar.textContent.indexOf('Also searching') >= 0 : false; })()`);
    if (hasExpansionBar) pass('Semantic expansion chips appear for "turnout" query');
    else fail('Semantic expansion chips appear for "turnout" query', 'Expansion bar not found');
  } catch (e) { fail('Semantic expansion chips appear for "turnout" query', e.message); }

  // ─── TEST 11: Match-tier badges appear on search result cards ───
  try {
    const hasTierBadge = await evaluate(cdp, `(function(){ var dd = document.getElementById('search-dropdown'); if(!dd) return false; var badges = dd.querySelectorAll('.search-card-type-badge'); var found = false; badges.forEach(function(b){ var txt = b.textContent; if(txt.indexOf('EXACT_ID') >= 0 || txt.indexOf('LEXICAL') >= 0 || txt.indexOf('SEMANTIC') >= 0 || txt.indexOf('HYBRID') >= 0) found = true; }); return found; })()`);
    if (hasTierBadge) pass('Match-tier badges appear on search result cards');
    else fail('Match-tier badges appear on search result cards', 'No tier badges found');
  } catch (e) { fail('Match-tier badges appear on search result cards', e.message); }

  // ─── TEST 12: expandSearchQuery function works correctly ───
  try {
    const expandTest = await evaluate(cdp, `(function(){ var result = expandSearchQuery('turnout'); return result.length > 3 && result.indexOf('tongue rail') >= 0 && result.indexOf('t-6155') >= 0; })()`);
    if (expandTest) pass('expandSearchQuery correctly expands "turnout"');
    else fail('expandSearchQuery correctly expands "turnout"', 'Expansion incomplete');
  } catch (e) { fail('expandSearchQuery correctly expands "turnout"', e.message); }

  // ─── TEST 13: auditKnowledgeGaps returns valid audit structure ───
  try {
    const auditValid = await evaluate(cdp, `(function(){ var audit = auditKnowledgeGaps(); return typeof audit.completeness_pct === 'number' && typeof audit.total_nodes === 'number' && typeof audit.gap_breakdown === 'object' && audit.total_nodes > 0; })()`);
    if (auditValid) pass('auditKnowledgeGaps returns valid structure');
    else fail('auditKnowledgeGaps returns valid structure', 'Audit structure invalid');
  } catch (e) { fail('auditKnowledgeGaps returns valid structure', e.message); }

  // ─── TEST 14: findConceptNeighbors returns neighbors with similarity ───
  try {
    const neighborsValid = await evaluate(cdp, `(function(){ var nb = findConceptNeighbors('drg_6155', 5); return nb.length > 0 && typeof nb[0].similarity === 'number' && nb[0].similarity > 0; })()`);
    if (neighborsValid) pass('findConceptNeighbors returns valid neighbor list');
    else fail('findConceptNeighbors returns valid neighbor list', 'Invalid neighbors');
  } catch (e) { fail('findConceptNeighbors returns valid neighbor list', e.message); }

  // ─── TEST 15: rankHybridSearchResults returns scored results with matchTier ───
  try {
    const hybridValid = await evaluate(cdp, `(function(){ var r = rankHybridSearchResults('crack'); return r.length > 0 && r[0].matchTier && typeof r[0].score === 'number' && r[0].score > 0; })()`);
    if (hybridValid) pass('rankHybridSearchResults returns scored+tiered results');
    else fail('rankHybridSearchResults returns scored+tiered results', 'Invalid hybrid results');
  } catch (e) { fail('rankHybridSearchResults returns scored+tiered results', e.message); }

  // ─── SUMMARY ───
  console.log('\n' + '='.repeat(60));
  console.log('  PHASE 7: SEMANTIC INTELLIGENCE — VERIFICATION SUMMARY');
  console.log('='.repeat(60));
  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  results.forEach(r => {
    console.log(`  ${r.status === 'PASS' ? '✅' : '❌'} ${r.name}${r.reason ? ` — ${r.reason}` : ''}`);
  });
  console.log('-'.repeat(60));
  console.log(`  Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log('='.repeat(60));

  cdp.close();
  process.exit(failed > 0 ? 1 : 0);
})();
