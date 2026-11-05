// Saves clone screenshots into replica/clone-screens/ (for replica-diff).  node tests/shots.mjs
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'replica/clone-screens'); mkdirSync(OUT, { recursive: true });
const BASE = process.env.BASE || 'http://127.0.0.1:8765';
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9334;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'shots-'))}`, 'about:blank'], { stdio: 'ignore' });
let ws, id = 0; const pend = new Map();
for (let i = 0; i < 50 && !ws; i++) {
  try {
    const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
    ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; });
    ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); } };
  } catch { ws = null; await sleep(200); }
}
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = (expression) => send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });

async function shot(name, path, w, h, { full = true, before } = {}) {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w < 700 });
  await send('Page.navigate', { url: BASE + path });
  for (let i = 0; i < 100; i++) { await sleep(100); if ((await ev('document.readyState')).result.result.value === 'complete') break; }
  await sleep(400);
  // lazy images: scroll through once so every picture is loaded before the capture
  await ev('(async()=>{document.querySelectorAll("img").forEach(i=>{i.loading="eager"});const h=document.documentElement.scrollHeight;for(let y=0;y<h;y+=300){scrollTo({top:y,behavior:"instant"});await new Promise(r=>setTimeout(r,100))}await Promise.all([...document.images].map(i=>i.complete?1:new Promise(r=>{i.onload=i.onerror=r})));scrollTo({top:0,behavior:"instant"})})()');
  await sleep(500);
  if (before) { await ev(before); await sleep(300); }
  let clip;
  if (full) {
    const m = await send('Page.getLayoutMetrics'); const c = m.result.cssContentSize || m.result.contentSize;
    clip = { x: 0, y: 0, width: w, height: Math.min(Math.ceil(c.height), 6000), scale: 1 };
  }
  const r = await send('Page.captureScreenshot', { format: 'png', ...(clip ? { clip, captureBeyondViewport: true } : {}) });
  writeFileSync(join(OUT, name + '.png'), Buffer.from(r.result.data, 'base64')); console.log('saved', name);
}

const pages = [['S01-home', '/'], ['S02-portfolio', '/portfolio/'], ['S03-grill-station', '/grill-station/'], ['S04-grill-zona', '/grill-zona/'], ['S05-portable', '/grill-na-kolesah/'], ['S06-kitchen', '/kuhni-nerjaveika/'], ['S07-tub', '/kupeli/'], ['S08-blog', '/blog/'], ['S09-partner', '/partner/'], ['S10-contact', '/contact/']];
for (const [n, p] of pages) await shot(n + '-desktop', p, 1440, 900);
for (const [n, p] of pages.slice(0, 3)) await shot(n + '-mobile', p, 390, 844);
await shot('S01-home-mobile-fold', '/', 390, 844, { full: false });
await shot('S11-lead-modal-desktop', '/grill-station/', 1440, 900, { full: false, before: 'document.querySelector(".pcard .btn").click()' });
await shot('S11-lead-modal-mobile', '/', 390, 844, { full: false, before: 'document.querySelector(".hero [data-lead-open]").click()' });
await shot('S11-lead-modal-error-desktop', '/', 1440, 900, { full: false, before: 'document.querySelector(".hero [data-lead-open]").click(); setTimeout(()=>document.querySelector("#lead button[type=submit]").click(),100)' });
ws.close(); chrome.kill();
