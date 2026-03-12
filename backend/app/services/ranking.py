"""
Service for ranking and selecting segment triplets using FAISS and scoring
"""
import random
import numpy as np
import faiss
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from collections import deque
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import (
    FAISS_CANDIDATE_COUNT,
    TOP_PAIRS_COUNT,
    DIVERSITY_BONUS,
    NOVELTY_BONUS,
    INDEXES_DIR,
    SEMANTIC_QUERIES,
    SEMANTIC_BONUS,
    SEMANTIC_PENALTY,
    ALIGNMENT_WEIGHT,
    ALIGNMENT_TOLERANCE,
)
from app.db.models import Segment, SegmentRole
from app.services.matching import compute_seam_score
from app.services.features import load_embedding, compute_text_image_similarity
from PIL import Image


# Global index cache
_indexes = {}
_id_mappings = {}

# Novelty tracking (recent artworks used)
# Reduced to 15 to prevent same paintings in consecutive generations
_recent_artworks = deque(maxlen=15)


def load_faiss_index(role: SegmentRole) -> Tuple[faiss.Index, np.ndarray]:
    """
    Load FAISS index for a specific role (cached)

    Args:
        role: Segment role

    Returns:
        Tuple of (index, segment_ids)
    """
    global _indexes, _id_mappings

    role_key = role.value

    if role_key in _indexes:
        return _indexes[role_key], _id_mappings[role_key]

    # Load index
    index_path = INDEXES_DIR / f"segments_{role_key}.index"
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found: {index_path}")

    index = faiss.read_index(str(index_path))

    # Load ID mapping
    ids_path = INDEXES_DIR / f"segments_{role_key}_ids.npy"
    if not ids_path.exists():
        raise FileNotFoundError(f"ID mapping not found: {ids_path}")

    segment_ids = np.load(ids_path)

    # Cache
    _indexes[role_key] = index
    _id_mappings[role_key] = segment_ids

    return index, segment_ids


def find_compatible_candidates(
    segment: Segment,
    target_role: SegmentRole,
    top_k: int = FAISS_CANDIDATE_COUNT,
    exclude_artwork_ids: Optional[List[int]] = None
) -> List[int]:
    """
    Find top-k compatible segment candidates using FAISS

    Args:
        segment: Query segment
        target_role: Role of candidates to find
        top_k: Number of candidates to return
        exclude_artwork_ids: Artwork IDs to exclude from results

    Returns:
        List of segment IDs
    """
    # Load FAISS index
    index, segment_ids = load_faiss_index(target_role)

    # Load query embedding
    query_embedding = load_embedding(segment.id)
    if query_embedding is None:
        raise ValueError(f"Embedding not found for segment {segment.id}")

    # Normalize and reshape for FAISS
    query_vector = query_embedding.astype('float32').reshape(1, -1)
    faiss.normalize_L2(query_vector)

    # Search (get more than needed to account for filtering)
    search_k = min(top_k * 3, index.ntotal)
    distances, indices = index.search(query_vector, int(search_k))

    # Convert to segment IDs
    candidate_ids = segment_ids[indices[0]].tolist()

    # Filter out excluded artworks if needed
    if exclude_artwork_ids:
        exclude_set = set(exclude_artwork_ids)
        filtered_ids = []
        for seg_id in candidate_ids:
            # Note: We'd need to query the database to get artwork_id for each segment
            # For now, we'll filter during scoring phase
            filtered_ids.append(seg_id)
        candidate_ids = filtered_ids

    return candidate_ids[:top_k]


