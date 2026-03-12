"""
Configuration settings for Exquisite Corpse Generator
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Check environment variables first, fall back to default paths
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
INDEXES_DIR = Path(os.getenv("INDEXES_DIR", str(BASE_DIR / "indexes")))

# Data subdirectories
RAW_IMAGES_DIR = DATA_DIR / "raw_images"
NORMALIZED_IMAGES_DIR = DATA_DIR / "normalized_images"
SEGMENT_PREVIEWS_DIR = DATA_DIR / "segment_previews"
OUTPUTS_DIR = DATA_DIR / "outputs"
EMBEDDINGS_DIR = INDEXES_DIR / "embeddings"

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR / 'exquisite_corpse.db'}"

# Met API settings
MET_API_BASE_URL = "https://collectionapi.metmuseum.org/public/collection/v1"
MET_SEARCH_ENDPOINT = f"{MET_API_BASE_URL}/search"
MET_OBJECT_ENDPOINT = f"{MET_API_BASE_URL}/objects"
MET_MAX_REQUESTS_PER_SECOND = 80
MET_REQUEST_DELAY = 1.0 / MET_MAX_REQUESTS_PER_SECOND  # ~0.0125 seconds

# Ingestion settings
CONCURRENT_DOWNLOADS = 5
DOWNLOAD_RETRY_ATTEMPTS = 3
DOWNLOAD_RETRY_DELAY = 2  # seconds
TARGET_ARTWORK_COUNT = 500

# Image processing settings
NORMALIZED_WIDTH = 1024  # pixels
MIN_IMAGE_WIDTH = 400  # reject if smaller
MIN_IMAGE_HEIGHT = 600  # reject if smaller
BORDER_DETECTION_THRESHOLD = 0.05  # 5% of dimension

# Segment settings
SEGMENT_HEIGHT_MIN = 200  # pixels
SEGMENT_HEIGHT_MAX = 600  # pixels
CROPS_PER_ROLE = 4

# Crop ranges (as percentages of image height)
CROP_RANGES = {
    "top": (0.0, 0.40),      # top 0-40%
    "middle": (0.30, 0.70),   # middle 30-70%
    "bottom": (0.60, 1.0)     # bottom 60-100%
}

# Seam settings
SEAM_STRIP_HEIGHT = 15  # pixels for color/edge analysis
SEAM_BLEND_HEIGHT = 5   # pixels for alpha blending

# Feature extraction
CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "openai"
COLOR_HISTOGRAM_BINS = 8  # per channel

# Seam scoring weights
# HEAVILY emphasize seam matching - edge and color continuity at boundaries
SEAM_WEIGHTS = {
    "color_similarity": 0.12,        # Reduced to make room for background plane
    "edge_similarity": 0.60,         # Reduced slightly for background plane
    "embedding_similarity": 0.0,     # DISABLED - don't care about similar styles at all
    "scale_penalty": 0.18,           # Reduced to make room for background plane
    "background_plane": 0.10         # NEW - bonus for matching background colors
}

# Background plane detection
BACKGROUND_EDGE_THRESHOLD = 0.05      # Max edge density for uniform plane (~5% edges)
BACKGROUND_COLOR_STD_THRESHOLD = 25.0  # Max color std deviation for uniform color
BACKGROUND_SIMILARITY_MULTIPLIER = 1.5 # Bonus multiplier when both seams are backgrounds

# Semantic placement queries for each role
SEMANTIC_QUERIES = {
    "top": ["head", "face", "portrait", "upper body", "shoulders", "bust"],
    "middle": ["torso", "body", "midsection", "waist", "clothing"],
    "bottom": ["legs", "feet", "lower body", "base", "ground", "standing"]
}

# Semantic scoring
SEMANTIC_BONUS = 0.15  # Bonus for semantically correct placement
SEMANTIC_PENALTY = 0.25  # Penalty for semantically incorrect placement (e.g., feet at top)

# Alignment scoring
ALIGNMENT_WEIGHT = 0.3  # Weight for horizontal alignment scoring
ALIGNMENT_TOLERANCE = 0.15  # Tolerance for center position difference (0.0-1.0)
# If centers differ by more than tolerance, apply penalty

# Blank region filtering
BLANK_REGION_THRESHOLD = 0.7  # Reject if >70% of segment is blank/uniform
MIN_EDGE_CONTENT = 0.02  # Minimum edge density to not be considered blank

# Scale constraints
MAX_SCALE_RATIO = 2.0   # reject if one segment is >2x height of another
MIN_SCALE_RATIO = 0.5   # reject if one segment is <0.5x height of another

# Triplet ranking
FAISS_CANDIDATE_COUNT = 50  # top-k candidates from FAISS search
TOP_PAIRS_COUNT = 10        # keep best top-middle pairs before bottom search
DIVERSITY_BONUS = 0.05      # bonus for different departments/periods
NOVELTY_BONUS = 0.03        # bonus for less recently used artworks
CACHE_SIZE = 100            # LRU cache size for generations

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000

# CORS Origins - support environment variable for production
_cors_origins_env = os.getenv("CORS_ORIGINS", "")
if _cors_origins_env:
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",")]
else:
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

# Create directories if they don't exist
for directory in [
    RAW_IMAGES_DIR,
    NORMALIZED_IMAGES_DIR,
    SEGMENT_PREVIEWS_DIR,
    OUTPUTS_DIR,
    EMBEDDINGS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)
