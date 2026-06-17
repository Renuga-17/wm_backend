import pathlib, re, sys

root = pathlib.Path('d:/wm_backend_/wm_backend')

from_pat = re.compile(r'^(\s*)from\s+wm_backend\.apps\.(.+)', re.MULTILINE)
import_pat = re.compile(r'^(\s*)import\s+wm_backend\.apps\.(.+)', re.MULTILINE)

modified_files = []

for py_path in root.rglob('*.py'):
    try:
        text = py_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f'Failed to read {py_path}: {e}', file=sys.stderr)
        continue
    new_text = from_pat.sub(lambda m: f"{m.group(1)}from apps.{m.group(2)}", text)
    new_text = import_pat.sub(lambda m: f"{m.group(1)}import apps.{m.group(2)}", new_text)
    if new_text != text:
        try:
            py_path.write_text(new_text, encoding='utf-8')
            modified_files.append(str(py_path))
        except Exception as e:
            print(f'Failed to write {py_path}: {e}', file=sys.stderr)

print(f'Total files modified: {len(modified_files)}')
for f in modified_files:
    print(f)
