import hashlib,json,pathlib,re,struct,zipfile,base64
root=pathlib.Path(__file__).parent
dist=root.parent/'dist'
out=root.parent/'offline'
out.mkdir(exist_ok=True)
mf=json.loads((dist/'data/manifest.json').read_text('utf-8'))
headers=[]
for p in sorted((dist/'data').glob('catalog-part-*.js')):
    s=p.read_text('utf-8');headers.extend(json.loads(s[s.index(',')+1:s.rindex(');')]))
entries={};bodies=[];offset=0
for c in mf['chunks']:
    s=(dist/c['url']).read_text('utf-8');body=s[s.index(',')+1:s.rindex(');')].encode()
    assert hashlib.sha256(body).hexdigest()==c['sha256']
    entries[c['url']]={'offset':offset,'bytes':len(body)};bodies.append(body);offset+=len(body)
index=json.dumps({'manifest':mf,'headers':headers,'entries':entries,'bodyBytes':offset},ensure_ascii=False,separators=(',',':')).encode()
pack=out/'临床资料.clinicalpack'
with pack.open('wb') as f:
    f.write(b'CLINPK01'+struct.pack('<I',len(index))+index)
    for b in bodies:f.write(b)
html=(dist/'index.html').read_text('utf-8')
html=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]+>', '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; frame-src blob:; img-src data:; connect-src \'none\'; object-src \'none\'; base-uri \'none\'; form-action \'none\'">',html)
html=re.sub(r'<link[^>]+>','',html)
icon=base64.b64encode((dist/'icons/icon.svg').read_bytes()).decode()
html=html.replace('</head>','<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,'+icon+'"></head>')
html=re.sub(r'<script defer[^>]+></script>','',html)
html=html.replace('</head>','<style>'+(dist/'app.css').read_text('utf-8')+'\n#packGate{max-width:560px;width:calc(100% - 32px);padding:28px;border:0;border-radius:16px}#packGate::backdrop{background:#e8eee8}#packFile{max-width:100%;margin:16px 0}#packMessage{overflow-wrap:anywhere}</style></head>')
gate='''<dialog id="packGate" aria-labelledby="packTitle"><h1 id="packTitle">导入离线临床资料</h1><p>主程序已完整保存在本网页，无需联网。请选择配套的“临床资料.clinicalpack”。资料分块校验后即可查阅。</p><label for="packFile">选择离线数据包</label><input id="packFile" type="file" accept=".clinicalpack,application/octet-stream"><p><label><input id="packSave" type="checkbox" checked> 尝试保存在本机，下次直接使用</label></p><p>若浏览器不允许保存，下次重新选择数据包即可。请始终保留原数据包；资料不会上传。</p><p id="packMessage" role="status" aria-live="polite">正在检查本机保存状态…</p></dialog>'''
gate=gate.replace('accept=".clinicalpack,application/octet-stream"','accept="*/*"')
html=html.replace('<noscript>',gate+'<noscript>')
portable=(dist/'portable.js').read_text('utf-8').replace("const enabled=location.protocol==='file:';","const enabled=true;")
app=(dist/'app.js').read_text('utf-8').replace('全部资料随包提供，无需联网或导入，按需读取。','离线数据包已载入，无需联网，正文按需读取。').replace('本版不需安装、联网或导入。请保留完整文件夹，双击网页即可使用。','本版无需联网。请保留主程序与数据包；浏览器未保存时重新选择数据包即可。')
start=app.index('function portableSettings()')
app=app[:start]+'''function portableSettings(){$('#view').innerHTML='<div class="welcome"><h1>离线数据包与设置</h1></div><div class="panel"><h2>资料完全本地使用</h2><p>全部7752条资料已载入目录，正文按需读取，最多暂存两个分块。急救始终免密码，其余模块仅锁定界面。</p><p>'+ (window.singlePackSaved?'浏览器已保存数据包；清理浏览器数据或更换打开路径可能需要重新导入。':'当前使用临时数据包；下次打开时请重新选择。')+'</p><button class="outline" data-action="prepare">逐块核验数据包</button><progress max="100" value="'+state.progress+'"></progress><p class="progress-msg">'+esc(state.progressMessage)+'</p><button class="outline" id="changePack">重新选择数据包</button><p>此按钮清除本应用保存的数据包并重新打开选择页，不会修改原数据包文件。</p><h2>自动锁定</h2><label for="idleSelect">闲置多久后锁定</label><select id="idleSelect"><option value="0">不自动锁定</option><option value="5">5 分钟</option><option value="15">15 分钟</option><option value="30">30 分钟</option></select><p>刷新后默认锁定；界面锁不加密资料。</p><h2>手机使用</h2><p>请用支持脚本和文件选择的浏览器打开本HTML，文件管理器的预览模式可能无法运行。打印需设备提供打印服务；复制受限时可手动选择文本。</p></div>';$('#idleSelect').value=String(state.idle);$('#changePack').onclick=()=>SinglePack.forget();}\n'''
adapter=(root/'single-pack.js').read_text('utf-8').replace('__INDEX_SHA__',hashlib.sha256(index).hexdigest())
scripts=[(dist/'db.js').read_text('utf-8'),(dist/'search-core.js').read_text('utf-8'),adapter,portable,app]
html=html.replace('</body>', ''.join('<script>'+s.replace('</script','<\\/script')+'</script>' for s in scripts)+'</body>')
(out/'临床工作站.html').write_text(html,encoding='utf-8')
print(json.dumps({'headers':len(headers),'chunks':len(bodies),'htmlBytes':(out/'临床工作站.html').stat().st_size,'packBytes':pack.stat().st_size},ensure_ascii=False))
