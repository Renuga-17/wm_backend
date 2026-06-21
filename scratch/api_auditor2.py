import os
import sys
import django

sys.path.append(r'd:\wm_backend_\wm_backend')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver

def analyze_api():
    resolver = get_resolver()
    api_endpoints = []
    
    def extract_urls(patterns, prefix=''):
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                url = prefix + str(pattern.pattern)
                if not url.startswith('api/'):
                    continue
                
                view_func = pattern.callback
                
                view_cls = getattr(view_func, 'view_class', None)
                if not view_cls:
                    view_cls = getattr(view_func, 'cls', None)
                
                methods = []
                if hasattr(view_func, 'actions'):
                    methods = [m.upper() for m in view_func.actions.keys()]
                elif view_cls and hasattr(view_cls, 'http_method_names'):
                    methods = [m.upper() for m in view_cls.http_method_names if m != 'options']
                elif hasattr(view_func, 'mapping'):
                     methods = [m.upper() for m in view_func.mapping.keys() if m != 'options']
                else:
                     methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
                
                has_serializer = False
                has_permissions = False
                has_swagger = False
                
                if view_cls:
                    if hasattr(view_cls, 'serializer_class') and view_cls.serializer_class is not None:
                        has_serializer = True
                    if hasattr(view_cls, 'get_serializer_class'):
                         has_serializer = True
                         
                    if hasattr(view_cls, 'permission_classes') and view_cls.permission_classes:
                        has_permissions = True
                        
                    # Check methods for swagger decorators
                    for m_name in [m.lower() for m in methods]:
                        m_func = getattr(view_cls, m_name, None)
                        if m_func:
                            if hasattr(m_func, '_swagger_auto_schema') or hasattr(m_func, 'swagger_auto_schema'):
                                has_swagger = True
                
                api_endpoints.append({
                    'endpoint': '/' + url,
                    'methods': methods,
                    'has_serializer': has_serializer,
                    'has_permissions': has_permissions,
                    'has_swagger': has_swagger,
                    'view_name': getattr(view_cls, '__name__', getattr(view_func, '__name__', 'Unknown'))
                })
                
            elif isinstance(pattern, URLResolver):
                extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
                
    extract_urls(resolver.url_patterns)
    
    md = "# API & Frontend Readiness Audit\n\n"
    md += "## API Details\n\n"
    
    complete = 0
    partial = 0
    missing = 0
    frontend_ready = []
    
    # Deduplicate APIRoot views for accurate counting
    filtered_endpoints = []
    seen = set()
    for ep in api_endpoints:
        if ep['view_name'] == 'APIRootView':
            continue
        key = (ep['endpoint'], tuple(ep['methods']))
        if key not in seen:
            seen.add(key)
            filtered_endpoints.append(ep)
            
    for ep in filtered_endpoints:
        status = "Missing"
        if ep['has_serializer'] and ep['has_permissions']:
            if ep['has_swagger']:
                status = "Complete"
                complete += 1
                frontend_ready.append(ep['endpoint'])
            else:
                status = "Partial"
                partial += 1
                frontend_ready.append(ep['endpoint'])
        elif ep['has_serializer'] or ep['has_permissions']:
            status = "Partial"
            partial += 1
        else:
            missing += 1
            
        methods_str = ", ".join(ep['methods']) if ep['methods'] else "ALL"
        
        md += f"### {ep['endpoint']}\n"
        md += f"* **Method**: {methods_str}\n"
        md += f"* **Status**: {status}\n"
        md += f"* **Serializer**: {'Yes' if ep['has_serializer'] else 'No'}\n"
        md += f"* **Auth/Perms**: {'Yes' if ep['has_permissions'] else 'No'}\n"
        md += f"* **Swagger/OpenAPI**: {'Yes' if ep['has_swagger'] else 'No'}\n"
        md += f"* **View**: {ep['view_name']}\n\n"
        
    md += "## Summary Metrics\n\n"
    total = len(filtered_endpoints)
    md += f"1. **Total API Count**: {total}\n"
    md += f"2. **Complete Endpoints**: {complete}\n"
    md += f"3. **Partial Endpoints**: {partial}\n"
    md += f"4. **Missing Endpoints**: {missing}\n"
    
    md += "\n5. **Frontend Ready APIs**:\n"
    for r in frontend_ready:
        md += f"   * {r}\n"
        
    md += "\n6. **Remaining Backend Gaps**:\n"
    md += "   * Missing Swagger documentation for partial APIs.\n"
    md += "   * Several APIs missing strict serializer validation and permissions.\n"
    
    completion_pct = int(((complete + (partial * 0.5)) / total) * 100) if total > 0 else 0
    md += f"\n7. **Backend Completion %**: {completion_pct}%\n"
    md += "8. **Expected WMS Completion After API Readiness**: 100%\n"
    
    with open('d:\\wm_backend_\\wm_backend\\scratch\\api_audit_report_raw.md', 'w') as f:
        f.write(md)
        
    print(f"Analysis complete. Total endpoints: {total}")

analyze_api()
