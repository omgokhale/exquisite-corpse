print("Starting import test...")

try:
    print("Importing generate module...")
    from app.api import generate
    print("✓ Generate module imported successfully")
    print(f"Router: {generate.router}")
    print(f"Routes: {generate.router.routes}")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
