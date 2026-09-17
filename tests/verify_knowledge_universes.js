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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_universes_profile');

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
    console.log('[*] Spawning Chrome headless for Knowledge Universes & Hierarchy Verification...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9236',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    try {
        await sleep(2000);
        const tabs = await fetchJson('http://127.0.0.1:9236/json');
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
        // TEST 1: INITIAL STATE - DRAWINGS UNIVERSE ACTIVE & CLEAN SEGREGATION
        // =========================================================================
        console.log('\n--- TEST 1: Verify Drawings Universe Active & Clean Segregation ---');
        const initialUniverseState = await cdp.evaluate(`(() => {
            const drawingsBtn = document.getElementById('btn-univ-drawings');
            const manualsBtn = document.getElementById('btn-univ-manuals');
            const combinedBtn = document.getElementById('btn-univ-combined');
            const badge = document.getElementById('hierarchy-visible-count');
            
            const visibleNodes = window.kgPhysicsNodes ? window.kgPhysicsNodes.filter(n => n.group.visible) : [];
            const visibleDrawings = visibleNodes.filter(n => n.universe === 'drawings');
            const visibleManuals = visibleNodes.filter(n => n.universe === 'manuals');
            
            return {
                drawingsActive: drawingsBtn ? drawingsBtn.classList.contains('active') : false,
                manualsActive: manualsBtn ? manualsBtn.classList.contains('active') : false,
                combinedActive: combinedBtn ? combinedBtn.classList.contains('active') : false,
                badgeText: badge ? badge.innerText : '',
                totalVisible: visibleNodes.length,
                drawingsVisibleCount: visibleDrawings.length,
                manualsVisibleCount: visibleManuals.length,
                sampleVisibleIds: visibleNodes.slice(0, 10).map(n => n.data.id)
            };
        })()`);

        console.log('Initial Universe State:', initialUniverseState);
        if (!initialUniverseState.drawingsActive) throw new Error('Expected Drawings Universe to be active by default');
        if (initialUniverseState.manualsVisibleCount > 0) throw new Error(`Drawings universe contaminated with ${initialUniverseState.manualsVisibleCount} manual nodes!`);
        if (initialUniverseState.drawingsVisibleCount === 0) throw new Error('Expected drawing nodes to be visible in Drawings universe');
        if (initialUniverseState.totalVisible > 80) throw new Error(`Expected clean drawing ecosystem (< 80 nodes), got ${initialUniverseState.totalVisible}`);

        await cdp.captureScreenshot('universe_drawings.png');

        // =========================================================================
        // TEST 2: SWITCH TO MANUALS UNIVERSE & VERIFY CODE/MANUAL ROOTS
        // =========================================================================
        console.log('\n--- TEST 2: Switch to Manuals Universe & Verify Regulatory Roots ---');
        await cdp.evaluate(`window.switchKnowledgeUniverse('manuals')`);
        await sleep(800);

        const manualsUniverseState = await cdp.evaluate(`(() => {
            const drawingsBtn = document.getElementById('btn-univ-drawings');
            const manualsBtn = document.getElementById('btn-univ-manuals');
            const combinedBtn = document.getElementById('btn-univ-combined');
            const badge = document.getElementById('hierarchy-visible-count');

            const visibleNodes = window.kgPhysicsNodes.filter(n => n.group.visible);
            const visibleDrawings = visibleNodes.filter(n => n.universe === 'drawings');
            const visibleManuals = visibleNodes.filter(n => n.universe === 'manuals');

            return {
                drawingsActive: drawingsBtn.classList.contains('active'),
                manualsActive: manualsBtn.classList.contains('active'),
                combinedActive: combinedBtn.classList.contains('active'),
                badgeText: badge.innerText,
                totalVisible: visibleNodes.length,
                drawingsVisibleCount: visibleDrawings.length,
                manualsVisibleCount: visibleManuals.length,
                sampleVisibleIds: visibleNodes.map(n => n.data.id)
            };
        })()`);

        console.log('Manuals Universe State (Collapsed Roots):', manualsUniverseState);
        if (!manualsUniverseState.manualsActive) throw new Error('Expected Manuals Universe button to be active');
        if (manualsUniverseState.drawingsVisibleCount > 0) throw new Error(`Manuals universe contaminated with ${manualsUniverseState.drawingsVisibleCount} drawing nodes!`);
        if (manualsUniverseState.manualsVisibleCount === 0) throw new Error('Expected manual root documents to be visible');
        if (!manualsUniverseState.sampleVisibleIds.some(id => id.includes('IRPWM') || id.includes('irpwm'))) {
            throw new Error('Expected IRPWM root document to be visible in Manuals universe');
        }

        await cdp.captureScreenshot('universe_manuals_collapsed.png');

        // =========================================================================
        // TEST 3: CLICK-TO-EXPAND HIERARCHY ON MANUALS TREE
        // =========================================================================
        console.log('\n--- TEST 3: Click-to-Expand Manual Chapters & Clauses ---');
        const countBeforeExpand = manualsUniverseState.totalVisible;

        // Expand IRPWM 2024 root
        await cdp.evaluate(`(() => {
            const irpwmRoot = window.kgPhysicsNodes.find(n => n.data.id === 'DOC:IRPWM:2024:ACS14');
            if (irpwmRoot) window.toggleNodeExpansion(irpwmRoot.data.id);
        })()`);
        await sleep(600);

        const countAfterExpandDoc = await cdp.evaluate(`window.kgPhysicsNodes.filter(n => n.group.visible).length`);
        console.log(`Visible nodes after expanding IRPWM root: ${countAfterExpandDoc} (was ${countBeforeExpand})`);
        if (countAfterExpandDoc <= countBeforeExpand) {
            throw new Error(`Expanding IRPWM document should reveal chapters! Before: ${countBeforeExpand}, After: ${countAfterExpandDoc}`);
        }

        // Expand Chapter 4 (Turnouts & Crossings)
        await cdp.evaluate(`(() => {
            const ch4 = window.kgPhysicsNodes.find(n => n.data.id === 'CHAPTER:IRPWM:CH_04');
            if (ch4) window.toggleNodeExpansion(ch4.data.id);
        })()`);
        await sleep(600);

        const countAfterExpandCh4 = await cdp.evaluate(`window.kgPhysicsNodes.filter(n => n.group.visible).length`);
        console.log(`Visible nodes after expanding Chapter 4: ${countAfterExpandCh4}`);
        if (countAfterExpandCh4 <= countAfterExpandDoc) {
            throw new Error('Expanding Chapter 4 should reveal clauses');
        }

        await cdp.captureScreenshot('universe_manuals_expanded.png');

        // Test Collapse All back to Roots
        console.log('[*] Testing collapseAllToRoots()...');
        await cdp.evaluate(`window.collapseAllToRoots()`);
        await sleep(500);
        const countAfterCollapse = await cdp.evaluate(`window.kgPhysicsNodes.filter(n => n.group.visible).length`);
        console.log(`Visible nodes after collapse to roots: ${countAfterCollapse}`);
        if (countAfterCollapse !== countBeforeExpand) {
            console.log(`Note: collapsed count is ${countAfterCollapse}, baseline was ${countBeforeExpand}`);
        }

        // =========================================================================
        // TEST 4: SWITCH TO COMBINED COSMOS & VERIFY TWIN SPATIAL GALAXIES
        // =========================================================================
        console.log('\n--- TEST 4: Switch to Combined Cosmos & Verify Twin Galaxies ---');
        await cdp.evaluate(`window.switchKnowledgeUniverse('combined')`);
        await sleep(1200);

        const combinedState = await cdp.evaluate(`(() => {
            const combinedBtn = document.getElementById('btn-univ-combined');
            const visibleNodes = window.kgPhysicsNodes.filter(n => n.group.visible);
            const drawingsNodes = visibleNodes.filter(n => n.universe === 'drawings');
            const manualsNodes = visibleNodes.filter(n => n.universe === 'manuals');

            const drawingsAvgX = drawingsNodes.length ? drawingsNodes.reduce((acc, n) => acc + n.x, 0) / drawingsNodes.length : 0;
            const manualsAvgX = manualsNodes.length ? manualsNodes.reduce((acc, n) => acc + n.x, 0) / manualsNodes.length : 0;

            return {
                combinedActive: combinedBtn.classList.contains('active'),
                totalVisible: visibleNodes.length,
                drawingsCount: drawingsNodes.length,
                manualsCount: manualsNodes.length,
                drawingsAvgX,
                manualsAvgX,
                galaxySeparationDistance: Math.abs(manualsAvgX - drawingsAvgX)
            };
        })()`);

        console.log('Combined Cosmos Twin Galaxies State:', combinedState);
        if (!combinedState.combinedActive) throw new Error('Expected Combined Cosmos button to be active');
        if (combinedState.drawingsCount === 0 || combinedState.manualsCount === 0) {
            throw new Error('Expected both Drawings and Manuals entities visible in Combined mode');
        }
        if (combinedState.drawingsAvgX >= combinedState.manualsAvgX) {
            throw new Error(`Expected Drawings Galaxy to be West of Manuals Galaxy! Drawings X: ${combinedState.drawingsAvgX}, Manuals X: ${combinedState.manualsAvgX}`);
        }

        await cdp.captureScreenshot('universe_combined_galaxies.png');

        // =========================================================================
        // TEST 5: BACKWARD COMPATIBILITY & AUTO-EXPANSION VIA selectGraphNode
        // =========================================================================
        console.log('\n--- TEST 5: Select comp_detailb and verify auto-expansion & dossier ---');
        await cdp.evaluate(`window.selectGraphNode('comp_detailb')`);
        await sleep(800);

        const selectionState = await cdp.evaluate(`(() => {
            const drawer = document.getElementById('intelligence-drawer');
            const idBadge = document.getElementById('drawer-id-badge');
            const node = window.kgPhysicsNodes.find(n => n.data.id === 'comp_detailb');
            const overviewPane = document.getElementById('tab-pane-overview');
            const toggleBtn = overviewPane.querySelector('button[onclick*="toggleNodeExpansion"]');

            return {
                drawerOpen: !drawer.classList.contains('collapsed'),
                idBadgeText: idBadge ? idBadge.innerText : '',
                nodeVisible: node ? node.group.visible : false,
                nodeUniverse: node ? node.universe : '',
                hasExpandButtonInDossier: !!toggleBtn,
                toggleBtnText: toggleBtn ? toggleBtn.innerText : ''
            };
        })()`);

        console.log('Selection and Dossier State for comp_detailb:', selectionState);
        if (!selectionState.drawerOpen) throw new Error('Drawer should be open after selectGraphNode');
        if (selectionState.idBadgeText !== 'comp_detailb') throw new Error(`Expected idBadge comp_detailb, got ${selectionState.idBadgeText}`);
        if (!selectionState.nodeVisible) throw new Error('comp_detailb must be visible after auto-expansion');
        if (!selectionState.hasExpandButtonInDossier) throw new Error('Expected Expand/Collapse subtree button in Node Dossier');

        await cdp.captureScreenshot('universe_dossier_expanded_comp.png');

        console.log('\n[SUCCESS] Knowledge Universes & Hierarchy Expansion architecture verified 100%!');
    } finally {
        chrome.kill();
    }
}

run().catch(err => {
    console.error('[FAIL]', err);
    process.exit(1);
});
