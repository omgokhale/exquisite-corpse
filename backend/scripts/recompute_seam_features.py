"""
Script to recompute seam features for all segments with new background plane detection

Usage:
    python scripts/recompute_seam_features.py
"""
import sys
import json
import numpy as np
from pathlib import Path
from tqdm import tqdm
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Segment
from app.services.segments import extract_seam_features


def main():
    """Recompute seam features for all segments"""
    print("Recomputing seam features with background plane detection...")

    db = get_db_session()

    try:
        # Get all segments
        segments = db.query(Segment).all()
        print(f"Found {len(segments)} segments to process")

        # Track background detection stats
        stats = {
            'top_backgrounds': 0,
            'bottom_backgrounds': 0,
            'processed': 0,
            'errors': 0
        }

        for segment in tqdm(segments, desc="Recomputing seam features"):
            try:
                # Load segment image
                image = Image.open(segment.preview_path)
                image_array = np.array(image)

                # Extract top seam features
                top_features = extract_seam_features(image_array, 'top')
                segment.top_seam_features = top_features

                # Extract bottom seam features
                bottom_features = extract_seam_features(image_array, 'bottom')
                segment.bottom_seam_features = bottom_features

                # Track background detection
                if top_features.get('is_background_plane', False):
                    stats['top_backgrounds'] += 1
                if bottom_features.get('is_background_plane', False):
                    stats['bottom_backgrounds'] += 1

                stats['processed'] += 1

                # Commit every 100 segments to avoid memory issues
                if stats['processed'] % 100 == 0:
                    db.commit()

            except Exception as e:
                print(f"\nError processing segment {segment.id}: {e}")
                stats['errors'] += 1
                continue

        # Final commit
        db.commit()

        # Print statistics
        print("\n" + "=" * 60)
        print("Seam Feature Recomputation Complete!")
        print("=" * 60)
        print(f"Total segments processed: {stats['processed']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nBackground Plane Detection:")
        print(f"  Top seams with background: {stats['top_backgrounds']} ({100*stats['top_backgrounds']/stats['processed']:.1f}%)")
        print(f"  Bottom seams with background: {stats['bottom_backgrounds']} ({100*stats['bottom_backgrounds']/stats['processed']:.1f}%)")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
