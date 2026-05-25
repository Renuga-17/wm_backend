import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def create_tables():
    print("Creating missing database tables...")
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rack_coordinates (
                coordinate_id UUID PRIMARY KEY,
                rack_id UUID REFERENCES racks(rack_id) ON DELETE CASCADE,
                access_point_x NUMERIC(10, 4) NOT NULL,
                access_point_y NUMERIC(10, 4) NOT NULL,
                access_point_z NUMERIC(10, 4) NOT NULL,
                side VARCHAR(50) NOT NULL
            );
        """)
        print("- Created rack_coordinates table (if not exists)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spatial_entities (
                entity_id UUID PRIMARY KEY,
                warehouse_id UUID REFERENCES warehouses(warehouse_id) ON DELETE CASCADE,
                entity_name VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                x NUMERIC(10, 4) NOT NULL,
                y NUMERIC(10, 4) NOT NULL,
                z NUMERIC(10, 4) NOT NULL,
                width NUMERIC(10, 4) NOT NULL,
                height NUMERIC(10, 4) NOT NULL,
                depth NUMERIC(10, 4) NOT NULL,
                rotation_angle NUMERIC(8, 4) NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """)
        print("- Created spatial_entities table (if not exists)")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS zone_boundaries (
                boundary_id UUID PRIMARY KEY,
                zone_id UUID REFERENCES zones(zone_id) ON DELETE CASCADE,
                polygon_points JSONB NOT NULL DEFAULT '[]'::jsonb
            );
        """)
        print("- Created zone_boundaries table (if not exists)")


if __name__ == '__main__':
    create_tables()
