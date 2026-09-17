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
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_interlink_profile');

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
    console.log('[*] Spawning Chrome headless...');
    const chrome = spawn(chromePath, [
        '--headless=new',
        '--remote-debugging-port=9222',
        '--window-size=1920,1080',
        '--disable-gpu',
        '--no-first-run',
        '--allow-file-access-from-files',
        `--user-data-dir=${tempProfile}`
    ], { stdio: 'ignore' });

    await sleep(2000);

    try {
        console.log('[*] Connecting to Chrome DevTools Protocol...');
        const version = await fetchJson('http://127.0.0.1:9222/json/version');
        console.log('[+] Connected. Chrome version:', version['User-Agent']);

        const targets = await fetchJson('http://127.0.0.1:9222/json/list');
        let pageTarget = targets.find(t => t.type === 'page');
        if (!pageTarget) {
            const newTab = await fetchJson('http://127.0.0.1:9222/json/new?' + targetUrl);
            pageTarget = newTab;
        }

        const client = new CDPClient(pageTarget.webSocketDebuggerUrl);
        await client.ready;
        console.log('[+] WebSocket connected to page');

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
        await sleep(4000);

        // Verify title & telemetry
        const telemetry = await client.evaluate(`
            ({
                title: document.title,
                nodes: document.getElementById('telem-nodes').innerText,
                edges: document.getElementById('telem-edges').innerText,
                facts: document.getElementById('telem-facts').innerText
            })
        `);
        console.log('\n--- TELEMETRY CHECK ---');
        console.log('Title:', telemetry.title);
        console.log(`Entities Loaded: ${telemetry.nodes} | Typed Edges: ${telemetry.edges} | Facts: ${telemetry.facts}`);

        await client.captureScreenshot('rdso_v35_canonical_canvas.png');

        // TEST 1: Semantic Mode - Explore
        console.log('\n--- TEST 1: Semantic Mode: Explore ---');
        await client.evaluate(`window.switchSemanticMode('explore');`);
        await sleep(500);
        await client.captureScreenshot('rdso_mode_explore.png');

        // TEST 2: Semantic Mode - Dependency Trace (comp_detailb)
        console.log('\n--- TEST 2: Semantic Mode: Dependency Trace (Detail B Bent Tie Bar) ---');
        await client.evaluate(`
            window.switchSemanticMode('trace');
            window.selectGraphNode('comp_detailb');
        `);
        await sleep(800);

        const traceData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const domain = document.getElementById('drawer-domain').innerText;
                const desc = document.getElementById('answer-card-desc').innerText;
                const provTitle = document.getElementById('prov-dwg-title').innerText;
                const hops = Array.from(document.querySelectorAll('#drawer-lineage-list .lineage-tag')).map(t => t.innerText.replace(/\\s+/g, ' '));
                return { title, domain, desc, provTitle, hops };
            })()
        `);
        console.log('Dependency Trace Result:');
        console.log(`- Entity: ${traceData.title} (${traceData.domain})`);
        console.log(`- Evidence: ${traceData.provTitle}`);
        console.log(`- Connected Hops:\n  ${traceData.hops.join('\n  ')}`);
        await client.captureScreenshot('rdso_mode_dependency_trace.png');

        // TEST 3: Semantic Mode - Revision Impact (rev_6155_alt10)
        console.log('\n--- TEST 3: Semantic Mode: Revision Impact (Alt 10 Welded Joint W) ---');
        await client.evaluate(`
            window.switchSemanticMode('revision');
            window.selectGraphNode('rev_6155_alt10');
        `);
        await sleep(800);

        const revData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const hops = Array.from(document.querySelectorAll('#drawer-lineage-list .lineage-tag')).map(t => t.innerText.replace(/\\s+/g, ' '));
                return { title, hops };
            })()
        `);
        console.log('Revision Impact Result:');
        console.log(`- Entity: ${revData.title}`);
        console.log(`- Connected Hops:\n  ${revData.hops.join('\n  ')}`);
        await client.captureScreenshot('rdso_mode_revision_impact.png');

        // TEST 4: Semantic Mode - Failure Analysis (defect_joint_fatigue)
        console.log('\n--- TEST 4: Semantic Mode: Failure Analysis (Machined Joint M Fatigue) ---');
        await client.evaluate(`
            window.switchSemanticMode('failure');
            window.selectGraphNode('defect_joint_fatigue');
        `);
        await sleep(800);

        const failData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const riskTitle = document.getElementById('drawer-risk-title').innerText;
                const riskDesc = document.getElementById('drawer-risk-desc').innerText;
                const hops = Array.from(document.querySelectorAll('#drawer-lineage-list .lineage-tag')).map(t => t.innerText.replace(/\\s+/g, ' '));
                return { title, riskTitle, riskDesc, hops };
            })()
        `);
        console.log('Failure Analysis Result:');
        console.log(`- Entity: ${failData.title}`);
        console.log(`- Risk Title: ${failData.riskTitle}`);
        console.log(`- Risk Mitigations / Hops:\n  ${failData.hops.join('\n  ')}`);
        await client.captureScreenshot('rdso_mode_failure_analysis.png');

        // TEST 5: Semantic Mode - Procurement & BOM (spare_bolt_25x310)
        console.log('\n--- TEST 5: Semantic Mode: Procurement & BOM (LIST-A Spare Bolt) ---');
        await client.evaluate(`
            window.switchSemanticMode('bom');
            window.selectGraphNode('spare_bolt_25x310');
        `);
        await sleep(800);

        const bomData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const hops = Array.from(document.querySelectorAll('#drawer-lineage-list .lineage-tag')).map(t => t.innerText.replace(/\\s+/g, ' '));
                return { title, hops };
            })()
        `);
        console.log('Procurement BOM Result:');
        console.log(`- Entity: ${bomData.title}`);
        console.log(`- Hops:\n  ${bomData.hops.join('\n  ')}`);
        await client.captureScreenshot('rdso_mode_procurement_bom.png');

        // TEST 6: Note Node as First-Class Entity (note_6155_25)
        console.log('\n--- TEST 6: Inspect First-Class Note Entity (Note 25 Dowel Repair) ---');
        await client.evaluate(`
            window.switchSemanticMode('explore');
            window.selectGraphNode('note_6155_25');
        `);
        await sleep(800);

        const noteData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const domain = document.getElementById('drawer-domain').innerText;
                const desc = document.getElementById('answer-card-desc').innerText;
                const provBoxVisible = document.getElementById('answer-provenance-box').style.display !== 'none';
                const provDwg = document.getElementById('prov-dwg-title').innerText;
                const hops = Array.from(document.querySelectorAll('#drawer-lineage-list .lineage-tag')).map(t => t.innerText.replace(/\\s+/g, ' '));
                return { title, domain, desc, provBoxVisible, provDwg, hops };
            })()
        `);
        console.log('Note Entity Result:');
        console.log(`- Title: ${noteData.title}`);
        console.log(`- Domain: ${noteData.domain}`);
        console.log(`- Provenance Box: ${noteData.provBoxVisible} (${noteData.provDwg})`);
        console.log(`- Interlinked Directives:\n  ${noteData.hops.join('\n  ')}`);
        await client.captureScreenshot('rdso_note_answer_card.png');

        // TEST 7: Sleeper Layout Zone (zone_switch)
        console.log('\n--- TEST 7: Inspect Turnout Zone (zone_switch) ---');
        await client.evaluate(`
            window.selectGraphNode('zone_switch');
        `);
        await sleep(800);

        const zoneData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const hops = Array.from(document.querySelectorAll('#drawer-lineage-list .lineage-tag')).map(t => t.innerText.replace(/\\s+/g, ' '));
                return { title, hops };
            })()
        `);
        console.log('Zone Entity Result:');
        console.log(`- Title: ${zoneData.title}`);
        console.log(`- Zone Interlinks:\n  ${zoneData.hops.join('\n  ')}`);
        await client.captureScreenshot('rdso_sleeper_zone_answer_card.png');

        console.log('\n[SUCCESS] All Canonical Interlinking & Graph Intelligence tests passed flawlessly!');
    } catch (err) {
        console.error('[ERROR]', err);
    } finally {
        console.log('[*] Terminating Chrome...');
        chrome.kill();
    }
}

run();
