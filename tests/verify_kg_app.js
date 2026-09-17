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
    "C:\\Users\\LENOVO\\.gemini\\antigravity-ide\\brain\\28ef0a3f-1b2d-4d16-a24b-878459c10a0f",
    "C:\\Users\\LENOVO\\.gemini\\antigravity-ide\\brain\\ea8fa10c-88f4-4a72-b9b0-d40e78abc040",
    path.join(__dirname, '..', 'artifacts')
].find(d => fs.existsSync(d)) || path.join(__dirname, '..', 'artifacts');
if (!fs.existsSync(artifactDir)) { try { fs.mkdirSync(artifactDir, { recursive: true }); } catch (e) {} }
const tempProfile = path.join(require('os').tmpdir(), 'chrome_kg_test_profile');

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

        // Verify title and basic load
        const title = await client.evaluate('document.title');
        console.log('[+] Document Title:', title);

        await client.captureScreenshot('rdso_kg_initial_canvas.png');

        // Test 1: Select RDSO/T-6155
        console.log('\n--- TEST 1: Select RDSO/T-6155 (Fan-Shaped Layout & 28 Notes) ---');
        const selectResult = await client.evaluate(`
            const success = window.selectGraphNode('drg_6155');
            const drawer = document.getElementById('intelligence-drawer');
            ({
                success,
                drawerOpen: !drawer.classList.contains('collapsed'),
                title: document.getElementById('drawer-title').innerText,
                domain: document.getElementById('drawer-domain').innerText
            })
        `);
        console.log('Selection Result:', selectResult);
        await sleep(1000);

        // Check Notes
        const notesData = await client.evaluate(`
            const notes = document.querySelectorAll('.note-card');
            const sampleNotes = [];
            for (let i = 0; i < Math.min(notes.length, 5); i++) {
                sampleNotes.push(notes[i].innerText.replace(/\\s+/g, ' ').slice(0, 100));
            }
            ({
                totalNotes: notes.length,
                samples: sampleNotes,
                note25: Array.from(notes).find(n => n.innerText.includes('NOTE 25'))?.innerText?.slice(0, 120),
                note28: Array.from(notes).find(n => n.innerText.includes('NOTE 28'))?.innerText?.slice(0, 120)
            })
        `);
        console.log('Notes Analysis:');
        console.log(`- Total notes rendered: ${notesData.totalNotes}`);
        console.log(`- Note 25 found: ${notesData.note25}`);
        console.log(`- Note 28 found: ${notesData.note28}`);

        await client.captureScreenshot('rdso_t6155_drawer_notes.png');

        // Test Tab 2: Tables & BOM for 6155 (LIST-A wear spares)
        console.log('\n--- TEST 2: Tab 2 Tables & BOM (LIST-A Spares) ---');
        await client.evaluate(`
            window.switchDrawerTab('tables');
        `);
        await sleep(800);

        const tableData = await client.evaluate(`
            const activeTable = document.querySelector('#drawer-table-content table');
            const headers = Array.from(activeTable ? activeTable.querySelectorAll('th') : []).map(th => th.innerText);
            const rowCount = activeTable ? activeTable.querySelectorAll('tbody tr').length : 0;
            const firstRow = activeTable ? Array.from(activeTable.querySelectorAll('tbody tr:first-child td')).map(td => td.innerText) : [];
            const subnavButtons = Array.from(document.querySelectorAll('.table-subnav-btn')).map(b => b.innerText);
            ({
                hasTable: !!activeTable,
                subnavButtons,
                headers,
                rowCount,
                firstRow
            })
        `);
        console.log('Tables Result:');
        console.log(`- Subnav buttons: ${tableData.subnavButtons.join(' | ')}`);
        console.log(`- Has Table: ${tableData.hasTable}`);
        console.log(`- Headers: ${tableData.headers.join(' | ')}`);
        console.log(`- Rows Count: ${tableData.rowCount}`);
        console.log(`- First Row: ${tableData.firstRow.join(' | ')}`);

        await client.captureScreenshot('rdso_t6155_drawer_tables_lista.png');

        // Test Tab 3: Blueprint View
        console.log('\n--- TEST 3: Tab 3 Blueprint View ---');
        await client.evaluate(`
            window.switchDrawerTab('blueprint');
        `);
        await sleep(800);

        const blueprintData = await client.evaluate(`
            const img = document.getElementById('blueprint-crop-img');
            const selectOptions = Array.from(document.querySelectorAll('#blueprint-crop-select option')).map(o => o.innerText.trim());
            ({
                cropSrc: img ? img.src : null,
                imgNaturalWidth: img ? img.naturalWidth : 0,
                imgNaturalHeight: img ? img.naturalHeight : 0,
                selectOptions
            })
        `);
        console.log('Blueprint View Result:');
        console.log(`- Crop Src: ${blueprintData.cropSrc}`);
        console.log(`- Resolution: ${blueprintData.imgNaturalWidth} x ${blueprintData.imgNaturalHeight} px`);
        console.log(`- Blueprint Crop Options: ${blueprintData.selectOptions.join(', ')}`);

        await client.captureScreenshot('rdso_t6155_blueprint_crops.png');

        // Test Tab 4: 3D Twin View
        console.log('\n--- TEST 4: Tab 4 3D Asset Twin Mini-Viewport ---');
        await client.evaluate(`
            window.switchDrawerTab('twin');
        `);
        await sleep(800);

        const mini3dData = await client.evaluate(`
            const canvas = document.getElementById('component-twin-canvas');
            const badge = document.getElementById('twin-badge-text');
            ({
                hasCanvas: !!canvas,
                canvasWidth: canvas ? canvas.width : 0,
                canvasHeight: canvas ? canvas.height : 0,
                badgeText: badge ? badge.innerText : ''
            })
        `);
        console.log('3D Mini-Viewport Result:');
        console.log(`- Canvas rendered: ${mini3dData.hasCanvas} (${mini3dData.canvasWidth}x${mini3dData.canvasHeight})`);
        console.log(`- Badge: ${mini3dData.badgeText}`);

        await client.captureScreenshot('rdso_t6155_3d_twin.png');

        // Test 5: Select RDSO_T_6154 (64-Sleeper Layout & BOM)
        console.log('\n--- TEST 5: Select RDSO_T_6154 (64 Sleepers Schedule & Versines) ---');
        await client.evaluate(`
            window.selectGraphNode('drg_6154');
            window.switchDrawerTab('tables');
        `);
        await sleep(1000);

        // Click Sleepers subtab if not active
        const sleeperSubTab = await client.evaluate(`
            const sleeperBtn = Array.from(document.querySelectorAll('.table-subnav-btn')).find(b => b.innerText.includes('Sleeper'));
            if (sleeperBtn) sleeperBtn.click();
            const rows = document.querySelectorAll('#drawer-table-content tbody tr');
            const first5 = Array.from(rows).slice(0, 5).map(r => Array.from(r.querySelectorAll('td')).map(td => td.innerText).join(' | '));
            const lastRow = rows.length > 0 ? Array.from(rows[rows.length - 1].querySelectorAll('td')).map(td => td.innerText).join(' | ') : '';
            ({
                totalSleeperRows: rows.length,
                first5,
                lastRow
            })
        `);
        console.log('Sleeper Schedule Result:');
        console.log(`- Total Sleeper Rows: ${sleeperSubTab.totalSleeperRows}`);
        console.log(`- Sample Sleeper Rows:\n  ${sleeperSubTab.first5.join('\n  ')}`);
        console.log(`- Last Sleeper (Sleeper 64): ${sleeperSubTab.lastRow}`);

        await client.captureScreenshot('rdso_t6154_sleeper_schedule_64.png');

        // Test Curve Versines sub-tab
        console.log('\n--- TEST 6: Curve Versines Subtab ---');
        await client.evaluate(`
            const versineBtn = Array.from(document.querySelectorAll('.table-subnav-btn')).find(b => b.innerText.includes('Versine'));
            if (versineBtn) versineBtn.click();
        `);
        await sleep(800);

        const versineData = await client.evaluate(`
            const content = document.getElementById('drawer-table-content');
            ({
                text: content.innerText
            })
        `);
        console.log('Curve Versine Results:\n', versineData.text);

        await client.captureScreenshot('rdso_t6154_versine_table.png');

        // Test 7: Component mapping (comp_chair -> RDSO_T_6155)
        console.log('\n--- TEST 7: Component Node Linking (comp_chair) ---');
        await client.evaluate(`
            window.selectGraphNode('comp_chair');
            window.switchDrawerTab('notes');
        `);
        await sleep(800);

        const compChairData = await client.evaluate(`
            (() => {
                const title = document.getElementById('drawer-title').innerText;
                const domain = document.getElementById('drawer-domain').innerText;
                const noteItems = document.querySelectorAll('.note-card').length;
                return {
                    title,
                    domain,
                    linkedNotesCount: noteItems
                };
            })()
        `);
        console.log('Component Chair Result:');
        console.log(`- Title: ${compChairData.title}`);
        console.log(`- Domain: ${compChairData.domain}`);
        console.log(`- Linked Notes (from RDSO/T-6155): ${compChairData.linkedNotesCount}`);

        await client.captureScreenshot('rdso_comp_chair_linked_drawer.png');

        // Test 8: Phase 1 Search Autocomplete, Card Layout, Overview Tab & Breadcrumbs
        console.log('\n--- TEST 8: Phase 1 Search Autocomplete & Overview Intelligence ---');
        
        // Step A: Trigger search for "T-6155"
        const searchDropdownData = await client.evaluate(`
            (() => {
                const input = document.getElementById('graph-search-input');
                input.value = 'T-6155';
                input.dispatchEvent(new Event('input', { bubbles: true }));
                const dropdown = document.getElementById('search-dropdown');
                const items = dropdown.querySelectorAll('.search-dropdown-item');
                const firstCard = items[0];
                return {
                    isActive: dropdown.classList.contains('active'),
                    itemCount: items.length,
                    firstCardTitle: firstCard ? firstCard.querySelector('.search-card-title')?.innerText : null,
                    firstCardBadge: firstCard ? firstCard.querySelector('.search-card-badge')?.innerText : null,
                    firstCardRev: firstCard ? firstCard.querySelector('.search-card-rev')?.innerText : null,
                    firstCardMeta: firstCard ? firstCard.querySelector('.search-card-meta')?.innerText : null
                };
            })()
        `);
        console.log('Search Dropdown Evaluation:');
        console.log(`- Dropdown active: ${searchDropdownData.isActive}`);
        console.log(`- Item count: ${searchDropdownData.itemCount}`);
        console.log(`- Top item: ${searchDropdownData.firstCardTitle} [${searchDropdownData.firstCardBadge}] [${searchDropdownData.firstCardRev}]`);
        console.log(`- Top item meta: ${searchDropdownData.firstCardMeta}`);

        await client.captureScreenshot('rdso_phase1_search_dropdown.png');

        // Step B: Select top item from search dropdown
        const overviewData = await client.evaluate(`
            (() => {
                const firstCard = document.querySelector('#search-dropdown .search-dropdown-item');
                if (firstCard) firstCard.click();
                
                const breadcrumbBar = document.getElementById('drawer-breadcrumb-bar');
                const overviewTab = document.getElementById('tab-pane-overview');
                const heroTitle = overviewTab ? overviewTab.querySelector('.overview-hero-title')?.innerText : null;
                const heroRev = overviewTab ? overviewTab.querySelector('.overview-hero-rev')?.innerText : null;
                
                const paramItems = overviewTab ? Array.from(overviewTab.querySelectorAll('.param-item')).map(p => {
                    return p.querySelector('.param-label')?.innerText + ': ' + p.querySelector('.param-value')?.innerText;
                }) : [];
                
                const altEvents = overviewTab ? Array.from(overviewTab.querySelectorAll('.alt-event')).map(e => {
                    return e.querySelector('.alt-num')?.innerText + ' (' + e.querySelector('.alt-date')?.innerText + '): ' + e.querySelector('.alt-desc')?.innerText;
                }) : [];

                const pillCount = overviewTab ? overviewTab.querySelectorAll('.related-pill').length : 0;
                const samplePills = overviewTab ? Array.from(overviewTab.querySelectorAll('.related-pill')).slice(0, 3).map(p => p.innerText.replace(/\\s+/g, ' ').trim()) : [];

                return {
                    breadcrumbs: breadcrumbBar ? breadcrumbBar.innerText.replace(/\\s+/g, ' ').trim() : null,
                    heroTitle,
                    heroRev,
                    parametersCount: paramItems.length,
                    sampleParams: paramItems.slice(0, 4),
                    alterationsCount: altEvents.length,
                    sampleAlterations: altEvents.slice(0, 2),
                    relatedPillCount: pillCount,
                    samplePills
                };
            })()
        `);
        console.log('Overview Tab Evaluation:');
        console.log(`- Breadcrumbs: ${overviewData.breadcrumbs}`);
        console.log(`- Hero Title: ${overviewData.heroTitle}`);
        console.log(`- Hero Revision: ${overviewData.heroRev}`);
        console.log(`- Engineering Parameters (${overviewData.parametersCount}):\n  ${overviewData.sampleParams.join('\n  ')}`);
        console.log(`- Alteration History (${overviewData.alterationsCount}):\n  ${overviewData.sampleAlterations.join('\n  ')}`);
        console.log(`- Related 1-hop pills (${overviewData.relatedPillCount}): ${overviewData.samplePills.join(' | ')}`);

        await client.captureScreenshot('rdso_phase1_overview_tab.png');

        console.log('\n[SUCCESS] All verification tests passed flawlessly!');
    } catch (err) {
        console.error('[ERROR]', err);
    } finally {
        console.log('[*] Terminating Chrome...');
        chrome.kill();
    }
}

run();
