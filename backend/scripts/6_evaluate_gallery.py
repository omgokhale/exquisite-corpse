"""
Script to generate evaluation gallery of composites

Usage:
    python scripts/6_evaluate_gallery.py [--count 100]
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import get_db_session
from app.services.ranking import generate_triplet
from app.services.compositing import create_generation
from app.core.config import OUTPUTS_DIR


def generate_gallery_html(generations, output_path):
    """Generate HTML gallery page"""

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Exquisite Corpse Evaluation Gallery</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }
            h1 {
                text-align: center;
                color: #333;
            }
            .gallery {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
                gap: 30px;
                margin-top: 30px;
            }
            .item {
                background: white;
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .item img {
                width: 100%;
                height: auto;
                border-radius: 4px;
            }
            .metadata {
                margin-top: 15px;
                font-size: 14px;
                color: #666;
            }
            .scores {
                margin-top: 10px;
                padding: 10px;
                background: #f9f9f9;
                border-radius: 4px;
                font-size: 12px;
            }
            .score-item {
                margin: 5px 0;
            }
            .sources {
                margin-top: 10px;
                font-size: 12px;
                line-height: 1.6;
            }
            .source {
                margin: 8px 0;
                padding: 8px;
                background: #f0f0f0;
                border-radius: 3px;
            }
            .role {
                font-weight: bold;
                color: #2563eb;
            }
        </style>
    </head>
    <body>
        <h1>Exquisite Corpse Evaluation Gallery</h1>
        <p style="text-align: center; color: #666;">
            Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """<br>
            Total composites: """ + str(len(generations)) + """
        </p>
        <div class="gallery">
    """

    for gen, details in generations:
        output_path_obj = Path(gen.output_path)
        image_filename = output_path_obj.name

        html += f"""
        <div class="item">
            <img src="{image_filename}" alt="Generation {gen.id}">
            <div class="metadata">
                <strong>Generation #{gen.id}</strong>
            </div>
            <div class="scores">
                <div class="score-item"><strong>Total Score:</strong> {details.get('total_score', 0):.3f}</div>
                <div class="score-item"><strong>Top-Middle Seam:</strong> {details.get('tm_score', 0):.3f}</div>
                <div class="score-item"><strong>Middle-Bottom Seam:</strong> {details.get('mb_score', 0):.3f}</div>
                <div class="score-item"><strong>Diversity Bonus:</strong> {details.get('diversity_bonus', 0):.3f}</div>
                <div class="score-item"><strong>Novelty Bonus:</strong> {details.get('novelty_bonus', 0):.3f}</div>
            </div>
            <div class="sources">
                <div class="source">
                    <span class="role">TOP:</span> {gen.top_segment.artwork.title or 'Untitled'}<br>
                    {gen.top_segment.artwork.artist or 'Unknown'} ({gen.top_segment.artwork.object_date or 'n.d.'})
                </div>
                <div class="source">
                    <span class="role">MIDDLE:</span> {gen.middle_segment.artwork.title or 'Untitled'}<br>
                    {gen.middle_segment.artwork.artist or 'Unknown'} ({gen.middle_segment.artwork.object_date or 'n.d.'})
                </div>
                <div class="source">
                    <span class="role">BOTTOM:</span> {gen.bottom_segment.artwork.title or 'Untitled'}<br>
                    {gen.bottom_segment.artwork.artist or 'Unknown'} ({gen.bottom_segment.artwork.object_date or 'n.d.'})
                </div>
            </div>
        </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description="Generate evaluation gallery")
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of composites to generate (default: 100)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Evaluation Gallery Generator")
    print("=" * 60)
    print(f"Target: {args.count} composites")
    print()

    # Get database session
    db = get_db_session()

    try:
        generations = []
        failed_count = 0

        print("Generating composites...")
        for i in tqdm(range(args.count), desc="Generating"):
            try:
                # Generate triplet
                top_seg, mid_seg, bot_seg, details = generate_triplet(db)

                # Create composite
                generation = create_generation(
                    top_segment_id=top_seg.id,
                    middle_segment_id=mid_seg.id,
                    bottom_segment_id=bot_seg.id,
                    tm_score=details.get('tm_score', 0.0),
                    mb_score=details.get('mb_score', 0.0),
                    total_score=details.get('total_score', 0.0),
                    db=db
                )

                generations.append((generation, details))

            except Exception as e:
                tqdm.write(f"Failed to generate composite: {e}")
                failed_count += 1

        print()
        print(f"Successfully generated: {len(generations)}")
        print(f"Failed: {failed_count}")
        print()

        if generations:
            # Generate HTML gallery
            gallery_path = OUTPUTS_DIR / "gallery.html"
            print(f"Creating gallery at: {gallery_path}")
            generate_gallery_html(generations, gallery_path)

            # Calculate statistics
            scores = [details.get('total_score', 0) for _, details in generations]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            print()
            print("=" * 60)
            print("Gallery generation complete!")
            print("=" * 60)
            print(f"Composites: {len(generations)}")
            print(f"Average score: {avg_score:.3f}")
            print(f"Max score: {max_score:.3f}")
            print(f"Min score: {min_score:.3f}")
            print(f"\nGallery saved to: {gallery_path}")
            print(f"Open in browser: file://{gallery_path.absolute()}")
            print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
