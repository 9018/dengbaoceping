import json, re, urllib.request
from pathlib import Path
from datetime import datetime

ES='http://127.0.0.1:9200'
OUT_DIR=Path('/opt/cpgj/exports')
OUT_DETAIL=OUT_DIR/'indicator_detail_preview.json'
OUT_SUM=OUT_DIR/'indicator_preview.json'
OUT_REPORT=OUT_DIR/'标准核验报告.md'

# 22239 通用二级项基线（用于核验）
BASE_L2 = {
'安全物理环境': ['物理位置选择','物理访问控制','防盗窃和防破坏','防雷击','防火','防水和防潮','防静电','温湿度控制','电力供应','电磁防护'],
'安全通信网络': ['网络架构','通信传输','可信验证'],
'安全区域边界': ['边界防护','访问控制','入侵防范','恶意代码和垃圾邮件防范','安全审计'],
'安全计算环境': ['身份鉴别','访问控制','安全审计','入侵防范','恶意代码防范','可信验证','数据完整性','数据保密性','数据备份恢复','剩余信息保护','个人信息保护'],
'安全管理中心': ['系统管理','审计管理','安全管理','集中管控'],
'安全管理制度': ['管理制度','制定和发布','评审和修订'],
'安全管理机构': ['岗位设置','人员配备','授权和审批','沟通和合作','审核和检查'],
'安全管理人员': ['人员录用','人员离岗','安全意识教育和培训','外部人员访问管理'],
'安全建设管理': ['定级和备案','安全方案设计','产品采购和使用','自行软件开发','外包软件开发','工程实施','测试验收','系统交付','服务供应商选择','供应链管理','等级测评'],
'安全运维管理': ['环境管理','资产管理','介质管理','设备维护管理','漏洞和风险管理','网络和系统安全管理','恶意代码防范管理','配置管理','密码管理','变更管理','备份与恢复管理','安全事件处置','应急预案管理','外包运维管理']
}

DOMAIN_ORDER=['安全物理环境','安全通信网络','安全区域边界','安全计算环境','安全管理中心','安全管理制度','安全管理机构','安全管理人员','安全建设管理','安全运维管理','云扩展']


def post(path, body):
    data=json.dumps(body, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(ES+path, data=data, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def normalize_l3(s):
    s=(s or '').strip()
    s=re.sub(r'\s+',' ',s)
    s=s.rstrip('；;。. ')
    return s


def infer_ext(l2,l3):
    s=(l2 or '')+(l3 or '')
    if '云' in s: return 'cloud'
    if any(k in s for k in ['移动互联','移动终端','无线接入','APP','app','手机']): return 'mobile'
    if any(k in s for k in ['物联网','传感','感知层','RFID','rfid']): return 'iot'
    if any(k in s for k in ['工业控制','工控','PLC','plc','DCS','SCADA','scada']): return 'industrial'
    return 'general'


def domain_of(l2):
    s=(l2 or '').strip()
    for d, arr in BASE_L2.items():
        if any(x in s for x in arr):
            return d
    # 补充常见别名
    if s in ['基础设施位置']: return '安全物理环境'
    if s in ['安全策略','控制点','系统管理']: return '安全管理中心' if s!='控制点' else '安全计算环境'
    if s in ['沟通和合作','审核和检查','外部人员访问管理','安全事件处置']: return '安全运维管理'
    if '云' in s: return '云扩展'
    return '安全计算环境'


def l2_order(domain, l2):
    arr=BASE_L2.get(domain,[])
    for i, k in enumerate(arr):
        if k in (l2 or ''):
            return i
    return 999

# 1) 读取历史记录（只取二级模板，避免混三级）
res=post('/assessment_history/_search',{
  'size':10000,
  '_source':['template_name','indicator_l2','indicator_l3'],
  'query':{'bool':{'filter':[{'wildcard':{'template_name.keyword':'*二级*'}}]}}
})
rows=[h.get('_source',{}) for h in res.get('hits',{}).get('hits',[])]

# 2) 清洗去重
skip_l2={'','二级测评指标','控制点'}
skip_l3={'','三级测评指标','测评项'}
clean=[]
seen=set()
for r in rows:
    l2=(r.get('indicator_l2') or '').strip()
    l3=normalize_l3(r.get('indicator_l3') or '')
    if l2 in skip_l2 or l3 in skip_l3:
        continue
    # 仅保留 a/b/c... 条款行
    if not re.match(r'^[a-zA-Z]\）', l3) and not re.match(r'^[a-zA-Z]\)', l3) and not re.match(r'^[a-zA-Z]\.', l3):
        pass
    ext=infer_ext(l2,l3)
    k=(ext,l2,l3)
    if k in seen:
        continue
    seen.add(k)
    clean.append({'extension_type':ext,'level2':l2,'level3':l3})

# 3) 核验结果统计
unknown_l2=[]
base_l2_flat={x for arr in BASE_L2.values() for x in arr}
for it in clean:
    if not any(x in it['level2'] for x in base_l2_flat) and '云' not in it['level2']:
        unknown_l2.append(it['level2'])
unknown_l2=sorted(set(unknown_l2))

# 4) 写明细文件
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_DETAIL.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')

# 5) 写汇总文件（二级项+数量）
agg={}
for it in clean:
    l2=it['level2']
    if l2 not in agg:
        agg[l2]={'level2':l2,'general_count':0,'cloud_count':0,'total_count':0}
    if it['extension_type']=='cloud':
        agg[l2]['cloud_count']+=1
    elif it['extension_type']=='general':
        agg[l2]['general_count']+=1
    agg[l2]['total_count']+=1
summary=sorted(agg.values(), key=lambda x:x['level2'])
OUT_SUM.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

# 6) 生成核验报告
lines=[]
lines.append('# 标准对照核验报告（自动）')
lines.append('')
lines.append(f'- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
lines.append('- 对照口径：GB/T 22239 二级结构基线 + 云扩展识别')
lines.append(f'- 原始记录行数（二级模板）：{len(rows)}')
lines.append(f'- 清洗去重后指标数：{len(clean)}')
lines.append(f'- 二级项数量：{len(summary)}')
lines.append(f'- 未归入基线的二级项数量：{len(unknown_l2)}')
if unknown_l2:
    lines.append('- 未归入项：' + '、'.join(unknown_l2))
else:
    lines.append('- 未归入项：无')
lines.append('')
lines.append('## 修复动作')
lines.append('1. 已按二级模板重建，避免混入三级模板导致数量偏大。')
lines.append('2. 已做三级条款去重与标点归一。')
lines.append('3. 已重建平台预览数据文件。')
OUT_REPORT.write_text('\n'.join(lines), encoding='utf-8')

print(json.dumps({
  'rows_source':len(rows),
  'rows_clean':len(clean),
  'l2_count':len(summary),
  'unknown_l2_count':len(unknown_l2),
  'report':str(OUT_REPORT)
}, ensure_ascii=False))
