import os
import shutil
import re

MOVES = [
    # IDENTITY BOUNDED CONTEXT
    ("apps/users/models.py", "apps/identity/infrastructure/persistence/user_models.py"),
    ("apps/users/serializers.py", "apps/identity/presentation/api/user_serializers.py"),
    ("apps/users/views.py", "apps/identity/presentation/api/user_views.py"),
    ("apps/users/urls.py", "apps/identity/presentation/api/user_urls.py"),
    ("apps/users/services.py", "apps/identity/application/services/user_services.py"),
    ("apps/users/admin.py", "apps/identity/infrastructure/persistence/user_admin.py"),
    ("apps/users/tests.py", "apps/identity/tests/test_users.py"),
    ("apps/audit_logs/models.py", "apps/identity/infrastructure/persistence/audit_models.py"),
    ("apps/audit_logs/serializers.py", "apps/identity/presentation/api/audit_serializers.py"),
    ("apps/audit_logs/views.py", "apps/identity/presentation/api/audit_views.py"),
    ("apps/audit_logs/urls.py", "apps/identity/presentation/api/audit_urls.py"),
    ("apps/audit_logs/services.py", "apps/identity/application/services/audit_services.py"),
    ("apps/audit_logs/admin.py", "apps/identity/infrastructure/persistence/audit_admin.py"),
    ("apps/audit_logs/tests.py", "apps/identity/tests/test_audit_logs.py"),

    # WAREHOUSE BOUNDED CONTEXT
    ("apps/warehouses/models.py", "apps/warehouse/infrastructure/persistence/warehouse_models.py"),
    ("apps/warehouses/serializers.py", "apps/warehouse/presentation/api/warehouse_serializers.py"),
    ("apps/warehouses/views.py", "apps/warehouse/presentation/api/warehouse_views.py"),
    ("apps/warehouses/urls.py", "apps/warehouse/presentation/api/warehouse_urls.py"),
    ("apps/warehouses/services.py", "apps/warehouse/application/services/warehouse_services.py"),
    ("apps/warehouses/admin.py", "apps/warehouse/infrastructure/persistence/warehouse_admin.py"),
    ("apps/warehouses/tests.py", "apps/warehouse/tests/test_warehouses.py"),
    ("apps/warehouses/layout_parser.py", "apps/warehouse/application/services/layout_parser.py"),
    ("apps/warehouses/layout_serializers.py", "apps/warehouse/presentation/api/layout_serializers.py"),
    ("apps/warehouses/layout_views.py", "apps/warehouse/presentation/api/layout_views.py"),
    ("apps/warehouses/layout_urls.py", "apps/warehouse/presentation/api/layout_urls.py"),
    ("apps/warehouses/twin_serializers.py", "apps/warehouse/presentation/api/twin_serializers.py"),
    ("apps/warehouses/twin_views.py", "apps/warehouse/presentation/api/twin_views.py"),
    ("apps/warehouses/twin_urls.py", "apps/warehouse/presentation/api/twin_urls.py"),
    ("apps/warehouses/consumers.py", "apps/warehouse/presentation/consumers.py"),
    ("apps/warehouses/signals.py", "apps/warehouse/infrastructure/messaging/warehouse_signals.py"),
    ("apps/zones/models.py", "apps/warehouse/infrastructure/persistence/zone_models.py"),
    ("apps/zones/serializers.py", "apps/warehouse/presentation/api/zone_serializers.py"),
    ("apps/zones/views.py", "apps/warehouse/presentation/api/zone_views.py"),
    ("apps/zones/urls.py", "apps/warehouse/presentation/api/zone_urls.py"),
    ("apps/zones/services.py", "apps/warehouse/application/services/zone_services.py"),
    ("apps/zones/admin.py", "apps/warehouse/infrastructure/persistence/zone_admin.py"),
    ("apps/zones/tests.py", "apps/warehouse/tests/test_zones.py"),
    ("apps/bins/models.py", "apps/warehouse/infrastructure/persistence/bin_models.py"),
    ("apps/bins/serializers.py", "apps/warehouse/presentation/api/bin_serializers.py"),
    ("apps/bins/views.py", "apps/warehouse/presentation/api/bin_views.py"),
    ("apps/bins/urls.py", "apps/warehouse/presentation/api/bin_urls.py"),
    ("apps/bins/services.py", "apps/warehouse/application/services/bin_services.py"),
    ("apps/bins/admin.py", "apps/warehouse/infrastructure/persistence/bin_admin.py"),
    ("apps/bins/tests.py", "apps/warehouse/tests/test_bins.py"),
    ("apps/routes/models.py", "apps/warehouse/infrastructure/persistence/route_models.py"),
    ("apps/routes/serializers.py", "apps/warehouse/presentation/api/route_serializers.py"),
    ("apps/routes/views.py", "apps/warehouse/presentation/api/route_views.py"),
    ("apps/routes/urls.py", "apps/warehouse/presentation/api/route_urls.py"),
    ("apps/routes/serializers_generate.py", "apps/warehouse/presentation/api/serializers_generate.py"),
    ("apps/routes/generate_route_view.py", "apps/warehouse/presentation/api/generate_route_view.py"),
    ("apps/routes/consumers.py", "apps/warehouse/presentation/route_consumers.py"),
    ("apps/routes/services/pathfinding.py", "apps/warehouse/application/services/pathfinding.py"),
    ("apps/routes/services/route_optimizer.py", "apps/warehouse/application/services/route_optimizer.py"),

    # INVENTORY BOUNDED CONTEXT
    ("apps/inventory/models.py", "apps/inventory/infrastructure/persistence/inventory_models.py"),
    ("apps/inventory/serializers.py", "apps/inventory/presentation/api/inventory_serializers.py"),
    ("apps/inventory/views.py", "apps/inventory/presentation/api/inventory_views.py"),
    ("apps/inventory/urls.py", "apps/inventory/presentation/api/inventory_urls.py"),
    ("apps/inventory/services.py", "apps/inventory/application/services/inventory_services.py"),
    ("apps/inventory/admin.py", "apps/inventory/infrastructure/persistence/inventory_admin.py"),
    ("apps/inventory/tests.py", "apps/inventory/tests/test_inventory.py"),
    ("apps/inventory/consumers.py", "apps/inventory/presentation/consumers.py"),
    ("apps/inventory/signals.py", "apps/inventory/infrastructure/messaging/inventory_signals.py"),
    ("apps/products/models.py", "apps/inventory/infrastructure/persistence/product_models.py"),
    ("apps/products/serializers.py", "apps/inventory/presentation/api/product_serializers.py"),
    ("apps/products/views.py", "apps/inventory/presentation/api/product_views.py"),
    ("apps/products/urls.py", "apps/inventory/presentation/api/product_urls.py"),
    ("apps/products/services.py", "apps/inventory/application/services/product_services.py"),
    ("apps/products/admin.py", "apps/inventory/infrastructure/persistence/product_admin.py"),
    ("apps/products/tests.py", "apps/inventory/tests/test_products.py"),
    ("apps/movements/models.py", "apps/inventory/infrastructure/persistence/movement_models.py"),
    ("apps/movements/serializers.py", "apps/inventory/presentation/api/movement_serializers.py"),
    ("apps/movements/views.py", "apps/inventory/presentation/api/movement_views.py"),
    ("apps/movements/urls.py", "apps/inventory/presentation/api/movement_urls.py"),
    ("apps/movements/services.py", "apps/inventory/application/services/movement_services.py"),
    ("apps/movements/admin.py", "apps/inventory/infrastructure/persistence/movement_admin.py"),
    ("apps/movements/tests.py", "apps/inventory/tests/test_movements.py"),
    ("apps/recommendations/models.py", "apps/inventory/infrastructure/persistence/recommendation_models.py"),
    ("apps/recommendations/serializers.py", "apps/inventory/presentation/api/recommendation_serializers.py"),
    ("apps/recommendations/views.py", "apps/inventory/presentation/api/recommendation_views.py"),
    ("apps/recommendations/urls.py", "apps/inventory/presentation/api/recommendation_urls.py"),
    ("apps/recommendations/ai_urls.py", "apps/inventory/presentation/api/ai_urls.py"),
    ("apps/recommendations/services.py", "apps/inventory/application/services/recommendation_services.py"),
    ("apps/recommendations/admin.py", "apps/inventory/infrastructure/persistence/recommendation_admin.py"),
    ("apps/recommendations/tests.py", "apps/inventory/tests/test_recommendations.py"),
    ("apps/recommendations/consumers.py", "apps/inventory/presentation/recommendation_consumers.py"),
    ("apps/recommendations/services/slotting_service.py", "apps/inventory/application/services/slotting_service.py"),
    ("apps/recommendations/services/ml_slotting.py", "apps/inventory/application/services/ml_slotting_old.py"),
    ("apps/recommendations/ai_engine/ml_slotting.py", "apps/inventory/application/ai/ml_slotting.py"),
    ("apps/recommendations/ai_engine/feedback_loop.py", "apps/inventory/application/ai/feedback_loop.py"),
    ("apps/recommendations/ai_engine/hotspot_prevention.py", "apps/inventory/application/ai/hotspot_prevention.py"),
    ("apps/recommendations/ai_engine/operational_scoring.py", "apps/inventory/application/ai/operational_scoring.py"),
    ("apps/dashboards/models.py", "apps/inventory/infrastructure/persistence/dashboard_models.py"),
    ("apps/dashboards/serializers.py", "apps/inventory/presentation/api/dashboard_serializers.py"),
    ("apps/dashboards/views.py", "apps/inventory/presentation/api/dashboard_views.py"),
    ("apps/dashboards/urls.py", "apps/inventory/presentation/api/dashboard_urls.py"),
    ("apps/dashboards/services.py", "apps/inventory/application/services/dashboard_services.py"),
    ("apps/dashboards/analytics_service.py", "apps/inventory/application/services/analytics_service.py"),
    ("apps/dashboards/admin.py", "apps/inventory/infrastructure/persistence/dashboard_admin.py"),
    ("apps/dashboards/tests.py", "apps/inventory/tests/test_dashboards.py"),

    # ORDERS BOUNDED CONTEXT
    ("apps/orders/models.py", "apps/orders/infrastructure/persistence/order_models.py"),
    ("apps/orders/serializers.py", "apps/orders/presentation/api/order_serializers.py"),
    ("apps/orders/views.py", "apps/orders/presentation/api/order_views.py"),
    ("apps/orders/urls.py", "apps/orders/presentation/api/order_urls.py"),
    ("apps/orders/services.py", "apps/orders/application/services/order_services.py"),
    ("apps/orders/admin.py", "apps/orders/infrastructure/persistence/order_admin.py"),
    ("apps/orders/tests.py", "apps/orders/tests/test_orders.py"),

    # INBOUND BOUNDED CONTEXT
    ("apps/inbound/models.py", "apps/inbound/infrastructure/persistence/inbound_models.py"),
    ("apps/inbound/serializers.py", "apps/inbound/presentation/api/inbound_serializers.py"),
    ("apps/inbound/views.py", "apps/inbound/presentation/api/inbound_views.py"),
    ("apps/inbound/urls.py", "apps/inbound/presentation/api/inbound_urls.py"),
    ("apps/inbound/services.py", "apps/inbound/application/services/inbound_services.py"),
    ("apps/inbound/admin.py", "apps/inbound/infrastructure/persistence/inbound_admin.py"),
    ("apps/inbound/tests.py", "apps/inbound/tests/test_inbound.py"),
    ("apps/ocr/models.py", "apps/inbound/infrastructure/persistence/ocr_models.py"),
    ("apps/ocr/serializers.py", "apps/inbound/presentation/api/ocr_serializers.py"),
    ("apps/ocr/views.py", "apps/inbound/presentation/api/ocr_views.py"),
    ("apps/ocr/urls.py", "apps/inbound/presentation/api/ocr_urls.py"),
    ("apps/ocr/rag_service.py", "apps/inbound/application/services/rag_service.py"),
    ("apps/ocr/admin.py", "apps/inbound/infrastructure/persistence/ocr_admin.py"),
    ("apps/ocr/tests.py", "apps/inbound/tests/test_ocr.py"),
]

