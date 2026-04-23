import json, urllib.request
from pathlib import Path

ES='http://127.0.0.1:9200'
OUT='/opt/cpgj/exports/indicator_preview.json'

def post(path, body):
    data=json.dumps(body, ensure_ascii=False).encode('utf-8')
    req=urllib.request.Request(ES+path,data=data,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

res=post('/record_template_v2/_search',{'size':5000,'sort':[{'extension_type':'asc'},{'level2':'asc'}]})
hits=[h.get('_source',{}) for h in res.get('hits',{}).get('hits',[])]

group={}
for s in hits:
    l2=s.get('level2','')
    ext=s.get('extension_type','general')
    c=s.get('level3_count',0)
    group.setdefault(l2,{'level2':l2,'general_count':0,'cloud_count':0,'total_count':0})
    if ext=='cloud':
        group[l2]['cloud_count']=c
    else:
        group[l2]['general_count']=c
    group[l2]['total_count']=group[l2]['general_count']+group[l2]['cloud_count']

rows=sorted(group.values(), key=lambda x:x['level2'])
Path('/opt/cpgj/exports').mkdir(parents=True, exist_ok=True)
Path(OUT).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'rows':len(rows),'out':OUT}, ensure_ascii=False))
