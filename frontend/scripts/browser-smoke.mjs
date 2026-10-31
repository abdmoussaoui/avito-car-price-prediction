// Optional browser regression check. Requires Node 22+, both app servers and
// headless Chrome with --remote-debugging-port=9225 and a separate profile.
// Run from frontend: node scripts/browser-smoke.mjs
import { writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const targets = await (await fetch('http://127.0.0.1:9225/json')).json();
const target = targets.find(item => item.type === 'page');
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => ws.addEventListener('open', resolve, { once: true }));
let sequence = 0;
const pending = new Map();
const exceptions = [];
let heldRequest;
ws.addEventListener('message', event => {
  const message = JSON.parse(String(event.data));
  if (message.id) {
    const handlers = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) handlers.reject(new Error(JSON.stringify(message.error)));
    else handlers.resolve(message.result);
  }
  if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params.exceptionDetails);
  if (message.method === 'Fetch.requestPaused') heldRequest = message.params.requestId;
});
function cdp(method, params = {}) {
  const id = ++sequence;
  return new Promise((resolve, reject) => { pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
}
async function evaluate(expression) {
  const value = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (value.exceptionDetails) throw new Error(JSON.stringify(value.exceptionDetails));
  return value.result.value;
}
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(expression) {
  for (let i = 0; i < 100; i++) { if (await evaluate(expression)) return; await sleep(100); }
  throw new Error(`Timed out: ${expression}`);
}
function assert(value, message) { if (!value) throw new Error(message); }
async function set(name, value) {
  await evaluate(`(() => { const el = document.getElementById(${JSON.stringify(name)}); const prototype = el.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype; Object.getOwnPropertyDescriptor(prototype, 'value').set.call(el, ${JSON.stringify(String(value))}); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); })()`);
  await sleep(70);
}
await cdp('Runtime.enable');
await cdp('Page.enable');
await cdp('Network.enable');
await cdp('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
await cdp('Page.navigate', { url: 'http://localhost:5173' });
await until(`document.querySelector('#marque option[value="Renault"]') !== null`);
await until(`document.querySelector('.automotive-image img').complete && document.querySelector('.automotive-image img').naturalWidth > 0`);
await evaluate('document.fonts.ready');
await sleep(500);
let shot = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
await writeFile(join(tmpdir(), 'autovaleur-desktop.png'), Buffer.from(shot.data, 'base64'));
await evaluate(`document.querySelector('button[type="submit"]').click()`);
assert(await evaluate(`document.querySelectorAll('[aria-invalid="true"]').length === 10`), 'Missing inline field errors');
assert(await evaluate(`document.activeElement.id === 'marque'`), 'First error did not receive focus');
await set('marque', 'Renault');
await set('modele', 'Clio');
await set('anneeModele', 2022);
await set('localisation', 'Rabat');
await set('kilometrage', 45000);
await set('puissanceFiscale', 6);
await set('typeDeCarburant', 'Essence');
await set('boiteDeVitesses', 'Automatique');
await set('etat', 'Bon');
await set('nombreDePortes', 5);
await evaluate(`document.querySelector('.equipment-disclosure').open = true`);
for (const equipment of ['ABS', 'Airbags', 'Climatisation']) {
  await evaluate(`Array.from(document.querySelectorAll('.equipment-chip')).find(el => el.textContent.trim() === ${JSON.stringify(equipment)}).click()`);
  await sleep(60);
}
await cdp('Network.setBlockedURLs', { urls: ['*/predict'] });
await evaluate(`document.querySelector('button[type="submit"]').click()`);
await until(`Boolean(document.querySelector('.error-banner')) && !document.querySelector('fieldset').disabled`);
assert(await evaluate(`document.getElementById('modele').value === 'Clio' && document.getElementById('kilometrage').value === '45000'`), 'Failed request cleared the vehicle');
await cdp('Network.setBlockedURLs', { urls: [] });
await cdp('Fetch.enable', { patterns: [{ urlPattern: '*/predict', requestStage: 'Request' }] });
await evaluate(`document.querySelector('button[type="submit"]').click()`);
for (let i = 0; i < 50 && !heldRequest; i++) await sleep(100);
assert(Boolean(heldRequest), 'Prediction request not sent');
assert(await evaluate(`Boolean(document.querySelector('.loading-state')) && document.querySelector('fieldset').disabled`), 'Loading state not visible');
await cdp('Fetch.continueRequest', { requestId: heldRequest });
await cdp('Fetch.disable');
await until(`document.querySelector('.result-price') !== null`);
const displayedPrice = await evaluate(`document.querySelector('.result-price').textContent.replace(/[^0-9]/g, '')`);
assert(displayedPrice === '124241', `UI prediction differs from real baseline: ${displayedPrice}`);
assert(await evaluate(`document.querySelectorAll('iframe').length === 0`), 'Unexpected embedded page');
for (const width of [1440, 1024, 768, 390, 320]) {
  await cdp('Emulation.setDeviceMetricsOverride', { width, height: 1000, deviceScaleFactor: 1, mobile: width < 640 });
  await sleep(150);
  assert(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'), `Horizontal overflow at ${width}px`);
  console.log(`Layout OK at ${width}px`);
}
await cdp('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
await evaluate(`document.querySelector('.story-panel').scrollIntoView({ block: 'start', behavior: 'instant' })`);
await sleep(200);
shot = await cdp('Page.captureScreenshot', { format: 'png' });
await writeFile(join(tmpdir(), 'autovaleur-mobile-result.png'), Buffer.from(shot.data, 'base64'));
await evaluate(`document.querySelector('.reset-button').click()`);
assert(await evaluate(`document.getElementById('marque').value === '' && !document.querySelector('.result-price')`), 'Reset did not clear the prediction');
await set('marque', 'Renault'); await set('modele', 'Clio'); await set('marque', 'Dacia');
assert(await evaluate(`document.getElementById('modele').value === ''`), 'Brand change did not reset the model');
await cdp('Network.setBlockedURLs', { urls: ['*/options'] });
await cdp('Page.reload', { ignoreCache: true });
await until(`Boolean(document.querySelector('.options-state .secondary-button'))`);
await cdp('Network.setBlockedURLs', { urls: [] });
await evaluate(`document.querySelector('.options-state .secondary-button').click()`);
await until(`Boolean(document.getElementById('marque'))`);
assert(exceptions.length === 0, `Browser exceptions: ${JSON.stringify(exceptions)}`);
console.log('PASS: inline validation, focus, real prediction, loading, reset, model selection, failed prediction retry, connection failure and retry.');
console.log(`Screenshots: ${join(tmpdir(), 'autovaleur-desktop.png')}, ${join(tmpdir(), 'autovaleur-mobile-result.png')}`);
ws.close();
