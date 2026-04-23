import json, hashlib, urllib.request
from datetime import datetime, UTC

ES='http://127.0.0.1:9200'


def post(path, body):
    data=json.dumps(body, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(ES+path,data=data,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

def put(path, body):
    data=json.dumps(body, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(ES+path,data=data,headers={'Content-Type':'application/json'},method='PUT')
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

def bulk(lines):
    if not lines:
        return {'errors':False}
    data=('\n'.join(lines)+'\n').encode('utf-8')
    req=urllib.request.Request(ES+'/_bulk?refresh=true',data=data,headers={'Content-Type':'application/x-ndjson'},method='POST')
    with urllib.request.urlopen(req,timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))

# 1) 建索引（二级/三级模型）
try:
    put('/indicator_catalog', {
      'mappings': {'properties': {
        'level2': {'type':'keyword'},
        'level3': {'type':'text'},
        'level3_kw': {'type':'keyword','ignore_above':2048},
        'extension_type': {'type':'keyword'},
        'source_template': {'type':'keyword'},
        'source_sheet': {'type':'keyword'},
        'route_domain': {'type':'keyword'},
        'updated_at': {'type':'date'}
      }}
    })
except Exception:
    pass

# 2) 抓取历史数据
res = post('/assessment_history/_search', {
  'size': 5000,
  '_source': ['template_name','sheet_name','indicator_l1','indicator_l2','indicator_l3']
})
hits = [h.get('_source',{}) for h in res.get('hits',{}).get('hits',[])]

catalog={}  # key=(l2,l3,ext)
for s in hits:
    l2=(s.get('indicator_l2') or '').strip()
    l3=(s.get('indicator_l3') or '').strip()
    l1=(s.get('indicator_l1') or '').strip()
    if not l2 or not l3:
        continue

    ext='general'
    if '扩展' in l1 or '云' in l2 or '云' in l3:
        ext='cloud'

    key=(l2,l3,ext)
    if key not in catalog:
        catalog[key]={
            'level2':l2,
            'level3':l3,
            'level3_kw':l3,
            'extension_type':ext,
            'source_template': s.get('template_name',''),
            'source_sheet': s.get('sheet_name',''),
            'route_domain':l2,
            'updated_at': datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
        }

# 3) 回写模型
lines=[]
for v in catalog.values():
    did=hashlib.sha1((v['level2']+'|'+v['level3']+'|'+v['extension_type']).encode('utf-8')).hexdigest()
    lines.append(json.dumps({'index':{'_index':'indicator_catalog','_id':did}},ensure_ascii=False))
    lines.append(json.dumps(v,ensure_ascii=False))
r=bulk(lines)

# 4) 输出统计
s1=post('/indicator_catalog/_search',{'size':0,'aggs':{'ext':{'terms':{'field':'extension_type','size':10}},'l2':{'terms':{'field':'level2','size':200}}}})
print(json.dumps({
  'catalog_total': len(catalog),
  'bulk_errors': r.get('errors', True),
  'extension_types': [b['key'] for b in s1.get('aggregations',{}).get('ext',{}).get('buckets',[])],
  'level2_total': len(s1.get('aggregations',{}).get('l2',{}).get('buckets',[]))
}, ensure_ascii=False))
