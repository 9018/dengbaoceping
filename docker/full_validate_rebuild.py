import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib import request

ES = 'http://127.0.0.1:9200'
OUT_DIR = Path('/opt/cpgj/exports')
OUT_DETAIL = OUT_DIR / 'indicator_detail_preview.json'
OUT_SUM = OUT_DIR / 'indicator_preview.json'
OUT_REPORT = OUT_DIR / '标准核验报告.md'

DOMAIN_ORDER = [
    '安全物理环境', '安全通信网络', '安全区域边界', '安全计算环境', '安全管理中心',
    '安全管理制度', '安全管理机构', '安全管理人员', '安全建设管理', '安全运维管理',
    '云扩展',
]

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
    '安全运维管理': ['环境管理','资产管理','介质管理','设备维护管理','漏洞和风险管理','网络和系统安全管理','恶意代码防范管理','配置管理','密码管理','变更管理','备份与恢复管理','安全事件处置','应急预案管理','外包运维管理'],
}

AMBIGUOUS_L2 = {'访问控制', '入侵防范', '安全审计', '可信验证'}
SKIP_L2 = {'', '二级测评指标', '控制点'}
SKIP_L3 = {'', '三级测评指标', '测评项'}


def post(path, body):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = request.Request(ES + path, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def norm(s):
    s = (s or '').strip()
    s = re.sub(r'\s+', ' ', s)
    s = s.rstrip('；;。.')
    return s.strip()


def infer_ext(l2, l3):
    s = f"{l2}{l3}"
    if '云' in s or '虚拟机' in s:
        return 'cloud'
    if any(k in s for k in ['移动互联', '移动终端', '无线接入', 'APP', 'app', '手机']):
        return 'mobile'
    if any(k in s for k in ['物联网', '传感', '感知层', 'RFID', 'rfid']):
        return 'iot'
    if any(k in s for k in ['工业控制', '工控', 'PLC', 'plc', 'DCS', 'SCADA', 'scada']):
        return 'industrial'
    return 'general'


def base_domain_by_l2(l2):
    for d, arr in BASE_L2.items():
        if any(x in l2 for x in arr):
            return d
    if '云' in l2:
        return '云扩展'
    return '安全计算环境'


def classify_domain(l1, l2, l3, ext):
    l1, l2, l3 = norm(l1), norm(l2), norm(l3)
    if ext == 'cloud':
        return '云扩展'
    if l2 not in AMBIGUOUS_L2:
        if l1 in DOMAIN_ORDER:
            return l1
        return base_domain_by_l2(l2)

    s = l3
    boundary_kw = ['边界', '区域', '数据包', '会话状态', '源地址', '目的地址', '端口', '协议', '受控接口', '网络之间', '进出']
    compute_kw = ['账户', '权限', '默认账户', '口令', '进程', '主体', '客体', '文件', '数据库', '登录', '鉴别', '系统资源']
    if any(k in s for k in boundary_kw):
        return '安全区域边界'
    if any(k in s for k in compute_kw):
        return '安全计算环境'

    if l1 == '安全区域边界':
        return '安全区域边界'
    if l1 == '安全计算环境':
        return '安全计算环境'
    return '安全计算环境'


def l2_order(domain, l2):
    arr = BASE_L2.get(domain, [])
    for i, x in enumerate(arr):
        if x in l2:
            return i
    return 999


res = post('/assessment_history/_search', {
    'size': 10000,
    '_source': ['template_name', 'sheet_name', 'indicator_l1', 'indicator_l2', 'indicator_l3'],
    'query': {'match_all': {}},
})

hits = [h.get('_source', {}) for h in res.get('hits', {}).get('hits', [])]
rows_src = len(hits)

rows = []
for r in hits:
    tn = norm(r.get('template_name'))
    if '二级' not in tn or '三级' in tn:
        continue
    l1 = norm(r.get('indicator_l1'))
    l2 = norm(r.get('indicator_l2'))
    l3 = norm(r.get('indicator_l3'))
    if l2 in SKIP_L2 or l3 in SKIP_L3:
        continue
    if not re.match(r'^[A-Za-z][\)\）\.]', l3):
        continue
    ext = infer_ext(l2, l3)
    domain = classify_domain(l1, l2, l3, ext)
    rows.append({'extension_type': ext, 'domain': domain, 'level2': l2, 'level3': l3})

seen = set()
clean = []
for r in rows:
    k = (r['extension_type'], r['domain'], r['level2'], r['level3'])
    if k in seen:
        continue
    seen.add(k)
    clean.append(r)

# summary: 基线全量补齐 + 实际数量回填
agg = {}
for d, l2s in BASE_L2.items():
    for l2 in l2s:
        agg[(d, l2)] = {'domain': d, 'level2': l2, 'general_count': 0, 'cloud_count': 0, 'mobile_count': 0, 'iot_count': 0, 'industrial_count': 0, 'total_count': 0}

for r in clean:
    key = (r['domain'], r['level2'])
    if key not in agg:
        agg[key] = {'domain': r['domain'], 'level2': r['level2'], 'general_count': 0, 'cloud_count': 0, 'mobile_count': 0, 'iot_count': 0, 'industrial_count': 0, 'total_count': 0}
    ext = r.get('extension_type') or 'general'
    agg[key]['total_count'] += 1
    if ext == 'cloud':
        agg[key]['cloud_count'] += 1
    elif ext == 'mobile':
        agg[key]['mobile_count'] += 1
    elif ext == 'iot':
        agg[key]['iot_count'] += 1
    elif ext == 'industrial':
        agg[key]['industrial_count'] += 1
    else:
        agg[key]['general_count'] += 1

summary = list(agg.values())
summary.sort(key=lambda x: (DOMAIN_ORDER.index(x['domain']) if x['domain'] in DOMAIN_ORDER else 999, l2_order(x['domain'], x['level2']), x['level2']))
clean.sort(key=lambda x: (DOMAIN_ORDER.index(x['domain']) if x['domain'] in DOMAIN_ORDER else 999, l2_order(x['domain'], x['level2']), x['level2'], x['level3']))

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_DETAIL.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding='utf-8')
OUT_SUM.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

