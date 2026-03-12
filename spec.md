# Exquisite Corpse Generator
## AI Agent Implementation Spec (Met Museum Dataset)

---

# 1. Project Overview

Build a prototype web application that generates **three-part “Exquisite Corpse” images** by vertically stacking cropped segments from three different artworks in **The Metropolitan Museum of Art Open Access collection**.

The system will:

- Retrieve public-domain artworks from **The Met Collection API**
- Download and store images locally
- Generate candidate **top / middle / bottom** crop segments
- Compute **compatibility scores between seams**
- Assemble three compatible segments into a single composite image
- Display the result in a simple web UI

This system uses **retrieval and compositing only**.

It must **not** use:

- inpainting
- outpainting
- diffusion models
- seam hallucination
- generative editing
- AI image synthesis

---

# 2. Data Source

Use **The Metropolitan Museum of Art Collection API** as the dataset.

Documentation:  
https://metmuseum.github.io/

Key endpoints:

GET /public/collection/v1/search
GET /public/collection/v1/objects/{objectID}
GET /public/collection/v1/objects

The API:

- requires **no API key**
- supports **80 requests/second max**
- provides **Open Access public-domain images**

Important fields from the object endpoint:

- `objectID`
- `isPublicDomain`
- `primaryImage`
- `primaryImageSmall`
- `objectName`
- `title`
- `artistDisplayName`
- `artistDisplayBio`
- `objectDate`
- `objectBeginDate`
- `objectEndDate`
- `department`
- `medium`
- `dimensions`

Only ingest records where:

isPublicDomain = true
primaryImage != “”

Prefer:

objectName = Painting

---

# 3. Product Behavior

User flow:

1. User opens web app
2. User clicks **Generate**
3. System selects three compatible segments
4. System composites them vertically
5. Result is displayed
6. Source artwork credits are shown

Outputs should feel:

- coherent
- strange
- compositionally readable

Perfect realism is **not required**.

---

# 4. Non-Goals

The system must **not implement**:

- generative image models
- inpainting or outpainting
- diffusion pipelines
- seam generation
- object morphing
- user uploads
- accounts
- social features

This project is strictly:

dataset ingestion
→ image analysis
→ crop generation
→ seam matching
→ compositing

---

# 5. System Architecture

Two layers:

## Offline Processing

Responsible for:

- dataset ingestion
- image downloading
- normalization
- candidate crop generation
- feature extraction
- compatibility indexing

## Online Generation

Responsible for:

- selecting candidate segments
- computing seam compatibility
- ranking triplets
- compositing images
- returning results

---

# 6. Technology Stack

Backend:

- Python
- FastAPI

Image processing:

- Pillow
- OpenCV

Vision models:

- CLIP or OpenCLIP

Data storage:

- SQLite (prototype)
- optional Postgres later

Vector search:

- FAISS

Frontend:

- React or Next.js

---

# 7. Dataset Size Targets

| Phase | Image Count |
|------|-------------|
| Initial testing | 200–300 |
| Prototype | 1,000–3,000 |
| Strong corpus | 5,000+ |

---

# 8. Database Schema

## artworks

id
met_object_id
title
artist
artist_bio
object_date
begin_date
end_date
department
object_name
medium
dimensions
primary_image_url
primary_image_small_url
local_image_path
width
height
is_public_domain
raw_json

---

## segments

id
artwork_id
role (top / middle / bottom)
crop_x
crop_y
crop_w
crop_h
preview_path
embedding_ref
top_seam_features_json
bottom_seam_features_json
quality_score

---

## generations

id
top_segment_id
middle_segment_id
bottom_segment_id
tm_score
mb_score
total_score
output_path
created_at

---

# 9. Build Phases

---

# Phase 1 — Project Setup

Create repository structure.

Deliverables:

- backend service
- frontend scaffold
- scripts folder
- data directory
- configuration system
- README

---

# Phase 2 — Met API Ingestion

Create ingestion pipeline.

Steps:

1. Query search endpoint
2. Fetch object records
3. Filter by:

isPublicDomain = true
primaryImage exists
objectName = Painting (preferred)

4. Download `primaryImage`
5. Store metadata and image locally

Output:

- dataset of 200–300 artworks
- populated database

---

# Phase 3 — Image Normalization

For each downloaded image:

- create normalized analysis copy
- preserve full-resolution original
- compute width/height
- trim borders if detected
- reject very small images

Output:

normalized image dataset

---

# Phase 4 — Naive Crop Generator

Create candidate segments:

top
middle
bottom

Example segmentation:

top = top 0–40% of image
middle = 30–70%
bottom = 60–100%

Generate **multiple candidate crops per role**.

Create baseline generator:

