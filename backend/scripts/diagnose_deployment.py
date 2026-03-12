"""
Diagnostic script to check deployment status on Render
Run this first to understand what's wrong
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Artwork, Segment
from app.core.config import DATA_DIR, INDEXES_DIR, DB_PATH

print("=" * 60)
print("DEPLOYMENT DIAGNOSTIC")
print("=" * 60)

# Check environment
print("\n1. ENVIRONMENT:")
print(f"   DATA_DIR: {DATA_DIR}")
print(f"   INDEXES_DIR: {INDEXES_DIR}")
print(f"   DB_PATH: {DB_PATH}")
print(f"   DB exists: {DB_PATH.exists()}")

# Check directory structure
print("\n2. DIRECTORY STRUCTURE:")
data_base = Path("/data")
if data_base.exists():
    print(f"   ✓ /data exists")
    for subdir in ["raw_images", "normalized_images", "segment_previews", "outputs", "indexes"]:
        path = data_base / subdir
        if path.exists():
            count = len(list(path.iterdir())) if path.is_dir() else 0
            print(f"   ✓ /data/{subdir} - {count} items")
        else:
            print(f"   ✗ /data/{subdir} - NOT FOUND")

    # Check for nested structure
    nested_data = data_base / "data"
    if nested_data.exists():
        print(f"\n   ⚠️  WARNING: Found nested /data/data/ directory!")
        print(f"   This will cause path issues. Contents:")
        for item in nested_data.iterdir():
            print(f"      - {item.name}")
else:
    print(f"   ✗ /data NOT FOUND")

# Check database
print("\n3. DATABASE:")
try:
    db = get_db_session()
    artwork_count = db.query(Artwork).count()
    segment_count = db.query(Segment).count()
    print(f"   ✓ Database accessible")
    print(f"   Artworks: {artwork_count}")
    print(f"   Segments: {segment_count}")

    # Sample some paths
    if artwork_count > 0:
        sample_artwork = db.query(Artwork).first()
        print(f"\n   Sample artwork path:")
        print(f"   {sample_artwork.local_image_path}")
        print(f"   Exists: {Path(sample_artwork.local_image_path).exists()}")

    if segment_count > 0:
        sample_segment = db.query(Segment).first()
        print(f"\n   Sample segment path:")
        print(f"   {sample_segment.preview_path}")
        print(f"   Exists: {Path(sample_segment.preview_path).exists()}")

except Exception as e:
    print(f"   ✗ Database error: {e}")

# Check FAISS indexes
print("\n4. FAISS INDEXES:")
for role in ["top", "middle", "bottom"]:
    index_path = INDEXES_DIR / f"segments_{role}.index"
    mapping_path = INDEXES_DIR / f"segments_{role}_ids.npy"
    if index_path.exists() and mapping_path.exists():
        print(f"   ✓ {role}: index and mapping exist")
    else:
        print(f"   ✗ {role}: missing files")

print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)

# Provide recommendations
recs = []
if not data_base.exists():
    recs.append("1. Run: python scripts/download_data.py")
elif (data_base / "data").exists():
    recs.append("1. Fix nested structure: mv /data/data/* /data/ && rmdir /data/data")
    recs.append("2. Then run: python scripts/fix_database_paths.py")
elif DB_PATH.exists():
    db = get_db_session()
    sample = db.query(Artwork).first()
    if sample and '/Users/' in str(sample.local_image_path):
        recs.append("1. Run: python scripts/fix_database_paths.py")
    elif sample and not Path(sample.local_image_path).exists():
        recs.append("1. Paths look correct but files missing - check data extraction")
else:
    recs.append("1. Database not found - upload data.tar.gz and extract")

if not recs:
    recs.append("✓ Everything looks good! Try generating a composite.")

for rec in recs:
    print(f"\n{rec}")

print("\n" + "=" * 60)
