/**
 * tests/verify_learn_ui.js
 * Browser check of browse.html: manual tree, reading view, sub-paragraphs, cross-references, tables, deep link, keyboard, themes, hand-off to the chat. empty state, cited answer, page viewer, follow-ups, commands, refusal, tables, local feedback, themes and settings, command palette, strict manual scope, history and saved answers, keyboard.
 */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9295;
const URL_TARGET = 'file:///' + path.resolve(__dirname, '..', 'learn.html').replace(/\\/g, '/');
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
  console.log("[*] Spawning Chrome headless for Learn UI Verification...");
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
    await sleep(2500);
    const ev = (js) => client.eval(js);
    const w = (ms) => sleep(ms);

    console.log("\n--- TEST 1: loads with the cards, six manuals offered, Learn tab current ---");
    const t1 = await ev(`({ ready: !!window.__learnReady, cards: window.RDSO_CARDS.length, opts: document.getElementById('manual').options.length, cur: document.querySelector('.tabs [aria-current]').innerText, tabs: document.querySelectorAll('.tabs a').length })`);
    console.log(t1);
    if (!t1.ready || t1.cards < 100 || t1.opts !== 7 || t1.cur !== 'Learn' || t1.tabs !== 4) throw new Error('Test 1 failed ' + JSON.stringify(t1));

    console.log("\n--- TEST 2: a practice card hides the number, reveals it with the full sentence and a source link; rating stores progress ---");
    const t2 = await ev(`(async () => { document.getElementById('startCards').click(); await new Promise(r => setTimeout(r, 100));
      const front = document.getElementById('front'); const before = front.innerText; const hasBlank = !!front.querySelector('.blank');
      document.getElementById('reveal').click(); await new Promise(r => setTimeout(r, 100));
      const out = { hasBlank, ans: (document.querySelector('.ans') || {}).innerText, src: (document.querySelector('#rev a') || {}).getAttribute('href'), srcText: document.getElementById('rev').innerText.slice(0, 120) };
      document.getElementById('knew').click(); await new Promise(r => setTimeout(r, 100));
      out.saved = JSON.parse(localStorage.getItem('rdso_learn_v1') || '{}'); out.boxes = Object.keys(out.saved.box || {}).length; out.next = document.getElementById('front') ? document.getElementById('front').innerText !== before : false; return out; })()`);
    console.log(t2);
    await client.captureScreenshot('learn_card.png');
    if (!t2.hasBlank || !t2.ans || !/^browse\.html#CLAUSE/.test(t2.src || '') || !/Source:/.test(t2.srcText) || t2.boxes !== 1 || !t2.next) throw new Error('Test 2 failed ' + JSON.stringify(t2));

    console.log("\n--- TEST 3: a quiz of 10 questions: pick answers, see the source, finish with a score and no certificate ---");
    const t3 = await ev(`(async () => { const w = ms => new Promise(r => setTimeout(r, ms)); document.getElementById('manual').value = 'IRPWM'; document.getElementById('startQuiz').click(); await w(100);
      let right = 0, n = 0;
      for (let i = 0; i < 10; i++) { const c = window.RDSO_CARDS; const opts = document.querySelectorAll('#opts button'); if (opts.length !== 4) break;
        opts[0].click(); await w(40); n++; if (document.querySelector('#opts .good') === opts[0]) right++;
        const hasSrc = /Source:/.test(document.getElementById('rev').innerText); if (!hasSrc) return { fail: 'no source at ' + i };
        document.getElementById('nextq').click(); await w(40); }
      return { n, right, result: document.getElementById('session').innerText.slice(0, 80), cert: /certificate/i.test(document.body.innerText) }; })()`);
    console.log(t3);
    if (t3.n !== 10 || !/Result: \d+ of 10/.test(t3.result) || t3.cert) throw new Error('Test 3 failed ' + JSON.stringify(t3));

    console.log("\n--- TEST 4: the review queue lists unanswered and not-helpful questions from the local chat log ---");
    const t4 = await ev(`(async () => { localStorage.setItem('rdso_feedback_v1', JSON.stringify([{ type: 'query', query: 'recipe for butter chicken', status: 'no_evidence' }, { type: 'feedback', query: 'check rail purpose', verdict: 'down' }, { type: 'query', query: 'what is cant', status: 'answer' }]));
      location.reload(); await new Promise(r => setTimeout(r, 1200)); return 1; })()`).catch(() => 1);
    await sleep(1500);
    const t4b = await ev(`({ items: document.querySelectorAll('#queue .q').length, text: document.getElementById('queue').innerText, exp: !document.getElementById('exportQueue').disabled })`);
    console.log(t4b);
    if (t4b.items !== 2 || !/butter chicken/.test(t4b.text) || !/check rail/.test(t4b.text) || !t4b.exp) throw new Error('Test 4 failed ' + JSON.stringify(t4b));

    console.log("\n[SUCCESS] Learn UI verified!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
