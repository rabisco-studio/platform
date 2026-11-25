// Spike (c): orquestra o teste de SQLite WASM + OPFS no Chrome instalado (puppeteer-core).
// Uso: node run.mjs [N_TILES]   (padrão 600 tiles de 64 KiB, ~37 MiB)
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const here = path.dirname(fileURLToPath(import.meta.url));
const DDL = path.resolve(here, '../../../contracts/document-format/rbsc-schema-v1.sql');
const CHROME = process.env.CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const N = Number(process.argv[2] || 600);

const PAGE = `<!doctype html><meta charset="utf-8"><script type="module">
const p = new URLSearchParams(location.search);
const ddl = await (await fetch('/ddl.sql')).text();
const w = new Worker('/worker.js', { type: 'module' });
w.onmessage = (e) => { window.__out = e.data; };
w.postMessage({ phase: p.get('phase'), vfs: p.get('vfs'), n: Number(p.get('n')), ddl });
</script>`;

function serve(isolated) {
  const srv = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x');
    const send = (type, body) => {
      const h = { 'Content-Type': type };
      if (isolated) { h['Cross-Origin-Opener-Policy'] = 'same-origin'; h['Cross-Origin-Embedder-Policy'] = 'require-corp'; }
      res.writeHead(200, h); res.end(body);
    };
    if (u.pathname === '/page.html') return send('text/html', PAGE);
    if (u.pathname === '/ddl.sql') return send('text/plain', fs.readFileSync(DDL));
    const f = path.join(here, decodeURIComponent(u.pathname));
    if (f.startsWith(here) && fs.existsSync(f) && fs.statSync(f).isFile()) {
      const type = f.endsWith('.wasm') ? 'application/wasm' : f.endsWith('.js') || f.endsWith('.mjs') ? 'text/javascript' : 'application/octet-stream';
      return send(type, fs.readFileSync(f));
    }
    res.writeHead(404); res.end('404');
  });
  return new Promise((r) => srv.listen(0, '127.0.0.1', () => r(srv)));
}

async function phase(userDir, port, vfs, ph) {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, userDataDir: userDir, args: ['--no-first-run'] });
  try {
    const page = await browser.newPage();
    page.on('pageerror', (e) => console.log('pageerror:', e.message));
    await page.goto(`http://127.0.0.1:${port}/page.html?phase=${ph}&vfs=${vfs}&n=${N}`);
    await page.waitForFunction('window.__out', { timeout: 120000 });
    return await page.evaluate('window.__out');
  } finally {
    await browser.close();
  }
}

const results = [];
const iso = await serve(true);
const plain = await serve(false);
for (const [vfs, srv, label] of [['opfs', iso, 'VFS opfs (COOP/COEP)'], ['sah', plain, 'VFS opfs-sahpool (sem COOP/COEP)']]) {
  const userDir = fs.mkdtempSync(path.join(os.tmpdir(), 'spike-c-chrome-'));
  const port = srv.address().port;
  const w = await phase(userDir, port, vfs, 'write');
  const r = await phase(userDir, port, vfs, 'read'); // navegador fechado e reaberto: prova persistência
  results.push({ label, write: w, read: r });
}
console.log(JSON.stringify(results, null, 2));
iso.close(); plain.close();
process.exit(0);
