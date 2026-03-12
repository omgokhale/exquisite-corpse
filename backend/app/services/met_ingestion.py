"""
Service for ingesting artworks from The Metropolitan Museum of Art Collection API
"""
import time
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.config import (
    MET_SEARCH_ENDPOINT,
    MET_OBJECT_ENDPOINT,
    MET_REQUEST_DELAY,
    CONCURRENT_DOWNLOADS,
    DOWNLOAD_RETRY_ATTEMPTS,
    DOWNLOAD_RETRY_DELAY,
    RAW_IMAGES_DIR,
)
from app.db.models import Artwork


def search_paintings(query: str = "painting", limit: Optional[int] = None) -> List[int]:
    """
    Search for paintings in The Met collection

    Args:
        query: Search query string
        limit: Maximum number of object IDs to return

    Returns:
        List of Met object IDs
    """
    params = {
        "q": query,
        "hasImages": "true",
    }

    try:
        response = requests.get(MET_SEARCH_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        object_ids = data.get("objectIDs", [])
        if object_ids and limit:
            return object_ids[:limit]
        return object_ids or []

    except Exception as e:
        print(f"Error searching Met collection: {e}")
        return []


def fetch_object_details(object_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed information about a specific object

    Args:
        object_id: Met object ID

    Returns:
        Object data dict or None if failed
    """
    url = f"{MET_OBJECT_ENDPOINT}/{object_id}"

    try:
        time.sleep(MET_REQUEST_DELAY)  # Rate limiting
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"Error fetching object {object_id}: {e}")
        return None


def download_image(url: str, save_path: Path, retries: int = DOWNLOAD_RETRY_ATTEMPTS) -> bool:
    """
    Download an image with retry logic

    Args:
        url: Image URL
        save_path: Local path to save image
        retries: Number of retry attempts

    Returns:
        True if successful, False otherwise
    """
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=60, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True

        except Exception as e:
            if attempt < retries - 1:
                wait_time = DOWNLOAD_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                print(f"Download failed (attempt {attempt + 1}/{retries}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f"Download failed after {retries} attempts: {e}")
                return False

    return False


def is_valid_artwork(obj_data: Dict[str, Any]) -> bool:
    """
    Check if artwork meets ingestion criteria

    Args:
        obj_data: Object data from Met API

    Returns:
        True if artwork should be ingested
    """
    # Must be public domain
    if not obj_data.get("isPublicDomain"):
        return False

    # Must have primary image
    primary_image = obj_data.get("primaryImage", "")
    if not primary_image or primary_image == "":
        return False

    return True


def should_prefer_artwork(obj_data: Dict[str, Any]) -> bool:
    """
    Check if artwork should be preferred (e.g., is a painting)

    Args:
        obj_data: Object data from Met API

    Returns:
        True if artwork is preferred type
    """
    object_name = obj_data.get("objectName", "").lower()
    return "painting" in object_name


def process_artwork(object_id: int, db: Session) -> Optional[Artwork]:
    """
    Process a single artwork: fetch details, download image, store in DB

    Args:
        object_id: Met object ID
        db: Database session

    Returns:
        Artwork model instance or None if failed
    """
    # Check if already exists
    existing = db.query(Artwork).filter(Artwork.met_object_id == object_id).first()
    if existing:
        return existing

    # Fetch object details
    obj_data = fetch_object_details(object_id)
    if not obj_data:
        return None

    # Validate artwork
    if not is_valid_artwork(obj_data):
        return None

    # Download image
    primary_image_url = obj_data.get("primaryImage")
    image_filename = f"{object_id}.jpg"
    image_path = RAW_IMAGES_DIR / image_filename

    if not download_image(primary_image_url, image_path):
        return None

    # Create artwork record
    artwork = Artwork(
        met_object_id=object_id,
        title=obj_data.get("title", ""),
        artist=obj_data.get("artistDisplayName", ""),
        artist_bio=obj_data.get("artistDisplayBio", ""),
        object_date=obj_data.get("objectDate", ""),
        begin_date=obj_data.get("objectBeginDate"),
        end_date=obj_data.get("objectEndDate"),
        department=obj_data.get("department", ""),
        object_name=obj_data.get("objectName", ""),
        medium=obj_data.get("medium", ""),
        dimensions=obj_data.get("dimensions", ""),
        primary_image_url=primary_image_url,
        primary_image_small_url=obj_data.get("primaryImageSmall", ""),
        local_image_path=str(image_path),
        is_public_domain=True,
        raw_json=obj_data,
    )

    db.add(artwork)
    db.commit()
    db.refresh(artwork)

    return artwork


def ingest_artworks(
    db: Session,
    target_count: int = 500,
    search_query: str = "painting",
    prefer_paintings: bool = True
) -> List[Artwork]:
    """
    Main ingestion pipeline

    Args:
        db: Database session
        target_count: Target number of artworks to ingest
        search_query: Search query for Met API
        prefer_paintings: Prioritize paintings over other object types

    Returns:
        List of ingested Artwork instances
    """
    print(f"Starting ingestion: target {target_count} artworks")

    # Search for object IDs (get more than needed to account for filtering)
    search_limit = target_count * 5  # Get 5x to account for public domain filtering
    print(f"Searching for {search_limit} objects with query '{search_query}'...")

    object_ids = search_paintings(query=search_query, limit=search_limit)
    print(f"Found {len(object_ids)} object IDs")

    if not object_ids:
        print("No objects found in search")
        return []

    # Process artworks sequentially (SQLite doesn't handle concurrent writes well)
    ingested_artworks = []
    failed_count = 0

    for i, obj_id in enumerate(object_ids):
        if len(ingested_artworks) >= target_count:
            break

        try:
            artwork = process_artwork(obj_id, db)
            if artwork:
                ingested_artworks.append(artwork)
                print(f"✓ Ingested [{len(ingested_artworks)}/{target_count}]: {artwork.title[:60]}")
            else:
                failed_count += 1
        except Exception as e:
            print(f"✗ Error processing object {obj_id}: {e}")
            failed_count += 1

    print(f"\nIngestion complete:")
    print(f"  Successfully ingested: {len(ingested_artworks)}")
    print(f"  Failed/skipped: {failed_count}")

    return ingested_artworks
