"""
Service for extracting CLIP embeddings from segments
"""
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from typing import Optional, Dict
import open_clip
import cv2

from app.core.config import (
    CLIP_MODEL_NAME,
    CLIP_PRETRAINED,
    EMBEDDINGS_DIR,
)


# Global model cache
_clip_model = None
_clip_preprocess = None
_device = None


def load_clip_model():
    """
    Load CLIP model (cached globally)

    Returns:
        Tuple of (model, preprocess_fn, device)
    """
    global _clip_model, _clip_preprocess, _device

    if _clip_model is not None:
        return _clip_model, _clip_preprocess, _device

    print("Loading CLIP model...")

    # Determine device
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {_device}")

    # Load model and tokenizer
    _clip_model, _, _clip_preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL_NAME,
        pretrained=CLIP_PRETRAINED,
        device=_device
    )

    _clip_model.eval()

    print(f"✓ CLIP model loaded: {CLIP_MODEL_NAME}")

    return _clip_model, _clip_preprocess, _device


def extract_clip_embedding(image: Image.Image) -> np.ndarray:
    """
    Extract CLIP embedding from an image

    Args:
        image: PIL Image

    Returns:
        Embedding as numpy array (normalized)
    """
    model, preprocess, device = load_clip_model()

    # Preprocess image
    image_tensor = preprocess(image).unsqueeze(0).to(device)

    # Extract features
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)

        # Normalize
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        # Convert to numpy
        embedding = image_features.cpu().numpy()[0]

    return embedding


def save_embedding(embedding: np.ndarray, segment_id: int) -> Path:
    """
    Save embedding to disk

    Args:
        embedding: Numpy array
        segment_id: Segment ID

    Returns:
        Path to saved embedding
    """
    embedding_path = EMBEDDINGS_DIR / f"{segment_id}.npy"
    np.save(embedding_path, embedding)
    return embedding_path


def load_embedding(segment_id: int) -> Optional[np.ndarray]:
    """
    Load embedding from disk

    Args:
        segment_id: Segment ID

    Returns:
        Numpy array or None if not found
    """
    embedding_path = EMBEDDINGS_DIR / f"{segment_id}.npy"

    if not embedding_path.exists():
        return None

    return np.load(embedding_path)


def compute_text_image_similarity(image: Image.Image, text_queries: list) -> dict:
    """
    Compute similarity between image and multiple text queries

    Args:
        image: PIL Image
        text_queries: List of text strings to compare against

    Returns:
        Dict mapping text query to similarity score (0-1)
    """
    model, preprocess, device = load_clip_model()

    # Get tokenizer
    tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)

    # Preprocess image
    image_tensor = preprocess(image).unsqueeze(0).to(device)

    # Tokenize text
    text_tokens = tokenizer(text_queries).to(device)

    # Extract features
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        text_features = model.encode_text(text_tokens)

        # Normalize
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Compute similarities
        similarities = (image_features @ text_features.T).squeeze(0)

        # Convert to dict
        results = {query: float(sim) for query, sim in zip(text_queries, similarities)}

    return results


def extract_features_for_segment(segment_id: int, preview_path: str) -> Path:
    """
    Extract and save CLIP embedding for a segment

    Args:
        segment_id: Segment ID
        preview_path: Path to segment preview image

    Returns:
        Path to saved embedding
    """
    # Load segment image
    image = Image.open(preview_path)

    # Extract embedding
    embedding = extract_clip_embedding(image)

    # Save embedding
    embedding_path = save_embedding(embedding, segment_id)

    return embedding_path


def detect_subject_alignment(image_path: str) -> Optional[Dict]:
    """
    Detect the main subject in an image and compute horizontal alignment features
    using multi-scale edge detection and contour analysis.

    Args:
        image_path: Path to segment preview image

    Returns:
        Dict with alignment features:
        {
            'center_x': float,  # Normalized horizontal center (0.0-1.0)
            'width': float,     # Normalized subject width (0.0-1.0)
            'bbox': [x, y, w, h]  # Subject bounding box
        }
        Returns None if subject detection fails
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return None

    height, width = image.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Method 1: Edge-based subject detection
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Multi-scale edge detection (combine multiple thresholds)
    edges1 = cv2.Canny(blurred, 30, 100)
    edges2 = cv2.Canny(blurred, 50, 150)
    edges3 = cv2.Canny(blurred, 70, 200)

    # Combine edges
    edges = cv2.bitwise_or(edges1, edges2)
    edges = cv2.bitwise_or(edges, edges3)

    # Method 2: Enhance with adaptive thresholding for texture
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    # Combine edges and texture
    combined = cv2.bitwise_or(edges, adaptive_thresh)

    # Morphological operations to connect nearby edges and fill gaps
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

    # Close to connect nearby regions
    morphed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel_close)
    # Open to remove small noise
    morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel_open)
    # Dilate to ensure subject is well-captured
    morphed = cv2.dilate(morphed, kernel_open, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        # No subject detected - use center half of image as fallback
        return {
            'center_x': 0.5,
            'width': 0.5,
            'bbox': [width // 4, 0, width // 2, height]
        }

    # Find the most "central" and substantial contour
    # Score contours by: area * (1 - distance_from_center)
    scored_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)

        # Skip very small contours
        if area < (width * height * 0.01):  # Less than 1% of image
            continue

        # Compute center of contour
        cx = x + w / 2
        cy = y + h / 2

        # Distance from image center (normalized)
        center_dist = abs(cx - width / 2) / (width / 2)

        # Score: prefer large, central contours
        score = area * (1.0 - center_dist * 0.5)
        scored_contours.append((score, contour, (x, y, w, h)))

    if not scored_contours:
        # No valid contours - use fallback
        return {
            'center_x': 0.5,
            'width': 0.5,
            'bbox': [width // 4, 0, width // 2, height]
        }

    # Get best contour
    scored_contours.sort(key=lambda x: x[0], reverse=True)
    _, best_contour, (x, y, w, h) = scored_contours[0]

    # Ensure minimum size (at least 15% of image width)
    if w < width * 0.15:
        # Too small, use fallback
        return {
            'center_x': 0.5,
            'width': 0.5,
            'bbox': [width // 4, 0, width // 2, height]
        }

    # Compute normalized features
    center_x = (x + w / 2) / width
    normalized_width = w / width

    return {
        'center_x': float(center_x),
        'width': float(normalized_width),
        'bbox': [int(x), int(y), int(w), int(h)]
    }
