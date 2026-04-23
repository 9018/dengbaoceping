import zipfile, xml.etree.ElementTree as ET
from pathlib import Path

NS={'a':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RELNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
base=Path('/opt/cpgj/uploads/03_历史测评记录_excel')
for x in base.rglob('*.xlsx'):
    print('===', x.name)
    z=zipfile.ZipFile(x)
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    sheets=wb.find('a:sheets',NS)
    for sh in sheets.findall('a:sheet',NS):
        print('sheet',sh.attrib.get('name'),sh.attrib.get(RELNS))
    sid=sheets.find('a:sheet',NS).attrib.get(RELNS)
    rel=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    target=None
    for r in rel:
        if r.attrib.get('Id')==sid:
            target=r.attrib.get('Target')
            break
    p=target if target.startswith('xl/') else 'xl/'+target
    print('first sheet path',p)
    sh=ET.fromstring(z.read(p))
    rows=sh.findall('.//a:sheetData/a:row',NS)
    print('rows',len(rows))
    c=0
    for row in rows:
        c+=1
        vals=[]
        for cell in row.findall('a:c',NS):
            ref=cell.attrib.get('r')
            t=cell.attrib.get('t','')
            v=cell.find('a:v',NS)
            isv=cell.find('a:is',NS)
            txt=''
            if v is not None and v.text:
                txt=v.text
            elif isv is not None:
                ts=isv.findall('.//a:t',NS)
                txt=''.join([k.text or '' for k in ts])
            vals.append((ref,t,txt[:30]))
        if vals:
            print('row',c,vals[:8])
        if c>=12:
            break
