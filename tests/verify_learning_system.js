/**
 * tests/verify_learning_system.js
 * End-to-end verification of Phase 6: Engineering Learning & Training System (§17, §21, §36).
 * Uses Chrome DevTools Protocol (CDP) to validate:
 * 1. Academy drawer tab navigation & 5-stage progression tracks.
 * 2. 3D Flip Flashcards with interactive flip animation and mastery tracking.
 * 3. Knowledge Assessment grading, strict 80% threshold, and gold competency certificate.
 * 4. Competency Matrix dashboard across 5 engineering domains.
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9245;
const URL_TARGET = 'file:///' + path.resolve(__dirname, '..', 'expert.html').replace(/\\/g, '/');
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

const tempProfile = require('./browser_env').freshProfile('chrome_learning_profile');

async function main() {
  console.log("[*] Spawning Chrome headless for Phase 6 Learning System Verification...");
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

    // The hand-written learning module is gone: the academy tab now points at learn.html and nothing hand-written is left.
    console.log("[*] Opening Drawer & switching to Academy tab...");
    await client.eval(`(() => { toggleIntelligenceDrawer(true); switchDrawerTab('learning'); })()`);
    await sleep(600);
    console.log("\n--- TEST 1: the academy tab points at the generated practice page; no hand-written content remains ---");
    const t1 = await client.eval(`(() => ({
      moved: !!document.querySelector('#learning-container #learning-moved'),
      link: (document.querySelector('#learning-moved a') || {}).getAttribute ? document.querySelector('#learning-moved a').getAttribute('href') : null,
      cards: (window.RDSO_CARDS || []).length,
      hand: (window.CANONICAL_FLASHCARDS || []).length + (window.CANONICAL_QUIZ_QUESTIONS || []).length + (window.CANONICAL_LEARNING_TRACKS || []).length,
      cert: /CERTIFICATE OF|AUTH-99824/.test(document.body.innerText)
    }))()`);
    console.log(t1);
    if (!t1.moved || t1.link !== 'learn.html' || t1.cards < 100 || t1.hand !== 0 || t1.cert) throw new Error('Test 1 failed ' + JSON.stringify(t1));
    await client.captureScreenshot('learning_moved.png');
    console.log("\n[SUCCESS] Learning module replaced by generated practice cards!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
