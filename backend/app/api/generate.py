"""
API endpoints for generating exquisite corpse composites
"""
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from pathlib import Path

from app.db.database import get_db
from app.db.models import Segment, SegmentRole
from app.schemas.generation import GenerationResponse, SourceArtwork
from app.services.ranking import generate_triplet
from app.services.compositing import create_generation


router = APIRouter(prefix="/api", tags=["generation"])


def generate_random_triplet(db: Session):
    """
    Generate a random triplet without FAISS (fallback method)

    Returns:
        Tuple of (top_seg, mid_seg, bot_seg, details)
    """
    # Debug: Check segment counts
    total = db.query(Segment).count()
    top_count = db.query(Segment).filter(Segment.role == SegmentRole.TOP).count()
    print(f"DEBUG: Total segments: {total}, Top segments: {top_count}")

    # Get random segments for each role
    top_seg = db.query(Segment).filter(
        Segment.role == SegmentRole.TOP
    ).order_by(func.random()).first()

    print(f"DEBUG: Top segment found: {top_seg}")

    if not top_seg:
        raise ValueError("No top segments available")

    middle_seg = db.query(Segment).filter(
        Segment.role == SegmentRole.MIDDLE,
        Segment.artwork_id != top_seg.artwork_id
    ).order_by(func.random()).first()

    if not middle_seg:
        raise ValueError("No middle segments available")

    bottom_seg = db.query(Segment).filter(
        Segment.role == SegmentRole.BOTTOM,
        Segment.artwork_id.notin_([top_seg.artwork_id, middle_seg.artwork_id])
    ).order_by(func.random()).first()

    if not bottom_seg:
        raise ValueError("No bottom segments available")

    details = {
        'tm_score': 0.0,
        'mb_score': 0.0,
        'total_score': 0.0,
        'method': 'random'
    }

    return top_seg, middle_seg, bottom_seg, details


