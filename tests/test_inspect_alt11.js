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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_alt11_profile');

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
    console.log('[*] Spawning Chrome headless for Alt 11 Node Dossier Verification...');
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

        console.log('\n--- Inspecting rev_6155_alt11 ---');
        await cdp.evaluate(`window.selectGraphNode('rev_6155_alt11')`);
        await sleep(800);

        const details = await cdp.evaluate(`(() => {
            const idBadge = document.getElementById('drawer-id-badge')?.innerText;
            const title = document.getElementById('drawer-title')?.innerText;
            const domain = document.getElementById('drawer-domain')?.innerText;
            const answerCardDesc = document.getElementById('answer-card-desc')?.innerText;
            const provTitle = document.getElementById('prov-dwg-title')?.innerText;
            const toolbarButtons = Array.from(document.querySelectorAll('#answer-card-toolbar .answer-tool-btn')).map(b => b.innerText.trim().replace(/\\s+/g, ' '));
            const overviewText = document.getElementById('tab-pane-overview')?.innerText;
            const govDwg = Array.from(document.querySelectorAll('#tab-pane-overview .drawing-meta-item')).find(el => el.querySelector('.drawing-meta-label')?.innerText.toLowerCase().includes('governing drawing'))?.querySelector('.drawing-meta-value')?.innerText.trim();
            const categoryMeta = Array.from(document.querySelectorAll('#tab-pane-overview .drawing-meta-item')).find(el => el.querySelector('.drawing-meta-label')?.innerText.toLowerCase().includes('alteration category'))?.querySelector('.drawing-meta-value')?.innerText.trim();

            return {
                idBadge,
                title,
                domain,
                answerCardDesc,
                provTitle,
                toolbarButtons,
                govDwg,
                categoryMeta,
                hasNote28InDesc: answerCardDesc.includes('Note 28'),
                hasAlt13Badge: answerCardDesc.includes('ALT 13'),
                hasAlt11Badge: answerCardDesc.includes('ALT 11'),
                hasTorque550: overviewText.includes('550–650'),
                overviewSnippet: overviewText.slice(0, 300)
            };
        })()`);

        console.log('Alt 11 Inspection Result:', JSON.stringify(details, null, 2));

        if (details.idBadge !== 'rev_6155_alt11') throw new Error(`Expected idBadge rev_6155_alt11, got ${details.idBadge}`);
        if (details.hasNote28InDesc) throw new Error('Unwanted Note 28 directive found in Alt 11 description!');
        if (details.hasAlt13Badge) throw new Error('Unwanted ALT 13 badge found in Alt 11 description!');
        if (!details.hasAlt11Badge) throw new Error('Expected ALT 11 badge in Alt 11 description!');
        if (details.hasTorque550) throw new Error('Unwanted torque limit 550-650 Nm found on revision node!');
        if (details.govDwg !== 'RDSO/T-6155 (ALT 11)') throw new Error(`Expected governing drawing RDSO/T-6155 (ALT 11), got ${details.govDwg}`);
        if (!details.categoryMeta.includes('Revision')) throw new Error(`Expected revision category, got ${details.categoryMeta}`);

        // Capture screenshot of clean Alt 11 panel
        await cdp.captureScreenshot('node_panel_selected_rev_alt11_clean.png');

        console.log('\n================================================================================');
        console.log('REV_6155_ALT11 PANEL PURITY: 100% VERIFIED');
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
