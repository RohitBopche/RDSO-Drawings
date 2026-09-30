// Shared browser-test environment: portable Chrome discovery, flags and artifact dir.
//   CHROME_PATH          explicit browser binary
//   RDSO_ARTIFACT_DIR    where screenshots go (default: OS temp dir, so runs never dirty the repo)
//   RDSO_HEADLESS=0      show the browser window (default headless)
const fs = require('fs');
const os = require('os');
const path = require('path');

function findChrome() {
    if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
    const candidates = [
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe'),
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium', '/usr/bin/chromium-browser'
    ];
    const pw = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
    try {
        for (const d of fs.readdirSync(pw)) {
            if (/^chromium-\d+$/.test(d)) {
                for (const sub of ['chrome-linux/chrome', 'chrome-linux64/chrome']) candidates.push(path.join(pw, d, sub));
            }
        }
    } catch (e) { /* no playwright browsers */ }
    return candidates.find(p => p && fs.existsSync(p)) || candidates[0];
}

const headless = process.env.RDSO_HEADLESS !== '0';
const chromeFlags = [
    ...(headless ? ['--headless=new'] : []),
    '--allow-file-access-from-files',
    '--disable-gpu-sandbox',
    '--enable-unsafe-swiftshader',
    '--ignore-gpu-blocklist',
    '--use-angle=swiftshader',
    ...(process.platform === 'linux' ? ['--no-sandbox'] : [])
];

const artifactDir = process.env.RDSO_ARTIFACT_DIR || path.join(os.tmpdir(), 'rdso-artifacts');
try { fs.mkdirSync(artifactDir, { recursive: true }); } catch (e) { /* ignore */ }

// Poll the DevTools HTTP endpoint instead of sleeping a fixed time (Chrome start-up varies a lot).
async function waitForDevtools(port, timeoutMs = 30000) {
    const http = require('http');
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        const ok = await new Promise(resolve => {
            http.get(`http://127.0.0.1:${port}/json/version`, res => { res.resume(); resolve(res.statusCode === 200); })
                .on('error', () => resolve(false));
        });
        if (ok) return;
        await new Promise(r => setTimeout(r, 250));
    }
    throw new Error(`Chrome DevTools not reachable on port ${port} after ${timeoutMs} ms`);
}

// A fresh profile directory per run: a crashed earlier run must not leave a lock that stops Chrome starting.
function freshProfile(name) {
    return fs.mkdtempSync(path.join(os.tmpdir(), `${name}-`));
}

module.exports = { freshProfile, waitForDevtools, chromePath: findChrome(), chromeFlags, artifactDir, headless };
