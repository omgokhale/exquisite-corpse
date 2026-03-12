"""
Script to extract CLIP embeddings for all segments

Usage:
    python scripts/4_extract_features.py
"""
import sys
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Segment
from app.services.features import extract_features_for_segment, load_clip_model


def main():
    print("=" * 60)
    print("CLIP Feature Extraction Script")
    print("=" * 60)
    print()

    # Pre-load CLIP model (downloads on first run)
    print("Loading CLIP model...")
    load_clip_model()
    print()

    # Get database session
    db = get_db_session()

    try:
        # Get all segments
        segments = db.query(Segment).filter(
            Segment.preview_path.isnot(None)
        ).all()

        if not segments:
            print("No segments found in database")
            return

        print(f"Found {len(segments)} segments to process")
        print()

        success_count = 0
        failed_count = 0
        skipped_count = 0

        # Process each segment
        for segment in tqdm(segments, desc="Extracting features"):
            try:
                # Skip if already processed
                if segment.embedding_path:
                    embedding_file = Path(segment.embedding_path)
                    if embedding_file.exists():
                        skipped_count += 1
                        continue

                # Extract and save embedding
                embedding_path = extract_features_for_segment(
                    segment_id=segment.id,
                    preview_path=segment.preview_path
                )

                # Update database
                segment.embedding_path = str(embedding_path)
                success_count += 1

                # Commit periodically (every 100 segments)
                if success_count % 100 == 0:
                    db.commit()

            except Exception as e:
                tqdm.write(f"Failed to extract features for segment {segment.id}: {e}")
                failed_count += 1

        # Final commit
        db.commit()

        print()
        print("=" * 60)
        print("Feature extraction complete:")
        print(f"  Successfully processed: {success_count}")
        print(f"  Skipped (already done): {skipped_count}")
        print(f"  Failed: {failed_count}")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during feature extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
