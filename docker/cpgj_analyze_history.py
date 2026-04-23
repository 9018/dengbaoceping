import json, urllib.request

ES = 'http://127.0.0.1:9200'

def post(path, body):
    data = json.dumps(body, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(ES + path, data=data, headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

res = post('/assessment_history/_search', {
    'size': 2000,
    '_source': ['template_name','sheet_name','indicator_l1','indicator_l2','indicator_l3','record_text','conclusion','suggestion'],
    'query': {'match_all': {}}
})

hits = [h.get('_source', {}) for h in res.get('hits',{}).get('hits',[])]
print('sample_count', len(hits))

non_empty_l2 = set()
non_empty_l3 = set()
non_empty_l1 = set()
for s in hits:
    if s.get('indicator_l1'): non_empty_l1.add(s['indicator_l1'])
    if s.get('indicator_l2'): non_empty_l2.add(s['indicator_l2'])
    if s.get('indicator_l3'): non_empty_l3.add(s['indicator_l3'])

print('non_empty_l1', len(non_empty_l1))
print('non_empty_l2', len(non_empty_l2))
print('non_empty_l3', len(non_empty_l3))
print('l2_examples', list(sorted(non_empty_l2))[:30])
print('l3_examples', list(sorted(non_empty_l3))[:20])

for i, s in enumerate(hits[:5], 1):
    print('row', i, json.dumps(s, ensure_ascii=False)[:300])
