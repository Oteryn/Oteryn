#!/usr/bin/env node
// Isolated public observations only: no credentials, submissions or product repair.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { SOURCE_SHA, SOURCE_TREE, SOURCE_BINDINGS, ORIGIN, PLAYWRIGHT, ROUTES, SIZES,
  requestAllowed, caseCriteria, evaluateReport } from './public-surface-contract.mjs';
const [rootArg, outputArg] = process.argv.slice(2);
if (process.env.OTERYN_AUDIT185_PUBLIC_UI !== '1' || !rootArg || !outputArg) throw Error('explicit isolated-public-UI consent, source and new output required');
const root = fs.realpathSync(rootArg), out = path.resolve(outputArg);
if (fs.existsSync(out) || out === root || out.startsWith(root + path.sep)) throw Error('new output outside provider required');
for (const [args, expected] of [[['rev-parse', 'HEAD'], SOURCE_SHA], [['rev-parse', 'HEAD^{tree}'], SOURCE_TREE], [['status', '--porcelain', '--untracked-files=no'], '']]) {
  if (execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim() !== expected) throw Error('wrong or dirty source');
}
for (const [name, expected] of Object.entries(SOURCE_BINDINGS)) {
  const bytes = fs.readFileSync(path.join(root, name));
  const hash = crypto.createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
  if (hash !== expected) throw Error('fixture/contract/lock source mismatch: ' + name);
}
const require = createRequire(path.join(root, 'scripts/acceptance/package.json'));
const { chromium } = require('@playwright/test');
if (require('@playwright/test/package.json').version !== PLAYWRIGHT) throw Error('unexpected Playwright dependency');
fs.mkdirSync(out, { recursive: true });
const report = { schema_version: 2, source_sha: SOURCE_SHA, source_tree: SOURCE_TREE, source_bindings: SOURCE_BINDINGS,
  playwright: PLAYWRIGHT, scope: 'Anonymous English synthetic fixture; Canary deliberately unavailable; no authenticated/admin/payment/game/production acceptance',
  cases: [], keyboard: [], no_javascript: null };
const browser = await chromium.launch({ headless: true });
report.browser = browser.version();
const save = () => fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(report, null, 2) + '\n');
function safeURL(raw) { try { const u = new URL(raw); return u.origin + u.pathname; } catch { return 'invalid-url'; } }
async function restrict(context, problems) {
  await context.route('**/*', route => {
    const r = route.request();
    if (requestAllowed(r.method(), r.url())) return route.continue();
    problems.push({ kind: 'blocked-request', method: r.method(), url: safeURL(r.url()) });
    return route.abort();
  });
}
try {
  for (const [width, height] of SIZES) {
    const context = await browser.newContext({ viewport: { width, height }, locale: 'en-US', reducedMotion: 'reduce' });
    const problems = []; await restrict(context, problems);
    const page = await context.newPage(); page.setDefaultTimeout(12000); page.setDefaultNavigationTimeout(15000);
    page.on('pageerror', e => problems.push({ kind: 'pageerror', message: e.message.slice(0, 300) }));
    page.on('requestfailed', r => problems.push({ kind: 'requestfailed', url: safeURL(r.url()), error: r.failure()?.errorText }));
    for (const route of ROUTES) {
      const start = problems.length, row = { route, width, height };
      try {
        const response = await page.goto(ORIGIN + route, { waitUntil: 'networkidle' });
        row.status = response?.status() ?? null; row.final_url = safeURL(page.url());
        row.dom = await page.evaluate(() => {
          const visible = e => !!e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden';
          const inputs = [...document.querySelectorAll('input:not([type=hidden]),textarea,select')].filter(visible);
          const labels = inputs.map(e => ({ type: e.type ?? e.tagName, id: e.id, name: e.name,
            has_name: !!(e.labels?.length || e.getAttribute('aria-label') || e.getAttribute('aria-labelledby') || (['submit', 'button'].includes(e.type) && e.value)) }));
          return { title: document.title, lang: document.documentElement.lang,
            main_count: [...document.querySelectorAll('main')].filter(visible).length,
            h1: [...document.querySelectorAll('h1')].filter(visible).map(x => x.innerText),
            horizontal_overflow: document.documentElement.scrollWidth > innerWidth + 1,
            unlabelled_inputs: labels.filter(x => !x.has_name),
            broken_images: [...document.images].filter(visible).filter(x => !x.complete || x.naturalWidth === 0).map(x => ({ alt: x.alt, src: new URL(x.src).pathname })),
            duplicate_ids: [...document.querySelectorAll('[id]')].map(x => x.id).filter((x, i, a) => x && a.indexOf(x) !== i),
            editorial_unconfigured: document.body.innerText.includes('This editorial page has not been configured.') };
        });
        if ([390, 1440].includes(width) && ['/', '/news', '/wiki', '/login'].includes(route)) {
          const name = `${width}-${route === '/' ? 'home' : route.slice(1)}.png`;
          await page.screenshot({ path: path.join(out, name), fullPage: true, animations: 'disabled' }); row.screenshot = name;
        }
      } catch (e) { row.error = String(e).slice(0, 350); }
      row.observed_errors = problems.slice(start); row.criteria = caseCriteria(row);
      report.cases.push(row); save();
    }
    await page.goto(ORIGIN + '/login', { waitUntil: 'networkidle' });
    const focus = [];
    for (let i = 0; i < 16; i++) {
      await page.keyboard.press('Tab');
      focus.push(await page.evaluate(() => {
        const e = document.activeElement, r = e.getBoundingClientRect(), s = getComputedStyle(e);
        return { tag: e.tagName, id: e.id, visible: r.width > 0 && r.height > 0, outline: s.outlineStyle, outline_width: s.outlineWidth };
      }));
    }
    report.keyboard.push({ width, route: '/login', status: 'OBSERVATION_ONLY', focus });
    await context.close();
  }
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false, locale: 'en-US' });
  const problems = []; await restrict(context, problems);
  const page = await context.newPage(); page.setDefaultNavigationTimeout(15000);
  const response = await page.goto(ORIGIN + '/login', { waitUntil: 'load' });
  report.no_javascript = { route: '/login', status: response?.status(), email_visible: await page.locator('input[type=email]').isVisible(),
    password_visible: await page.locator('input[type=password]').isVisible(), blocked_requests: problems };
  if (problems.length) throw Error('no-JavaScript context attempted an out-of-scope request');
  await context.close();
} finally {
  await browser.close(); report.assessment = evaluateReport(report); save();
  const hashes = Object.fromEntries(fs.readdirSync(out).sort().map(name => [name, crypto.createHash('sha256').update(fs.readFileSync(path.join(out, name))).digest('hex')]));
  fs.writeFileSync(path.join(out, 'SHA256SUMS.json'), JSON.stringify(hashes, null, 2) + '\n');
}
console.log(JSON.stringify(report.assessment));
if (report.assessment.errors.length) process.exitCode = 1;
