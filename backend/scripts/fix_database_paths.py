"""
Fix all database paths to point to /data instead of local machine paths
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Artwork, Segment, Generation

db = get_db_session()

print("Fixing Artwork paths...")
artworks = db.query(Artwork).all()
for artwork in artworks:
    # Fix local_image_path
    old_path = str(artwork.local_image_path)
    if '/Users/' in old_path or '/app/data' in old_path:
        # Extract just the filename and rebuild path
        parts = Path(old_path).parts
        if 'normalized_images' in parts:
            new_path = f"/data/normalized_images/{Path(old_path).name}"
        elif 'raw_images' in parts:
            new_path = f"/data/raw_images/{Path(old_path).name}"
        else:
            new_path = old_path
        artwork.local_image_path = new_path

print(f"✓ Fixed {len(artworks)} artworks")

print("\nFixing Segment paths...")
segments = db.query(Segment).all()
for segment in segments:
    # Fix preview_path
    if segment.preview_path:
        old_path = str(segment.preview_path)
        if '/Users/' in old_path or '/app/data' in old_path:
            new_path = f"/data/segment_previews/{Path(old_path).name}"
            segment.preview_path = new_path

print(f"✓ Fixed {len(segments)} segments")

print("\nFixing Generation paths...")
generations = db.query(Generation).all()
for gen in generations:
    if gen.output_path:
        old_path = str(gen.output_path)
        if '/Users/' in old_path or '/app/data' in old_path:
            new_path = f"/data/outputs/{Path(old_path).name}"
            gen.output_path = new_path

print(f"✓ Fixed {len(generations)} generations")

db.commit()
print("\n✅ All database paths fixed!")

# Verify
segment_count = db.query(Segment).count()
print(f"\nVerification: {segment_count} segments in database")
