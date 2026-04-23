import json
from pathlib import Path

def domain_of(s):
    s=(s or '').strip()
    if (not s): return '其他'
    if any(k in s for k in ['物理','防火','防盗','防雷','防水','温湿度','电力','电磁','防静电']): return '物理环境'
    if any(k in s for k in ['通信','网络架构']): return '安全通信网络'
    if '边界' in s: return '安全区域边界'
    if any(k in s for k in ['身份鉴别','访问控制','入侵防范','恶意代码','审计','剩余信息','数据','配置','可信验证','计算','镜像']): return '安全计算环境'
    if any(k in s for k in ['集中管控','安全管理中心','安全策略']): return '安全管理中心'
    if any(k in s for k in ['管理制度','制定和发布','评审和修订']): return '安全管理制度'
    if any(k in s for k in ['管理机构','岗位设置','授权和审批']): return '安全管理机构'
    if any(k in s for k in ['管理人员','人员录用','人员离岗','意识教育']): return '安全管理人员'
    if any(k in s for k in ['建设','方案设计','产品采购','自行软件开发','外包软件开发','工程实施','测试验收','系统交付','等级测评','服务供应商','供应链']): return '安全建设管理'
    if any(k in s for k in ['运维','介质管理','设备维护','漏洞','变更管理','备份','应急','外包运维','资产管理','密码管理','网络和系统安全管理']): return '安全运维管理'
    if '云' in s: return '云扩展'
    return '其他'

rows=json.loads(Path('/opt/cpgj/exports/indicator_preview.json').read_text(encoding='utf-8'))
others=[r.get('level2','') for r in rows if domain_of(r.get('level2',''))=='其他']
print('other_count', len(others))
for x in others:
    print(x)
