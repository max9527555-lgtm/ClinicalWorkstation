/* A shared bounded-memory search engine. Full text is scanned only on explicit request. */
(function(g){
const allowed=(s,r)=>!s||r.setting===s||(['out','in'].includes(s)&&['shared','mixed'].includes(r.setting));
function match(r,ff,q,terms){const normalized=ff.map(f=>({label:f[0],text:String(f[1]||''),norm:K.norm(f[1]),weight:f[2]}));if(!terms.every(w=>normalized.some(f=>f.norm.includes(w))))return null;const hits=normalized.filter(f=>terms.some(w=>f.norm.includes(w))).sort((a,b)=>b.weight-a.weight);const explain=hits.find(f=>['常见症状','主要功效','适应病症'].includes(f.label))||hits[0];const first=terms.find(w=>explain.norm.includes(w));const at=first?explain.norm.indexOf(first):0;return {header:K.head(r),score:(K.norm(r.title)===K.norm(q.query)?1000:K.norm(r.title).startsWith(K.norm(q.query))?500:0)+hits.reduce((v,h)=>v+h.weight,0),hit:{label:explain.label,text:explain.text.slice(Math.max(0,at-28),Math.max(0,at-28)+180)}};}
async function run(q,provider,cancelled){
const terms=K.norm(q.query).split(' ').filter(Boolean).slice(0,16);let all=[];
for(const pair of q.modules){if(cancelled())return null;const mk=pair.version+'|'+pair.module;
const eligible=r=>(!q.category||r.category===q.category)&&allowed(q.setting,r);
if(!terms.length||q.scope!=='full'){const hh=await provider.heads(mk);for(let i=0;i<hh.length;i++){if(cancelled())return null;const r=hh[i];if(!eligible(r))continue;if(!terms.length)all.push({header:K.head(r),score:0,hit:null});else{const result=match(r,[['标题',r.title,100],['分类',r.category,20],['完整拼音',r.pinyin,70],['首字母',r.initials,70]].concat(r.quickFields||[]),q,terms);if(result)all.push(result);}if(provider.yield&&i%160===0)await provider.yield();}}
else await provider.walk(mk,r=>{if(!eligible(r))return;const result=match(r,K.fields(r),q,terms);if(result)all.push(result);},cancelled);
}
if(cancelled())return null;all.sort((a,b)=>b.score-a.score||a.header.title.localeCompare(b.header.title,'zh-CN')||a.header.id.localeCompare(b.header.id));return {job:q.job,total:all.length,results:all.slice((q.page||0)*40,((q.page||0)+1)*40)};
}
g.ClinicalSearch={run};
})(typeof self!=='undefined'?self:window);
