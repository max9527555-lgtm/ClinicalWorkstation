importScripts('db.js','search-core.js');
let generation=0;const headCache=new Map();async function heads(mk){if(!headCache.has(mk)){headCache.set(mk,await K.allHeads(mk));while(headCache.size>5)headCache.delete(headCache.keys().next().value);}return headCache.get(mk);}
self.onmessage=async e=>{const q=e.data,job=++generation;try{
const result=await ClinicalSearch.run(q,{heads,async walk(mk,visit,cancelled){
const d=await K.open();await new Promise((ok,no)=>{const t=d.transaction('records'),rq=t.objectStore('records').index('moduleKey').openCursor(IDBKeyRange.only(mk));rq.onerror=()=>no(rq.error);rq.onsuccess=()=>{const c=rq.result;if(!c||cancelled()){ok();return;}visit(c.value);c.continue();};});}},()=>job!==generation);
if(result&&job===generation)self.postMessage(result);
}catch(err){if(job===generation)self.postMessage({job:q.job,error:'搜索暂时不可用，请刷新或重新准备本机资料。'});}};
