import pathlib, re, sys
root = pathlib.Path('d:/wm_backend_/wm_backend')
from_pat = re.compile(r'^(\s*)from\s+apps\.', re.MULTILINE)
import_pat = re.compile(r'^(\s*)import\s+apps\.', re.MULTILINE)
for py_path in root.rglob('*.py'):
    try:
        text = py_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f'Failed to read {py_path}: {e}', file=sys.stderr)
        continue
    new_text = from_pat.sub(r'\1from wm_backend.apps.', text)
    new_text = import_pat.sub(r'\1import wm_backend.apps.', new_text)
    if new_text != text:
        try:
            py_path.write_text(new_text, encoding='utf-8')
            print(f'Updated {py_path}')
        except Exception as e:
            print(f'Failed to write {py_path}: {e}', file=sys.stderr)
