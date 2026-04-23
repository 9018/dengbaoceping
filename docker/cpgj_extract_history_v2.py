import json, zipfile, xml.etree.ElementTree as ET, hashlib
from pathlib import Path
from datetime import datetime, UTC
import urllib.request

BASE = Path('/opt/cpgj/uploads/03_历史测评记录_excel')
ES = 'http://127.0.0.1:9200'
NS = {'a':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RELNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def col_to_idx(ref):
    s = ''.join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def row_map(row, shared):
    out = {}
    for c in row.findall('a:c', NS):
        ref = c.attrib.get('r', '')
        idx = col_to_idx(ref)
        t = c.attrib.get('t', '')
        v = c.find('a:v', NS)
        isv = c.find('a:is', NS)
        txt = ''
        if v is not None and v.text is not None:
            txt = v.text
            if t == 's' and txt.isdigit() and int(txt) < len(shared):
                txt = shared[int(txt)]
        elif isv is not None:
            txt = ''.join(x.text or '' for x in isv.findall('.//a:t', NS))
        out[idx] = (txt or '').strip()
    return out


def bulk(lines):
    if not lines:
        return {'errors': False}
    data = ('\n'.join(lines) + '\n').encode('utf-8')
    req = urllib.request.Request(ES + '/_bulk?refresh=true', data=data, headers={'Content-Type':'application/x-ndjson'}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))

inserted = 0
lines = []
now = datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')

for xlsx in BASE.rglob('*.xlsx'):
    z = zipfile.ZipFile(xlsx)

    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in ss.findall('a:si', NS):
            shared.append(''.join(t.text or '' for t in si.findall('.//a:t', NS)))

    wb = ET.fromstring(z.read('xl/workbook.xml'))
    sheets = wb.find('a:sheets', NS)
    rel = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid_to_target = {r.attrib.get('Id'): r.attrib.get('Target') for r in rel}

    for sheet in sheets.findall('a:sheet', NS):
        sname = sheet.attrib.get('name', '')
        rid = sheet.attrib.get(RELNS)
        target = rid_to_target.get(rid)
        if not target:
            continue
        sp = target if target.startswith('xl/') else ('xl/' + target)
        sh = ET.fromstring(z.read(sp))
        rows = sh.findall('.//a:sheetData/a:row', NS)

        l1 = l2 = l3 = ''
        for r in rows:
            rm = row_map(r, shared)
            # 模板列固定：A一级 B二级 C三级 D检查 E判定 F问题 G建议
            a = rm.get(0, '').strip()
            b = rm.get(1, '').strip()
            c = rm.get(2, '').strip()
            d = rm.get(3, '').strip()
            e = rm.get(4, '').strip()
            f = rm.get(5, '').strip()
            g = rm.get(6, '').strip()

            if a: l1 = a
            if b: l2 = b
            if c: l3 = c

            # 跳过纯表头
            if l1 == '一级测评指标' and l2 == '二级测评指标':
                continue
            if not any([l1, l2, l3, d, e, f, g]):
                continue
            if not (c or d or e or f or g):
                continue

            source_file = str(xlsx).replace('/opt/cpgj/uploads/', '')
            doc = {
                'project_type': '等级保护测评',
                'template_name': xlsx.name,
                'indicator_l1': l1,
                'indicator_l2': l2,
                'indicator_l3': l3,
                'record_text': d,
                'conclusion': e,
                'risk_level': '',
                'suggestion': g if g else f,
                'created_at': now,
                'source_file': source_file,
                'sheet_name': sname,
            }
            raw = f"{source_file}|{sname}|{r.attrib.get('r','')}|{l1}|{l2}|{l3}|{d}|{e}|{f}|{g}"
            did = hashlib.sha1(raw.encode('utf-8')).hexdigest()
            lines.append(json.dumps({'index': {'_index': 'assessment_history', '_id': did}}, ensure_ascii=False))
            lines.append(json.dumps(doc, ensure_ascii=False))
            inserted += 1

res = bulk(lines)
print(json.dumps({'inserted': inserted, 'errors': res.get('errors', True)}, ensure_ascii=False))
