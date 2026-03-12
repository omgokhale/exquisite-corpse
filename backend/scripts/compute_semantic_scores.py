"""
Script to compute and store semantic scores for all segments

Usage:
    python scripts/compute_semantic_scores.py
"""
import sys
from pathlib import Path
from tqdm import tqdm
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.db.models import Segment, SegmentRole
from app.services.features import compute_text_image_similarity
from app.core.config import SEMANTIC_QUERIES, SEMANTIC_BONUS, SEMANTIC_PENALTY


def compute_semantic_score_for_segment(segment: Segment) -> float:
    """
    Compute semantic appropriateness score for a segment

    Args:
        segment: Segment to score

    Returns:
        Semantic score (can be positive bonus or negative penalty)
    """
    try:
        # Load segment image
        image = Image.open(segment.preview_path)

        # Get queries for this role
        correct_queries = SEMANTIC_QUERIES[segment.role.value]

        # Get opposite role queries for penalty detection
        if segment.role == SegmentRole.TOP:
            wrong_queries = SEMANTIC_QUERIES["bottom"]
        elif segment.role == SegmentRole.BOTTOM:
            wrong_queries = SEMANTIC_QUERIES["top"]
        else:  # MIDDLE
            wrong_queries = []  # Middle is flexible

        # Compute similarities
        all_queries = correct_queries + wrong_queries
        similarities = compute_text_image_similarity(image, all_queries)

        # Get max similarity for correct and wrong queries
        correct_max = max([similarities[q] for q in correct_queries])
        wrong_max = max([similarities[q] for q in wrong_queries]) if wrong_queries else 0.0

        # Determine bonus or penalty
        if correct_max > wrong_max:
            # Segment matches its role well
            return SEMANTIC_BONUS * correct_max
        elif wrong_max > correct_max and wrong_max > 0.3:
            # Segment strongly matches wrong role (e.g., feet at top)
            return -SEMANTIC_PENALTY
        else:
            # Neutral
            return 0.0

    except Exception as e:
        print(f"Error computing semantic score for segment {segment.id}: {e}")
        return 0.0


def main():
    print("=" * 60)
    print("Semantic Score Pre-computation")
    print("=" * 60)
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

        # Process each segment
        for segment in tqdm(segments, desc="Computing semantic scores"):
            try:
                # Compute semantic score
                semantic_score = compute_semantic_score_for_segment(segment)

                # Update database
                segment.semantic_score = semantic_score
                success_count += 1

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
        print("Semantic score computation complete:")
        print(f"  Successfully processed: {success_count}")
        print(f"  Failed: {failed_count}")
        print("=" * 60)

        # Show score distribution
        print()
        print("Score distribution by role:")
        for role in SegmentRole:
            segments_for_role = db.query(Segment).filter(Segment.role == role).all()
            scores = [s.semantic_score for s in segments_for_role if s.semantic_score is not None]
            if scores:
                avg = sum(scores) / len(scores)
                positive = sum(1 for s in scores if s > 0)
                negative = sum(1 for s in scores if s < 0)
                print(f"  {role.value}:")
                print(f"    Average: {avg:.3f}")
                print(f"    Positive (good): {positive}/{len(scores)}")
                print(f"    Negative (bad): {negative}/{len(scores)}")

    except Exception as e:
        print(f"\nError during computation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
