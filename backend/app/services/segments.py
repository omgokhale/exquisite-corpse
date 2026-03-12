"""
Service for generating and managing image segments
Handles crop generation, seam feature extraction, and quality scoring
"""
import numpy as np
import cv2
from PIL import Image
from pathlib import Path
from typing import List, Tuple, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import (
    NORMALIZED_WIDTH,
    SEGMENT_HEIGHT_MIN,
    SEGMENT_HEIGHT_MAX,
    CROP_RANGES,
    CROPS_PER_ROLE,
    SEAM_STRIP_HEIGHT,
    COLOR_HISTOGRAM_BINS,
    SEGMENT_PREVIEWS_DIR,
    NORMALIZED_IMAGES_DIR,
    BLANK_REGION_THRESHOLD,
    MIN_EDGE_CONTENT,
    BACKGROUND_EDGE_THRESHOLD,
    BACKGROUND_COLOR_STD_THRESHOLD,
)
from app.db.models import Segment, SegmentRole, Artwork


def generate_crops_for_role(
    image: Image.Image,
    role: SegmentRole,
    count: int = CROPS_PER_ROLE
) -> List[Tuple[int, int, int, int]]:
    """
    Generate candidate crop coordinates for a given role

    Args:
        image: PIL Image
        role: Segment role (top/middle/bottom)
        count: Number of crop candidates to generate

    Returns:
        List of crop tuples (x, y, width, height)
    """
    width, height = image.size
    crop_range = CROP_RANGES[role.value]

    crops = []

    for i in range(count):
        # Vary the vertical position within the role's range
        range_start = crop_range[0]
        range_end = crop_range[1]
        range_size = range_end - range_start

        # Distribute crops evenly across the range with slight variation
        offset = (i / max(count - 1, 1)) if count > 1 else 0.5
        vertical_position = range_start + (range_size * offset)

        # Calculate crop height (vary slightly)
        base_height = (range_size * height)
        crop_height = int(min(max(base_height, SEGMENT_HEIGHT_MIN), SEGMENT_HEIGHT_MAX))

        # Ensure crop height is within min/max bounds and fits in image
        crop_height = min(crop_height, height - int(vertical_position * height))
        crop_height = max(crop_height, SEGMENT_HEIGHT_MIN)

        # Calculate y coordinate
        if role == SegmentRole.TOP:
            crop_y = int(vertical_position * height)
        elif role == SegmentRole.MIDDLE:
            crop_y = int((vertical_position * height) - (crop_height / 2))
        else:  # BOTTOM
            crop_y = int((vertical_position * height) - crop_height)

        # Ensure crop is within image bounds
        crop_y = max(0, min(crop_y, height - crop_height))

        crops.append((0, crop_y, width, crop_height))

    return crops


