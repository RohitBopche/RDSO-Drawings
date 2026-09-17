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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_nodepanel_profile');

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
    console.log('[*] Spawning Chrome headless for Right Side Panel Upgrade Verification...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9235',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    try {
        await sleep(2000);
        const tabs = await fetchJson('http://127.0.0.1:9235/json');
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
        // TEST 1: SELECT COMPONENT NODE (comp_detailb) & VERIFY NODE PROFILE
        // =========================================================================
        console.log('\n--- TEST 1: Select comp_detailb and verify Node Dossier ---');
        await cdp.evaluate(`window.selectGraphNode('comp_detailb')`);
        await sleep(800);

        const nodePanelData = await cdp.evaluate(`(() => {
            const drawer = document.getElementById('intelligence-drawer');
            const idBadge = document.getElementById('drawer-id-badge');
            const title = document.getElementById('drawer-title');
            const tabLabel = document.getElementById('overview-tab-label');
            const overviewPane = document.getElementById('tab-pane-overview');
            const sections = Array.from(overviewPane.querySelectorAll('.drawing-section'));
            const sectionTitles = sections.map(s => s.querySelector('.drawing-section-title')?.innerText?.trim());
            const metaItems = Array.from(overviewPane.querySelectorAll('.drawing-meta-item'));
            const lineages = Array.from(overviewPane.querySelectorAll('.lineage-tag'));

            return {
                drawerOpen: !drawer.classList.contains('collapsed'),
                idBadgeText: idBadge ? idBadge.innerText : '',
                idBadgeDisplay: idBadge ? idBadge.style.display : '',
                titleText: title ? title.innerText : '',
                tabLabelText: tabLabel ? tabLabel.innerText : '',
                sectionCount: sections.length,
                sectionTitles,
                metaCount: metaItems.length,
                lineageCount: lineages.length,
                fullText: overviewPane.innerText
            };
        })()`);

        console.log('Node Panel Result for comp_detailb:', {
            drawerOpen: nodePanelData.drawerOpen,
            idBadgeText: nodePanelData.idBadgeText,
            titleText: nodePanelData.titleText,
            tabLabelText: nodePanelData.tabLabelText,
            sectionCount: nodePanelData.sectionCount,
            sectionTitles: nodePanelData.sectionTitles,
            metaCount: nodePanelData.metaCount,
            lineageCount: nodePanelData.lineageCount
        });

        if (!nodePanelData.drawerOpen) throw new Error('Drawer failed to open on node selection');
        if (nodePanelData.idBadgeText !== 'comp_detailb') throw new Error(`Expected idBadge comp_detailb, got ${nodePanelData.idBadgeText}`);
        if (!nodePanelData.titleText.includes("Detail 'B'")) throw new Error(`Expected title containing Detail B, got ${nodePanelData.titleText}`);
        if (nodePanelData.tabLabelText !== 'Node Dossier') throw new Error(`Expected tab label 'Node Dossier', got ${nodePanelData.tabLabelText}`);
        if (nodePanelData.metaCount < 4) throw new Error(`Expected at least 4 metadata specs, got ${nodePanelData.metaCount}`);
        if (nodePanelData.lineageCount === 0) throw new Error('Expected connected graph lineage hops, got 0');
        if (!nodePanelData.fullText.includes('222 mm')) throw new Error('Expected 222 mm drop specification in node profile');

        await cdp.captureScreenshot('node_panel_selected_comp_detailb.png');

        // =========================================================================
        // TEST 2: SELECT STANDARD NODE (std_irs_t10) & VERIFY DEDICATED PROFILE
        // =========================================================================
        console.log('\n--- TEST 2: Select std_irs_t10 and verify Standard Profile ---');
        await cdp.evaluate(`window.selectGraphNode('std_irs_t10')`);
        await sleep(800);

        const stdPanelData = await cdp.evaluate(`(() => {
            const idBadge = document.getElementById('drawer-id-badge');
            const title = document.getElementById('drawer-title');
            const tabLabel = document.getElementById('overview-tab-label');
            const overviewPane = document.getElementById('tab-pane-overview');

            return {
                idBadgeText: idBadge ? idBadge.innerText : '',
                titleText: title ? title.innerText : '',
                tabLabelText: tabLabel ? tabLabel.innerText : '',
                hasStandardsText: overviewPane.innerText.includes('IRS: T 10') || overviewPane.innerText.includes('Curved Switch')
            };
        })()`);

        console.log('Node Panel Result for std_irs_t10:', stdPanelData);
        if (stdPanelData.idBadgeText !== 'std_irs_t10') throw new Error(`Expected idBadge std_irs_t10, got ${stdPanelData.idBadgeText}`);
        if (stdPanelData.tabLabelText !== 'Node Dossier') throw new Error(`Expected tab label 'Node Dossier', got ${stdPanelData.tabLabelText}`);

        await cdp.captureScreenshot('node_panel_selected_std_irst10.png');

        // =========================================================================
        // TEST 3: SELECT DRAWING NODE (drg_6155) & VERIFY 9 DRAWING SECTIONS
        // =========================================================================
        console.log('\n--- TEST 3: Select drg_6155 and verify Drawing Overview ---');
        await cdp.evaluate(`window.selectGraphNode('drg_6155')`);
        await sleep(800);

        const drgPanelData = await cdp.evaluate(`(() => {
            const idBadge = document.getElementById('drawer-id-badge');
            const tabLabel = document.getElementById('overview-tab-label');
            const overviewPane = document.getElementById('tab-pane-overview');
            const sections = Array.from(overviewPane.querySelectorAll('.drawing-section'));

            return {
                idBadgeText: idBadge ? idBadge.innerText : '',
                tabLabelText: tabLabel ? tabLabel.innerText : '',
                sectionCount: sections.length
            };
        })()`);

        console.log('Node Panel Result for drg_6155:', drgPanelData);
        if (drgPanelData.tabLabelText !== 'Drawing Overview') throw new Error(`Expected tab label 'Drawing Overview', got ${drgPanelData.tabLabelText}`);
        if (drgPanelData.sectionCount < 9) throw new Error(`Expected 9 drawing sections, got ${drgPanelData.sectionCount}`);

        await cdp.captureScreenshot('node_panel_selected_drg_6155.png');

        console.log('\n================================================================================');
        console.log('RIGHT SIDE PANEL NODE SELECTION UPGRADE: 100% VERIFIED');
        console.log('================================================================================\n');

    } finally {
        chrome.kill('SIGKILL');
        try { fs.rmSync(tempProfile, { recursive: true, force: true }); } catch (e) {}
    }
}

run().catch(err => {
    console.error('[!] Node Panel verification failed:', err);
    process.exit(1);
});
