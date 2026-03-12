"""
Script to test random baseline composite generation

Usage:
    python scripts/test_random_baseline.py [--count 20]
"""
import sys
import random
import argparse
from pathlib import Path
from sqlalchemy import func

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Segment, SegmentRole
from app.services.compositing import create_generation


def generate_random_composite(db, verbose=True):
    """
    Generate a single random composite by selecting random segments

    Returns:
        Generation instance or None if failed
    """
    try:
        # Get random segments for each role
        top_segment = db.query(Segment).filter(
            Segment.role == SegmentRole.TOP
        ).order_by(func.random()).first()

        middle_segment = db.query(Segment).filter(
            Segment.role == SegmentRole.MIDDLE,
            Segment.artwork_id != top_segment.artwork_id  # Different artwork
        ).order_by(func.random()).first()

        bottom_segment = db.query(Segment).filter(
            Segment.role == SegmentRole.BOTTOM,
            Segment.artwork_id.notin_([top_segment.artwork_id, middle_segment.artwork_id])
        ).order_by(func.random()).first()

        if not all([top_segment, middle_segment, bottom_segment]):
            if verbose:
                print("Could not find segments for all roles")
            return None

        # Create composite
        generation = create_generation(
            top_segment_id=top_segment.id,
            middle_segment_id=middle_segment.id,
            bottom_segment_id=bottom_segment.id,
            tm_score=0.0,
            mb_score=0.0,
            total_score=0.0,
            db=db
        )

        if verbose:
            print(f"✓ Generated composite {generation.id}")
            print(f"  Top: {top_segment.artwork.title} (artwork {top_segment.artwork_id})")
            print(f"  Middle: {middle_segment.artwork.title} (artwork {middle_segment.artwork_id})")
            print(f"  Bottom: {bottom_segment.artwork.title} (artwork {bottom_segment.artwork_id})")
            print(f"  Output: {generation.output_path}")
            print()

        return generation

    except Exception as e:
        if verbose:
            print(f"Error generating composite: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate random baseline composites")
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of composites to generate (default: 20)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Random Baseline Composite Generator")
    print("=" * 60)
    print(f"Target: {args.count} composites")
    print()

    # Get database session
    db = get_db_session()

    try:
        # Check if we have segments
        segment_counts = {
            "top": db.query(Segment).filter(Segment.role == SegmentRole.TOP).count(),
            "middle": db.query(Segment).filter(Segment.role == SegmentRole.MIDDLE).count(),
            "bottom": db.query(Segment).filter(Segment.role == SegmentRole.BOTTOM).count(),
        }

        print("Segment counts:")
        for role, count in segment_counts.items():
            print(f"  {role}: {count}")
        print()

        if any(count == 0 for count in segment_counts.values()):
            print("Error: No segments found. Run scripts 1-3 first:")
            print("  1. python scripts/1_fetch_met_objects.py")
            print("  2. python scripts/2_normalize_images.py")
            print("  3. python scripts/3_generate_segments.py")
            sys.exit(1)

        # Generate composites
        success_count = 0
        for i in range(args.count):
            print(f"[{i+1}/{args.count}]")
            generation = generate_random_composite(db, verbose=True)
            if generation:
                success_count += 1

        print("=" * 60)
        print(f"Random baseline generation complete:")
        print(f"  Successfully generated: {success_count}/{args.count}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
