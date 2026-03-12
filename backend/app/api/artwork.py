"""
API endpoints for artwork information
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Artwork, Generation
from app.schemas.artwork import ArtworkDetail
from app.schemas.generation import GenerationDetail, SourceArtwork
from pathlib import Path


router = APIRouter(prefix="/api", tags=["artwork"])


@router.get("/artwork/{artwork_id}", response_model=ArtworkDetail)
def get_artwork(artwork_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about an artwork

    Args:
        artwork_id: Artwork database ID

    Returns:
        ArtworkDetail
    """
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()

    if not artwork:
        raise HTTPException(status_code=404, detail="Artwork not found")

    return artwork


@router.get("/generation/{generation_id}", response_model=GenerationDetail)
def get_generation(generation_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a generation

    Args:
        generation_id: Generation database ID

    Returns:
        GenerationDetail with full source information
    """
    generation = db.query(Generation).filter(Generation.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    # Build source information
    sources = [
        SourceArtwork(
            role="top",
            artwork_id=generation.top_segment.artwork.id,
            title=generation.top_segment.artwork.title,
            artist=generation.top_segment.artwork.artist,
            object_date=generation.top_segment.artwork.object_date,
            department=generation.top_segment.artwork.department,
            primary_image_url=generation.top_segment.artwork.primary_image_url,
            segment_id=generation.top_segment.id,
            crop_x=generation.top_segment.crop_x,
            crop_y=generation.top_segment.crop_y,
            crop_w=generation.top_segment.crop_w,
            crop_h=generation.top_segment.crop_h,
        ),
        SourceArtwork(
            role="middle",
            artwork_id=generation.middle_segment.artwork.id,
            title=generation.middle_segment.artwork.title,
            artist=generation.middle_segment.artwork.artist,
            object_date=generation.middle_segment.artwork.object_date,
            department=generation.middle_segment.artwork.department,
            primary_image_url=generation.middle_segment.artwork.primary_image_url,
            segment_id=generation.middle_segment.id,
            crop_x=generation.middle_segment.crop_x,
            crop_y=generation.middle_segment.crop_y,
            crop_w=generation.middle_segment.crop_w,
            crop_h=generation.middle_segment.crop_h,
        ),
        SourceArtwork(
            role="bottom",
            artwork_id=generation.bottom_segment.artwork.id,
            title=generation.bottom_segment.artwork.title,
            artist=generation.bottom_segment.artwork.artist,
            object_date=generation.bottom_segment.artwork.object_date,
            department=generation.bottom_segment.artwork.department,
            primary_image_url=generation.bottom_segment.artwork.primary_image_url,
            segment_id=generation.bottom_segment.id,
            crop_x=generation.bottom_segment.crop_x,
            crop_y=generation.bottom_segment.crop_y,
            crop_w=generation.bottom_segment.crop_w,
            crop_h=generation.bottom_segment.crop_h,
        ),
    ]

    return GenerationDetail(
        id=generation.id,
        output_path=generation.output_path,
        total_score=generation.total_score,
        tm_score=generation.tm_score,
        mb_score=generation.mb_score,
        created_at=generation.created_at,
        sources=sources
    )
