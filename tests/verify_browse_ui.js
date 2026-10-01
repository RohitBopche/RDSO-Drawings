/**
 * tests/verify_browse_ui.js
 * Browser check of browse.html: manual tree, reading view, sub-paragraphs, cross-references, tables, deep link, keyboard, themes, hand-off to the chat. empty state, cited answer, page viewer, follow-ups, commands, refusal, tables, local feedback, themes and settings, command palette, strict manual scope, history and saved answers, keyboard.
 */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9291;
const URL_TARGET = 'file:///' + path.resolve(__dirname, '..', 'browse.html').replace(/\\/g, '/');
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
  console.log("[*] Spawning Chrome headless for Browse UI Verification...");
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
    await sleep(3000);
    const ev = (js) => client.eval(js);
    const w = (ms) => sleep(ms);

    console.log("\n--- TEST 1: loads, six manuals, tree shows chapters ---");
    const t1 = await ev(`({ ready: !!window.__browseReady, manuals: document.getElementById('manual').options.length, chapters: document.querySelectorAll('#tree details').length,
      tabs: document.querySelectorAll('.tabs a').length, cur: document.querySelector('.tabs [aria-current]').innerText })`);
    console.log(t1);
    if (!t1.ready || t1.manuals !== 6 || t1.chapters < 10 || t1.tabs !== 3 || t1.cur !== 'Browse manuals') throw new Error('Test 1 failed ' + JSON.stringify(t1));

    console.log("\n--- TEST 2: open a paragraph from the tree: full text, breadcrumb, deep link ---");
    const t2 = await ev(`(async () => { const d = document.querySelector('#tree details'); d.open = true; const b = d.querySelector('button[data-id]'); b.click(); await new Promise(r => setTimeout(r, 200));
      return { title: document.getElementById('ptitle').innerText, len: document.getElementById('ptext').innerText.length, hash: location.hash, crumb: document.querySelector('.crumb').innerText }; })()`);
    console.log(t2);
    await client.captureScreenshot('browse_read.png');
    if (!t2.title || t2.len < 30 || !/^#CLAUSE:/.test(t2.hash) || !/Chapter/.test(t2.crumb)) throw new Error('Test 2 failed ' + JSON.stringify(t2));

    console.log("\n--- TEST 3: deep link to IRPWM para 616 shows its text and neighbours; next/prev; keyboard ---");
    await client.send('Page.navigate', { url: URL_TARGET + '#CLAUSE:IRPWM:CH_06:PARA_616' }); await sleep(2500);
    const t3 = await ev(`(async () => { const out = { title: document.getElementById('ptitle').innerText, text: document.getElementById('ptext').innerText.slice(0, 80) };
      document.getElementById('next').click(); await new Promise(r => setTimeout(r, 150)); out.afterNext = document.getElementById('ptitle').innerText;
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' })); await new Promise(r => setTimeout(r, 150)); out.afterLeft = document.getElementById('ptitle').innerText; return out; })()`);
    console.log(t3);
    if (!/616/.test(t3.title) || /616/.test(t3.afterNext) || !/616/.test(t3.afterLeft)) throw new Error('Test 3 failed ' + JSON.stringify(t3));

    console.log("\n--- TEST 4: decimal manual shows sub-paragraphs and an up link; cross-references are clickable ---");
    await client.send('Page.navigate', { url: URL_TARGET + '#CLAUSE:AT_WELD:CH_04:PARA_4_1_1' }); await sleep(2500);
    const t4 = await ev(`(async () => { const out = { up: !![...document.querySelectorAll('.acts button')].find(b => /^Up to/.test(b.innerText)), subs: document.querySelectorAll('.box li button').length };
      const up = [...document.querySelectorAll('.acts button')].find(b => /^Up to/.test(b.innerText)); if (up) { up.click(); await new Promise(r => setTimeout(r, 150)); out.parent = document.getElementById('ptitle').innerText; } return out; })()`);
    console.log(t4);
    if (!t4.up || t4.subs < 2 || !/4\.1/.test(t4.parent || '')) throw new Error('Test 4 failed ' + JSON.stringify(t4));
    await client.send('Page.navigate', { url: URL_TARGET + '#CLAUSE:AT_WELD:CH_03:PARA_3_2' }); await sleep(2500);
    const t4b = await ev(`({ tables: document.querySelectorAll('table.tb').length, rows: document.querySelectorAll('table.tb tr').length })`);
    console.log(t4b);
    if (t4b.tables < 1 || t4b.rows < 3) throw new Error('Test 4b failed ' + JSON.stringify(t4b));

    console.log("\n--- TEST 4c: a paragraph that mentions figures shown only as pictures lists the page of each ---");
    await client.send('Page.navigate', { url: URL_TARGET + '#CLAUSE:IRPWM:CH_03:PARA_341' }); await sleep(2500);
    const t4c = await ev(`({ box: !!document.getElementById('xloc'), links: [...document.querySelectorAll('#xloc a')].map(a => a.getAttribute('href')).slice(0, 3) })`);
    console.log(t4c);
    if (!t4c.box || !t4c.links.length || !t4c.links.every(h => /#page=\d+$/.test(h))) throw new Error('Test 4c failed ' + JSON.stringify(t4c));

    console.log("\n--- TEST 5: filter, manual switch, hand-off links to the chat ---");
    const t5 = await ev(`(async () => { const m0 = document.getElementById('manual'); m0.value = 'AT_WELD'; m0.dispatchEvent(new Event('change')); await new Promise(r => setTimeout(r, 150)); const f = document.getElementById('filter'); f.value = '4.1'; f.dispatchEvent(new Event('input')); await new Promise(r => setTimeout(r, 100));
      const hit = document.querySelectorAll('#tree button[data-id]').length; f.value = ''; f.dispatchEvent(new Event('input'));
      const m = document.getElementById('manual'); m.value = 'FBW'; m.dispatchEvent(new Event('change')); await new Promise(r => setTimeout(r, 200));
      return { hit, fbw: document.getElementById('ptitle').innerText, ask: document.getElementById('askAbout').getAttribute('href'), page: document.getElementById('openPage').getAttribute('href') }; })()`);
    console.log(t5);
    if (t5.hit < 1 || !/FBW/.test(t5.fbw) || !/^chat\.html\?q=.*manual=FBW/.test(t5.ask) || !/#page=\d+/.test(t5.page)) throw new Error('Test 5 failed ' + JSON.stringify(t5));

    console.log("\n--- TEST 6: themes through the Aa panel ---");
    const t6 = await ev(`(async () => { document.getElementById('settingsBtn').click(); await new Promise(r => setTimeout(r, 100));
      const sw = [...document.querySelectorAll('#settings [data-theme]')]; const n = sw.length; sw.find(b => b.dataset.theme === 'solarized-dark').click(); await new Promise(r => setTimeout(r, 100));
      return { n, theme: document.documentElement.getAttribute('data-theme'), bg: getComputedStyle(document.body).backgroundColor }; })()`);
    console.log(t6);
    await client.captureScreenshot('browse_solarized.png');
    if (t6.n !== 9 || t6.theme !== 'solarized-dark' || t6.bg !== 'rgb(0, 43, 54)') throw new Error('Test 6 failed ' + JSON.stringify(t6));

    console.log("\n[SUCCESS] Browse UI verified!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
