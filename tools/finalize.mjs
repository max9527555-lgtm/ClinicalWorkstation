import fs from 'node:fs';import crypto from 'node:crypto';import path from 'node:path';
const files=['index.html','app.js','app.css','db.js','chunks.js','portable.js','search-core.js','search-worker.js','manifest.webmanifest','data/manifest.json','icons/icon.svg','icons/icon-192.png','icons/icon-512.png'];
const sum=crypto.createHash('sha256');for(const f of files){const b=fs.readFileSync(path.join('dist',f));sum.update(f.endsWith('.png')?b:b.toString('utf8').replace(/const SHELL='clinical-shell-[^']*'/g,"const SHELL='clinical-shell-BUILD'"));}
const version=sum.digest('hex').slice(0,16);for(const f of ['app.js','sw.js']){const p=path.join('dist',f);const t=fs.readFileSync(p,'utf8').replace(/const SHELL='clinical-shell-[^']*'/g,"const SHELL='clinical-shell-"+version+"'");fs.writeFileSync(p,t);}
fs.writeFileSync('reports/build.json',JSON.stringify({appVersion:'2.0.0',shellVersion:version,generated:new Date().toISOString()},null,2));console.log('Shell build',version);
