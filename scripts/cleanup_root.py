import os
import shutil

# Target destinations mapping for root level loose scripts
MOVES = {
    # Move to scripts/ (Dev & Admin tasks)
    "create_test_user.py": "scripts/create_test_user.py",
    "inspect_users.py": "scripts/inspect_users.py",
    "list_and_login.py": "scripts/list_and_login.py",
    "list_tables.py": "scripts/list_tables.py",
    "fix_imports.py": "scripts/fix_imports.py",
    "fix_imports_batch.py": "scripts/fix_imports_batch.py",
    "fix_imports_rollback.py": "scripts/fix_imports_rollback.py",
    
    # Move to tests/ (Test cases)
    "test_warehouse_api.py": "tests/test_warehouse_api.py",
    "test_zone_api.py": "tests/test_zone_api.py",
    "warehouse_api_test.py": "tests/warehouse_api_test.py",
    
    # Move to scratch/ (Temporary verification/experimental scripts)
    "temp_cad_report.py": "scratch/temp_cad_report.py",
    "temp_verify_clickhouse.py": "scratch/temp_verify_clickhouse.py",
    "verification_temp.py": "scratch/verification_temp.py",
    "verification_twin.py": "scratch/verification_twin.py",
    "verify_analytics.py": "scratch/verify_analytics.py",
    "verify_recommendation_endpoints.py": "scratch/verify_recommendation_endpoints.py"
}

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Starting root folder cleanup in: {root_dir}")
    
    for filename, rel_dest in MOVES.items():
        src_path = os.path.join(root_dir, filename)
        dest_path = os.path.join(root_dir, rel_dest)
        
        if os.path.exists(src_path):
            # Ensure target parent directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            try:
                shutil.move(src_path, dest_path)
                print(f"Moved: {filename} -> {rel_dest}")
            except Exception as e:
                print(f"Failed to move {filename}: {e}")
        else:
            print(f"Skipped (does not exist in root): {filename}")

if __name__ == "__main__":
    main()
