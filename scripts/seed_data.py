import os
import sys
import django
import random
import uuid
import json
from datetime import datetime, timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.db import connection

def batch_insert(cursor, table, columns, records):
    if not records:
        return
        
    from django.db import connection
    db_cols = connection.introspection.get_table_description(cursor, table)
    
    # Auto-fill missing NOT NULL columns that do not have database-level defaults
    for col_info in db_cols:
        col_name = col_info.name
        if col_name not in columns and not col_info.null_ok and col_info.default is None:
            # Decide sensible default value based on type or column name
            name_lower = col_name.lower()
            val = ""
            if "date" in name_lower or "time" in name_lower or "joined" in name_lower:
                val = datetime.utcnow()
            elif "is_" in name_lower or name_lower in ["active", "staff", "superuser"]:
                val = False
            elif "int" in name_lower or "qty" in name_lower or "quantity" in name_lower:
                val = 0
            elif col_info.type_code in ["integer", "real", "numeric"] or "int" in str(col_info.type_code).lower():
                val = 0
            elif col_info.type_code in [3802, "jsonb", "json"] or "json" in str(col_info.type_code).lower():
                val = "[]"
                
            columns.append(col_name)
            for i, r in enumerate(records):
                if isinstance(r, dict):
                    r[col_name] = val
                else:
                    records[i] = list(r) + [val]
                    
    col_str = ",".join(columns)
    row_placeholder = "(" + ",".join(["%s"] * len(columns)) + ")"
    placeholders = ",".join([row_placeholder] * len(records))
    
    flat_args = []
    for r in records:
        if isinstance(r, dict):
            for col in columns:
                flat_args.append(r[col])
        else:
            flat_args.extend(r)
            
    if connection.vendor == 'sqlite':
        import uuid as uuid_mod
        def clean_uuid(val):
            if isinstance(val, uuid_mod.UUID):
                return val.hex
            if isinstance(val, str) and len(val) == 36 and val.count('-') == 4:
                try:
                    return uuid_mod.UUID(val).hex
                except ValueError:
                    pass
            return val
        flat_args = [clean_uuid(arg) for arg in flat_args]
            
    query = f"INSERT INTO {table} ({col_str}) VALUES {placeholders}"
    cursor.execute(query, flat_args)

