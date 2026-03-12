"""
Script to build FAISS indexes for fast similarity search

Usage:
    python scripts/5_build_indexes.py
"""
import sys
import numpy as np
import faiss
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Segment, SegmentRole
from app.core.config import INDEXES_DIR


def build_index_for_role(role: SegmentRole, db):
    """
    Build FAISS index for a specific segment role

    Args:
        role: SegmentRole (TOP, MIDDLE, or BOTTOM)
        db: Database session
    """
    print(f"\nBuilding index for role: {role.value}")
    print("-" * 40)

    # Get all segments for this role with embeddings
    segments = db.query(Segment).filter(
        Segment.role == role,
        Segment.embedding_path.isnot(None)
    ).all()

    if not segments:
        print(f"No segments found for role {role.value}")
        return

    print(f"Found {len(segments)} segments")

    # Load all embeddings
    embeddings = []
    segment_ids = []

    for segment in segments:
        try:
            embedding_path = Path(segment.embedding_path)
            if embedding_path.exists():
                embedding = np.load(embedding_path)
                embeddings.append(embedding)
                segment_ids.append(segment.id)
        except Exception as e:
            print(f"Error loading embedding for segment {segment.id}: {e}")

    if not embeddings:
        print(f"No valid embeddings found for role {role.value}")
        return

    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype('float32')
    print(f"Loaded {len(embeddings)} embeddings, shape: {embeddings_array.shape}")

    # Normalize embeddings (CLIP embeddings should already be normalized, but ensure it)
    faiss.normalize_L2(embeddings_array)

    # Build FAISS index (using IndexFlatL2 for exact search)
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)

    # Add vectors to index
    index.add(embeddings_array)

    print(f"Index built with {index.ntotal} vectors")

    # Save index
    index_path = INDEXES_DIR / f"segments_{role.value}.index"
    faiss.write_index(index, str(index_path))
    print(f"✓ Index saved: {index_path}")

    # Save segment ID mapping
    ids_path = INDEXES_DIR / f"segments_{role.value}_ids.npy"
    np.save(ids_path, np.array(segment_ids))
    print(f"✓ ID mapping saved: {ids_path}")


def main():
    print("=" * 60)
    print("FAISS Index Building Script")
    print("=" * 60)

    # Get database session
    db = get_db_session()

    try:
        # Build indexes for each role
        for role in SegmentRole:
            build_index_for_role(role, db)

        print()
        print("=" * 60)
        print("✓ All indexes built successfully")
        print("=" * 60)
        print()
        print("Index files:")
        for role in SegmentRole:
            index_path = INDEXES_DIR / f"segments_{role.value}.index"
            ids_path = INDEXES_DIR / f"segments_{role.value}_ids.npy"
            if index_path.exists():
                print(f"  {role.value}: {index_path}")
                print(f"  {role.value} IDs: {ids_path}")

    except Exception as e:
        print(f"\nError building indexes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
