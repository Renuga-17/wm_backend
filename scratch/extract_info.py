import os
import sys
import django

# Set up Django environment
sys.path.append(r"d:\wm_backend_\wm_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps
from django.urls import get_resolver

print("=== MODELS ===")
for app in apps.get_app_configs():
    if app.name.startswith('apps.'):
        print(f"\nApp: {app.name}")
        for model in app.get_models():
            print(f" - {model.__name__}")

print("\n=== URLS ===")
resolver = get_resolver()

def show_urls(patterns, prefix=""):
    for p in patterns:
        if hasattr(p, 'url_patterns'):
            show_urls(p.url_patterns, prefix + str(p.pattern))
        else:
            print(f"{prefix}{p.pattern}")

show_urls(resolver.url_patterns)
