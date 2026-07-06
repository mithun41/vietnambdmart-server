import os
import glob
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Delete DB
db_path = os.path.join(BASE_DIR, "db.sqlite3")
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("Deleted db.sqlite3")
    except Exception as e:
        print(f"Error deleting db: {e}")

# Delete migrations
apps = ["orders", "products", "users"]
for app in apps:
    mig_dir = os.path.join(BASE_DIR, app, "migrations")
    if os.path.exists(mig_dir):
        files = glob.glob(os.path.join(mig_dir, "*.py"))
        for f in files:
            if not f.endswith("__init__.py"):
                try:
                    os.remove(f)
                    print(f"Deleted {f}")
                except Exception as e:
                    print(f"Error deleting {f}: {e}")
        
        # also delete __pycache__ inside migrations
        pycache_dir = os.path.join(mig_dir, "__pycache__")
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir, ignore_errors=True)

print("Cleanup Complete! You can now run makemigrations and migrate.")
