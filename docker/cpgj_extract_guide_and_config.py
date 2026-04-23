import json, zipfile, xml.etree.ElementTree as ET, hashlib
from pathlib import Path
from datetime import datetime, UTC
import urllib.request

UPLOAD = Path('/opt/cpgj/uploads')
ES = 'http://127.0.0.1:9200'
WNS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def extract_docx_text(p: Path) -> str:
    try:
        with zipfile.ZipFile(p) as z:
            data = z.read('word/document.xml')
        root = ET.fromstring(data)
        lines = []
        for para in root.findall('.//w:p', WNS):
            txt = ''.join(t.text or '' for t in para.findall('.//w:t', WNS)).strip()
            if txt:
                lines.append(txt)
        return '\n'.join(lines)
    except Exception:
        return ''


def bulk(lines):
    if not lines:
        return {'errors': False}
    data = ('\n'.join(lines) + '\n').encode('utf-8')
    req = urllib.request.Request(ES + '/_bulk?refresh=true', data=data, headers={'Content-Type':'application/x-ndjson'}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def chunk_text(t: str, n=1200):
    out=[]
    cur=[]
    cur_len=0
    for line in t.splitlines():
        if cur_len + len(line) + 1 > n and cur:
            out.append('\n'.join(cur))
            cur=[line]
            cur_len=len(line)
        else:
            cur.append(line)
            cur_len += len(line)+1
    if cur:
        out.append('\n'.join(cur))
    return out

now = datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
lines=[]
res_stat={'guide_chunks':0,'config_docs':0}

# 指导书正文切块入 standards_clauses
for p in (UPLOAD/'01_指导书').rglob('*.docx'):
    text = extract_docx_text(p)
    if not text.strip():
        continue
    chunks = chunk_text(text, 1200)
    rel = str(p).replace('/opt/cpgj/uploads/','')
    for i, ch in enumerate(chunks, 1):
        raw = f"guide|{rel}|{i}|{ch[:80]}"
        did = hashlib.sha1(raw.encode('utf-8')).hexdigest()
        doc = {
            'doc_type':'guide_clause',
            'standard':'测评指导书',
            'clause_id':f'guide-{i}',
            'level1':'指导书',
            'level2':p.parent.name,
            'level3':p.name,
            'title':f'{p.name}-片段{i}',
            'content':ch,
            'check_method':'',
            'judgement_rule':'',
            'updated_at':now,
            'source_file':rel,
        }
        lines.append(json.dumps({'index': {'_index':'standards_clauses', '_id':did}}, ensure_ascii=False))
        lines.append(json.dumps(doc, ensure_ascii=False))
        res_stat['guide_chunks'] += 1

# 配置文本入 evidence_assets（log/docx）
for p in (UPLOAD/'05_交换机与linux配置').rglob('*'):
    if not p.is_file():
        continue
    text=''
    if p.suffix.lower() in ('.log','.txt','.conf','.cfg'):
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            text = ''
    elif p.suffix.lower()=='.docx':
        text = extract_docx_text(p)
    rel = str(p).replace('/opt/cpgj/uploads/','')
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    did = sha
    doc = {
        'project_id':'default',
        'asset_type':'config_file',
        'source_file':rel,
        'ocr_text':'',
        'config_text':text[:200000],
        'device':'',
        'ports':[],
        'evidence_time':now,
        'tags':['配置','自动抽取',p.suffix.lower().lstrip('.')],
        'file_sha256':sha,
    }
    lines.append(json.dumps({'index': {'_index':'evidence_assets', '_id':did}}, ensure_ascii=False))
    lines.append(json.dumps(doc, ensure_ascii=False))
    res_stat['config_docs'] += 1

# 拓扑docx作为证据文本补充
for p in (UPLOAD/'04_拓扑与设备截图').rglob('*.docx'):
    text = extract_docx_text(p)
    rel = str(p).replace('/opt/cpgj/uploads/','')
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    did = sha
    doc = {
        'project_id':'default',
        'asset_type':'topology_doc',
        'source_file':rel,
        'ocr_text':text[:200000],
        'config_text':'',
        'device':'',
        'ports':[],
        'evidence_time':now,
        'tags':['拓扑','docx','自动抽取'],
        'file_sha256':sha,
    }
    lines.append(json.dumps({'index': {'_index':'evidence_assets', '_id':did}}, ensure_ascii=False))
    lines.append(json.dumps(doc, ensure_ascii=False))

resp = bulk(lines)
res_stat['errors'] = resp.get('errors', True)
print(json.dumps(res_stat, ensure_ascii=False))