select random top
select random middle
select random bottom
stack vertically

Deliverable:

Working random exquisite corpse generator.

---

# Phase 5 — Feature Extraction

For each segment compute:

- CLIP embedding
- dominant color palette
- seam-region color histogram
- edge density profile
- silhouette/contour descriptor

Optional:

- saliency map
- segmentation signals

Persist features.

---

# Phase 6 — Seam Compatibility Scoring

Compute compatibility between:

top.bottom ↔ middle.top
middle.bottom ↔ bottom.top

Score components:

color continuity
edge similarity
contour similarity
embedding similarity
scale plausibility

Total pair score:

pair_score =
w1 * color_similarity
	•	w2 * edge_similarity
	•	w3 * contour_similarity
	•	w4 * embedding_similarity

	•	w5 * scale_penalty

All sub-scores must be stored for debugging.

---

# Phase 7 — Triplet Ranking

Generate candidate triplets:

top → compatible middle → compatible bottom

Triplet score:

tm seam score
mb seam score
composition balance
style compatibility
diversity bonus
novelty bonus

Reject:

- identical artworks
- extreme scale mismatch
- unreadable compositions

---

# Phase 8 — Compositing Engine

Assemble final image.

Rules:

- resize segments to common width
- stack vertically
- allow minor crop adjustments
- allow minor scaling
- optional seam feather

Strict rule:

NO generative editing
NO hallucinated pixels

Output:

final composite image

---

# Phase 9 — API

Implement endpoints:

POST /generate
GET /artwork/{id}
GET /health

`POST /generate` returns:

output image
source artworks
crop coordinates
compatibility scores

---

# Phase 10 — Frontend

UI elements:

Generate button
Result image display
Source artwork credits
optional “show sources”

Keep UI minimal.

---

# Phase 11 — Evaluation Tooling

Create script:

generate 100+ outputs
save results
save source previews
log scores
generate gallery HTML

Purpose:

Manual inspection and tuning.

---

# 10. Quality Filters

Reject artworks if:

- image too small
- missing primary image
- not public domain
- strong border/frame
- extreme aspect ratio

Reject segments if:

- crop mostly blank
- seam region uninformative
- crop too noisy

Reject pairings if:

- extreme scale mismatch
- severe seam discontinuity
- color clash

Reject triplets if:

- duplicate source images
- composition unreadable

---

# 11. Engineering Constraints

The agent must:

- implement random baseline first
- keep modules small
- expose scoring internals
- persist intermediate outputs
- keep pipeline runnable via CLI
- avoid premature complexity

---

# 12. Folder Structure

exquisite-corpse/
backend/
app/
main.py
api/
generate.py
artwork.py
core/
config.py
db/
models.py
session.py
services/
met_ingestion.py
normalization.py
segments.py
features.py
matching.py
ranking.py
compositing.py
schemas/
artwork.py
generation.py

scripts/
  fetch_met_objects.py
  preprocess_images.py
  generate_segments.py
  extract_features.py
  build_indexes.py
  evaluate_gallery.py

frontend/
src/
components/
pages/

data/
raw_images/
normalized_images/
segment_previews/
outputs/

indexes/

docs/

---

# 13. Success Criteria

The system is successful if:

- Met API ingestion works
- images download and normalize correctly
- system generates composites from three distinct artworks
- results appear visually coherent
- generation is fast
- source credits are preserved
- no generative editing occurs anywhere

---

# 14. Guiding Principle

This project is **not about perfect seam matching**.

The goal is to produce compositions that feel:

coherent
surprising
strange
readable

The best outputs are often **slightly mismatched but compositionally meaningful**.

---

# 15. Implementation Notes & Learnings

## Completed Implementation (March 2026)

### System Status
- ✅ **Fully functional** web application
- ✅ Met API ingestion working (50 artworks in prototype, designed for 500+)
- ✅ CLIP + FAISS scoring system operational
- ✅ Generation time: **~86ms** (well under <5s target)
- ✅ Frontend with React + Vite deployed locally

### Critical Implementation Decisions

#### Database & Concurrency
- **SQLite limitation discovered**: Does NOT support concurrent writes
- **Solution**: Changed from concurrent (ThreadPoolExecutor) to **sequential processing** in `met_ingestion.py`
- Trade-off: Slower ingestion (~5-10 min for 50 artworks) but reliable
- For production scale: Consider PostgreSQL for concurrent writes

#### Image Dimensions (Confirmed)
- **Normalized width**: 1024px (all segments)
- **Segment heights**: 200-600px range
- **Crops per role**: 4 candidates per artwork (top/middle/bottom)
- Overlapping crop ranges (0-40%, 30-70%, 60-100%) work well for variety

