/**
 * tests/verify_chat_ui.js
 * Browser check of chat.html: empty state, cited answer, page viewer, follow-ups, commands, refusal, tables, local feedback, themes and settings, command palette, strict manual scope, history and saved answers, keyboard.
 */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9271;
const URL_TARGET = 'file:///' + path.resolve(__dirname, '..', 'chat.html').replace(/\\/g, '/');
const ARTIFACTS_DIR = envArtifactDir;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 1;
    this.callbacks = new Map();
    this.ready = new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.callbacks.has(msg.id)) {
        const { resolve, reject } = this.callbacks.get(msg.id);
        this.callbacks.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      }
    };
  }

  async connect() {
    return this.ready;
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.id++;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (res.exceptionDetails) {
      throw new Error(`Eval error: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res.result.value;
  }

  async captureScreenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(res.data, 'base64');
    const fullPath = path.join(ARTIFACTS_DIR, filename);
    fs.writeFileSync(fullPath, buffer);
    console.log(`[+] Screenshot saved: ${fullPath}`);
  }

  close() {
    if (this.ws) this.ws.close();
  }
}

const tempProfile = require('./browser_env').freshProfile('chrome_qa_profile');

async function main() {
  console.log("[*] Spawning Chrome headless for Retrieval UI Verification...");
  const chromeProc = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    ...chromeFlags,
    '--window-size=1920,1080',
    '--no-sandbox',
    '--no-first-run',
    '--allow-file-access-from-files',
    `--user-data-dir=${tempProfile}`
  ]);

  await waitForDevtools(PORT);

  try {
    const targets = await fetchJson(`http://127.0.0.1:${PORT}/json`);
    const pageTarget = targets.find(t => t.type === 'page') || targets[0];
    console.log(`[*] Connecting CDP to: ${pageTarget.webSocketDebuggerUrl}`);

    const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
    await client.connect();

    await client.send('Page.enable');
    await client.send('DOM.enable');
    await client.send('Runtime.enable');

    console.log(`[*] Navigating to: ${URL_TARGET}`);
    await client.send('Page.navigate', { url: URL_TARGET });
    await sleep(3500);

    const ev = (js) => client.eval(js);
    const submit = (q) => ev(`(async () => { const i = document.getElementById('q'); i.value = ${JSON.stringify(q)};
      document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await new Promise(r => setTimeout(r, 450));
      const bots = document.querySelectorAll('.msg.bot'); const last = bots[bots.length - 1];
      return { n: bots.length, text: last.innerText.slice(0, 500), cites: last.querySelectorAll('.cite').length, chips: last.querySelectorAll('.chip').length,
               dot: !!last.querySelector('.dot'), citeLabel: (last.querySelector('.cite') || {}).innerText || '' }; })()`);

    console.log("\n--- TEST 1: empty state with topic cards; ready; a theme is applied ---");
    const t1 = await ev(`({ hero: !!document.querySelector('.hero'), cards: document.querySelectorAll('.card').length, disabled: document.getElementById('q').disabled,
                            status: document.getElementById('status').innerText, theme: document.documentElement.getAttribute('data-theme'), scope: document.getElementById('scope').options.length })`);
    console.log(t1);
    if (!t1.hero || t1.cards !== 6 || t1.disabled || !/Ready/.test(t1.status) || !/^(light|dark)$/.test(t1.theme) || t1.scope !== 7) throw new Error('Test 1 failed ' + JSON.stringify(t1));

    console.log("\n--- TEST 2: a question gets a cited answer; the citation opens the manual page beside it ---");
    const t2 = await submit('How is casual renewal of a defective or fractured rail carried out?');
    console.log(t2);
    await client.captureScreenshot('chat_answer.png');
    const ed = await ev(`(document.getElementById('edition') || {}).innerText || ''`);
    if (!/Permanent Way Manual, 2024 \(ACS 1-14\)/.test(ed)) throw new Error('Test 2 failed: no edition line: ' + ed);
    if (!/Para 616/.test(t2.citeLabel) || !t2.dot || t2.chips < 1 || await ev(`!!document.querySelector('.hero')`)) throw new Error('Test 2 failed ' + JSON.stringify(t2));
    const v = await ev(`(async () => { document.querySelector('.msg.bot .cite').click(); await new Promise(r => setTimeout(r, 300));
      return { open: document.getElementById('viewer').classList.contains('open'), src: document.getElementById('viewerFrame').src, title: document.getElementById('viewerTitle').innerText }; })()`);
    console.log(v);
    if (!v.open || !/#page=321/.test(v.src) || !/616/.test(v.title)) throw new Error('Test 2b failed ' + JSON.stringify(v));

    console.log("\n--- TEST 3: an 'ask next' chip asks the next question ---");
    const t3 = await ev(`(async () => { const before = document.querySelectorAll('.msg.bot').length; document.querySelector('.msg.bot:last-child .next .chip').click();
      await new Promise(r => setTimeout(r, 450)); return { before, after: document.querySelectorAll('.msg.bot').length, users: document.querySelectorAll('.msg.user').length }; })()`);
    console.log(t3);
    if (t3.after !== t3.before + 1 || t3.users !== 2) throw new Error('Test 3 failed ' + JSON.stringify(t3));

    console.log("\n--- TEST 4: commands and out-of-scope question ---");
    const t4a = await submit('what about the source');
    const t4b = await submit('What is the recipe for butter chicken?');
    if (!/That answer comes from .+ Para \S+, page \d+/.test(t4a.text) || !/could not find/.test(t4b.text)) throw new Error('Test 4 failed ' + JSON.stringify([t4a.text, t4b.text]));

    console.log("\n--- TEST 4b: a table answer is shown as a table with headers and highlighted cells ---");
    const t4c = await ev(`(async () => { const i = document.getElementById('q'); i.value = 'what is the speed of utility track vehicle';
      document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await new Promise(r => setTimeout(r, 450));
      const bots = document.querySelectorAll('.msg.bot'); const last = bots[bots.length - 1]; const tb = last.querySelector('table.tb');
      return { has: !!tb, heads: tb ? [...tb.querySelectorAll('th')].map(x => x.innerText).join('|') : '', hit: last.querySelectorAll('td.hit').length, text: tb ? tb.querySelector('tbody').innerText : '' }; })()`);
    console.log(t4c);
    await client.captureScreenshot('chat_table.png');
    if (!t4c.has || !/Name of the Machine/.test(t4c.heads) || t4c.hit < 1 || !/Utility Track Vehicle/.test(t4c.text)) throw new Error('Test 4b failed ' + JSON.stringify(t4c));

    console.log("\n--- TEST 5: feedback is stored locally; HTML in a question is not executed ---");
    const t5 = await ev(`(async () => { localStorage.removeItem('rdso_feedback_v1'); const i = document.getElementById('q'); i.value = '<img src=x onerror=window.__pwn=1> rail gap';
      document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await new Promise(r => setTimeout(r, 400));
      const btn = [...document.querySelectorAll('[data-fb="up"]')].pop(); if (btn) btn.click();
      const rows = window.rdsoFeedback.read(); return { pwn: !!window.__pwn, kinds: rows.map(r => r.type + ':' + (r.verdict || r.status)), via: rows[0] && rows[0].via }; })()`);
    console.log(t5);
    if (t5.pwn || !t5.kinds.some(k => k.startsWith('query:')) || t5.via !== 'chat') throw new Error('Test 5 failed ' + JSON.stringify(t5));

    console.log("\n--- TEST 6: themes: switch from the settings panel and from the command palette; choices persist; text size changes ---");
    const t6 = await ev(`(async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      document.getElementById('settingsBtn').click(); await w(100);
      out.panel = !document.getElementById('settings').hidden; out.swatches = document.querySelectorAll('#swatches .sw').length;
      document.querySelector('.sw[data-theme="solarized-dark"]').click(); await w(100);
      out.solar = document.documentElement.getAttribute('data-theme'); out.bg = getComputedStyle(document.body).backgroundColor;
      out.stored = JSON.parse(localStorage.getItem('rdso_ui_v1')).theme;
      document.querySelector('#sizeSeg button[data-v="l"]').click(); await w(50); out.size = document.documentElement.getAttribute('data-size'); out.fs = getComputedStyle(document.documentElement).fontSize;
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true })); await w(100);
      out.palette = !document.getElementById('paletteModal').hidden;
      const pi = document.getElementById('paletteInput'); pi.value = 'theme: nord'; pi.dispatchEvent(new Event('input')); await w(50);
      pi.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); await w(100);
      out.nord = document.documentElement.getAttribute('data-theme'); out.closed = document.getElementById('paletteModal').hidden;
      document.querySelector('#settings #resetUi').click(); await w(50); out.reset = document.documentElement.getAttribute('data-size');
      return out; })()`);
    console.log(t6);
    if (!t6.panel || t6.swatches !== 9 || t6.solar !== 'solarized-dark' || t6.stored !== 'solarized-dark' || t6.bg !== 'rgb(0, 43, 54)' || t6.size !== 'l' || t6.fs !== '18px' || !t6.palette || t6.nord !== 'nord' || !t6.closed || t6.reset !== 'm') throw new Error('Test 6 failed ' + JSON.stringify(t6));

    console.log("\n--- TEST 7: restricting the search to one manual is strict ---");
    const t7 = await ev(`(async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const sc = document.getElementById('scope'); const res = {};
      for (const a of ['USFD', 'TMM']) { sc.value = a; sc.dispatchEvent(new Event('change')); await w(50);
        const i = document.getElementById('q'); i.value = 'what is the frequency of testing'; document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await w(350);
        const bots = document.querySelectorAll('.msg.bot'); res[a] = (bots[bots.length - 1].querySelector('.cite') || {}).innerText || ''; }
      sc.value = ''; sc.dispatchEvent(new Event('change')); return res; })()`);
    console.log(t7);
    if (!/^📄 USFD/.test(t7.USFD) || !/^📄 TMM/.test(t7.TMM)) throw new Error('Test 7 failed ' + JSON.stringify(t7));

    console.log("\n--- TEST 8: history, saved answers, copy, keyboard ---");
    const t8 = await ev(`(async () => { const w = ms => new Promise(r => setTimeout(r, ms)); const out = {};
      document.querySelector('[data-act="save"]').click(); await w(100);
      document.getElementById('sideBtn').click(); await w(250);
      out.side = document.getElementById('side').classList.contains('open'); out.history = document.querySelectorAll('#historyList .item').length; out.saved = document.querySelectorAll('#savedList .item').length;
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })); await w(60); out.viewerClosed = !document.getElementById('viewer').classList.contains('open');
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })); await w(100); out.sideClosed = !document.getElementById('side').classList.contains('open');
      document.getElementById('q').blur(); document.dispatchEvent(new KeyboardEvent('keydown', { key: '/' })); await w(50); out.focus = document.activeElement.id;
      document.getElementById('newchat').click(); await w(100); out.cards = document.querySelectorAll('.card').length;
      return out; })()`);
    console.log(t8);
    if (!t8.side || t8.history < 3 || t8.saved < 1 || !t8.viewerClosed || !t8.sideClosed || t8.focus !== 'q' || t8.cards !== 6) throw new Error('Test 8 failed ' + JSON.stringify(t8));

    console.log("\n--- TEST 9: hand-off from Browse (?q= and manual=) asks the question in that manual; viewer links back to Browse ---");
    await client.send('Page.navigate', { url: URL_TARGET + '?q=' + encodeURIComponent('Explain IRPWM para 616') + '&manual=IRPWM' });
    await sleep(3500);
    const t9 = await ev(`(async () => { await new Promise(r => setTimeout(r, 600)); const bots = document.querySelectorAll('.msg.bot'); const last = bots[bots.length - 1];
      const out = { n: bots.length, scope: document.getElementById('scope').value, tabs: document.querySelectorAll('.tabs a').length, cites: last ? last.querySelectorAll('.cite').length : 0 };
      if (out.cites) { last.querySelector('.cite').click(); await new Promise(r => setTimeout(r, 200)); out.ctx = document.getElementById('viewerContext').getAttribute('href'); } return out; })()`);
    console.log(t9);
    if (t9.n < 1 || t9.scope !== 'IRPWM' || t9.tabs !== 4 || !/^browse\.html#CLAUSE/.test(t9.ctx || '')) throw new Error('Test 9 failed ' + JSON.stringify(t9));

    console.log("\n[SUCCESS] Chat UI verified!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
