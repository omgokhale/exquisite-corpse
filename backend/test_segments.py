from app.db.database import get_db_session
from app.db.models import Segment, SegmentRole
from sqlalchemy import func

db = get_db_session()

print(f"Total segments: {db.query(Segment).count()}")

top_seg = db.query(Segment).filter(
    Segment.role == SegmentRole.TOP
).order_by(func.random()).first()

print(f"Top segment found: {top_seg}")

if top_seg:
    print(f"  Segment ID: {top_seg.id}")
    print(f"  Artwork ID: {top_seg.artwork_id}")
else:
    print("  ERROR: No top segment found!")

db.close()
