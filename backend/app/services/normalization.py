"""
Service for normalizing artwork images
Handles border detection, trimming, and resizing to standard dimensions
"""
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional

from app.core.config import (
    NORMALIZED_WIDTH,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    BORDER_DETECTION_THRESHOLD,
)


def detect_uniform_border(image: Image.Image, threshold: float = BORDER_DETECTION_THRESHOLD) -> Tuple[int, int, int, int]:
    """
    Detect uniform color borders at image edges

    Args:
        image: PIL Image
        threshold: Minimum border size as fraction of dimension

    Returns:
        Tuple of (left, top, right, bottom) border sizes in pixels
    """
    img_array = np.array(image)
    height, width = img_array.shape[:2]

    min_border_width = int(width * threshold)
    min_border_height = int(height * threshold)

    left = top = right = bottom = 0

    # Check left border
    for x in range(min(min_border_width, width // 2)):
        column = img_array[:, x]
        if np.std(column) < 10:  # Low variance = uniform color
            left = x + 1
        else:
            break

    # Check right border
    for x in range(width - 1, max(width - min_border_width - 1, width // 2), -1):
        column = img_array[:, x]
        if np.std(column) < 10:
            right = width - x
        else:
            break

    # Check top border
    for y in range(min(min_border_height, height // 2)):
        row = img_array[y, :]
        if np.std(row) < 10:
            top = y + 1
        else:
            break

    # Check bottom border
    for y in range(height - 1, max(height - min_border_height - 1, height // 2), -1):
        row = img_array[y, :]
        if np.std(row) < 10:
            bottom = height - y
        else:
            break

    return left, top, right, bottom


def trim_borders(image: Image.Image) -> Image.Image:
    """
    Trim uniform borders from image

    Args:
        image: PIL Image

    Returns:
        Trimmed image
    """
    left, top, right, bottom = detect_uniform_border(image)

    if left > 0 or top > 0 or right > 0 or bottom > 0:
        width, height = image.size
        crop_box = (
            left,
            top,
            width - right,
            height - bottom
        )
        return image.crop(crop_box)

    return image


def resize_to_standard_width(image: Image.Image, target_width: int = NORMALIZED_WIDTH) -> Image.Image:
    """
    Resize image to standard width while preserving aspect ratio

    Args:
        image: PIL Image
        target_width: Target width in pixels

    Returns:
        Resized image
    """
    width, height = image.size

    if width == target_width:
        return image

    # Calculate new height maintaining aspect ratio
    aspect_ratio = height / width
    new_height = int(target_width * aspect_ratio)

    return image.resize((target_width, new_height), Image.Resampling.LANCZOS)


def validate_dimensions(image: Image.Image) -> bool:
    """
    Check if image meets minimum dimension requirements

    Args:
        image: PIL Image

    Returns:
        True if dimensions are acceptable
    """
    width, height = image.size
    return width >= MIN_IMAGE_WIDTH and height >= MIN_IMAGE_HEIGHT


def normalize_image(input_path: Path, output_path: Path) -> Optional[Tuple[int, int]]:
    """
    Main normalization pipeline:
    1. Load image
    2. Detect and trim borders
    3. Resize to standard width
    4. Validate dimensions
    5. Save normalized image

    Args:
        input_path: Path to raw image
        output_path: Path to save normalized image

    Returns:
        Tuple of (width, height) if successful, None if failed
    """
    try:
        # Load image
        image = Image.open(input_path)

        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Trim borders
        image = trim_borders(image)

        # Resize to standard width
        image = resize_to_standard_width(image)

        # Validate dimensions
        if not validate_dimensions(image):
            print(f"Image too small after normalization: {image.size}")
            return None

        # Save normalized image
        image.save(output_path, 'JPEG', quality=95)

        return image.size

    except Exception as e:
        print(f"Error normalizing image {input_path}: {e}")
        return None


def normalize_artwork_image(artwork_id: int, input_path: str, output_dir: Path) -> Optional[Tuple[int, int]]:
    """
    Normalize a single artwork image

    Args:
        artwork_id: Artwork database ID
        input_path: Path to raw image
        output_dir: Directory to save normalized images

    Returns:
        Tuple of (width, height) if successful, None if failed
    """
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Input file not found: {input_path}")
        return None

    output_path = output_dir / f"{artwork_id}.jpg"

    return normalize_image(input_file, output_path)
