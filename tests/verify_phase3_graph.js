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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_phase3_profile');

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
    console.log('[*] Spawning Chrome headless for Phase 3 Verification...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9233',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    try {
        await sleep(2000);
        const tabs = await fetchJson('http://127.0.0.1:9233/json');
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

        // 1. Verify Path Finder Drawer Tab
        console.log('[*] Step 1: Testing Path Finder Drawer Tab...');
        const pathTabExists = await cdp.evaluate(`!!document.querySelector('.drawer-tab[data-tab="paths"]')`);
        console.log(`    Path Tab Button Exists: ${pathTabExists}`);
        if (!pathTabExists) throw new Error('Path Finder tab button not found in DOM');

        // Click Path Finder tab
        await cdp.evaluate(`
            toggleIntelligenceDrawer(true);
            switchDrawerTab('paths');
        `);
        await sleep(1000);

        const activeTabPane = await cdp.evaluate(`document.getElementById('tab-pane-paths').classList.contains('active')`);
        console.log(`    Path Tab Pane Active: ${activeTabPane}`);
        if (!activeTabPane) throw new Error('tab-pane-paths failed to activate');

        // 2. Test Component Path Template (comp_tongue_rail -> std_irs_t10)
        console.log('[*] Step 2: Testing Component Path Template (§14.1)...');
        await cdp.evaluate(`window.loadPathTemplate('component')`);
        await sleep(600);

        const compStepsCount = await cdp.evaluate(`document.querySelectorAll('#path-results-container .path-step-card').length`);
        console.log(`    Component Path Steps Count: ${compStepsCount}`);
        if (compStepsCount < 2) throw new Error(`Expected at least 2 steps for Component Path, got ${compStepsCount}`);

        const compPathText = await cdp.evaluate(`document.getElementById('path-results-container').innerText`);
        console.log(`    Found Banner: ${compPathText.includes('PATH FOUND IN')}`);
        if (!compPathText.includes('PATH FOUND IN')) throw new Error('Path Finder banner not found for Component Path');

        await cdp.captureScreenshot('phase3_pathfinder_component_path.png');

        // 3. Test Failure Path Template (defect_joint_fatigue -> hazard_derailment_split)
        console.log('[*] Step 3: Testing Failure Path Template (§14.2)...');
        await cdp.evaluate(`window.loadPathTemplate('failure')`);
        await sleep(600);

        const failStepsCount = await cdp.evaluate(`document.querySelectorAll('#path-results-container .path-step-card').length`);
        console.log(`    Failure Path Steps Count: ${failStepsCount}`);
        if (failStepsCount < 2) throw new Error(`Expected at least 2 steps for Failure Path, got ${failStepsCount}`);

        await cdp.captureScreenshot('phase3_failure_path_template.png');

        // 4. Test Procedure and Procurement Path Templates (§14.3, §14.4)
        console.log('[*] Step 4: Testing Procedure & Procurement Templates...');
        await cdp.evaluate(`window.loadPathTemplate('procedure')`);
        await sleep(400);
        const procSteps = await cdp.evaluate(`document.querySelectorAll('#path-results-container .path-step-card').length`);
        console.log(`    Procedure Path Steps: ${procSteps}`);
        if (procSteps < 2) throw new Error('Procedure Path template failed');

        await cdp.evaluate(`window.loadPathTemplate('procurement')`);
        await sleep(400);
        const spareSteps = await cdp.evaluate(`document.querySelectorAll('#path-results-container .path-step-card').length`);
        console.log(`    Procurement Path Steps: ${spareSteps}`);
        if (spareSteps < 2) throw new Error('Procurement Path template failed');

        // 5. Test "Why Connected?" Explanation Modal (§13.3)
        console.log('[*] Step 5: Testing "Why Connected?" Modal (§13.3)...');
        await cdp.evaluate(`window.openWhyConnectedModal('comp_tongue_rail', 'drg_6155', 'CONTAINS')`);
        await sleep(600);

        const modalVisible = await cdp.evaluate(`
            const m = document.getElementById('why-connected-modal');
            m && m.style.display === 'flex';
        `);
        console.log(`    Why Connected Modal Display: ${modalVisible}`);
        if (!modalVisible) throw new Error('why-connected-modal failed to open');

        const modalContent = await cdp.evaluate(`document.getElementById('why-connected-modal-content').innerText`);
        console.log(`    Modal Raw Content:`, JSON.stringify(modalContent));
        console.log(`    Modal Contains Rationale: ${modalContent.toLowerCase().includes('justification') || modalContent.toLowerCase().includes('rationale')}`);
        console.log(`    Modal Contains Source: ${modalContent.includes('RDSO/T-6155')}`);
        if (!modalContent.toLowerCase().includes('justification') && !modalContent.toLowerCase().includes('rationale')) {
            throw new Error('Why Connected modal content incomplete');
        }

        await cdp.captureScreenshot('phase3_why_connected_modal.png');

        // Close modal
        await cdp.evaluate(`window.closeWhyConnectedModal()`);
        await sleep(300);
        const modalClosed = await cdp.evaluate(`document.getElementById('why-connected-modal').style.display === 'none'`);
        console.log(`    Modal Closed cleanly: ${modalClosed}`);
        if (!modalClosed) throw new Error('why-connected-modal failed to close');

        // 6. Test 3D Predicate Family Filtering (§13.2)
        console.log('[*] Step 6: Testing 3D Predicate Family Filtering (§13.2)...');
        const predCountInitial = await cdp.evaluate(`document.getElementById('pred-active-count').innerText`);
        console.log(`    Initial Predicate Families Active: ${predCountInitial}`);
        if (!predCountInitial.includes('4/4')) throw new Error(`Expected 4/4 active, got ${predCountInitial}`);

        // Toggle structural family off
        await cdp.evaluate(`window.togglePredicateFamily('structural', false)`);
        await sleep(300);
        const predCountReduced = await cdp.evaluate(`document.getElementById('pred-active-count').innerText`);
        console.log(`    After Toggle Off: ${predCountReduced}`);
        if (!predCountReduced.includes('3/4')) throw new Error(`Expected 3/4 active, got ${predCountReduced}`);

        // Toggle structural family back on
        await cdp.evaluate(`window.togglePredicateFamily('structural', true)`);
        await sleep(300);
        const predCountRestored = await cdp.evaluate(`document.getElementById('pred-active-count').innerText`);
        console.log(`    After Toggle On: ${predCountRestored}`);
        if (!predCountRestored.includes('4/4')) throw new Error(`Expected 4/4 active, got ${predCountRestored}`);

        // 7. Test Focus Path in 3D
        console.log('[*] Step 7: Testing 3D Path Focus...');
        const focusWorked = await cdp.evaluate(`
            try {
                window.focusPathIn3D(['comp_tongue_rail', 'drg_6155', 'std_irs_t10']);
                true;
            } catch(e) {
                false;
            }
        `);
        console.log(`    Focus Path In 3D Execution: ${focusWorked}`);
        if (!focusWorked) throw new Error('focusPathIn3D threw an error');

        console.log('\n================================================================================');
        console.log('PHASE 3 VERIFICATION: 100% PASSED');
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
