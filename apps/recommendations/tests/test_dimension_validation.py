from django.test import TestCase
from decimal import Decimal
from unittest.mock import MagicMock
from apps.recommendations.services.dimension_validation import (
    validate_bin_dimensions,
    validate_product_dimensions,
    DimensionValidationError,
    safe_decimal,
    ValidatedDimension
)

class DimensionValidationTestCase(TestCase):
    def test_safe_decimal_valid(self):
        self.assertEqual(safe_decimal("12.50", Decimal("10.0"), "test_field", "test_id"), Decimal("12.50"))
        self.assertEqual(safe_decimal(15, Decimal("10.0"), "test_field", "test_id"), Decimal("15"))
        self.assertEqual(safe_decimal(Decimal("25.3"), Decimal("10.0"), "test_field", "test_id"), Decimal("25.3"))

    def test_safe_decimal_fallbacks(self):
        # Test None
        self.assertEqual(safe_decimal(None, Decimal("20.0"), "test_field", "test_id"), Decimal("20.0"))
        # Test Empty string
        self.assertEqual(safe_decimal("  ", Decimal("20.0"), "test_field", "test_id"), Decimal("20.0"))
        # Test Invalid string
        self.assertEqual(safe_decimal("abc", Decimal("20.0"), "test_field", "test_id"), Decimal("20.0"))
        # Test Negative
        self.assertEqual(safe_decimal("-5.5", Decimal("20.0"), "test_field", "test_id"), Decimal("20.0"))

    def test_validate_bin_dimensions_valid(self):
        mock_bin = MagicMock()
        mock_bin.id = "bin-uuid"
        mock_bin.bin_code = "BIN-A-01"
        mock_bin.length = Decimal("10.0")
        mock_bin.width = Decimal("15.0")
        mock_bin.height = Decimal("20.0")
        
        # Mock the relationships to check safety
        mock_bin.shelf.rack.zone.warehouse.id = "wh-uuid"
        
        validated = validate_bin_dimensions(mock_bin)
        self.assertIsInstance(validated, ValidatedDimension)
        self.assertEqual(validated.length, Decimal("10.0"))
        self.assertEqual(validated.width, Decimal("15.0"))
        self.assertEqual(validated.height, Decimal("20.0"))

    def test_validate_bin_dimensions_invalid(self):
        mock_bin = MagicMock()
        mock_bin.id = "bin-uuid"
        mock_bin.bin_code = "BIN-A-01"
        mock_bin.length = Decimal("-10.0")  # Invalid negative
        mock_bin.width = None                # Invalid None
        mock_bin.height = "abc"              # Invalid format

        with self.assertRaises(DimensionValidationError) as context:
            validate_bin_dimensions(mock_bin)
            
        self.assertIn("Invalid dimensions for bin", str(context.exception))
        self.assertIn("non-positive", str(context.exception))
        self.assertIn("is None", str(context.exception))
        self.assertIn("not a valid decimal", str(context.exception))

    def test_validate_product_dimensions_valid(self):
        mock_product_dim = MagicMock()
        mock_product_dim.id = "prod-dim-uuid"
        mock_product_dim.product.sku = "SKU-TEST"
        mock_product_dim.length = Decimal("5.5")
        mock_product_dim.width = Decimal("6.6")
        mock_product_dim.height = Decimal("7.7")
        
        validated = validate_product_dimensions(mock_product_dim)
        self.assertIsInstance(validated, ValidatedDimension)
        self.assertEqual(validated.length, Decimal("5.5"))
        self.assertEqual(validated.width, Decimal("6.6"))
        self.assertEqual(validated.height, Decimal("7.7"))

    def test_validate_product_dimensions_invalid(self):
        mock_product_dim = MagicMock()
        mock_product_dim.id = "prod-dim-uuid"
        mock_product_dim.product.sku = "SKU-TEST"
        mock_product_dim.length = Decimal("0.0")  # Invalid non-positive
        mock_product_dim.width = "  "             # Invalid empty string
        mock_product_dim.height = None            # Invalid None

        with self.assertRaises(DimensionValidationError) as context:
            validate_product_dimensions(mock_product_dim)
            
        self.assertIn("Invalid dimensions for product", str(context.exception))
        self.assertIn("non-positive", str(context.exception))
        self.assertIn("is empty", str(context.exception))
        self.assertIn("is None", str(context.exception))