MIGRATION_MAPPING = {
    "apps/users/migrations": "apps/identity/infrastructure/persistence/migrations",
    "apps/audit_logs/migrations": "apps/identity/infrastructure/persistence/migrations",
    
    "apps/warehouses/migrations": "apps/warehouse/infrastructure/persistence/migrations",
    "apps/zones/migrations": "apps/warehouse/infrastructure/persistence/migrations",
    "apps/routes/migrations": "apps/warehouse/infrastructure/persistence/migrations",
    
    "apps/products/migrations": "apps/inventory/infrastructure/persistence/migrations",
    "apps/inventory/migrations": "apps/inventory/infrastructure/persistence/migrations",
    "apps/movements/migrations": "apps/inventory/infrastructure/persistence/migrations",
    "apps/recommendations/migrations": "apps/inventory/infrastructure/persistence/migrations",
    "apps/dashboards/migrations": "apps/inventory/infrastructure/persistence/migrations",
    
    "apps/orders/migrations": "apps/orders/infrastructure/persistence/migrations",
    
    "apps/inbound/migrations": "apps/inbound/infrastructure/persistence/migrations",
    "apps/ocr/migrations": "apps/inbound/infrastructure/persistence/migrations",
}

COMMAND_MOVES = [
    ("apps/warehouses/management", "apps/warehouse/infrastructure/persistence/management"),
    ("apps/routes/management", "apps/warehouse/infrastructure/persistence/management"),
]