id_items = sorted({r['level3'] for r in clean if r['domain'] == '安全计算环境' and r['level2'] == '身份鉴别'})
ac_compute = sorted({r['level3'] for r in clean if r['domain'] == '安全计算环境' and r['level2'] == '访问控制'})
ac_boundary = sorted({r['level3'] for r in clean if r['domain'] == '安全区域边界' and r['level2'] == '访问控制'})

lines = []
lines.append('# 标准对照核验报告（全量重建）')
lines.append('')
lines.append(f'- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
lines.append('- 核验口径：二级模板全量读取 + 三级条款去重 + 重名二级项分域 + 基线补齐')
lines.append(f'- 原始记录总行数：{rows_src}')
lines.append(f'- 二级模板过滤后：{len(rows)}')
lines.append(f'- 去重后三级条款数：{len(clean)}')
lines.append(f'- 预览二级项总数（含0数量补齐）：{len(summary)}')
lines.append('')
lines.append('## 关键核验点')
lines.append(f'- 安全计算环境/身份鉴别：{len(id_items)} 项（应为3项）')
lines.append(f'- 安全计算环境/访问控制：{len(ac_compute)} 项')
lines.append(f'- 安全区域边界/访问控制：{len(ac_boundary)} 项')
lines.append('')
lines.append('## 修复动作')
lines.append('1. 修复模板过滤口径，避免空结果。')
lines.append('2. 重名二级项按三级语义分域，不再混到同一领域。')
lines.append('3. 按 GB/T 22239 二级基线补齐零数量项，保证顺序完整。')
OUT_REPORT.write_text('\n'.join(lines), encoding='utf-8')

print(json.dumps({
    'rows_src': rows_src,
    'rows_filtered': len(rows),
    'rows_clean': len(clean),
    'summary_rows': len(summary),
    'id_count': len(id_items),
    'ac_compute': len(ac_compute),
    'ac_boundary': len(ac_boundary),
}, ensure_ascii=False))
