/**
 * tests/verify_chat_ui.js
 * Browser check of chat.html: greeting, cited answer with page link, follow-up chips, commands, refusal, local feedback, HTML escaping.
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

    const ask = async (q) => client.eval(`(async () => { const i = document.getElementById('q'); i.value = ${JSON.stringify(q)};
      document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await new Promise(r => setTimeout(r, 400));
      const bots = document.querySelectorAll('.msg.bot'); const last = bots[bots.length - 1];
      return { n: bots.length, text: last.innerText.slice(0, 400), cites: last.querySelectorAll('a.cite').length, chips: last.querySelectorAll('.chip').length,
               badge: (last.querySelector('.badge') || {}).innerText || '', href: (last.querySelector('a.cite') || {}).href || '' }; })()`);
    console.log("\n--- TEST 1: ready, greeting shown, input enabled ---");
    const t1 = await client.eval(`({ disabled: document.getElementById('q').disabled, bots: document.querySelectorAll('.msg.bot').length, status: document.getElementById('status').innerText,
                                     examples: document.querySelectorAll('.msg.bot .chip').length })`);
    console.log(t1);
    if (t1.disabled || t1.bots !== 1 || !/Ready/.test(t1.status) || t1.examples < 3) throw new Error('Test 1 failed ' + JSON.stringify(t1));

    console.log("\n--- TEST 2: a question gets a cited answer with a link to the manual page and follow-up chips ---");
    const t2 = await ask('How is casual renewal of a defective or fractured rail carried out?');
    console.log(t2);
    await client.captureScreenshot('chat_answer.png');
    if (!/Para 616/.test(t2.text) || t2.cites < 1 || t2.chips < 1 || !/#page=321/.test(t2.href) || !/match/.test(t2.badge)) throw new Error('Test 2 failed ' + JSON.stringify(t2));

    console.log("\n--- TEST 3: a follow-up chip asks the next question ---");
    const t3 = await client.eval(`(async () => { const before = document.querySelectorAll('.msg.bot').length; document.querySelector('.msg.bot:last-child .chip').click();
      await new Promise(r => setTimeout(r, 400)); const bots = document.querySelectorAll('.msg.bot'); return { before, after: bots.length, users: document.querySelectorAll('.msg.user').length,
      last: bots[bots.length - 1].innerText.slice(0, 120) }; })()`);
    console.log(t3);
    if (t3.after !== t3.before + 1 || t3.users !== 2) throw new Error('Test 3 failed ' + JSON.stringify(t3));

    console.log("\n--- TEST 4: commands and out-of-scope question ---");
    const t4a = await ask('what about the source');
    const t4b = await ask('What is the recipe for butter chicken?');
    console.log(t4a.text.slice(0, 100), '|', t4b.text.slice(0, 100));
    if (!/That answer comes from .+ Para \S+, page \d+/.test(t4a.text) || !/could not find/.test(t4b.text)) throw new Error('Test 4 failed');

    console.log("\n--- TEST 5: feedback is stored locally and exportable; HTML in a question is not executed ---");
    const t5 = await client.eval(`(async () => { localStorage.removeItem('rdso_feedback_v1'); await (async () => { const i = document.getElementById('q'); i.value = '<img src=x onerror=window.__pwn=1> rail gap';
      document.getElementById('f').dispatchEvent(new Event('submit', { cancelable: true })); await new Promise(r => setTimeout(r, 300)); })();
      const btn = [...document.querySelectorAll('[data-fb="up"]')].pop(); if (btn) btn.click();
      const rows = window.rdsoFeedback.read(); return { pwn: !!window.__pwn, kinds: rows.map(r => r.type + ':' + (r.verdict || r.status)), via: rows[0] && rows[0].via }; })()`);
    console.log(t5);
    if (t5.pwn || !t5.kinds.some(k => k.startsWith('query:')) || t5.via !== 'chat') throw new Error('Test 5 failed ' + JSON.stringify(t5));

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
