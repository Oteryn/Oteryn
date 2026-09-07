#!/usr/bin/env node
// Observation-only public UI audit. No credentials, form submissions, DOM rewrites or product repair.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
const [rootArg, outputArg] = process.argv.slice(2);
if (process.env.OTERYN_AUDIT185_PUBLIC_UI !== '1' || !rootArg || !outputArg) throw Error('explicit isolated-public-UI consent, source and new output required');
const root = fs.realpathSync(rootArg), out = path.resolve(outputArg);
if (fs.existsSync(out)) throw Error('output already exists');
const sha = 'de917b3477a1de0667531380de3660e8b2ab59aa';
for (const [args, expected] of [[['rev-parse','HEAD'],sha], [['rev-parse','HEAD^{tree}'],'ffdf2a286d3a39f2344cf2ff53b28e4ef7369a8e'], [['status','--porcelain','--untracked-files=no'],'']]) {
  if (execFileSync('git',args,{cwd:root,encoding:'utf8'}).trim() !== expected) throw Error('wrong or dirty source');
}
const require = createRequire(path.join(root,'scripts/acceptance/package.json'));
const { chromium } = require('@playwright/test');
const version = require('@playwright/test/package.json').version;
if (version !== '1.62.1') throw Error('unexpected Playwright dependency');
fs.mkdirSync(out,{recursive:true});
const routes = ['/', '/news', '/news/welcome-to-oteryn', '/wiki', '/download', '/login', '/register', '/forgot-password', '/recovery-key', '/events', '/support', '/legal/privacy'];
const sizes = [[390,844],[820,1180],[1440,1000],[1920,1080]];
const report={source_sha:sha,playwright:version,scope:'Anonymous public UI; SQLite with canonical synthetic news/identity fixtures; Canary deliberately unavailable; no authenticated account/admin/payment/real-game qualification',cases:[],keyboard:[],no_javascript:null};
const browser = await chromium.launch({headless:true});
report.browser=browser.version();
function sanitizedURL(raw) { try {const u=new URL(raw);return u.origin+u.pathname;} catch {return 'invalid-url';} }
try {
  for(const [width,height] of sizes) {
    const context=await browser.newContext({viewport:{width,height},locale:'en-US',reducedMotion:'reduce'});
    const page=await context.newPage();page.setDefaultTimeout(12000);page.setDefaultNavigationTimeout(15000);
    const problems=[];
    await context.route('**/*', route => ['GET','HEAD'].includes(route.request().method()) ? route.continue() : route.abort());
    page.on('pageerror',e=>problems.push({kind:'pageerror',message:e.message.slice(0,300)}));
    page.on('requestfailed',r=>problems.push({kind:'requestfailed',url:sanitizedURL(r.url()),error:r.failure()?.errorText}));
    for(const route of routes) {
      const start=problems.length;const row={route,width,height};
      try {
        const response=await page.goto('http://127.0.0.1:8080'+route,{waitUntil:'networkidle'});
        row.status=response?.status()??null;row.final_url=sanitizedURL(page.url());
        row.dom=await page.evaluate(()=>{
          const visible=e=>!!e.getClientRects().length && getComputedStyle(e).visibility!=='hidden';
          const inputs=[...document.querySelectorAll('input:not([type=hidden]),textarea,select')].filter(visible);
          const labels=inputs.map(e=>({type:e.type??e.tagName,id:e.id,name:e.name,has_name:!!(e.labels?.length||e.getAttribute('aria-label')||e.getAttribute('aria-labelledby')||(['submit','button'].includes(e.type)&&e.value))}));
          return {title:document.title,lang:document.documentElement.lang,main_count:[...document.querySelectorAll('main')].filter(visible).length,
            h1:[...document.querySelectorAll('h1')].filter(visible).map(x=>x.innerText),
            horizontal_overflow:document.documentElement.scrollWidth>innerWidth+1,unlabelled_inputs:labels.filter(x=>!x.has_name),
            broken_images:[...document.images].filter(visible).filter(x=>!x.complete||x.naturalWidth===0).map(x=>({alt:x.alt,src:new URL(x.src).pathname})),
            duplicate_ids:[...document.querySelectorAll('[id]')].map(x=>x.id).filter((x,i,a)=>x&&a.indexOf(x)!==i),
            main_font:document.querySelector('main')?getComputedStyle(document.querySelector('main')).fontFamily:null};
        });
        if([390,1440].includes(width)&&['/','/news','/wiki','/login'].includes(route)) {
          const name=`${width}-${route==='/'?'home':route.slice(1)}.png`;
          await page.screenshot({path:path.join(out,name),fullPage:true,animations:'disabled'});row.screenshot=name;
        }
        row.criteria={http_ok:row.status===200,main:row.dom.main_count===1,heading:row.dom.h1.length===1,language:!!row.dom.lang,title:!!row.dom.title,no_overflow:!row.dom.horizontal_overflow,labels:row.dom.unlabelled_inputs.length===0,images:row.dom.broken_images.length===0,unique_ids:row.dom.duplicate_ids.length===0};
      }catch(e){row.error=String(e).slice(0,350);}
      row.observed_errors=problems.slice(start);report.cases.push(row);
      fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2)+'\n');
    }
    await page.goto('http://127.0.0.1:8080/login',{waitUntil:'networkidle'});
    const focus=[];
    for(let i=0;i<16;i++){
      await page.keyboard.press('Tab');
      focus.push(await page.evaluate(()=>{const e=document.activeElement;const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {tag:e.tagName,id:e.id,text:(e.innerText||e.getAttribute('aria-label')||e.name||'').slice(0,90),visible:r.width>0&&r.height>0,outline:s.outlineStyle,outline_width:s.outlineWidth};}));
    }
    report.keyboard.push({width,route:'/login',focus});await context.close();
  }
  const context=await browser.newContext({viewport:{width:390,height:844},javaScriptEnabled:false,locale:'en-US'});
  const page=await context.newPage();page.setDefaultNavigationTimeout(15000);
  const response=await page.goto('http://127.0.0.1:8080/login',{waitUntil:'load'});
  report.no_javascript={route:'/login',status:response?.status(),email_visible:await page.locator('input[type=email]').isVisible(),password_visible:await page.locator('input[type=password]').isVisible()};
  await context.close();
}finally{
  await browser.close();
  report.failed_criteria=report.cases.flatMap(r=>r.error?[{route:r.route,width:r.width,error:r.error}]:Object.entries(r.criteria??{}).filter(([,v])=>!v).map(([criterion])=>({route:r.route,width:r.width,criterion})));
  fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(report,null,2)+'\n');
  const hashes=Object.fromEntries(fs.readdirSync(out).sort().map(name=>[name,crypto.createHash('sha256').update(fs.readFileSync(path.join(out,name))).digest('hex')]));
  fs.writeFileSync(path.join(out,'SHA256SUMS.json'),JSON.stringify(hashes,null,2)+'\n');
}
console.log(JSON.stringify({cases:report.cases.length,failed_criteria:report.failed_criteria,no_javascript:report.no_javascript}));
if(report.cases.length!==48||report.failed_criteria.length||!report.no_javascript?.email_visible||!report.no_javascript?.password_visible) process.exitCode=1;
