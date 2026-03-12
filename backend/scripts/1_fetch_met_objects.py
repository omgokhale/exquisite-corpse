"""
Script to fetch and ingest artworks from The Met Collection API

Usage:
    python scripts/1_fetch_met_objects.py [--count 500] [--query "painting"]
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import init_db, get_db_session
from app.services.met_ingestion import ingest_artworks
from app.core.config import TARGET_ARTWORK_COUNT


def main():
    parser = argparse.ArgumentParser(description="Ingest artworks from The Met Collection API")
    parser.add_argument(
        "--count",
        type=int,
        default=TARGET_ARTWORK_COUNT,
        help=f"Target number of artworks to ingest (default: {TARGET_ARTWORK_COUNT})"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="painting",
        help="Search query (default: 'painting')"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Met Collection Ingestion Script")
    print("=" * 60)
    print(f"Target count: {args.count}")
    print(f"Search query: '{args.query}'")
    print()

    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized")
    print()

    # Get database session
    db = get_db_session()

    try:
        # Run ingestion
        artworks = ingest_artworks(
            db=db,
            target_count=args.count,
            search_query=args.query,
            prefer_paintings=True
        )

        print()
        print("=" * 60)
        print(f"✓ Ingestion complete: {len(artworks)} artworks ingested")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nIngestion interrupted by user")
        db.close()
        sys.exit(1)

    except Exception as e:
        print(f"\n\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
