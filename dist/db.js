/* Shared IndexedDB primitives: every mutation resolves on commit. */
(function(g){
'use strict';
const DB='clinical-desk',SCHEMA=1;
const req=r=>new Promise((ok,no)=>{r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error);});
const done=t=>new Promise((ok,no)=>{t.oncomplete=()=>ok();t.onabort=()=>no(t.error||Error('资料写入中断'));t.onerror=()=>no(t.error||Error('资料写入失败'));});
let dbPromise;
function open(){if(!dbPromise)dbPromise=new Promise((ok,no)=>{const r=indexedDB.open(DB,SCHEMA);r.onupgradeneeded=()=>{const d=r.result;['records','headers'].forEach(n=>{const s=d.createObjectStore(n,{keyPath:'key'});s.createIndex('moduleKey','moduleKey');});d.createObjectStore('meta',{keyPath:'key'});};r.onblocked=()=>no(Error('旧页面正在使用资料库，请关闭其他工作站标签页后重试。'));r.onerror=()=>{dbPromise=null;no(r.error);};r.onsuccess=()=>{const d=r.result;d.onversionchange=()=>{d.close();dbPromise=null;};ok(d);};});return dbPromise;}
async function get(store,key){const d=await open();return req(d.transaction(store).objectStore(store).get(key));}
async function meta(key){const x=await get('meta',key);return x&&x.value;}
async function setMeta(key,value){const d=await open(),t=d.transaction('meta','readwrite'),p=done(t);t.objectStore('meta').put({key,value});await p;}
function head(r){const h={};['key','id','module','moduleKey','version','title','category','setting','caseName','templateNames','flags','missingDetails','flow','emptyTemplates','duplicateIds','quickFields','pinyin','initials'].forEach(k=>{if(r[k]!==undefined)h[k]=r[k];});return h;}
async function putChunk(rows,mark){const d=await open(),t=d.transaction(['records','headers','meta'],'readwrite'),p=done(t);rows.forEach(r=>{t.objectStore('records').put(r);t.objectStore('headers').put(head(r));});t.objectStore('meta').put({key:mark,value:true});t.objectStore('meta').put({key:mark+':ids',value:rows.map(r=>r.key)});await p;}
async function allHeads(moduleKey){const d=await open();return req(d.transaction('headers').objectStore('headers').index('moduleKey').getAll(moduleKey));}
async function count(moduleKey){const d=await open();return req(d.transaction('records').objectStore('records').index('moduleKey').count(moduleKey));}
async function hash(buffer){if(!g.crypto||!g.crypto.subtle)throw Error('当前连接不支持完整性校验，请使用安全连接或本机服务。');return Array.from(new Uint8Array(await g.crypto.subtle.digest('SHA-256',buffer))).map(b=>b.toString(16).padStart(2,'0')).join('');}
const norm=x=>String(x==null?'':x).normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
function flat(v){if(v==null)return '';if(Array.isArray(v))return v.map(flat).join('\n');if(typeof v==='object')return Object.keys(v).map(k=>flat(v[k])).join('\n');return String(v);}
const labels={name:'名称',category:'分类',summary:'摘要',symptoms:'常见症状',diagnosis:'诊断',infusion:'输液方案',oral_medication:'口服用药',treatment:'治疗',management:'管理',notes:'注意事项',emergency:'急救内容',pinyin:'原拼音',icd10:'疾病编码',physical_exam:'体格检查',lab_tests:'辅助检查',nursing:'护理',diet:'饮食',topical_medication:'外用药物',tcm_fangji:'中医方剂',differential:'鉴别诊断',data_flags:'资料标记',icd10_diagnosis:'主要诊断编码',icd10_secondary:'次要诊断编码',icd9cm3_procedure:'手术操作编码'};
function fields(r){let f=[['标题',r.title,100],['分类',r.category,20],['完整拼音',r.pinyin,70],['首字母',r.initials,70]];
if(r.module==='orders')Object.keys(r.raw).forEach(k=>f.push([labels[k]||'原始扩展字段：'+k,flat(r.raw[k]),k==='symptoms'?60:15]));
if(r.module==='drugs')Object.keys(r.raw).forEach(k=>f.push([k,flat(r.raw[k]),['主要功效','适应病症'].includes(k)?60:15]));
if(r.module==='templates'){f.push(['病例名称',r.caseName,60]);Object.keys(r.raw.case.templates).forEach(k=>f.push([k,r.raw.case.templates[k],15]));['icd10_diagnosis','icd10_secondary','icd9cm3_procedure'].forEach(k=>f.push([labels[k],flat(r.raw.case[k]),15]));}
if(r.module==='emergency')f.push(['急救正文',r.raw.lines.join('\n'),30]);
if(r.module==='documents')f.push(['文书正文',r.raw.text,20]);
return f;}
g.K={open,get,meta,setMeta,done,req,putChunk,head,allHeads,count,hash,norm,flat,labels,fields,DB,SCHEMA};
})(typeof self!=='undefined'?self:window);

