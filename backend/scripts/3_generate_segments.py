"""
Script to generate segments for all normalized artworks

Usage:
    python scripts/3_generate_segments.py
"""
import sys
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Artwork
from app.services.segments import generate_segments_for_artwork


def main():
    print("=" * 60)
    print("Segment Generation Script")
    print("=" * 60)
    print()

    # Get database session
    db = get_db_session()

    try:
        # Get all normalized artworks
        artworks = db.query(Artwork).filter(
            Artwork.width.isnot(None),
            Artwork.height.isnot(None)
        ).all()

        if not artworks:
            print("No normalized artworks found in database")
            return

        print(f"Found {len(artworks)} normalized artworks")
        print()

        success_count = 0
        failed_count = 0
        total_segments = 0

        # Process each artwork
        for artwork in tqdm(artworks, desc="Generating segments"):
            try:
                segments = generate_segments_for_artwork(artwork.id, db)
                success_count += 1
                total_segments += len(segments)
            except Exception as e:
                tqdm.write(f"Failed to generate segments for artwork {artwork.id}: {e}")
                failed_count += 1

        print()
        print("=" * 60)
        print("Segment generation complete:")
        print(f"  Successfully processed: {success_count} artworks")
        print(f"  Total segments created: {total_segments}")
        print(f"  Failed: {failed_count}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during segment generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
