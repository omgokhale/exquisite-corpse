"""
Service for computing seam compatibility scores between segments
"""
import numpy as np
from typing import Dict, Any, Tuple
from app.core.config import (
    SEAM_WEIGHTS,
    MAX_SCALE_RATIO,
    MIN_SCALE_RATIO,
    BACKGROUND_SIMILARITY_MULTIPLIER,
)


def color_similarity(hist1: list, hist2: list) -> float:
    """
    Compute color histogram similarity using chi-square distance

    Args:
        hist1: Color histogram (flattened RGB)
        hist2: Color histogram (flattened RGB)

    Returns:
        Similarity score (0-1, higher is better)
    """
    h1 = np.array(hist1)
    h2 = np.array(hist2)

    # Chi-square distance
    eps = 1e-10  # Avoid division by zero
    chi_square = np.sum(((h1 - h2) ** 2) / (h1 + h2 + eps))

    # Normalize to 0-1 range (lower chi-square = higher similarity)
    # Typical chi-square values range from 0 to ~10 for normalized histograms
    similarity = 1.0 / (1.0 + chi_square)

    return float(similarity)


def edge_similarity(density1: float, density2: float) -> float:
    """
    Compute edge density similarity

    Args:
        density1: Edge density of first seam
        density2: Edge density of second seam

    Returns:
        Similarity score (0-1, higher is better)
    """
    # Absolute difference
    diff = abs(density1 - density2)

    # Convert to similarity (0 diff = 1.0 similarity)
    similarity = 1.0 - min(diff, 1.0)

    return float(similarity)


def embedding_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """
    Compute cosine similarity between CLIP embeddings

    Args:
        emb1: First embedding (normalized)
        emb2: Second embedding (normalized)

    Returns:
        Cosine similarity (0-1, higher is better)
    """
    # Cosine similarity (embeddings should already be normalized)
    similarity = np.dot(emb1, emb2)

    # Ensure in range [0, 1] (should be [-1, 1] but normalized embeddings give [0, 1])
    similarity = (similarity + 1.0) / 2.0  # Map from [-1, 1] to [0, 1]
    similarity = np.clip(similarity, 0.0, 1.0)

    return float(similarity)


def scale_penalty(height1: int, height2: int) -> float:
    """
    Compute penalty for scale mismatch between segments

    Args:
        height1: Height of first segment
        height2: Height of second segment

    Returns:
        Penalty score (0-1, higher penalty is worse)
    """
    # Calculate ratio
    ratio = height1 / height2 if height2 > 0 else 1.0

    # If ratio is acceptable, no penalty
    if MIN_SCALE_RATIO <= ratio <= MAX_SCALE_RATIO:
        return 0.0

    # Calculate how far outside acceptable range
    if ratio < MIN_SCALE_RATIO:
        penalty = (MIN_SCALE_RATIO - ratio) / MIN_SCALE_RATIO
    else:
        penalty = (ratio - MAX_SCALE_RATIO) / MAX_SCALE_RATIO

    # Cap penalty at 1.0
    penalty = min(penalty, 1.0)

    return float(penalty)


def background_plane_similarity(features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
    """
    Compute bonus for matching background planes.
    When both seams are uniform background colors, reward similar colors.

    Args:
        features1: First seam features (with is_background_plane, dominant_color)
        features2: Second seam features (with is_background_plane, dominant_color)

    Returns:
        Similarity score (0-1, higher is better). Returns 0 if not both backgrounds.
    """
    # Check if both seams are background planes
    is_bg1 = features1.get('is_background_plane', False)
    is_bg2 = features2.get('is_background_plane', False)

    # Only activate when BOTH seams are backgrounds
    if not (is_bg1 and is_bg2):
        return 0.0

    # Compare dominant colors using Euclidean distance in RGB space
    color1 = np.array(features1['dominant_color'])
    color2 = np.array(features2['dominant_color'])
    color_distance = np.linalg.norm(color1 - color2)

    # Normalize: practical max distance for similar colors is ~100
    # (theoretical max is ~441 for RGB space, but we focus on similar colors)
    similarity = 1.0 - min(color_distance / 100.0, 1.0)

    # Apply bonus multiplier (creates strong signal when backgrounds match)
    return similarity * BACKGROUND_SIMILARITY_MULTIPLIER


def compute_seam_score(
    seg1_bottom_features: Dict[str, Any],
    seg2_top_features: Dict[str, Any],
    seg1_embedding: np.ndarray,
    seg2_embedding: np.ndarray,
    seg1_height: int,
    seg2_height: int
) -> Tuple[float, Dict[str, float]]:
    """
    Compute comprehensive seam compatibility score

    Args:
        seg1_bottom_features: Bottom seam features of first segment
        seg2_top_features: Top seam features of second segment
        seg1_embedding: CLIP embedding of first segment
        seg2_embedding: CLIP embedding of second segment
        seg1_height: Height of first segment
        seg2_height: Height of second segment

    Returns:
        Tuple of (total_score, subscores_dict)
    """
    # Extract individual scores
    color_sim = color_similarity(
        seg1_bottom_features['color_hist'],
        seg2_top_features['color_hist']
    )

    edge_sim = edge_similarity(
        seg1_bottom_features['edge_density'],
        seg2_top_features['edge_density']
    )

    emb_sim = embedding_similarity(seg1_embedding, seg2_embedding)

    scale_pen = scale_penalty(seg1_height, seg2_height)

    bg_plane_sim = background_plane_similarity(seg1_bottom_features, seg2_top_features)

    # Apply weights
    weights = SEAM_WEIGHTS
    weighted_score = (
        weights['color_similarity'] * color_sim +
        weights['edge_similarity'] * edge_sim +
        weights['embedding_similarity'] * emb_sim +
        weights['scale_penalty'] * (1.0 - scale_pen) +  # Convert penalty to bonus
        weights['background_plane'] * bg_plane_sim
    )

    # Normalize to 0-1 (weights should sum to 1.0)
    total_score = np.clip(weighted_score, 0.0, 1.0)

    subscores = {
        'color_similarity': color_sim,
        'edge_similarity': edge_sim,
        'embedding_similarity': emb_sim,
        'scale_penalty': scale_pen,
        'background_plane_similarity': bg_plane_sim,
    }

    return float(total_score), subscores
