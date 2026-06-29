import os
import sys
import django
from decimal import Decimal, InvalidOperation

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from apps.warehouse.models import Bin
from django.db import transaction

def repair_dimensions():
    print("Starting database bin dimensions repair script...")
    print(f"Defaults from settings: L={settings.DEFAULT_BIN_LENGTH}, W={settings.DEFAULT_BIN_WIDTH}, H={settings.DEFAULT_BIN_HEIGHT}")
    
    bins = Bin.objects.all()
    checked_count = 0
    repaired_count = 0
    
    with transaction.atomic():
        for bin_obj in bins:
            checked_count += 1
            needs_repair = False
            
            # Check length
            l_val = bin_obj.length
            try:
                if l_val is None or Decimal(str(l_val)) <= 0:
                    needs_repair = True
            except (InvalidOperation, ValueError, TypeError):
                needs_repair = True
                
            # Check width
            w_val = bin_obj.width
            try:
                if w_val is None or Decimal(str(w_val)) <= 0:
                    needs_repair = True
            except (InvalidOperation, ValueError, TypeError):
                needs_repair = True
                
            # Check height
            h_val = bin_obj.height
            try:
                if h_val is None or Decimal(str(h_val)) <= 0:
                    needs_repair = True
            except (InvalidOperation, ValueError, TypeError):
                needs_repair = True
                
            if needs_repair:
                # Update with defaults
                old_dims = f"L={l_val}, W={w_val}, H={h_val}"
                bin_obj.length = settings.DEFAULT_BIN_LENGTH
                bin_obj.width = settings.DEFAULT_BIN_WIDTH
                bin_obj.height = settings.DEFAULT_BIN_HEIGHT
                bin_obj.save()
                
                new_dims = f"L={bin_obj.length}, W={bin_obj.width}, H={bin_obj.height}"
                print(f"Repaired Bin {bin_obj.bin_code} (ID: {bin_obj.id}): {old_dims} -> {new_dims}")
                repaired_count += 1
                
    print(f"Repair process finished. Checked {checked_count} bins, repaired {repaired_count} bins.")

if __name__ == '__main__':
    repair_dimensions()
