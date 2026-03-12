"""
Database models for Exquisite Corpse Generator
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, JSON, DateTime, ForeignKey, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class SegmentRole(str, enum.Enum):
    """Enum for segment position roles"""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class Artwork(Base):
    """Represents an artwork from The Met collection"""
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True)
    met_object_id = Column(Integer, unique=True, nullable=False, index=True)

    # Metadata
    title = Column(String(500))
    artist = Column(String(500))
    artist_bio = Column(Text)
    object_date = Column(String(200))
    begin_date = Column(Integer)
    end_date = Column(Integer)
    department = Column(String(200))
    object_name = Column(String(200))
    medium = Column(String(500))
    dimensions = Column(Text)

    # Images
    primary_image_url = Column(String(1000))
    primary_image_small_url = Column(String(1000))
    local_image_path = Column(String(500))

    # Image properties
    width = Column(Integer)
    height = Column(Integer)

    # Flags
    is_public_domain = Column(Boolean, default=True, index=True)

    # Raw data
    raw_json = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    segments = relationship("Segment", back_populates="artwork", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_public_domain_object_name', 'is_public_domain', 'object_name'),
    )


class Segment(Base):
    """Represents a cropped segment from an artwork"""
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False, index=True)

    # Segment properties
    role = Column(Enum(SegmentRole), nullable=False, index=True)

    # Crop coordinates
    crop_x = Column(Integer, nullable=False)
    crop_y = Column(Integer, nullable=False)
    crop_w = Column(Integer, nullable=False)
    crop_h = Column(Integer, nullable=False)

    # Files
    preview_path = Column(String(500))
    embedding_path = Column(String(500))

    # Seam features (JSON stored as dict)
    top_seam_features = Column(JSON)  # {color_hist: [...], edge_density: float}
    bottom_seam_features = Column(JSON)

    # Quality score
    quality_score = Column(Float)

    # Semantic score (pre-computed CLIP text-image similarity for role appropriateness)
    semantic_score = Column(Float, default=0.0)

    # Alignment features (pre-computed subject position for horizontal alignment)
    # JSON: {center_x: float, width: float, bbox: [x, y, w, h]}
    # center_x and width are normalized 0.0-1.0 relative to segment width
    alignment_features = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    artwork = relationship("Artwork", back_populates="segments")

    # For generations - these are the reverse relationships
    top_generations = relationship(
        "Generation",
        foreign_keys="Generation.top_segment_id",
        back_populates="top_segment"
    )
    middle_generations = relationship(
        "Generation",
        foreign_keys="Generation.middle_segment_id",
        back_populates="middle_segment"
    )
    bottom_generations = relationship(
        "Generation",
        foreign_keys="Generation.bottom_segment_id",
        back_populates="bottom_segment"
    )

    # Indexes
    __table_args__ = (
        Index('idx_artwork_role', 'artwork_id', 'role'),
    )


class Generation(Base):
    """Represents a generated exquisite corpse composite"""
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)

    # Segments used
    top_segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    middle_segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    bottom_segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)

    # Scores
    tm_score = Column(Float)  # top-middle seam score
    mb_score = Column(Float)  # middle-bottom seam score
    total_score = Column(Float)

    # Output
    output_path = Column(String(500))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    top_segment = relationship("Segment", foreign_keys=[top_segment_id], back_populates="top_generations")
    middle_segment = relationship("Segment", foreign_keys=[middle_segment_id], back_populates="middle_generations")
    bottom_segment = relationship("Segment", foreign_keys=[bottom_segment_id], back_populates="bottom_generations")