OLD_APP_DIRS = [
    "apps/users",
    "apps/audit_logs",
    "apps/warehouses",
    "apps/zones",
    "apps/bins",
    "apps/routes",
    "apps/products",
    "apps/movements",
    "apps/recommendations",
    "apps/dashboards",
    "apps/ocr"
]

def make_apps_py(app_name, path):
    content = f"""from django.apps import AppConfig

class {app_name.capitalize()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app_name}'
"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def make_aggregate_file(imports, dest_file):
    content = "\n".join([f"from {imp} import *" for imp in imports]) + "\n"
    os.makedirs(os.path.dirname(dest_file), exist_ok=True)
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Executing migration in: {root_dir}")

    # 1. Move normal files
    for src_rel, dest_rel in MOVES:
        src = os.path.join(root_dir, src_rel)
        dest = os.path.join(root_dir, dest_rel)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            print(f"Copied: {src_rel} -> {dest_rel}")

    # 2. Move management commands
    for src_rel, dest_rel in COMMAND_MOVES:
        src = os.path.join(root_dir, src_rel)
        dest = os.path.join(root_dir, dest_rel)
        if os.path.exists(src):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(f"Copied command folder: {src_rel} -> {dest_rel}")

    # 3. Create app configurations (apps.py)
    make_apps_py("identity", os.path.join(root_dir, "apps/identity/apps.py"))
    make_apps_py("warehouse", os.path.join(root_dir, "apps/warehouse/apps.py"))
    make_apps_py("inventory", os.path.join(root_dir, "apps/inventory/apps.py"))
    make_apps_py("orders", os.path.join(root_dir, "apps/orders/apps.py"))
    make_apps_py("inbound", os.path.join(root_dir, "apps/inbound/apps.py"))
    make_apps_py("outbound", os.path.join(root_dir, "apps/outbound/apps.py"))

    # 4. Create aggregate files
    # Identity persistence aggregates
    make_aggregate_file([".user_models", ".audit_models"], os.path.join(root_dir, "apps/identity/infrastructure/persistence/models.py"))
    make_aggregate_file([".user_admin", ".audit_admin"], os.path.join(root_dir, "apps/identity/infrastructure/persistence/admin.py"))
    # Identity presentation aggregates
    make_aggregate_file([".user_views", ".audit_views"], os.path.join(root_dir, "apps/identity/presentation/api/views.py"))
    make_aggregate_file([".user_serializers", ".audit_serializers"], os.path.join(root_dir, "apps/identity/presentation/api/serializers.py"))

    # Warehouse persistence aggregates
    make_aggregate_file([".warehouse_models", ".zone_models", ".bin_models", ".route_models"], os.path.join(root_dir, "apps/warehouse/infrastructure/persistence/models.py"))
    make_aggregate_file([".warehouse_admin", ".zone_admin", ".bin_admin"], os.path.join(root_dir, "apps/warehouse/infrastructure/persistence/admin.py"))
    # Warehouse presentation aggregates
    make_aggregate_file([".warehouse_views", ".layout_views", ".twin_views", ".zone_views", ".bin_views", ".route_views", ".generate_route_view"], os.path.join(root_dir, "apps/warehouse/presentation/api/views.py"))
    make_aggregate_file([".warehouse_serializers", ".layout_serializers", ".twin_serializers", ".summary_serializers", ".zone_serializers", ".bin_serializers", ".route_serializers", ".serializers_generate"], os.path.join(root_dir, "apps/warehouse/presentation/api/serializers.py"))

    # Inventory persistence aggregates
    make_aggregate_file([".inventory_models", ".product_models", ".movement_models", ".recommendation_models", ".dashboard_models"], os.path.join(root_dir, "apps/inventory/infrastructure/persistence/models.py"))
    make_aggregate_file([".inventory_admin", ".product_admin", ".movement_admin", ".recommendation_admin", ".dashboard_admin"], os.path.join(root_dir, "apps/inventory/infrastructure/persistence/admin.py"))
    # Inventory presentation aggregates
    make_aggregate_file([".inventory_views", ".product_views", ".movement_views", ".recommendation_views", ".dashboard_views"], os.path.join(root_dir, "apps/inventory/presentation/api/views.py"))
    make_aggregate_file([".inventory_serializers", ".product_serializers", ".movement_serializers", ".recommendation_serializers", ".dashboard_serializers"], os.path.join(root_dir, "apps/inventory/presentation/api/serializers.py"))

    # Inbound persistence aggregates
    make_aggregate_file([".inbound_models", ".ocr_models"], os.path.join(root_dir, "apps/inbound/infrastructure/persistence/models.py"))
    make_aggregate_file([".inbound_admin", ".ocr_admin"], os.path.join(root_dir, "apps/inbound/infrastructure/persistence/admin.py"))
    # Inbound presentation aggregates
    make_aggregate_file([".inbound_views", ".ocr_views"], os.path.join(root_dir, "apps/inbound/presentation/api/views.py"))
    make_aggregate_file([".inbound_serializers", ".ocr_serializers"], os.path.join(root_dir, "apps/inbound/presentation/api/serializers.py"))

    # Orders persistence aggregates
    make_aggregate_file([".order_models"], os.path.join(root_dir, "apps/orders/infrastructure/persistence/models.py"))
    make_aggregate_file([".order_admin"], os.path.join(root_dir, "apps/orders/infrastructure/persistence/admin.py"))
    # Orders presentation aggregates
    make_aggregate_file([".order_views"], os.path.join(root_dir, "apps/orders/presentation/api/views.py"))
    make_aggregate_file([".order_serializers"], os.path.join(root_dir, "apps/orders/presentation/api/serializers.py"))

    # 5. Move migrations and fix dependencies
    for src_rel, dest_rel in MIGRATION_MAPPING.items():
        src_path = os.path.join(root_dir, src_rel)
        dest_path = os.path.join(root_dir, dest_rel)
        if os.path.exists(src_path):
            os.makedirs(dest_path, exist_ok=True)
            for f in os.listdir(src_path):
                if f.endswith(".py"):
                    shutil.copy2(os.path.join(src_path, f), os.path.join(dest_path, f))
            print(f"Copied migrations: {src_rel} -> {dest_rel}")

    # 6. Global Rewrite of Python imports
    rewrite_rules = [
        (re.compile(r'from\s+apps\.users\.models\s+import'), 'from apps.identity.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.users\.serializers\s+import'), 'from apps.identity.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.users\.views\s+import'), 'from apps.identity.presentation.api.views import'),
        (re.compile(r'from\s+apps\.users\.services\s+import'), 'from apps.identity.application.services.user_services import'),
        (re.compile(r'from\s+apps\.users\b'), 'from apps.identity'),
        
        (re.compile(r'from\s+apps\.audit_logs\.models\s+import'), 'from apps.identity.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.audit_logs\.serializers\s+import'), 'from apps.identity.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.audit_logs\.views\s+import'), 'from apps.identity.presentation.api.views import'),
        (re.compile(r'from\s+apps\.audit_logs\.services\s+import'), 'from apps.identity.application.services.audit_services import'),
        (re.compile(r'from\s+apps\.audit_logs\b'), 'from apps.identity'),

        (re.compile(r'from\s+apps\.warehouses\.models\s+import'), 'from apps.warehouse.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.warehouses\.serializers\s+import'), 'from apps.warehouse.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.warehouses\.views\s+import'), 'from apps.warehouse.presentation.api.views import'),
        (re.compile(r'from\s+apps\.warehouses\.services\s+import'), 'from apps.warehouse.application.services.warehouse_services import'),
        (re.compile(r'from\s+apps\.warehouses\b'), 'from apps.warehouse'),

        (re.compile(r'from\s+apps\.zones\.models\s+import'), 'from apps.warehouse.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.zones\.serializers\s+import'), 'from apps.warehouse.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.zones\.views\s+import'), 'from apps.warehouse.presentation.api.views import'),
        (re.compile(r'from\s+apps\.zones\b'), 'from apps.warehouse'),

        (re.compile(r'from\s+apps\.bins\.models\s+import'), 'from apps.warehouse.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.bins\.serializers\s+import'), 'from apps.warehouse.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.bins\.views\s+import'), 'from apps.warehouse.presentation.api.views import'),
        (re.compile(r'from\s+apps\.bins\b'), 'from apps.warehouse'),

        (re.compile(r'from\s+apps\.routes\.models\s+import'), 'from apps.warehouse.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.routes\.serializers\s+import'), 'from apps.warehouse.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.routes\.views\s+import'), 'from apps.warehouse.presentation.api.views import'),
        (re.compile(r'from\s+apps\.routes\b'), 'from apps.warehouse'),

        (re.compile(r'from\s+apps\.products\.models\s+import'), 'from apps.inventory.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.products\.serializers\s+import'), 'from apps.inventory.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.products\.views\s+import'), 'from apps.inventory.presentation.api.views import'),
        (re.compile(r'from\s+apps\.products\b'), 'from apps.inventory'),

        (re.compile(r'from\s+apps\.inventory\.models\s+import'), 'from apps.inventory.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.inventory\.serializers\s+import'), 'from apps.inventory.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.inventory\.views\s+import'), 'from apps.inventory.presentation.api.views import'),
        (re.compile(r'from\s+apps\.inventory\b'), 'from apps.inventory'),

        (re.compile(r'from\s+apps\.movements\.models\s+import'), 'from apps.inventory.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.movements\.serializers\s+import'), 'from apps.inventory.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.movements\.views\s+import'), 'from apps.inventory.presentation.api.views import'),
        (re.compile(r'from\s+apps\.movements\b'), 'from apps.inventory'),

        (re.compile(r'from\s+apps\.recommendations\.models\s+import'), 'from apps.inventory.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.recommendations\.serializers\s+import'), 'from apps.inventory.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.recommendations\.views\s+import'), 'from apps.inventory.presentation.api.views import'),
        (re.compile(r'from\s+apps\.recommendations\b'), 'from apps.inventory'),

        (re.compile(r'from\s+apps\.dashboards\.models\s+import'), 'from apps.inventory.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.dashboards\.serializers\s+import'), 'from apps.inventory.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.dashboards\.views\s+import'), 'from apps.inventory.presentation.api.views import'),
        (re.compile(r'from\s+apps\.dashboards\b'), 'from apps.inventory'),

        (re.compile(r'from\s+apps\.inbound\.models\s+import'), 'from apps.inbound.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.inbound\.serializers\s+import'), 'from apps.inbound.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.inbound\.views\s+import'), 'from apps.inbound.presentation.api.views import'),
        (re.compile(r'from\s+apps\.inbound\b'), 'from apps.inbound'),

        (re.compile(r'from\s+apps\.ocr\.models\s+import'), 'from apps.inbound.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.ocr\.serializers\s+import'), 'from apps.inbound.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.ocr\.views\s+import'), 'from apps.inbound.presentation.api.views import'),
        (re.compile(r'from\s+apps\.ocr\b'), 'from apps.inbound'),

        (re.compile(r'from\s+apps\.orders\.models\s+import'), 'from apps.orders.infrastructure.persistence.models import'),
        (re.compile(r'from\s+apps\.orders\.serializers\s+import'), 'from apps.orders.presentation.api.serializers import'),
        (re.compile(r'from\s+apps\.orders\.views\s+import'), 'from apps.orders.presentation.api.views import'),
        (re.compile(r'from\s+apps\.orders\b'), 'from apps.orders'),
    ]

    # Walk all files in root/apps, root/config, root/scripts, root/tests, root/scratch to update imports and migrations dependency mappings
    for dir_name in ["apps", "config", "scripts", "tests", "scratch"]:
        dir_path = os.path.join(root_dir, dir_name)
        if not os.path.exists(dir_path):
            continue
        for r, d, fs in os.walk(dir_path):
            for f in fs:
                if f.endswith(".py"):
                    py_file = os.path.join(r, f)
                    try:
                        with open(py_file, "r", encoding="utf-8") as file_obj:
                            text = file_obj.read()
                    except Exception as e:
                        print(f"Skipped reading {py_file}: {e}")
                        continue
                    
                    original_text = text
                    
                    # Apply regex import rules
                    for regex, replacement in rewrite_rules:
                        text = regex.sub(replacement, text)
                    
                    # Fix relative imports in presentation view/serializer files
                    # e.g., if a file imports from .models, replace it with the clean architecture path
                    if "presentation\\api" in r or "presentation/api" in r:
                        if "identity" in r:
                            text = text.replace("from .models import", "from apps.identity.infrastructure.persistence.models import")
                        elif "warehouse" in r:
                            text = text.replace("from .models import", "from apps.warehouse.infrastructure.persistence.models import")
                        elif "inventory" in r:
                            text = text.replace("from .models import", "from apps.inventory.infrastructure.persistence.models import")
                        elif "orders" in r:
                            text = text.replace("from .models import", "from apps.orders.infrastructure.persistence.models import")
                        elif "inbound" in r:
                            text = text.replace("from .models import", "from apps.inbound.infrastructure.persistence.models import")

                    # Fix internal model imports (remove direct models cross-imports since they are merged in same models.py)
                    # For example, in zone_models: from apps.warehouse.infrastructure.persistence.models import Warehouse is unnecessary as it's merged
                    if "infrastructure\\persistence" in r or "infrastructure/persistence" in r:
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Warehouse", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Rack", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import NavigationNode", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Zone", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Bin, Shelf", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Bin", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Shelf", "")
                        text = text.replace("from apps.inventory.infrastructure.persistence.models import Product", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import OptimizedRoute", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Warehouse, Rack, SpatialEntity, NavigationNode, WarehousePath, RackCoordinate", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import Rack, Warehouse", "")
                        text = text.replace("from apps.warehouse.infrastructure.persistence.models import NavigationNode, WarehousePath", "")
                    
                    # Fix migrations dependencies
                    if "migrations" in r:
                        text = text.replace("('users', ", "('identity', ")
                        text = text.replace("('audit_logs', ", "('identity', ")
                        text = text.replace("('warehouses', ", "('warehouse', ")
                        text = text.replace("('zones', ", "('warehouse', ")
                        text = text.replace("('routes', ", "('warehouse', ")
                        text = text.replace("('products', ", "('inventory', ")
                        text = text.replace("('inventory', ", "('inventory', ")
                        text = text.replace("('movements', ", "('inventory', ")
                        text = text.replace("('recommendations', ", "('inventory', ")
                        text = text.replace("('dashboards', ", "('inventory', ")
                        text = text.replace("('ocr', ", "('inbound', ")
                        text = text.replace("('inbound', ", "('inbound', ")

                    # Fix Django models foreign keys string references in models
                    # e.g., 'warehouse.Warehouse' -> 'warehouse.Warehouse'
                    text = text.replace("'identity.User'", "'identity.User'")
                    text = text.replace("'warehouse.Warehouse'", "'warehouse.Warehouse'")
                    text = text.replace("'warehouse.Rack'", "'warehouse.Rack'")
                    text = text.replace("'warehouse.NavigationNode'", "'warehouse.NavigationNode'")
                    text = text.replace("'warehouse.Zone'", "'warehouse.Zone'")
                    text = text.replace("'warehouse.Bin'", "'warehouse.Bin'")
                    text = text.replace("'warehouse.Shelf'", "'warehouse.Shelf'")
                    text = text.replace("'inventory.Product'", "'inventory.Product'")
                    text = text.replace("'inbound.OCRDocument'", "'inbound.OCRDocument'")
                    text = text.replace("'warehouse.OptimizedRoute'", "'warehouse.OptimizedRoute'")

                    if text != original_text:
                        with open(py_file, "w", encoding="utf-8") as file_obj:
                            file_obj.write(text)
                        print(f"Updated imports in: {py_file}")

    # 7. Update settings.py
    settings_file = os.path.join(root_dir, "config/settings.py")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Replace INSTALLED_APPS apps
        old_apps = """    'apps.users.apps.UsersConfig',
    'apps.warehouses.apps.WarehousesConfig',
    'apps.zones.apps.ZonesConfig',
    'apps.bins.apps.BinsConfig',
    'apps.products.apps.ProductsConfig',
    'apps.inventory.apps.InventoryConfig',
    'apps.inbound.apps.InboundConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.movements.apps.MovementsConfig',
    'apps.recommendations.apps.RecommendationsConfig',
    'apps.dashboards.apps.DashboardsConfig',
    'apps.audit_logs.apps.AuditLogsConfig',
    'apps.routes.apps.RoutesConfig',
    'apps.ocr.apps.OcrConfig',"""
        
        new_apps = """    'apps.identity.apps.IdentityConfig',
    'apps.warehouse.apps.WarehouseConfig',
    'apps.inventory.apps.InventoryConfig',
    'apps.orders.apps.OrdersConfig',
    'apps.inbound.apps.InboundConfig',
    'apps.outbound.apps.OutboundConfig',"""
        
        text = text.replace(old_apps, new_apps)
        
        # Replace auth user model
        text = text.replace("AUTH_USER_MODEL = 'identity.User'", "AUTH_USER_MODEL = 'identity.User'")
        
        with open(settings_file, "w", encoding="utf-8") as f:
            f.write(text)
        print("Updated config/settings.py")

    # 8. Update urls.py
    urls_file = os.path.join(root_dir, "config/urls.py")
    if os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            text = f.read()
            
        old_patterns = """    path('api/users/', include('apps.users.urls')),
    path('api/layout/', include('apps.warehouses.layout_urls')),
    path('api/twin/', include('apps.warehouses.twin_urls')),
    path('api/warehouses/', include('apps.warehouses.urls')),
    path('api/zones/', include('apps.zones.urls')),
    path('api/bins/', include('apps.bins.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/inbound/', include('apps.inbound.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/movements/', include('apps.movements.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/ai/', include('apps.recommendations.ai_urls')),
    path('api/dashboards/', include('apps.dashboards.urls')),
    path('api/audit-logs/', include('apps.audit_logs.urls')),
    path('api/routes/', include('apps.routes.urls')),
    path('api/ocr/', include('apps.ocr.urls')),"""
        
        new_patterns = """    path('api/users/', include('apps.identity.presentation.api.user_urls')),
    path('api/audit-logs/', include('apps.identity.presentation.api.audit_urls')),
    
    path('api/layout/', include('apps.warehouse.presentation.api.layout_urls')),
    path('api/twin/', include('apps.warehouse.presentation.api.twin_urls')),
    path('api/warehouses/', include('apps.warehouse.presentation.api.warehouse_urls')),
    path('api/zones/', include('apps.warehouse.presentation.api.zone_urls')),
    path('api/bins/', include('apps.warehouse.presentation.api.bin_urls')),
    path('api/routes/', include('apps.warehouse.presentation.api.route_urls')),
    
    path('api/products/', include('apps.inventory.presentation.api.product_urls')),
    path('api/inventory/', include('apps.inventory.presentation.api.inventory_urls')),
    path('api/movements/', include('apps.inventory.presentation.api.movement_urls')),
    path('api/recommendations/', include('apps.inventory.presentation.api.recommendation_urls')),
    path('api/ai/', include('apps.inventory.presentation.api.ai_urls')),
    path('api/dashboards/', include('apps.inventory.presentation.api.dashboard_urls')),
    
    path('api/orders/', include('apps.orders.presentation.api.order_urls')),
    
    path('api/inbound/', include('apps.inbound.presentation.api.inbound_urls')),
    path('api/ocr/', include('apps.inbound.presentation.api.ocr_urls')),"""
        
        text = text.replace(old_patterns, new_patterns)
        with open(urls_file, "w", encoding="utf-8") as f:
            f.write(text)
        print("Updated config/urls.py")

    # 9. Clean up old directories
    for old_dir in OLD_APP_DIRS:
        full_old_dir = os.path.join(root_dir, old_dir)
        if os.path.exists(full_old_dir):
            shutil.rmtree(full_old_dir)
            print(f"Removed unnecessary old folder: {old_dir}")

    print("Codebase reorganization completed successfully!")

if __name__ == "__main__":
    main()
