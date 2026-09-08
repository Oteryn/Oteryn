import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {SOURCE_SHA,SOURCE_TREE,SOURCE_BINDINGS,PLAYWRIGHT,ORIGIN,ROUTES,SIZES,expectedStatus,evaluateReport,requestAllowed} from './public-surface-contract.mjs';
import { createNewOutputDirectory } from './safe-output.mjs';
function valid() {
  return {schema_version:2,source_sha:SOURCE_SHA,source_tree:SOURCE_TREE,source_bindings:{...SOURCE_BINDINGS},playwright:PLAYWRIGHT,browser:'unit-test-double',
    cases:SIZES.flatMap(([width,height])=>ROUTES.map(route=>({route,width,height,status:expectedStatus(route),final_url:ORIGIN+route,observed_errors:[],
      dom:{main_count:1,h1:['Test'],lang:'en',title:'Test',horizontal_overflow:false,unlabelled_inputs:[],broken_images:[],duplicate_ids:[],editorial_unconfigured:expectedStatus(route)===404}}))),
    no_javascript:{route:'/login',status:200,email_visible:true,password_visible:true,blocked_requests:[]}};
}
test('hardening fixture itself passes',()=>assert.equal(evaluateReport(valid()).errors.length,0));
for (const [name,mutate] of [
 ['same-origin wrong page is rejected',r=>{r.cases[0].final_url=ORIGIN+'/login';}],
 ['missing source-binding map is rejected',r=>{delete r.source_bindings;}],
 ['wrong fixture-binding hash is rejected',r=>{r.source_bindings['scripts/acceptance/seed.php']='0'.repeat(40);}],
 ['no-JavaScript blocked request is rejected',r=>{r.no_javascript.blocked_requests=[{method:'POST',url:ORIGIN+'/login'}];}],
 ['missing no-JavaScript network observations are rejected',r=>{delete r.no_javascript.blocked_requests;}],
]) test(name,()=>{const r=valid();mutate(r);assert.notEqual(evaluateReport(r).errors.length,0);});
test('URLs carrying credentials are not anonymous requests',()=>assert.equal(requestAllowed('GET','http://example:example@127.0.0.1:8080/login'),false));

test('browser output rejects symlinked ancestor resolving inside provider', t => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'audit185-safe-output-'));
  t.after(() => fs.rmSync(tmp, { recursive: true, force: true }));
  const provider = path.join(tmp, 'provider');
  const nested = path.join(provider, 'nested');
  fs.mkdirSync(nested, { recursive: true });
  const link = path.join(tmp, 'provider-link');
  try { fs.symlinkSync(provider, link, process.platform === 'win32' ? 'junction' : 'dir'); }
  catch { t.skip('symlink unavailable'); return; }
  assert.throws(() => createNewOutputDirectory(provider, path.join(link, 'nested', 'new-evidence')), /outside provider|required/);
  assert.equal(fs.existsSync(path.join(provider, 'nested', 'new-evidence')), false);
});

test('browser output rejects a dangling final symlink without creating its target', t => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'audit185-safe-output-'));
  t.after(() => fs.rmSync(tmp, { recursive: true, force: true }));
  const provider = path.join(tmp, 'provider');
  const outParent = path.join(tmp, 'evidence');
  fs.mkdirSync(provider); fs.mkdirSync(outParent);
  const target = path.join(tmp, 'should-not-exist');
  const link = path.join(outParent, 'new-evidence');
  try { fs.symlinkSync(target, link, process.platform === 'win32' ? 'file' : undefined); }
  catch { t.skip('symlink unavailable'); return; }
  assert.throws(() => createNewOutputDirectory(provider, link), /existing output path or symlink/);
  assert.equal(fs.existsSync(target), false);
});

test('browser output creates a new canonical directory outside provider', t => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'audit185-safe-output-'));
  t.after(() => fs.rmSync(tmp, { recursive: true, force: true }));
  const provider = path.join(tmp, 'provider');
  const outParent = path.join(tmp, 'evidence');
  fs.mkdirSync(provider); fs.mkdirSync(outParent);
  const result = createNewOutputDirectory(provider, path.join(outParent, 'new-evidence'));
  assert.equal(result.root, fs.realpathSync(provider));
  assert.equal(result.out, fs.realpathSync(path.join(outParent, 'new-evidence')));
});
