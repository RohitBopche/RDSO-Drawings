const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const artifactDir = "C:\\Users\\acer\\.gemini\\antigravity-ide\\brain\\5a58433d-2c07-448d-a15f-8232a40ea7a5";
const tempProfile = "C:\\Users\\acer\\AppData\\Local\\Temp\\chrome_kg_manuals_profile";

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
        console.log(`[SNAPSHOT] Saved: ${filename}`);
    }
}

async function run() {
    console.log("================================================================================");
    console.log("AUTOMATED CDP VERIFICATION: RDSO EXTENDED KNOWLEDGE GRAPH WITH RAILWAY MANUALS");
    console.log("================================================================================");

    const port = 9226;
    const chrome = spawn(chromePath, [
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${tempProfile}`,
        '--no-first-run',
        '--no-default-browser-check',
        '--window-size=1920,1080',
        'file:///F:/git/RDSO-Drawings/index.html'
    ]);

    let client = null;

    try {
        console.log(`[*] Connecting to Chrome on port ${port}...`);
        let versionData = null;
        for (let i = 0; i < 30; i++) {
            await sleep(500);
            try {
                versionData = await fetchJson(`http://localhost:${port}/json/version`);
                if (versionData && versionData.webSocketDebuggerUrl) break;
            } catch (e) {}
        }

        if (!versionData) throw new Error("Could not connect to Chrome debugging port");

        const tabs = await fetchJson(`http://localhost:${port}/json`);
        const pageTab = tabs.find(t => t.type === 'page');
        if (!pageTab) throw new Error("No page tab found");

        console.log(`[*] Attaching WebSocket CDP client to ${pageTab.title}...`);
        client = new CDPClient(pageTab.webSocketDebuggerUrl);
        await client.ready;

        await client.send('Page.enable');
        await client.send('Runtime.enable');
        await client.send('DOM.enable');

        console.log("[*] Waiting for 3D Knowledge Graph initialization...");
        await sleep(3500);

        // 1. Verify Entity Counts
        console.log("\n--- TEST 1: Canonical Entity and Edge Metrics ---");
        const metrics = await client.evaluate(`({
            nodes: kgPhysicsNodes.length,
            edges: kgPhysicsEdges.length,
            facts: rawKGFacts.length,
            modes: Array.from(document.querySelectorAll('.semantic-mode-btn')).map(b => b.dataset.mode)
        })`);
        console.log(`[*] Active Nodes: ${metrics.nodes} (Target >= 99)`);
        console.log(`[*] Active Edges: ${metrics.edges} (Target >= 141)`);
        console.log(`[*] Active Facts: ${metrics.facts} (Target >= 141)`);
        console.log(`[*] Semantic Modes: ${metrics.modes.join(', ')}`);

        if (metrics.nodes < 99 || metrics.edges < 141) {
            throw new Error(`Metrics lower than canonical baseline: nodes=${metrics.nodes}, edges=${metrics.edges}`);
        }
        if (!metrics.modes.includes('manuals')) {
            throw new Error("Semantic modes bar missing 'manuals' mode button!");
        }
        console.log("[PASS] Knowledge Core extended with Railway Codes & Manuals!");

        // 2. Test "Codes & Manuals" Semantic Mode
        console.log("\n--- TEST 2: Codes & Manuals Mode Switching ---");
        await client.evaluate(`switchSemanticMode('manuals')`);
        await sleep(1000);

        const modeState = await client.evaluate(`({
            currentMode: currentSemanticMode,
            indicator: document.getElementById('mode-active-indicator').innerText,
            activeBtn: document.querySelector('.semantic-mode-btn.active')?.dataset.mode,
            visibleManualNodes: kgPhysicsNodes.filter(n => n.mesh.material.opacity > 0.5).length
        })`);
        console.log(`[*] Mode Indicator: ${modeState.indicator}`);
        console.log(`[*] Active Mode: ${modeState.currentMode}`);
        console.log(`[*] Visible / Highlighted Entities: ${modeState.visibleManualNodes}`);

        if (modeState.currentMode !== 'manuals' || modeState.indicator !== 'CODES & MANUALS') {
            throw new Error("Failed to switch to CODES & MANUALS mode");
        }
        await client.captureScreenshot('rdso_mode_codes_manuals.png');
        console.log("[PASS] Codes & Manuals mode activated and rendered successfully!");

        // 3. Inspect IRPWM 2024 Document Node
        console.log("\n--- TEST 3: Inspect IRPWM 2024 Document Node ---");
        await client.evaluate(`window.selectGraphNode('doc_irpwm_2024')`);
        await sleep(1200);

        const docCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            domain: document.getElementById('drawer-domain').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText
        })`);
        console.log(`[*] Drawer Title: ${docCard.title}`);
        console.log(`[*] Domain: ${docCard.domain}`);
        console.log(`[*] Card Snippet: ${docCard.cardDesc.substring(0, 150)}...`);

        if (!docCard.cardDesc.includes("530 Pages") || !docCard.cardDesc.includes("Railway Board")) {
            throw new Error("IRPWM 2024 Document Answer Card missing pages or authority citation");
        }
        await client.captureScreenshot('rdso_manual_doc_card.png');
        console.log("[PASS] IRPWM Document Answer Card validated!");

        // 4. Inspect IRPWM Para 429(3) Crossing Clearance Clause
        console.log("\n--- TEST 4: Inspect IRPWM Para 429(3) Crossing Clearance Clause ---");
        await client.evaluate(`window.selectGraphNode('spec_irpwm_para429_crossing')`);
        await sleep(1200);

        const clauseCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText,
            lineageCount: document.getElementById('drawer-lineage-list').children.length
        })`);
        console.log(`[*] Clause Title: ${clauseCard.title}`);
        console.log(`[*] Card Details: ${clauseCard.cardDesc.substring(0, 180)}...`);
        console.log(`[*] Connected Lineage Hops: ${clauseCard.lineageCount}`);

        if (!clauseCard.cardDesc.includes("41 to 45 mm") || !clauseCard.cardDesc.includes("10 mm")) {
            throw new Error("Para 429(3) Answer Card missing check rail clearance (41-45 mm) or vertical wear (10 mm)!");
        }
        await client.captureScreenshot('rdso_clause_para429_card.png');
        console.log("[PASS] Para 429(3) Regulatory Answer Card validated!");

        // 5. Inspect Tolerance Node: Check Rail Clearance (41 - 45 mm)
        console.log("\n--- TEST 5: Inspect Tolerance Node (41 - 45 mm) ---");
        await client.evaluate(`window.selectGraphNode('tol_checkrail_clearance')`);
        await sleep(1200);

        const tolCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText
        })`);
        console.log(`[*] Tolerance Title: ${tolCard.title}`);
        console.log(`[*] Tolerance Details: ${tolCard.cardDesc.substring(0, 160)}...`);

        if (!tolCard.cardDesc.includes("41 - 45 mm") || !tolCard.cardDesc.includes("IRPWM Para 429(3)(b)")) {
            throw new Error("Tolerance Answer Card missing 41 - 45 mm or Para 429(3)(b) citation");
        }
        await client.captureScreenshot('rdso_tolerance_checkrail_card.png');
        console.log("[PASS] Tolerance Answer Card validated!");

        // 6. Test USFD Chapter 10 Tongue Rail Scanning SOP
        console.log("\n--- TEST 6: Inspect USFD Chapter 10 Tongue Rail Scanning SOP ---");
        await client.evaluate(`window.selectGraphNode('sop_usfd_switch_testing')`);
        await sleep(1200);

        const usfdCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText
        })`);
        console.log(`[*] USFD SOP Title: ${usfdCard.title}`);
        console.log(`[*] USFD SOP Details: ${usfdCard.cardDesc.substring(0, 180)}...`);

        if (!usfdCard.cardDesc.includes("Zone-1") || !usfdCard.cardDesc.includes("70°")) {
            throw new Error("USFD SOP Answer Card missing Zone-1 or 70° probe details");
        }
        console.log("[PASS] USFD SOP Answer Card validated!");

        // 7. Global Search Query for Railway Regulations
        console.log("\n--- TEST 7: Search for Manual Clauses & Regulations ---");
        const searchRes = await client.evaluate(`(() => {
            const input = document.getElementById('global-search');
            input.value = "Para 429";
            input.dispatchEvent(new Event('input'));
            const dropdown = document.getElementById('search-dropdown');
            return {
                display: dropdown.style.display,
                itemCount: dropdown.querySelectorAll('.search-item').length,
                firstItem: dropdown.querySelector('.search-item-title')?.innerText
            };
        })()`);
        console.log(`[*] Search Dropdown Display: ${searchRes.display}`);
        console.log(`[*] Matching Items: ${searchRes.itemCount}`);
        console.log(`[*] First Match: ${searchRes.firstItem}`);

        if (searchRes.itemCount === 0 || !searchRes.firstItem) {
            throw new Error("Search for 'Para 429' returned 0 matches in dropdown");
        }
        await client.captureScreenshot('rdso_search_manuals.png');
        console.log("[PASS] Search indexing for Railway Manuals validated!");

        console.log("\n================================================================================");
        console.log("ALL 7 AUTOMATED VERIFICATION TESTS PASSED SUCCESSFULLY!");
        console.log("================================================================================");

    } catch (err) {
        console.error("\n[FAIL] Test Error:", err);
        process.exitCode = 1;
    } finally {
        if (client && client.ws) {
            client.ws.close();
        }
        chrome.kill();
        console.log("[*] Chrome test instance terminated.");
    }
}

run();
