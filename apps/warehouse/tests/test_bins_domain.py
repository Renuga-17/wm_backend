from django.test import TestCase
from apps.warehouse.presentation.api.bin_serializers import BinSerializer
from apps.warehouse.infrastructure.persistence.models import Shelf, Rack, Zone, Warehouse, ZoneGroup
from decimal import Decimal

class BinsTestCase(TestCase):
    def setUp(self):
        # Create standard layout prerequisites
        self.warehouse = Warehouse.objects.create(name='Test Warehouse')
        self.zone_group = ZoneGroup.objects.create(warehouse=self.warehouse, code='A', name='Group A')
        self.zone = Zone.objects.create(
            warehouse=self.warehouse, zone_group=self.zone_group, zone_name='Z1', zone_type='GENERAL',
            x=0, y=0, z=0, width=10, height=10, depth=10
        )
        self.rack = Rack.objects.create(
            zone=self.zone, rack_code='RACK-VALID', max_weight=500,
            x=0, y=0, z=0, width=5, height=5, depth=5, rotation_angle=0
        )
        self.shelf = Shelf.objects.create(rack=self.rack, shelf_number=1, max_weight=200, height_from_ground=0)

    def test_bin_serializer_validation_positive_values(self):
        # Test valid payload
        valid_payload = {
            'shelf': str(self.shelf.id),
            'bin_code': 'BIN-V01',
            'max_capacity': 100.0,
            'length': 10.0,
            'width': 15.0,
            'height': 20.0
        }
        serializer = BinSerializer(data=valid_payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_bin_serializer_validation_invalid_nonpositive(self):
        # Test zero length
        invalid_payload = {
            'shelf': str(self.shelf.id),
            'bin_code': 'BIN-I01',
            'max_capacity': 100.0,
            'length': 0.0,
            'width': 15.0,
            'height': 20.0
        }
        serializer = BinSerializer(data=invalid_payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn('length', serializer.errors)

        # Test negative width
        invalid_payload2 = {
            'shelf': str(self.shelf.id),
            'bin_code': 'BIN-I02',
            'max_capacity': 100.0,
            'length': 10.0,
            'width': -5.0,
            'height': 20.0
        }
        serializer = BinSerializer(data=invalid_payload2)
        self.assertFalse(serializer.is_valid())
        self.assertIn('width', serializer.errors)
