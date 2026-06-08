import os

MODULES = ["identity", "warehouse", "inventory", "orders", "inbound", "outbound"]
SUBFOLDERS = [
    # Domain Layer
    "domain/entities",
    "domain/value_objects",
    "domain/exceptions",
    "domain/events",
    "domain/repositories",
    # Application Layer
    "application/use_cases",
    "application/dtos",
    "application/event_handlers",
    # Infrastructure Layer
    "infrastructure/persistence",
    "infrastructure/external_services",
    "infrastructure/messaging",
    # Presentation Layer
    "presentation/api"
]

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps"))
    print(f"Creating skeletons in base directory: {base_dir}")

    for module in MODULES:
        module_path = os.path.join(base_dir, module)
        # Create module init file
        os.makedirs(module_path, exist_ok=True)
        with open(os.path.join(module_path, "__init__.py"), "w") as f:
            f.write(f'# {module.capitalize()} bounded context\n')

        # Create layers
        for sub in SUBFOLDERS:
            full_path = os.path.join(module_path, sub)
            os.makedirs(full_path, exist_ok=True)
            
            # Create a __init__.py or .gitkeep to ensure it's tracked
            init_file = os.path.join(full_path, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    f.write("# Auto-generated package init\n")
            print(f"  Created: {full_path}")

    print("Skeleton creation complete!")

if __name__ == "__main__":
    main()
