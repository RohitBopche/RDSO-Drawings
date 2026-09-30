/**
 * tests/verify_review_packet.js
 * Browser check of the offline human-review packet (scripts/make_review_packet.py): items with source images, decisions collected.
 */
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9251;
const PACKET = path.resolve(__dirname, '..', 'artifacts', 'review', 'packet_s7.html');
const URL_TARGET = 'file:///' + PACKET.replace(/\\/g, '/');
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

require('child_process').execFileSync('python', [path.resolve(__dirname, '..', 'scripts', 'make_review_packet.py'), '--per-kind', '6', '--seed', '7'], { stdio: 'ignore' });
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

    // TEST 1
    console.log("\n--- TEST 1: packet shows items with source images; decisions are collected, needing a name ---");
    const t1 = await client.eval(`
      (() => {
        const cards = document.querySelectorAll('.card').length;
        const withImg = document.querySelectorAll('.card img').length;
        document.getElementById('who').value = 'Test Reviewer';
        for (let i = 0; i < 3; i++) document.querySelector('input[name=d' + i + '][value=approved]').click();
        document.querySelector('input[name=d3][value=rejected]').click();
        document.querySelector('input[name=n3]').value = 'wrong end';
        document.querySelector('input[name=d4][value=unsure]').click();
        const out = collect();
        return { cards, withImg, reviewer: out.reviewer, n: out.decisions.length, kinds: [...new Set(out.decisions.map(d => d.kind))].length,
                 rejectedNote: out.decisions.find(d => d.decision === 'rejected').note, hasMark: !!document.querySelector('mark'),
                 count: document.getElementById('count').textContent };
      })()
    `);
    console.log(t1);
    await client.captureScreenshot('review_packet.png');
    if (t1.cards !== 30 || t1.withImg < 25 || t1.reviewer !== 'Test Reviewer' || t1.n !== 5 || t1.rejectedNote !== 'wrong end' || !t1.hasMark) throw new Error('Test 1 failed ' + JSON.stringify(t1));

    console.log("\n[SUCCESS] Review packet verified!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
