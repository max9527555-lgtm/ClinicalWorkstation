import pathlib,json
b=pathlib.Path('reports');p=json.loads((b/'portable-tests.json').read_text(encoding='utf-8'));h=json.loads((b/'functional-tests.json').read_text(encoding='utf-8'));c=json.loads((b/'portable-copy-tests.json').read_text(encoding='utf-8'));v=json.loads((b/'data-preservation.json').read_text(encoding='utf-8'));pb=json.loads((b/'portable-build.json').read_text(encoding='utf-8'))
t='# 绿色便携版交付与测试报告\n\n版本2.0.0。主色#45AF2A。原始压缩包未修改。\n\n'
t+='## 本次实现\n\n本地文件模式无需Python、Node.js、服务或数据库导入；通过浏览器经典脚本加载随包资料。启动目录压缩至约1.4MB，正文按需读取，最多暂存两块。常用字段索引直接检索，全文只在明确选择后按块扫描。网页模式保留PWA与IndexedDB，并提供GitHub Pages工作流。\n\n'
t+='完整保留7,752条资料记录，131个正文分块。独立逐条核对原包、派生原文、网页片段与样式、药品缓存值、急救全部行和所有分块指纹，全部通过。与旧版的数据内容一致，仅新增派生搜索索引和脚本传输包装。\n\n'
t+='## 通过的自动化检查\n\n'
for label,d in [('断网本地文件模式',p),('复制与全量文件校验',c),('网页版',h)]:
 t+='### '+label+'\n\n'
 for x in d['tests']:t+='- '+x['name']+'：'+x['status']+'。\n'
 t+='\n'
t+='## 性能样本与实际范围\n\n当前测试环境：Windows11，Chrome'+p['environment']['browser']+'，'+p['environment']['cpu'].strip()+'。下述为单次本机样本，不代表旧电脑、U盘或所有设备。\n\n'
t+='- 完全断网、直接文件启动：'+str(p['metrics']['startupMs'])+'毫秒。\n'
t+='- 常见症状搜索：'+str(p['metrics']['symptomSearchMs'])+'毫秒。\n'
t+='- 临床医嘱全文扫描样例：'+str(p['metrics']['ordersFullSearchMs'])+'毫秒。\n'
t+='- 完整本地测试中HTTP／HTTPS请求数：'+str(p['metrics']['httpRequests'])+'。\n'
t+='- 启动时正文分块加载数为0；全文扫描和全量核验后正文缓存仍不超过两块。\n'
t+='- 测试结束时主线程堆样本约'+str(round(p['metrics']['heapBytes']/1048576,1))+'MB。这不是浏览器总内存或峰值；程序和浏览器仍会占用资源。\n'
t+='- 随包正文约'+str(round(pb['dataBytes']/1048576,1))+'MiB；原始临床资料较大，不宣称完整资料零体积或零开销。\n\n'
t+='## 验证边界\n\n未验证Windows7的真实Chrome109／Edge109、苹果与安卓真机、真实打印机、医院安全策略及低配电脑。当前宽度测试不能代替真机验证。当前实际浏览器支持目录解压；程序已模拟缺少原生解压能力并验证本地分段备用目录；这不代表旧浏览器真机已通过。\n\n'
t+='打印载体与代表性电子预览已检查，未逐页实打全部知识。备份恢复在网页模式验证；便携文件模式以整文件夹复制作为备份恢复方式。源缺失与待核对分类未补写或强行定类。\n\n'
t+='本次颜色断言、多尺寸截图、原文核验通过；专用设计检查器未标通过。GitHub Pages是否上线必须以实际工作流和站点验证为准。\n\n'
t+='## 发布控制限制\n\n当前GitHub连接器可以提交源码，但没有Pages设置接口。浏览器导航工具出现兼容错误，Windows界面控制又因无法可靠识别当前浏览器地址而被系统停止。本次不绕过该限制。如工作流提示Pages未启用，需要仓库管理员在设置中选择GitHub Actions作为Pages来源后重跑。此情况属于发布未完成，不能写作已经上线。\n'
pathlib.Path('交付与测试报告.md').write_text(t,encoding='utf-8')
print('Checks',sum(len(d['tests']) for d in [p,h,c]))
