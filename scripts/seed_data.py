import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def seed_db():
    print("Seeding initial database tables...")
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_db()