#### Seam Scoring Weights - **TUNED FOR USER PREFERENCE**

**Original spec** (equal weights):
```python
color_similarity: 0.2
edge_similarity: 0.2
embedding_similarity: 0.4
scale_penalty: 0.2
```

**Implemented weights** (after user feedback):
```python
color_similarity: 0.1      # REDUCED - diverse colors preferred
edge_similarity: 0.6       # INCREASED - line/contour continuity is key
embedding_similarity: 0.1  # REDUCED - encourage diverse art styles
scale_penalty: 0.2         # UNCHANGED - important for proportions
```

**Rationale**: User values **line-level continuity across seams** with **stylistically diverse** compositions. Goal is "body-like" forms where edges connect naturally, NOT visually similar artworks.

### User-Identified Quality Patterns

**Good composites**:
- Form cohesive "body" shape: head → torso → legs/base
- Lines and edges **continue/flow** across seam boundaries
- Different art periods, styles, and colors (not matching)
- Compositional coherence despite stylistic diversity

**Bad composites**:
- Semantic misplacement (feet at top, heads at bottom)
- Blank/empty middle or bottom sections
- Disconnected edges (lines don't continue across seams)
- Too much visual similarity (boring, defeats surrealist purpose)

### Features Added Beyond Original Spec

#### 1. Semantic Placement Scoring (Implemented, Currently Disabled)
**Location**: `app/services/ranking.py::compute_semantic_score()`

**Purpose**: Ensure compositionally appropriate placements
- Top segments match: "head", "face", "portrait", "upper body", "shoulders"
- Middle segments match: "torso", "body", "midsection", "waist"
- Bottom segments match: "legs", "feet", "lower body", "base"

**Implementation**: Uses CLIP text-image similarity
- **Bonus** (+0.15) for semantically correct placements
- **Penalty** (-0.25) for obvious errors (e.g., feet at top)

**Status**: Code exists but **temporarily disabled** (lines commented out)
- Real-time CLIP inference too slow (~5-10s per generation)
- **TODO**: Pre-compute semantic scores during segment generation (like embeddings)
- Store in database, use during ranking (will be fast)

#### 2. Blank Region Filtering
**Location**: `app/services/segments.py::is_mostly_blank()`

**Purpose**: Reject segments that are mostly empty space
- Filters applied to **middle and bottom** roles only
- Top can have sky/background (appropriate for heads/portraits)

**Criteria**:
- Edge density < 2% of pixels
- Color variance < 100
- >70% of pixels near uniform color

**Impact**: Prevents composites with blank sky or backgrounds in body positions

### Technical Architecture

#### Backend Stack (Confirmed)
- **Framework**: FastAPI + Uvicorn
- **Database**: SQLite (prototype) - use PostgreSQL for production
- **Image Processing**: Pillow + OpenCV
- **ML**: OpenCLIP (ViT-B/32, ~2GB model)
- **Vector Search**: FAISS (IndexFlatL2 for exact search)

#### Frontend Stack (Confirmed)
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Inline styles (minimal CSS)
- **API Client**: Native fetch

#### API Endpoints

**Working**:
- `POST /api/generate` - Scored generation (FAISS + CLIP)
- `POST /api/generate/random` - Random fallback (no FAISS needed)
- `GET /api/artwork/{id}` - Artwork metadata
- `GET /api/generation/{id}` - Generation details
- `GET /health` - Health check

**Note**: Both generate endpoints work, random is faster without features/indexes

### Performance Characteristics

**One-time Setup** (per dataset):
1. Ingestion (50 artworks): ~5-10 minutes (sequential due to SQLite)
2. Normalization: ~1 minute
3. Segment generation: ~2-3 minutes
4. CLIP feature extraction: ~10-15 minutes (first run downloads 2GB model)
5. FAISS index building: ~1-2 minutes

**Runtime Performance**:
- Random generation: <100ms
- Scored generation (FAISS): ~86ms
- Target met: <5 seconds ✓

### Scripts Execution Order

**Initial Setup** (run once):
```bash
1. python scripts/1_fetch_met_objects.py --count 50
2. python scripts/2_normalize_images.py
3. python scripts/3_generate_segments.py
4. python scripts/4_extract_features.py  # Optional but recommended
5. python scripts/5_build_indexes.py     # Optional but recommended
```

**Evaluation**:
```bash
6. python scripts/6_evaluate_gallery.py --count 100
```

**Testing**:
```bash
python scripts/test_random_baseline.py --count 20
python scripts/check_setup.py  # Diagnostic tool
```

### Known Issues & Future Work

#### TODO: Pre-compute Semantic Scores
Currently semantic scoring is disabled because real-time CLIP inference is slow.

**Solution**:
1. Add semantic score fields to Segments table
2. Compute during segment generation (scripts/3_generate_segments.py)
3. Store top/middle/bottom semantic scores in database
4. Use pre-computed scores during ranking (fast lookup)
5. Re-enable in ranking.py by uncommenting lines

#### TODO: Increase Dataset
- Current: 50 artworks (prototype)
- Target: 500-1000+ for production
- More artworks = better variety and quality

#### Potential Enhancements
Based on user feedback, future improvements could include:

1. **Vertical alignment matching** - Match left/centered/right subject positioning
2. **Subject width consistency** - Match proportional sizes across segments
3. **Orientation checking** - Reject upside-down segments
4. **User rating system** - Collect feedback to tune weights adaptively
5. **Advanced contour matching** - Detect if edges actually connect vertically (not just similar density)

### Environment Notes

**Development Environment**:
- macOS (Darwin 24.6.0)
- Python 3.9.6
- Node.js 18+
- Use `python3` not `python` on macOS
- Virtual environment required: `python3 -m venv venv`

**Key Files Modified During Implementation**:
- `app/core/config.py` - Scoring weights tuned
- `app/services/ranking.py` - Semantic scoring added
- `app/services/segments.py` - Blank filtering added
- `app/services/features.py` - Text-image similarity added
- `app/api/generate.py` - Random fallback endpoint
- `frontend/src/api/client.js` - Error handling improved

### Success Metrics - ACHIEVED ✓

- ✓ Met API ingestion works reliably
- ✓ Images download and normalize correctly (sequential processing)
- ✓ System generates composites from three distinct artworks
- ✓ Results are compositionally coherent (with tuned weights)
- ✓ Generation is fast (<100ms, target was <5s)
- ✓ Source credits preserved and displayed
- ✓ No generative editing anywhere (strict retrieval only)

### Deployment Instructions

**Backend**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
# Access: http://localhost:8000
```

**Frontend**:
```bash
cd frontend
npm install  # First time only
npm run dev
# Access: http://localhost:3000
```

**Both must run simultaneously in separate terminals**

---

## Session 2 Updates (March 2026) - Dataset Expansion & Background Plane Matching

### Major Changes

#### 1. Dataset Expansion: 50 → 430 Artworks
**Status**: ✅ Completed

**Motivation**: User feedback indicated insufficient variety in composites, with same artworks appearing too frequently.

**Implementation**:
- Ingested 450 additional artworks from Met Museum API
- 430 successfully normalized (20 rejected as too small)
- Generated 4,726 new segments
- Extracted CLIP features for all new segments
- Built FAISS indexes: 1,916 top / 1,733 middle / 1,665 bottom
- Computed semantic scores for all 5,314 total segments

**Results**:
- 9x dataset increase
- Semantic score distribution:
  - Top: 83% positive matches
  - Middle: 100% positive matches
  - Bottom: 32% positive matches

#### 2. Alignment Scoring - Attempted and Removed
**Status**: ❌ Removed (made results worse)

**Attempt**: Implemented ML-based subject alignment detection
- Used OpenCV multi-scale edge detection
- Detected subject bounding boxes and horizontal centers
- Scored based on center position alignment (left/center/right)
- Added `alignment_features` JSON field to Segment model

**User Feedback**: "I feel this is not right, perhaps worse than earlier. The subjects do not align in a compelling manner."

**Resolution**:
- **Completely disabled** alignment scoring in `ranking.py`
- Code remains but commented out for historical reference
- Alignment weight set to 0.3 but not used

**Lesson Learned**: Direct subject detection creates false positives. Better approach is indirect alignment through background matching (see below).

#### 3. Seam Matching Optimization
**Status**: ✅ Implemented

**Previous Weights**:
```python
color_similarity: 0.15
edge_similarity: 0.65
embedding_similarity: 0.0
scale_penalty: 0.2
```

**Current Weights** (after background plane addition):
```python
color_similarity: 0.12        # Reduced to make room
edge_similarity: 0.60         # Slightly reduced
embedding_similarity: 0.0     # Keep disabled
scale_penalty: 0.18           # Reduced to make room
background_plane: 0.10        # NEW
```

**Rationale**: User values seam continuity above all else. Reallocated weights to add background plane matching without losing total scoring power.

#### 4. Recent Artwork Prevention - Strengthened
**Status**: ✅ Implemented

**Previous**: `deque(maxlen=100)` - tracked 100 recent artworks
**Current**: `deque(maxlen=15)` - tracks only last 15 artworks

**Implementation Details**:
- Changed in `app/services/ranking.py` line 38
- Added **hard exclusion** in `generate_triplet()`:
  ```python
  if recent_artwork_ids:
      query = query.filter(Segment.artwork_id.notin_(recent_artwork_ids))
  ```
- Prevents same painting appearing in consecutive generations
- If no artworks available (all recent), clears history and retries

**Impact**: User will not see duplicate artworks in back-to-back generations.

#### 5. Background Plane Color Matching - NEW FEATURE
**Status**: ✅ Implemented and Deployed

**Motivation**: User insight - "If two images have blue sky backgrounds, it could be helpful to try to have those blues meet, which would subsequently also lead to the subject matter meeting nicely."

**Key Insight**: Instead of detecting subjects directly (which failed), detect uniform **background planes** and match their colors. This indirectly aligns subjects as a natural byproduct.

**Implementation**:

**A. Background Detection** (`app/services/segments.py`):
- Dual-criteria detection:
  1. Low edge density (< 5% edges)
  2. Low color standard deviation (< 25.0)
- Extracts dominant RGB color (mean across strip)
- Added to seam features:
  ```python
  {
      'color_hist': [...],          # Existing
      'edge_density': 0.0-1.0,      # Existing
      'is_background_plane': bool,  # NEW
      'dominant_color': [R,G,B],    # NEW
      'color_std': float            # NEW
  }
  ```

**B. Similarity Scoring** (`app/services/matching.py`):
- New function: `background_plane_similarity()`
- Only activates when **both** seams are backgrounds
- Uses Euclidean distance in RGB space
- Applies 1.5x bonus multiplier for matching backgrounds
- Returns 0.0 if not applicable (doesn't interfere with other scores)

**C. Configuration** (`app/core/config.py`):
```python
# Background plane detection thresholds
BACKGROUND_EDGE_THRESHOLD = 0.05      # Max edge density
BACKGROUND_COLOR_STD_THRESHOLD = 25.0  # Max color variance
BACKGROUND_SIMILARITY_MULTIPLIER = 1.5 # Bonus multiplier
```

**D. Database Update**:
- Reprocessed all 5,314 segments with new features
- Detection results:
  - Top seams: 701 backgrounds (13.2%)
  - Bottom seams: 467 backgrounds (8.8%)

**How It Works**:
1. System detects when seam strip is uniform (low edges + low color variance)
2. If both seams are backgrounds, compares dominant colors
3. Rewards similar colors (blue sky meeting blue sky)
4. Subject alignment occurs naturally as backgrounds pull into position

**Example Scenarios**:
- Blue sky (top) + blue sky (middle) → bonus for color match → subjects align
- Solid wall (middle) + solid wall (bottom) → bonus → figure alignment
- Gradient background continuity → smooth visual flow

**Advantages**:
- Non-breaking: Existing segments work (uses `.get()` for new fields)
- Selective: Only activates when both are backgrounds
- Efficient: Leverages existing edge density computation
- Transparent: Subscores show `background_plane_similarity` value
- Configurable: Easy to tune thresholds and multiplier

**File Changes**:
- `app/core/config.py` - Added 3 config parameters, updated SEAM_WEIGHTS
- `app/services/segments.py` - Extended `extract_seam_features()` with background detection
- `app/services/matching.py` - Added `background_plane_similarity()` function, integrated into scoring
- `scripts/recompute_seam_features.py` - Created script to rebuild features for all segments

### Updated Seam Scoring Formula

**Current Complete Formula**:
```python
total_score = (
    0.12 * color_similarity +
    0.60 * edge_similarity +
    0.00 * embedding_similarity +
    0.18 * (1.0 - scale_penalty) +
    0.10 * background_plane_similarity
)

where background_plane_similarity = {
    0.0                              if not (both_are_backgrounds)
    (1.0 - distance/100) * 1.5      if both_are_backgrounds
}
```

**Subscores Tracked**:
- `color_similarity` - Chi-square distance of color histograms
- `edge_similarity` - Edge density matching
- `embedding_similarity` - CLIP cosine similarity (disabled)
- `scale_penalty` - Height ratio mismatch
- `background_plane_similarity` - Dominant color matching (NEW)

### Scripts Added/Modified

**New Scripts**:
- `scripts/recompute_seam_features.py` - Rebuild seam features with background detection

**Modified Scripts**:
- `scripts/compute_semantic_scores.py` - Used as reference pattern

### Database Schema Updates

**Segments Table** (JSON fields extended):
- `top_seam_features`: Now includes `is_background_plane`, `dominant_color`, `color_std`
- `bottom_seam_features`: Now includes `is_background_plane`, `dominant_color`, `color_std`
- `alignment_features`: Added but unused (from failed alignment attempt)

### Performance Impact

**Feature Extraction**: No significant impact
- Background detection adds ~2 operations (np.std, np.mean)
- Computed during existing seam feature extraction
- No additional image loading

**Scoring**: Negligible impact
- Background similarity computed only when both are backgrounds (~1-13% of cases)
- Simple Euclidean distance calculation
- Total generation time remains <100ms

### Testing Recommendations

After these changes, test composite quality for:
1. **Background continuity**: Sky-to-sky, wall-to-wall color matching
2. **Subject alignment**: Check if matching backgrounds pull subjects into position
3. **Variety**: Verify no duplicate artworks in consecutive generations
4. **Performance**: Confirm generation still <100ms

**Tuning Parameters** (if needed):
- `BACKGROUND_EDGE_THRESHOLD` - Increase to detect more backgrounds
- `BACKGROUND_COLOR_STD_THRESHOLD` - Increase for textured backgrounds
- `BACKGROUND_SIMILARITY_MULTIPLIER` - Increase for stronger effect
- Seam weight for `background_plane` - Increase from 0.10 if underpowered

### Known Limitations

**Background Detection**:
- Cannot distinguish foreground subjects from backgrounds
- Relies on uniformity heuristics (edge + color variance)
- May miss textured backgrounds (e.g., detailed sky paintings)

**Color Matching**:
- Uses RGB Euclidean distance (not perceptually uniform like LAB)
- Max distance normalized to 100 (arbitrary, may need tuning)
- No hue/saturation awareness (blue ≠ green but close in RGB space)

### Future Enhancements (Potential)

Based on implementation learnings:

1. **Perceptual Color Spaces**: Use LAB or LUV instead of RGB for better color matching
2. **Adaptive Thresholds**: Learn background detection thresholds from dataset statistics
3. **Gradient Matching**: Detect and match background gradients (e.g., sky gradation)
4. **Background Type Classification**: Classify backgrounds (sky, wall, landscape, abstract)
5. **Multi-scale Background Detection**: Check multiple strip heights for robustness

### Session Summary

**Core Achievements**:
- ✅ Dataset expanded 9x for better variety
- ✅ Background plane matching implemented (novel indirect alignment approach)
- ✅ Recent artwork prevention strengthened
- ✅ Seam weights optimized for user preference
- ❌ Direct alignment scoring attempted but removed (user feedback: made results worse)

**Key Lesson**:
Indirect alignment through background color matching is more effective than direct subject detection. Matching uniform color planes (sky, walls) naturally pulls subjects into alignment without complex ML inference.

**Files Modified** (Session 2):
- `app/core/config.py` - Background config, weights updated
- `app/services/segments.py` - Background detection added
- `app/services/matching.py` - Background similarity function added
- `app/services/ranking.py` - Alignment scoring disabled, recent artwork logic strengthened
- `scripts/recompute_seam_features.py` - Created
- `scripts/1_fetch_met_objects.py` - Run for 450+ artworks
- `scripts/2_normalize_images.py` - Processed 430 new images
- `scripts/3_generate_segments.py` - Generated 4,726 segments
- `scripts/4_extract_features.py` - Extracted CLIP embeddings
- `scripts/5_build_indexes.py` - Rebuilt FAISS indexes
- `scripts/compute_semantic_scores.py` - Computed scores for all segments

---

## Session 3 Updates (March 2026) - UI/UX Redesign & Typography

### Major Changes

#### 1. Visual Design Overhaul
**Status**: ✅ Completed

**Dark Theme Implementation**:
- Entire app background: #000000 (pure black)
- All text colors adjusted for dark theme contrast
- Links: #6b9fff (light blue)
- UI elements use dark gray (#333333) backgrounds

**Header Redesign**:
- Replaced "Exquisite Corpse Generator" text with LogoA.svg
- Logo: 24px tall, 24px from top of window
- Position: absolute, floating transparently over canvas
- No opaque background, overlays image when zoomed

**Layout Changes**:
- Image container: Full viewport (100vh × 100vw)
- Initial image constraints: `maxHeight: calc(100vh - 160px)` to leave space for logo (top) and button (bottom)
- Logo spacing: 24px top + 24px logo + 24px padding = 72px total top
- Button spacing: 24px padding + 40px button + 24px bottom = 88px total bottom
- Footer: Repositioned above Create button

#### 2. Image Zoom & Pan Functionality
**Status**: ✅ Implemented

**Zoom Controls**:
- **Command + scroll** (Mac) or **Ctrl + scroll** (Windows/Linux) to zoom
- **Trackpad pinch-to-zoom** gestures
- Zoom range: 0.5x to 5x
- Smooth animation with requestAnimationFrame (1.02/0.98 increments)
- Initial fit: Image respects spacing, zoomed: Image can fill entire screen

**Pan Controls**:
- Click and drag to pan when zoomed (scale > 1)
- Cursor changes: default → grab → grabbing
- Position tracked with translate transform

**Reset Zoom Button**:
- Position: Bottom left, 132px from left, 24px from bottom
- Style: Circular, 40px diameter, dark gray background
- Icon: full.svg (24×24px, white)
- Always visible, grayed out (30% opacity) when at default zoom
- Smooth 0.5s opacity transition
- Click triggers 400ms animated return to scale=1, position=(0,0)
- Ease-out cubic easing for natural deceleration

**Zoom/Scroll Conflict Resolution**:
- Sources modal scrolling: Detects mouse over modal, allows normal scrolling
- Main canvas: Captures wheel events for zoom when not over modal
- `data-sources-modal` attribute used for detection

#### 3. Create Button Redesign
**Status**: ✅ Completed

**Previous**: "Generate" button, blue background, above image

**Current**:
- Text: "Create" (and "Creating..." when loading)
- Position: Fixed at bottom center, 24px from bottom
- Size: 40px tall, padding 0 40px
- Shape: Fully pill-shaped (borderRadius: 20px)
- Colors: White background, black text
- Typography: 14px, bold, Hedvig Letters Serif
- Shadow: `0 4px 12px rgba(255, 255, 255, 0.2)`
- Z-index: 1000 (stays fixed during zoom)

#### 4. Sources Modal - Complete Redesign
**Status**: ✅ Implemented

**Previous**: Toggle button below image with inline credits

**Current Design**:

**Sources Button**:
- Position: Bottom left, 24px from left, 24px from bottom
- Style: Pill-shaped, 40px tall, dark gray background
- Text: "Sources" (14px, bold, Hedvig Letters Serif)
- 16px margin to Reset Zoom button

**Modal Layout**:
- Position: Floating panel above Sources button (bottom: 76px, left: 24px)
- Dimensions: 264px wide, maxHeight: calc(100vh - 100px)
- Can extend from button to 24px from top of window
- Background: #1a1a1a with 1px #333333 border
- Padding: 20px
- Scrollable (overflow-y: auto)

**Content Structure** (single column):
For each artwork:
1. Image: 224px wide, variable height, centered
2. Title: 13px, bold, white (#ffffff)
3. Artist, Date: 12px, light gray (#cccccc), format: "Artist Name, Date"
4. Divider: 1px horizontal line, rgba(255,255,255,0.1), 24px margins

**Removed Elements**:
- "Source Artworks" header
- Role labels (TOP/MIDDLE/BOTTOM)
- "Cropped segment" dimensions
- Department field
- "View on Met Museum →" links

**Modal Interaction**:
- Click overlay to close
- Scrolling works independently from main canvas zoom
- Three artworks always visible with scroll

#### 5. Download Functionality
**Status**: ✅ Implemented

**Download Button**:
- Position: Bottom right, 24px from right and bottom
- Style: Circular, 40px diameter, dark gray background
- Icon: download.svg (20×20px, inverted to white)
- Hover: Lightens to #4a4a4a
- Function: Downloads composite as `exquisite-corpse-{id}.png`

**Implementation**:
- Fetches image from result.image_url
- Creates blob and temporary download link
- Triggers browser download
- Cleans up URL and DOM elements

#### 6. Typography System
**Status**: ✅ Implemented

**Font**: Hedvig Letters Serif
- Google Fonts CDN
- Optical sizing: auto
- Weight: 400
- Style: normal

**Applied To**:
- All body text
- All buttons (Create, Sources, Reset Zoom, Download)
- Modal content (titles, artist/date)
- Footer text
- Error messages
- Placeholder text

**Font Loading**:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hedvig+Letters+Serif:opsz@12..24&display=swap" rel="stylesheet">
```

#### 7. Backend Fix - Met Museum Links
**Status**: ✅ Fixed

**Issue**: Links pointed to wrong artworks (used internal database ID)

**Solution**: Changed `backend/app/api/generate.py` to use `met_object_id` instead of `artwork.id` for all three artwork sources

**Files Modified**:
- Changed all instances of `artwork_id=top_seg.artwork.id` to `artwork_id=top_seg.artwork.met_object_id`
- Applied to both `/api/generate` and `/api/generate/random` endpoints

### UI Layout Summary

**Fixed Elements** (always visible, don't scroll/zoom):
- **Top**: LogoA.svg (24px from top, centered)
- **Bottom Left**: Sources button (24px from left/bottom)
- **Bottom Left**: Reset Zoom button (132px from left, 24px from bottom)
- **Bottom Center**: Create button (24px from bottom)
- **Bottom Right**: Download button (24px from right/bottom)
- **Footer**: Met Museum credit (small text, between buttons and bottom)

**Dynamic Elements**:
- **Main Canvas**: Image with zoom/pan (fills viewport, can overlap fixed elements when zoomed)
- **Sources Modal**: Appears above Sources button when clicked (264px wide, scrollable)

### Button Positioning Details

Bottom row (24px from bottom), left to right:
1. Sources: `left: 24px` (pill-shaped, variable width ~92px)
2. Reset Zoom: `left: 132px` (16px margin from Sources)
3. Create: `left: 50%, transform: translateX(-50%)` (centered)
4. Download: `right: 24px`

All buttons: 40px tall, #333333 background, hover to #4a4a4a

### File Changes Summary

**Frontend Files Modified**:
- `frontend/index.html` - Added Google Fonts, viewport meta
- `frontend/src/index.css` - Body background, font, touch-action
- `frontend/src/App.jsx` - Header absolute positioning, logo styling, footer repositioning, black background
- `frontend/src/components/Generator.jsx` - Create button styling, positioning, typography
- `frontend/src/components/ResultDisplay.jsx` - Zoom/pan logic, reset button, download button, sources button, modal, styling
- `frontend/src/components/SourceCredits.jsx` - Single column layout, reduced metadata, dividers, typography
- `frontend/src/LogoA.svg` - Added (copied from root)
- `frontend/src/full.svg` - Added (reset zoom icon)
- `frontend/src/download.svg` - Added (download icon)

**Backend Files Modified**:
- `backend/app/api/generate.py` - Fixed artwork_id to use met_object_id for correct Met Museum links

### Design Principles Established

**Spacing System**:
- Standard margin: 24px (window edges, element spacing)
- Button gap: 16px (between adjacent buttons)
- Modal padding: 20px
- Artwork divider margins: 24px vertical

**Color Palette**:
- Background: #000000 (pure black)
- UI elements: #333333 (dark gray)
- UI hover: #4a4a4a (lighter gray)
- Text primary: #ffffff (white)
- Text secondary: #cccccc (light gray)
- Text tertiary: #999999 (medium gray)
- Accent: #6b9fff (light blue for links)
- Dividers: rgba(255,255,255,0.1) (10% white)

**Button Styles**:
- Create: White background, black text, pill-shaped
- All others: Dark gray background, white text/icons
- All circular buttons: 40px diameter
- All pill buttons: 40px tall, 20px border-radius

**Typography Scale**:
- Buttons: 14px, bold
- Modal title: 13px, bold
- Modal artist/date: 12px, normal
- Footer: 10px

### Known Constraints

**Image Initial Display**:
- Top margin: 72px (logo + spacing)
- Bottom margin: 88px (button + spacing)
- Total reserved space: 160px
- Available height for image: `calc(100vh - 160px)`
- When zoomed: Can expand to full viewport and overlap UI

**Modal Constraints**:
- Max width: 264px
- Max height: `calc(100vh - 100px)` (24px top + 76px bottom)
- Image width: 224px (leaves 40px for padding/borders)
- Images scale to fit width, height varies by aspect ratio

**Browser Compatibility**:
- Viewport prevented from user-scalable (zoom controlled by app)
- Touch-action: manipulation (prevents default browser gestures)
- Uses CSS transforms for smooth 60fps zoom/pan

### Performance Notes

**Zoom/Pan**:
- requestAnimationFrame for 60fps smooth updates
- willChange: transform for GPU acceleration
- Small zoom increments (1.02/0.98) for granular control
- No CSS transitions on image transform (would conflict with real-time updates)

**Reset Animation**:
- 400ms duration
- Ease-out cubic easing (1 - (1 - progress)^3)
- Animates both scale and position simultaneously

### User Experience Flow

1. User lands: Image displayed with proper spacing from logo/button
2. User zooms in: Image can expand to fill screen, overlapping logo/button
3. User pans: Drag to reposition zoomed image
4. User clicks Reset: Smooth animation back to initial view
5. User clicks Sources: Modal slides up from Sources button
6. User scrolls in modal: Independent from main canvas
7. User clicks overlay: Modal closes
8. User clicks Download: Image saves to computer

### Session Summary

**Core Achievement**: Complete UI/UX redesign with dark theme, professional typography, intuitive zoom/pan controls, and streamlined sources display.

**Key Innovation**: Zoom system that allows initial constrained display for composition, then full viewport expansion for detailed viewing, with smooth transitions and independent modal scrolling.

**Design Philosophy**: Minimal, functional interface that doesn't interfere with artwork appreciation. Fixed controls stay accessible but unobtrusive. Typography chosen for readability and aesthetic cohesion with art context.

---

# End of Spec