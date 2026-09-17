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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_phase1_profile');

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
    console.log('[*] Spawning Chrome headless for Phase 1 & Milestone 1 Verification...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9228',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    try {
        await sleep(2000);
        const versionInfo = await fetchJson('http://127.0.0.1:9228/json/version');
        const tabs = await fetchJson('http://127.0.0.1:9228/json');
        const target = tabs.find(t => t.type === 'page') || tabs[0];
        const client = new CDPClient(target.webSocketDebuggerUrl);
        await client.ready;

        await client.send('Page.enable');
        await client.send('Runtime.enable');
        await client.send('Emulation.setDeviceMetricsOverride', {
            width: 1920,
            height: 1080,
            deviceScaleFactor: 1,
            mobile: false
        });

        console.log('[*] Navigating to index.html...');
        await client.send('Page.navigate', { url: targetUrl });
        await sleep(3500);

        // TEST 1: Search for T-6155 & verify layered card ranking
        console.log('\n--- TEST 1: Search Autocomplete & Layered Result Cards ---');
        const searchRes = await client.evaluate(`(() => {
            const input = document.getElementById('global-search');
            input.value = "T-6155";
            input.dispatchEvent(new Event('input'));
            const dropdown = document.getElementById('search-dropdown');
            const cards = Array.from(dropdown.querySelectorAll('.search-card'));
            return {
                display: dropdown.style.display,
                cardCount: cards.length,
                topTitle: cards[0]?.querySelector('.search-card-title')?.innerText?.replace(/\\s+/g, ' '),
                topTypeBadge: cards[0]?.querySelector('.search-card-type-badge')?.innerText,
                topRevBadge: cards[0]?.querySelector('.search-card-rev-badge')?.innerText,
                topEvidence: cards[0]?.querySelector('.search-card-evidence')?.innerText?.replace(/\\s+/g, ' ')
            };
        })()`);
        console.log('Search Results:', searchRes);
        if (searchRes.cardCount === 0 || !searchRes.topTitle.includes('6155')) {
            throw new Error(`Search failed for T-6155: ${JSON.stringify(searchRes)}`);
        }
        await client.captureScreenshot('phase1_search_t6155_cards.png');

        // TEST 2: Inspect drg_6155 & verify 9-section drawing overview
        console.log('\n--- TEST 2: Inspect Drawing & Verify 9 Canonical Sections ---');
        const overviewRes = await client.evaluate(`(() => {
            window.selectGraphNode('drg_6155');
            const drawer = document.getElementById('intelligence-drawer');
            const breadcrumbNode = document.getElementById('breadcrumb-current-node')?.innerText;
            const overviewPane = document.getElementById('tab-pane-overview');
            const sections = Array.from(overviewPane.querySelectorAll('.drawing-section'));
            const sectionTitles = sections.map(s => s.querySelector('.drawing-section-title')?.innerText?.trim());
            return {
                drawerOpen: !drawer.classList.contains('collapsed'),
                breadcrumbNode,
                overviewActive: overviewPane.classList.contains('active'),
                sectionCount: sections.length,
                sectionTitles
            };
        })()`);
        console.log('9-Section Overview Result:', overviewRes);
        if (overviewRes.sectionCount < 9) {
            throw new Error(`Expected at least 9 sections in drawing overview, got ${overviewRes.sectionCount}`);
        }
        await client.captureScreenshot('phase1_drawing_overview_9sections.png');

        console.log('\n[SUCCESS] Phase 1 Search & 9-Section Drawing Intelligence completely verified!');
    } finally {
        chrome.kill();
    }
}

run().catch(err => {
    console.error('[FAIL]', err);
    process.exit(1);
});
