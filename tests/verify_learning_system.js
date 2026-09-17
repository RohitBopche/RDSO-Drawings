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

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9245;
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

const tempProfile = path.join(require('os').tmpdir(), 'chrome_learning_profile');

async function main() {
  console.log("[*] Spawning Chrome headless for Phase 6 Learning System Verification...");
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

    // Open intelligence drawer and switch to Learning tab
    console.log("[*] Opening Drawer & switching to Academy tab...");
    await client.eval(`
      (() => {
        toggleIntelligenceDrawer(true);
        switchDrawerTab('learning');
      })()
    `);
    await sleep(600);

    // =========================================================================
    // TEST 1: Learning Tracks View & 5-Stage Progression
    // =========================================================================
    console.log("\n--- TEST 1: Validate Learning Tracks View & 5-Stage Progression ---");
    const test1Result = await client.eval(`
      (() => {
        const container = document.getElementById('learning-container');
        const tracks = container ? container.querySelectorAll('.learning-track-card') : [];
        const trackTitles = Array.from(tracks).map(t => t.querySelector('span:nth-child(2)').innerText);
        const firstTrackStages = tracks.length > 0 ? Array.from(tracks[0].querySelectorAll('.learning-stage-row')).map(r => r.querySelector('.learning-stage-badge').innerText) : [];
        
        return {
          hasContainer: !!container,
          subnavButtons: Array.from(container.querySelectorAll('.learning-subnav-btn')).map(b => b.innerText.trim()),
          trackCount: tracks.length,
          trackTitles: trackTitles,
          firstTrackStages: firstTrackStages
        };
      })()
    `);
    console.log("Test 1 Result:", test1Result);
    if (test1Result.trackCount !== 3 || test1Result.firstTrackStages.length !== 5) {
      throw new Error(`Test 1 Failed: Expected 3 tracks with 5 stages each: ${JSON.stringify(test1Result)}`);
    }
    await sleep(400);
    await client.captureScreenshot('phase6_learning_tracks.png');

    // =========================================================================
    // TEST 2: 3D Flip Flashcards & Mastery Tracking
    // =========================================================================
    console.log("\n--- TEST 2: Validate 3D Flip Flashcards & Mastery Tracking ---");
    const test2Result = await client.eval(`
      (() => {
        renderLearningModule('flashcards');
        const cardBox = document.querySelector('.flashcard-box');
        const cardInner = document.getElementById('active-flashcard-card');
        const frontText = cardInner ? cardInner.querySelector('.flashcard-front div:nth-child(2)').innerText : '';
        
        // Trigger flip
        flipCurrentFlashcard();
        const isFlippedAfter1 = cardInner ? cardInner.classList.contains('flipped') : false;
        const backAnswer = cardInner ? cardInner.querySelector('.flashcard-back div:nth-child(2)').innerText : '';
        const backCitation = cardInner ? cardInner.querySelector('.flashcard-back strong').innerText : '';
        
        // Mark mastered
        markFlashcardMastered(0);
        const masteredCountAfter = window.masteredFlashcards.size;
        
        // Next card
        nextFlashcard();
        const nextCardQuestion = document.getElementById('active-flashcard-card') ? document.getElementById('active-flashcard-card').querySelector('.flashcard-front div:nth-child(2)').innerText : '';

        return {
          hasCardBox: !!cardBox,
          isFlipped: isFlippedAfter1,
          frontQuestion: frontText,
          backAnswerSnippet: backAnswer.slice(0, 60),
          citation: backCitation,
          masteredCount: masteredCountAfter,
          nextQuestionSnippet: nextCardQuestion.slice(0, 60)
        };
      })()
    `);
    console.log("Test 2 Result:", test2Result);
    if (!test2Result.hasCardBox || !test2Result.isFlipped || test2Result.masteredCount !== 1) {
      throw new Error(`Test 2 Failed: Flashcard interaction failure: ${JSON.stringify(test2Result)}`);
    }
    // Flip back to card 1 for a screenshot of the 3D card
    await client.eval(`prevFlashcard(); flipCurrentFlashcard();`);
    await sleep(500);
    await client.captureScreenshot('phase6_flashcards_flip.png');

    // =========================================================================
    // TEST 3: Knowledge Assessment 100% Score & Gold Certificate Generation
    // =========================================================================
    console.log("\n--- TEST 3: Knowledge Assessment 100% Score & Certificate ---");
    const test3Result = await client.eval(`
      (() => {
        renderLearningModule('quiz');
        
        // Select all correct options
        // Q0: opt 1 (41.0 – 45.0 mm)
        selectQuizOption(0, 1);
        // Q1: opt 2 (222 mm)
        selectQuizOption(1, 2);
        // Q2: opt 1 (10%)
        selectQuizOption(2, 1);
        // Q3: opt 1 (Every 3 Months / 10 GMT)
        selectQuizOption(3, 1);
        // Q4: opt 2 (IRS:T-46)
        selectQuizOption(4, 2);

        submitQuizAssessment();

        const score = window.lastQuizScore;
        const certEl = document.querySelector('#learning-subview-mount div[style*="border: 2px solid #ffd700"]');
        const certTitle = certEl ? certEl.querySelector('div:nth-child(2)').innerText : '';
        const certId = certEl ? certEl.querySelector('strong[style*="font-family: var(--font-mono)"]').innerText : '';

        return {
          score: score.score,
          total: score.total,
          percentage: score.percentage,
          passed: score.passed,
          hasCertificate: !!certEl,
          certTitle: certTitle,
          certId: certId
        };
      })()
    `);
    console.log("Test 3 Result:", test3Result);
    if (test3Result.score !== 5 || test3Result.percentage !== 100 || !test3Result.passed || !test3Result.hasCertificate) {
      throw new Error(`Test 3 Failed: 100% quiz evaluation or certificate missing: ${JSON.stringify(test3Result)}`);
    }
    await sleep(500);
    await client.captureScreenshot('phase6_quiz_certificate_100.png');

    // =========================================================================
    // TEST 4: Competency Matrix Dashboard
    // =========================================================================
    console.log("\n--- TEST 4: Validate Competency Matrix Dashboard ---");
    const test4Result = await client.eval(`
      (() => {
        renderLearningModule('competency');
        const cards = document.querySelectorAll('.competency-card');
        const domains = Array.from(cards).map(c => ({
          name: c.querySelector('span:nth-child(1)').innerText,
          badge: c.querySelector('.search-card-type-badge').innerText,
          score: c.querySelector('span[style*="font-family: var(--font-mono)"]').innerText
        }));

        const summaryPct = document.querySelector('#learning-subview-mount div[style*="font-size: 16px"]').innerText;
        const statusEl = document.querySelector('#learning-subview-mount div[style*="text-transform: uppercase"]');
        const summaryStatus = statusEl ? statusEl.innerText : '';

        return {
          domainCount: cards.length,
          domains: domains,
          summaryPct: summaryPct,
          summaryStatus: summaryStatus
        };
      })()
    `);
    console.log("Test 4 Result:", test4Result);
    if (test4Result.domainCount !== 5 || test4Result.summaryPct !== '100%') {
      throw new Error(`Test 4 Failed: Competency dashboard mapping incomplete: ${JSON.stringify(test4Result)}`);
    }
    await sleep(400);
    await client.captureScreenshot('phase6_competency_matrix.png');

    // =========================================================================
    // TEST 5: Assessment Strict 80% Threshold (Fail / Retest)
    // =========================================================================
    console.log("\n--- TEST 5: Strict 80% Passing Threshold (Fail & Retest) ---");
    const test5Result = await client.eval(`
      (() => {
        renderLearningModule('quiz');
        resetQuizAssessment();

        // 3 correct, 2 wrong -> 60%
        selectQuizOption(0, 1); // correct
        selectQuizOption(1, 2); // correct
        selectQuizOption(2, 0); // WRONG (5% instead of 10%)
        selectQuizOption(3, 0); // WRONG (1 month instead of 3 months)
        selectQuizOption(4, 2); // correct

        submitQuizAssessment();

        const score = window.lastQuizScore;
        const warningEl = document.querySelector('#learning-subview-mount div[style*="color: rgb(255, 136, 153)"], #learning-subview-mount div[style*="color: #ff8899"]');
        const certEl = document.querySelector('#learning-subview-mount div[style*="border: 2px solid #ffd700"]');

        return {
          score: score.score,
          total: score.total,
          percentage: score.percentage,
          passed: score.passed,
          hasWarning: !!warningEl,
          warningText: warningEl ? warningEl.innerText : '',
          hasCertificate: !!certEl
        };
      })()
    `);
    console.log("Test 5 Result:", test5Result);
    if (test5Result.score !== 3 || test5Result.percentage !== 60 || test5Result.passed !== false || test5Result.hasCertificate) {
      throw new Error(`Test 5 Failed: 80% threshold not strictly enforced: ${JSON.stringify(test5Result)}`);
    }
    await sleep(400);
    await client.captureScreenshot('phase6_quiz_retest_failed.png');

    console.log("\n=========================================================================");
    console.log("ALL PHASE 6 ENGINEERING LEARNING & TRAINING SYSTEM TESTS PASSED!");
    console.log("=========================================================================");

    client.close();
  } catch (err) {
    console.error("[-] Verification Error:", err);
    process.exit(1);
  } finally {
    try {
      chromeProc.kill();
    } catch (e) {}
  }
}

main();
