// A closed, source-bound fixture oracle. This is not production or WCAG acceptance.
export const SOURCE_SHA = 'de917b3477a1de0667531380de3660e8b2ab59aa';
export const SOURCE_TREE = 'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e';
export const ORIGIN = 'http://127.0.0.1:8080';
export const PLAYWRIGHT = '1.62.1';
export const ROUTES = Object.freeze([
  '/', '/news', '/news/welcome-to-oteryn', '/wiki', '/download', '/login',
  '/register', '/forgot-password', '/recovery-key', '/events', '/support', '/legal/privacy',
]);
export const SIZES = Object.freeze([[390, 844], [820, 1180], [1440, 1000], [1920, 1080]].map(Object.freeze));
export const SOURCE_BINDINGS = Object.freeze({
  'scripts/acceptance/seed.php': 'e6ac69c2ab87731ae6b8ed476bd0f482deb16478',
  'tests/Feature/Support/EditorialSupportLegalTest.php': 'dfb0f6432e2a5c48d3c4c179bbf21f1e3908a678',
  'app/Support/PublicEditorialPage.php': 'ca3f38d5fc9c621bffd2300f98eed07fe75f1b31',
  'app/Cms/Editorial/EditorialPageQuery.php': '9520e53836219308797b803cbe69e673b9fb8dec',
  'scripts/acceptance/package-lock.json': 'd11790667e716bbe63bac4eb73f62d6a2fde6021',
});

// The pinned seed empties managed_pages and publishes only about-oteryn.
// The pinned controller and regression test require 404 for missing editorial pages.
// Never generalize this exception to arbitrary routes, fixtures or production.
export function expectedStatus(route) {
  if (!ROUTES.includes(route)) throw Error('route outside the closed fixture matrix');
  return ['/support', '/legal/privacy'].includes(route) ? 404 : 200;
}
export function requestAllowed(method, raw) {
  try { return ['GET', 'HEAD'].includes(method) && new URL(raw).origin === ORIGIN; }
  catch { return false; }
}
const empty = value => Array.isArray(value) && value.length === 0;
const nonempty = value => typeof value === 'string' && value.trim().length > 0;
export function caseCriteria(row, { legacy = false } = {}) {
  const d = row?.dom ?? {};
  const known = ROUTES.includes(row?.route);
  return {
    fixture_identity: known && SIZES.some(([w, h]) => row.width === w && row.height === h),
    http_ok: known && row.status === expectedStatus(row.route),
    local_response: requestAllowed('GET', row?.final_url),
    main: d.main_count === 1,
    heading: Array.isArray(d.h1) && d.h1.length === 1 && nonempty(d.h1[0]),
    language: d.lang === 'en', title: nonempty(d.title),
    no_overflow: d.horizontal_overflow === false,
    labels: empty(d.unlabelled_inputs), images: empty(d.broken_images), unique_ids: empty(d.duplicate_ids),
    no_browser_errors: empty(row?.observed_errors) && !row?.error,
    missing_editorial_state: legacy || !known || expectedStatus(row.route) !== 404 || d.editorial_unconfigured === true,
  };
}
export function evaluateReport(report, { legacy = false } = {}) {
  const errors = [];
  if (report?.source_sha !== SOURCE_SHA) errors.push('source_sha');
  if (!legacy && (report?.schema_version !== 2 || report?.source_tree !== SOURCE_TREE)) errors.push('schema/source_tree');
  if (report?.playwright !== PLAYWRIGHT || !nonempty(report?.browser)) errors.push('browser/toolchain');
  const cases = Array.isArray(report?.cases) ? report.cases : [];
  const expected = new Set(SIZES.flatMap(([w, h]) => ROUTES.map(r => `${w}:${h}:${r}`)));
  const seen = new Set();
  for (const row of cases) {
    const key = `${row?.width}:${row?.height}:${row?.route}`;
    if (seen.has(key) || !expected.has(key)) errors.push(`duplicate/unknown case ${key}`);
    seen.add(key);
    for (const [criterion, pass] of Object.entries(caseCriteria(row, { legacy }))) {
      if (!pass) errors.push(`${key}:${criterion}`);
    }
  }
  if (cases.length !== expected.size || [...expected].some(key => !seen.has(key))) errors.push('incomplete matrix');
  const noJS = report?.no_javascript;
  if (noJS?.route !== '/login' || noJS.status !== 200 || noJS.email_visible !== true || noJS.password_visible !== true) errors.push('no-javascript control');
  return { verdict: errors.length ? 'FAIL' : 'PASS_SCOPED_PUBLIC_FIXTURE', cases: cases.length,
    mode: legacy ? 'REPLAY_OF_CAPTURED_OBSERVATIONS_NOT_NEW_BROWSER_EXECUTION' : 'CAPTURED_BROWSER_OBSERVATIONS',
    missing_editorial_text_checked: !legacy, errors,
    limitations: 'Anonymous English fixture only; keyboard sequence is observational. No authenticated journey, complete accessibility, production, native game or independent visual acceptance.' };
}
