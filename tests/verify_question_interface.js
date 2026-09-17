/**
 * tests/verify_question_interface.js
 * End-to-end verification of Phase 5: Question Interface & Natural Language Retrieval.
 * Uses Chrome DevTools Protocol (CDP) to validate:
 * 1. Global search Question Intent detection & Answer Card Preview card.
 * 2. Dedicated Q&A drawer tab with prompt chips and full Answer Card rendering.
 * 3. Parameter matrix, cross-domain traversal breadcrumbs, and conflict disclosure.
 * 4. 3D Cosmos focus from Answer Card action buttons.
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9240;
const URL_TARGET = "file:///F:/git/RDSO-Drawings/index.html";
const ARTIFACTS_DIR = "F:\\git\\RDSO-Drawings\\artifacts";

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

const tempProfile = path.join(require('os').tmpdir(), 'chrome_qa_profile');

async function main() {
  console.log("[*] Spawning Chrome headless for Phase 5 Question Interface Verification...");
  const chromeProc = spawn(CHROME_PATH, [
    `--remote-debugging-port=${PORT}`,
    '--headless=new',
    '--disable-gpu',
    '--window-size=1920,1080',
    '--no-sandbox',
    '--no-first-run',
    '--allow-file-access-from-files',
    `--user-data-dir=${tempProfile}`
  ]);

  await sleep(2000);

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

    // =========================================================================
    // TEST 1: Global Search Intent Detection & Answer Card Preview Card
    // =========================================================================
    console.log("\n--- TEST 1: Global Search Intent Detection for 'What is the permissible wear for tongue rails?' ---");
    const test1Result = await client.eval(`
      (() => {
        const input = document.getElementById('global-search');
        input.focus();
        input.value = "What is the permissible wear for tongue rails?";
        input.dispatchEvent(new Event('input'));
        
        const dropdown = document.getElementById('search-dropdown');
        const previewCard = dropdown ? dropdown.querySelector('.qa-preview-card') : null;
        
        return {
          dropdownVisible: dropdown && dropdown.style.display !== 'none',
          hasPreviewCard: !!previewCard,
          cardTitle: previewCard ? previewCard.querySelector('.search-card-title').innerText : '',
          intentBadge: previewCard ? previewCard.querySelector('.search-card-type-badge').innerText : '',
          confidenceBadge: previewCard ? previewCard.querySelector('.search-card-rev-badge').innerText : '',
          statementSnippet: previewCard ? previewCard.querySelector('.search-card-body').innerText.slice(0, 80) : ''
        };
      })()
    `);
    console.log("Test 1 Result:", test1Result);
    if (!test1Result.hasPreviewCard || !test1Result.intentBadge.includes("TOLERANCE INQUIRY")) {
      throw new Error(`Test 1 Failed: Answer Card preview not rendered properly: ${JSON.stringify(test1Result)}`);
    }
    await sleep(500);
    await client.captureScreenshot('phase5_search_question_preview.png');

    // =========================================================================
    // TEST 2: Inspect Full Answer Card in Dedicated Q&A Drawer Tab
    // =========================================================================
    console.log("\n--- TEST 2: Open Full Answer Card in Q&A Drawer Tab ---");
    const test2Result = await client.eval(`
      (() => {
        // Click the View Full Answer button in the preview card
        const btn = document.querySelector('.qa-preview-card .qa-inspect-btn');
        if (btn) btn.click();
        
        const drawer = document.getElementById('intelligence-drawer');
        const qaPane = document.getElementById('tab-pane-qa');
        const answerCard = qaPane ? qaPane.querySelector('.qa-answer-card') : null;
        const paramTable = answerCard ? answerCard.querySelector('.qa-param-table') : null;
        const traversalPath = answerCard ? answerCard.querySelector('.qa-traversal-path') : null;
        const provCard = answerCard ? answerCard.querySelector('.qa-provenance-card') : null;
        
        return {
          drawerOpen: drawer && !drawer.classList.contains('collapsed'),
          qaTabActive: qaPane && qaPane.classList.contains('active'),
          hasAnswerCard: !!answerCard,
          statement: answerCard ? answerCard.querySelector('.qa-statement-box').innerText : '',
          hasParamTable: !!paramTable,
          paramRowCount: paramTable ? paramTable.querySelectorAll('tbody tr').length : 0,
          hasTraversalPath: !!traversalPath,
          traversalNodeCount: traversalPath ? traversalPath.querySelectorAll('.qa-traversal-node').length : 0,
          hasProvenance: !!provCard
        };
      })()
    `);
    console.log("Test 2 Result:", test2Result);
    if (!test2Result.hasAnswerCard || test2Result.paramRowCount < 2 || test2Result.traversalNodeCount < 3) {
      throw new Error(`Test 2 Failed: Full Answer Card incomplete: ${JSON.stringify(test2Result)}`);
    }
    await sleep(500);
    await client.captureScreenshot('phase5_answer_card_wear.png');

    // =========================================================================
    // TEST 3: Quick Prompt Chip Selection & Conflict Disclosure
    // =========================================================================
    console.log("\n--- TEST 3: Quick Prompt Chip Selection (Switch Throw at Toe) ---");
    const test3Result = await client.eval(`
      (() => {
        onQuestionPromptSelected('What is the standard switch throw at the toe of curved switch?');
        
        const qaPane = document.getElementById('tab-pane-qa');
        const answerCard = qaPane ? qaPane.querySelector('.qa-answer-card') : null;
        const conflictBox = answerCard ? answerCard.querySelector('.qa-conflict-box') : null;
        const statement = answerCard ? answerCard.querySelector('.qa-statement-box').innerText : '';
        
        return {
          hasAnswerCard: !!answerCard,
          statement: statement,
          hasConflictBox: !!conflictBox,
          conflictText: conflictBox ? conflictBox.innerText : ''
        };
      })()
    `);
    console.log("Test 3 Result:", test3Result);
    if (!test3Result.statement.includes("160") || !test3Result.hasConflictBox) {
      throw new Error(`Test 3 Failed: Throw answer or conflict box missing: ${JSON.stringify(test3Result)}`);
    }
    await sleep(500);
    await client.captureScreenshot('phase5_answer_card_throw.png');

    // =========================================================================
    // TEST 4: Multi-Hop Specification Question & 3D Focus
    // =========================================================================
    console.log("\n--- TEST 4: Specification Question (Rubber Pads) & 3D Cosmos Focus ---");
    const test4Result = await client.eval(`
      (() => {
        onQuestionPromptSelected('Which IRS specification governs sleeper rubber pads?');
        
        const qaPane = document.getElementById('tab-pane-qa');
        const answerCard = qaPane ? qaPane.querySelector('.qa-answer-card') : null;
        const statement = answerCard ? answerCard.querySelector('.qa-statement-box').innerText : '';
        
        // Test 3D focus button
        const focusBtn = answerCard ? answerCard.querySelector('.qa-card-toolbar button') : null;
        if (focusBtn) focusBtn.click();
        
        return {
          hasAnswerCard: !!answerCard,
          statement: statement,
          specFound: statement.includes("IRS:T-46"),
          currentSelectedId: currentSelectedNode ? currentSelectedNode.data.id : null
        };
      })()
    `);
    console.log("Test 4 Result:", test4Result);
    if (!test4Result.specFound || test4Result.currentSelectedId !== 'comp_grsp') {
      throw new Error(`Test 4 Failed: Specification question or 3D focus incorrect: ${JSON.stringify(test4Result)}`);
    }
    await sleep(800);
    await client.captureScreenshot('phase5_answer_card_focus_3d.png');

    // =========================================================================
    // TEST 5: Revision Comparison Question (Alt 11 Changes)
    // =========================================================================
    console.log("\n--- TEST 5: Revision Comparison Question (Alt 11 Changes) ---");
    const test5Result = await client.eval(`
      (() => {
        onQuestionPromptSelected('What was changed in Alt 11 for T-6155?');
        
        const qaPane = document.getElementById('tab-pane-qa');
        const answerCard = qaPane ? qaPane.querySelector('.qa-answer-card') : null;
        const statement = answerCard ? answerCard.querySelector('.qa-statement-box').innerText : '';
        const intentBadge = answerCard ? answerCard.querySelector('.qa-intent-badge').innerText : '';
        
        return {
          hasAnswerCard: !!answerCard,
          intentBadge: intentBadge,
          statement: statement,
          has222Drop: statement.includes("222 mm"),
          hasListABuffer: statement.includes("10% LIST-A")
        };
      })()
    `);
    console.log("Test 5 Result:", test5Result);
    if (!test5Result.intentBadge.toLowerCase().includes("revision") || !test5Result.has222Drop || !test5Result.hasListABuffer) {
      throw new Error(`Test 5 Failed: Alt 11 revision answer incomplete: ${JSON.stringify(test5Result)}`);
    }
    await sleep(500);
    await client.captureScreenshot('phase5_answer_card_alt11.png');

    console.log("\n[SUCCESS] Phase 5: Question Interface & Natural Language Retrieval verified 100%!");
    client.close();
  } catch (err) {
    console.error("[!] Verification error:", err);
    process.exit(1);
  } finally {
    chromeProc.kill();
  }
}

main();
