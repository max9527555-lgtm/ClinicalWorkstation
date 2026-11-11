import pathlib,json,hashlib,shutil,gzip,base64
from PIL import Image,ImageDraw
root=pathlib.Path.cwd();dist=root/'dist';data=dist/'data'
mf=json.loads((data/'manifest.json').read_text(encoding='utf-8'));mf['transport']='classic-script-v1';mf['appVersion']='2.0.0'
heads=[]
fields=['key','id','module','moduleKey','version','title','category','setting','caseName','templateNames','flags','missingDetails','flow','emptyTemplates','duplicateIds','pinyin','initials','quickFields']
def enc(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'))
for c in mf['chunks']:
 old=data/pathlib.Path(c['url']).name
 if not old.exists() or old.suffix==".js":
  old=root.parent/'clinical-desk/dist'/c['url'].replace('.js','.json')
 raw=old.read_bytes();rows=json.loads(raw)
 for r in rows:
  q=[['标题',r['title'],100],['分类',r['category'],20],['完整拼音',r.get('pinyin',''),70],['首字母',r.get('initials',''),70]]
  if r['module']=='orders':
   q += [['常见症状','\\n'.join(r['raw'].get('symptoms',[])),60],['摘要',r['raw'].get('summary',''),30],['疾病编码',r['raw'].get('icd10',''),30],['原首字母',r['raw'].get('pinyin',''),60]]
  elif r['module']=='drugs':
   q += [[k,r['raw'].get(k) or '',60 if k in ['主要功效','适应病症'] else 30] for k in ['通用名','商品名','主要功效','适应病症','规格','剂型']]
  elif r['module']=='templates':
   q += [['病例名称',r.get('caseName',''),60],['模板名称',' '.join(r.get('templateNames',[])),30],['主要诊断编码',r['raw']['case'].get('icd10_diagnosis',''),30]]
  elif r['module']=='emergency':q += [['急救正文','\\n'.join(r['raw']['lines']),30]]
  r['quickFields']=q[4:]
 newurl=c['url'].rsplit('.',1)[0]+'.js';js=('ClinicalChunks.register('+enc(newurl)+','+enc(rows)+');').encode()
 (dist/newurl).write_bytes(js)
 c['sha256']=hashlib.sha256(enc(rows).encode()).hexdigest();c['bytes']=len(enc(rows).encode());c['url']=newurl;c['transportSha256']=hashlib.sha256(js).hexdigest();c['transportBytes']=len(js)
 for r in rows:
  h={k:r[k] for k in fields if k in r};h['chunk']=newurl;heads.append(h)
 # Only generated JSON copies are removed; original ZIPs are never touched.
 generated=data/old.name
 if generated.exists() and generated.parent.resolve()==data.resolve() and generated.suffix=='.json':generated.unlink()
(data/'manifest.json').write_text(enc(mf),encoding='utf-8')
catalog='ClinicalChunks.catalog('+enc({'manifest':mf,'headers':heads})+');'
payload=enc({'manifest':mf,'headers':heads}).encode()
packed=base64.b64encode(gzip.compress(payload,compresslevel=9,mtime=0)).decode()
parts=[heads[i:i+400] for i in range(0,len(heads),400)]
(data/'catalog-fallback.js').write_text('ClinicalChunks.catalogFallback('+enc(mf)+','+str(len(parts))+');',encoding='utf-8')
for i,part in enumerate(parts):(data/('catalog-part-'+str(i).zfill(3)+'.js')).write_text('ClinicalChunks.catalogPart('+str(i)+','+enc(part)+');',encoding='utf-8')
(data/'catalog.js').write_text('ClinicalChunks.catalogPacked('+enc(packed)+');',encoding='utf-8')
(root/'reports/portable-build.json').write_text(json.dumps({'color':'#45AF2A','records':len(heads),'startupIndexBytes':(data/'catalog.js').stat().st_size,'uncompressedIndexBytes':len(catalog.encode()),'dataChunks':len(mf['chunks']),'dataBytes':sum(c['transportBytes'] for c in mf['chunks']),'originalJSONBodiesPreserved':True,'externalRuntimeRequired':False,'browserRequired':True},ensure_ascii=False,indent=2),encoding='utf-8')
# Theme only changes application chrome; source HTML styles remain byte-exact.
p=dist/'app.css';css=p.read_text(encoding='utf-8-sig').split('\n/* User supplied exact brand green:')[0]
for a,b in {'--accent:#176867':'--accent:#286a19','--accent-soft:#eaf4f1':'--accent-soft:#eef8e9','background:var(--accent);color:white':'background:#45af2a;color:#152b0d','background:var(--accent);color:white;border-color:var(--accent)':'background:#45af2a;color:#152b0d;border-color:#45af2a','background:#125451':'background:#3e9e26','color:#526b67':'color:#486943','border:1px solid #d6e8e2':'border:1px solid #d8e9d0'}.items():css=css.replace(a,b)
css+='\n/* User supplied exact brand green: RGB(69,175,42); dark labels preserve contrast. */\n.search-wrap button,.primary{background:#45af2a;color:#152b0d;border-color:#45af2a}.search-wrap button:hover,.primary:hover{background:#3e9e26;color:#102008}.brand-mark{background:#45af2a;color:#152b0d}.book:hover{border-color:#94c680}.nav-item.active{color:#286a19}.status-text,.status-badge{color:#286a19}\n'
p.write_text(css,encoding='utf-8')
for name in ['index.html','manifest.webmanifest','icons/icon.svg']:
 p=dist/name;t=p.read_text(encoding='utf-8-sig').replace('#176867','#45af2a');p.write_text(t,encoding='utf-8')
svg=(dist/'icons/icon.svg').read_text();svg=svg.replace('fill="white"','fill="#152b0d"');(dist/'icons/icon.svg').write_text(svg,encoding='utf-8')
for size in [192,512]:
 im=Image.new('RGB',(size,size),'#45af2a');d=ImageDraw.Draw(im);s=size/128;d.rectangle((55*s,28*s,73*s,100*s),fill='#152b0d');d.rectangle((28*s,55*s,100*s,73*s),fill='#152b0d');im.save(dist/f'icons/icon-{size}.png')
print(json.dumps({'heads':len(heads),'catalogBytes':len(catalog.encode()),'color':'#45AF2A','chunks':len(mf['chunks'])},ensure_ascii=False))