def compute_semantic_score(segment: Segment) -> float:
    """
    Compute semantic appropriateness of a segment for its role

    Args:
        segment: Segment to score

    Returns:
        Semantic score adjustment (can be positive bonus or negative penalty)
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
        print(f"Warning: Semantic scoring failed for segment {segment.id}: {e}")
        return 0.0


def compute_alignment_score(seg1: Segment, seg2: Segment) -> float:
    """
    Compute horizontal alignment compatibility between two adjacent segments.
    Rewards segments where subjects are horizontally aligned (same center position).
    Penalizes segments where subjects are misaligned (e.g., left vs right).

    Args:
        seg1: Upper segment
        seg2: Lower segment

    Returns:
        Alignment score (positive = good alignment, negative = poor alignment)
    """
    try:
        # Load alignment features from database
        if not seg1.alignment_features or not seg2.alignment_features:
            return 0.0  # Neutral if features not available

        features1 = json.loads(seg1.alignment_features)
        features2 = json.loads(seg2.alignment_features)

        # Get horizontal centers (0.0 = left, 0.5 = center, 1.0 = right)
        center1 = features1.get('center_x', 0.5)
        center2 = features2.get('center_x', 0.5)

        # Compute difference in horizontal position
        center_diff = abs(center1 - center2)

        # Score based on alignment
        if center_diff <= ALIGNMENT_TOLERANCE:
            # Well aligned - give bonus proportional to how well aligned
            alignment_quality = 1.0 - (center_diff / ALIGNMENT_TOLERANCE)
            return ALIGNMENT_WEIGHT * alignment_quality
        else:
            # Poorly aligned - give penalty
            misalignment = (center_diff - ALIGNMENT_TOLERANCE) / (1.0 - ALIGNMENT_TOLERANCE)
            return -ALIGNMENT_WEIGHT * misalignment

    except Exception as e:
        print(f"Warning: Alignment scoring failed for segments {seg1.id}-{seg2.id}: {e}")
        return 0.0


def score_pair(
    seg1: Segment,
    seg2: Segment,
    db: Session
) -> Tuple[float, Dict]:
    """
    Score compatibility between two adjacent segments

    Args:
        seg1: First segment (top)
        seg2: Second segment (bottom)
        db: Database session

    Returns:
        Tuple of (score, subscores)
    """
    # Load embeddings
    emb1 = load_embedding(seg1.id)
    emb2 = load_embedding(seg2.id)

    if emb1 is None or emb2 is None:
        return 0.0, {}

    # Compute seam score (color, edge, embedding, scale)
    score, subscores = compute_seam_score(
        seg1_bottom_features=seg1.bottom_seam_features,
        seg2_top_features=seg2.top_seam_features,
        seg1_embedding=emb1,
        seg2_embedding=emb2,
        seg1_height=seg1.crop_h,
        seg2_height=seg2.crop_h
    )

    # ALIGNMENT SCORING DISABLED - was creating false positives
    # Compute horizontal alignment score
    # alignment_score = compute_alignment_score(seg1, seg2)
    # total_score = score + alignment_score
    # subscores['alignment_score'] = alignment_score

    return score, subscores


def score_triplet(
    top_seg: Segment,
    mid_seg: Segment,
    bot_seg: Segment,
    db: Session
) -> Tuple[float, Dict]:
    """
    Score a complete triplet

    Args:
        top_seg: Top segment
        mid_seg: Middle segment
        bot_seg: Bottom segment
        db: Database session

    Returns:
        Tuple of (total_score, details_dict)
    """
    # Check for duplicate artworks
    artwork_ids = {top_seg.artwork_id, mid_seg.artwork_id, bot_seg.artwork_id}
    if len(artwork_ids) < 3:
        return 0.0, {'error': 'duplicate_artworks'}

    # Score seams
    tm_score, tm_subscores = score_pair(top_seg, mid_seg, db)
    mb_score, mb_subscores = score_pair(mid_seg, bot_seg, db)

    # Base score: average of seam scores
    base_score = (tm_score + mb_score) / 2.0

    # Semantic appropriateness scores (using pre-computed values from database)
    top_semantic = top_seg.semantic_score if top_seg.semantic_score is not None else 0.0
    mid_semantic = mid_seg.semantic_score if mid_seg.semantic_score is not None else 0.0
    bot_semantic = bot_seg.semantic_score if bot_seg.semantic_score is not None else 0.0
    semantic_total = top_semantic + mid_semantic + bot_semantic

    # Diversity bonus: different departments or time periods
    diversity = 0.0
    departments = {
        top_seg.artwork.department,
        mid_seg.artwork.department,
        bot_seg.artwork.department
    }
    if len(departments) > 1:
        diversity = DIVERSITY_BONUS

    # Novelty bonus: artworks not recently used
    novelty = 0.0
    recent_set = set(_recent_artworks)
    novel_count = sum(1 for aid in artwork_ids if aid not in recent_set)
    if novel_count == 3:
        novelty = NOVELTY_BONUS

    # Total score (including semantic adjustment)
    total_score = base_score + semantic_total + diversity + novelty

    details = {
        'tm_score': tm_score,
        'mb_score': mb_score,
        'base_score': base_score,
        'semantic_top': top_semantic,
        'semantic_middle': mid_semantic,
        'semantic_bottom': bot_semantic,
        'semantic_total': semantic_total,
        'diversity_bonus': diversity,
        'novelty_bonus': novelty,
        'total_score': total_score,
        'tm_subscores': tm_subscores,
        'mb_subscores': mb_subscores,
    }

    return total_score, details


def generate_triplet(db: Session) -> Tuple[Segment, Segment, Segment, Dict]:
    """
    Generate a high-quality triplet using FAISS and scoring

    Args:
        db: Database session

    Returns:
        Tuple of (top_seg, mid_seg, bot_seg, scores_dict)
    """
    # Get list of recently used artwork IDs to exclude
    recent_artwork_ids = list(_recent_artworks)

    # Step 1: Pick random top segment (excluding recent artworks)
    query = db.query(Segment).filter(
        Segment.role == SegmentRole.TOP,
        Segment.embedding_path.isnot(None)
    )

    if recent_artwork_ids:
        query = query.filter(Segment.artwork_id.notin_(recent_artwork_ids))

    top_seg = query.order_by(func.random()).first()

    if not top_seg:
        # If no segments available (all recent), clear history and try again
        _recent_artworks.clear()
        top_seg = db.query(Segment).filter(
            Segment.role == SegmentRole.TOP,
            Segment.embedding_path.isnot(None)
        ).order_by(func.random()).first()

        if not top_seg:
            raise ValueError("No top segments available")

    # Step 2: Find compatible middle candidates using FAISS
    middle_candidate_ids = find_compatible_candidates(
        segment=top_seg,
        target_role=SegmentRole.MIDDLE,
        top_k=FAISS_CANDIDATE_COUNT,
        exclude_artwork_ids=[top_seg.artwork_id]
    )

    # Get segment objects (excluding same artwork as top AND recent artworks)
    exclude_artworks = [top_seg.artwork_id] + recent_artwork_ids
    middle_candidates = db.query(Segment).filter(
        Segment.id.in_(middle_candidate_ids),
        Segment.artwork_id.notin_(exclude_artworks)
    ).all()

    if not middle_candidates:
        raise ValueError("No compatible middle segments found")

    # Step 3: Score all top-middle pairs
    tm_pairs = []
    for mid_seg in middle_candidates[:FAISS_CANDIDATE_COUNT]:
        if mid_seg.artwork_id == top_seg.artwork_id:
            continue
        score, _ = score_pair(top_seg, mid_seg, db)
        tm_pairs.append((score, mid_seg))

    # Keep top N pairs
    tm_pairs.sort(key=lambda x: x[0], reverse=True)
    top_pairs = tm_pairs[:TOP_PAIRS_COUNT]

    if not top_pairs:
        raise ValueError("No valid top-middle pairs found")

    # Step 4: For each top-middle pair, find compatible bottom candidates
    best_triplet = None
    best_score = -1
    best_details = None

    for tm_score, mid_seg in top_pairs:
        # Find bottom candidates
        bottom_candidate_ids = find_compatible_candidates(
            segment=mid_seg,
            target_role=SegmentRole.BOTTOM,
            top_k=FAISS_CANDIDATE_COUNT,
            exclude_artwork_ids=[top_seg.artwork_id, mid_seg.artwork_id]
        )

        # Get segment objects (excluding same artworks as top/middle AND recent artworks)
        exclude_artworks = [top_seg.artwork_id, mid_seg.artwork_id] + recent_artwork_ids
        bottom_candidates = db.query(Segment).filter(
            Segment.id.in_(bottom_candidate_ids),
            Segment.artwork_id.notin_(exclude_artworks)
        ).all()

        # Score triplets
        for bot_seg in bottom_candidates[:20]:  # Limit to avoid too much computation
            score, details = score_triplet(top_seg, mid_seg, bot_seg, db)

            if score > best_score:
                best_score = score
                best_triplet = (top_seg, mid_seg, bot_seg)
                best_details = details

    if best_triplet is None:
        raise ValueError("No valid triplets found")

    # Update novelty tracking
    top_seg, mid_seg, bot_seg = best_triplet
    _recent_artworks.extend([top_seg.artwork_id, mid_seg.artwork_id, bot_seg.artwork_id])

    return top_seg, mid_seg, bot_seg, best_details
