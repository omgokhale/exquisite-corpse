"""
Pydantic schemas for generations
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class SourceArtwork(BaseModel):
    role: str
    artwork_id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    object_date: Optional[str] = None
    department: Optional[str] = None
    primary_image_url: Optional[str] = None
    segment_id: int
    crop_x: int
    crop_y: int
    crop_w: int
    crop_h: int


class GenerationResponse(BaseModel):
    id: int
    image_url: str
    generation_time_ms: int
    total_score: float
    tm_score: float
    mb_score: float
    sources: list[SourceArtwork]
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class GenerationDetail(BaseModel):
    id: int
    output_path: str
    total_score: float
    tm_score: float
    mb_score: float
    created_at: datetime
    sources: list[SourceArtwork]

    class Config:
        from_attributes = True
