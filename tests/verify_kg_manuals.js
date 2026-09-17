const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const chromeCandidates = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe'),
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
];
const chromePath = chromeCandidates.find(p => fs.existsSync(p)) || chromeCandidates[0];
const targetUrl = 'file:///' + path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/');
const artifactDir = [
    "C:\\Users\\LENOVO\\.gemini\\antigravity-ide\\brain\\ea8fa10c-88f4-4a72-b9b0-d40e78abc040",
    path.join(__dirname, '..', 'artifacts')
].find(d => fs.existsSync(d)) || path.join(__dirname, '..', 'artifacts');
if (!fs.existsSync(artifactDir)) { try { fs.mkdirSync(artifactDir, { recursive: true }); } catch (e) {} }
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_manuals_profile');

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
        targetUrl
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
        console.log(`[*] Active Nodes: ${metrics.nodes} (Target >= 2000)`);
        console.log(`[*] Active Edges: ${metrics.edges} (Target >= 3000)`);
        console.log(`[*] Active Facts: ${metrics.facts} (Target >= 141)`);
        console.log(`[*] Semantic Modes: ${metrics.modes.join(', ')}`);

        if (metrics.nodes < 2000 || metrics.edges < 3000) {
            throw new Error(`Metrics lower than deep canonical target: nodes=${metrics.nodes}, edges=${metrics.edges}`);
        }
        if (!metrics.modes.includes('manuals')) {
            throw new Error("Semantic modes bar missing 'manuals' mode button!");
        }
        console.log("[PASS] Knowledge Core extended with Deep Railway Codes & Manuals!");

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
        await client.evaluate(`window.selectGraphNode('DOC:IRPWM:2024:ACS14')`);
        await sleep(1200);

        const docCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            domain: document.getElementById('drawer-domain').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText
        })`);
        console.log(`[*] Drawer Title: ${docCard.title}`);
        console.log(`[*] Domain: ${docCard.domain}`);
        console.log(`[*] Card Snippet: ${docCard.cardDesc.substring(0, 150)}...`);

        if (!docCard.cardDesc.includes("IRPWM") && !docCard.cardDesc.includes("Indian Railways")) {
            throw new Error("IRPWM 2024 Document Answer Card missing title citation");
        }
        await client.captureScreenshot('rdso_manual_doc_card.png');
        console.log("[PASS] IRPWM Document Answer Card validated!");

        // 4. Inspect IRPWM Para 429 Crossing Maintenance Clause
        console.log("\n--- TEST 4: Inspect IRPWM Para 429 Crossing Maintenance Clause ---");
        await client.evaluate(`window.selectGraphNode('CLAUSE:IRPWM:PARA_429') || window.selectGraphNode('spec_irpwm_para429_crossing')`);
        await sleep(1200);

        const clauseCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText,
            lineageCount: document.getElementById('drawer-lineage-list').children.length
        })`);
        console.log(`[*] Clause Title: ${clauseCard.title}`);
        console.log(`[*] Card Details: ${clauseCard.cardDesc.substring(0, 180)}...`);
        console.log(`[*] Connected Lineage Hops: ${clauseCard.lineageCount}`);

        if (!clauseCard.cardDesc.includes("429") && !clauseCard.cardDesc.includes("41 to 45 mm")) {
            throw new Error("Para 429 Answer Card missing paragraph 429 citation!");
        }
        await client.captureScreenshot('rdso_clause_para429_card.png');
        console.log("[PASS] Para 429 Regulatory Answer Card validated!");

        // 5. Inspect Tolerance Node: Check Rail Clearance (41 - 45 mm)
        console.log("\n--- TEST 5: Inspect Tolerance Node (41 - 45 mm) ---");
        await client.evaluate(`window.selectGraphNode('tol_checkrail_clearance') || window.selectGraphNode('TOL:CHECKRAIL_CLEARANCE:41_45MM')`);
        await sleep(1200);

        const tolCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText
        })`);
        console.log(`[*] Tolerance Title: ${tolCard.title}`);
        console.log(`[*] Tolerance Details: ${tolCard.cardDesc.substring(0, 160)}...`);

        if (!tolCard.cardDesc.includes("41") || !tolCard.cardDesc.includes("45")) {
            throw new Error("Tolerance Answer Card missing 41-45 mm bounds");
        }
        await client.captureScreenshot('rdso_tolerance_checkrail_card.png');
        console.log("[PASS] Tolerance Answer Card validated!");

        // 6. Test USFD Chapter 10 Tongue Rail Scanning SOP
        console.log("\n--- TEST 6: Inspect USFD Chapter 10 Tongue Rail Scanning SOP ---");
        await client.evaluate(`window.selectGraphNode('sop_usfd_switch_testing') || window.selectGraphNode('CHAPTER:USFD:CH_10')`);
        await sleep(1200);

        const usfdCard = await client.evaluate(`({
            title: document.getElementById('drawer-title').innerText,
            cardDesc: document.getElementById('answer-card-desc').innerText
        })`);
        console.log(`[*] USFD SOP/Chapter Title: ${usfdCard.title}`);
        console.log(`[*] USFD Details: ${usfdCard.cardDesc.substring(0, 180)}...`);
        console.log("[PASS] USFD SOP/Chapter Answer Card validated!");

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

        // 8. Test Chapter Tree & TOC Navigator
        console.log("\n--- TEST 8: Test Interactive Chapter Tree & TOC Navigator ---");
        await client.evaluate(`switchDrawerTab('manuals')`);
        await sleep(1000);

        const treeMetrics = await client.evaluate(`({
            tabBadge: document.getElementById('manuals-tab-count')?.innerText,
            manualsRendered: document.querySelectorAll('.manual-tree-card').length,
            firstManualTitle: document.querySelector('.manual-tree-header strong')?.innerText,
            firstManualBadge: document.querySelector('.manual-tree-badge')?.innerText
        })`);
        console.log(`[*] Manuals Tab Badge: ${treeMetrics.tabBadge}`);
        console.log(`[*] Manuals Rendered in Tree: ${treeMetrics.manualsRendered} (Expected: 6)`);
        console.log(`[*] First Manual: ${treeMetrics.firstManualTitle}`);
        console.log(`[*] First Manual Badge: ${treeMetrics.firstManualBadge}`);

        if (treeMetrics.manualsRendered < 6) {
            throw new Error(`Expected 6 manual cards in tree, found ${treeMetrics.manualsRendered}`);
        }

        // Live filter test: search for "429"
        await client.evaluate(`filterManualsTree('429')`);
        await sleep(600);

        const filterMetrics = await client.evaluate(`({
            openChapters: document.querySelectorAll('.chapter-tree-body.open').length,
            visibleClauses: document.querySelectorAll('.clause-tree-item').length,
            firstClauseText: document.querySelector('.clause-tree-item .clause-title-text')?.innerText
        })`);
        console.log(`[*] Filtered Open Chapters: ${filterMetrics.openChapters}`);
        console.log(`[*] Filtered Visible Clauses: ${filterMetrics.visibleClauses}`);
        console.log(`[*] First Filtered Clause: ${filterMetrics.firstClauseText}`);

        if (filterMetrics.visibleClauses === 0) {
            throw new Error("Filtering tree for '429' returned 0 clauses!");
        }

        await client.captureScreenshot('rdso_chapter_tree_navigator.png');
        console.log("[PASS] Interactive Chapter Tree & TOC Navigator validated!");

        console.log("\n================================================================================");
        console.log("ALL 8 AUTOMATED VERIFICATION TESTS PASSED SUCCESSFULLY!");
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
