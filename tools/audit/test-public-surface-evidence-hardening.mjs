import test from 'node:test';
import assert from 'node:assert/strict';
import {SOURCE_SHA,SOURCE_TREE,SOURCE_BINDINGS,PLAYWRIGHT,ORIGIN,ROUTES,SIZES,expectedStatus,evaluateReport,requestAllowed} from './public-surface-contract.mjs';
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
