"""
Pydantic schemas for artworks
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ArtworkBase(BaseModel):
    met_object_id: int
    title: Optional[str] = None
    artist: Optional[str] = None
    artist_bio: Optional[str] = None
    object_date: Optional[str] = None
    department: Optional[str] = None
    object_name: Optional[str] = None
    medium: Optional[str] = None


class ArtworkDetail(ArtworkBase):
    id: int
    primary_image_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_public_domain: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SegmentInfo(BaseModel):
    id: int
    role: str
    crop_x: int
    crop_y: int
    crop_w: int
    crop_h: int
    artwork_id: int

    class Config:
        from_attributes = True