def extract_seam_features(image_array: np.ndarray, position: str) -> Dict[str, Any]:
    """
    Extract features from a seam region (top or bottom strip of segment)

    Args:
        image_array: Numpy array of image (H, W, 3)
        position: 'top' or 'bottom'

    Returns:
        Dict with color_hist and edge_density features
    """
    height = image_array.shape[0]
    strip_height = min(SEAM_STRIP_HEIGHT, height // 4)  # Use at most 1/4 of segment

    if position == 'top':
        seam_strip = image_array[:strip_height, :, :]
    else:  # bottom
        seam_strip = image_array[-strip_height:, :, :]

    # Color histogram (per channel)
    color_hist = []
    for channel in range(3):  # RGB
        hist, _ = np.histogram(
            seam_strip[:, :, channel],
            bins=COLOR_HISTOGRAM_BINS,
            range=(0, 256)
        )
        # Normalize
        hist = hist.astype(float) / hist.sum() if hist.sum() > 0 else hist.astype(float)
        color_hist.extend(hist.tolist())

    # Edge density using Canny edge detection
    gray_seam = cv2.cvtColor(seam_strip, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray_seam, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)

    # Background plane detection (uniform color regions)
    # Criterion 1: Low edge density indicates uniform region
    # Criterion 2: Low color variance indicates uniform color
    color_std = float(np.std(seam_strip))
    is_background = (edge_density < BACKGROUND_EDGE_THRESHOLD and
                     color_std < BACKGROUND_COLOR_STD_THRESHOLD)

    # Extract dominant color (mean across strip)
    dominant_color = np.mean(seam_strip, axis=(0, 1)).tolist()  # [R, G, B]

    return {
        'color_hist': color_hist,
        'edge_density': edge_density,
        'is_background_plane': is_background,
        'dominant_color': dominant_color,
        'color_std': color_std
    }


def is_mostly_blank(image_array: np.ndarray) -> bool:
    """
    Check if segment is mostly blank/uniform space

    Args:
        image_array: Numpy array of segment image

    Returns:
        True if segment is mostly blank
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    # Check edge content
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size

    if edge_density < MIN_EDGE_CONTENT:
        return True

    # Check color variance
    color_variance = np.var(image_array)
    if color_variance < 100:  # Very uniform color
        return True

    # Check if large uniform regions exist
    # Simple approach: check if most pixels are similar to mean
    mean_color = np.mean(image_array, axis=(0, 1))
    distances = np.linalg.norm(image_array - mean_color, axis=2)
    uniform_ratio = np.sum(distances < 30) / distances.size

    if uniform_ratio > BLANK_REGION_THRESHOLD:
        return True

    return False


def compute_quality_score(image_array: np.ndarray) -> float:
    """
    Compute quality score for a segment

    Args:
        image_array: Numpy array of segment image

    Returns:
        Quality score (0-1)
    """
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    # Edge variance (higher is better)
    edges = cv2.Canny(gray, 50, 150)
    edge_variance = np.var(edges)

    # Color variance (higher is better)
    color_variance = np.var(image_array)

    # Check if mostly blank (penalty)
    mean_intensity = np.mean(gray)
    blank_penalty = 1.0
    if mean_intensity < 20 or mean_intensity > 235:  # Very dark or very light
        blank_penalty = 0.5

    # Normalize and combine
    edge_score = min(edge_variance / 1000.0, 1.0)
    color_score = min(color_variance / 5000.0, 1.0)

    quality = (edge_score * 0.6 + color_score * 0.4) * blank_penalty

    return float(quality)


def save_segment_preview(image: Image.Image, segment_id: int) -> Path:
    """
    Save segment preview image

    Args:
        image: PIL Image of segment
        segment_id: Segment database ID

    Returns:
        Path to saved preview
    """
    preview_path = SEGMENT_PREVIEWS_DIR / f"{segment_id}.jpg"
    image.save(preview_path, 'JPEG', quality=90)
    return preview_path


def generate_segments_for_artwork(artwork_id: int, db: Session) -> List[Segment]:
    """
    Generate all segments for an artwork

    Args:
        artwork_id: Artwork database ID
        db: Database session

    Returns:
        List of created Segment instances
    """
    # Get artwork
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork:
        raise ValueError(f"Artwork {artwork_id} not found")

    if not artwork.width or not artwork.height:
        raise ValueError(f"Artwork {artwork_id} not normalized (missing dimensions)")

    # Load normalized image
    image_path = NORMALIZED_IMAGES_DIR / f"{artwork_id}.jpg"
    if not image_path.exists():
        raise FileNotFoundError(f"Normalized image not found: {image_path}")

    image = Image.open(image_path)
    image_array = np.array(image)

    created_segments = []

    # Generate segments for each role
    for role in SegmentRole:
        crops = generate_crops_for_role(image, role, count=CROPS_PER_ROLE)

        for crop_x, crop_y, crop_w, crop_h in crops:
            # Extract crop
            crop_image = image.crop((
                crop_x,
                crop_y,
                crop_x + crop_w,
                crop_y + crop_h
            ))
            crop_array = np.array(crop_image)

            # Skip mostly blank segments for middle and bottom roles
            # (Top can have sky/background, but middle/bottom should have content)
            if role in [SegmentRole.MIDDLE, SegmentRole.BOTTOM]:
                if is_mostly_blank(crop_array):
                    continue  # Skip this segment

            # Extract seam features
            top_seam_features = extract_seam_features(crop_array, 'top')
            bottom_seam_features = extract_seam_features(crop_array, 'bottom')

            # Compute quality score
            quality_score = compute_quality_score(crop_array)

            # Create segment record (without saving preview yet)
            segment = Segment(
                artwork_id=artwork_id,
                role=role,
                crop_x=crop_x,
                crop_y=crop_y,
                crop_w=crop_w,
                crop_h=crop_h,
                top_seam_features=top_seam_features,
                bottom_seam_features=bottom_seam_features,
                quality_score=quality_score,
            )

            db.add(segment)
            db.flush()  # Get segment ID

            # Save preview
            preview_path = save_segment_preview(crop_image, segment.id)
            segment.preview_path = str(preview_path)

            created_segments.append(segment)

    db.commit()

    return created_segments
