/* Portable file mode. It reads only a small catalogue and, on demand, at most two body chunks. */
(function(g){
'use strict';const enabled=location.protocol==='file:';g.PORTABLE=enabled;if(!enabled)return;
let cat=null,byKey=null,byModule=null,metaMemory={};const yieldTask=()=>new Promise(r=>setTimeout(r,0));
async function ready(){if(cat)return cat;cat=await ClinicalChunks.getCatalog();byKey=new Map(cat.headers.map(h=>[h.key,h]));byModule={};for(const h of cat.headers){(byModule[h.moduleKey]||(byModule[h.moduleKey]=[])).push(h);}return cat;}
K.open=ready;
K.meta=async key=>{await ready();if(key==='activeDataset'||key==='active:emergency')return cat.manifest.version;if(key.startsWith('ready:'))return true;if(key==='manifest:'+cat.manifest.version)return cat.manifest;if(key.endsWith(':ids')){const url=key.slice(('chunk:'+cat.manifest.version+':').length,-4);return cat.headers.filter(h=>h.chunk===url).map(h=>h.key);}if(metaMemory[key]!==undefined)return metaMemory[key];try{return JSON.parse(localStorage.getItem('clinical-portable:'+key)||'null');}catch(e){return null;}};
K.setMeta=async(key,value)=>{metaMemory[key]=value;try{localStorage.setItem('clinical-portable:'+key,JSON.stringify(value));}catch(e){}};
K.allHeads=async mk=>{await ready();return byModule[mk]||[];};
K.count=async mk=>(await K.allHeads(mk)).length;
K.get=async(store,key)=>{await ready();if(store!=='records')return null;const h=byKey.get(key);if(!h)return null;const rows=await ClinicalChunks.load(h.chunk);const r=rows.find(r=>r.key===key);if(!r)throw Error('资料目录与正文不匹配，请重新解压完整包。');return r;};
K.putChunk=async()=>{throw Error('便携版资料直接保存在文件夹，请通过完整文件夹备份或恢复。');};
class PortableSearch{
constructor(){this.generation=0;this.onmessage=null;this.onerror=null;}
terminate(){this.generation++;}
postMessage(q){const gen=++this.generation;(async()=>{await ready();const result=await ClinicalSearch.run(q,{heads:K.allHeads,yield:yieldTask,async walk(mk,visit,cancelled){for(const c of cat.manifest.chunks.filter(c=>cat.manifest.version+'|'+c.module===mk)){if(cancelled())return;const rows=await ClinicalChunks.load(c.url);for(let i=0;i<rows.length;i++){if(cancelled())return;await visit(rows[i]);if(i%12===0)await yieldTask();}await yieldTask();}}},()=>gen!==this.generation);if(result&&gen===this.generation&&this.onmessage)this.onmessage({data:result});})().catch(e=>{if(gen===this.generation&&this.onmessage)this.onmessage({data:{job:q.job,error:e.message||'本地资料读取失败，请重新解压。'}});});}
}
g.PortableSearch=PortableSearch;g.Portable={ready,get manifest(){return cat&&cat.manifest;},stats:()=>({cachedChunks:ClinicalChunks.cacheSize(),...ClinicalChunks.stats}),async verifyAll(progress){await ready();let count=0;for(const c of cat.manifest.chunks){const rr=await ClinicalChunks.load(c.url);if(rr.length!==c.count)throw Error('本地资料数量不匹配：'+c.url);if(window.crypto&&crypto.subtle&&await K.hash(new TextEncoder().encode(JSON.stringify(rr)))!==c.sha256)throw Error('资料内容校验失败：'+c.url);count+=rr.length;if(progress)progress(count,cat.headers.length);await yieldTask();}return count;}};
})(window);