@router.post("/generate", response_model=GenerationResponse)
def generate_composite(db: Session = Depends(get_db)):
    """
    Generate a new exquisite corpse composite
    Uses FAISS-based scoring if available, otherwise falls back to random selection

    Returns:
        GenerationResponse with image URL and metadata
    """
    start_time = time.time()

    try:
        # Try FAISS-based generation first
        try:
            top_seg, mid_seg, bot_seg, details = generate_triplet(db)
        except FileNotFoundError:
            # FAISS indexes not built yet, fall back to random
            top_seg, mid_seg, bot_seg, details = generate_random_triplet(db)
        except Exception as e:
            # Other errors with FAISS, fall back to random
            if "index" in str(e).lower() or "embedding" in str(e).lower():
                top_seg, mid_seg, bot_seg, details = generate_random_triplet(db)
            else:
                raise

        # Create composite image
        generation = create_generation(
            top_segment_id=top_seg.id,
            middle_segment_id=mid_seg.id,
            bottom_segment_id=bot_seg.id,
            tm_score=details.get('tm_score', 0.0),
            mb_score=details.get('mb_score', 0.0),
            total_score=details.get('total_score', 0.0),
            db=db
        )

        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        sources = [
            SourceArtwork(
                role="top",
                artwork_id=top_seg.artwork.met_object_id,
                title=top_seg.artwork.title,
                artist=top_seg.artwork.artist,
                object_date=top_seg.artwork.object_date,
                department=top_seg.artwork.department,
                primary_image_url=top_seg.artwork.primary_image_url,
                segment_id=top_seg.id,
                crop_x=top_seg.crop_x,
                crop_y=top_seg.crop_y,
                crop_w=top_seg.crop_w,
                crop_h=top_seg.crop_h,
            ),
            SourceArtwork(
                role="middle",
                artwork_id=mid_seg.artwork.met_object_id,
                title=mid_seg.artwork.title,
                artist=mid_seg.artwork.artist,
                object_date=mid_seg.artwork.object_date,
                department=mid_seg.artwork.department,
                primary_image_url=mid_seg.artwork.primary_image_url,
                segment_id=mid_seg.id,
                crop_x=mid_seg.crop_x,
                crop_y=mid_seg.crop_y,
                crop_w=mid_seg.crop_w,
                crop_h=mid_seg.crop_h,
            ),
            SourceArtwork(
                role="bottom",
                artwork_id=bot_seg.artwork.met_object_id,
                title=bot_seg.artwork.title,
                artist=bot_seg.artwork.artist,
                object_date=bot_seg.artwork.object_date,
                department=bot_seg.artwork.department,
                primary_image_url=bot_seg.artwork.primary_image_url,
                segment_id=bot_seg.id,
                crop_x=bot_seg.crop_x,
                crop_y=bot_seg.crop_y,
                crop_w=bot_seg.crop_w,
                crop_h=bot_seg.crop_h,
            ),
        ]

        # Get relative image path for URL
        output_path = Path(generation.output_path)
        image_url = f"/outputs/{output_path.name}"

        return GenerationResponse(
            id=generation.id,
            image_url=image_url,
            generation_time_ms=generation_time_ms,
            total_score=generation.total_score,
            tm_score=generation.tm_score,
            mb_score=generation.mb_score,
            sources=sources,
            details=details
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("/generate/random", response_model=GenerationResponse)
def generate_random_composite(db: Session = Depends(get_db)):
    """
    Generate a random exquisite corpse composite (no scoring)
    Useful for testing or when FAISS indexes aren't available

    Returns:
        GenerationResponse with image URL and metadata
    """
    start_time = time.time()

    try:
        # Generate random triplet
        top_seg, mid_seg, bot_seg, details = generate_random_triplet(db)

        # Create composite image
        generation = create_generation(
            top_segment_id=top_seg.id,
            middle_segment_id=mid_seg.id,
            bottom_segment_id=bot_seg.id,
            tm_score=0.0,
            mb_score=0.0,
            total_score=0.0,
            db=db
        )

        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Build response
        sources = [
            SourceArtwork(
                role="top",
                artwork_id=top_seg.artwork.met_object_id,
                title=top_seg.artwork.title,
                artist=top_seg.artwork.artist,
                object_date=top_seg.artwork.object_date,
                department=top_seg.artwork.department,
                primary_image_url=top_seg.artwork.primary_image_url,
                segment_id=top_seg.id,
                crop_x=top_seg.crop_x,
                crop_y=top_seg.crop_y,
                crop_w=top_seg.crop_w,
                crop_h=top_seg.crop_h,
            ),
            SourceArtwork(
                role="middle",
                artwork_id=mid_seg.artwork.met_object_id,
                title=mid_seg.artwork.title,
                artist=mid_seg.artwork.artist,
                object_date=mid_seg.artwork.object_date,
                department=mid_seg.artwork.department,
                primary_image_url=mid_seg.artwork.primary_image_url,
                segment_id=mid_seg.id,
                crop_x=mid_seg.crop_x,
                crop_y=mid_seg.crop_y,
                crop_w=mid_seg.crop_w,
                crop_h=mid_seg.crop_h,
            ),
            SourceArtwork(
                role="bottom",
                artwork_id=bot_seg.artwork.met_object_id,
                title=bot_seg.artwork.title,
                artist=bot_seg.artwork.artist,
                object_date=bot_seg.artwork.object_date,
                department=bot_seg.artwork.department,
                primary_image_url=bot_seg.artwork.primary_image_url,
                segment_id=bot_seg.id,
                crop_x=bot_seg.crop_x,
                crop_y=bot_seg.crop_y,
                crop_w=bot_seg.crop_w,
                crop_h=bot_seg.crop_h,
            ),
        ]

        # Get relative image path for URL
        output_path = Path(generation.output_path)
        image_url = f"/outputs/{output_path.name}"

        return GenerationResponse(
            id=generation.id,
            image_url=image_url,
            generation_time_ms=generation_time_ms,
            total_score=0.0,
            tm_score=0.0,
            mb_score=0.0,
            sources=sources,
            details=details
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Random generation failed: {str(e)}")
