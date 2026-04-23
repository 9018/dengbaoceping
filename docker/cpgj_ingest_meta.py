import os, json, hashlib, datetime, pathlib, urllib.request

BASE = '/opt/cpgj/uploads'
ES = 'http://127.0.0.1:9200'

idx_map = {
    '01_指导书': 'standards_clauses',
    '02_标准文档': 'standards_clauses',
    '03_历史测评记录_excel': 'assessment_history',
    '04_拓扑与设备截图': 'evidence_assets',
    '05_交换机与linux配置': 'evidence_assets',
}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

def es_bulk(lines):
    data = ('\n'.join(lines) + '\n').encode('utf-8')
    req = urllib.request.Request(
        ES + '/_bulk', data=data,
        headers={'Content-Type': 'application/x-ndjson'}, method='POST'
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

lines = []
count = 0
for root, _, files in os.walk(BASE):
    for fn in files:
        p = os.path.join(root, fn)
        rel = os.path.relpath(p, BASE).replace('\\', '/')
        parts = rel.split('/')
        if len(parts) < 3:
            continue
        cat, batch = parts[0], parts[1]
        idx = idx_map.get(cat)
        if not idx:
            continue
        ext = pathlib.Path(fn).suffix.lower()
        size = os.path.getsize(p)
        mtime = datetime.datetime.utcfromtimestamp(os.path.getmtime(p)).replace(microsecond=0).isoformat() + 'Z'
        sha = sha256_file(p)
        doc_id = sha

        if idx == 'standards_clauses':
            standard = '测评指导书' if cat == '01_指导书' else '标准文档'
            doc = {
                'doc_type': 'guide' if cat == '01_指导书' else 'standard',
                'standard': standard,
                'clause_id': '',
                'level1': cat,
                'level2': batch,
                'level3': fn,
                'title': fn,
                'content': '',
                'check_method': '',
                'judgement_rule': '',
                'updated_at': now_iso(),
                'source_file': rel,
                'file_ext': ext,
                'file_size': size,
                'file_sha256': sha,
                'file_mtime': mtime,
            }
        elif idx == 'assessment_history':
            doc = {
                'project_type': 'unknown',
                'template_name': fn,
                'indicator_l1': '',
                'indicator_l2': '',
                'indicator_l3': '',
                'record_text': '',
                'conclusion': '',
                'risk_level': '',
                'suggestion': '',
                'created_at': now_iso(),
                'source_file': rel,
                'file_ext': ext,
                'file_size': size,
                'file_sha256': sha,
                'file_mtime': mtime,
            }
        else:
            asset_type = 'topology_image' if cat == '04_拓扑与设备截图' else 'config_file'
            doc = {
                'project_id': 'default',
                'asset_type': asset_type,
                'source_file': rel,
                'ocr_text': '',
                'config_text': '',
                'device': '',
                'ports': [],
                'evidence_time': now_iso(),
                'tags': [cat, batch, ext.lstrip('.')],
                'file_ext': ext,
                'file_size': size,
                'file_sha256': sha,
                'file_mtime': mtime,
            }

        lines.append(json.dumps({'index': {'_index': idx, '_id': doc_id}}, ensure_ascii=False))
        lines.append(json.dumps(doc, ensure_ascii=False))
        count += 1

if lines:
    res = es_bulk(lines)
    print(json.dumps({'total_files': count, 'errors': res.get('errors', True)}, ensure_ascii=False))
else:
    print(json.dumps({'total_files': 0, 'errors': False}, ensure_ascii=False))
