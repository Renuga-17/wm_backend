import pathlib, re, sys, json

def replace_imports(root_path):
    root = pathlib.Path(root_path)
    pattern_from = re.compile(r'from\s+wm_backend\.apps\.(.+)\s+import')
    pattern_import = re.compile(r'import\s+wm_backend\.apps\.(.+)')
    modified_files = []
    for py_path in root.rglob('*.py'):
        try:
            text = py_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f'Failed to read {py_path}: {e}', file=sys.stderr)
            continue
        new_text = re.sub(r'from\s+wm_backend\.apps\.', r'from apps.', text)
        new_text = re.sub(r'import\s+wm_backend\.apps\.', r'import apps.', new_text)
        if new_text != text:
            try:
                py_path.write_text(new_text, encoding='utf-8')
                modified_files.append(str(py_path))
                print(f'Updated {py_path}')
            except Exception as e:
                print(f'Failed to write {py_path}: {e}', file=sys.stderr)
    return modified_files

if __name__ == '__main__':
    root_dir = r'd:/wm_backend_/wm_backend'
    modified = replace_imports(root_dir)
    result = {
        'total_modified': len(modified),
        'files': modified
    }
    print(json.dumps(result, indent=2))
