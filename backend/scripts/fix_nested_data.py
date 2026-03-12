"""
Fix nested /data/data/ structure if download_data.py created it
This moves everything from /data/data/* to /data/ directly
"""
import os
import shutil
from pathlib import Path

data_base = Path("/data")
nested_data = data_base / "data"

if not nested_data.exists():
    print("✓ No nested /data/data/ directory found")
    print("Structure is correct, no action needed!")
    exit(0)

print("Found nested /data/data/ directory")
print("Moving contents to /data/ ...")

# Move each subdirectory
for item in nested_data.iterdir():
    src = item
    dst = data_base / item.name

    if dst.exists():
        print(f"⚠️  {dst} already exists, skipping {src}")
        continue

    print(f"Moving {src.name}...")
    shutil.move(str(src), str(dst))

# Remove empty nested directory
if not any(nested_data.iterdir()):
    nested_data.rmdir()
    print("✓ Removed empty /data/data/ directory")

print("\n✅ Structure fixed!")
print("\nCurrent /data/ contents:")
for item in sorted(data_base.iterdir()):
    if item.is_dir():
        count = len(list(item.iterdir()))
        print(f"  {item.name}/ - {count} items")
    else:
        size_mb = item.stat().st_size / (1024 * 1024)
        print(f"  {item.name} - {size_mb:.1f}MB")
