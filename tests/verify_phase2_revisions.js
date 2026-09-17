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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_phase2_profile');

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
    console.log('[*] Spawning Chrome headless for Phase 2 Verification...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9232',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    try {
        await sleep(2000);
        const tabs = await fetchJson('http://127.0.0.1:9232/json');
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

        // TEST 1: Select T-6155 and Switch to Revisions & Diff Tab
        console.log('\n--- TEST 1: Interactive Revision Diff View (Alt 10 -> Alt 13) ---');
        const diffRes = await client.evaluate(`(() => {
            window.selectGraphNode('drg_6155');
            window.switchDrawerTab('revisions');
            const pane = document.getElementById('tab-pane-revisions');
            const diffCards = Array.from(pane.querySelectorAll('.diff-card'));
            const addedPill = pane.querySelector('.diff-metric-val')?.innerText;
            const impactTitle = pane.querySelector('.drawing-section-title')?.innerText?.replace(/\\s+/g, ' ');
            const hops = Array.from(pane.querySelectorAll('.impact-step-card')).map(h => h.innerText.replace(/\\s+/g, ' '));
            return {
                activeTab: pane.classList.contains('active'),
                diffCardCount: diffCards.length,
                addedCount: addedPill,
                impactTitle,
                firstDiffItem: diffCards[0]?.innerText?.replace(/\\s+/g, ' ').slice(0, 120),
                hopsCount: hops.length
            };
        })()`);
        console.log('Revision Diff Result:', diffRes);
        if (!diffRes.activeTab || diffRes.diffCardCount === 0 || diffRes.hopsCount === 0) {
            throw new Error(`Revision diff test failed: ${JSON.stringify(diffRes)}`);
        }
        await client.captureScreenshot('phase2_revisions_diff_view.png');

        // TEST 2: Alteration Selection (Alt 11 -> Alt 12)
        console.log('\n--- TEST 2: Alteration Selection & Detail B Dowel Note Diff (Alt 11 -> Alt 12) ---');
        const alt12Res = await client.evaluate(`(() => {
            window.renderRevisionDiffView(11, 12);
            const pane = document.getElementById('tab-pane-revisions');
            const diffCards = Array.from(pane.querySelectorAll('.diff-card'));
            const note25Card = diffCards.find(c => c.innerText.includes('NOTE 25'));
            return {
                diffCount: diffCards.length,
                hasNote25: !!note25Card,
                note25Snippet: note25Card ? note25Card.innerText.replace(/\\s+/g, ' ').slice(0, 140) : null
            };
        })()`);
        console.log('Alt 12 Diff Result:', alt12Res);
        if (!alt12Res.hasNote25) {
            throw new Error(`Alt 12 diff failed to show Note 25: ${JSON.stringify(alt12Res)}`);
        }
        await client.captureScreenshot('phase2_revisions_diff_alt12.png');

        // TEST 3: Standards Conflict Dashboard (Blueprint Section 30)
        console.log('\n--- TEST 3: Standards Conflict & Precedence Dashboard ---');
        const conflictRes = await client.evaluate(`(() => {
            window.switchDrawerTab('conflicts');
            const pane = document.getElementById('tab-pane-conflicts');
            const conflictCards = Array.from(pane.querySelectorAll('.conflict-card'));
            const titles = conflictCards.map(c => c.querySelector('strong')?.innerText);
            const statuses = conflictCards.map(c => c.querySelector('.conflict-status-badge')?.innerText);
            return {
                activeTab: pane.classList.contains('active'),
                cardCount: conflictCards.length,
                titles,
                statuses
            };
        })()`);
        console.log('Conflict Dashboard Result:', conflictRes);
        if (!conflictRes.activeTab || conflictRes.cardCount !== 3 || !conflictRes.statuses.every(s => s === 'RESOLVED')) {
            throw new Error(`Conflict dashboard test failed: ${JSON.stringify(conflictRes)}`);
        }
        await client.captureScreenshot('phase2_standards_conflicts.png');

        // TEST 4: Evidence Modal & Deep Provenance
        console.log('\n--- TEST 4: Evidence Modal & Provenance Verification ---');
        const evidenceRes = await client.evaluate(`(() => {
            window.openEvidenceModal({
                title: 'Note 28: LIST-A 10% Spares Quota',
                text: '10% QUANTITY (i.e. 1/10th Nos. OF THE QUANTITY OF TURNOUT ON ORDER) OF LIST-A ITEMS SHALL BE PROCURED...',
                dwg: 'RDSO/T-6155 Alt 13',
                crop: 'crops/t6155_notes_full.png'
            });
            const modal = document.getElementById('evidence-modal');
            const content = document.getElementById('evidence-modal-content');
            const statusBadge = content.querySelector('.drawing-meta-value')?.innerText;
            const isVisible = modal.style.display === 'flex';
            return {
                modalVisible: isVisible,
                title: content.querySelector('blockquote')?.innerText?.replace(/\\s+/g, ' ').slice(0, 100),
                status: statusBadge
            };
        })()`);
        console.log('Evidence Modal Result:', evidenceRes);
        if (!evidenceRes.modalVisible) {
            throw new Error(`Evidence modal failed to open: ${JSON.stringify(evidenceRes)}`);
        }
        await client.captureScreenshot('phase2_evidence_modal.png');

        // Close modal
        await client.evaluate(`window.closeEvidenceModal()`);
        const isClosed = await client.evaluate(`document.getElementById('evidence-modal').style.display === 'none'`);
        if (!isClosed) {
            throw new Error('Evidence modal failed to close');
        }

        console.log('\n[SUCCESS] Phase 2 Evidence and Revision Intelligence completely verified!');
    } finally {
        chrome.kill();
    }
}

run().catch(err => {
    console.error('[FAIL]', err);
    process.exit(1);
});
