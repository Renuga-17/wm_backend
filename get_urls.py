import os
import django
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

def get_urls(patterns, prefix=""):
    urls = []
    for p in patterns:
        if isinstance(p, URLPattern):
            urls.append(prefix + str(p.pattern))
        elif isinstance(p, URLResolver):
            new_prefix = prefix + str(p.pattern)
            urls.extend(get_urls(p.url_patterns, new_prefix))
    return urls

urls = get_urls(get_resolver().url_patterns)
for u in urls:
    print(u)
