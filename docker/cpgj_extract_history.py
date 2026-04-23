import json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, UTC
import urllib.request

BASE = Path('/opt/cpgj/uploads/03_历史测评记录_excel')
ES = 'http://127.0.0.1:9200'
NS = {'a':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RELNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def read_sheet_rows(xlsx: Path):
    z = zipfile.ZipFile(xlsx)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    sheets = wb.find('a:sheets', NS)
    sid = sheets.find('a:sheet', NS).attrib.get(RELNS)

    rel = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    target = None
    for r in rel:
        if r.attrib.get('Id') == sid:
            target = r.attrib.get('Target')
            break
    if not target:
        return []
    sheet_path = target if target.startswith('xl/') else ('xl/' + target)

    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        ss = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in ss.findall('a:si', NS):
            txt = ''.join(t.text or '' for t in si.findall('.//a:t', NS))
            shared.append(txt)

    out = []
    sh = ET.fromstring(z.read(sheet_path))
    rows = sh.findall('.//a:sheetData/a:row', NS)
    for row in rows:
        vals = []
        for c in row.findall('a:c', NS):
            t = c.attrib.get('t')
            v = c.find('a:v', NS)
            if v is None:
                vals.append('')
                continue
            x = v.text or ''
            if t == 's' and x.isdigit() and int(x) < len(shared):
                x = shared[int(x)]
            vals.append(x.strip())
        if any(vals):
            out.append(vals)
    return out


def guess_cols(header):
    m = {'l1':None,'l2':None,'l3':None,'check':None,'result':None,'problem':None,'suggest':None}
    for i, h in enumerate(header):
        s = str(h)
        if ('一级' in s and '指标' in s) or s.startswith('一级'):
            m['l1'] = i
        elif ('二级' in s and '指标' in s) or s.startswith('二级'):
            m['l2'] = i
        elif ('三级' in s and '指标' in s) or s.startswith('三级'):
            m['l3'] = i
        elif '检查' in s:
            m['check'] = i
        elif '结论' in s or '判定' in s:
            m['result'] = i
        elif '问题' in s:
            m['problem'] = i
        elif '建议' in s:
            m['suggest'] = i
    return m


def val(row, idx):
    if idx is None or idx >= len(row):
        return ''
    return str(row[idx]).strip()


def bulk(lines):
    data = ('\n'.join(lines) + '\n').encode('utf-8')
    req = urllib.request.Request(ES + '/_bulk?refresh=true', data=data, headers={'Content-Type':'application/x-ndjson'}, method='POST')
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))

lines = []
inserted = 0
now = datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')

for xlsx in BASE.rglob('*.xlsx'):
    rows = read_sheet_rows(xlsx)
    if not rows:
        continue
    header = rows[0]
    cols = guess_cols(header)
    l1=l2=l3=''
    for r in rows[1:]:
        if len(r) < 2:
            continue
        if val(r, cols['l1']): l1 = val(r, cols['l1'])
        if val(r, cols['l2']): l2 = val(r, cols['l2'])
        if val(r, cols['l3']): l3 = val(r, cols['l3'])
        check = val(r, cols['check'])
        result = val(r, cols['result'])
        problem = val(r, cols['problem'])
        suggest = val(r, cols['suggest'])
        if not any([l1,l2,l3,check,result,problem,suggest]):
            continue
        source_file = str(xlsx).replace('/opt/cpgj/uploads/','')
        doc = {
            'project_type':'等级保护测评',
            'template_name': xlsx.name,
            'indicator_l1': l1,
            'indicator_l2': l2,
            'indicator_l3': l3,
            'record_text': check,
            'conclusion': result,
            'risk_level':'',
            'suggestion': suggest if suggest else problem,
            'created_at': now,
            'source_file': source_file,
        }
        did = f"{xlsx.name}:{inserted}"
        lines.append(json.dumps({'index': {'_index':'assessment_history', '_id': did}}, ensure_ascii=False))
        lines.append(json.dumps(doc, ensure_ascii=False))
        inserted += 1

if lines:
    res = bulk(lines)
    print(json.dumps({'inserted': inserted, 'errors': res.get('errors', True)}, ensure_ascii=False))
else:
    print(json.dumps({'inserted': 0, 'errors': False}, ensure_ascii=False))
