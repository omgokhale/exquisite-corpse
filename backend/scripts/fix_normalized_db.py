"""
Quick fix to mark images as normalized without reprocessing
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Artwork
from PIL import Image

db = get_db_session()
artworks = db.query(Artwork).all()

print(f"Updating {len(artworks)} artworks...")

for artwork in artworks:
    # Update path to normalized
    old_path = str(artwork.local_image_path)
    new_path = old_path.replace('raw_images', 'normalized_images')
    artwork.local_image_path = new_path

    # Set dimensions from actual image
    try:
        if Path(new_path).exists():
            img = Image.open(new_path)
            artwork.width, artwork.height = img.size
            print(f"✓ {artwork.title}: {artwork.width}x{artwork.height}")
    except Exception as e:
        print(f"✗ {artwork.title}: {e}")

db.commit()
print(f"\n✓ Updated {len(artworks)} artworks")
