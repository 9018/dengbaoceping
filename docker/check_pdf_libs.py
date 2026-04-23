import importlib.util
mods=['pypdf','PyPDF2','pdfplumber','fitz','pdfminer']
for m in mods:
    print(m, bool(importlib.util.find_spec(m)))
