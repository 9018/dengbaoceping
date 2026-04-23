import json, urllib.request
from pathlib import Path

ES='http://127.0.0.1:9200'
OUT_DETAIL='/opt/cpgj/exports/indicator_detail_preview.json'
OUT_SUM='/opt/cpgj/exports/indicator_preview.json'


def post(path, body):
    data=json.dumps(body, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(ES+path,data=data,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def infer_ext(level2, level3, old):
    s=((level2 or '')+' '+(level3 or '')).lower()
    s_zh=(level2 or '')+(level3 or '')
    if '云' in s_zh or old=='cloud':
        return 'cloud'
    if any(k in s_zh for k in ['移动互联','移动终端','无线接入','app','手机']):
        return 'mobile'
    if any(k in s_zh for k in ['物联网','传感','感知层','rfid','标签识别']):
        return 'iot'
    if any(k in s_zh for k in ['工业控制','工控','plc','dcs','scada']):
        return 'industrial'
    return 'general'

res=post('/indicator_catalog/_search',{
  'size':5000,
  '_source':['extension_type','level2','level3'],
  'sort':[{'level2':'asc'}]
})

rows=[]
for h in res.get('hits',{}).get('hits',[]):
    s=h.get('_source',{})
    l2=(s.get('level2') or '').strip()
    l3=(s.get('level3') or '').strip()
    if not l2 or not l3:
        continue
    ext=infer_ext(l2,l3,(s.get('extension_type') or '').strip())
    rows.append({'extension_type':ext,'level2':l2,'level3':l3})

# 去重
uniq=[]
seen=set()
for r in rows:
    k=(r['extension_type'],r['level2'],r['level3'])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)

# 汇总（兼容旧接口）
agg={}
for r in uniq:
    l2=r['level2']
    if l2 not in agg:
        agg[l2]={'level2':l2,'general_count':0,'cloud_count':0,'total_count':0}
    if r['extension_type']=='cloud':
        agg[l2]['cloud_count']+=1
    elif r['extension_type']=='general':
        agg[l2]['general_count']+=1
    agg[l2]['total_count']+=1

Path('/opt/cpgj/exports').mkdir(parents=True, exist_ok=True)
Path(OUT_DETAIL).write_text(json.dumps(uniq, ensure_ascii=False, indent=2), encoding='utf-8')
Path(OUT_SUM).write_text(json.dumps(sorted(agg.values(), key=lambda x:x['level2']), ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'detail_rows':len(uniq),'l2_rows':len(agg),'out_detail':OUT_DETAIL}, ensure_ascii=False))
