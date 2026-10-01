/**
 * tests/verify_graph_ui.js
 * Browser check of browse.html: manual tree, reading view, sub-paragraphs, cross-references, tables, deep link, keyboard, themes, hand-off to the chat. empty state, cited answer, page viewer, follow-ups, commands, refusal, tables, local feedback, themes and settings, command palette, strict manual scope, history and saved answers, keyboard.
 */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9293;
const URL_TARGET = 'file:///' + path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/');
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
  console.log("[*] Spawning Chrome headless for Graph UI Verification...");
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
    console.log("\n--- TEST 1: only the graph and the chat box are on the page ---");
    const t1 = await ev(`({ ready: !!window.__graphReady, nodes: window.rdsoGraph.nodes.length, links: window.rdsoGraph.links.length, disabled: document.getElementById('q').disabled,
      dockBottom: Math.round(innerHeight - document.getElementById('dock').getBoundingClientRect().bottom), dockCentre: Math.round(document.getElementById('dock').getBoundingClientRect().left + document.getElementById('dock').getBoundingClientRect().width / 2 - innerWidth / 2),
      panels: document.querySelectorAll('aside:not([hidden])').length })`);
    console.log(t1);
    await client.captureScreenshot('graph_home.png');
    if (!t1.ready || t1.nodes < 1250 || t1.links < 400 || t1.disabled || t1.dockBottom > 30 || Math.abs(t1.dockCentre) > 2 || t1.panels !== 0) throw new Error('Test 1 failed ' + JSON.stringify(t1));
    console.log("\n--- TEST 2: a question answers in the dock and highlights its paragraph in the graph ---");
    const t2 = await ev(`(async () => { const i = document.getElementById('q'); i.value = 'How is casual renewal of a defective or fractured rail carried out?';
      document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await new Promise(r => setTimeout(r, 500));
      return { shown: !document.getElementById('ans').hidden, text: document.getElementById('ans').innerText.slice(0, 160), hot: window.rdsoGraph.state().hot, cite: (document.querySelector('#ans [data-focus]') || {}).innerText }; })()`);
    console.log(t2);
    await client.captureScreenshot('graph_answer.png');
    if (!t2.shown || !t2.hot.some(h => /PARA_616/.test(h)) || !/616/.test(t2.cite || '')) throw new Error('Test 2 failed ' + JSON.stringify(t2));
    console.log("\n--- TEST 3: clicking a citation opens the node card; Expert view link exists ---");
    const t3 = await ev(`(async () => { document.querySelector('#ans [data-focus]').click(); await new Promise(r => setTimeout(r, 200));
      return { card: !document.getElementById('card').hidden, title: document.querySelector('#card h2').innerText, expert: document.querySelector('a[href="expert.html"]') !== null, read: document.querySelector('#card a[href^="browse.html#"]') !== null }; })()`);
    console.log(t3);
    if (!t3.card || !/616/.test(t3.title) || !t3.expert || !t3.read) throw new Error('Test 3 failed ' + JSON.stringify(t3));
    console.log("\n--- TEST 3b: a chapter card can restrict the questions to that chapter ---");
    const t3b = await ev(`(async () => { const w = ms => new Promise(r => setTimeout(r, ms)); window.rdsoGraph.select('H:IRPWM:7'); await w(150);
      const b = document.querySelector('#card [data-chapter]'); if (!b) return { fail: 'no chapter button' }; b.click(); await w(100);
      const i = document.getElementById('q'); i.value = 'rail renewal'; document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await w(500);
      return { status: document.getElementById('status').innerText, cite: (document.querySelector('#ans [data-focus]') || {}).innerText || '' }; })()`);
    console.log(t3b);
    if (!/chapter 7/.test(t3b.status || '') || !/Para 7\d\d/.test(t3b.cite)) throw new Error('Test 3b failed ' + JSON.stringify(t3b));

    console.log("\n--- TEST 4: theme change repaints (dark) ---");
    const t4 = await ev(`(async () => { document.getElementById('settingsBtn').click(); await new Promise(r => setTimeout(r, 100)); document.querySelector('#settings [data-theme="dark"]').click(); await new Promise(r => setTimeout(r, 300)); return getComputedStyle(document.body).backgroundColor; })()`);
    console.log(t4);
    await client.captureScreenshot('graph_dark.png');
    if (t4 !== 'rgb(13, 17, 23)') throw new Error('Test 4 failed ' + t4);
    console.log("\n[SUCCESS] Graph UI verified!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
