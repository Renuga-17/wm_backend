import logging
from decimal import Decimal, InvalidOperation
from django.conf import settings

logger = logging.getLogger(__name__)

class DimensionValidationError(ValueError):
    """Exception raised when dimensions are invalid (None, empty, negative, or invalid format)."""
    pass

class ValidatedDimension:
    """Centralized value object for validated dimensions."""
    def __init__(self, length: Decimal, width: Decimal, height: Decimal):
        self.length = length
        self.width = width
        self.height = height

    def __repr__(self):
        return f"ValidatedDimension(length={self.length}, width={self.width}, height={self.height})"


def safe_decimal(value, default_val, name, context_id, warehouse_id=None) -> Decimal:
    """
    Emergency fallback decimal parser.
    Executes only if corrupted data somehow bypasses the validation layer.
    Logs a warning detailing the issue for data audit and returns default_val cleanly.
    """
    if value is None:
        logger.warning(
            "DATA INTEGRITY WARNING: Dimension '%s' is None for ID '%s' (Warehouse: %s). Fallback '%s' applied.",
            name, context_id, warehouse_id, default_val
        )
        return Decimal(str(default_val))
    
    val_str = str(value).strip()
    if not val_str:
        logger.warning(
            "DATA INTEGRITY WARNING: Dimension '%s' is empty for ID '%s' (Warehouse: %s). Fallback '%s' applied.",
            name, context_id, warehouse_id, default_val
        )
        return Decimal(str(default_val))
    
    try:
        dec_val = Decimal(val_str)
        if dec_val < 0:
            logger.warning(
                "DATA INTEGRITY WARNING: Dimension '%s' is negative (%s) for ID '%s' (Warehouse: %s). Fallback '%s' applied.",
                name, dec_val, context_id, warehouse_id, default_val
            )
            return Decimal(str(default_val))
        return dec_val
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning(
            "DATA INTEGRITY WARNING: Dimension '%s' has invalid format '%s' for ID '%s' (Warehouse: %s). Error: %s. Fallback '%s' applied.",
            name, val_str, context_id, warehouse_id, str(e), default_val
        )
        return Decimal(str(default_val))


def validate_bin_dimensions(bin_obj) -> ValidatedDimension:
    """
    Validates bin dimensions (length, width, height).
    Detects None, empty strings, invalid numeric formats, and negative values.
    Raises DimensionValidationError if any dimension is invalid.
    """
    bin_id = getattr(bin_obj, 'id', 'Unknown')
    bin_code = getattr(bin_obj, 'bin_code', 'Unknown')
    context_id = f"BinCode:{bin_code} (ID:{bin_id})"
    
    # Try to resolve warehouse_id
    warehouse_id = None
    try:
        if hasattr(bin_obj, 'shelf') and bin_obj.shelf:
            shelf = bin_obj.shelf
            if hasattr(shelf, 'rack') and shelf.rack:
                rack = shelf.rack
                if hasattr(rack, 'zone') and rack.zone:
                    zone = rack.zone
                    if hasattr(zone, 'warehouse') and zone.warehouse:
                        warehouse_id = zone.warehouse.id
    except Exception:
        pass

    errors = []
    dims = {}
    for name in ('length', 'width', 'height'):
        val = getattr(bin_obj, name, None)
        if val is None:
            errors.append(f"Dimension '{name}' is None")
            continue
        
        val_str = str(val).strip()
        if not val_str:
            errors.append(f"Dimension '{name}' is empty")
            continue
            
        try:
            dec_val = Decimal(val_str)
            if dec_val <= 0:
                errors.append(f"Dimension '{name}' is non-positive: {dec_val}")
            else:
                dims[name] = dec_val
        except (InvalidOperation, ValueError, TypeError) as e:
            errors.append(f"Dimension '{name}' is not a valid decimal: '{val_str}' (Error: {str(e)})")

    if errors:
        error_msg = f"Invalid dimensions for bin {context_id} in warehouse {warehouse_id}: {'; '.join(errors)}"
        raise DimensionValidationError(error_msg)

    return ValidatedDimension(length=dims['length'], width=dims['width'], height=dims['height'])


def validate_product_dimensions(product_dim_obj) -> ValidatedDimension:
    """
    Validates product dimensions (length, width, height).
    Detects None, empty strings, invalid numeric formats, and negative values.
    Raises DimensionValidationError if any dimension is invalid.
    """
    dim_id = getattr(product_dim_obj, 'id', 'Unknown')
    sku = 'Unknown'
    if hasattr(product_dim_obj, 'product') and product_dim_obj.product:
        sku = getattr(product_dim_obj.product, 'sku', 'Unknown')
    context_id = f"SKU:{sku} (DimID:{dim_id})"

    errors = []
    dims = {}
    for name in ('length', 'width', 'height'):
        val = getattr(product_dim_obj, name, None)
        if val is None:
            errors.append(f"Dimension '{name}' is None")
            continue
        
        val_str = str(val).strip()
        if not val_str:
            errors.append(f"Dimension '{name}' is empty")
            continue
            
        try:
            dec_val = Decimal(val_str)
            if dec_val <= 0:
                errors.append(f"Dimension '{name}' is non-positive: {dec_val}")
            else:
                dims[name] = dec_val
        except (InvalidOperation, ValueError, TypeError) as e:
            errors.append(f"Dimension '{name}' is not a valid decimal: '{val_str}' (Error: {str(e)})")

    if errors:
        error_msg = f"Invalid dimensions for product {context_id}: {'; '.join(errors)}"
        raise DimensionValidationError(error_msg)

    return ValidatedDimension(length=dims['length'], width=dims['width'], height=dims['height'])
