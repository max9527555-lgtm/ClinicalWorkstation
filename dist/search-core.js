/* Bounded search: one result set and weakly-held normalized header fields. */
(function(g){
'use strict';
const collator=new Intl.Collator('zh-CN');let prepared=new WeakMap(),memo=null;
const stats={runs:0,cacheHits:0,normalizedHeaders:0};
const allowed=(s,r)=>!s||r.setting===s||(['out','in'].includes(s)&&['shared','mixed'].includes(r.setting));
function normalizeFields(fields){return fields.map(f=>({label:f[0],text:String(f[1]||''),norm:K.norm(f[1]),weight:f[2]}));}
function header(r){let x=prepared.get(r);if(!x){x={header:K.head(r),title:K.norm(r.title),fields:null};prepared.set(r,x);}return x;}
function focused(r){const x=header(r);if(!x.fields){x.fields=normalizeFields([['标题',r.title,100],['分类',r.category,20],['完整拼音',r.pinyin,70],['首字母',r.initials,70]].concat(r.quickFields||[]));stats.normalizedHeaders++;}return x;}
function match(r,x,query,terms){if(!terms.every(w=>x.fields.some(f=>f.norm.includes(w))))return null;const hits=x.fields.filter(f=>terms.some(w=>f.norm.includes(w))).sort((a,b)=>b.weight-a.weight);const explain=hits.find(f=>['常见症状','主要功效','适应病症'].includes(f.label))||hits[0],first=terms.find(w=>explain.norm.includes(w)),at=first?explain.norm.indexOf(first):0;return {header:x.header,score:(x.title===query?1000:x.title.startsWith(query)?500:0)+hits.reduce((v,h)=>v+h.weight,0),hit:{label:explain.label,text:explain.text.slice(Math.max(0,at-28),Math.max(0,at-28)+180)}};}
function page(q,all){const n=Math.max(0,Math.floor(Number(q.page)||0));return {job:q.job,total:all.length,results:all.slice(n*40,(n+1)*40)};}
async function run(q,provider,cancelled){
stats.runs++;const query=K.norm(q.query),terms=query.split(' ').filter(Boolean).slice(0,16),signature=JSON.stringify([q.modules,query,q.scope,q.category||'',q.setting||'']);
if(cancelled())return null;if(memo&&memo.signature===signature){stats.cacheHits++;return page(q,memo.rows);}
let all=[],lastYield=performance.now();for(const pair of q.modules){if(cancelled())return null;const mk=pair.version+'|'+pair.module,eligible=r=>(!q.category||r.category===q.category)&&allowed(q.setting,r);
if(!terms.length||q.scope!=='full'){const hh=await provider.heads(mk);for(let i=0;i<hh.length;i++){if(cancelled())return null;const r=hh[i];if(eligible(r)){if(!terms.length)all.push({header:header(r).header,score:0,hit:null});else{const result=match(r,focused(r),query,terms);if(result)all.push(result);}}if(provider.yield&&i%160===0&&performance.now()-lastYield>12){await provider.yield();lastYield=performance.now();}}}
else await provider.walk(mk,r=>{if(!eligible(r))return;const result=match(r,{header:K.head(r),title:K.norm(r.title),fields:normalizeFields(K.fields(r))},query,terms);if(result)all.push(result);},cancelled);
}
if(cancelled())return null;all.sort((a,b)=>b.score-a.score||collator.compare(a.header.title,b.header.title)||collator.compare(a.header.id,b.header.id));if(cancelled())return null;memo={signature,rows:all};return page(q,all);
}
g.ClinicalSearch={run,stats,clear(){memo=null;prepared=new WeakMap();}};
})(typeof self!=='undefined'?self:window);
