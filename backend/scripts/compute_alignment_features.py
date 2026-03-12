"""
Script to compute and store alignment features for all segments using saliency detection

Usage:
    python3 scripts/compute_alignment_features.py
"""
import sys
import json
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Segment, SegmentRole
from app.services.features import detect_subject_alignment


def compute_alignment_for_segment(segment: Segment) -> dict:
    """
    Compute alignment features for a segment using subject detection

    Args:
        segment: Segment to analyze

    Returns:
        Alignment features dict or None if detection fails
    """
    try:
        # Detect subject and get alignment features
        alignment_features = detect_subject_alignment(segment.preview_path)
        return alignment_features

    except Exception as e:
        print(f"Error computing alignment for segment {segment.id}: {e}")
        return None


def main():
    print("=" * 60)
    print("Subject Alignment Feature Pre-computation")
    print("=" * 60)
    print()
    print("This will detect the main subject in each segment and")
    print("compute horizontal alignment features for ranking.")
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
        fallback_count = 0

        # Process each segment
        for segment in tqdm(segments, desc="Computing alignment features"):
            try:
                # Compute alignment features
                alignment_features = compute_alignment_for_segment(segment)

                if alignment_features:
                    # Check if using fallback (center=0.5)
                    if alignment_features['center_x'] == 0.5 and alignment_features['width'] == 0.5:
                        fallback_count += 1

                    # Store as JSON
                    segment.alignment_features = json.dumps(alignment_features)
                    success_count += 1
                else:
                    failed_count += 1

                # Commit periodically (every 50 segments)
                if success_count % 50 == 0:
                    db.commit()

            except Exception as e:
                tqdm.write(f"Failed for segment {segment.id}: {e}")
                failed_count += 1

        # Final commit
        db.commit()

        print()
        print("=" * 60)
        print("Alignment feature computation complete:")
        print(f"  Successfully processed: {success_count}")
        print(f"  Using fallback (no clear subject): {fallback_count}")
        print(f"  Failed: {failed_count}")
        print("=" * 60)

        # Show alignment distribution
        print()
        print("Horizontal alignment distribution by role:")
        for role in SegmentRole:
            segments_for_role = db.query(Segment).filter(Segment.role == role).all()

            # Parse alignment features
            centers = []
            widths = []
            for s in segments_for_role:
                if s.alignment_features:
                    try:
                        features = json.loads(s.alignment_features)
                        centers.append(features['center_x'])
                        widths.append(features['width'])
                    except:
                        pass

            if centers:
                avg_center = sum(centers) / len(centers)
                avg_width = sum(widths) / len(widths)

                # Categorize alignment
                left_aligned = sum(1 for c in centers if c < 0.4)
                center_aligned = sum(1 for c in centers if 0.4 <= c <= 0.6)
                right_aligned = sum(1 for c in centers if c > 0.6)

                print(f"  {role.value}:")
                print(f"    Average center: {avg_center:.3f} (0=left, 0.5=center, 1=right)")
                print(f"    Average width: {avg_width:.3f}")
                print(f"    Left-aligned: {left_aligned}/{len(centers)}")
                print(f"    Center-aligned: {center_aligned}/{len(centers)}")
                print(f"    Right-aligned: {right_aligned}/{len(centers)}")

    except Exception as e:
        print(f"\nError during computation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
