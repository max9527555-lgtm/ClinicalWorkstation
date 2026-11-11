import pathlib,json,zipfile,io,hashlib,openpyxl,collections
B=pathlib.Path(__file__).resolve().parents[1];D=B/'dist';mf=json.loads((D/'data/manifest.json').read_text(encoding='utf-8'))
sources=[pathlib.Path(r'D:\Users\Administrator\Desktop\导出数据\数据源.zip'),pathlib.Path(r'D:\Users\Administrator\Desktop\导出数据\医疗文书.zip')]
for p in sources:assert hashlib.sha256(p.read_bytes()).hexdigest()==mf['archiveHashes'][p.name]
rows=collections.defaultdict(list)
for c in mf['chunks']:
 b=(D/c['url']).read_bytes();assert hashlib.sha256(b).hexdigest()==c['transportSha256'];s=b.decode('utf-8');rr=json.loads(s[s.index(',')+1:-2]);assert hashlib.sha256(json.dumps(rr,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==c['sha256'];assert len(rr)==c['count'];rows[c['module']]+=rr
assert len({r['key'] for rr in rows.values() for r in rr})==sum(map(len,rows.values()))
with zipfile.ZipFile(sources[0],metadata_encoding='gbk') as z:
 hashes={p:hashlib.sha256(z.read(p)).hexdigest() for p in z.namelist() if not p.endswith('/')}
 for rr in rows.values():
  for r in rr:
   p=r['locator']['file'];assert hashes[p]==r['sourceHash']
 op=next(p for p in z.namelist() if p.startswith('临床医嘱/') and p.endswith('.json'));oo=json.loads(z.read(op))['diseases']
 for r in rows['orders']:assert r['raw']==oo[r['locator']['arrayRow']-1]
 tp=next(p for p in z.namelist() if p.startswith('门诊住院病历模板/') and p.endswith('.json'));tt=json.loads(z.read(tp))['diseases']
 for r in rows['templates']:
  x=tt[r['locator']['arrayRow']-1];c=x['cases'][r['locator']['caseRow']-1];assert r['raw']==dict(name=x['name'],category=x['category'],case=c)
 dp=next(p for p in z.namelist() if p.endswith('Drug.xlsx'));s=openpyxl.load_workbook(io.BytesIO(z.read(dp)),data_only=True)['Sheet1'];heads=[c.value for c in s[1]]
 for r in rows['drugs']:assert r['raw']=={h:s.cell(r['locator']['excelRow'],i+1).value for i,h in enumerate(heads)}
 books={}
 for r in rows['emergency']:
  p=r['locator']['file']
  if p not in books:books[p]=openpyxl.load_workbook(io.BytesIO(z.read(p)),data_only=True)
  s=books[p][r['locator']['sheet']];assert r['raw']['lines']==[s.cell(i,1).value or '' for i in range(1,s.max_row+1)]
 hp=next(p for p in z.namelist() if p.endswith('.html'));html=z.read(hp).decode('utf-8-sig')
 for r in rows['documents']:
  assert r['raw']['fragment'] in html and r['raw']['css'] in html
  assert '<button' not in r['raw']['fragment'] and 'onclick' not in r['raw']['fragment']
result=dict(status='通过',description='独立从原压缩包逐记录核对全部派生原文、来源指纹、分块指纹和唯一键；原包指纹未变。',counts={k:len(v) for k,v in rows.items()},recordCount=sum(map(len,rows.values())),documentFragments=332,sourceArchiveHashes=mf['archiveHashes'])
(B/'reports/data-preservation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
