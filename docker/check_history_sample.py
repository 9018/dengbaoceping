import json, urllib.request
ES='http://127.0.0.1:9200'
q={'size':50,'_source':['template_name','sheet_name','indicator_l2','indicator_l3']}
req=urllib.request.Request(ES+'/assessment_history/_search',data=json.dumps(q,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=60) as r:
    res=json.loads(r.read().decode('utf-8'))
for i,h in enumerate(res.get('hits',{}).get('hits',[]),1):
    s=h.get('_source',{})
    print(i, s.get('template_name','<none>'), '|', s.get('sheet_name','<none>'), '|', s.get('indicator_l2',''))
