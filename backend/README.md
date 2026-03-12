# Exquisite Corpse Generator

A web application that generates three-part "Exquisite Corpse" composite images from The Metropolitan Museum of Art collection using retrieval and compositing only (no generative AI).

## Overview

This system:
- Retrieves public-domain artworks from The Met Collection API
- Normalizes and processes images
- Generates top/middle/bottom segment candidates
- Computes compatibility scores between seams
- Assembles compatible segments into composite images
- Displays results in a web UI

**No generative AI** - strict retrieval and compositing only.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Pipeline

```bash
# Step 1: Fetch artworks from The Met (target: 500 paintings)
python scripts/1_fetch_met_objects.py --count 500

# Step 2: Normalize images (resize, trim borders)
python scripts/2_normalize_images.py

# Step 3: Generate segment candidates
python scripts/3_generate_segments.py

# Step 4: Test random baseline
python scripts/test_random_baseline.py --count 20
```

Check `data/outputs/` for generated composites!

### 3. Advanced Features (Optional)

For better quality composites with CLIP and FAISS:

```bash
# Extract CLIP embeddings for segments
python scripts/4_extract_features.py

# Build FAISS indexes for fast similarity search
python scripts/5_build_indexes.py

# Generate evaluation gallery
python scripts/6_evaluate_gallery.py --count 100
```

### 4. Run the API Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`

## Project Structure

```
backend/
├── app/
│   ├── api/           # FastAPI endpoints
│   ├── core/          # Configuration
│   ├── db/            # Database models
│   ├── services/      # Core logic (ingestion, segments, scoring, etc.)
│   └── schemas/       # Pydantic schemas
├── scripts/           # Command-line tools (run in order)
├── requirements.txt   # Python dependencies
└── README.md

data/
├── raw_images/        # Original downloaded images
├── normalized_images/ # Processed images (1024px width)
├── segment_previews/  # Cropped segments
├── outputs/           # Generated composites
└── exquisite_corpse.db  # SQLite database

indexes/
├── embeddings/        # CLIP embeddings (.npy files)
└── *.index            # FAISS indexes
```

## Configuration

Edit `backend/app/core/config.py` to customize:
- Image dimensions
- Crop ranges for top/middle/bottom
- Seam scoring weights
- CLIP model settings
- API settings

## Database Schema

**Artworks**: Met collection metadata and images
- Fields: title, artist, date, department, dimensions, etc.
- Stores both raw and normalized image paths

**Segments**: Cropped regions from artworks
- 4 candidates per role (top/middle/bottom) = 12 per artwork
- Includes seam features (color histogram, edge density)
- Links to CLIP embeddings

**Generations**: Created composites
- References to three segments used
- Seam compatibility scores
- Output image path

## API Endpoints

**POST /api/generate**
- Generate a new composite
- Returns image URL and source artwork metadata

**GET /api/artwork/{id}**
- Get artwork details

**GET /api/generation/{id}**
- Get generation details with full source info

**GET /health**
- Health check

## Development Notes

### Random Baseline vs. Scored Generation

The project supports two modes:

1. **Random Baseline** (implemented, fast)
   - Randomly select compatible segments
   - Quick validation of pipeline
   - Good for testing

2. **Scored Generation** (requires features + indexes)
   - Uses CLIP embeddings for similarity
   - FAISS for fast candidate retrieval
   - Multi-factor seam scoring
   - Better quality composites

### Scoring Components

When using scored generation:
- **Color similarity**: Chi-square distance of seam histograms
- **Edge similarity**: Edge density matching
- **Embedding similarity**: CLIP cosine similarity
- **Scale penalty**: Reject extreme height mismatches
- **Diversity bonus**: Prefer different departments/time periods
- **Novelty bonus**: Avoid recently used artworks

### Performance

Target: <5 seconds per generation

Optimizations:
- FAISS for fast vector search
- Pre-computed seam features
- LRU cache for recent generations
- Batch processing for feature extraction

## Troubleshooting

**Images not downloading?**
- Check internet connection
- Met API may be down (status: https://metmuseum.github.io/)
- Rate limits: system respects 80 req/sec max

**Segments not generating?**
- Ensure normalization completed successfully
- Check that artworks have width/height in database
- Verify normalized images exist in `data/normalized_images/`

**CLIP model not loading?**
- Requires ~2GB download on first run
- Check disk space
- May need GPU for faster processing (CPU works but slower)

**Database locked errors?**
- SQLite doesn't handle concurrent writes well
- Close other database connections
- Consider upgrading to PostgreSQL for production

## Credits

- Data source: [The Metropolitan Museum of Art Collection API](https://metmuseum.github.io/)
- All artwork images are public domain from The Met's Open Access collection
- CLIP model: OpenAI via OpenCLIP

## License

MIT License - See LICENSE file for details

Note: Individual artworks have their own copyright status. This project only uses public domain works from The Met.