def seed_db():
    print("Seeding initial database tables with enterprise mock data (optimized batch insert)...")
    
    random.seed(42) # For reproducible random data
    
    # 20 Months Time Horizon
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=20 * 30) # approx 20 months
    
    def get_random_timestamp():
        delta_seconds = int((end_time - start_time).total_seconds())
        random_seconds = random.randint(0, delta_seconds)
        return start_time + timedelta(seconds=random_seconds)

    # 1. Warehouses
    warehouse_id = str(uuid.uuid4())
    warehouse_name = "Enterprise Fulfillment Center"
    warehouse_loc = "8000 Industrial Pkwy, Suite A"
    total_area_sqft = 8000
    
    # 2. Warehouse Layouts
    layout_id = str(uuid.uuid4())
    layout_name = "8K SqFt Optimised 3D Grid"
    cad_file_url = "https://assets.warehouse-twin.ai/layouts/8k_layout_v3.dwg"
    w_width, w_height, w_depth = 100.0, 28.0, 80.0
    
    # 3. Zones (excluding A4 and D4 as requested)
    # Zone Types: FAST, MEDIUM, HEAVY, SMALL_PARTS
    zone_definitions = [
        # Zone Group A (Fast Moving): A1, A2, A3
        {"name": "Zone A1", "type": "FAST", "x": 10.0, "y": 0.0, "z": 0.0, "w": 20.0, "h": 20.0, "d": 20.0},
        {"name": "Zone A2", "type": "FAST", "x": 30.0, "y": 0.0, "z": 0.0, "w": 20.0, "h": 20.0, "d": 20.0},
        {"name": "Zone A3", "type": "FAST", "x": 50.0, "y": 0.0, "z": 0.0, "w": 20.0, "h": 20.0, "d": 20.0},
        # Zone Group B (Medium Moving): B1, B2, B3
        {"name": "Zone B1", "type": "MEDIUM", "x": 10.0, "y": 0.0, "z": 25.0, "w": 20.0, "h": 20.0, "d": 20.0},
        {"name": "Zone B2", "type": "MEDIUM", "x": 30.0, "y": 0.0, "z": 25.0, "w": 20.0, "h": 20.0, "d": 20.0},
        {"name": "Zone B3", "type": "MEDIUM", "x": 50.0, "y": 0.0, "z": 25.0, "w": 20.0, "h": 20.0, "d": 20.0},
        # Zone Group C (Heavy/Pallet): C1, C2, C3, C4
        {"name": "Zone C1", "type": "HEAVY", "x": 10.0, "y": 0.0, "z": 50.0, "w": 15.0, "h": 25.0, "d": 20.0},
        {"name": "Zone C2", "type": "HEAVY", "x": 28.0, "y": 0.0, "z": 50.0, "w": 15.0, "h": 25.0, "d": 20.0},
        {"name": "Zone C3", "type": "HEAVY", "x": 46.0, "y": 0.0, "z": 50.0, "w": 15.0, "h": 25.0, "d": 20.0},
        {"name": "Zone C4", "type": "HEAVY", "x": 64.0, "y": 0.0, "z": 50.0, "w": 15.0, "h": 25.0, "d": 20.0},
        # Zone Group D (Small Parts): D1, D2, D3
        {"name": "Zone D1", "type": "SMALL_PARTS", "x": 75.0, "y": 0.0, "z": 10.0, "w": 10.0, "h": 15.0, "d": 15.0},
        {"name": "Zone D2", "type": "SMALL_PARTS", "x": 75.0, "y": 0.0, "z": 30.0, "w": 10.0, "h": 15.0, "d": 15.0},
        {"name": "Zone D3", "type": "SMALL_PARTS", "x": 75.0, "y": 0.0, "z": 50.0, "w": 10.0, "h": 15.0, "d": 15.0},
    ]
    
    zones = []
    for zd in zone_definitions:
        zones.append({
            "id": str(uuid.uuid4()),
            "name": zd["name"],
            "type": zd["type"],
            "x": zd["x"], "y": zd["y"], "z": zd["z"],
            "w": zd["w"], "h": zd["h"], "d": zd["d"]
        })

    # 4. Racks
    # Generate 2 racks per zone (Total 26 racks)
    racks = []
    for z in zones:
        for r_num in range(1, 3):
            rack_code = f"RACK-{z['name'].split()[-1]}-{r_num:02d}"
            racks.append({
                "id": str(uuid.uuid4()),
                "zone_id": z["id"],
                "code": rack_code,
                "max_weight": 5000.0 if z["type"] == "HEAVY" else 1500.0,
                "x": z["x"] + (r_num * 4), "y": z["y"], "z": z["z"] + 2,
                "w": 8.0, "h": 12.0, "d": 4.0,
                "rotation": 0.0
            })

    # 5. Shelves
    # 4 shelves per rack
    shelves = []
    for r in racks:
        for s_num in range(1, 5):
            shelves.append({
                "id": str(uuid.uuid4()),
                "rack_id": r["id"],
                "number": s_num,
                "max_weight": r["max_weight"] / 4,
                "height": (s_num - 1) * 3.0
            })

    # 6. Bins (Actual storage locations)
    # 3 bins per shelf
    bins = []
    for s in shelves:
        # Find the parent rack to construct a clean bin code
        parent_rack = next(r for r in racks if r["id"] == s["rack_id"])
        for b_num in range(1, 4):
            bin_code = f"{parent_rack['code']}-L{s['number']}-B{b_num:02d}"
            bins.append({
                "id": str(uuid.uuid4()),
                "shelf_id": s["id"],
                "code": bin_code,
                "max_capacity": 100.0,
                "current_capacity": 0.0,
                "is_occupied": False,
                "length": float(settings.DEFAULT_BIN_LENGTH),
                "width": float(settings.DEFAULT_BIN_WIDTH),
                "height": float(settings.DEFAULT_BIN_HEIGHT)
            })

    # 7. CAD Objects
    cad_objects = []
    for r in racks:
        cad_objects.append({
            "id": str(uuid.uuid4()),
            "type": "RACK",
            "label": f"Detected Rack {r['code']}",
            "conf": round(0.94 + (random.random() * 0.05), 3),
            "x": r["x"], "y": r["y"], "z": r["z"],
            "w": r["w"], "h": r["h"], "d": r["d"]
        })
    station_names = ["Dock Door Inbound", "Dock Door Outbound", "Packing Station 1", "Packing Station 2"]
    for i, s_name in enumerate(station_names):
        cad_objects.append({
            "id": str(uuid.uuid4()),
            "type": "STATION",
            "label": s_name,
            "conf": 0.99,
            "x": 5.0 + (i * 20.0), "y": 0.0, "z": 1.0,
            "w": 5.0, "h": 8.0, "d": 5.0
        })

    # 8. ML Extractions
    ml_extractions = []
    for co in cad_objects:
        extracted_data = {
            "bbox_3d": {"center": [co["x"], co["y"], co["z"]], "size": [co["w"], co["h"], co["d"]]},
            "class_probabilities": {co["type"]: co["conf"], "OTHER": round(1.0 - co["conf"], 3)},
            "processing_metadata": {"gpu_id": "cuda:0", "inference_latency_ms": 12.5}
        }
        ml_extractions.append({
            "id": str(uuid.uuid4()),
            "object_id": co["id"],
            "extracted_data": json.dumps(extracted_data),
            "model_version": "yolov8-3dwms-v2.1"
        })

    # 9. Product Categories
    categories = [
        {"id": str(uuid.uuid4()), "name": "Wireless Devices"},
        {"id": str(uuid.uuid4()), "name": "Power Chargers & Adapters"},
        {"id": str(uuid.uuid4()), "name": "Earbuds & Audio"},
        {"id": str(uuid.uuid4()), "name": "Fasteners & Hardware"},
        {"id": str(uuid.uuid4()), "name": "Scanner Accessories"}
    ]

    # 10. Products (150 product distribution strategy)
    products = []
    brands = ["Logitech", "Anker", "JBL", "Sony", "Bose", "Samsung", "Apple", "Belkin", "Milwaukee", "DeWalt"]
    product_adjectives = ["Pro", "Elite", "Ultra", "Max", "Mini", "Super", "Industrial", "Heavy-Duty", "Standard", "Slim"]
    
    category_product_types = {
        "Wireless Devices": ["Mouse", "Keyboard", "Presenter Clicker", "Trackball", "Wireless Receiver"],
        "Power Chargers & Adapters": ["Wall Charger", "USB-C Cable", "Power Bank", "Wireless Charging Pad", "Car Charger"],
        "Earbuds & Audio": ["TWS Earbuds", "Noise Cancelling Headphones", "Bluetooth Speaker", "Audio Adapter", "Microphone"],
        "Fasteners & Hardware": ["Steel Screws Pack", "Wall Anchors", "Bolts Kit", "L-Bracket", "Hex Nuts Set"],
        "Scanner Accessories": ["Holster", "Charging Dock", "Hand Strap", "Protective Boot", "Battery Pack"]
    }

    for i in range(1, 151):
        cat = random.choice(categories)
        p_types = category_product_types[cat["name"]]
        p_type = random.choice(p_types)
        brand = random.choice(brands)
        adj = random.choice(product_adjectives)
        
        sku = f"SKU-{cat['name'][:3].upper()}-{10000 + i}"
        name = f"{brand} {adj} {p_type}"
        weight = round(random.uniform(0.1, 15.0), 2)
        is_fragile = random.random() < 0.15
        is_hazardous = (cat["name"] == "Power Chargers & Adapters") and (random.random() < 0.2)
        
        products.append({
            "id": str(uuid.uuid4()),
            "category_id": cat["id"],
            "sku": sku,
            "name": name,
            "weight": weight,
            "is_fragile": is_fragile,
            "is_hazardous": is_hazardous
        })

    # 11. Product Dimensions
    product_dimensions = []
    for p in products:
        length = round(random.uniform(2.0, 18.0), 1)
        width = round(random.uniform(1.5, 12.0), 1)
        height = round(random.uniform(0.5, 10.0), 1)
        product_dimensions.append({
            "id": str(uuid.uuid4()),
            "product_id": p["id"],
            "length": length,
            "width": width,
            "height": height,
            "box_length": length + 0.5,
            "box_width": width + 0.5,
            "box_height": height + 0.5
        })

    # 12. Product Storage Rules
    product_rules = []
    for p in products:
        allowed_zones = ["FAST", "MEDIUM"]
        if p["is_hazardous"]:
            allowed_zones = ["HEAVY"]
        elif p["weight"] > 10.0:
            allowed_zones = ["HEAVY"]
        elif p["weight"] < 0.5:
            allowed_zones = ["SMALL_PARTS"]

        product_rules.append({
            "id": str(uuid.uuid4()),
            "product_id": p["id"],
            "allowed_zone_type": random.choice(allowed_zones),
            "max_stack_height": random.choice([3, 5, 10]),
            "required_temp": round(random.uniform(18.0, 24.0), 1),
            "orientation_rule": random.choice(["UPRIGHT_ONLY", "NO_RESTRICTION", "FACE_FORWARD"])
        })

    # 13. Inventory
    inventory = []
    for p in products:
        total_qty = random.randint(10, 1000)
        reserved_qty = int(total_qty * random.uniform(0.0, 0.15))
        damaged_qty = int(total_qty * random.uniform(0.0, 0.02))
        inventory.append({
            "id": str(uuid.uuid4()),
            "product_id": p["id"],
            "total_quantity": total_qty,
            "reserved_quantity": reserved_qty,
            "damaged_quantity": damaged_qty
        })

    # 14. Inbound Shipments
    inbound_shipments = []
    for i in range(1, 101):
        shipment_time = get_random_timestamp()
        status = "COMPLETED" if shipment_time < end_time - timedelta(days=2) else random.choice(["EXPECTED", "ARRIVED"])
        inbound_shipments.append({
            "id": str(uuid.uuid4()),
            "code": f"INB-PO-{2024 + (i // 50)}-{i:04d}",
            "supplier": f"{random.choice(brands)} Logistics Ltd.",
            "arrival": shipment_time,
            "status": status
        })

    # 15. Outbound Shipments
    outbound_shipments = []
    customers = ["Amazon Fulfillment", "Best Buy Corp", "Walmart Stores", "Target Supply", "D2C Direct Customer"]
    for i in range(1, 201):
        dispatch_time = get_random_timestamp()
        status = "COMPLETED" if dispatch_time < end_time - timedelta(days=1) else random.choice(["NEW", "PENDING"])
        outbound_shipments.append({
            "id": str(uuid.uuid4()),
            "code": f"OUT-ORD-{2024 + (i // 100)}-{i:04d}",
            "customer": random.choice(customers),
            "dispatch": dispatch_time,
            "status": status
        })

    # 16. Stock Movements (250 records over 20 months)
    stock_movements = []
    movement_types = ["PUTAWAY", "REPLENISHMENT", "FIFO_ROTATION", "CYCLE_COUNT_ADJUSTMENT"]
    for i in range(250):
        prod = random.choice(products)
        from_b = random.choice(bins)
        to_b = random.choice(bins)
        while from_b["id"] == to_b["id"]:
            to_b = random.choice(bins)
        
        stock_movements.append({
            "id": str(uuid.uuid4()),
            "product_id": prod["id"],
            "from_bin": from_b["id"],
            "to_bin": to_b["id"],
            "quantity": random.randint(1, 50),
            "type": random.choice(movement_types),
            "moved_at": get_random_timestamp()
        })

    # 17. Storage Allocations
    storage_allocations = []
    bin_occupations = {}
    for inv in inventory:
        prod_id = inv["product_id"]
        qty_left = inv["total_quantity"]
        num_allocs = random.randint(1, 3)
        for _ in range(num_allocs):
            if qty_left <= 0:
                break
            alloc_qty = qty_left if num_allocs == 1 else random.randint(1, qty_left)
            qty_left -= alloc_qty
            
            target_bin = random.choice(bins)
            storage_allocations.append({
                "id": str(uuid.uuid4()),
                "product_id": prod_id,
                "bin_id": target_bin["id"],
                "quantity": alloc_qty,
                "allocated_at": get_random_timestamp()
            })
            bin_occupations[target_bin["id"]] = bin_occupations.get(target_bin["id"], 0) + alloc_qty

    # Update current bin capacities
    for b in bins:
        total_qty_in_bin = bin_occupations.get(b["id"], 0)
        if total_qty_in_bin > 0:
            b["current_capacity"] = total_qty_in_bin
            b["is_occupied"] = True

    # 18. Allocation Recommendations
    allocation_recs = []
    reasoning_templates = [
        {"reason": "Optimal velocity routing. Placing item near entry point.", "score_multiplier": 1.0},
        {"reason": "Adhering to strict hazard-isolation protocol for battery devices.", "score_multiplier": 1.1},
        {"reason": "Compatible product density weight limits.", "score_multiplier": 0.95},
        {"reason": "Fragile packing safety recommendation.", "score_multiplier": 1.05}
    ]
    for i in range(120):
        prod = random.choice(products)
        rec_b = random.choice(bins)
        template = random.choice(reasoning_templates)
        conf = round(min(0.99, 0.70 + (random.random() * 0.28) * template["score_multiplier"]), 3)
        
        allocation_recs.append({
            "id": str(uuid.uuid4()),
            "product_id": prod["id"],
            "recommended_bin": rec_b["id"],
            "confidence_score": conf,
            "reasoning": json.dumps({
                "logic": template["reason"],
                "calculated_at": get_random_timestamp().isoformat(),
                "model": "wms-slotting-nn-v3"
            }),
            "created_at": get_random_timestamp()
        })

    # 19. Route Optimizations
    route_opts = []
    locations_list = [f"Dock Inbound {i}" for i in range(1, 3)] + [f"Aisle {chr(65+i)}{j}" for i in range(4) for j in range(1, 4)]
    for i in range(80):
        src = random.choice(locations_list)
        dest = random.choice(locations_list)
        while src == dest:
            dest = random.choice(locations_list)
        
        route_opts.append({
            "id": str(uuid.uuid4()),
            "src": src,
            "dest": dest,
            "path": json.dumps({
                "nodes": [src, "Intersection-Center", "Aisle-Access-Way", dest],
                "distance_meters": round(random.uniform(5.0, 45.0), 2)
            }),
            "est_time": round(random.uniform(10.0, 120.0), 1),
            "created_at": get_random_timestamp()
        })

    # 20. Warehouse Heatmaps
    warehouse_heatmaps = []
    for z in zones:
        warehouse_heatmaps.append({
            "id": str(uuid.uuid4()),
            "zone_id": z["id"],
            "score": round(random.uniform(0.1, 0.99), 3),
            "gen_at": get_random_timestamp()
        })

    # 21. AI Models
    ai_models = [
        {"id": str(uuid.uuid4()), "name": "Warehouse Slotting Optimiser", "version": "v1.4", "accuracy": 0.885, "deployed": datetime.utcnow() - timedelta(days=200)},
        {"id": str(uuid.uuid4()), "name": "3D Bounding Box Extractor", "version": "v2.1", "accuracy": 0.942, "deployed": datetime.utcnow() - timedelta(days=150)},
        {"id": str(uuid.uuid4()), "name": "AGV Path Routing Engine", "version": "v0.9-beta", "accuracy": 0.910, "deployed": datetime.utcnow() - timedelta(days=80)},
    ]

    # 22. AI Predictions
    ai_predictions = []
    pred_types = ["SLOTTING_PLACEMENT", "LAYOUT_DETECTION", "ROBOT_DISPATCH_SPEED"]
    for i in range(150):
        model = random.choice(ai_models)
        p_type = random.choice(pred_types)
        ai_predictions.append({
            "id": str(uuid.uuid4()),
            "model_id": model["id"],
            "type": p_type,
            "result": json.dumps({
                "prediction": "STABLE",
                "variance": round(random.random() * 0.05, 4),
                "runtime_ms": random.randint(5, 45)
            }),
            "created_at": get_random_timestamp()
        })

    # 23. Scan Logs
    scan_logs = []
    scan_types = ["BARCODE_SCAN", "RFID_GATEWAY", "QR_CODE_SNAP", "MANUAL_ENTRY"]
    for i in range(500):
        prod = random.choice(products)
        scan_logs.append({
            "id": str(uuid.uuid4()),
            "product_id": prod["id"],
            "type": random.choice(scan_types),
            "loc": f"Aisle {random.randint(1, 10)}-Shelf {random.randint(1, 4)}",
            "scanned_at": get_random_timestamp()
        })

    # 24. Robot Tasks
    robot_tasks = []
    robot_task_types = ["PRODUCT_PICK", "REPLENISHMENT_CARRY", "EMPTY_BIN_RETRIEVAL"]
    task_statuses = ["COMPLETED", "FAILED", "IN_PROGRESS", "ABORTED"]
    for i in range(150):
        robot_tasks.append({
            "id": str(uuid.uuid4()),
            "type": random.choice(robot_task_types),
            "src": f"BIN-{random.randint(1, 10):02d}",
            "dest": f"PACKING-STATION-{random.randint(1, 3)}",
            "status": random.choices(task_statuses, weights=[0.85, 0.05, 0.05, 0.05])[0],
            "created_at": get_random_timestamp()
        })

    # 25. Users
    user_names = [
        ("Alice Vance", "alice@enterprise-wms.com", "WAREHOUSE_MANAGER"),
        ("Bob Smith", "bob@enterprise-wms.com", "INVENTORY_CLERK"),
        ("Charlie Dev", "charlie@enterprise-wms.com", "SYSTEM_ADMIN"),
        ("David Miller", "david@enterprise-wms.com", "AGV_OPERATOR"),
        ("Eva Green", "eva@enterprise-wms.com", "INVENTORY_CLERK")
    ]
    users = []
    for full_name, email, role in user_names:
        users.append({
            "id": str(uuid.uuid4()),
            "full_name": full_name,
            "email": email,
            "role": role
        })

    # 26. Audit Logs
    audit_logs = []
    actions = ["BIN_REALLOCATION", "THRESHOLD_BREACH", "USER_LOGIN", "MANUAL_ADJUSTMENT", "SYSTEM_REBOOT"]
    tables_list = ["inventory", "bins", "users", "racks", "storage_allocations"]
    for i in range(300):
        u = random.choice(users)
        audit_logs.append({
            "id": str(uuid.uuid4()),
            "user_id": u["id"],
            "action": random.choice(actions),
            "table": random.choice(tables_list),
            "record": str(uuid.uuid4()),
            "time": get_random_timestamp()
        })

    # ==========================================
    # DATABASE INSERTS
    # ==========================================
    with connection.cursor() as cursor:
        try:
            print("Clearing tables to prevent key violations...")
            if connection.vendor == 'sqlite':
                tables = ["audit_logs", "users", "robot_tasks", "scan_logs", "ai_predictions", "ai_models", "warehouse_heatmaps", "route_optimizations", "allocation_recommendations", "storage_allocations", "stock_movements", "outbound_shipments", "inbound_shipments", "inventory", "product_storage_rules", "product_dimensions", "products", "product_categories", "ml_extractions", "cad_objects", "bins", "shelves", "racks", "zones", "warehouse_layouts", "warehouses"]
                for t in tables:
                    cursor.execute(f"DELETE FROM {t};")
            else:
                cursor.execute("TRUNCATE TABLE audit_logs, users, robot_tasks, scan_logs, ai_predictions, ai_models, warehouse_heatmaps, route_optimizations, allocation_recommendations, storage_allocations, stock_movements, outbound_shipments, inbound_shipments, inventory, product_storage_rules, product_dimensions, products, product_categories, ml_extractions, cad_objects, bins, shelves, racks, zones, warehouse_layouts, warehouses CASCADE;")
            
            # 1. Warehouses
            print("Inserting Warehouse...")
            batch_insert(cursor, "warehouses", ["warehouse_id", "name", "location", "total_area_sqft"], [[warehouse_id, warehouse_name, warehouse_loc, total_area_sqft]])
            
            # 2. Warehouse Layouts
            print("Inserting Warehouse Layouts...")
            batch_insert(cursor, "warehouse_layouts", ["layout_id", "warehouse_id", "layout_name", "cad_file_url", "width", "height", "depth"], [[layout_id, warehouse_id, layout_name, cad_file_url, w_width, w_height, w_depth]])
            
            # 3. Zones
            print("Inserting Zones...")
            batch_insert(cursor, "zones", ["zone_id", "warehouse_id", "zone_name", "zone_type", "x", "y", "z", "width", "height", "depth"], 
                         [[z["id"], warehouse_id, z["name"], z["type"], z["x"], z["y"], z["z"], z["w"], z["h"], z["d"]] for z in zones])
                
            # 4. Racks
            print("Inserting Racks...")
            batch_insert(cursor, "racks", ["rack_id", "zone_id", "rack_code", "max_weight", "x", "y", "z", "width", "height", "depth", "rotation_angle"],
                         [[r["id"], r["zone_id"], r["code"], r["max_weight"], r["x"], r["y"], r["z"], r["w"], r["h"], r["d"], r["rotation"]] for r in racks])
                
            # 5. Shelves
            print("Inserting Shelves...")
            batch_insert(cursor, "shelves", ["shelf_id", "rack_id", "shelf_number", "max_weight", "height_from_ground"],
                         [[s["id"], s["rack_id"], s["number"], s["max_weight"], s["height"]] for s in shelves])
                
            # 6. Bins
            print("Inserting Bins...")
            batch_insert(cursor, "bins", ["bin_id", "shelf_id", "bin_code", "max_capacity", "current_capacity", "is_occupied", "length", "width", "height"],
                         [[b["id"], b["shelf_id"], b["code"], b["max_capacity"], b["current_capacity"], b["is_occupied"], b["length"], b["width"], b["height"]] for b in bins])
                
            # 7. CAD Objects
            print("Inserting CAD Objects...")
            batch_insert(cursor, "cad_objects", ["object_id", "layout_id", "object_type", "detected_label", "confidence_score", "x", "y", "z", "width", "height", "depth"],
                         [[co["id"], layout_id, co["type"], co["label"], co["conf"], co["x"], co["y"], co["z"], co["w"], co["h"], co["d"]] for co in cad_objects])
                
            # 8. ML Extractions
            print("Inserting ML Extractions...")
            batch_insert(cursor, "ml_extractions", ["extraction_id", "object_id", "extracted_data", "model_version"],
                         [[mle["id"], mle["object_id"], mle["extracted_data"], mle["model_version"]] for mle in ml_extractions])
                
            # 9. Product Categories
            print("Inserting Product Categories...")
            batch_insert(cursor, "product_categories", ["category_id", "category_name"],
                         [[cat["id"], cat["name"]] for cat in categories])
                
            # 10. Products
            print("Inserting Products...")
            batch_insert(cursor, "products", ["product_id", "category_id", "sku", "product_name", "weight", "is_fragile", "is_hazardous"],
                         [[p["id"], p["category_id"], p["sku"], p["name"], p["weight"], p["is_fragile"], p["is_hazardous"]] for p in products])
                
            # 11. Product Dimensions
            print("Inserting Product Dimensions...")
            batch_insert(cursor, "product_dimensions", ["dimension_id", "product_id", "length", "width", "height", "box_length", "box_width", "box_height"],
                         [[pd["id"], pd["product_id"], pd["length"], pd["width"], pd["height"], pd["box_length"], pd["box_width"], pd["box_height"]] for pd in product_dimensions])
                
            # 12. Product Storage Rules
            print("Inserting Product Storage Rules...")
            batch_insert(cursor, "product_storage_rules", ["rule_id", "product_id", "allowed_zone_type", "max_stack_height", "required_temperature", "orientation_rule"],
                         [[pr["id"], pr["product_id"], pr["allowed_zone_type"], pr["max_stack_height"], pr["required_temp"], pr["orientation_rule"]] for pr in product_rules])
                
            # 13. Inventory
            print("Inserting Inventory...")
            batch_insert(cursor, "inventory", ["inventory_id", "product_id", "total_quantity", "reserved_quantity", "damaged_quantity"],
                         [[inv["id"], inv["product_id"], inv["total_quantity"], inv["reserved_quantity"], inv["damaged_quantity"]] for inv in inventory])
                
            # 14. Inbound Shipments
            print("Inserting Inbound Shipments...")
            batch_insert(cursor, "inbound_shipments", ["inbound_id", "shipment_code", "supplier_name", "expected_arrival", "status"],
                         [[iship["id"], iship["code"], iship["supplier"], iship["arrival"], iship["status"]] for iship in inbound_shipments])
                
            # 15. Outbound Shipments
            print("Inserting Outbound Shipments...")
            batch_insert(cursor, "outbound_shipments", ["outbound_id", "shipment_code", "customer_name", "dispatch_time", "status"],
                         [[oship["id"], oship["code"], oship["customer"], oship["dispatch"], oship["status"]] for oship in outbound_shipments])
                
            # 16. Stock Movements
            print("Inserting Stock Movements...")
            batch_insert(cursor, "stock_movements", ["movement_id", "product_id", "from_bin", "to_bin", "quantity", "movement_type", "moved_at"],
                         [[sm["id"], sm["product_id"], sm["from_bin"], sm["to_bin"], sm["quantity"], sm["type"], sm["moved_at"]] for sm in stock_movements])
                
            # 17. Storage Allocations
            print("Inserting Storage Allocations...")
            batch_insert(cursor, "storage_allocations", ["allocation_id", "product_id", "bin_id", "quantity", "allocated_at"],
                         [[sa["id"], sa["product_id"], sa["bin_id"], sa["quantity"], sa["allocated_at"]] for sa in storage_allocations])
                
            # 18. Allocation Recommendations
            print("Inserting Allocation Recommendations...")
            batch_insert(cursor, "allocation_recommendations", ["recommendation_id", "product_id", "recommended_bin", "confidence_score", "reasoning", "created_at"],
                         [[ar["id"], ar["product_id"], ar["recommended_bin"], ar["confidence_score"], ar["reasoning"], ar["created_at"]] for ar in allocation_recs])
                
            # 19. Route Optimizations
            print("Inserting Route Optimizations...")
            batch_insert(cursor, "route_optimizations", ["route_id", "source_location", "destination_location", "optimized_path", "estimated_time", "created_at"],
                         [[ro["id"], ro["src"], ro["dest"], ro["path"], ro["est_time"], ro["created_at"]] for ro in route_opts])
                
            # 20. Warehouse Heatmaps
            print("Inserting Warehouse Heatmaps...")
            batch_insert(cursor, "warehouse_heatmaps", ["heatmap_id", "zone_id", "activity_score", "generated_at"],
                         [[wh["id"], wh["zone_id"], wh["score"], wh["gen_at"]] for wh in warehouse_heatmaps])
                
            # 21. AI Models
            print("Inserting AI Models...")
            batch_insert(cursor, "ai_models", ["model_id", "model_name", "model_version", "accuracy", "deployed_at"],
                         [[am["id"], am["name"], am["version"], am["accuracy"], am["deployed"]] for am in ai_models])
                
            # 22. AI Predictions
            print("Inserting AI Predictions...")
            batch_insert(cursor, "ai_predictions", ["prediction_id", "model_id", "prediction_type", "prediction_result", "created_at"],
                         [[ap["id"], ap["model_id"], ap["type"], ap["result"], ap["created_at"]] for ap in ai_predictions])
                
            # 23. Scan Logs
            print("Inserting Scan Logs...")
            batch_insert(cursor, "scan_logs", ["scan_id", "product_id", "scan_type", "scanned_location", "scanned_at"],
                         [[sl["id"], sl["product_id"], sl["type"], sl["loc"], sl["scanned_at"]] for sl in scan_logs])
                
            # 24. Robot Tasks
            print("Inserting Robot Tasks...")
            batch_insert(cursor, "robot_tasks", ["task_id", "task_type", "source_location", "destination_location", "status", "created_at"],
                         [[rt["id"], rt["type"], rt["src"], rt["dest"], rt["status"], rt["created_at"]] for rt in robot_tasks])
                
            # 25. Users
            print("Inserting Users...")
            user_records = []
            for u in users:
                username = u["email"].split('@')[0]
                password = "pbkdf2_sha256$260000$dummy$dummy"
                is_superuser = False
                is_staff = False
                is_active = True
                user_records.append([
                    u["id"], u["full_name"], u["email"], u["role"],
                    username, password, is_superuser, is_staff, is_active
                ])
            batch_insert(cursor, "users", 
                         ["user_id", "full_name", "email", "role", "username", "password", "is_superuser", "is_staff", "is_active"],
                         user_records)
                
            # 26. Audit Logs
            print("Inserting Audit Logs...")
            batch_insert(cursor, "audit_logs", ["log_id", "user_id", "action_type", "table_name", "record_id", "action_time"],
                         [[al["id"], al["user_id"], al["action"], al["table"], al["record"], al["time"]] for al in audit_logs])

            print("Database transaction commit...")
            connection.commit()
            print("All 26 tables successfully seeded in Neon PostgreSQL!")

        except Exception as e:
            print(f"Error seeding database: {e}")
            connection.rollback()
            raise e

if __name__ == '__main__':
    seed_db()
