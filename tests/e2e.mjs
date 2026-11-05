// End-to-end checks. Needs: node >= 22, Google Chrome, and `python3 server.py 8765` running.
//   node tests/e2e.mjs
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const BASE = process.env.BASE || 'http://127.0.0.1:8765';
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const PORT = 9333;
const LEADS = join(ROOT, 'leads.jsonl');
const leadCount = () => (existsSync(LEADS) ? readFileSync(LEADS, 'utf8').trim().split('\n').filter(Boolean).length : 0);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn(CHROME, ['--headless=new', '--disable-gpu', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'e2e-'))}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
let ws, id = 0; const pend = new Map(); const consoleErrors = [];
async function connect() {
  for (let i = 0; i < 50; i++) {
    try {
      const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
      ws = new WebSocket(t.webSocketDebuggerUrl);
      await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
      ws.onmessage = (m) => {
        const d = JSON.parse(m.data);
        if (d.id && pend.has(d.id)) { pend.get(d.id)(d); pend.delete(d.id); }
        if (d.method === 'Runtime.exceptionThrown') consoleErrors.push(d.params.exceptionDetails.text + ' ' + (d.params.exceptionDetails.exception?.description || ''));
        if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') consoleErrors.push(d.params.args.map((a) => a.value || a.description).join(' '));
      };
      return;
    } catch { await sleep(200); }
  }
  throw new Error('cannot connect to Chrome');
}
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => { const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }); if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.text + ' ' + (r.result.exceptionDetails.exception?.description || '')); return r.result.result.value; };
async function go(path, w = 1440, h = 900) {
  await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w < 700 });
  await send('Page.navigate', { url: BASE + path });
  for (let i = 0; i < 100; i++) { await sleep(100); if (await ev('document.readyState') === 'complete') break; }
  await sleep(250);
}
const click = (sel, nth = 0) => ev(`(()=>{const e=document.querySelectorAll(${JSON.stringify(sel)})[${nth}]; if(!e) throw new Error('no ${sel}'); e.click(); return true})()`);
const setVal = (sel, v, scope = 'document') => ev(`(()=>{const e=${scope}.querySelector(${JSON.stringify(sel)}); e.focus(); e.value=${JSON.stringify(v)}; e.dispatchEvent(new Event('input',{bubbles:true})); return e.value})()`);

let pass = 0, fail = 0; const failures = [];
const t = async (name, fn) => { try { const r = await fn(); if (r === false) throw new Error('returned false'); pass++; console.log('  ok  ', name); } catch (e) { fail++; failures.push(name); console.log('  FAIL', name, '-', e.message); } };

await connect();
await send('Runtime.enable'); await send('Page.enable'); await send('Network.enable');

