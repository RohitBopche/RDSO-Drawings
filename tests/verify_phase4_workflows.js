const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const chromeCandidates = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe')
];
const chromePath = chromeCandidates.find(p => fs.existsSync(p)) || chromeCandidates[0];
const targetUrl = 'file:///' + path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/');
const artifactDir = path.join(__dirname, '..', 'artifacts');
if (!fs.existsSync(artifactDir)) { try { fs.mkdirSync(artifactDir, { recursive: true }); } catch (e) {} }
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_phase4_profile');

async function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

function fetchJson(url) {
    return new Promise((resolve, reject) => {
        http.get(url, res => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

class CDPClient {
    constructor(wsUrl) {
        this.ws = new WebSocket(wsUrl);
        this.id = 1;
        this.pending = new Map();
        this.ready = new Promise((resolve, reject) => {
            this.ws.onopen = resolve;
            this.ws.onerror = reject;
        });
        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.id && this.pending.has(msg.id)) {
                const { resolve, reject } = this.pending.get(msg.id);
                this.pending.delete(msg.id);
                if (msg.error) reject(msg.error);
                else resolve(msg.result);
            }
        };
    }

    send(method, params = {}) {
        return new Promise((resolve, reject) => {
            const id = this.id++;
            this.pending.set(id, { resolve, reject });
            this.ws.send(JSON.stringify({ id, method, params }));
        });
    }

    async evaluate(expression) {
        const res = await this.send('Runtime.evaluate', {
            expression,
            returnByValue: true,
            awaitPromise: true
        });
        if (res.exceptionDetails) {
            throw new Error(JSON.stringify(res.exceptionDetails));
        }
        return res.result ? res.result.value : undefined;
    }

    async captureScreenshot(filename) {
        const res = await this.send('Page.captureScreenshot', { format: 'png' });
        const filePath = path.join(artifactDir, filename);
        fs.writeFileSync(filePath, Buffer.from(res.data, 'base64'));
        console.log(`[+] Screenshot saved: ${filePath}`);
        return filePath;
    }
}

async function run() {
    console.log('[*] Spawning Chrome headless for Phase 4 Verification...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9234',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    try {
        await sleep(2000);
        const tabs = await fetchJson('http://127.0.0.1:9234/json');
        const pageTab = tabs.find(t => t.type === 'page') || tabs[0];
        if (!pageTab) throw new Error('No page tab found in Chrome CDP');

        console.log(`[*] Connecting CDP to: ${pageTab.webSocketDebuggerUrl}`);
        const cdp = new CDPClient(pageTab.webSocketDebuggerUrl);
        await cdp.ready;

        await cdp.send('Page.enable');
        await cdp.send('Runtime.enable');

        console.log(`[*] Navigating to: ${targetUrl}`);
        await cdp.send('Page.navigate', { url: targetUrl });
        await sleep(3500);

        // =========================================================================
        // STEP 1: VERIFY FIELD INSPECTION CHECKLIST (§16, §18)
        // =========================================================================
        console.log('[*] Step 1: Testing Field Inspection Checklist Tab (§18)...');
        const inspTabExists = await cdp.evaluate(`!!document.querySelector('.drawer-tab[data-tab="inspection"]')`);
        console.log(`    Field Inspection Tab Button Exists: ${inspTabExists}`);
        if (!inspTabExists) throw new Error('Field Inspection tab button not found in DOM');

        // Open Drawer and activate Inspection Tab
        await cdp.evaluate(`
            toggleIntelligenceDrawer(true);
            switchDrawerTab('inspection');
        `);
        await sleep(800);

        const activeInspPane = await cdp.evaluate(`document.getElementById('tab-pane-inspection').classList.contains('active')`);
        console.log(`    Inspection Tab Pane Active: ${activeInspPane}`);
        if (!activeInspPane) throw new Error('tab-pane-inspection failed to activate');

        // Verify initial state (all checks pass)
        const initialStatus = await cdp.evaluate(`document.getElementById('insp-compliance-label').innerText`);
        console.log(`    Initial Compliance Status: "${initialStatus}"`);
        if (!initialStatus.includes('6/6 CHECKS PASSED (100%)')) {
            throw new Error(`Expected initial 6/6 pass, got: ${initialStatus}`);
        }

        // Test real-time bounds violation: Check Rail Clearance set to 39.0 mm (standard is 41 - 45 mm)
        console.log('    Injecting out-of-tolerance value: Check Rail Clearance = 39.0 mm...');
        await cdp.evaluate(`(() => {
            const input = document.getElementById('insp-val-check_rail');
            input.value = "39.0";
            evaluateFieldInspection();
        })()`);
        await sleep(400);

        const defectBadge = await cdp.evaluate(`document.getElementById('insp-badge-check_rail').innerText`);
        const updatedStatus = await cdp.evaluate(`document.getElementById('insp-compliance-label').innerText`);
        console.log(`    Check Rail Badge: "${defectBadge}"`);
        console.log(`    Updated Compliance Status: "${updatedStatus}"`);
        if (defectBadge !== 'DEFECT') throw new Error(`Expected DEFECT badge, got ${defectBadge}`);
        if (!updatedStatus.includes('SPEED RESTRICTION REQUIRED')) {
            throw new Error(`Expected SPEED RESTRICTION REQUIRED, got ${updatedStatus}`);
        }

        // Restore to compliant value: 43.0 mm
        console.log('    Restoring compliant value: Check Rail Clearance = 43.0 mm...');
        await cdp.evaluate(`(() => {
            const input = document.getElementById('insp-val-check_rail');
            input.value = "43.0";
            evaluateFieldInspection();
        })()`);
        await sleep(400);

        const restoredBadge = await cdp.evaluate(`document.getElementById('insp-badge-check_rail').innerText`);
        const restoredStatus = await cdp.evaluate(`document.getElementById('insp-compliance-label').innerText`);
        console.log(`    Restored Check Rail Badge: "${restoredBadge}"`);
        console.log(`    Restored Compliance Status: "${restoredStatus}"`);
        if (restoredBadge !== 'PASS') throw new Error(`Expected PASS badge, got ${restoredBadge}`);
        if (!restoredStatus.includes('6/6 CHECKS PASSED (100%)')) {
            throw new Error(`Expected 6/6 pass after restoration, got ${restoredStatus}`);
        }

        await cdp.captureScreenshot('phase4_field_inspection_checklist.png');

        // =========================================================================
        // STEP 2: VERIFY TURNOUT SPARES & PROCUREMENT CALCULATOR (§19)
        // =========================================================================
        console.log('[*] Step 2: Testing Turnout Spares & BOM Calculator Tab (§19)...');
        const procTabExists = await cdp.evaluate(`!!document.querySelector('.drawer-tab[data-tab="procurement"]')`);
        console.log(`    Procurement Tab Button Exists: ${procTabExists}`);
        if (!procTabExists) throw new Error('Procurement tab button not found in DOM');

        // Switch to procurement tab
        await cdp.evaluate(`switchDrawerTab('procurement')`);
        await sleep(800);

        const activeProcPane = await cdp.evaluate(`document.getElementById('tab-pane-procurement').classList.contains('active')`);
        console.log(`    Procurement Tab Pane Active: ${activeProcPane}`);
        if (!activeProcPane) throw new Error('tab-pane-procurement failed to activate');

        // Test Multiplier: Select 10 Sets
        console.log('    Testing 10 Sets Order Multiplier with Note 28 10% Spares Buffer...');
        await cdp.evaluate(`renderProcurementCalculator(10)`);
        await sleep(400);

        const bomRowsCount = await cdp.evaluate(`document.querySelectorAll('#procurement-container tbody tr').length`);
        console.log(`    BOM Item Rows Count: ${bomRowsCount}`);
        if (bomRowsCount < 8) throw new Error(`Expected at least 8 BOM items, got ${bomRowsCount}`);

        // Verify calculation for HTS Fishbolts 25x310 mm (Base: 24, Order: 10 => 240 + 24 = 264)
        const fishboltCalc = await cdp.evaluate(`(() => {
            const rows = Array.from(document.querySelectorAll('#procurement-container tbody tr'));
            const boltRow = rows.find(r => r.innerText.includes('Fishbolt'));
            return boltRow ? boltRow.innerText : '';
        })()`);
        console.log(`    HTS Fishbolt Row Text: ${JSON.stringify(fishboltCalc)}`);
        if (!fishboltCalc.includes('264 Nos') || !fishboltCalc.includes('24 × 10 sets + 24 (10% buffer)')) {
            throw new Error(`Note 28 calculation mismatch for fishbolts: ${fishboltCalc}`);
        }

        // Verify calculation for Tie Bar Detail 'B' (Base: 2, Order: 10 => 20 + 2 = 22)
        const tieBarCalc = await cdp.evaluate(`(() => {
            const rows = Array.from(document.querySelectorAll('#procurement-container tbody tr'));
            const tieRow = rows.find(r => r.innerText.includes("Detail 'B'"));
            return tieRow ? tieRow.innerText : '';
        })()`);
        console.log(`    Tie Bar Detail B Row Text: ${JSON.stringify(tieBarCalc)}`);
        if (!tieBarCalc.includes('22 Nos') || !tieBarCalc.includes('2 × 10 sets + 2 (10% buffer)')) {
            throw new Error(`Note 28 calculation mismatch for Tie Bar: ${tieBarCalc}`);
        }

        await cdp.captureScreenshot('phase4_procurement_spares_calc.png');

        // =========================================================================
        // STEP 3: VERIFY 6-COMPARTMENT ANSWER CARD & ACTION TOOLBAR (§15)
        // =========================================================================
        console.log('[*] Step 3: Testing 6-Compartment Engineering Answer Card & Action Toolbar (§15)...');
        
        // Select comp_detailb
        await cdp.evaluate(`window.selectGraphNode('comp_detailb')`);
        await sleep(800);

        const cardVisible = await cdp.evaluate(`(() => {
            const c = document.getElementById('drawer-answer-card');
            const tb = document.getElementById('answer-card-toolbar');
            return !!(c && tb && tb.style.display === 'flex');
        })()`);
        console.log(`    Answer Card & Action Toolbar Visible: ${cardVisible}`);
        if (!cardVisible) throw new Error('Answer Card Action Toolbar failed to display');

        const cardDesc = await cdp.evaluate(`document.getElementById('answer-card-desc').innerText`);
        console.log(`    Answer Card Compartment Content:`, JSON.stringify(cardDesc.slice(0, 200)));
        if (!cardDesc.includes('RDSO/T-6155') || !cardDesc.toUpperCase().includes('CRITICAL PARAMETERS')) {
            throw new Error('Answer Card missing critical parameters or drawing scope compartments');
        }

        // Check Action Toolbar Buttons
        const toolBtnCount = await cdp.evaluate(`document.querySelectorAll('#answer-card-toolbar .answer-tool-btn').length`);
        console.log(`    Action Toolbar Buttons Count: ${toolBtnCount}`);
        if (toolBtnCount !== 5) throw new Error(`Expected 5 action toolbar buttons, got ${toolBtnCount}`);

        // Test toolbar button click: Field Inspection button
        console.log('    Clicking Field Inspection action toolbar button...');
        await cdp.evaluate(`document.getElementById('btn-answer-inspection').click()`);
        await sleep(500);

        const tabAfterInspClick = await cdp.evaluate(`document.getElementById('tab-pane-inspection').classList.contains('active')`);
        console.log(`    Switched to Inspection Tab via Toolbar: ${tabAfterInspClick}`);
        if (!tabAfterInspClick) throw new Error('Action button failed to switch to Field Inspection tab');

        // Test toolbar button click: Spares & BOM button
        console.log('    Clicking Spares & BOM action toolbar button...');
        await cdp.evaluate(`document.getElementById('btn-answer-procurement').click()`);
        await sleep(500);

        const tabAfterProcClick = await cdp.evaluate(`document.getElementById('tab-pane-procurement').classList.contains('active')`);
        console.log(`    Switched to Procurement Tab via Toolbar: ${tabAfterProcClick}`);
        if (!tabAfterProcClick) throw new Error('Action button failed to switch to Procurement tab');

        // Switch back to overview to showcase full Unified Answer Card
        await cdp.evaluate(`switchDrawerTab('overview')`);
        await sleep(400);

        await cdp.captureScreenshot('phase4_unified_answer_card.png');

        console.log('\n================================================================================');
        console.log('PHASE 4 VERIFICATION: 100% PASSED');
        console.log('================================================================================\n');

    } finally {
        chrome.kill('SIGKILL');
        try { fs.rmSync(tempProfile, { recursive: true, force: true }); } catch (e) {}
    }
}

run().catch(err => {
    console.error('[!] Verification failed:', err);
    process.exit(1);
});
