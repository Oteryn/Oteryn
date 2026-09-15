import test from 'node:test';
import assert from 'node:assert/strict';
import { SOURCE_SHA, SOURCE_TREE, SOURCE_BINDINGS, ORIGIN, PLAYWRIGHT, ROUTES, SIZES, expectedStatus, requestAllowed, evaluateReport } from './public-surface-contract.mjs';
function fixture() {
  return { schema_version: 2, source_sha: SOURCE_SHA, source_tree: SOURCE_TREE, source_bindings: { ...SOURCE_BINDINGS }, playwright: PLAYWRIGHT, browser: 'test-double',
    cases: SIZES.flatMap(([width, height]) => ROUTES.map(route => ({ route, width, height,
      status: expectedStatus(route), final_url: ORIGIN + route, observed_errors: [],
      dom: { title: 'fixture', lang: 'en', main_count: 1, h1: ['fixture'], horizontal_overflow: false,
        unlabelled_inputs: [], broken_images: [], duplicate_ids: [], editorial_unconfigured: expectedStatus(route) === 404 } }))),
    no_javascript: { route: '/login', status: 200, email_visible: true, password_visible: true, blocked_requests: [] } };
}
const pass = r => evaluateReport(r).errors.length === 0;
test('closed fixture includes exactly eight justified 404 observations', () => {
  const r = fixture(); assert.equal(r.cases.length, 48); assert.equal(r.cases.filter(x => x.status === 404).length, 8); assert.ok(pass(r));
});
for (const [name, mutate] of [
  ['source substitution', r => { r.source_sha = '0'.repeat(40); }],
  ['tree substitution', r => { r.source_tree = '0'.repeat(40); }],
  ['unversioned capture', r => { delete r.schema_version; }],
  ['toolchain substitution', r => { r.playwright = 'wrong'; }],
  ['normal route missing', r => { r.cases[0].status = 404; }],
  ['missing editorial unexpectedly published', r => { r.cases[10].status = 200; }],
  ['wrong editorial state', r => { r.cases[10].dom.editorial_unconfigured = false; }],
  ['duplicate conceals missing row', r => { r.cases[1] = structuredClone(r.cases[0]); }],
  ['missing row', r => { r.cases.pop(); }],
  ['extra row', r => { r.cases.push(structuredClone(r.cases[0])); }],
  ['unknown viewport', r => { r.cases[0].height = 843; }],
  ['unknown route', r => { r.cases[0].route = '/unreviewed'; }],
  ['external redirect', r => { r.cases[0].final_url = 'https://example.invalid/'; }],
  ['missing DOM observations', r => { delete r.cases[0].dom; }],
  ['string false is not false', r => { r.cases[0].dom.horizontal_overflow = 'false'; }],
  ['missing label observations', r => { delete r.cases[0].dom.unlabelled_inputs; }],
  ['broken image', r => { r.cases[0].dom.broken_images = ['missing']; }],
  ['duplicate DOM id', r => { r.cases[0].dom.duplicate_ids = ['duplicate']; }],
  ['missing main', r => { r.cases[0].dom.main_count = 0; }],
  ['empty heading', r => { r.cases[0].dom.h1 = [' ']; }],
  ['missing language', r => { r.cases[0].dom.lang = ''; }],
  ['page error', r => { r.cases[0].observed_errors = [{ kind: 'pageerror' }]; }],
  ['navigation exception', r => { r.cases[0].error = 'timeout'; }],
  ['no-JS missing password', r => { r.no_javascript.password_visible = false; }],
]) test(name, () => { const r = fixture(); mutate(r); assert.equal(pass(r), false); });
test('only explicit legacy replay may omit newly captured state/tree, and is labelled', () => {
  const r = fixture(); delete r.schema_version; delete r.source_tree;
  for (const c of r.cases) delete c.dom.editorial_unconfigured;
  assert.equal(pass(r), false); const result = evaluateReport(r, { legacy: true });
  assert.equal(result.errors.length, 0); assert.match(result.mode, /NOT_NEW_BROWSER_EXECUTION/); assert.equal(result.missing_editorial_text_checked, false);
});
test('HTTP-only loopback read policy rejects mutation, other ports, other hosts and malformed URLs', () => {
  for (const method of ['GET', 'HEAD']) assert.equal(requestAllowed(method, ORIGIN + '/login'), true);
  for (const [method, url] of [['POST', ORIGIN], ['GET', 'http://127.0.0.1:8081/'], ['GET', 'http://localhost:8080/'], ['GET', 'https://example.invalid/'], ['GET', 'file:///etc/passwd'], ['GET', 'bad']]) assert.equal(requestAllowed(method, url), false);
  assert.throws(() => expectedStatus('/unknown'));
});
