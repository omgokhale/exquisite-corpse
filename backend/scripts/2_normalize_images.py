"""
Script to normalize all ingested artwork images

Usage:
    python scripts/2_normalize_images.py
"""
import sys
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Artwork
from app.services.normalization import normalize_artwork_image
from app.core.config import NORMALIZED_IMAGES_DIR


def main():
    print("=" * 60)
    print("Image Normalization Script")
    print("=" * 60)
    print()

    # Get database session
    db = get_db_session()

    try:
        # Get all artworks
        artworks = db.query(Artwork).filter(
            Artwork.local_image_path.isnot(None)
        ).all()

        if not artworks:
            print("No artworks found in database")
            return

        print(f"Found {len(artworks)} artworks to normalize")
        print()

        success_count = 0
        failed_count = 0

        # Process each artwork
        for artwork in tqdm(artworks, desc="Normalizing images"):
            dimensions = normalize_artwork_image(
                artwork_id=artwork.id,
                input_path=artwork.local_image_path,
                output_dir=NORMALIZED_IMAGES_DIR
            )

            if dimensions:
                width, height = dimensions
                artwork.width = width
                artwork.height = height
                success_count += 1
            else:
                failed_count += 1

        # Commit all updates
        db.commit()

        print()
        print("=" * 60)
        print("Normalization complete:")
        print(f"  Successfully normalized: {success_count}")
        print(f"  Failed: {failed_count}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during normalization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
