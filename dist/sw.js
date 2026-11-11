/* Versioned application shell only. Knowledge bodies live in IndexedDB, never duplicated here. */
const SHELL='clinical-shell-10023511f5ac79cb';
const ASSETS=['./','index.html','app.css','app.js','db.js','chunks.js','portable.js','search-core.js','search-worker.js','manifest.webmanifest','icons/icon.svg','icons/icon-192.png','icons/icon-512.png','data/manifest.json'];
self.addEventListener('install',e=>e.waitUntil((async()=>{const c=await caches.open(SHELL);await c.addAll(ASSETS);await self.skipWaiting();})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(k.startsWith('clinical-shell-')&&k!==SHELL)await caches.delete(k);await self.clients.claim();})()));
self.addEventListener('fetch',e=>{
 const u=new URL(e.request.url);if(u.origin!==location.origin||e.request.method!=='GET')return;
 if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).then(async r=>{if(r.ok){const c=await caches.open(SHELL);await c.put('index.html',r.clone());}return r;}).catch(()=>caches.match('index.html')));return;}
 if(u.pathname.includes('/data/')&&!u.pathname.endsWith('/manifest.json'))return;
 e.respondWith((async()=>{const c=await caches.open(SHELL),cached=await c.match(e.request);if(cached)return cached;return fetch(e.request);})());
});
