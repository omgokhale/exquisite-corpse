"""
Diagnostic script to check system setup

Usage:
    python scripts/check_setup.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session, init_db
from app.db.models import Artwork, Segment, Generation, SegmentRole
from app.core.config import INDEXES_DIR, EMBEDDINGS_DIR


def check_database():
    """Check database contents"""
    print("Checking database...")

    # Initialize database if it doesn't exist
    try:
        init_db()
    except Exception as e:
        print(f"  Error initializing database: {e}")
        return False

    db = get_db_session()

    try:
        artwork_count = db.query(Artwork).count()
        segment_count = db.query(Segment).count()
        generation_count = db.query(Generation).count()

        print(f"  Artworks: {artwork_count}")
        print(f"  Segments: {segment_count}")
        print(f"  Generations: {generation_count}")

        # Check segments by role
        for role in SegmentRole:
            count = db.query(Segment).filter(Segment.role == role).count()
            print(f"    {role.value}: {count}")

        # Check embeddings
        segments_with_embeddings = db.query(Segment).filter(
            Segment.embedding_path.isnot(None)
        ).count()
        print(f"  Segments with embeddings: {segments_with_embeddings}")

        return artwork_count > 0 and segment_count > 0
    finally:
        db.close()


def check_indexes():
    """Check FAISS indexes"""
    print("\nChecking FAISS indexes...")

    for role in ['top', 'middle', 'bottom']:
        index_file = INDEXES_DIR / f"segments_{role}.index"
        ids_file = INDEXES_DIR / f"segments_{role}_ids.npy"

        index_exists = index_file.exists()
        ids_exist = ids_file.exists()

        print(f"  {role}:")
        print(f"    Index: {'✓' if index_exists else '✗'} {index_file}")
        print(f"    IDs: {'✓' if ids_exist else '✗'} {ids_file}")

    all_exist = all(
        (INDEXES_DIR / f"segments_{role}.index").exists()
        for role in ['top', 'middle', 'bottom']
    )

    return all_exist


def check_embeddings():
    """Check embeddings directory"""
    print("\nChecking embeddings...")

    if not EMBEDDINGS_DIR.exists():
        print(f"  ✗ Embeddings directory doesn't exist: {EMBEDDINGS_DIR}")
        return False

    embedding_files = list(EMBEDDINGS_DIR.glob("*.npy"))
    print(f"  Embedding files: {len(embedding_files)}")

    return len(embedding_files) > 0


def main():
    print("=" * 60)
    print("Exquisite Corpse - System Diagnostic")
    print("=" * 60)
    print()

    has_data = check_database()
    has_indexes = check_indexes()
    has_embeddings = check_embeddings()

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if has_data and has_indexes and has_embeddings:
        print("✓ System is fully set up!")
        print("  You can use /api/generate for scored generation")
    elif has_data:
        print("⚠ Data ingested but missing FAISS setup")
        print("  You can use /api/generate/random for random generation")
        print()
        print("  To enable scored generation, run:")
        print("    python scripts/4_extract_features.py")
        print("    python scripts/5_build_indexes.py")
    else:
        print("✗ No data found")
        print()
        print("  Please run the data pipeline:")
        print("    1. python scripts/1_fetch_met_objects.py --count 500")
        print("    2. python scripts/2_normalize_images.py")
        print("    3. python scripts/3_generate_segments.py")
        print()
        print("  For scored generation, also run:")
        print("    4. python scripts/4_extract_features.py")
        print("    5. python scripts/5_build_indexes.py")

    print("=" * 60)


if __name__ == "__main__":
    main()
