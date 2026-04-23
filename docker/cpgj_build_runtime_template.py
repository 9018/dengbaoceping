import json, urllib.request
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

# index
try:
    put('/record_template_v2', {'mappings': {'properties': {
      'extension_type': {'type':'keyword'},
      'level2': {'type':'keyword'},
      'level3_list': {'type':'text'},
      'level3_count': {'type':'integer'},
      'updated_at': {'type':'date'}
    }}})
except Exception:
    pass

res=post('/indicator_catalog/_search',{'size':5000,'_source':['extension_type','level2','level3']})
rows=[h.get('_source',{}) for h in res.get('hits',{}).get('hits',[])]

bucket={}
for r in rows:
    ext=(r.get('extension_type') or 'general').strip()
    l2=(r.get('level2') or '').strip()
    l3=(r.get('level3') or '').strip()
    if not l2 or not l3:
        continue
    k=(ext,l2)
    bucket.setdefault(k,set()).add(l3)

now=datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
lines=[]
for (ext,l2), s in sorted(bucket.items()):
    l3s=sorted(s)
    did=(ext+'|'+l2)
    lines.append(json.dumps({'index':{'_index':'record_template_v2','_id':did}},ensure_ascii=False))
    lines.append(json.dumps({
      'extension_type': ext,
      'level2': l2,
      'level3_list': l3s,
      'level3_count': len(l3s),
      'updated_at': now
    },ensure_ascii=False))

rb=bulk(lines)
print(json.dumps({'rows':len(bucket),'errors':rb.get('errors',True)},ensure_ascii=False))
