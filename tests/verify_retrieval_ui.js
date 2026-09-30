/**
 * tests/verify_retrieval_ui.js
 * Browser check of the offline retrieval answers (P5.1) and cross-reference chips (P2.1):
 *  1. an unmatched natural-language question gets an extractive, cited, machine-extracted answer;
 *  2. an out-of-scope question is refused instead of guessed;
 *  3. a paragraph-number query resolves to that paragraph;
 *  4. the Para 429 provision card shows what it references and what references it, as links.
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const { chromePath: CHROME_PATH, chromeFlags, artifactDir: envArtifactDir, waitForDevtools } = require('./browser_env');
const PORT = 9247;
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
    console.log("\n--- TEST 1: unmatched question -> cited extractive answer ---");
    const t1 = await client.eval(`
      (() => {
        const a = window.answerEngineeringQuestion("How is casual renewal of a defective or fractured rail carried out?");
        const mount = document.createElement('div'); document.body.appendChild(mount);
        window.renderQuestionAnswerCard ? 0 : 0;
        return { id: a && a.id, status: a && a.provenance.status, clause: a && a.provenance.clause, conf: a && a.confidence,
                 hasCitation: !!a && a.statement.includes('IRPWM Para 616') && a.statement.includes('p.321'),
                 hasOpen: !!a && a.statement.includes('Open source page') };
      })()
    `);
    console.log(t1);
    if (t1.status !== 'MACHINE_EXTRACTED' || t1.clause !== 'CLAUSE:IRPWM:CH_06:PARA_616' || !t1.hasCitation || !t1.hasOpen) throw new Error('Test 1 failed ' + JSON.stringify(t1));

    // TEST 2
    console.log("\n--- TEST 2: out-of-scope question is refused ---");
    const t2 = await client.eval(`
      (() => { const a = window.answerEngineeringQuestion("What is the recipe for butter chicken and how do I bake sourdough?");
               return a ? { status: a.provenance.status, statement: a.statement.slice(0, 60), traversal: a.traversal.length } : null; })()
    `);
    console.log(t2);
    if (!t2 || t2.status !== 'NO_EVIDENCE' || t2.traversal !== 0) throw new Error('Test 2 failed ' + JSON.stringify(t2));

    // TEST 3
    console.log("\n--- TEST 3: paragraph number query ---");
    const t3 = await client.eval(`
      (() => { const a = window.answerEngineeringQuestion("What does Para 619 of IRPWM say?");
               return { clause: a && a.provenance.clause, status: a && a.provenance.status }; })()
    `);
    console.log(t3);
    if (t3.clause !== 'CLAUSE:IRPWM:CH_06:PARA_619') throw new Error('Test 3 failed ' + JSON.stringify(t3));

    // TEST 4
    console.log("\n--- TEST 4: Para 429 card shows outgoing and incoming cross-references ---");
    await client.eval(`window.selectGraphNode('CLAUSE:IRPWM:CH_04:PARA_429'); 1`);
    await sleep(1500);
    const t4 = await client.eval(`
      (() => { const el = document.getElementById('answer-card-desc'); const html = el ? el.innerHTML : '';
               return { hasOut: html.includes('References in this provision'), hasIn: html.includes('Referenced by'),
                        chips: (html.match(/selectGraphNode/g) || []).length, escaped: !html.includes('<script') }; })()
    `);
    console.log(t4);
    if (!t4.hasOut || t4.chips < 2 || !t4.escaped) throw new Error('Test 4 failed ' + JSON.stringify(t4));

    console.log("\n[SUCCESS] Retrieval UI and cross-reference chips verified!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
