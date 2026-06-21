import re

def clean():
    with open('scratch/dump_urls.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    clean_lines = []
    seen = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip DRF format suffix patterns
        if '\\.(?P<format>[a-z0-9]+)/?$' in line or '<drf_format_suffix:format>' in line:
            continue
        
        parts = line.split(' | ')
        if len(parts) < 5:
            continue
        url, methods, serializer, view, name = parts
        
        # Clean regex patterns to clean URLs
        # Replace ^ and $
        url = url.replace('^', '').replace('$', '')
        # Replace (?P<pk>[^/.]+) with {id}
        url = re.sub(r'\(\?P<pk>\[\^/\.\]\+\)', '{id}', url)
        # Replace other URL parameter groups like (?P<path>.*)
        url = re.sub(r'\(\?P<([^>]+)>[^\)]+\)', r'{\1}', url)
        
        # Determine clean methods
        if not methods or methods == '':
            if 'ViewSet' in view:
                methods = 'GET, POST, PUT, PATCH, DELETE (ViewSet)'
            else:
                methods = 'GET/POST'
        
        key = f"{url} | {methods} | {view}"
        if key in seen:
            continue
        seen.add(key)
        
        clean_lines.append((url, methods, serializer, view, name))
    
    # Sort and group
    clean_lines.sort(key=lambda x: x[0])
    
    with open('scratch/clean_urls.txt', 'w', encoding='utf-8') as outf:
        for url, methods, serializer, view, name in clean_lines:
            outf.write(f"{url} | {methods} | {serializer} | {view} | {name}\n")

if __name__ == '__main__':
    clean()
