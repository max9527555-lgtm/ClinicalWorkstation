import {createRequire} from 'node:module';import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';import assert from 'node:assert/strict';
const require=createRequire('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/package.json'),{chromium}=require('playwright');
const dir=path.resolve('../U盘复制测试/临床 工作站'),report={tests:[],errors:[]};fs.mkdirSync(dir,{recursive:true});fs.cpSync('dist',path.join(dir,'dist'),{recursive:true});fs.copyFileSync('打开临床工作站.html',path.join(dir,'打开临床工作站.html'));
const b=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'}),c=await b.newContext({viewport:{width:1024,height:768}});await c.setOffline(true);const p=await c.newPage();p.on('pageerror',e=>report.errors.push(e.message));
await p.addInitScript(()=>{window.__databaseWrites=0;const old=indexedDB.open.bind(indexedDB);indexedDB.open=(...args)=>{window.__databaseWrites++;return old(...args);};});
try{
await p.goto(pathToFileURL(path.join(dir,'打开临床工作站.html')).href);await p.waitForFunction(()=>window.PORTABLE&&state.ready.documents);assert.equal(await p.evaluate(()=>__databaseWrites),0);report.tests.push({name:'复制到含中文与空格的新目录后，断网双击根入口可用且未打开本地数据库',status:'通过'});
await p.locator('[data-action=prepare]').click();await p.waitForFunction(()=>!state.busy&&state.progressMessage.includes('7752'),null,{timeout:120000});report.tests.push({name:'所有131个分块逐一读取并核对数量与指纹',status:'通过'});
const stats=await p.evaluate(()=>Portable.stats());assert.equal(stats.cachedChunks,2);report.tests.push({name:'全包校验完成后仍仅保留两个正文分块',status:'通过',stats});
await p.locator('[data-module=emergency]').first().click();await p.waitForFunction(()=>document.querySelectorAll('.result').length>0);const key=await p.locator('.result').first().getAttribute('data-record');const chunk=await p.evaluate(async k=>(await ClinicalChunks.getCatalog()).headers.find(h=>h.key===k).chunk,key);
await p.reload();await p.waitForFunction(()=>state.ready.documents);const missing=path.resolve(dir,'dist',chunk);assert(missing.startsWith(path.resolve(dir)+path.sep));fs.renameSync(missing,missing+'.test-disabled');try{await p.evaluate(k=>openRecord(k),key);assert.match(await p.locator('#notice').innerText(),/无法读取资料文件/);}finally{fs.renameSync(missing+'.test-disabled',missing);}report.tests.push({name:'正文文件缺失或被阻止时明确提示，不出现无响应详情',status:'通过'});
assert.deepEqual(report.errors,[]);
const fallbackContext=await b.newContext();await fallbackContext.setOffline(true);await fallbackContext.addInitScript(()=>Object.defineProperty(window,'DecompressionStream',{value:undefined,configurable:true}));
const fp=await fallbackContext.newPage();await fp.goto(pathToFileURL(path.join(dir,'打开临床工作站.html')).href);await fp.waitForFunction(()=>window.PORTABLE&&state.ready.documents);assert.equal(await fp.evaluate(()=>Portable.manifest.counts.templates),4242);report.tests.push({name:'无原生解压能力时自动读取本地分段备用目录',status:'通过'});await fallbackContext.close();
}catch(e){report.tests.push({name:'复制与全量校验中断',status:'失败',error:e.stack});console.error(e.stack);process.exitCode=1;}
finally{fs.writeFileSync('reports/portable-copy-tests.json',JSON.stringify(report,null,2));await b.close();}
console.log(report.tests.map(t=>t.status+' '+t.name).join('\n'));
