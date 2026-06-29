import os
import sys
import django

# Setup Django environment
sys.path.append(r'd:\wm_backend_\wm_backend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def get_all_urls():
    urls = []
    resolver = get_resolver()
    
    def extract_urls(patterns, prefix=''):
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                # Process individual URL
                url = prefix + str(pattern.pattern)
                name = pattern.name
                
                # Get view info
                view_func = pattern.callback
                module = getattr(view_func, '__module__', '')
                view_name = getattr(view_func, '__name__', '')
                docstring = getattr(view_func, '__doc__', '')
                
                if hasattr(view_func, 'view_class'):
                    view_name = view_func.view_class.__name__
                    docstring = view_func.view_class.__doc__
                    module = view_func.view_class.__module__
                
                # Extract HTTP methods from ViewSet/APIView if possible
                methods = []
                if hasattr(view_func, 'actions'):
                    methods = [m.upper() for m in view_func.actions.keys()]
                elif hasattr(view_func, 'view_class'):
                    if hasattr(view_func.view_class, 'http_method_names'):
                        methods = [m.upper() for m in view_func.view_class.http_method_names if m != 'options']
                
                urls.append({
                    'url': url,
                    'name': name,
                    'view': f"{module}.{view_name}",
                    'docstring': docstring.strip() if docstring else "",
                    'methods': methods
                })
            elif isinstance(pattern, URLResolver):
                # Recursively process included URLs
                extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
    
    extract_urls(resolver.url_patterns)
    return urls

import json
urls = get_all_urls()
with open('d:\\wm_backend_\\wm_backend\\scratch\\api_urls_dump.json', 'w') as f:
    json.dump(urls, f, indent=2)

print(f"Dumped {len(urls)} URLs to api_urls_dump.json")
