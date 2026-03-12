"""
Service for compositing exquisite corpse images from segments
"""
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.core.config import SEAM_BLEND_HEIGHT, OUTPUTS_DIR
from app.db.models import Segment, Generation


def blend_seam(
    top_image: np.ndarray,
    bottom_image: np.ndarray,
    blend_height: int = SEAM_BLEND_HEIGHT
) -> np.ndarray:
    """
    Blend the seam between two images using linear alpha blending

    Args:
        top_image: Numpy array of top image (H1, W, 3)
        bottom_image: Numpy array of bottom image (H2, W, 3)
        blend_height: Number of pixels to blend

    Returns:
        Blended composite as numpy array
    """
    # Get dimensions
    h1 = top_image.shape[0]
    h2 = bottom_image.shape[0]
    width = top_image.shape[1]

    # Ensure both images have same width
    if top_image.shape[1] != bottom_image.shape[1]:
        raise ValueError("Images must have same width for blending")

    # Calculate total height
    total_height = h1 + h2

    # Create output array
    composite = np.zeros((total_height, width, 3), dtype=np.uint8)

    # If blend height is 0, just stack
    if blend_height == 0:
        composite[:h1, :, :] = top_image
        composite[h1:, :, :] = bottom_image
        return composite

    # Ensure blend height doesn't exceed image heights
    actual_blend = min(blend_height, h1 // 4, h2 // 4)

    if actual_blend <= 0:
        # No blending possible, just stack
        composite[:h1, :, :] = top_image
        composite[h1:, :, :] = bottom_image
        return composite

    # Copy top image (except blend region)
    composite[:h1 - actual_blend, :, :] = top_image[:-actual_blend, :, :]

    # Copy bottom image (except blend region)
    composite[h1 + actual_blend:, :, :] = bottom_image[actual_blend:, :, :]

    # Blend the seam region
    for i in range(actual_blend * 2):
        # Alpha from 1 (top) to 0 (bottom)
        alpha = 1.0 - (i / (actual_blend * 2))

        top_row_idx = h1 - actual_blend + i
        bottom_row_idx = i
        composite_row_idx = h1 - actual_blend + i

        if top_row_idx < h1 and bottom_row_idx < h2:
            blended_row = (
                alpha * top_image[top_row_idx, :, :].astype(float) +
                (1 - alpha) * bottom_image[bottom_row_idx, :, :].astype(float)
            )
            composite[composite_row_idx, :, :] = blended_row.astype(np.uint8)

    return composite


def composite_triplet(
    top_segment: Segment,
    middle_segment: Segment,
    bottom_segment: Segment,
    output_filename: Optional[str] = None,
    blend: bool = True
) -> Tuple[Path, Tuple[int, int]]:
    """
    Create composite image from three segments

    Args:
        top_segment: Top segment
        middle_segment: Middle segment
        bottom_segment: Bottom segment
        output_filename: Optional custom filename (without extension)
        blend: Whether to blend seams (default True)

    Returns:
        Tuple of (output_path, (width, height))
    """
    # Load segment images
    top_img = Image.open(top_segment.preview_path)
    middle_img = Image.open(middle_segment.preview_path)
    bottom_img = Image.open(bottom_segment.preview_path)

    # Convert to numpy arrays
    top_array = np.array(top_img)
    middle_array = np.array(middle_img)
    bottom_array = np.array(bottom_img)

    # Composite top and middle
    if blend:
        top_middle = blend_seam(top_array, middle_array)
    else:
        top_middle = np.vstack([top_array, middle_array])

    # Composite with bottom
    if blend:
        final_composite = blend_seam(top_middle, bottom_array)
    else:
        final_composite = np.vstack([top_middle, bottom_array])

    # Convert back to PIL Image
    composite_image = Image.fromarray(final_composite)

    # Generate output filename if not provided
    if not output_filename:
        output_filename = f"composite_{top_segment.id}_{middle_segment.id}_{bottom_segment.id}"

    output_path = OUTPUTS_DIR / f"{output_filename}.jpg"

    # Save composite
    composite_image.save(output_path, 'JPEG', quality=95)

    return output_path, composite_image.size


def create_generation(
    top_segment_id: int,
    middle_segment_id: int,
    bottom_segment_id: int,
    tm_score: float = 0.0,
    mb_score: float = 0.0,
    total_score: float = 0.0,
    db: Session = None
) -> Generation:
    """
    Create a generation record and composite image

    Args:
        top_segment_id: Top segment ID
        middle_segment_id: Middle segment ID
        bottom_segment_id: Bottom segment ID
        tm_score: Top-middle seam score
        mb_score: Middle-bottom seam score
        total_score: Total score
        db: Database session

    Returns:
        Generation instance
    """
    if not db:
        raise ValueError("Database session required")

    # Get segments
    top_seg = db.query(Segment).filter(Segment.id == top_segment_id).first()
    middle_seg = db.query(Segment).filter(Segment.id == middle_segment_id).first()
    bottom_seg = db.query(Segment).filter(Segment.id == bottom_segment_id).first()

    if not all([top_seg, middle_seg, bottom_seg]):
        raise ValueError("One or more segments not found")

    # Create generation record first to get ID
    generation = Generation(
        top_segment_id=top_segment_id,
        middle_segment_id=middle_segment_id,
        bottom_segment_id=bottom_segment_id,
        tm_score=tm_score,
        mb_score=mb_score,
        total_score=total_score,
    )

    db.add(generation)
    db.flush()  # Get generation ID

    # Create composite
    output_path, dimensions = composite_triplet(
        top_seg,
        middle_seg,
        bottom_seg,
        output_filename=f"gen_{generation.id}"
    )

    generation.output_path = str(output_path)

    db.commit()
    db.refresh(generation)

    return generation
