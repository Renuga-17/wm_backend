import os
import django
import sys

# Setup django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver

out_path = os.path.join(os.path.dirname(__file__), 'dump_urls.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    def dump_patterns(patterns, prefix=''):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                new_prefix = prefix + str(pattern.pattern)
                dump_patterns(pattern.url_patterns, new_prefix)
            elif isinstance(pattern, URLPattern):
                view_class = getattr(pattern.callback, 'cls', None)
                if not view_class:
                    view_class = pattern.callback
                view_name = view_class.__name__ if hasattr(view_class, '__name__') else str(view_class)
                
                methods = []
                if hasattr(view_class, 'actions') and view_class.actions:
                    methods = list(view_class.actions.keys())
                else:
                    for m in ['get', 'post', 'put', 'patch', 'delete']:
                        if hasattr(view_class, m.lower()) and getattr(view_class, m.lower()).__code__.co_name != 'http_method_not_allowed':
                            methods.append(m.upper())
                
                serializer_class = getattr(view_class, 'serializer_class', None)
                serializer_name = serializer_class.__name__ if serializer_class else 'None'
                
                f.write(f"{prefix}{pattern.pattern} | {', '.join(methods)} | {serializer_name} | {view_name} | {pattern.name}\n")

    dump_patterns(get_resolver().url_patterns)

print(f"Dumped to {out_path}")