console.log('# desktop 1440');
await go('/');
await t('home: title + h1', async () => (await ev('document.title')).includes('ЖАРСТАЛЬ') && (await ev('document.querySelectorAll("h1").length')) === 1);
await t('home: models dropdown closed at load', async () => (await ev('getComputedStyle(document.querySelector(".nav .sub")).display')) === 'none');
await t('home: dropdown opens on click, aria-expanded', async () => { await click('.nav__btn'); return (await ev('getComputedStyle(document.querySelector(".nav .sub")).display')) === 'flex' && (await ev('document.querySelector(".nav__btn").getAttribute("aria-expanded")')) === 'true'; });
await t('home: dropdown has 5 links to category pages', async () => (await ev('document.querySelectorAll(".nav .sub a").length')) === 5);
await t('home: hero CTA opens lead dialog', async () => { await click('.hero [data-lead-open]'); return await ev('document.getElementById("lead").open'); });
await t('lead: empty submit -> phone error, no request', async () => { const before = leadCount(); await click('#lead button[type=submit]'); await sleep(150); return (await ev('document.querySelector("#lead .err").textContent')).includes('телефон') && leadCount() === before; });
await t('lead: phone is masked', async () => (await setVal('#lead input[name=phone]', '89001234567')) === '+7 (900) 123-45-67');
await t('lead: no consent -> consent error', async () => { await click('#lead button[type=submit]'); await sleep(150); return (await ev('document.querySelector("#lead .err").textContent')).includes('согласие'); });
await t('lead: valid submit shows success and stores 1 lead', async () => {
  const before = leadCount();
  await ev('document.querySelector("#lead input[name=consent]").click()');
  await click('#lead button[type=submit]'); await sleep(600);
  const okShown = await ev('!document.querySelector("#lead .ok").hidden');
  return okShown && leadCount() === before + 1;
});
await t('lead: stored record has normalised phone + source', async () => { const last = JSON.parse(readFileSync(LEADS, 'utf8').trim().split('\n').pop()); return last.phone === '+79001234567' && last.source === 'calc' && last.consent === true; });
await t('dialog: Escape closes', async () => { await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 }); await sleep(150); return !(await ev('document.getElementById("lead").open')); });
await t('lead: honeypot filled -> fake ok, nothing stored', async () => {
  const before = leadCount();
  await click('.hero [data-lead-open]');
  await setVal('#lead input[name=phone]', '89001112233');
  await ev('document.querySelector("#lead input[name=website]").value="http://spam"; document.querySelector("#lead input[name=consent]").click()');
  await click('#lead button[type=submit]'); await sleep(500);
  return leadCount() === before;
});
await t('order/calc mode: e-mail field is NOT rendered', async () => { await go('/'); await click('.hero [data-lead-open]'); await sleep(100); return (await ev('getComputedStyle(document.querySelector("#lead [data-catalog-only]")).display')) === 'none'; });
await t('catalog mode: e-mail field IS rendered + catalog note after send', async () => {
  await go('/'); await click('[data-lead-open=catalog]'); await sleep(100);
  const shown = (await ev('getComputedStyle(document.querySelector("#lead [data-catalog-only]")).display')) !== 'none';
  await setVal('#lead input[name=phone]', '89007770011'); await setVal('#lead input[name=email]', 'bad');
  await ev('document.querySelector("#lead input[name=consent]").click()'); await click('#lead button[type=submit]'); await sleep(200);
  const badEmailErr = (await ev('document.querySelector("#lead .err").textContent')).includes('e-mail');
  await setVal('#lead input[name=email]', 'a@b.co'); const before = leadCount();
  await click('#lead button[type=submit]'); await sleep(600);
  return shown && badEmailErr && leadCount() === before + 1 && (await ev('getComputedStyle(document.querySelector("#lead .ok__cat")).display')) !== 'none';
});
await t('consult form on page submits inline', async () => {
  await go('/'); const before = leadCount();
  await setVal('.consult__form input[name=phone]', '+79005550011');
  await ev('document.querySelector(".consult__form input[name=consent]").click()');
  await click('.consult__form button[type=submit]'); await sleep(600);
  return leadCount() === before + 1 && (await ev('!document.querySelector(".ok--inline").hidden'));
});
await t('gallery: photo tile opens viewer with image', async () => { await go('/'); await click('[data-view-img]'); await sleep(100); return (await ev('document.getElementById("viewer").open')) && (await ev('!!document.querySelector("#viewer-body img")')); });
await t('gallery: video tile without url shows the not-connected note', async () => { await go('/'); await click('[data-view-video]'); await sleep(100); return (await ev('document.querySelector("#viewer-body").textContent')).includes('не подключено'); });
await t('dock: collapse toggles', async () => { await go('/'); await click('.dock__t'); return await ev('document.querySelector(".dock").classList.contains("is-min")'); });

