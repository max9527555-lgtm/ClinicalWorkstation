import pathlib,sys,zipfile,json,hashlib,re,io,html,collections,argparse
sys.path.insert(0,str(pathlib.Path(__file__).parent/'vendor'))
from pypinyin import lazy_pinyin,Style
import openpyxl
from lxml import html as lh
ROOT=pathlib.Path(__file__).resolve().parents[1];DIST=ROOT/'dist';DATA=DIST/'data';DATA.mkdir(parents=True,exist_ok=True);(ROOT/'reports').mkdir(exist_ok=True)
args=argparse.ArgumentParser(description='只读构建临床资料分块');args.add_argument('--data-zip',default=r'D:\Users\Administrator\Desktop\导出数据\数据源.zip');args.add_argument('--documents-zip',default=r'D:\Users\Administrator\Desktop\导出数据\医疗文书.zip');opts=args.parse_args();SOURCES=[pathlib.Path(opts.data_zip),pathlib.Path(opts.documents_zip)]
def digest(b):return hashlib.sha256(b).hexdigest()
def encode(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
src={};source_manifest=[]
for p in SOURCES:
 with zipfile.ZipFile(p,metadata_encoding='gbk') as z:
  assert z.testzip() is None
  for i in z.infolist():
   assert not i.filename.startswith(('/','\\')) and '..' not in pathlib.PurePosixPath(i.filename).parts
   if i.is_dir():continue
   b=z.read(i);source_manifest.append(dict(archive=p.name,path=i.filename,bytes=len(b),sha256=digest(b)))
   if p==SOURCES[0]:src[i.filename]=b
source_hash={p.name:digest(p.read_bytes()) for p in SOURCES}
version='v1-'+digest(encode(source_hash))[:16]; records=collections.defaultdict(list);maps=[];dups={};missing=[];transform=[]
def loc(path,**kw):return dict(file=path,**kw)
def add(module,title,category,raw,locator,**extra):
 locator_json=json.dumps(locator,ensure_ascii=False,sort_keys=True)
 rid=module+'-'+digest(locator_json.encode())[:20]
 pin=lazy_pinyin(title,errors='default')
 r=dict(id=rid,key=version+'|'+rid,module=module,moduleKey=version+'|'+module,version=version,title=title,category=category,raw=raw,locator=locator,sourceHash=next(x['sha256'] for x in source_manifest if x['path']==locator['file']),contentHash=digest(encode(raw)),pinyin=''.join(pin),initials=''.join(x[0] for x in pin if x),**extra)
 records[module].append(r);return r
op=next(k for k in src if k.startswith('临床医嘱/') and k.endswith('.json'));orders=json.loads(src[op]);assert len(orders['diseases'])==orders['count']
for i,r in enumerate(orders['diseases']):
 add('orders',r['name'],r['category'],r,loc(op,arrayRow=i+1),flags=r.get('data_flags',[]),emptySymptoms=not r.get('symptoms'))
tp=next(k for k in src if k.startswith('门诊住院病历模板/') and k.endswith('.json'));templates=json.loads(src[tp])['diseases']
out={'主诉','现病史','既往史','个人史及过敏史','体格检查','辅助检查','初步诊断','处理方案'};ins={'入院记录','首次病程记录','出院记录','主治医师查房记录','主任医师查房记录','手术记录','术前小结','术前讨论'}
for i,x in enumerate(templates):
 for j,c in enumerate(x['cases']):
  ks=set(c['templates']);a=out<=ks;b=bool(ks&ins);setting='mixed' if a and b else 'out' if a else 'in' if b else 'shared'
  r=add('templates',x['name'],x['category'],dict(name=x['name'],category=x['category'],case=c),loc(tp,arrayRow=i+1,caseRow=j+1),setting=setting,caseName=c['case_name'],templateNames=list(c['templates']),emptyTemplates=[k for k,v in c['templates'].items() if not v],escapedNewlines=[k for k,v in c['templates'].items() if '\\n' in v])
  maps.append(dict(id=r['id'],locator=r['locator'],name=x['name'],category=x['category'],setting=setting,keys=list(c['templates'])))
dp=next(k for k in src if k.endswith('Drug.xlsx'));fw=openpyxl.load_workbook(io.BytesIO(src[dp]),data_only=False);vw=openpyxl.load_workbook(io.BytesIO(src[dp]),data_only=True);s=vw['Sheet1'];f=fw['Sheet1'];headers=[c.value for c in s[1]]
formula_count=0
for row in range(2,s.max_row+1):
 values={h:s.cell(row,col+1).value for col,h in enumerate(headers)};formulas={}
 for col in range(1,14):
  c=f.cell(row,col)
  if c.data_type=='f':
   assert re.fullmatch(r'="(?:[^"]|"")*"',c.value)
   formula_count+=1;formulas[c.coordinate]=c.value
   if values[headers[col-1]] is None:values[headers[col-1]]=c.value[2:-1].replace('""','"')
 r=add('drugs',values['通用名'],values['类别'],values,loc(dp,sheet='Sheet1',excelRow=row),formulas=formulas,missingDetails=values['主要功效'] is None and values['适应病症'] is None)
 if r['missingDetails']:missing.append(dict(id=r['id'],locator=r['locator'],name=r['title'],category=r['category']))
for p in [k for k in src if k.startswith('急症急救快速通道/') and k.endswith('.xlsx')]:
 w=openpyxl.load_workbook(io.BytesIO(src[p]),data_only=False)
 for s in w:
  assert s.max_column==1
  lines=[s.cell(r,1).value or '' for r in range(1,s.max_row+1)]
  assert all(isinstance(x,str) for x in lines)
  add('emergency',s.title,pathlib.PurePosixPath(p).stem,dict(lines=lines),loc(p,sheet=s.title),flow='流程图' in p)
hp=next(k for k in src if k.endswith('.html'));hs=src[hp].decode('utf-8-sig')
css=re.search(r'<style>(.*?)</style>',hs,re.S).group(1)
assert not re.search(r'url\s*\(|@import|expression\s*\(',css,re.I)
docpat=r'<div class="page">\s*<div class="doc-category">(.*?)</div>\s*<div class="doc-title">(.*?)</div>\s*<div class="doc-content">(.*?)</div>\s*</div>'
for i,m in enumerate(re.finditer(docpat,hs,re.S)):
 fragment=m.group(0);dom=lh.fromstring(fragment)
 for n in dom.iter():
  assert n.tag in ['div','br'],n.tag
  assert all(k in ['class'] for k in n.attrib),n.attrib
 plain=re.sub(r'<br\s*/?>','\n',m.group(3));plain=html.unescape(re.sub(r'<[^>]*>','',plain))
 add('documents',html.unescape(m.group(2)),html.unescape(m.group(1)).strip('【】'),dict(fragment=fragment,css=css,text=plain),loc(hp,documentRow=i+1,line=hs[:m.start()].count('\n')+1))
assert len(records['documents'])==332
for module,rr in records.items():
 byname=collections.defaultdict(list);bybody=collections.defaultdict(list)
 for r in rr:byname[r['title']].append(r['id']);bybody[r['contentHash']].append(r['id'])
 groups=[v for v in bybody.values() if len(v)>1]
 for group in groups:
  for r in rr:
   if r['id'] in group:r['duplicateIds']=group
 dups[module]=dict(sameName=[dict(name=k,ids=v) for k,v in byname.items() if len(v)>1],exactBodies=groups)
chunks=[]
for module in ['emergency','orders','drugs','templates','documents']:
 batch=[];size=0;n=0
 def flush(batch,n):
  b=encode(batch);url=f'data/{module}-{n:03d}.json';(DIST/url).write_bytes(b);chunks.append(dict(module=module,url=url,count=len(batch),bytes=len(b),sha256=digest(b)))
 for r in records[module]:
  b=encode(r)
  if batch and size+len(b)>650000:flush(batch,n);batch=[];size=0;n+=1
  batch.append(r);size+=len(b)
 if batch:flush(batch,n)
manifest=dict(version=version,appVersion='1.0.0',date='2026-11-11',sources=source_manifest,archiveHashes=source_hash,sourceMetadata=dict(orders={k:v for k,v in orders.items() if k!='diseases'},templateRootKeys=['diseases']),counts={k:len(v) for k,v in records.items()},categories={k:dict(collections.Counter(r['category'] for r in v)) for k,v in records.items()},chunks=chunks,details=dict(topLevelTemplates=len(templates),caseCount=len(maps),templateFields=sum(len(c['templates']) for x in templates for c in x['cases']),templateKeys=len(set(k for x in templates for c in x['cases'] for k in c['templates'])),formulaCells=formula_count,missingDrugDetails=len(missing),emptySymptoms=sum(not x['symptoms'] for x in orders['diseases']),settings=dict(collections.Counter(x['setting'] for x in maps))))
(DATA/'manifest.json').write_bytes(encode(manifest))
(ROOT/'reports/source-manifest.json').write_bytes(encode(manifest));(ROOT/'reports/setting-map.json').write_bytes(encode(maps));(ROOT/'reports/duplicates.json').write_bytes(encode(dups));(ROOT/'reports/missing-drugs.json').write_bytes(encode(missing))
(ROOT/'reports/html-safety.json').write_bytes(encode(dict(documents=332,allowedTags=['div','br'],allowedAttributes=['class'],externalResources=0,sourceChanged=False,toolBehaviorRemoved='源末尾打印按钮不进入逐篇正文；应用使用受控打印按钮。',cssHash=digest(css.encode()),sourceHash=digest(src[hp]))))
print(json.dumps(dict(version=version,counts=manifest['counts'],details=manifest['details'],chunks=len(chunks),bytes=sum(c['bytes'] for c in chunks)),ensure_ascii=False))
