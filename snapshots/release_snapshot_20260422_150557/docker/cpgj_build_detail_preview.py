import json, urllib.request
from pathlib import Path

ES='http://127.0.0.1:9200'
OUT='/opt/cpgj/exports/indicator_detail_preview.json'

def post(path, body):
    data=json.dumps(body, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(ES+path,data=data,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

res=post('/indicator_catalog/_search',{
  'size':5000,
  '_source':['extension_type','level2','level3'],
  'sort':[{'extension_type':'asc'},{'level2':'asc'}]
})
rows=[]
for h in res.get('hits',{}).get('hits',[]):
    s=h.get('_source',{})
    l2=(s.get('level2') or '').strip()
    l3=(s.get('level3') or '').strip()
    if not l2 or not l3:
        continue
    rows.append({
      'extension_type': (s.get('extension_type') or 'general').strip() or 'general',
      'level2': l2,
      'level3': l3
    })

# 去重
uniq=[]
seen=set()
for r in rows:
    k=(r['extension_type'],r['level2'],r['level3'])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)

Path('/opt/cpgj/exports').mkdir(parents=True, exist_ok=True)
Path(OUT).write_text(json.dumps(uniq, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'rows':len(uniq),'out':OUT}, ensure_ascii=False))