console.log('# catalog page');
await go('/grill-station/');
await t('station: 6 product cards, each with price + order button', async () => (await ev('document.querySelectorAll(".pcard").length')) === 6 && (await ev('document.querySelectorAll(".pcard .price b").length')) === 6);
await t('station: accordion opens', async () => { await click('.acc summary'); return await ev('document.querySelector(".acc").open'); });
await t('station: slider next/thumb switch active slide', async () => { await click('.slider__nav--r'); const a = await ev('document.querySelectorAll(".pcard")[0].querySelector(".slide.is-on").dataset.i'); await click('.thumb', 0); const b = await ev('document.querySelectorAll(".pcard")[0].querySelector(".slide.is-on").dataset.i'); return a === '1' && b === '0'; });
await t('station: Заказать prefills product', async () => { await click('.pcard .btn', 0); await sleep(100); return (await ev('document.getElementById("lead-prod").textContent')).includes('Атлас Мини с бутылочницей'); });
await t('price formatted with nbsp grouping and ruble sign', async () => /^640 000 ₽$/.test(await ev('document.querySelector(".price b").textContent')));
for (const [p, n] of [['/grill-zona/', 4], ['/grill-na-kolesah/', 4], ['/kuhni-nerjaveika/', 7], ['/kupeli/', 6]]) await t(`${p}: ${n} cards`, async () => { await go(p); return (await ev('document.querySelectorAll(".pcard").length')) === n; });
await t('zone: 7 module cards', async () => { await go('/grill-zona/'); return (await ev('document.querySelectorAll(".mcard").length')) === 7; });
await t('portfolio: 12 projects, 3 videos', async () => { await go('/portfolio/'); return (await ev('document.querySelectorAll(".pf").length')) === 12 && (await ev('document.querySelectorAll(".pf [data-view-video]").length')) === 3; });
await t('blog: 9 videos', async () => { await go('/blog/'); return (await ev('document.querySelectorAll(".vid").length')) === 9; });

console.log('# photos');
for (const p of ['/', '/grill-station/', '/grill-zona/', '/grill-na-kolesah/', '/kuhni-nerjaveika/', '/kupeli/', '/portfolio/', '/blog/'])
  await t(`photos: all load, content images have alt ${p}`, async () => {
    await go(p);
    const r = JSON.parse(await ev(`(async()=>{document.querySelectorAll('img').forEach(i=>{i.loading='eager'});const h=document.documentElement.scrollHeight;for(let y=0;y<h;y+=400){scrollTo({top:y,behavior:'instant'});await new Promise(r=>setTimeout(r,80))}
      await Promise.all([...document.images].map(i=>i.complete?1:new Promise(r=>{i.onload=i.onerror=r})));
      const all=[...document.images];
      return JSON.stringify({n:all.length,broken:all.filter(i=>i.naturalWidth===0).map(i=>i.src),noAlt:all.filter(i=>i.closest('.slide,.tile,.pf__media,.vid__media,.show,.hero,.chero,.mcard')&&!i.alt).length})})()`));
    if (r.broken.length) throw new Error('broken: ' + r.broken.join(','));
    if (r.noAlt) throw new Error(r.noAlt + ' content images without alt');
    return r.n > 3;
  });
await t('credits page: every photo has a source link', async () => { await go('/credits/'); const n = await ev('document.querySelectorAll(".credits li").length'); const bad = await ev('[...document.querySelectorAll(".credits li")].filter(l=>!l.querySelector("a[href^=https]")).length'); return n >= 15 && bad === 0; });
await t('clean room: no reference to the original domain in any page', async () => {
  const { readdirSync, statSync } = await import('node:fs'); const hits = [];
  const walk = (d) => { for (const f of readdirSync(d)) { const q = join(d, f); if (statSync(q).isDirectory()) walk(q); else if (/\.(html|css|js|xml|txt|svg)$/.test(f) && /bestmangal/i.test(readFileSync(q, 'utf8'))) hits.push(q); } };
  walk(join(ROOT, 'site')); if (hits.length) throw new Error(hits.join(', ')); return true;
});

console.log('# mobile 390');
await go('/', 390, 844);
await t('mobile: burger opens nav', async () => { await click('.burger'); return (await ev('getComputedStyle(document.getElementById("nav")).display')) !== 'none' && (await ev('document.querySelector(".burger").getAttribute("aria-expanded")')) === 'true'; });
for (const p of ['/', '/grill-station/', '/grill-zona/', '/grill-na-kolesah/', '/kuhni-nerjaveika/', '/kupeli/', '/portfolio/', '/blog/', '/partner/', '/contact/', '/privacy/'])
  await t(`mobile: no horizontal overflow ${p}`, async () => { await go(p, 390, 844); return (await ev('document.documentElement.scrollWidth')) <= 391; });

console.log('# console');
await t('no JS errors / console errors', async () => { const own = consoleErrors.filter((e) => !/fonts\.(googleapis|gstatic)|Failed to load resource/.test(e)); if (own.length) throw new Error(own.slice(0, 3).join(' | ')); return true; });

ws.close(); chrome.kill();
console.log(`\n${pass} passed, ${fail} failed`);
if (fail) { console.log('failed:', failures.join('; ')); process.exit(1); }
