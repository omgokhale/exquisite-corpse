# Exquisite Corpse Generator

A web application that generates three-part "Exquisite Corpse" composite images from The Metropolitan Museum of Art collection using retrieval and compositing only (no generative AI).

## Features

- Fetches public-domain artworks from The Met Collection API
- Normalizes and processes images (border trimming, resizing)
- Generates segment candidates (top/middle/bottom crops)
- Extracts CLIP embeddings and seam features
- Uses FAISS for fast similarity search
- Computes multi-factor compatibility scores
- Creates visually coherent composites
- Web interface for generation and browsing
- Evaluation gallery generation

**Target**: <5 second generation time

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- ~5GB disk space for images and models

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Pipeline

Run these scripts in order to build your dataset:

```bash
# Step 1: Fetch 500 paintings from The Met (takes ~20-30 min)
python scripts/1_fetch_met_objects.py --count 500

# Step 2: Normalize images (resize, trim borders)
python scripts/2_normalize_images.py

# Step 3: Generate segment candidates (4 per role = 12 per artwork)
python scripts/3_generate_segments.py

# Step 4: Extract CLIP embeddings (downloads model on first run, ~2GB)
python scripts/4_extract_features.py

# Step 5: Build FAISS indexes for fast search
python scripts/5_build_indexes.py
```

### 3. Test the System

```bash
# Test with random baseline (no scoring)
python scripts/test_random_baseline.py --count 20

# Or generate evaluation gallery with full scoring
python scripts/6_evaluate_gallery.py --count 100
```

Check `data/outputs/` for generated composites!

### 4. Start the API Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

API available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

### 5. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend available at `http://localhost:3000`

## Project Structure

```
exquisite-corpse/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── core/             # Configuration
│   │   ├── db/               # Database models
│   │   ├── services/         # Core logic
│   │   └── schemas/          # Pydantic schemas
│   ├── scripts/              # Data pipeline scripts (run in order)
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api/              # API client
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   ├── raw_images/           # Downloaded artworks
│   ├── normalized_images/    # Processed (1024px width)
│   ├── segment_previews/     # Cropped segments
│   ├── outputs/              # Generated composites
│   └── exquisite_corpse.db   # SQLite database
│
├── indexes/
│   ├── embeddings/           # CLIP embeddings (.npy)
│   └── *.index               # FAISS indexes
│
├── spec.md                   # Original specification
└── README.md                 # This file
```

## How It Works

### Pipeline Overview

1. **Ingestion**: Download public domain paintings from Met API
2. **Normalization**: Resize to 1024px width, trim borders
3. **Segmentation**: Generate 4 crop candidates per role (top/middle/bottom)
4. **Feature Extraction**: Compute CLIP embeddings + seam features
5. **Indexing**: Build FAISS indexes for fast similarity search
6. **Generation**:
   - Pick random top segment
   - Use FAISS to find compatible middle candidates
   - Score top-middle pairs, keep top 10
   - For each pair, find compatible bottom candidates
   - Score all triplets, return best

### Scoring Components

**Seam Compatibility** (between adjacent segments):
- Color similarity (chi-square distance of histograms)
- Edge similarity (edge density matching)
- Embedding similarity (CLIP cosine similarity)
- Scale penalty (reject extreme height mismatches)

**Triplet Score**:
- Average of seam scores (top-middle, middle-bottom)
- Diversity bonus (different departments/periods)
- Novelty bonus (less recently used artworks)

### Configuration

Edit `backend/app/core/config.py`:
- Image dimensions (1024px width, 200-600px height range)
- Crop ranges (top: 0-40%, middle: 30-70%, bottom: 60-100%)
- Seam scoring weights (color: 0.2, edge: 0.2, embedding: 0.4, scale: 0.2)
- CLIP model (ViT-B/32)
- FAISS candidate count (50)

## API Endpoints

**POST /api/generate**
- Generate new composite
- Returns: image URL, scores, source artworks

**GET /api/artwork/{id}**
- Get artwork details

**GET /api/generation/{id}**
- Get generation with full metadata

**GET /health**
- Health check

## Development

### Random Baseline vs Scored

The system supports two modes:

1. **Random Baseline** (`test_random_baseline.py`)
   - Fast, random selection
   - Good for testing pipeline

2. **Scored Generation** (API `/generate` endpoint)
   - Uses CLIP + FAISS
   - Multi-factor seam scoring
   - Better quality

### Adding More Artworks

```bash
# Ingest more artworks
python scripts/1_fetch_met_objects.py --count 1000

# Re-run normalization, segmentation, feature extraction, indexing
python scripts/2_normalize_images.py
python scripts/3_generate_segments.py
python scripts/4_extract_features.py
python scripts/5_build_indexes.py
```

### Tuning Scores

Edit weights in `backend/app/core/config.py`:

```python
SEAM_WEIGHTS = {
    "color_similarity": 0.2,
    "edge_similarity": 0.2,
    "embedding_similarity": 0.4,
    "scale_penalty": 0.2
}
```

Generate evaluation gallery to see effects:

```bash
python scripts/6_evaluate_gallery.py --count 100
open data/outputs/gallery.html
```

## Performance

- Target: <5 seconds per generation
- Achieved through:
  - Pre-computed seam features
  - FAISS for fast vector search (exact L2)
  - Smart candidate filtering (50 candidates → 10 pairs → best triplet)
  - LRU cache for recent generations

## Troubleshooting

**Met API errors?**
- Check https://metmuseum.github.io/ for status
- System respects 80 req/sec rate limit
- Retry logic handles transient failures

**CLIP model download fails?**
- Requires ~2GB download on first feature extraction
- Check internet connection and disk space

**Generation too slow?**
- Verify FAISS indexes built correctly
- Check that embeddings exist for all segments
- Consider using GPU (CUDA) for faster CLIP inference

**SQLite locked errors?**
- Close other database connections
- Scripts handle this with retries
- Consider PostgreSQL for production

## Credits

- **Data**: [The Metropolitan Museum of Art Open Access Collection](https://www.metmuseum.org/about-the-met/policies-and-documents/open-access)
- **CLIP Model**: OpenAI via [OpenCLIP](https://github.com/mlfoundations/open_clip)
- **Concept**: [Exquisite Corpse](https://en.wikipedia.org/wiki/Exquisite_corpse) surrealist technique

## License

MIT License

All artwork images are public domain from The Met's Open Access collection.

## Next Steps

1. Run the data pipeline (steps 1-5)
2. Generate test composites
3. Start the API and frontend
4. Generate evaluation gallery
5. Tune scoring weights based on results
6. Enjoy creating strange and beautiful composites!
